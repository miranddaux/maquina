#!/usr/bin/env python3
"""Local CurioLab studio. Standard library only; binds loopback by default."""
import argparse
import base64
import binascii
import math
import mimetypes
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
import uuid
import zipfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, unquote, parse_qs
from panel_state import PanelState, VIDEO_NAME
from mascot_registry import MascotRegistry, PIN_KEYS, configured_sql_store

ROOT = Path(__file__).resolve().parent
DATA = ROOT / '.local' / 'projects'
OUTPUTS = ROOT / 'outputs'
ASSETS = ROOT / '.local' / 'assets'
MAX_UPLOAD = 30 * 1024 * 1024
JOBS = {}
LOCK = threading.Lock()
RENDER_LOCK = threading.Lock()
def panel_store():
    return PanelState(ROOT, assets=ASSETS)


def mascot_catalog():
    registry=MascotRegistry(ROOT);raw=registry.catalog();grouped={}
    for item in raw['mascots']:
        config=registry.load(item['id'],item['version'])
        prefix=f"/mascot-assets/{item['id']}/{item['version']}"
        previews={}
        for view in ['front','side','rear']:
            if (ROOT/'assets/mascots'/item['id']/item['version']/'previews'/(view+'.png')).is_file():
                previews[view]=prefix+'/previews/'+view+'.png'
        value={**item,'reference_status':('approved' if sum(a.get('kind')=='reference' and bool(a.get('path')) for a in item.get('assets',[]))>=2 else 'pending_original_bytes'),
            'preview_urls':previews,'viewer_url':'/mascot-viewer/','config_url':'/api/mascots/'+item['id']+'/'+item['version'],
            'approval_required':item['status']!='approved'}
        grouped.setdefault(item['id'],{'id':item['id'],'name':item['name'],'versions':[]})['versions'].append(value)
    return {'mascots':list(grouped.values()),'count':raw['count'],'errors':raw['errors'],
        'storage':{'active':'versioned_files','sql':'proposal_not_applied','proposal_url':'/docs/MASCOT-DATABASE-PROPOSAL.md'}}


class VoiceRequestError(Exception):
    def __init__(self, message, status_code=400, category='voice_error'):
        super().__init__(message)
        self.status_code=status_code
        self.category=category


def voice_operation(method,*args,**kwargs):
    from integrations.voice_service import VoiceService,VoiceServiceError
    try:
        return getattr(VoiceService(root=ROOT),method)(*args,**kwargs)
    except VoiceServiceError as error:
        raise VoiceRequestError(str(error),getattr(error,'status_code',400),getattr(error,'category','voice_error')) from None


def voice_provider(value):
    if value not in {'elevenlabs','openai'}:
        raise ValueError('Escolha ElevenLabs ou OpenAI para usar uma API de voz.')
    return value


SCRIPT = ('A Terra gira porque nasceu em movimento. Há cerca de 4,6 bilhões de anos, '
          'o Sistema Solar se formou de uma nuvem de gás e poeira em rotação. '
          'Esse movimento ajudou a dar origem à rotação do nosso planeta. '
          'No espaço, há pouca resistência para frear esse giro. '
          'A gravidade da Lua, porém, desacelera a rotação lentamente.')

def asset_record(aid):
    if not re.fullmatch(r'[a-f0-9]{32}',str(aid)):
        raise ValueError('Identificador de arquivo inválido.')
    try:
        record=json.loads((ASSETS/(aid+'.json')).read_text())
    except FileNotFoundError:
        raise ValueError('Arquivo enviado não encontrado.') from None
    return record

def asset_file(aid,kind=None):
    record=asset_record(aid)
    if kind and record['kind']!=kind:raise ValueError('Tipo de arquivo incorreto para esta etapa.')
    path=(ASSETS/record['stored_name']).resolve()
    if not path.is_relative_to(ASSETS.resolve()) or not path.is_file():raise ValueError('Arquivo indisponível.')
    return path

def public_asset(record):
    return {key:record[key] for key in ['id','filename','kind','url','size_bytes']}

