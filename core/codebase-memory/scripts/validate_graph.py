#!/usr/bin/env python3
"""Validate the shared portable code-graph contract without indexing or writes."""
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re


def validate(data, repo=None):
    errors, warnings = [], []
    def need(ok, message):
        if not ok:
            errors.append(message)
    def text(value):
        return isinstance(value, str) and bool(value.strip())
    def integer(value):
        return type(value) is int
    def finite(value):
        try:
            return type(value) in (int, float) and math.isfinite(value)
        except OverflowError:
            return False
    def digest(value):
        return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None
    def path_ok(value):
        return (text(value) and not value.startswith('/') and '\\' not in value
                and ':' not in value and all(p not in ('', '.', '..') for p in value.split('/')))
    def span(row, label):
        a, b = row.get('start_line'), row.get('end_line')
        need(integer(a) and integer(b) and 1 <= a <= b, label + ': invalid source span')
    def rows(name):
        value = data.get(name)
        need(isinstance(value, list), name + ': expected array')
        return value if isinstance(value, list) else []
    if not isinstance(data, dict):
        return {'valid': False, 'errors': ['graph: expected object'], 'warnings': []}
    need(type(data.get('schema_version')) is int and data.get('schema_version') == 1,
         'schema_version: expected 1')
    manifest = data.get('manifest', {})
    if not isinstance(manifest, dict):
        manifest = {}
        errors.append('manifest: expected object')
    for key in ('repo', 'generation', 'tool_version'):
        need(text(manifest.get(key)), 'manifest: missing ' + key)
    commit = manifest.get('commit')
    need(isinstance(commit, str) and re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', commit) is not None,
         'manifest: invalid full commit hash')
    for key in ('dirty', 'complete', 'pagination_exhausted'):
        need(type(manifest.get(key)) is bool, 'manifest: expected boolean ' + key)
    if manifest.get('dirty'):
        need(digest(manifest.get('dirty_digest')), 'manifest: dirty snapshot needs dirty_digest')
    scopes = manifest.get('scope')
    need(isinstance(scopes, list) and bool(scopes), 'manifest: scope must be nonempty array')
    scopes = scopes if isinstance(scopes, list) else []
    for scope in scopes:
        need(scope == '.' or path_ok(scope), 'manifest: unsafe scope')
    scopes = [x for x in scopes if x == '.' or path_ok(x)]
    if manifest.get('complete'):
        need(manifest.get('pagination_exhausted') is True, 'complete export has unexhausted pagination')
    else:
        warnings.append('Partial export: exhaustive conclusions are unavailable.')
    files, nodes, edges = rows('files'), rows('nodes'), rows('edges')
    file_map, node_ids, edge_ids = {}, set(), set()
    gaps = 0
    for row in files:
        if not isinstance(row, dict):
            errors.append('file: expected object')
            continue
        path = row.get('path')
        if not path_ok(path):
            errors.append('file: unsafe path')
            continue
        need(path not in file_map, 'duplicate file path: ' + path)
        file_map[path] = row
        need(any(x == '.' or path == x or path.startswith(x + '/') for x in scopes),
             'file outside scope: ' + path)
        need(digest(row.get('sha256')), 'file missing hash: ' + path)
        coverage = row.get('coverage')
        need(coverage in ('indexed', 'partial', 'excluded', 'unsupported', 'failed', 'unknown'),
             'invalid coverage: ' + path)
        if coverage != 'indexed':
            gaps += 1
            need(text(row.get('reason')), 'coverage gap needs reason: ' + path)
        if manifest.get('complete'):
            need(coverage not in ('partial', 'failed', 'unknown'), 'complete export has coverage gap: ' + path)
        missed = row.get('missed_ranges', [])
        need(isinstance(missed, list), 'missed_ranges must be array: ' + path)
        if isinstance(missed, list):
            for part in missed:
                if isinstance(part, dict):
                    span(part, 'missed range: ' + path)
                else:
                    errors.append('missed range: expected object')
    for label, values, ids in [('node', nodes, node_ids), ('edge', edges, edge_ids)]:
        for row in values:
            if not isinstance(row, dict):
                errors.append(label + ': expected object')
                continue
            identity = row.get('id')
            if not text(identity):
                errors.append(label + ': missing string id')
            else:
                need(identity not in ids, label + ': duplicate id ' + identity)
                ids.add(identity)
            need(text(row.get('kind')), label + ': missing kind')
            if label == 'node':
                need(text(row.get('qualified_name')), 'node: missing qualified name')
                origin = row.get('origin')
                need(origin in ('source', 'external'), 'node: invalid origin')
                if origin == 'source':
                    need(path_ok(row.get('path')) and row.get('path') in file_map,
                         'node: source path not inventoried')
                    span(row, 'node')
                if origin == 'external':
                    need(text(row.get('reason')), 'external node needs reason')
                    need(not any(key in row for key in ('path', 'start_line', 'end_line')),
                         'external node has source location')
            else:
                for key in ('source', 'target'):
                    need(text(row.get(key)) and row.get(key) in node_ids, 'edge: dangling ' + key)
                need(row.get('evidence') in ('parsed', 'inferred', 'semantic', 'historical', 'observed'),
                     'edge: missing evidence category')
                need(text(row.get('strategy')), 'edge: missing strategy')
                if 'confidence' in row:
                    c = row['confidence']
                    need(finite(c) and 0 <= c <= 1,
                         'edge: invalid confidence')
                if any(key in row for key in ('path', 'start_line', 'end_line')):
                    need(path_ok(row.get('path')) and row.get('path') in file_map,
                         'edge: evidence path not inventoried')
                    span(row, 'edge')
    embed = data.get('embeddings')
    if embed is not None:
        if not isinstance(embed, dict):
            errors.append('embeddings: expected object')
        else:
            dim = embed.get('dimension')
            need(integer(dim) and dim > 0, 'embeddings: invalid dimension')
            need(text(embed.get('model')), 'embeddings: missing model')
            need(embed.get('generation') == manifest.get('generation'), 'embeddings: generation drift')
            items, seen = embed.get('items'), set()
            need(isinstance(items, list), 'embeddings: expected items array')
            for row in items if isinstance(items, list) else []:
                if not isinstance(row, dict):
                    errors.append('embedding: expected object')
                    continue
                identity = row.get('node_id')
                if text(identity):
                    need(identity in node_ids and identity not in seen, 'embedding: missing/duplicate node')
                    seen.add(identity)
                else:
                    errors.append('embedding: missing node_id')
                need(digest(row.get('input_sha256')), 'embedding: invalid input hash')
                vector = row.get('vector')
                need(isinstance(vector, list) and len(vector) == dim and
                     all(finite(v) for v in vector),
                     'embedding: invalid vector')
    if repo is not None:
        root = Path(repo).resolve()
        line_counts = {}
        for path, row in file_map.items():
            source = (root / PurePosixPath(path)).resolve()
            if not source.is_relative_to(root):
                errors.append('source escapes checkout: ' + path)
                continue
            try:
                raw = source.read_bytes()
                need(hashlib.sha256(raw).hexdigest() == row.get('sha256'), 'source hash mismatch: ' + path)
                line_counts[path] = len(raw.splitlines())
            except OSError:
                errors.append('source unreadable: ' + path)
        for row in nodes + edges:
            if isinstance(row, dict) and path_ok(row.get('path')) and row.get('path') in line_counts and 'end_line' in row:
                end = row['end_line']
                need(integer(end) and end <= line_counts[row['path']], 'source span beyond file: ' + row['path'])
        for path, row in file_map.items():
            for part in row.get('missed_ranges', []) if isinstance(row.get('missed_ranges', []), list) else []:
                if isinstance(part, dict) and path in line_counts:
                    end = part.get('end_line')
                    need(integer(end) and end <= line_counts[path], 'missed range beyond file: ' + path)
    return {'valid': not errors, 'complete': manifest.get('complete'),
            'counts': {'files': len(files), 'nodes': len(nodes), 'edges': len(edges), 'coverage_gaps': gaps},
            'errors': errors, 'warnings': warnings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifact', type=Path)
    parser.add_argument('--repo', type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.artifact.read_text(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        result = validate(data, args.repo)
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({'valid': False, 'errors': ['Unreadable or malformed graph: ' + str(exc)]}))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
