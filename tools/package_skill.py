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
VERSION = '0.4.0-preview.2'
FILENAME = 'curiolab-3d-runtime-' + VERSION + '.zip'
MANIFEST = 'PACKAGE-MANIFEST.json'
DIRECTORIES = ('skills', 'engine', 'integrations', 'docs', 'web', 'tests', 'tools',
               'shared', 'assets', 'mascot-studio', 'migrations')
FILES = ('README.md', 'THIRD-PARTY-NOTICES.txt', 'app.py', 'panel_state.py',
         'mascot_registry.py', 'CLAUDE.md', 'SECURITY.md', 'INSTALAR-SKILL.py', '.gitignore')
EXCLUDED = {'.local', '.git', '.env', '.venv', '__pycache__', 'node_modules',
            '.agents', '.claude', '.codex', '.aws'}
ALLOWED_EXTENSIONS = {'.md', '.txt', '.py', '.json', '.yaml', '.yml', '.js', '.mjs',
                      '.ts', '.tsx', '.html', '.css', '.map', '.sql', '.glb', '.gltf',
                      '.bin', '.png', '.jpg', '.jpeg', '.webp', '.mp4'}
SKILL_EXTENSIONS = {'.md', '.yaml', '.yml', '.json'}


def checked_data(path):
    data = path.read_bytes()
    # Reject native executable magic even when disguised as a document or image.
    if data.startswith((b'MZ', b'\x7fELF', b'\xca\xfe\xba\xbe', b'\xcf\xfa\xed\xfe', b'\xfe\xed\xfa\xcf')):
        raise ValueError('Executável nativo não permitido na distribuição: ' + path.name)
    return data


def collect_files(root=ROOT, kind='runtime'):
    root = Path(root).resolve()
    if kind not in {'runtime', 'skill'}:
        raise ValueError('Escolha runtime ou skill.')
    if kind == 'skill':
        source = root / 'skills/curiolab-3d'
        entries = {}
        for path in source.rglob('*'):
            if path.is_symlink():
                raise ValueError('A skill textual não aceita links simbólicos.')
            if path.is_file():
                if path.suffix.lower() not in SKILL_EXTENSIONS:
                    raise ValueError('A skill textual não aceita código ou binários: ' + path.name)
                data = checked_data(path)
                data.decode('utf8')
                entries[path.relative_to(source).as_posix()] = data
        if 'SKILL.md' not in entries:
            raise ValueError('SKILL.md ausente.')
        # Keep the writing/visual method useful even before the engine is installed.
        reference_files = {
            'references/production-recipe.md': 'docs/RECEITA-DE-PRODUCAO.md',
            'references/palette-and-environment.md': 'docs/PALETA-E-AMBIENTACAO.md',
            'references/installation-guide.md': 'docs/INSTALACAO.md',
            'references/nico-config.json': 'shared/mascots/nico/1.0.0-candidate.1/config.json',
            'references/channel-brand.json': 'shared/brand.json',
        }
        for name, source_file in reference_files.items():
            path = root / source_file
            if path.is_file():
                data = checked_data(path)
                data.decode('utf8')
                entries[name] = data
        return entries
    entries = {}
    for directory in DIRECTORIES:
        for path in (root / directory).rglob('*'):
            relative = path.relative_to(root)
            if EXCLUDED.intersection(relative.parts) or path.name.startswith('.env') or path.suffix == '.pyc':
                continue
            if path.is_symlink():
                raise ValueError('O pacote não aceita links simbólicos: ' + relative.as_posix())
            if path.is_file():
                if path.suffix.lower() in ALLOWED_EXTENSIONS or path.name == '.gitignore':
                    entries[relative.as_posix()] = checked_data(path)
    for name in FILES:
        path = root / name
        if path.is_file() and not path.is_symlink():
            entries[name] = checked_data(path)
    # A standalone skill loader finds SKILL.md at the package root too.
    entries['SKILL.md'] = (root / 'skills/curiolab-3d/SKILL.md').read_bytes()
    for folder in ['references', 'agents']:
        for path in (root / 'skills/curiolab-3d' / folder).rglob('*'):
            if path.is_file():
                entries[folder + '/' + path.relative_to(root / 'skills/curiolab-3d' / folder).as_posix()] = checked_data(path)
    for name in ('casa-fullhd.mp4', 'casa-fullhd.metadata.json',
                 'sala-amarela-fullhd.mp4', 'sala-amarela-fullhd.metadata.json'):
        path = root / 'outputs' / name
        if path.is_file() and not path.is_symlink():
            entries['outputs/' + name] = checked_data(path)
    required = ('SKILL.md', 'INSTALAR-SKILL.py', 'tools/install_skill.py',
                'tools/smoke_skill.py', 'engine/render.py', 'web/panel.html',
                'web/mascot-viewer/index.html', 'mascot_registry.py')
    for name in required:
        if name not in entries:
            raise ValueError('Pacote incompleto: ' + name)
    return entries


def build_package(root=ROOT, kind='runtime'):
    entries = collect_files(root, kind)
    manifest = {'application': 'curiolab-3d', 'version': VERSION,
                'kind': kind, 'antivirus_clearance': 'not_established',
                'migration_applied': False, 'voice_api_called': False,
                'files': {name: {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                          for name, data in sorted(entries.items())}}
    entries[MANIFEST] = json.dumps(manifest, ensure_ascii=False, indent=2).encode('utf8')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(entries.items()):
            archive_name = ('curiolab-3d/' if kind == 'skill' else '') + name
            info = zipfile.ZipInfo(archive_name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
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
    parser.add_argument('--output', type=Path)
    parser.add_argument('--kind', choices=['runtime', 'skill'], default='runtime')
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    try:
        if args.verify:
            print(json.dumps(verify_package(args.verify, required=True), ensure_ascii=False))
        else:
            data, manifest = build_package(kind=args.kind)
            filename = FILENAME if args.kind == 'runtime' else 'curiolab-3d-skill-' + VERSION + '.zip'
            output = (args.output or ROOT / 'outputs' / filename).resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            temporary = output.with_name(output.name + '.tmp')
            temporary.write_bytes(data)
            os.replace(temporary, output)
            digest = hashlib.sha256(data).hexdigest()
            output.with_suffix('.sha256').write_text(digest + '  ' + output.name + '\n', encoding='utf8')
            print(json.dumps({'file': str(output), 'bytes': len(data), 'sha256': digest,
                              'files': len(manifest['files']), 'version': VERSION,
                              'kind': args.kind, 'antivirus_clearance': 'not_established'}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