def upload_asset(payload):
    filename=Path(str(payload.get('filename',''))).name[:160]
    extension=Path(filename).suffix.lower()
    if extension not in {'.png','.jpg','.jpeg','.webp','.mp3','.wav','.m4a'}:
        raise ValueError('Envie PNG, JPG, WebP, MP3, WAV ou M4A.')
    try:data=base64.b64decode(payload.get('data_base64',''),validate=True)
    except (ValueError,binascii.Error,TypeError):raise ValueError('Arquivo base64 inválido.') from None
    if not data or len(data)>MAX_UPLOAD:raise ValueError('O arquivo deve ter até 30 MB.')
    signatures={'.png':data.startswith(b'\x89PNG\r\n\x1a\n'),'.jpg':data.startswith(b'\xff\xd8\xff'),
        '.jpeg':data.startswith(b'\xff\xd8\xff'),'.webp':data[:4]==b'RIFF' and data[8:12]==b'WEBP',
        '.wav':data[:4]==b'RIFF' and data[8:12]==b'WAVE',
        '.mp3':data.startswith(b'ID3') or (len(data)>2 and data[0]==255 and data[1]&224==224),
        '.m4a':data[4:8]==b'ftyp'}
    if not signatures[extension]:raise ValueError('O conteúdo do arquivo não corresponde à extensão informada.')
    aid=uuid.uuid4().hex
    stored=aid+extension
    record=dict(id=aid,filename=filename,kind='image' if extension in {'.png','.jpg','.jpeg','.webp'} else 'audio',
        url='/assets/'+stored,size_bytes=len(data),stored_name=stored)
    ASSETS.mkdir(parents=True,exist_ok=True)
    (ASSETS/stored).write_bytes(data)
    (ASSETS/(aid+'.json')).write_text(json.dumps(record,ensure_ascii=False))
    return public_asset(record)

