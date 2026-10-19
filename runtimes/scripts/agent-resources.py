#!/usr/bin/env python3
"""Inventory home-level agent resources without recording configuration values."""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / 'agent-resources'
SKILL_ROOTS = ('.agents/skills', '.claude/skills', '.codex/skills',
               '.config/opencode/skills', '.zcode/skills', '.gemini/config/skills',
               '.codex/plugins/cache', '.claude/plugins/cache')


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def portable(path):
    return os.path.relpath(path, ROOT) if path.is_relative_to(ROOT) else str(path)


def inventory():
    tracked = set(git('ls-files', '-z').decode().split('\0'))
    resources, edges, links = {}, [], []

    def add(path, kind):
        rel = portable(path)
        entry = {'id': rel, 'kind': kind, 'exists': path.exists(),
                 'tracked': rel in tracked,
                 'ignored': subprocess.run(['git', '-C', str(ROOT), 'check-ignore',
                                           '-q', '--', rel]).returncode == 0}
        resources.setdefault(rel, entry)
        edges.append({'source': '.', 'relation': 'contains', 'target': rel})
        if path.is_symlink():
            target = path.resolve()
            entry['target'] = portable(target)
            edges.append({'source': rel, 'relation': 'links_to', 'target': entry['target']})
            if target.is_relative_to(ROOT):
                links.append({'path': rel, 'target': entry['target']})
            else:
                entry['restore'] = 'external host dependency'
        return entry

    for base in SKILL_ROOTS:
        directory = ROOT / base
        if not directory.exists():
            continue
        # Include bundled/plugin skills and symlink consumers. Never read skill content.
        candidates = {p.parent for p in directory.rglob('SKILL.md')}
        candidates.update(p for p in directory.iterdir()
                          if p.is_symlink() or (p / 'SKILL.md').exists())
        # Aborted plugin installs leave transient clones that are not real resources.
        candidates = {p for p in candidates
                      if not any(part.startswith('temp_subdir_') for part in p.relative_to(directory).parts)}
        for path in sorted(candidates):
            entry = add(path, 'skill')
            source = path.resolve() / 'SKILL.md'
            source_rel = portable(source)
            entry['source'] = source_rel
            entry['source_tracked'] = source_rel in tracked
            entry['restore'] = ('dotfiles' if source_rel in tracked else
                                'project clone' if source.is_relative_to(ROOT / 'Bachelorprojekt') else
                                'provider-managed' if '/plugins/' in source_rel or '/.system/' in source_rel else
                                'missing source' if not source.exists() else 'untracked source')
            edges.append({'source': entry['id'], 'relation': 'defined_by', 'target': source_rel})

    # Local executables: presence and ownership only, never run them to inspect versions.
    for base in ('.local/bin', '.npm-global/bin', '.opencode/bin', '.bun/bin'):
        directory = ROOT / base
        if directory.exists():
            for path in sorted(directory.iterdir()):
                if not path.name.startswith('.') and (path.is_symlink() or
                                                       (path.is_file() and os.access(path, os.X_OK))):
                    entry = add(path, 'tool')
                    entry['executable'] = os.access(path, os.X_OK)
                    if not entry['tracked']:
                        entry['restore'] = 'installer or external source required'

    for path in sorted((ROOT / '.config/systemd/user').rglob('*')):
        if path.suffix in {'.service', '.timer', '.conf'}:
            entry = add(path, 'service')
            if path.is_symlink() and path.exists():
                entry['restore'] = 'portable link'

    # Track additional resources already admitted by the narrow dotfiles whitelist.
    for rel in sorted(tracked):
        if rel.startswith(('.agents/', '.claude/', '.codex/', '.config/', '.zcode/', '.gemini/', '.qwen/')):
            if '/skills/' not in rel and rel not in resources:
                add(ROOT / rel, 'configuration')
    for rel in ('AGENTS.md', '.claude/sr_opus_5_system_prompt.md', '.codex/hooks.json',
                '.gemini/settings.json', '.gemini/config/config.json',
                '.gemini/config/hooks.json', '.gemini/config/mcp_config.json',
                '.qwen/settings.json'):
        if (ROOT / rel).exists():
            add(ROOT / rel, 'configuration')

    for line in (ROOT / 'repos.txt').read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('#'):
            rel, _remote = line.split(None, 1)
            entry = add(ROOT / rel, 'repository')
            entry['restore'] = 'repos.txt clone'
    node_ids = {'.'} | set(resources) | {edge['target'] for edge in edges}
    return {'schema_version': 1, 'root': '.', 'nodes': sorted(node_ids),
            'resources': list(resources.values()),
            'edges': edges}, links


