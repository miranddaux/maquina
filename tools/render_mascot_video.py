#!/usr/bin/env python3
"""Capture the installed R3F mascot at frame/fps; candidates require --preview."""
import argparse,json,math,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from mascot_registry import MascotRegistry

def main():
 p=argparse.ArgumentParser();p.add_argument('--mascot',default='nico');p.add_argument('--version',required=True)
 p.add_argument('--animation',choices=['idle','walk','run','talk','point','wave','celebrate'],default='wave')
 p.add_argument('--duration',type=float,default=2);p.add_argument('--fps',type=int,default=30);p.add_argument('--preview',action='store_true');p.add_argument('--output',required=True,type=Path)
 p.add_argument('--base-url',default='http://127.0.0.1:8000');p.add_argument('--width',type=int,default=1080);p.add_argument('--height',type=int,default=1920)
 a=p.parse_args()
 if not math.isfinite(a.duration) or not 1<=a.duration<=30 or a.fps not in [24,30] or (a.width,a.height) not in [(360,640),(1080,1920)]:p.error('Use1..30s,24/30fps e vertical360x640 ou1080x1920.')
 if a.output.suffix.lower()!='.mp4':p.error('Use uma saída MP4.')
 from urllib.parse import urlsplit
 base=urlsplit(a.base_url)
 if base.scheme!='http' or base.hostname not in ['127.0.0.1','localhost'] or base.username or base.password:p.error('O renderizador usa somente um servidor local.')
 registry=MascotRegistry(ROOT);pin=registry.pin(a.mascot,a.version,require_approved=not a.preview)
 from playwright.sync_api import sync_playwright
 output=a.output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='.nico-video-',dir=output.parent) as temp:
  directory=Path(temp)
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
   page=browser.new_page(viewport={'width':max(1440,a.width+100),'height':max(1100,a.height+100)},device_scale_factor=1)
   page.goto(a.base_url+'/mascot-viewer/',wait_until='networkidle');page.wait_for_function('window.__NICO?.ready',timeout=60000)
   metadata=page.evaluate('()=>window.__NICO.getMetadata()')
   if metadata['mascotId']!=pin['id'] or metadata['modelVersion']!=pin['version'] or metadata['configSha256']!=pin['config_sha256']:raise ValueError('O viewer não corresponde à versão fixada.')
   page.locator('[data-testid="mascot-canvas"]').evaluate('(el,size)=>{el.style.width=size[0]+"px";el.style.height=size[1]+"px";}',[a.width,a.height])
   canvas=page.locator('[data-testid="mascot-canvas"] canvas')
   for frame in range(round(a.duration*a.fps)):
    page.evaluate('(s)=>window.__NICO.setState(s)',{'view':'front','animation':a.animation,'timeSeconds':frame/a.fps,'playing':False})
    canvas.screenshot(path=str(directory/f'frame-{frame:04}.png'))
    if frame%30==0:print('Quadro',frame,flush=True)
   browser.close()
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate',str(a.fps),'-i',str(directory/'frame-%04d.png'),'-vf',f'crop={a.width}:{a.height}:0:0,setsar=1','-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(directory/'complete.mp4')],check=True)
  import os;os.replace(directory/'complete.mp4',output)
 output.with_suffix('.metadata.json').write_text(json.dumps({'title':'NICO · '+a.animation+(' (candidato, sem voz)' if a.preview else ''),'mascot':pin,'source':'r3f_candidate_preview' if a.preview else 'r3f_approved_mascot','preview':a.preview,'script':'Prévia silenciosa do modelo; não é episódio narrado.','render_time':'frame/fps','duration':a.duration,'fps':a.fps,'width':a.width,'height':a.height},ensure_ascii=False,indent=2))
 print(output)
if __name__=='__main__':main()