def make_project(payload):
    topic=str(payload.get('topic','')).strip()[:240]
    if not topic:raise ValueError('Escreva uma pergunta para começar.')
    mode=payload.get('mode','earth_rotation')
    if mode not in {'slideshow','earth_rotation','house_assembly','room_airflow'}:raise ValueError('Modo de projeto inválido.')
    resolution=payload.get('resolution','1080x1920')
    if resolution not in {'1080x1920','360x640'}:raise ValueError('Resolução inválida.')
    duration=float(payload.get('duration',8))
    if not math.isfinite(duration) or not 3<=duration<=180:raise ValueError('Use uma duração de 3 a 180 segundos.')
    earth=bool(re.search(r'terra.*gir|gir.*terra|earth.rotation',topic,re.I))
    script=str(payload.get('script') or (SCRIPT if earth else
        f'Pergunta: {topic}\n\nEscreva e revise sua explicação antes de gerar a narração.'))[:10000]
    default=[dict(start=0,end=duration*3/8,text='POR QUE A TERRA GIRA?'),
        dict(start=duration*3/8,end=duration*6/8,text='ELA NASCEU EM MOVIMENTO'),
        dict(start=duration*6/8,end=duration,text='UM GIRO QUE CONTINUA')]
    if mode=='house_assembly':
        default=[dict(start=0,end=duration*3/8,text='COMO UMA CASA GANHA FORMA?'),dict(start=duration*3/8,end=duration*6/8,text='UMA PEÇA DE CADA VEZ'),dict(start=duration*6/8,end=duration,text='ILUSTRAÇÃO, NÃO PROJETO DE OBRA')]
        if not payload.get('script'):script='Ilustração simplificada da montagem de uma casa. As peças entram em etapas para mostrar a ideia visual; não são instruções técnicas de construção.'
    if mode=='room_airflow':
        default=[dict(start=0,end=duration/3,text='UMA SALA, UMA PERGUNTA'),dict(start=duration/3,end=duration*2/3,text='O VENTILADOR MOVIMENTA O AR'),dict(start=duration*2/3,end=duration,text='FLUXO ILUSTRATIVO') ]
    scenes=payload.get('scenes',[])
    if not isinstance(scenes,list) or len(scenes)>24:raise ValueError('Use no máximo 24 cenas.')
    normalized=[]
    for index,scene in enumerate(scenes):
        if not isinstance(scene,dict):raise ValueError('Cena inválida.')
        start=float(scene.get('start',0));end=float(scene.get('end',duration))
        if not all(math.isfinite(v) for v in [start,end]) or start<0 or end-start<0.5 or end>duration:
            raise ValueError(f'Confira início e fim da cena {index+1}.')
        if normalized and start < normalized[-1]['end']-0.01:raise ValueError('As cenas não podem se sobrepor.')
        motion=scene.get('motion','zoom_in')
        if motion not in {'zoom_in','zoom_out','pan_left','pan_right','static'}:raise ValueError('Movimento de câmera inválido.')
        aid=scene.get('asset_id') or None
        if aid:asset_file(aid,'image')
        normalized.append(dict(asset_id=aid,start=start,end=end,motion=motion,
            caption=str(scene.get('caption',''))[:240],prompt=str(scene.get('prompt',''))[:3000]))
    if mode=='slideshow' and normalized:
        if abs(normalized[0]['start'])>0.01 or abs(normalized[-1]['end']-duration)>0.01 or any(abs(normalized[i]['start']-normalized[i-1]['end'])>0.01 for i in range(1,len(normalized))):
            raise ValueError('A timeline precisa começar em 0, seguir sem lacunas e terminar na duração total.')
    audio=payload.get('audio_asset_id') or None
    if audio:asset_file(audio,'audio')
    if mode=='slideshow':
        ready=bool(normalized and all(scene['asset_id'] for scene in normalized))
        captions=[dict(start=x['start'],end=x['end'],text=x['caption']) for x in normalized]
    else:
        if duration>30:raise ValueError('O template 3D suporta no máximo 30 segundos.')
        ready=earth or mode in {'house_assembly','room_airflow'}
        captions=[dict(start=x['start'],end=x['end'],text=x['caption']) for x in normalized] if normalized else default
    result=dict(id=uuid.uuid4().hex,topic=topic,title=str(payload.get('title') or topic)[:240],script=script,
        mode=mode,resolution=resolution,renderable=ready,duration=duration,audio_asset_id=audio,
        template=mode,captions=captions,
        scenes=normalized if mode=='slideshow' else normalized or [dict(title='Cena '+str(i+1),caption=x['text'],start=x['start'],end=x['end'],motion='static',asset_id=None) for i,x in enumerate(default)],
        sources=['https://spaceplace.nasa.gov/solar-system-formation/en/'] if earth else [],
        review_status='draft',created_at=time.time(),updated_at=time.time(),
        note='Imagens enviadas são animadas em 2D com pan/zoom. Geometria 3D real está nos templates Terra e Casa em montagem. Narração é opcional e precisa ser enviada.')

    selection=panel_store().channel().get("mascot",{})
    result["mascot"]=MascotRegistry(ROOT).pin(selection["id"],selection["version"],require_approved=True) if selection.get("id") else None
    return result

def project_path(pid):
    if not re.fullmatch(r'[a-f0-9]{32}',pid):
        raise FileNotFoundError('Projeto não encontrado.')
    return DATA / (pid + '.json')

def read_project(pid):
    return json.loads(project_path(pid).read_text())

