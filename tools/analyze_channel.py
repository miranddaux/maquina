#!/usr/bin/env python3
"""Bounded reference acquisition. Metadata only unless --download is explicit."""
import argparse
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urlparse

TARGET = 'https://www.youtube.com/shorts/P337IKPsixQ'
CHANNEL = 'https://www.youtube.com/@DesmontandoOMundo/shorts'
ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['id', 'url', 'title', 'channel', 'duration_seconds', 'views', 'likes',
          'upload_date', 'collected_at_utc', 'download_status', 'download_path']


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def metric(value):
    """Keep missing counters missing; reject booleans, NaN and invented estimates."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value) or value < 0 or int(value) != value:
        return None
    return int(value)


def duration(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(value) and value >= 0 else None


def youtube_url(value):
    parsed = urlparse(value)
    if parsed.scheme != 'https' or parsed.hostname not in {'www.youtube.com', 'youtube.com', 'youtu.be'}:
        raise ValueError('Use uma URL HTTPS pública do YouTube.')
    if parsed.username or parsed.password or parsed.port:
        raise ValueError('A URL não pode conter credenciais ou porta personalizada.')
    return value


def video_url(item):
    video_id = item.get('id')
    return ('https://www.youtube.com/watch?v=' + video_id
            if isinstance(video_id, str) and re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id) else None)


def normalize(item):
    if not video_url(item):
        raise ValueError('Metadados sem identificador de vídeo válido.')
    return {
        'id': item['id'], 'url': video_url(item), 'title': str(item.get('title') or ''),
        'channel': str(item.get('channel') or item.get('uploader') or ''),
        'duration_seconds': duration(item.get('duration')),
        'views': metric(item.get('view_count')), 'likes': metric(item.get('like_count')),
        'upload_date': item.get('upload_date') if re.fullmatch(r'\d{8}', str(item.get('upload_date'))) else None,
        'collected_at_utc': utc_now(), 'download_status': 'not_requested', 'download_path': None,
        'caption_languages': sorted(set(item.get('subtitles') or {}) | set(item.get('automatic_captions') or {})),
    }


def safe_cell(value):
    # Prevent spreadsheet formula injection from untrusted titles/channel names.
    if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + value
    return '' if value is None else value


def failure_category(stderr):
    text = stderr.lower()
    if any(x in text for x in ('403', 'blocked', 'denied', 'forbidden')):
        return 'access_denied'
    if any(x in text for x in ('sign in', 'confirm you', 'bot', 'cookies')):
        return 'authentication_or_bot_check'
    if any(x in text for x in ('proxy', 'connection', 'network', 'resolve', 'timed out')):
        return 'network_failure'
    if 'unavailable' in text or 'private video' in text:
        return 'video_unavailable'
    return 'extractor_or_download_failure'


class Collector:
    def __init__(self, executable, timeout):
        self.executable = executable
        self.timeout = timeout
        self.attempts = []

    def call(self, args, operation, url):
        record = {'operation': operation, 'url': url, 'attempted_at_utc': utc_now()}
        self.attempts.append(record)
        try:
            result = subprocess.run([self.executable, '--ignore-config', '--no-progress',
                                     '--retries', '1', '--socket-timeout', '15', *args, url],
                                    capture_output=True, text=True, timeout=self.timeout)
        except subprocess.TimeoutExpired:
            record.update(status='failed', error_category='timeout')
            return None
        except OSError:
            record.update(status='failed', error_category='executable_unavailable')
            return None
        record['exit_code'] = result.returncode
        if result.returncode:
            record.update(status='failed', error_category=failure_category(result.stderr))
            return None
        record['status'] = 'succeeded'
        return result.stdout

    def metadata(self, url, playlist_limit=None):
        args = ['--skip-download', '--dump-single-json']
        args += ['--flat-playlist', '--playlist-end', str(playlist_limit)] if playlist_limit else ['--no-playlist']
        output = self.call(args, 'channel_metadata' if playlist_limit else 'video_metadata', url)
        if output is None:
            return None
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            self.attempts[-1].update(status='failed', error_category='invalid_metadata_json')
            return None

    def download(self, item, directory):
        destination = directory / (item['id'] + '.%(ext)s')
        output = self.call(['--no-playlist', '--no-write-info-json', '--no-write-thumbnail',
                            '-f', 'bv*[height<=720]+ba/b[height<=720]', '--merge-output-format', 'mp4',
                            '--print', 'after_move:filepath', '-o', str(destination)],
                           'video_download', item['url'])
        if output is None:
            item['download_status'] = 'failed'
            return
        paths = [Path(line.strip()).resolve() for line in output.splitlines() if line.strip()]
        files = [p for p in paths if p.is_relative_to(directory.resolve()) and p.is_file() and p.stat().st_size > 0]
        if not files:
            item['download_status'] = 'failed'
            self.attempts[-1].update(status='failed', error_category='output_file_not_verified')
            return
        item.update(download_status='downloaded', download_path=str(files[-1]))


def write_results(directory, payload):
    (directory / 'metadata.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (directory / 'metrics.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for item in payload['videos']:
            writer.writerow({key: safe_cell(item.get(key)) for key in FIELDS})
    mode = 'FIXTURE LOCAL: não representa observação do YouTube.' if payload['source'] == 'fixture' else 'Coleta via yt-dlp; métricas são uma fotografia do momento da extração.'
    lines = ['# Referências: resultado observado', '', mode, '',
             'Coleta UTC: ' + payload['collected_at_utc'], '',
             f"Vídeos com metadados: {len(payload['videos'])}. Tentativas com falha: {sum(a['status'] == 'failed' for a in payload['attempts'])}.", '',
             '| Vídeo | Duração (s) | Views | Likes | Download |', '| --- | ---: | ---: | ---: | --- |']
    display = lambda x: 'não disponível' if x is None else str(x)
    for item in payload['videos']:
        lines.append(f"| {item['id']} | {display(item['duration_seconds'])} | {display(item['views'])} | {display(item['likes'])} | {item['download_status']} |")
    lines += ['', 'Contadores ausentes continuam nulos no JSON e vazios no CSV; não representam zero. Não há consulta de métricas privadas do Studio.', '',
              'Não foi feita inferência sobre modelos de IA, ferramentas, prompts, custo ou autoria. Download e leitura de metadados não demonstram inspeção visual ou transcrição.', '',
              '## Timeline a preencher após inspeção', '',
              '| Intervalo | Evidência visual/sonora observada | Função narrativa | Confiança |',
              '| --- | --- | --- | --- |', '| A preencher | Inspeção ainda não realizada por este analisador | A preencher | Pendente |', '',
              'Não inclui transcrição integral de terceiros. Para marcações por palavra, usar áudio autorizado e um alinhador/transcritor real; não derivar tempos de palavras pela duração do vídeo.']
    (directory / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', default=TARGET, type=youtube_url)
    parser.add_argument('--channel', default=CHANNEL, type=youtube_url)
    parser.add_argument('--limit', type=int, default=8, help='Número de Shorts do canal, entre 1 e 8; alvo adicional deduplicado.')
    parser.add_argument('--yt-dlp', default=str(ROOT / '.local/tools/bin/yt-dlp'))
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/references')
    parser.add_argument('--timeout', type=int, default=60, help='Segundos máximos por operação.')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--metadata-only', action='store_true', help='Padrão: não baixa vídeo ou legendas.')
    modes.add_argument('--download', action='store_true', help='Baixa vídeos autorizados para análise local, até 720p.')
    parser.add_argument('--fixture', type=Path, help='JSON local para testar formato sem rede; resultados marcados como fixture.')
    args = parser.parse_args()
    if not 1 <= args.limit <= 8:
        parser.error('--limit deve estar entre 1 e 8.')
    if not 1 <= args.timeout <= 600:
        parser.error('--timeout deve estar entre 1 e 600.')
    if args.fixture and args.download:
        parser.error('--fixture não pode baixar vídeos.')
    if not args.fixture and not (Path(args.yt_dlp).is_file() or shutil.which(args.yt_dlp)):
        parser.error('yt-dlp não encontrado; instale-o ou indique --yt-dlp.')
    directory = args.output.resolve() / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    directory.mkdir(parents=True, exist_ok=False)
    collector = Collector(args.yt_dlp, args.timeout)
    videos = {}

    def add_video(raw, url):
        try:
            item = normalize(raw)
        except (ValueError, TypeError, AttributeError):
            collector.attempts.append({'operation': 'normalize_metadata', 'url': url,
                                       'attempted_at_utc': utc_now(), 'status': 'failed',
                                       'error_category': 'invalid_video_metadata'})
            return
        videos[item['id']] = item

    if args.fixture:
        fixture = json.loads(args.fixture.read_text(encoding='utf-8'))
        entries = fixture if isinstance(fixture, list) else fixture.get('entries', [fixture])
        for raw in entries[:args.limit + 1]:
            add_video(raw, 'local_fixture')
    else:
        target = collector.metadata(args.target)
        if target:
            add_video(target, args.target)
        channel = collector.metadata(args.channel, args.limit)
        if channel:
            for raw in (channel.get('entries') or [])[:args.limit]:
                url = video_url(raw)
                if not url or raw['id'] in videos:
                    continue
                data = collector.metadata(url)
                if data:
                    add_video(data, url)
        if args.download:
            for item in videos.values():
                collector.download(item, directory)
    payload = {'source': 'fixture' if args.fixture else 'youtube', 'collected_at_utc': utc_now(),
               'requested_target': args.target, 'requested_channel': args.channel, 'channel_limit': args.limit,
               'download_requested': args.download, 'videos': list(videos.values()), 'attempts': collector.attempts}
    write_results(directory, payload)
    print(json.dumps({'output': str(directory), 'videos': len(videos),
                      'failed_attempts': sum(a['status'] == 'failed' for a in collector.attempts),
                      'source': payload['source']}, ensure_ascii=False))
    return 1 if not videos or any(a['status'] == 'failed' for a in collector.attempts) else 0


if __name__ == '__main__':
    sys.exit(main())
