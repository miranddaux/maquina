#!/usr/bin/env python3
"""Build a complete portable skill package; never include private runtime state."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.4.0-preview.1'
FILENAME = 'curiolab-3d-' + VERSION + '.zip'
MANIFEST = 'PACKAGE-MANIFEST.json'
DIRECTORIES = ('skills', 'engine', 'integrations', 'docs', 'web', 'tests', 'tools',
               'shared', 'assets', 'mascot-studio', 'migrations')
FILES = ('README.md', 'THIRD-PARTY-NOTICES.txt', 'app.py', 'panel_state.py',
         'mascot_registry.py', 'CLAUDE.md', 'ABRIR-PAINEL.sh', 'ABRIR-PAINEL.bat',
         'INSTALAR-SKILL.py', 'INSTALAR-SKILL.sh', 'INSTALAR-SKILL.bat', '.gitignore')
EXCLUDED = {'.local', '.git', '.env', '.venv', '__pycache__', 'node_modules',
            '.agents', '.claude', '.codex', '.aws'}


def collect_files(root=ROOT):
    root = Path(root).resolve()
    entries = {}
    for directory in DIRECTORIES:
        for path in (root / directory).rglob('*'):
            relative = path.relative_to(root)
            if EXCLUDED.intersection(relative.parts) or path.name.startswith('.env') or path.suffix == '.pyc':
                continue
            if path.is_symlink():
                raise ValueError('O pacote não aceita links simbólicos: ' + relative.as_posix())
            if path.is_file():
                entries[relative.as_posix()] = path.read_bytes()
    for name in FILES:
        path = root / name
        if path.is_file() and not path.is_symlink():
            entries[name] = path.read_bytes()
    # A standalone skill loader finds SKILL.md at the package root too.
    entries['SKILL.md'] = (root / 'skills/curiolab-3d/SKILL.md').read_bytes()
    for path in (root / 'skills/curiolab-3d/references').glob('*.md'):
        entries['references/' + path.name] = path.read_bytes()
    for name in ('casa-fullhd.mp4', 'casa-fullhd.metadata.json',
                 'sala-amarela-fullhd.mp4', 'sala-amarela-fullhd.metadata.json'):
        path = root / 'outputs' / name
        if path.is_file() and not path.is_symlink():
            entries['outputs/' + name] = path.read_bytes()
    required = ('SKILL.md', 'INSTALAR-SKILL.py', 'tools/install_skill.py',
                'tools/smoke_skill.py', 'engine/render.py', 'web/panel.html',
                'web/mascot-viewer/index.html', 'mascot_registry.py')
    for name in required:
        if name not in entries:
            raise ValueError('Pacote incompleto: ' + name)
    return entries


def build_package(root=ROOT):
    entries = collect_files(root)
    manifest = {'application': 'curiolab-3d', 'version': VERSION,
                'migration_applied': False, 'voice_api_called': False,
                'files': {name: {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                          for name, data in sorted(entries.items())}}
    entries[MANIFEST] = json.dumps(manifest, ensure_ascii=False, indent=2).encode('utf8')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100755 if name.endswith('.sh') else 0o100644) << 16
            archive.writestr(info, data)
    return buffer.getvalue(), manifest


def verify_package(root=ROOT, required=False):
    root = Path(root).resolve()
    path = root / MANIFEST
    if not path.is_file():
        if required:
            raise ValueError('Manifesto ausente. Extraia o pacote completo.')
        return {'status': 'source_checkout', 'files_verified': 0}
    manifest = json.loads(path.read_text(encoding='utf8'))
    if manifest.get('application') != 'curiolab-3d' or not isinstance(manifest.get('files'), dict):
        raise ValueError('Manifesto de pacote inválido.')
    for name, expected in manifest['files'].items():
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts or '\\' in name or not relative.parts:
            raise ValueError('Caminho inválido no manifesto.')
        file = root.joinpath(*relative.parts)
        if file.is_symlink() or not file.resolve().is_relative_to(root) or not file.is_file():
            raise ValueError('Arquivo ausente ou caminho não permitido: ' + name)
        data = file.read_bytes()
        if len(data) != expected['size'] or hashlib.sha256(data).hexdigest() != expected['sha256']:
            raise ValueError('Integridade divergente: ' + name + '. Extraia uma cópia íntegra; nada foi instalado.')
    return {'status': 'verified', 'version': manifest['version'], 'files_verified': len(manifest['files'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs' / FILENAME)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    try:
        if args.verify:
            print(json.dumps(verify_package(args.verify, required=True), ensure_ascii=False))
        else:
            data, manifest = build_package()
            output = args.output.resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            temporary = output.with_name(output.name + '.tmp')
            temporary.write_bytes(data)
            os.replace(temporary, output)
            digest = hashlib.sha256(data).hexdigest()
            output.with_suffix('.sha256').write_text(digest + '  ' + output.name + '\n', encoding='utf8')
            print(json.dumps({'file': str(output), 'bytes': len(data), 'sha256': digest,
                              'files': len(manifest['files']), 'version': VERSION}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
