#!/usr/bin/env python3
"""Diagnóstico local do CurioLab. Não compra, baixa nem instala ferramentas externas."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LINKS = {
    'python': 'https://www.python.org/downloads/',
    'blender': 'https://www.blender.org/download/',
    'ffmpeg': 'https://ffmpeg.org/download.html',
    'ffprobe': 'https://ffmpeg.org/download.html',
}


def candidate_paths(tool, system=None, environ=None):
    """Common locations only; discovery never changes system environment."""
    system = system or platform.system()
    environ = os.environ if environ is None else environ
    candidates = []
    if system == 'Windows':
        program_roots = [Path(value) for key in ('ProgramFiles', 'ProgramFiles(x86)')
                         if (value := environ.get(key))]
        for root in program_roots:
            if tool == 'blender':
                candidates.extend(sorted((root / 'Blender Foundation').glob('Blender */blender.exe'), reverse=True))
            else:
                candidates.extend([root / 'ffmpeg' / 'bin' / (tool + '.exe'), root / 'FFmpeg' / 'bin' / (tool + '.exe')])
        if tool in ('ffmpeg', 'ffprobe'):
            candidates.append(Path('C:/ffmpeg/bin') / (tool + '.exe'))
        local = environ.get('LOCALAPPDATA')
        if local:
            candidates.append(Path(local) / 'Microsoft' / 'WinGet' / 'Links' / (tool + '.exe'))
            if tool in ('ffmpeg', 'ffprobe'):
                packages = Path(local) / 'Microsoft' / 'WinGet' / 'Packages'
                for package in packages.glob('Gyan.FFmpeg*'):
                    candidates.extend(package.glob('ffmpeg*/bin/' + tool + '.exe'))
    elif system == 'Darwin':
        if tool == 'blender':
            candidates.append(Path('/Applications/Blender.app/Contents/MacOS/Blender'))
        candidates.extend(Path(prefix) / tool for prefix in ('/opt/homebrew/bin', '/usr/local/bin', '/usr/bin'))
    else:
        candidates.extend(Path(prefix) / tool for prefix in ('/usr/bin', '/usr/local/bin', '/snap/bin'))
    return candidates


def discover_tool(tool, system=None, environ=None):
    environ = os.environ if environ is None else environ
    found = shutil.which(tool, path=environ.get('PATH', ''))
    if found:
        return str(Path(found).resolve())
    for candidate in candidate_paths(tool, system=system, environ=environ):
        if candidate.is_file():
            return str(candidate.resolve())
    return None


def process_environment(tools, environ=None):
    """Add tool folders to one child process, preserving inherited proxy/CA/auth."""
    env = dict(os.environ if environ is None else environ)
    folders = list(dict.fromkeys(str(Path(value).parent) for value in tools.values() if value))
    env['PATH'] = os.pathsep.join(folders + [env.get('PATH', '')])
    return env


def probe(command, timeout=12):
    try:
        result = subprocess.run(command, capture_output=True, text=True, errors='replace', timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return {'ok': False, 'version': None, 'output': ''}
    output = result.stdout + '\n' + result.stderr
    return {'ok': result.returncode == 0, 'version': next((line.strip() for line in output.splitlines() if line.strip()), '')[:240], 'output': output}


def diagnose():
    tools = {name: discover_tool(name) for name in ('blender', 'ffmpeg', 'ffprobe')}
    checks = []
    checks.append({'id': 'python', 'label': 'Python 3.12 ou superior', 'required_for': 'panel',
                   'ready': sys.version_info >= (3, 12), 'version': platform.python_version(), 'url': LINKS['python']})
    for name in ('blender', 'ffmpeg', 'ffprobe'):
        result = probe([tools[name], '--version' if name == 'blender' else '-version']) if tools[name] else {'ok': False, 'version': None}
        compatible = result['ok']
        if name == 'blender' and result.get('version'):
            match = re.search(r'Blender\s+(\d+)\.(\d+)', result['version'])
            compatible = bool(match and tuple(map(int, match.groups())) >= (4, 3))
        checks.append({'id': name, 'label': name, 'required_for': '3d_render' if name == 'blender' else 'video_export',
                       'ready': compatible, 'path': tools[name], 'version': result.get('version'), 'url': LINKS[name]})
    ffmpeg = tools['ffmpeg']
    encoders = probe([ffmpeg, '-hide_banner', '-encoders']) if ffmpeg else {'ok': False, 'output': ''}
    filters = probe([ffmpeg, '-hide_banner', '-filters']) if ffmpeg else {'ok': False, 'output': ''}
    checks.extend([
        {'id': 'libx264', 'label': 'FFmpeg com codificador H.264 libx264', 'required_for': 'video_export',
         'ready': bool(encoders['ok'] and re.search(r'\blibx264\b', encoders['output'])), 'url': LINKS['ffmpeg']},
        {'id': 'libass', 'label': 'FFmpeg com filtro de legendas ASS', 'required_for': 'video_export',
         'ready': bool(filters['ok'] and re.search(r'\bass\s+V', filters['output'])), 'url': LINKS['ffmpeg']},
    ])
    by_id = {item['id']: item['ready'] for item in checks}
    panel_ready = by_id['python'] and (ROOT / 'app.py').is_file()
    export_ready = panel_ready and all(by_id[k] for k in ('ffmpeg', 'ffprobe', 'libx264', 'libass'))
    return {'application': 'curiolab-3d', 'system': platform.system(), 'panel_ready': panel_ready,
            'image_export_ready': export_ready, 'native_3d_ready': export_ready and by_id['blender'],
            'checks': checks, 'tools': tools,
            'note': 'Credenciais, saldo e acesso às APIs são verificados no painel. O diagnóstico não imprime chaves e não faz chamadas pagas.'}


def install_skill(destination=None, replace=False, agent="codex"):
    """Copy skill with a stable project pointer and preserve an existing install."""
    source = ROOT / 'skills' / 'curiolab-3d'
    if not (source / 'SKILL.md').is_file():
        raise ValueError('A skill não está no pacote. Extraia o pacote completo antes de instalar.')
    if agent not in {'codex','claude'}:raise ValueError('Escolha claude ou codex.')
    if destination is None:
        if agent=='claude':
            destination=Path.home()/'.claude'/'skills'/'curiolab-3d'
        else:
            codex_home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))).expanduser()
            destination = codex_home / 'skills' / 'curiolab-3d'
    target = Path(destination).expanduser()
    if target.is_symlink():
        raise ValueError('O destino é um link simbólico. Escolha um diretório próprio; nada foi substituído.')
    if target.resolve() == source.resolve():
        raise ValueError('O destino já é a skill do pacote. Não é necessário copiar sobre ela.')
    backup = None
    if target.exists():
        if not replace:
            raise ValueError('Já existe uma skill nesse destino. Nada foi alterado. Para atualizar preservando backup, use --replace-skill.')
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        backup = target.with_name(target.name + '.backup-' + stamp)
        # Copy first, then verify basic preservation before replacing the destination.
        if target.is_dir():
            shutil.copytree(target, backup, symlinks=True)
            if sorted(str(p.relative_to(target)) for p in target.rglob('*')) != sorted(str(p.relative_to(backup)) for p in backup.rglob('*')):
                raise ValueError('Não foi possível verificar o backup. Instalação anterior foi preservada.')
            shutil.rmtree(target)
        else:
            shutil.copy2(target, backup)
            if target.read_bytes() != backup.read_bytes():
                raise ValueError('Não foi possível verificar o backup. Instalação anterior foi preservada.')
            target.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)
    # The root file lets the installed skill locate this complete package without
    # modifying shell profiles or replacing HOME/CODEX_HOME.
    (target / 'CURIOLAB_ROOT.txt').write_text(str(ROOT.resolve()) + '\n', encoding='utf8')
    return {'installed': True, 'path': str(target), 'project_root': str(ROOT),
            'backup': str(backup) if backup else None,
            'agent':agent, 'next_step': ('Reabra o Claude Code e use /curiolab-3d.' if agent=='claude' else 'Reabra o Codex e use $curiolab-3d.')+' Abra também a pasta do pacote como projeto; a skill contém CURIOLAB_ROOT.txt com o caminho.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true', help='Saída estruturada, sem valores de credenciais.')
    parser.add_argument('--install-skill', action='store_true')
    parser.add_argument('--agent',choices=['codex','claude'],default='codex',help='Assistente em que a skill será instalada.')
    parser.add_argument('--replace-skill', action='store_true', help='Preserva backup antes de atualizar uma skill existente.')
    parser.add_argument('--skill-destination', type=Path, help='Destino da skill; padrão: pasta de skills do Codex.')
    args = parser.parse_args()
    if args.replace_skill and not args.install_skill:
        parser.error('--replace-skill exige --install-skill.')
    result = diagnose()
    if args.install_skill:
        try:
            result['skill_installation'] = install_skill(args.skill_destination, replace=args.replace_skill,agent=args.agent)
        except (ValueError, OSError) as exc:
            result['skill_installation'] = {'installed': False, 'error': str(exc)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print('CurioLab 3D — diagnóstico local')
        for check in result['checks']:
            print(('OK   ' if check['ready'] else 'FALTA') + ' · ' + check['label'] + (' · ' + check['version'] if check.get('version') else ''))
            if not check['ready']:
                print('      Instalação oficial: ' + check['url'])
        print('Painel: ' + ('pode abrir' if result['panel_ready'] else 'requer Python/pacote completo'))
        print('Exportação de imagens: ' + ('pronta' if result['image_export_ready'] else 'há requisitos pendentes'))
        print('Render 3D nativo: ' + ('pronto' if result['native_3d_ready'] else 'há requisitos pendentes'))
        if 'skill_installation' in result:
            print(json.dumps(result['skill_installation'], ensure_ascii=False, indent=2))
    return 0 if result['panel_ready'] and result.get('skill_installation', {}).get('installed', True) else 1


if __name__ == '__main__':
    raise SystemExit(main())