def render_job(job_id,project):
    with RENDER_LOCK:
        with LOCK:JOBS[job_id]['status']='running'
        try:
            OUTPUTS.mkdir(exist_ok=True)
            spec=OUTPUTS/(job_id+'.json');target=OUTPUTS/(job_id+'.mp4');log=OUTPUTS/(job_id+'.log')
            mode=project.get('mode','earth_rotation')
            width,height=map(int,project.get('resolution','360x640').split('x'))
            if mode=='slideshow':
                scenes=[dict(scene,image_path=str(asset_file(scene['asset_id'],'image'))) for scene in project['scenes']]
                config=dict(project,width=width,height=height,fps=30,scenes=scenes)
                if project.get('audio_asset_id'):config['narration_path']=str(asset_file(project['audio_asset_id'],'audio'))
                command=[os.sys.executable,str(ROOT/'engine/slideshow.py'),'--project',str(spec),'--output',str(target)]
            else:
                config=dict(title=project['title'],topic=mode,duration=project.get('duration',8),captions=project['captions'])
                command=[os.sys.executable,str(ROOT/'engine/render.py'),'--project',str(spec),'--output',str(target)]
                if width==360:command.append('--preview')
                else:command.append('--full-hd')
                if project.get('audio_asset_id'):command.extend(['--narration',str(asset_file(project['audio_asset_id'],'audio'))])
            config['branding']=panel_store().channel()
            frozen=project.get('mascot')
            if frozen:MascotRegistry(ROOT).resolve(frozen,require_approved=True)
            config['branding']['mascot']=frozen or {}
            config['mascot']=frozen
            config['project_id']=project['id']
            config['script']=project.get('script','')
            spec.write_text(json.dumps(config,ensure_ascii=False))
            with log.open('w') as handle:subprocess.run(command,cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT,check=True,timeout=1200)
            if not target.is_file() or target.stat().st_size<1000:raise RuntimeError('MP4 ausente.')
            if frozen:
                sql=configured_sql_store()
                if sql:
                    try:
                        sql.register_version(MascotRegistry(ROOT),frozen['id'],frozen['version'])
                        sql.assign_video(job_id,frozen)
                    finally:sql.close()
            with LOCK:JOBS[job_id].update(status='completed',download_url='/outputs/'+target.name,resolution=project.get('resolution','360x640'))
        except Exception:
            with LOCK:JOBS[job_id].update(status='failed',error='Falha no render. Consulte outputs/'+job_id+'.log; seus arquivos e projeto foram preservados.')

