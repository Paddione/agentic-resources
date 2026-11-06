#!/usr/bin/env python3
"""Validate the shared portable code-graph contract without indexing or writes."""
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re


class _Ctx:
    """Mutable validation context shared by composable checks (error order = check order)."""

    def __init__(self, data, repo=None):
        self.data = data
        self.repo = repo
        self.errors = []
        self.warnings = []
        self.manifest = {}
        self.scopes = []
        self.file_map = {}
        self.node_ids = set()
        self.edge_ids = set()
        self.nodes = []
        self.edges = []
        self.files = []
        self.gaps = 0
        self.line_counts = {}

    def need(self, ok, message):
        if not ok:
            self.errors.append(message)


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


def check_schema(ctx):
    data = ctx.data
    if not isinstance(data, dict):
        return {'valid': False, 'errors': ['graph: expected object'], 'warnings': []}
    ctx.need(type(data.get('schema_version')) is int and data.get('schema_version') == 1,
             'schema_version: expected 1')
    return None


def check_manifest(ctx):
    data = ctx.data
    manifest = data.get('manifest', {})
    if not isinstance(manifest, dict):
        manifest = {}
        ctx.errors.append('manifest: expected object')
    ctx.manifest = manifest
    for key in ('repo', 'generation', 'tool_version'):
        ctx.need(text(manifest.get(key)), 'manifest: missing ' + key)
    commit = manifest.get('commit')
    ctx.need(isinstance(commit, str) and re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', commit) is not None,
             'manifest: invalid full commit hash')
    for key in ('dirty', 'complete', 'pagination_exhausted'):
        ctx.need(type(manifest.get(key)) is bool, 'manifest: expected boolean ' + key)
    if manifest.get('dirty'):
        ctx.need(digest(manifest.get('dirty_digest')), 'manifest: dirty snapshot needs dirty_digest')
    scopes = manifest.get('scope')
    ctx.need(isinstance(scopes, list) and bool(scopes), 'manifest: scope must be nonempty array')
    scopes = scopes if isinstance(scopes, list) else []
    for scope in scopes:
        ctx.need(scope == '.' or path_ok(scope), 'manifest: unsafe scope')
    ctx.scopes = [x for x in scopes if x == '.' or path_ok(x)]
    if manifest.get('complete'):
        ctx.need(manifest.get('pagination_exhausted') is True, 'complete export has unexhausted pagination')
    else:
        ctx.warnings.append('Partial export: exhaustive conclusions are unavailable.')
    return manifest


def _span(ctx, row, label):
    a, b = row.get('start_line'), row.get('end_line')
    ctx.need(integer(a) and integer(b) and 1 <= a <= b, label + ': invalid source span')


def check_files(ctx):
    data = ctx.data
    manifest, scopes = ctx.manifest, ctx.scopes
    value = data.get('files')
    ctx.need(isinstance(value, list), 'files: expected array')
    files = value if isinstance(value, list) else []
    ctx.files = files
    file_map, gaps = {}, 0
    for row in files:
        if not isinstance(row, dict):
            ctx.errors.append('file: expected object')
            continue
        path = row.get('path')
        if not path_ok(path):
            ctx.errors.append('file: unsafe path')
            continue
        ctx.need(path not in file_map, 'duplicate file path: ' + path)
        file_map[path] = row
        ctx.need(any(x == '.' or path == x or path.startswith(x + '/') for x in scopes),
                 'file outside scope: ' + path)
        ctx.need(digest(row.get('sha256')), 'file missing hash: ' + path)
        coverage = row.get('coverage')
        ctx.need(coverage in ('indexed', 'partial', 'excluded', 'unsupported', 'failed', 'unknown'),
                 'invalid coverage: ' + path)
        if coverage != 'indexed':
            gaps += 1
            ctx.need(text(row.get('reason')), 'coverage gap needs reason: ' + path)
        if manifest.get('complete'):
            ctx.need(coverage not in ('partial', 'failed', 'unknown'), 'complete export has coverage gap: ' + path)
        missed = row.get('missed_ranges', [])
        ctx.need(isinstance(missed, list), 'missed_ranges must be array: ' + path)
        if isinstance(missed, list):
            for part in missed:
                if isinstance(part, dict):
                    _span(ctx, part, 'missed range: ' + path)
                else:
                    ctx.errors.append('missed range: expected object')
    ctx.file_map = file_map
    ctx.gaps = gaps
    return file_map