def package_sources():
    """Record locally installed npm package identities, not registry guesses."""
    packages = []
    base = ROOT / '.npm-global/lib/node_modules'
    if base.exists():
        paths = list(base.glob('*/package.json')) + list(base.glob('@*/*/package.json'))
        for path in sorted(paths):
            info = json.loads(path.read_text())
            if path.parent.is_symlink():
                packages.append({'name': info['name'], 'source': portable(path.parent.resolve()),
                                 'restore': 'project-owned package; install from source'})
            else:
                packages.append({'name': info['name'], 'version': info['version'],
                                 'restore': 'npm install -g --prefix "$HOME/.npm-global" '
                                            + info['name'] + '@' + info['version']})
    return packages


def restore(links, dry_run):
    failures = []
    for link in links:
        path, target = ROOT / link['path'], ROOT / link['target']
        if not path.is_relative_to(ROOT) or not target.is_relative_to(ROOT):
            raise ValueError('link outside home')
        if '..' in Path(link['path']).parts or '..' in Path(link['target']).parts:
            raise ValueError('non-portable link')
        if path.is_symlink() and path.resolve() == target.resolve() and target.exists():
            continue
        if not target.exists():
            failures.append(f'missing source: {link["target"]}')
            continue
        if path.exists() or path.is_symlink():
            failures.append(f'preserved existing destination: {link["path"]}')
            continue
        print(f'link {link["path"]} -> {link["target"]}')
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(os.path.relpath(target, path.parent))
    for failure in failures:
        print(failure)
    return bool(failures)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['scan', 'check', 'check-rebuild', 'restore', 'restore-npm'])
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.command == 'check-rebuild':
        recipes = json.loads((DEST / 'tool-recipes.json').read_text())
        unresolved = [r['path'] for r in recipes if r['kind'] == 'unresolved']
        prerequisites = json.loads((DEST / 'external-prerequisites.json').read_text())
        report_path = DEST / 'fresh-wsl-report.json'
        report = json.loads(report_path.read_text()) if report_path.exists() else {}
        verified = bool(report.get('complete_rebuild_verified')) and not unresolved
        print(f'{len(recipes)} tool recipes, {len(unresolved)} unresolved, '
              f'{len(prerequisites)} external prerequisites')
        print('complete rebuild verified:', verified)
        return 0 if verified else 1
    if args.command == 'restore-npm':
        failures = False
        for package in json.loads((DEST / 'npm-packages.json').read_text()):
            if 'version' not in package:
                print(f'project source required: {package["name"]}')
                continue
            command = ['npm', 'install', '-g', '--prefix', str(ROOT / '.npm-global'),
                       package['name'] + '@' + package['version']]
            print(' '.join(command))
            if not args.dry_run:
                failures |= subprocess.run(command).returncode != 0
        return failures
    if args.command == 'restore':
        return restore(json.loads((DEST / 'links.json').read_text()), args.dry_run)
    graph, links = inventory()
    if args.command == 'scan':
        DEST.mkdir(exist_ok=True)
        (DEST / 'inventory.json').write_text(json.dumps(graph, indent=2) + '\n')
        (DEST / 'links.json').write_text(json.dumps(links, indent=2) + '\n')
        (DEST / 'npm-packages.json').write_text(json.dumps(package_sources(), indent=2) + '\n')
    gaps = [r for r in graph['resources'] if not r['exists'] or
            r.get('restore') in {'missing source', 'untracked source'} or
            (r['kind'] in {'configuration', 'service'} and not r['tracked']
             and r.get('restore') != 'portable link')]
    print(f'{len(graph["resources"])} resources, {len(graph["edges"])} edges, '
          f'{len(links)} portable links, {len(gaps)} source/configuration gaps')
    for resource in gaps:
        print(f'gap: {resource["id"]}')
    print('Binary installers and provider-managed plugins require their original runtimes/accounts.')
    return bool(gaps) if args.command == 'check' else 0


if __name__ == '__main__':
    raise SystemExit(main())
