#!/usr/bin/env python3
"""Optional paid narration. Only executes when explicitly invoked."""
import argparse
import json
import os
from pathlib import Path
import urllib.request
import urllib.error
import re

def synthesize(text, output):
    key=os.environ.get('ELEVENLABS_API_KEY')
    voice=os.environ.get('ELEVENLABS_VOICE_ID')
    if not key or not voice:
        raise ValueError('Configure ELEVENLABS_API_KEY e ELEVENLABS_VOICE_ID com segurança antes de gerar voz.')
    if not re.fullmatch(r'[A-Za-z0-9_-]+',voice):raise ValueError('Identificador de voz inválido.')
    if not text.strip() or len(text)>5000:raise ValueError('Use um texto de 1 a 5000 caracteres.')
    request=urllib.request.Request('https://api.elevenlabs.io/v1/text-to-speech/'+voice,
        data=json.dumps({'text':text,'model_id':'eleven_multilingual_v2'}).encode(),
        headers={'xi-api-key':key,'Content-Type':'application/json','Accept':'audio/mpeg'},method='POST')
    try:
        with urllib.request.urlopen(request,timeout=90) as response: data=response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'ElevenLabs respondeu HTTP {exc.code}; confira acesso, saldo e voz. Nenhuma credencial foi registrada.') from None
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_bytes(data)

if __name__=='__main__':
    p=argparse.ArgumentParser(description='Gera voz por API; pode consumir créditos ElevenLabs.')
    p.add_argument('--text-file',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    try:synthesize(Path(a.text_file).read_text(),a.output)
    except (ValueError,RuntimeError) as e:p.exit(1,str(e)+'\n')