def render_character_preview(job_id,branding):
    with RENDER_LOCK:
        with LOCK:JOBS[job_id]['status']='running'
        try:
            OUTPUTS.mkdir(exist_ok=True)
            spec=OUTPUTS/(job_id+'.json');target=OUTPUTS/(job_id+'.png')
            spec.write_text(json.dumps({'branding':branding},ensure_ascii=False))
            with (OUTPUTS/(job_id+'.log')).open('w') as log:
                subprocess.run(['blender','-b','-noaudio','--factory-startup','-t','2','--python',str(ROOT/'engine/render_character.py'),'--',str(spec),str(target)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=90)
            if not target.is_file():raise ValueError('A imagem não foi produzida.')
            with LOCK:JOBS[job_id].update(status='completed',image_url='/previews/'+target.name)
        except Exception:
            with LOCK:JOBS[job_id].update(status='failed',error='A prévia 3D não foi concluída. Confira o log em outputs/'+job_id+'.log.')

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT/'web'),**kwargs)

    def send_json(self,data,status=200):
        content=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(content)))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        self.wfile.write(content)

    def file_response(self,path,kind,download=False):
        content=path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(len(content)))
        if download:self.send_header('Content-Disposition','attachment; filename="'+path.name+'"')
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        route=urlsplit(self.path).path
        try:
            if route=='/api/mascots':return self.send_json(mascot_catalog())
            mascot_config=re.fullmatch(r'/api/mascots/([a-z][a-z0-9_-]*)/([0-9A-Za-z.-]+)',route)
            if mascot_config:return self.send_json(MascotRegistry(ROOT).load(*mascot_config.groups()))
            if route.startswith('/mascot-assets/'):
                relative=Path(unquote(route.removeprefix('/mascot-assets/')))
                base=(ROOT/'assets/mascots').resolve();path=(base/relative).resolve()
                if not path.is_relative_to(base) or not path.is_file() or path.suffix.lower() not in {'.png','.jpg','.jpeg','.webp','.json','.glb','.gltf','.bin','.mp4'}:raise FileNotFoundError()
                return self.file_response(path,mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
            if route.startswith('/previews/'):
                name=route.removeprefix('/previews/')
                if not re.fullmatch(r'[a-f0-9]{32}\.png',name):raise FileNotFoundError()
                return self.file_response(OUTPUTS/name,'image/png')
            if route=='/api/voice/status':
                return self.send_json(voice_operation('connection_status'))
            if route=='/api/voice/voices':
                provider=voice_provider(parse_qs(urlsplit(self.path).query).get('provider',['elevenlabs'])[0])
                return self.send_json(voice_operation('list_voices',provider))
            if route=='/api/channel':
                return self.send_json(panel_store().channel())
            if route=='/api/channel/export':
                data=json.dumps(panel_store().channel(),ensure_ascii=False,indent=2).encode()
                self.send_response(200)
                self.send_header('Content-Type','application/json; charset=utf-8')
                self.send_header('Content-Disposition','attachment; filename="curiolab-canal.json"')
                self.send_header('Content-Length',str(len(data)))
                self.end_headers();self.wfile.write(data);return
            if route=='/api/method':
                return self.send_json(panel_store().method())
            if route=='/api/readiness':
                return self.send_json(panel_store().readiness())
            if route=='/api/videos':
                return self.send_json(panel_store().videos())
            if route=='/api/models':
                return self.send_json(panel_store().models())
            if route=='/api/requests':
                return self.send_json(panel_store().requests())
            request_match=re.fullmatch(r'/api/requests/([a-f0-9]{32})(/brief)?',route)
            if request_match:
                request_file=ROOT/'.local/requests'/request_match[1]/('brief.md' if request_match[2] else 'request.json')
                if request_match[2]:return self.file_response(request_file,'text/plain; charset=utf-8',True)
                return self.send_json(json.loads(request_file.read_text()))
            if route=='/api/handoff':
                return self.send_json(dict(channel=panel_store().channel(),method=panel_store().method(),
                    instructions='Use a skill curiolab-3d no Codex e abra o pedido salvo em .local/requests. Este painel não executa um modelo de IA.'))
            if route=='/' and (ROOT/'web/panel.html').is_file():
                self.path='/panel.html'
                return super().do_GET()
            if route=='/studio.html':
                self.path='/index.html'
                return super().do_GET()
            if route=='/curiolab-editor-visual.html':return self.file_response(OUTPUTS/'curiolab-editor-visual.html','text/html; charset=utf-8')
            if route=='/nico-visual.html':return self.file_response(OUTPUTS/'nico-visual.html','text/html; charset=utf-8')
            if route in {'/visual.html','/curiolab-visual.html'}:
                return self.file_response(OUTPUTS/'curiolab-visual.html','text/html; charset=utf-8')
            if route=='/downloads/analysis.zip':
                return self.file_response(OUTPUTS/'analysis/folhas-e-medidas.zip','application/zip',True)
            if route=='/api/status':
                return self.send_json(dict(application='curiolab-3d',version='0.3',tools={x:bool(shutil.which(x)) for x in ['blender','ffmpeg']},
                    mode='local', narration_configured=bool(os.getenv('ELEVENLABS_API_KEY') and os.getenv('ELEVENLABS_VOICE_ID')),
                    limitations=['Imagens animadas usam composição 2D; os templates Terra e Casa usam geometria 3D.', 'Envie áudio para narração; publicação é manual.']))
            if route=='/api/assets':
                return self.send_json({'assets':[public_asset(json.loads(p.read_text())) for p in sorted(ASSETS.glob('*.json'))]})
            if route=='/api/analysis':
                index=OUTPUTS/'analysis/index.json'
                content=json.loads(index.read_text()) if index.is_file() else None
                files=[]
                for category in ['analysis','transcripts','ocr']:
                    base=OUTPUTS/category
                    for p in sorted(base.rglob('*')):
                        if p.is_file() and p.suffix.lower() in {'.json','.csv','.md','.jpg','.png','.pdf','.srt','.vtt','.txt','.html','.mp4','.wav'}:
                            files.append(dict(category=category,name=str(p.relative_to(base)),url='/research/'+category+'/'+p.relative_to(base).as_posix(),size_bytes=p.stat().st_size))
                return self.send_json({'index':content,'files':files})
            if route.startswith('/assets/'):
                name=route.removeprefix('/assets/')
                if not re.fullmatch(r'[a-f0-9]{32}\.(png|jpg|jpeg|webp|mp3|wav|m4a)',name):raise FileNotFoundError()
                return self.file_response(ASSETS/name,mimetypes.guess_type(name)[0] or 'application/octet-stream')
            if route.startswith('/docs/'):
                relative=Path(unquote(route.removeprefix('/docs/')))
                path=(ROOT/'docs'/relative).resolve()
                if not path.is_relative_to((ROOT/'docs').resolve()) or not path.is_file() or path.suffix.lower() not in {'.md','.html','.json','.csv'}:raise FileNotFoundError()
                return self.file_response(path,'text/plain; charset=utf-8' if path.suffix=='.md' else mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
            if route.startswith('/research/'):
                name=unquote(route.removeprefix('/research/'))
                relative=Path(name)
                path=(OUTPUTS/relative).resolve()
                if not relative.parts or relative.parts[0] not in {'analysis','transcripts','ocr'} or not path.is_relative_to(OUTPUTS.resolve()) or not path.is_file():raise FileNotFoundError()
                return self.file_response(path,mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
            if route=='/api/projects':
                return self.send_json({'projects':[json.loads(p.read_text()) for p in sorted(DATA.glob('*.json'),reverse=True)]})
            if route=='/api/demo':
                name='casa-fullhd.mp4' if (OUTPUTS/'casa-fullhd.mp4').is_file() else 'demo.mp4'
                available=(OUTPUTS/name).is_file()
                return self.send_json(dict(available=available,download_url='/outputs/'+name if available else None))
            if route.startswith('/api/projects/'):
                parts=route.strip('/').split('/')
                path=project_path(parts[2])
                if len(parts)==4 and parts[3]=='download':return self.file_response(path,'application/json',True)
                if len(parts)==3:return self.send_json(read_project(parts[2]))
            if route.startswith('/api/jobs/'):
                with LOCK: job=JOBS.get(route.rsplit('/',1)[-1])
                return self.send_json(job or {'error':'Renderização não encontrada.'},200 if job else 404)
            if route=='/api/skill/download':
                from tools.package_skill import build_package, FILENAME
                data,_=build_package(ROOT)
                self.send_response(200)
                self.send_header('Content-Type','application/zip')
                self.send_header('Content-Disposition','attachment; filename="'+FILENAME+'"')
                self.send_header('Content-Length',str(len(data)))
                self.end_headers();self.wfile.write(data);return
            if route.startswith('/outputs/'):
                name=route.removeprefix('/outputs/')
                if not VIDEO_NAME.fullmatch(name):raise FileNotFoundError()
                return self.file_response(OUTPUTS/name,'video/mp4')
            if route.startswith('/api/'):
                return self.send_json({'error':'Endpoint não encontrado.'},404)
            return super().do_GET()
        except VoiceRequestError as exc:
            self.send_json({'error':str(exc),'category':exc.category},exc.status_code)
        except FileNotFoundError:
            self.send_json({'error':'Arquivo ou projeto não encontrado.'},404)
        except (ValueError,TypeError):
            self.send_json({'error':'Configuração ou arquivo de dados inválido. Revise o arquivo local sem compartilhar credenciais.'},400)

    def do_POST(self):
        # Local app: disallow cross-origin writes and unbounded request bodies.
        origin=self.headers.get('Origin')
        if origin and urlsplit(origin).netloc != self.headers.get('Host'):
            return self.send_json({'error':'Origem não permitida.'},403)
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<0 or size>MAX_UPLOAD*4//3+4096:raise ValueError('Solicitação muito grande.')
            payload=json.loads(self.rfile.read(size) or b'{}')
            if not isinstance(payload,dict):raise ValueError('Envie um objeto JSON.')
            route=urlsplit(self.path).path
            if route=='/api/mascots/select':
                if set(payload)!={'id','version'}:raise ValueError('Informe somente ID e versão do mascote.')
                pin=MascotRegistry(ROOT).pin(payload['id'],payload['version'],require_approved=True)
                return self.send_json(panel_store().save_channel({'mascot':pin}))
            if route=='/api/character/preview':
                if not shutil.which('blender'):raise ValueError('Instale Blender para gerar a prévia real.')
                with LOCK:
                    if sum(j['status'] in ['queued','running'] for j in JOBS.values())>=2:return self.send_json({'error':'Aguarde a fila de renderização.'},429)
                    jid=uuid.uuid4().hex;JOBS[jid]={'job_id':jid,'status':'queued'}
                threading.Thread(target=render_character_preview,args=(jid,panel_store().channel()),daemon=True).start()
                return self.send_json({'job_id':jid},202)
            if route=='/api/voice/connect':
                if set(payload)-{'provider','api_key'}:raise ValueError('Campos inválidos na conexão de voz.')
                provider=voice_provider(payload.get('provider'))
                voice_operation('configure',provider,payload.get('api_key',''))
                return self.send_json(voice_operation('test_connection',provider))
            if route=='/api/voice/synthesize':
                if set(payload)-{'provider','voice_id','text','confirm_credits'}:raise ValueError('Campos inválidos na geração de voz.')
                if payload.get('confirm_credits') is not True:raise ValueError('Confirme o possível consumo de créditos antes de gerar voz.')
                provider=voice_provider(payload.get('provider'))
                aid=uuid.uuid4().hex
                ASSETS.mkdir(parents=True,exist_ok=True)
                target=ASSETS/(aid+'.mp3')
                result=voice_operation('synthesize',provider,payload.get('voice_id',''),payload.get('text',''),target)
                if not target.is_file() or target.stat().st_size<32:raise ValueError('O serviço não devolveu áudio válido.')
                record=dict(id=aid,filename='narracao-'+aid[:8]+'.mp3',kind='audio',url='/assets/'+target.name,
                    size_bytes=target.stat().st_size,stored_name=target.name,provider=provider)
                (ASSETS/(aid+'.json')).write_text(json.dumps(record,ensure_ascii=False))
                return self.send_json(dict(asset=public_asset(record),provider=provider,voice_id=result.get('voice_id')),201)
            if route=='/api/channel':return self.send_json(panel_store().save_channel(payload))
            if route=='/api/method':return self.send_json(panel_store().save_method(payload))
            if route=='/api/method/reset':return self.send_json(panel_store().reset_method(payload.get('section')))
            if route=='/api/requests':return self.send_json(panel_store().create_request(payload),201)
            if route=='/api/assets':return self.send_json(upload_asset(payload),201)
            if route=='/api/projects':
                p=make_project(payload)
                DATA.mkdir(parents=True,exist_ok=True)
                project_path(p['id']).write_text(json.dumps(p,ensure_ascii=False,indent=2))
                return self.send_json(p,201)
            update=re.fullmatch(r'/api/projects/([a-f0-9]{32})',route)
            if update:
                previous=read_project(update[1])
                p=make_project(payload)
                p.update(id=previous['id'],created_at=previous.get('created_at',time.time()))
                project_path(p['id']).write_text(json.dumps(p,ensure_ascii=False,indent=2))
                return self.send_json(p)
            match=re.fullmatch(r'/api/projects/([a-f0-9]{32})/render',route)
            if match:
                p=read_project(match[1])
                if not p['renderable']:raise ValueError('Envie uma imagem para cada cena, ou selecione o template Terra com um tema compatível.')
                required=['ffmpeg'] if p.get('mode')=='slideshow' else ['blender','ffmpeg']
                if not all(shutil.which(x) for x in required):raise ValueError('Instale as ferramentas de renderização necessárias.')
                with LOCK:
                    if sum(j['status'] in ['queued','running'] for j in JOBS.values())>=2:
                        return self.send_json({'error':'Há dois renders na fila. Aguarde a conclusão.'},429)
                    jid=uuid.uuid4().hex
                    JOBS[jid]=dict(job_id=jid,status='queued')
                threading.Thread(target=render_job,args=(jid,p),daemon=True).start()
                return self.send_json({'job_id':jid},202)
            return self.send_json({'error':'Endpoint não encontrado.'},404)
        except VoiceRequestError as exc:self.send_json({'error':str(exc),'category':exc.category},exc.status_code)
        except (ValueError,TypeError,json.JSONDecodeError) as exc:self.send_json({'error':str(exc)},400)
        except FileNotFoundError:self.send_json({'error':'Projeto não encontrado.'},404)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',default=8000,type=int)
    args=parser.parse_args()
    print(f'CurioLab 3D: porta {args.port} (uso local)',flush=True)
    ThreadingHTTPServer((args.host,args.port),Handler).serve_forever()
