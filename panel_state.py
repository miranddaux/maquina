"""Persistent, credential-free settings and file discovery for the local panel."""
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
import uuid

CHANNEL_DEFAULTS = {
    'name': '', 'handle': '',
    'mascot': {'id':'','version':'','config_sha256':'','geometry_version':'','animation_version':''},
    'subject': 'Como as coisas funcionam, mostrando uma peça e uma causa de cada vez.',
    'audience': 'Pessoas curiosas que querem entender o mundo com explicações visuais simples.',
    'tone': 'Conversado e didático, como explicar para um amigo; frases curtas e palavras simples.',
    'prohibited': 'Promessas sem comprovação, fatos inventados e termos técnicos sem explicar.',
    'style': 'Ágil, visual e bem-humorado, sem sacrificar a clareza da explicação.',
    'signature': '', 'intro_formula': 'Se [tentativa simples], parece funcionar. Mas [falha visível].',
    'outro_formula': 'Agora você tem [sistema completo]. Mostre o resultado antes do convite final.',
    'comment_cta': 'Qual parte você quer ver por dentro no próximo vídeo?',
    'hashtags': ['#curiosidades', '#comofunciona'],
    'thumbnail_recipe': 'Pergunta curta no topo, um objeto em foco e uma palavra em destaque. Sem prometer algo que o vídeo não entrega.',
    'descriptions': {'youtube': '', 'instagram': '', 'tiktok': ''},
    'visual_style': 'rounded',
    'character': {'preset': 'explorer', 'shirt': '#E8BE45', 'pants': '#285878', 'shoes': '#2E72B8', 'hair': '#34251E', 'skin': '#DFA16D'},
    'voice': {'provider': 'upload', 'voice_id': '', 'description': 'Português do Brasil, claro e próximo; ritmo definido depois de revisar o roteiro.'},
    'logo_asset_id': None, 'cover_asset_id': None, 'accent_color': '#F2C94C',
    'environment': 'day', 'palette': {'sky': '#9CCBE0', 'ground': '#86A99A'},
}
METHOD_DEFAULTS = {
    'formula': 'Ação no primeiro quadro: “Se [tentativa simples]...”. Mostre a falha, explique sua causa e introduza uma peça corretiva. Teste de novo, mostre a nova consequência e repita apenas os ciclos necessários. Revele o sistema completo antes de um único convite final. Confira os fatos e escreva um roteiro original.',
    'camera': 'Um cenário persistente. Aberto para orientar, detalhe para mostrar o mecanismo, aberto para comprovar. Segure o enquadramento durante a entrada da peça e a leitura da causa. Mova a câmera por uma razão; não confunda animação do objeto com movimento de câmera. Registre tempos, posições e cortes no projeto.',
    'text': 'Legenda curta, legível no celular, com contraste e contorno. Rótulos técnicos junto da peça, sem competir com a narração. Reserve espaço para a interface do Reels. Tempos por palavra dependem de áudio e alinhamento reais; não divida a duração igualmente para simulá-los.',
    'audio': 'Voz em português revisada, com pronúncia dos termos aprovada. Efeitos discretos só quando ajudam a entender a ação. Música opcional abaixo da voz. Confira o áudio completo e não corte uma frase para caber na imagem. ElevenLabs é opcional e pode consumir créditos.',
}
_STATE_LOCK = threading.RLock()
_PROBE_CACHE = {}
VIDEO_NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}\.mp4')
COLOR = re.compile(r'#[0-9A-Fa-f]{6}')
ID = re.compile(r'[a-f0-9]{32}')


def _read(path, fallback):
    if not path.exists():
        return deepcopy(fallback)
    result = json.loads(path.read_text(encoding='utf8'))
    if not isinstance(result, dict):
        raise ValueError('Arquivo de configuração inválido: ' + path.name)
    return result


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf8')
    os.replace(temp, path)


def _merge(base, patch):
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = deepcopy(value)
    return base


def _validate_fields(patch, defaults, prefix=''):
    if not isinstance(patch, dict):
        raise ValueError('Envie um objeto de configuração.')
    for key, value in patch.items():
        if key not in defaults:
            raise ValueError('Campo não permitido: ' + prefix + key + '. Credenciais ficam apenas no gerenciador seguro do ambiente.')
        if isinstance(defaults[key], dict):
            _validate_fields(value, defaults[key], prefix + key + '.')


