#!/usr/bin/env python3
"""Collect catalog evidence with explicit Kubernetes targets and read-only psql.

Auth: relies on ambient in-pod auth (trust/peer/cert) for --user.
Never add a --password/PGPASSWORD flag: it would land in the output JSON
under target.vars (args) and leak via process list. Prefer a restricted
read-only role, e.g. --user audit_ro.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('context', 'namespace', 'pod', 'container', 'output'):
        parser.add_argument('--' + key, required=True)
    parser.add_argument('--user', default=os.environ.get('PGUSER', 'postgres'),
                        help='DB role (default: $PGUSER or postgres). Prefer a restricted read-only role, e.g. --user audit_ro.')
    parser.add_argument('--database', action='append', help='Default: all connectable non-template DBs')
    args = parser.parse_args()
    queries = json.loads((Path(__file__).resolve().parent.parent / 'references/queries.json').read_text())
    base = ['kubectl', '--context', args.context, '-n', args.namespace, 'exec', args.pod,
            '-c', args.container, '--', 'env',
            'PGOPTIONS=-c default_transaction_read_only=on -c statement_timeout=15000 -c lock_timeout=2000 -c idle_in_transaction_session_timeout=5000',
            'psql', '-X', '-w', '-v', 'ON_ERROR_STOP=1', '-U', args.user, '-At']

    def raw(db, sql, timeout=25):
        result = subprocess.run(base + ['-d', db, '-c', sql], capture_output=True, text=True, timeout=timeout)
        if result.returncode:
            raise RuntimeError('kubectl/psql: ' + result.stderr.strip())
        return result.stdout.strip()

    def query(db, sql):
        wrapped = 'SELECT COALESCE(json_agg(q),\'[]\'::json) FROM (' + sql.rstrip(';') + ') q'
        return json.loads(raw(db, wrapped))

    def server_version(db):
        try:
            return int(raw(db, "SELECT current_setting('server_version_num')"))
        except (RuntimeError, subprocess.TimeoutExpired, ValueError):
            return 0

    now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = {'started_at': now(), 'target': vars(args), 'queries': sorted(queries), 'databases': {}}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        parser.error('output already exists; choose a new evidence path')

    def save():
        tmp = None
        try:
            fd, tmppath = tempfile.mkstemp(dir=str(output.parent), prefix=output.name + '.tmp.')
            tmp = tmppath
            with os.fdopen(fd, 'w') as handle:
                json.dump(result, handle, indent=2)
                handle.write('\n')
            os.chmod(tmppath, 0o600)
            os.replace(tmppath, output)
            tmp = None
        finally:
            if tmp:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

    def extensions_installed(evidence):
        exts = evidence.get('extensions', [])
        return isinstance(exts, list) and any(
            isinstance(e, dict) and e.get('extname') == 'pg_stat_statements' for e in exts)

    try:
        result['database_inventory'] = query('postgres', queries['databases'])
    except (RuntimeError, subprocess.TimeoutExpired, ValueError) as exc:
        result['inventory_error'] = str(exc)
        save()
        return 1
    databases = args.database or [d['datname'] for d in result['database_inventory'] if isinstance(d, dict) and 'datname' in d]
    for db in databases:
        evidence = result['databases'][db] = {'started_at': now()}
        version = server_version(db)
        if version:
            evidence['server_version_num'] = version
        # Version-dispatched query selection: PG13- lacks total_exec_time,
        # PG15- lacks indnullsnotdistinct, PG14- lacks pg_stat_statements_info.
        renames = {}
        if version and version < 130000 and 'top_queries_legacy' in queries:
            renames['top_queries'] = 'top_queries_legacy'
        if version and version < 150000 and 'duplicates_legacy' in queries:
            renames['duplicates'] = 'duplicates_legacy'
        for name, sql in queries.items():
            if name == 'databases' or name.endswith('_legacy'):
                continue
            if name in ('top_queries', 'stats_info') and not extensions_installed(evidence):
                evidence[name] = {'skipped': 'pg_stat_statements not installed in this database'}
                continue
            if name == 'stats_info' and version and version < 140000:
                evidence[name] = {'skipped': 'pg_stat_statements_info requires PG14+'}
                continue
            if name == 'sequences' and version and version < 100000:
                evidence[name] = {'skipped': 'pg_sequences requires PG10+'}
                continue
            effective = renames.get(name, name)
            try:
                evidence[name] = query(db, queries[effective])
                if effective != name:
                    evidence[name + '_variant'] = effective
            except (RuntimeError, subprocess.TimeoutExpired, ValueError) as exc:
                evidence[name] = {'error': str(exc)}
        evidence['finished_at'] = now()
        save()
        print(f'{args.namespace}/{db}: collected', flush=True)
    result['finished_at'] = now()
    save()
    return int(any(isinstance(v, dict) and 'error' in v
                   for db in result['databases'].values() for v in db.values()))


if __name__ == '__main__':
    sys.exit(main())
