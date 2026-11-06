#!/usr/bin/env python3
"""Install the complete CurioLab skill for a project or a user's assistant."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from doctor import ROOT, diagnose, install_skill, process_environment
from package_skill import verify_package


def project_target(root, agent):
    return Path(root) / ('.agents' if agent == 'codex' else '.claude') / 'skills' / 'curiolab-3d'


def matches_installation(source, target, root):
    pointer = target / 'CURIOLAB_ROOT.txt'
    if not target.is_dir() or target.is_symlink() or not pointer.is_file():
        return False
    if pointer.read_text(encoding='utf8').strip() != str(root.resolve()):
        return False
    expected = {p.relative_to(source).as_posix(): p.read_bytes() for p in source.rglob('*') if p.is_file()}
    actual = {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob('*')
              if p.is_file() and p.name != 'CURIOLAB_ROOT.txt'}
    return expected == actual


def install(agent, scope='project', replace=False):
    source = ROOT / 'skills/curiolab-3d'
    target = project_target(ROOT, agent) if scope == 'project' else None
    if target is None:
        target = ((Path.home() / '.claude') if agent == 'claude' else
                  Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))).expanduser() / 'skills/curiolab-3d'
    if matches_installation(source, target, ROOT):
        return {'installed': True, 'unchanged': True, 'agent': agent, 'scope': scope,
                'path': str(target), 'project_root': str(ROOT)}
    result = install_skill(target, replace=replace, agent=agent)
    return {**result, 'unchanged': False, 'scope': scope}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent', choices=['codex', 'claude', 'both'], default='both')
    parser.add_argument('--scope', choices=['project', 'user'], default='project')
    parser.add_argument('--replace', action='store_true', help='Preserve backup before updating a different existing skill.')
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--test', action='store_true', help='Produce and verify a new Full HD MP4 without paid APIs.')
    args = parser.parse_args(argv)
    try:
        package = verify_package(ROOT)
        status = diagnose()
        if not status['panel_ready']:
            raise ValueError('Instale Python 3.12+ e extraia o pacote completo. Leia docs/INSTALACAO.md.')
        result = {'application': 'curiolab-3d', 'package': package, 'project_root': str(ROOT),
                  'panel_ready': status['panel_ready'], 'native_3d_ready': status['native_3d_ready'],
                  'migration_applied': False, 'paid_api_called': False, 'installations': []}
        if not args.check_only:
            for agent in (['codex', 'claude'] if args.agent == 'both' else [args.agent]):
                result['installations'].append(install(agent, args.scope, args.replace))
        if args.test:
            if not status['native_3d_ready']:
                raise ValueError('Skill instalada, mas o teste 3D requer Blender 4.3+, FFmpeg e ffprobe. Execute tools/doctor.py.')
            subprocess.run([sys.executable, str(ROOT / 'tools/smoke_skill.py')], cwd=ROOT,
                           env=process_environment(status['tools']), check=True)
            result['smoke_test'] = 'passed'
        if result['installations']:
            receipt = ROOT / '.local/installations/last-install.json'
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print('\nAbra esta pasta no assistente e inicie uma nova sessão. Codex: $curiolab-3d · Claude Code: /curiolab-3d')
        print('Painel: python tools/launch_panel.py · teste: python tools/smoke_skill.py')
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print('Instalação/teste não concluído: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