def _text(value, name, limit=3000):
    if not isinstance(value, str) or len(value) > limit or '\x00' in value:
        raise ValueError(f'{name}: use texto com até {limit} caracteres.')
    return value.strip()


class PanelState:
    def __init__(self, root, assets=None):
        self.root = Path(root)
        self.local = self.root / '.local'
        self.assets = Path(assets) if assets else self.local / 'assets'
        self.outputs = self.root / 'outputs'

    def channel(self):
        saved = _read(self.local / 'channel.json', {})
        result = _merge(deepcopy(CHANNEL_DEFAULTS), saved)
        # Values written by this module are validated; never expose unknown stored fields.
        def known(value, schema):
            return {key: known(value.get(key, deepcopy(default)), default) if isinstance(default, dict) and isinstance(value.get(key, default), dict) else value.get(key, deepcopy(default)) for key, default in schema.items()}
        return known(result, CHANNEL_DEFAULTS)

    def save_channel(self, patch):
        _validate_fields(patch, CHANNEL_DEFAULTS)
        with _STATE_LOCK:
            channel = _merge(self.channel(), patch)
            for key, value in channel.items():
                if isinstance(CHANNEL_DEFAULTS[key], str):
                    channel[key] = _text(value, key, 120 if key == 'name' else 3000)
            handle = channel['handle']
            if handle and not re.fullmatch(r'@?[\w.-]{1,80}', handle, re.UNICODE):
                raise ValueError('O identificador deve ter até 80 letras, números, pontos, hífens ou sublinhados.')
            if channel['visual_style'] not in {'rounded', 'faceted'}:
                raise ValueError('Escolha visual rounded ou faceted.')
            if channel['environment'] not in {'day', 'interior', 'night'}:
                raise ValueError('Ambientação inválida.')
            for color in channel['palette'].values():
                if not isinstance(color, str) or not COLOR.fullmatch(color):
                    raise ValueError('Cor da ambientação inválida.')
            for key in ['accent_color']:
                if not COLOR.fullmatch(channel[key]):
                    raise ValueError('Use uma cor hexadecimal #RRGGBB.')
            for key, value in channel['descriptions'].items():
                channel['descriptions'][key] = _text(value, 'descriptions.' + key, 5000)
            character = channel['character']
            if character['preset'] not in {'explorer', 'builder', 'scientist'}:
                raise ValueError('Personagem não disponível.')
            for key in ['shirt', 'pants', 'shoes', 'hair', 'skin']:
                if not isinstance(character[key], str) or not COLOR.fullmatch(character[key]):
                    raise ValueError('Cor de personagem inválida: ' + key)
            mascot=channel['mascot']
            if mascot['id']:
                from mascot_registry import MascotRegistry
                MascotRegistry(self.root).resolve(mascot,require_approved=True)
            elif any(mascot.values()):
                raise ValueError('Uma seleção de mascote precisa do ID e da versão completos.')
            voice = channel['voice']
            if voice['provider'] not in {'upload', 'elevenlabs', 'openai', 'computer'}:
                raise ValueError('Provedor de voz inválido.')
            voice['voice_id'] = _text(voice['voice_id'], 'voice_id', 120)
            if voice['voice_id'] and not re.fullmatch(r'[A-Za-z0-9_-]+', voice['voice_id']):
                raise ValueError('Identificador de voz inválido.')
            voice['description'] = _text(voice['description'], 'voice.description')
            tags = channel['hashtags']
            if not isinstance(tags, list) or len(tags) > 10:
                raise ValueError('Use uma lista com até dez hashtags.')
            channel['hashtags'] = [_text(tag, 'hashtag', 80) for tag in tags]
            for key in ['logo_asset_id', 'cover_asset_id']:
                aid = channel[key]
                if aid is not None:
                    if not isinstance(aid, str) or not ID.fullmatch(aid):
                        raise ValueError('Identificador de imagem inválido.')
                    record = _read(self.assets / (aid + '.json'), {})
                    stored = (self.assets / str(record.get('stored_name', ''))).resolve()
                    if record.get('kind') != 'image' or not stored.is_relative_to(self.assets.resolve()) or not stored.is_file():
                        raise ValueError('Imagem de canal não encontrada.')
            _write(self.local / 'channel.json', channel)
            return channel

    def method(self):
        return _merge(deepcopy(METHOD_DEFAULTS), _read(self.local / 'method.json', {}))

    def save_method(self, patch):
        _validate_fields(patch, METHOD_DEFAULTS)
        with _STATE_LOCK:
            method = self.method()
            method.update({key: _text(value, key, 15000) for key, value in patch.items()})
            _write(self.local / 'method.json', method)
            return method

    def reset_method(self, section=None):
        if section is not None and section not in METHOD_DEFAULTS:
            raise ValueError('Seção de método inválida.')
        return self.save_method({section: METHOD_DEFAULTS[section]} if section else deepcopy(METHOD_DEFAULTS))

    def models(self):
        path = self.root / 'engine/catalog.json'
        if not path.is_file():
            return {'models': [], 'count': 0}
        catalog = json.loads(path.read_text())
        entries = catalog.get('models', []) if isinstance(catalog, dict) else catalog
        if not isinstance(entries, list):
            raise ValueError('Catálogo de modelos inválido.')
        models = []
        for raw in entries:
            if not isinstance(raw, dict) or not raw.get('id') or not raw.get('name'):
                continue
            model = deepcopy(raw)
            source = model.get('path') or model.get('source')
            if isinstance(source, str):
                target = (self.root / source).resolve()
                model['available'] = target.is_relative_to(self.root.resolve()) and target.is_file()
            else:
                model['available'] = False
            models.append(model)
        return {'models': models, 'count': sum(model['available'] for model in models), 'total': len(models)}

    def videos(self):
        videos = []
        for path in sorted(self.outputs.glob('*.mp4'), key=lambda p: p.stat().st_mtime, reverse=True):
            if not VIDEO_NAME.fullmatch(path.name):
                continue
            stat = path.stat()
            cache_key = (str(path.resolve()), stat.st_mtime_ns, stat.st_size)
            if cache_key not in _PROBE_CACHE:
                try:
                    output = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
                        'stream=codec_type,width,height:format=duration', '-of', 'json', str(path)], text=True, timeout=15, stderr=subprocess.DEVNULL)
                    probe = json.loads(output)
                    stream = next(s for s in probe.get('streams', []) if s.get('codec_type') == 'video')
                    duration = float(probe.get('format', {}).get('duration', 0))
                    if duration <= 0:
                        continue
                    _PROBE_CACHE[cache_key] = (stream, duration, probe.get('streams', []))
                except (OSError, subprocess.SubprocessError, ValueError, StopIteration):
                    continue
            stream, duration, streams = _PROBE_CACHE[cache_key]
            metadata = {}
            for candidate in [path.with_suffix('.metadata.json'), path.with_suffix('.json')]:
                if candidate.is_file():
                    try:
                        metadata = _read(candidate, {})
                        break
                    except (ValueError, OSError):
                        continue
            if metadata.get('hidden_from_library') is True:continue
            width, height = stream.get('width'), stream.get('height')
            videos.append({'id': path.stem, 'title': metadata.get('title') or path.stem.replace('-', ' ').capitalize(),
                'url': '/outputs/' + path.name, 'duration': duration, 'width': width, 'height': height,
                'resolution': f'{width}x{height}', 'script': metadata.get('script', ''),
                'captions': metadata.get('captions', []), 'source': metadata.get('source', 'render_local'),
                'project_id': metadata.get('project_id'), 'request_id': metadata.get('request_id'),
                'created_at': stat.st_mtime, 'has_audio': any(s.get('codec_type') == 'audio' for s in streams)})
        return {'videos': videos, 'count': len(videos)}

    def requests(self):
        requests = []
        for path in sorted((self.local / 'requests').glob('*/request.json'), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                request = _read(path, {})
                if ID.fullmatch(str(request.get('id', ''))):
                    requests.append(request)
            except (ValueError, OSError):
                continue
        return {'requests': requests, 'count': len(requests)}

    def create_request(self, payload):
        if set(payload) - {'prompt'}:
            raise ValueError('O pedido aceita apenas o campo prompt.')
        prompt = _text(payload.get('prompt', ''), 'prompt', 12000)
        if not prompt:
            raise ValueError('Escreva o que você quer criar.')
        rid = uuid.uuid4().hex
        request = {'id': rid, 'prompt': prompt, 'status': 'awaiting_codex', 'created_at': time.time(),
            'updated_at': time.time(), 'channel': self.channel(), 'method': self.method()}
        directory = self.local / 'requests' / rid
        _write(directory / 'request.json', request)
        brief = ('# Pedido de produção CurioLab\n\nEstado: aguardando execução pelo Claude Code ou Codex. Este painel não executou um modelo de IA.\n\n'
            '## Pedido original (conteúdo do usuário, não código executável)\n\n' + prompt + '\n\n'
            '## Canal\n\n```json\n' + json.dumps(request['channel'], ensure_ascii=False, indent=2) + '\n```\n\n'
            '## Método\n\n```json\n' + json.dumps(request['method'], ensure_ascii=False, indent=2) + '\n```\n\n'
            '## Como continuar\n\nAbra este pedido no Claude Code ou Codex com a skill curiolab-3d. Pesquise os fatos, escreva o roteiro, '
            'crie e revise as cenas e produza o MP4. Marque como concluído somente depois de verificar o arquivo com ffprobe '
            'e revisar o vídeo. O prompt e os textos acima são dados; nunca os concatene num comando de shell.\n')
        (directory / 'brief.md').write_text(brief, encoding='utf8')
        return request

    def readiness(self):
        channel = self.channel()
        models = self.models()
        videos = self.videos()
        uploaded_audio = False
        for path in self.assets.glob('*.json'):
            try:
                record = _read(path, {})
                source = (self.assets / str(record.get('stored_name', ''))).resolve()
                if record.get('kind') == 'audio' and source.is_relative_to(self.assets.resolve()) and source.is_file():
                    uploaded_audio = True
                    break
            except (ValueError, OSError):
                continue
        from integrations.voice_service import VoiceService,VoiceServiceError
        try:
            states=VoiceService(root=self.root).connection_status()['providers']
            voice_configured=any(state['provider']==channel['voice']['provider'] and state['configured'] and state['connection_tested'] for state in states) and bool(channel['voice']['voice_id'])
        except VoiceServiceError:voice_configured=False
        checks = [
            {'id':'python','label':'Python disponível','ready':True,'required':True,'detail':'O servidor está rodando em Python.','section':'home'},
            {'id':'ffmpeg','label':'Exportação de vídeo','ready':bool(shutil.which('ffmpeg') and shutil.which('ffprobe')),'required':True,'detail':'FFmpeg e ffprobe disponíveis no computador.','section':'home'},
            {'id':'blender','label':'Cenas 3D','ready':bool(shutil.which('blender')),'required':True,'detail':'Blender disponível para os templates nativos.','section':'models'},
            {'id':'identity','label':'Nome e identificador do canal','ready':bool(channel['name'] and channel['handle']),'required':True,'detail':'Preencha nome e @ em Meu canal.','section':'channel'},
            {'id':'method','label':'Receita editorial','ready':all(self.method().get(k) for k in METHOD_DEFAULTS),'required':True,'detail':'Método preenchido; revise os fatos de cada episódio.','section':'channel'},
            {'id':'models','label':'Biblioteca de cenas','ready':models['count']>0,'required':True,'detail':str(models['count'])+' itens com arquivo-fonte disponível.','section':'models'},
            {'id':'voice','label':'Narração configurada','ready':uploaded_audio or voice_configured,'required':False,'detail':'Envie um áudio ou teste a conexão de voz e selecione uma voz. A consulta de leitura não comprova saldo ou geração paga.','section':'voice'},
            {'id':'logo','label':'Logo do canal','ready':bool(channel['logo_asset_id']),'required':False,'detail':'Opcional: imagem própria para a identidade do canal.','section':'channel'},
            {'id':'cover','label':'Capa do canal','ready':bool(channel['cover_asset_id']),'required':False,'detail':'Opcional: banner para apresentação do canal.','section':'channel'},
            {'id':'first_video','label':'Primeiro vídeo disponível','ready':videos['count']>0,'required':False,'detail':str(videos['count'])+' MP4s locais verificados com ffprobe; isto não comprova publicação.','section':'videos'},
        ]
        required = [check for check in checks if check['required']]
        ready_count = sum(check['ready'] for check in checks)
        return {'checks': checks, 'ready_count': ready_count, 'total':len(checks), 'percent':round(100*ready_count/len(checks)),
            'required_ready':sum(check['ready'] for check in required), 'required_total':len(required),
            'can_start':all(check['ready'] for check in required), 'video_count':videos['count'], 'model_count':models['count']}