def check_nodes_edges(ctx):
    data = ctx.data
    file_map = ctx.file_map
    node_ids, edge_ids = set(), set()

    def rows(name):
        value = data.get(name)
        ctx.need(isinstance(value, list), name + ': expected array')
        return value if isinstance(value, list) else []

    nodes, edges = rows('nodes'), rows('edges')
    ctx.nodes, ctx.edges = nodes, edges
    for label, values, ids in [('node', nodes, node_ids), ('edge', edges, edge_ids)]:
        for row in values:
            if not isinstance(row, dict):
                ctx.errors.append(label + ': expected object')
                continue
            identity = row.get('id')
            if not text(identity):
                ctx.errors.append(label + ': missing string id')
            else:
                ctx.need(identity not in ids, label + ': duplicate id ' + identity)
                ids.add(identity)
            ctx.need(text(row.get('kind')), label + ': missing kind')
            if label == 'node':
                ctx.need(text(row.get('qualified_name')), 'node: missing qualified name')
                origin = row.get('origin')
                ctx.need(origin in ('source', 'external'), 'node: invalid origin')
                if origin == 'source':
                    ctx.need(path_ok(row.get('path')) and row.get('path') in file_map,
                             'node: source path not inventoried')
                    _span(ctx, row, 'node')
                if origin == 'external':
                    ctx.need(text(row.get('reason')), 'external node needs reason')
                    ctx.need(not any(key in row for key in ('path', 'start_line', 'end_line')),
                             'external node has source location')
            else:
                for key in ('source', 'target'):
                    ctx.need(text(row.get(key)) and row.get(key) in node_ids, 'edge: dangling ' + key)
                ctx.need(row.get('evidence') in ('parsed', 'inferred', 'semantic', 'historical', 'observed'),
                         'edge: missing evidence category')
                ctx.need(text(row.get('strategy')), 'edge: missing strategy')
                if 'confidence' in row:
                    c = row['confidence']
                    ctx.need(finite(c) and 0 <= c <= 1,
                             'edge: invalid confidence')
                if any(key in row for key in ('path', 'start_line', 'end_line')):
                    ctx.need(path_ok(row.get('path')) and row.get('path') in file_map,
                             'edge: evidence path not inventoried')
                    _span(ctx, row, 'edge')
    ctx.node_ids, ctx.edge_ids = node_ids, edge_ids
    return node_ids


def check_embeddings(ctx):
    data = ctx.data
    manifest = ctx.manifest
    node_ids = ctx.node_ids
    embed = data.get('embeddings')
    if embed is not None:
        if not isinstance(embed, dict):
            ctx.errors.append('embeddings: expected object')
        else:
            dim = embed.get('dimension')
            ctx.need(integer(dim) and dim > 0, 'embeddings: invalid dimension')
            ctx.need(text(embed.get('model')), 'embeddings: missing model')
            ctx.need(embed.get('generation') == manifest.get('generation'), 'embeddings: generation drift')
            items, seen = embed.get('items'), set()
            ctx.need(isinstance(items, list), 'embeddings: expected items array')
            for row in items if isinstance(items, list) else []:
                if not isinstance(row, dict):
                    ctx.errors.append('embedding: expected object')
                    continue
                identity = row.get('node_id')
                if text(identity):
                    ctx.need(identity in node_ids and identity not in seen, 'embedding: missing/duplicate node')
                    seen.add(identity)
                else:
                    ctx.errors.append('embedding: missing node_id')
                ctx.need(digest(row.get('input_sha256')), 'embedding: invalid input hash')
                vector = row.get('vector')
                ctx.need(isinstance(vector, list) and len(vector) == dim and
                         all(finite(v) for v in vector),
                         'embedding: invalid vector')


def check_repo(ctx):
    if ctx.repo is None:
        return
    root = Path(ctx.repo).resolve()
    line_counts = {}
    for path, row in ctx.file_map.items():
        source = (root / PurePosixPath(path)).resolve()
        if not source.is_relative_to(root):
            ctx.errors.append('source escapes checkout: ' + path)
            continue
        try:
            raw = source.read_bytes()
            ctx.need(hashlib.sha256(raw).hexdigest() == row.get('sha256'), 'source hash mismatch: ' + path)
            line_counts[path] = len(raw.splitlines())
        except OSError:
            ctx.errors.append('source unreadable: ' + path)
    ctx.line_counts = line_counts
    for row in ctx.nodes + ctx.edges:
        if isinstance(row, dict) and path_ok(row.get('path')) and row.get('path') in line_counts and 'end_line' in row:
            end = row['end_line']
            ctx.need(integer(end) and end <= line_counts[row['path']], 'source span beyond file: ' + row['path'])
    for path, row in ctx.file_map.items():
        for part in row.get('missed_ranges', []) if isinstance(row.get('missed_ranges', []), list) else []:
            if isinstance(part, dict) and path in line_counts:
                end = part.get('end_line')
                ctx.need(integer(end) and end <= line_counts[path], 'missed range beyond file: ' + path)


def validate(data, repo=None):
    """Run composable checks in contract order; identical errors/CLI/exit codes."""
    ctx = _Ctx(data, repo)
    early = check_schema(ctx)
    if early is not None:
        return early
    check_manifest(ctx)
    check_files(ctx)
    check_nodes_edges(ctx)
    check_embeddings(ctx)
    check_repo(ctx)
    return {'valid': not ctx.errors, 'complete': ctx.manifest.get('complete'),
            'counts': {'files': len(ctx.files), 'nodes': len(ctx.nodes), 'edges': len(ctx.edges), 'coverage_gaps': ctx.gaps},
            'errors': ctx.errors, 'warnings': ctx.warnings}


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
