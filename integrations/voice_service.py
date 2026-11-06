"""Explicit, optional paid speech APIs with local credential storage.

No network call occurs at import or from connection_status/configure. TLS trust
and inherited proxy configuration are left to urllib's standard implementation.
"""
from __future__ import annotations

import json
import hashlib
import time
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import urllib.error
import urllib.request

PROVIDERS = {
    'elevenlabs': {'label': 'ElevenLabs', 'environment_variable': 'ELEVENLABS_API_KEY'},
    'openai': {'label': 'OpenAI API', 'environment_variable': 'OPENAI_API_KEY'},
}
OPENAI_VOICES = ('alloy', 'ash', 'ballad', 'coral', 'echo', 'fable', 'nova',
                 'onyx', 'sage', 'shimmer', 'verse', 'marin', 'cedar')
MAX_AUDIO_BYTES = 30 * 1024 * 1024


class VoiceServiceError(Exception):
    """Safe-to-display error, deliberately excluding upstream bodies and keys."""
    def __init__(self, message, *, status_code=400, category='validation'):
        super().__init__(message)
        self.status_code = status_code
        self.category = category

    def as_dict(self):
        return {'error': str(self), 'category': self.category}


class VoiceService:
    def __init__(self, root=None):
        self.root = Path(root) if root is not None else Path(__file__).resolve().parents[1]
        self.directory = self.root / '.local' / 'credentials'
        self.vault = self.directory / 'voice.json'

    @staticmethod
    def _provider(provider):
        if provider not in PROVIDERS:
            raise VoiceServiceError('Escolha ElevenLabs ou OpenAI API.')
        return provider

    def _read_vault(self):
        try:
            if self.vault.is_symlink():
                raise VoiceServiceError('O arquivo de credenciais não pode ser um link.', category='credential_storage')
            data = json.loads(self.vault.read_text(encoding='utf-8'))
        except FileNotFoundError:
            return {}
        except (OSError, ValueError):
            raise VoiceServiceError('Não foi possível ler o cofre local de voz. Configure a conexão novamente.',
                                    status_code=503, category='credential_storage') from None
        if not isinstance(data, dict):
            raise VoiceServiceError('Formato do cofre local inválido.', status_code=503, category='credential_storage')
        return {p: value for p, value in data.items()
                if p in PROVIDERS and isinstance(value, str) and value.strip()}

    def _key(self, provider):
        provider = self._provider(provider)
        injected = os.environ.get(PROVIDERS[provider]['environment_variable'], '').strip()
        if injected:
            return injected, 'environment'
        saved = self._read_vault().get(provider)
        return (saved, 'local_vault') if saved else (None, None)

    def connection_status(self, provider=None):
        selected = [self._provider(provider)] if provider else list(PROVIDERS)
        states = []
        for item in selected:
            key, source = self._key(item)
            receipt={}
            try:
                receipt=json.loads((self.directory/'checks.json').read_text()).get(item,{})
            except (OSError,ValueError,AttributeError):pass
            fingerprint=hashlib.sha256(key.encode()).hexdigest() if key else None
            tested=bool(key and receipt.get('fingerprint')==fingerprint)
            states.append({'provider': item, 'label': PROVIDERS[item]['label'],
                           'configured': bool(key), 'credential_source': source,
                           'connection_tested': tested, 'last_tested_at': receipt.get('tested_at') if tested else None,
                           'note': 'A última consulta autenticada não garante saldo nem disponibilidade futura. Teste novamente quando necessário.' if tested else 'Chave presente não comprova acesso. Teste a conexão para consultar o provedor.'})
        return {'providers': states, 'billing_notice': 'Gerar voz pode consumir créditos do provedor. ChatGPT Pro não inclui créditos de API.'}

    def configure(self, provider, key):
        provider = self._provider(provider)
        if not isinstance(key, str) or not key.strip() or len(key) > 2048 or '\x00' in key or '\n' in key or '\r' in key:
            raise VoiceServiceError('Informe uma chave válida no campo protegido.')
        # Never persist this key in channel metadata, requests, projects or logs.
        keys = self._read_vault()
        keys[provider] = key.strip()
        try:
            self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            if self.directory.is_symlink():
                raise VoiceServiceError('O diretório de credenciais não pode ser um link.', category='credential_storage')
            os.chmod(self.directory, 0o700)
            descriptor, temporary = tempfile.mkstemp(prefix='.voice-', suffix='.json', dir=self.directory)
            try:
                if hasattr(os,"fchmod"):os.fchmod(descriptor, 0o600)
                with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
                    json.dump(keys, handle, ensure_ascii=False)
                os.replace(temporary, self.vault)
                os.chmod(self.vault, 0o600)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        except OSError:
            raise VoiceServiceError('Não foi possível guardar a conexão no cofre local.',
                                    status_code=503, category='credential_storage') from None
        return self.connection_status(provider)

    def _request(self, provider, path, *, data=None, audio=False):
        key, _ = self._key(provider)
        if not key:
            raise VoiceServiceError('Conecte a conta de voz antes de continuar.', status_code=409, category='missing_credentials')
        # Fixed provider origins only; no arbitrary endpoint/secret destination.
        origin = 'https://api.elevenlabs.io' if provider == 'elevenlabs' else 'https://api.openai.com'
        headers = {'Accept': 'audio/mpeg' if audio else 'application/json',
                   'User-Agent': 'CurioLab-3D/0.3'}
        headers['xi-api-key' if provider == 'elevenlabs' else 'Authorization'] = key if provider == 'elevenlabs' else 'Bearer ' + key
        payload = None
        if data is not None:
            headers['Content-Type'] = 'application/json'
            payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        request = urllib.request.Request(origin + path, data=payload, headers=headers,
                                         method='POST' if data is not None else 'GET')
        try:
            # No custom SSL context or proxy override: retain TLS verification.
            with urllib.request.urlopen(request, timeout=90 if audio else 25) as response:
                content = response.read((MAX_AUDIO_BYTES if audio else 2 * 1024 * 1024) + 1)
        except urllib.error.HTTPError as error:
            code = error.code
            category = ('authentication' if code == 401 else 'permission_or_network_policy' if code == 403 else
                        'credits_or_rate_limit' if code in (402, 429) else 'provider_error')
            detail = {401: 'Chave recusada. Confira a conta e a chave.',
                      403: 'Acesso negado. Confira permissões da chave e a política de rede.',
                      402: 'Créditos indisponíveis no provedor.',
                      429: 'Limite de requisições ou créditos atingido.'}.get(code, 'O provedor não concluiu a solicitação.')
            raise VoiceServiceError(f'{PROVIDERS[provider]["label"]} respondeu HTTP {code}. {detail}',
                                    status_code=502, category=category) from None
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError):
            raise VoiceServiceError('Não foi possível acessar o provedor de voz. Confira rede e proxy; nenhuma verificação TLS foi desativada.',
                                    status_code=502, category='network') from None
        limit = MAX_AUDIO_BYTES if audio else 2 * 1024 * 1024
        if len(content) > limit:
            raise VoiceServiceError('A resposta do provedor excedeu o tamanho permitido.', status_code=502, category='invalid_response')
        if audio:
            return content
        try:
            result = json.loads(content)
        except (ValueError, UnicodeDecodeError):
            raise VoiceServiceError('O provedor não retornou uma resposta JSON válida.', status_code=502, category='invalid_response') from None
        if not isinstance(result, dict):
            raise VoiceServiceError('Formato de resposta inesperado do provedor.', status_code=502, category='invalid_response')
        return result

    def list_voices(self, provider):
        provider = self._provider(provider)
        if provider == 'elevenlabs':
            result = self._request(provider, '/v1/voices')
            if not isinstance(result.get('voices'), list):
                raise VoiceServiceError('A lista de vozes não foi retornada pelo ElevenLabs.', status_code=502, category='invalid_response')
            voices = []
            for voice in result['voices']:
                if not isinstance(voice, dict):
                    continue
                identifier = voice.get('voice_id')
                if not isinstance(identifier, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', identifier):
                    continue
                labels = voice.get('labels') if isinstance(voice.get('labels'), dict) else {}
                voices.append({'id': identifier, 'name': str(voice.get('name') or identifier)[:200],
                               'description': str(voice.get('description') or '')[:500],
                               'language': str(labels.get('language') or '')[:80]})
        else:
            # This is an authenticated read-only connectivity test, not a claim
            # that any particular model or speech credit is available.
            self._request(provider, '/v1/models')
            voices = [{'id': name, 'name': name.title(), 'description': 'Voz predefinida da OpenAI API.'}
                      for name in OPENAI_VOICES]
        return {'provider': provider, 'voices': voices,
                'note': 'Listar vozes testa acesso de leitura; geração ainda depende de permissões e créditos.'}

    def test_connection(self, provider):
        response = self.list_voices(provider)
        key,_=self._key(provider)
        self.directory.mkdir(parents=True,exist_ok=True,mode=0o700)
        receipt_path=self.directory/'checks.json'
        try:receipts=json.loads(receipt_path.read_text())
        except (OSError,ValueError):receipts={}
        if not isinstance(receipts,dict):receipts={}
        receipts[provider]={'fingerprint':hashlib.sha256(key.encode()).hexdigest(),'tested_at':time.time()}
        fd,temporary=tempfile.mkstemp(prefix='.check-',dir=self.directory)
        try:
            with os.fdopen(fd,'w') as file:json.dump(receipts,file)
            os.replace(temporary,receipt_path)
            os.chmod(receipt_path,0o600)
        finally:
            if os.path.exists(temporary):os.unlink(temporary)
        return {**response, 'status': 'connected', 'connection_tested': True,
                'note': 'Consulta autenticada concluída. Nenhum áudio foi gerado e nenhum crédito de síntese foi consumido por esta ação.'}

    def synthesize(self, provider, voice_id, text, output):
        provider = self._provider(provider)
        if not isinstance(voice_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', voice_id):
            raise VoiceServiceError('Selecione uma voz válida.')
        if provider == 'openai' and voice_id not in OPENAI_VOICES:
            raise VoiceServiceError('Selecione uma voz da lista da OpenAI API.')
        if not isinstance(text, str) or not text.strip() or len(text) > 4000:
            raise VoiceServiceError('Use um texto de 1 a 4.000 caracteres.')
        output = Path(output)
        if output.suffix.lower() != '.mp3':
            raise VoiceServiceError('A saída de narração deve ser um arquivo MP3.')
        if not shutil.which('ffprobe'):
            raise VoiceServiceError('Instale FFmpeg/ffprobe antes de gerar voz para validar o áudio recebido.',
                                    status_code=409, category='missing_dependency')
        if provider == 'elevenlabs':
            path = '/v1/text-to-speech/' + voice_id
            data = {'text': text.strip(), 'model_id': 'eleven_multilingual_v2'}
        else:
            path = '/v1/audio/speech'
            data = {'model': 'gpt-4o-mini-tts', 'voice': voice_id,
                    'input': text.strip(), 'response_format': 'mp3'}
        content = self._request(provider, path, data=data, audio=True)
        if not content or not (content.startswith(b'ID3') or
                               (len(content) > 2 and content[0] == 255 and content[1] & 224 == 224)):
            raise VoiceServiceError('O provedor não retornou um MP3 reconhecível.', status_code=502, category='invalid_audio')
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            descriptor, temporary = tempfile.mkstemp(prefix='.voice-audio-', suffix='.mp3', dir=output.parent)
            with os.fdopen(descriptor, 'wb') as handle:
                handle.write(content)
            probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                                    '-show_entries', 'stream=codec_type:format=duration', '-of', 'json', temporary],
                                   capture_output=True, text=True, timeout=30)
            try:
                details = json.loads(probe.stdout)
                duration = float(details.get('format', {}).get('duration', 0))
                audio_stream = any(s.get('codec_type') == 'audio' for s in details.get('streams', []))
            except (ValueError, TypeError):
                duration, audio_stream = 0, False
            if probe.returncode or not audio_stream or duration <= 0:
                raise VoiceServiceError('O áudio recebido não passou na validação. Nenhum arquivo final foi substituído.',
                                        status_code=502, category='invalid_audio')
            os.replace(temporary, output)
            return {'provider': provider, 'voice_id': voice_id, 'path': str(output),
                    'size_bytes': len(content), 'duration': duration, 'content_type': 'audio/mpeg',
                    'note': 'Áudio gerado por IA; revise pronúncia, conteúdo e direitos antes de publicar.'}
        except (OSError, subprocess.TimeoutExpired):
            raise VoiceServiceError('Não foi possível validar ou guardar o áudio. A geração pode ter consumido créditos; confira o provedor antes de repetir.',
                                    status_code=503, category='audio_storage') from None
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)
