#!/usr/bin/env python3
"""Local span recording and summaries; no network or third-party dependencies."""
import argparse
import json
import math
from pathlib import Path
import sqlite3
import tempfile
from datetime import datetime, timezone
from uuid import uuid4


def connect(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('''CREATE TABLE IF NOT EXISTS spans (
        span_id TEXT PRIMARY KEY, trace_id TEXT NOT NULL, parent_id TEXT,
        timestamp TEXT NOT NULL, name TEXT NOT NULL, environment TEXT NOT NULL,
        status TEXT NOT NULL, latency_ms REAL, input_tokens INTEGER, output_tokens INTEGER)''')
    return conn


def record(db_path, *, name, status, trace_id=None, parent_id=None,
           environment='local', latency_ms=None, input_tokens=None, output_tokens=None):
    if status not in ('ok', 'error'):
        raise ValueError('status must be ok or error')
    for label, value in [('name', name), ('environment', environment),
                         ('trace_id', trace_id), ('parent_id', parent_id)]:
        if value is not None and (not isinstance(value, str) or not value.strip() or len(value) > 128):
            raise ValueError(label + ' must be a nonempty string of at most 128 characters')
    for label, value in [('latency_ms', latency_ms), ('input_tokens', input_tokens), ('output_tokens', output_tokens)]:
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(label + ' must be finite and nonnegative')
            if label != 'latency_ms' and (not isinstance(value, int) or value > 2**63 - 1):
                raise ValueError(label + ' must be a SQLite-sized integer')
    conn = connect(db_path)
    try:
        with conn:
            if parent_id:
                parent = conn.execute('SELECT trace_id FROM spans WHERE span_id=?', (parent_id,)).fetchone()
                if parent is None:
                    raise ValueError('parent span does not exist in this database')
                if trace_id and parent['trace_id'] != trace_id:
                    raise ValueError('parent must belong to the same trace')
                trace_id = parent['trace_id']
            row = dict(span_id=uuid4().hex, trace_id=trace_id or uuid4().hex,
                       parent_id=parent_id, timestamp=datetime.now(timezone.utc).isoformat(),
                       name=name, environment=environment, status=status,
                       latency_ms=latency_ms, input_tokens=input_tokens, output_tokens=output_tokens)
            conn.execute('INSERT INTO spans VALUES (:span_id,:trace_id,:parent_id,:timestamp,:name,:environment,:status,:latency_ms,:input_tokens,:output_tokens)', row)
        return row
    finally:
        conn.close()


def report(db_path):
    if not Path(db_path).is_file():
        raise ValueError('telemetry database does not exist')
    conn = connect(db_path)
    try:
        agg = dict(conn.execute('''SELECT COUNT(*) spans, COUNT(DISTINCT trace_id) traces,
            SUM(status='error') errors, MAX(timestamp) latest_timestamp,
            COUNT(latency_ms) latency_samples, AVG(latency_ms) latency_mean_ms,
            COUNT(input_tokens) input_token_samples, SUM(input_tokens) input_tokens,
            COUNT(output_tokens) output_token_samples, SUM(output_tokens) output_tokens FROM spans''').fetchone())
        n = agg['spans']
        agg['errors'] = agg['errors'] or 0
        agg['span_error_rate'] = agg['errors'] / n if n else None
        for percentile in (50, 95):
            count = agg['latency_samples']
            row = conn.execute('SELECT latency_ms FROM spans WHERE latency_ms IS NOT NULL ORDER BY latency_ms LIMIT 1 OFFSET ?', (max(0, math.ceil(count * percentile / 100) - 1),)).fetchone()
            agg[f'latency_p{percentile}_ms'] = row[0] if row else None
        agg['scope'] = 'all locally recorded spans; synthetic events included'
        return agg
    finally:
        conn.close()


def self_test():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / 'spans.sqlite'
        root = record(db, name='test-root', status='ok', latency_ms=10, input_tokens=0)
        child = record(db, name='test-child', status='error', parent_id=root['span_id'], latency_ms=30, output_tokens=5)
        assert child['trace_id'] == root['trace_id']
        record(db, name='test-unknown', status='ok')
        result = report(db)
        assert result['spans'] == 3 and result['traces'] == 2 and result['errors'] == 1
        assert result['latency_mean_ms'] == 20 and result['latency_p95_ms'] == 30
        assert result['input_token_samples'] == 1 and result['input_tokens'] == 0
        assert result['output_token_samples'] == 1 and result['output_tokens'] == 5
        conn = connect(db)
        try:
            assert conn.execute('SELECT parent_id FROM spans WHERE span_id=?', (child['span_id'],)).fetchone()[0] == root['span_id']
        finally:
            conn.close()
        for kwargs in ({'latency_ms': -1}, {'latency_ms': float('nan')}, {'input_tokens': 1.5}, {'parent_id': 'missing'}, {'parent_id': root['span_id'], 'trace_id': 'wrong'}):
            try:
                record(db, name='invalid', status='ok', **kwargs)
            except ValueError:
                pass
            else:
                raise AssertionError('invalid input accepted')
        assert report(db)['spans'] == 3
        empty = Path(tmp) / 'empty.sqlite'
        connect(empty).close()
        assert report(empty)['span_error_rate'] is None
    return {'self_test': 'passed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', help='Explicit path to local SQLite telemetry')
    commands = parser.add_subparsers(dest='command', required=True)
    rec = commands.add_parser('record')
    rec.add_argument('--name', required=True)
    rec.add_argument('--status', choices=['ok', 'error'], required=True)
    rec.add_argument('--trace-id')
    rec.add_argument('--parent-id')
    rec.add_argument('--environment', default='local')
    rec.add_argument('--latency-ms', type=float)
    rec.add_argument('--input-tokens', type=int)
    rec.add_argument('--output-tokens', type=int)
    commands.add_parser('report')
    commands.add_parser('self-test')
    args = vars(parser.parse_args())
    command = args.pop('command')
    db = args.pop('db')
    try:
        if command == 'self-test':
            result = self_test()
        elif not db:
            parser.error('--db is required for record and report')
        elif command == 'record':
            result = record(db, **args)
        else:
            result = report(db)
    except (ValueError, OSError, sqlite3.Error) as exc:
        parser.exit(1, f'telemetry error: {exc}\n')
    print(json.dumps(result, allow_nan=False))


if __name__ == '__main__':
    main()
