#!/usr/bin/env python3
"""Open the local CurioLab panel without changing global machine settings."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

from doctor import ROOT, diagnose, process_environment


def own_server(port, timeout=.7):
    # This bypass applies only to an explicit loopback URL, never public APIs.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f'http://127.0.0.1:{port}/api/status', timeout=timeout) as response:
            data = json.load(response)
        return data.get('application') == 'curiolab-3d'
    except (OSError, ValueError, urllib.error.URLError):
        return False


def free_port(start, attempts=20):
    for port in range(start, min(65536, start + attempts)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(('127.0.0.1', port))
            except OSError:
                continue
            return port
    raise OSError('Não há porta local disponível no intervalo. Feche outra instância ou escolha --port.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--no-browser', action='store_true', help='Inicia o painel sem abrir navegador automaticamente.')
    parser.add_argument('--check-only', action='store_true', help='Verifica dependências sem iniciar processos.')
    args = parser.parse_args()
    if not 1024 <= args.port <= 65515:
        parser.error('--port deve ficar entre 1024 e 65515.')
    status = diagnose()
    if args.check_only:
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 0 if status['panel_ready'] else 1
    if not status['panel_ready']:
        print('Instale Python 3.12+ e extraia o pacote completo. Consulte docs/INSTALACAO.md.', file=sys.stderr)
        return 1
    if own_server(args.port):
        url = f'http://127.0.0.1:{args.port}/'
        print('Painel CurioLab já aberto nesta máquina. Reutilizando a instância existente.')
        if not args.no_browser:
            webbrowser.open(url)
        return 0
    try:
        port = free_port(args.port)
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    directory = ROOT / '.local' / 'logs'
    directory.mkdir(parents=True, exist_ok=True)
    log = directory / 'panel.log'
    env = process_environment(status['tools'])
    with log.open('a', encoding='utf8') as stream:
        process = subprocess.Popen([sys.executable, str(ROOT / 'app.py'), '--host', '127.0.0.1', '--port', str(port)],
                                   cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline and process.poll() is None:
        if own_server(port):
            break
        time.sleep(.2)
    else:
        if process.poll() is None:
            process.terminate()
        print('O painel não ficou pronto. Consulte .local/logs/panel.log e docs/INSTALACAO.md.', file=sys.stderr)
        return 1
    url = f'http://127.0.0.1:{port}/'
    print('CurioLab iniciado. Mantenha esta janela aberta enquanto usar o painel.', flush=True)
    if not status['native_3d_ready']:
        print('O painel abriu, mas ainda há dependências para render. Veja o diagnóstico em Comece aqui.', flush=True)
    if not args.no_browser:
        opened = webbrowser.open(url)
        if not opened:
            print('O navegador não abriu automaticamente. O endereço está no arquivo .local/panel-address.txt.', flush=True)
    (ROOT / '.local' / 'panel-address.txt').write_text(url + '\n', encoding='utf8')
    try:
        return process.wait()
    except KeyboardInterrupt:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
