#!/usr/bin/env python3
"""Exercise an installed package: HTTP, request, native Full HD render and gallery."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
import urllib.request
import uuid
from http.server import ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from doctor import diagnose, process_environment
from package_skill import verify_package


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-nico', action='store_true', help='Also capture a new candidate NICO clip; requires Playwright/Chromium.')
    args = parser.parse_args(argv)
    run_id = uuid.uuid4().hex
    directory = ROOT / '.local/smoke' / run_id
    directory.mkdir(parents=True)
    report = {'run_id': run_id, 'application': 'curiolab-3d', 'status': 'running',
              'paid_api_called': False, 'sql_migration_applied': False, 'checks': {}}
    server = None
    try:
        report['package'] = verify_package(ROOT)
        status = diagnose()
        if not status['native_3d_ready']:
            raise ValueError('Teste requer Python 3.12+, Blender 4.3+, FFmpeg/libx264/libass e ffprobe. Execute tools/doctor.py.')
        env = process_environment(status['tools'])
        import app
        from mascot_registry import MascotRegistry
        class QuietHandler(app.Handler):
            def log_message(self, *values):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = 'http://127.0.0.1:' + str(server.server_port)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        def request(path, body=None, binary=False):
            data = json.dumps(body).encode('utf8') if body is not None else None
            req = urllib.request.Request(base + path, data=data, headers={'Content-Type': 'application/json'})
            with opener.open(req, timeout=30) as response:
                value = response.read()
                return (value, response.headers.get_content_type()) if binary else json.loads(value)

        assert request('/api/status')['application'] == 'curiolab-3d'
        html, content_type = request('/', binary=True)
        assert content_type == 'text/html' and b'page-inicio' in html
        report['checks']['panel_http'] = True
        viewer, content_type = request('/mascot-viewer/', binary=True)
        assert content_type == 'text/html' and b'<div id="root"' in viewer
        catalog = request('/api/mascots')
        assert any(item['id'] == 'nico' for item in catalog['mascots'])
        registry = MascotRegistry(ROOT)
        pin = registry.pin('nico', '1.0.0-candidate.1', require_approved=False)
        glb, _ = request('/mascot-assets/nico/1.0.0-candidate.1/nico.glb', binary=True)
        assert glb[:4] == b'glTF'
        report['checks']['nico_versioned_assets'] = True
        report['nico_pin'] = pin

        def execute(arguments, log_name):
            print('Teste: ' + log_name, flush=True)
            with (directory / log_name).open('w', encoding='utf8') as log:
                subprocess.run([sys.executable, *arguments], cwd=ROOT, env=env,
                               stdout=log, stderr=subprocess.STDOUT, check=True)

        item = request('/api/requests', {'prompt': 'Teste técnico de instalação: montagem de casa, 3 segundos, sem voz. Não publicar.'})
        ident = item['id']
        report['request_id'] = ident
        execute(['tools/process_request.py', '--root', str(ROOT), '--start', ident], 'start.log')
        project = json.loads((ROOT / 'engine/house_demo.json').read_text(encoding='utf8'))
        project.update(title='Nicolume · teste técnico da instalação', duration=3,
                       captions=[{'start': 0, 'end': 1, 'text': 'TESTE DA INSTALAÇÃO'},
                                 {'start': 1, 'end': 2, 'text': 'CADA PEÇA TEM UMA FUNÇÃO'},
                                 {'start': 2, 'end': 3, 'text': 'PRÉVIA TÉCNICA SEM VOZ'}],
                       branding=item['channel'])
        project_path = directory / 'render-project.json'
        project_path.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding='utf8')
        output = ROOT / 'outputs' / (ident + '.mp4')
        execute(['engine/render.py', '--project', str(project_path), '--output', str(output), '--full-hd'], 'render.log')
        metadata_path = directory / 'metadata.json'
        metadata_path.write_text(json.dumps({'title': project['title'], 'script': 'Teste técnico sem narração; não é um episódio publicado.',
                                            'mode': 'native_3d', 'review_notes': 'Teste de instalação: sem API paga, sem publicação e sem revisão editorial.'},
                                           ensure_ascii=False, indent=2), encoding='utf8')
        execute(['tools/process_request.py', '--root', str(ROOT), '--complete', ident,
                 '--video', str(output), '--metadata', str(metadata_path)], 'complete.log')
        stored = json.loads((ROOT / '.local/requests' / ident / 'request.json').read_text(encoding='utf8'))
        assert stored['status'] == 'completed'
        assert any(video['id'] == ident for video in request('/api/videos')['videos'])
        payload = subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(output)], env=env, text=True)
        streams = json.loads(payload)['streams']
        stream = next(value for value in streams if value['codec_type'] == 'video')
        assert (stream['width'], stream['height'], stream['r_frame_rate']) == (1080, 1920, '30/1')
        report['checks'].update(request_lifecycle=True, native_full_hd=True, complete_decode=True, gallery=True)
        report['video'] = {'path': str(output), 'width': 1080, 'height': 1920, 'fps': 30,
                           'duration': 3, 'silent': not any(value['codec_type'] == 'audio' for value in streams),
                           'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}
        if args.with_nico:
            nico_output = ROOT / 'outputs' / ('nico-install-test-' + run_id + '.mp4')
            execute(['tools/render_mascot_video.py', '--mascot', 'nico', '--version', pin['version'],
                     '--animation', 'wave', '--duration', '1', '--preview', '--base-url', base,
                     '--output', str(nico_output)], 'nico.log')
            subprocess.run(['ffmpeg', '-v', 'error', '-i', str(nico_output), '-f', 'null', '-'], env=env, check=True)
            report['checks']['nico_candidate_capture'] = True
            report['nico_candidate_video'] = str(nico_output)
        report['status'] = 'passed'
        report['editorial_review_pending'] = True
        print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
        return 0
    except (OSError, ValueError, KeyError, AssertionError, subprocess.CalledProcessError) as error:
        report.update(status='failed', error=str(error))
        print('Teste interrompido: ' + str(error) + '. Logs: ' + str(directory), file=sys.stderr)
        return 1
    finally:
        report['finished_at'] = time.time()
        (directory / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
        if server:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    raise SystemExit(main())
