#!/usr/bin/env python3
"""Publish explicit binaries to an app-scoped stable channel. Requires gh authentication."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

REPO = 'deborahfam/app-releases'
MARKER = 'app-release:'


def metadata(app, version, code, files):
    if not re.fullmatch(r'[a-z][a-z0-9-]{1,39}', app):
        raise ValueError('Use a lowercase app ID, 2–40 letters/digits/hyphens')
    if not re.fullmatch(r'\d+\.\d+\.\d+', version) or code <= 0:
        raise ValueError('Use numeric x.y.z version and positive increasing code')
    hashes = {}
    for path in files:
        if not path.is_file() or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', path.name):
            raise ValueError('Explicit asset files with simple filenames are required')
        if path.name in hashes:
            raise ValueError('Duplicate asset filename')
        if path.suffix.lower() not in {'.apk', '.aab', '.exe', '.msi', '.dmg', '.pkg', '.appimage', '.deb', '.rpm', '.zip', '.gz', '.txt', '.json'}:
            raise ValueError('Unsupported public asset type')
        with path.open('rb') as stream:
            hashes[path.name] = hashlib.file_digest(stream, 'sha256').hexdigest()
    if not hashes:
        raise ValueError('At least one explicit release asset is required')
    return dict(app=app, version=version, code=code, sha256=hashes)


def read_metadata(body):
    match = re.search(r'<!-- app-release:(\{[^\n]*\}) -->', body or '')
    if not match:
        raise ValueError('Existing channel has no recognized publisher metadata')
    return json.loads(match[1])


def check_forward(previous, current):
    if previous['app'] != current['app']:
        raise ValueError('App ID mismatch')
    if previous['code'] > current['code']:
        raise ValueError('Refusing to downgrade the stable channel')
    if previous['code'] == current['code'] and previous != current:
        raise ValueError('A published code cannot be reused for different files or versions')


def gh(*args):
    return subprocess.check_output(['gh', *args], text=True)


def find_release(repo, tag):
    # Do not interpret permission/network errors as an absent release.
    pages = json.loads(gh('api', '--paginate', '--slurp', f'repos/{repo}/releases?per_page=100'))
    matches = [r for page in pages for r in page if r['tag_name'] == tag]
    return matches[0] if matches else None


def publish(repo, data, files, notes):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
        raise ValueError('Invalid repository')
    if json.loads(gh('api', f'repos/{repo}'))['private']:
        raise ValueError('The distribution repository must be public')
    version_tag = f"{data['app']}-v{data['version']}"
    stable_tag = f"{data['app']}-stable"
    stable = find_release(repo, stable_tag)
    if stable:
        check_forward(read_metadata(stable['body']), data)
    version = find_release(repo, version_tag)
    if version and read_metadata(version['body']) != data:
        raise ValueError('The historical release already contains different metadata')
    body = (f"{data['app']} {data['version']} (build {data['code']})\n\n" + notes.strip() +
            '\n\n<!-- app-release:' + json.dumps(data, separators=(',', ':'), sort_keys=True) + ' -->\n')
    with tempfile.TemporaryDirectory(prefix='public-release-') as temp:
        notes_path = Path(temp) / 'notes.md'
        notes_path.write_text(body)
        if not version:
            gh('release', 'create', version_tag, '--repo', repo, '--target', 'main', '--draft',
               '--title', f"{data['app']} {data['version']}", '--notes-file', str(notes_path))
        if not version or version['draft']:
            gh('release', 'upload', version_tag, '--repo', repo, *map(str, files), '--clobber')
            gh('release', 'edit', version_tag, '--repo', repo, '--draft=false', '--latest=false')
        # Stable tag stays on the public documentation commit. It never points to private source.
        if not stable:
            gh('release', 'create', stable_tag, '--repo', repo, '--target', 'main', '--draft',
               '--title', f"{data['app']} · stable", '--notes-file', str(notes_path))
        # Same-code retries are idempotent; avoid replacing assets unnecessarily.
        if not stable or read_metadata(stable['body']) != data or stable['draft']:
            gh('release', 'upload', stable_tag, '--repo', repo, *map(str, files), '--clobber')
            gh('release', 'edit', stable_tag, '--repo', repo, '--draft=false', '--latest=false',
               '--title', f"{data['app']} {data['version']} · stable", '--notes-file', str(notes_path))
            for asset in (stable or {}).get('assets', []):
                if asset['name'] not in data['sha256']:
                    gh('api', '--method', 'DELETE', f"repos/{repo}/releases/assets/{asset['id']}")
    print(f'https://github.com/{repo}/releases/tag/{stable_tag}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default=REPO)
    parser.add_argument('--app', required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--code', type=int, required=True)
    parser.add_argument('--asset', type=Path, action='append', required=True)
    parser.add_argument('--notes', type=Path)
    args = parser.parse_args()
    data = metadata(args.app, args.version, args.code, args.asset)
    notes = args.notes.read_text() if args.notes else 'Install the signed package over your current installation. Do not uninstall first.'
    publish(args.repo, data, args.asset, notes)


if __name__ == '__main__':
    main()
