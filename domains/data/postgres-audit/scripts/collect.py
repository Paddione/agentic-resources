#!/usr/bin/env python3
"""Collect catalog evidence with explicit Kubernetes targets and read-only psql."""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('context', 'namespace', 'pod', 'container', 'output'):
        parser.add_argument('--' + key, required=True)
    parser.add_argument('--user', default='postgres')
    parser.add_argument('--database', action='append', help='Default: all connectable non-template DBs')
    args = parser.parse_args()
    queries = json.loads((Path(__file__).resolve().parent.parent / 'references/queries.json').read_text())
    base = ['kubectl', '--context', args.context, '-n', args.namespace, 'exec', args.pod,
            '-c', args.container, '--', 'env',
            'PGOPTIONS=-c default_transaction_read_only=on -c statement_timeout=15000 -c lock_timeout=2000',
            'psql', '-X', '-w', '-v', 'ON_ERROR_STOP=1', '-U', args.user, '-At']
    def query(db, sql):
        wrapped = 'SELECT COALESCE(json_agg(q),\'[]\'::json) FROM (' + sql.rstrip(';') + ') q'
        result = subprocess.run(base + ['-d', db, '-c', wrapped], capture_output=True, text=True, timeout=25)
        if result.returncode:
            raise RuntimeError(result.stderr.strip())
        return json.loads(result.stdout)
    now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = {'started_at': now(), 'target': vars(args), 'queries': queries, 'databases': {}}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        parser.error('output already exists; choose a new evidence path')
    def save():
        with os.fdopen(os.open(output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 'w') as handle:
            json.dump(result, handle, indent=2)
            handle.write('\n')
    try:
        result['database_inventory'] = query('postgres', queries['databases'])
    except (RuntimeError, subprocess.TimeoutExpired, ValueError) as exc:
        result['inventory_error'] = str(exc)
        save()
        return 1
    databases = args.database or [d['datname'] for d in result['database_inventory']]
    for db in databases:
        evidence = result['databases'][db] = {'started_at': now()}
        for name, sql in queries.items():
            if name == 'databases':
                continue
            if name in ('top_queries', 'stats_info') and not any(
                    e.get('extname') == 'pg_stat_statements' for e in evidence.get('extensions', [])):
                evidence[name] = {'skipped': 'pg_stat_statements not installed in this database'}
                continue
            try:
                evidence[name] = query(db, sql)
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
