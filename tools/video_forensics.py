#!/usr/bin/env python3
"""Frame contact sheets and conservative image-motion estimates, not physical-camera reconstruction."""
import argparse,csv,json,math,re,subprocess,time
from pathlib import Path
from datetime import datetime,timezone
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont

cv2.setNumThreads(1)
ROOT=Path(__file__).resolve().parents[1]
FONT_PATH='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT=ImageFont.truetype(FONT_PATH,13)
SMALL=ImageFont.truetype(FONT_PATH,11)
FIELDS=['frame','time_s','pts_ms','dx_image_px','dy_image_px','dx_pct_width','dy_pct_height','scale_ratio','zoom_pct','rotation_deg','tracks','inliers','inlier_ratio','coverage','residual_px','fit_confidence','confidence','motion_warning','pixel_diff','histogram_change','cut_candidate','image_direction','inferred_camera_direction','state']

def timestamp(t):
 m=int(t//60);s=t%60
 return f'{m:02d}:{s:06.3f}'

def direction(dx,dy,threshold=.3):
 parts=[]
 if abs(dx)>threshold:parts.append('direita' if dx>0 else 'esquerda')
 if abs(dy)>threshold:parts.append('baixo' if dy>0 else 'cima')
 return '+'.join(parts) or 'parado'

def estimate(prev,gray):
 h,w=gray.shape
 diff=float(np.mean(cv2.absdiff(prev,gray))/255)
 hist1=cv2.calcHist([prev],[0],None,[32],[0,256]);cv2.normalize(hist1,hist1)
 hist2=cv2.calcHist([gray],[0],None,[32],[0,256]);cv2.normalize(hist2,hist2)
 hist=float(cv2.compareHist(hist1,hist2,cv2.HISTCMP_BHATTACHARYYA))
 mask=np.zeros_like(prev);mask[int(h*.2):int(h*.9),int(w*.03):int(w*.97)]=255
 points=cv2.goodFeaturesToTrack(prev,160,.015,6,mask=mask)
 base=dict(dx_image_px=0.,dy_image_px=0.,scale_ratio=1.,rotation_deg=0.,tracks=0,inliers=0,inlier_ratio=0.,coverage=0.,residual_px=None,confidence='low',pixel_diff=diff,histogram_change=hist,cut_candidate=False)
 if points is not None and len(points)>=6:
  nxt,status,error=cv2.calcOpticalFlowPyrLK(prev,gray,points,None,winSize=(19,19),maxLevel=2,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,20,.02))
  good=(status.reshape(-1)==1)&(error.reshape(-1)<35)
  a=points.reshape(-1,2)[good];b=nxt.reshape(-1,2)[good]
  base['tracks']=len(a)
  if len(a)>=6:
   affine,inliers=cv2.estimateAffinePartial2D(a,b,method=cv2.RANSAC,ransacReprojThreshold=1.8,maxIters=150,confidence=.97)
   if affine is not None:
    keep=inliers.reshape(-1).astype(bool);n=int(keep.sum());ratio=n/len(a)
    center=np.array([w/2,h/2]);shift=affine[:,:2]@center+affine[:,2]-center
    scale=float(math.hypot(affine[0,0],affine[1,0]));rotation=math.degrees(math.atan2(affine[1,0],affine[0,0]))
    residual=float(np.median(np.linalg.norm(a@affine[:,:2].T+affine[:,2]-b,axis=1)))
    coverage=float(np.ptp(a[keep,0])*np.ptp(a[keep,1])/(w*h)) if n>2 else 0
    confidence='high' if n>=30 and ratio>.75 and coverage>.22 else 'medium' if n>=12 and ratio>.55 and coverage>.08 else 'low'
    base.update(dx_image_px=float(shift[0]),dy_image_px=float(shift[1]),scale_ratio=scale,rotation_deg=float(rotation),inliers=n,inlier_ratio=ratio,coverage=coverage,residual_px=residual,confidence=confidence)
 base['cut_candidate']=bool((hist>.40 and diff>.12) or (diff>.25 and (base['inlier_ratio']<.5 or hist>.18)) or (diff>.15 and base['tracks']<8 and hist>.24) or (hist>.20 and diff>.08 and base['inlier_ratio']<.45) or (diff>.13 and base['inlier_ratio']<.22 and (base['residual_px'] or 0)>8))
 base['dx_pct_width']=base['dx_image_px']/w*100
 base['dy_pct_height']=base['dy_image_px']/h*100
 base['zoom_pct']=(base['scale_ratio']-1)*100
 base['fit_confidence']=base['confidence']
 base['motion_warning']=''
 if not base['cut_candidate'] and (abs(base['zoom_pct'])>1.2 or abs(base['dx_pct_width'])>2 or abs(base['dy_pct_height'])>2):
  base['confidence']='low'
  base['motion_warning']='rapid_motion_or_repeated_pattern_alias'
 base['image_direction']=direction(base['dx_image_px'],base['dy_image_px'])
 base['inferred_camera_direction']=direction(-base['dx_image_px'],-base['dy_image_px']) if base['confidence']!='low' else 'indeterminado'
 if base['cut_candidate']:state='cut_candidate'
 elif diff<.0035:state='static_image'
 elif base['confidence']=='low':state='unreliable_or_object_motion'
 elif abs(base['dx_image_px'])<.35 and abs(base['dy_image_px'])<.35 and abs(base['zoom_pct'])<.14 and abs(base['rotation_deg'])<.15:state='camera_approximately_static'
 elif abs(base['zoom_pct'])>=.14:state='zoom_in_candidate' if base['zoom_pct']>0 else 'zoom_out_candidate'
 else:state='pan_or_object_motion'
 base['state']=state
 return base

class Sheets:
 def __init__(self,directory,prefix,title,subtitle):
  self.directory=directory;self.prefix=prefix;self.title=title;self.subtitle=subtitle;self.items=[];self.paths=[];self.n=0
 def add(self,frame,image,seconds,label=''):
  rgb=cv2.cvtColor(image,cv2.COLOR_BGR2RGB);im=Image.fromarray(rgb);im.thumbnail((144,256))
  self.items.append((frame,im,seconds,label))
  if len(self.items)==40:self.flush()
 def flush(self):
  if not self.items:return
  self.n+=1;rows=math.ceil(len(self.items)/5)
  out=Image.new('RGB',(780,86+rows*290),(21,24,34));d=ImageDraw.Draw(out)
  d.text((12,10),self.title[:100],font=FONT,fill=(243,242,235))
  d.text((12,32),self.subtitle[:110],font=SMALL,fill=(175,194,214))
  d.text((12,53),f'Folha {self.n:03d} | {timestamp(self.items[0][2])} — {timestamp(self.items[-1][2])}',font=SMALL,fill=(175,194,214))
  for n,(index,im,seconds,label) in enumerate(self.items):
   x=12+(n%5)*154;y=86+(n//5)*290
   out.paste(im,(x+(144-im.width)//2,y))
   d.text((x,y+258),f'#{index:05d}  {timestamp(seconds)}',font=SMALL,fill=(245,241,211))
   if label:d.text((x,y+273),label[:24],font=SMALL,fill=(180,215,139))
  p=self.directory/f'{self.prefix}-{self.n:03d}.jpg';out.save(p,quality=84,optimize=True);self.paths.append(str(p.relative_to(ROOT/'outputs')));self.items=[]


def interval_rows(rows,fps):
 intervals=[];start=None
 for n,r in enumerate(rows):
  static=r['state'] in ['static_image','camera_approximately_static']
  if static and start is None:start=n
  if start is not None and (not static or n==len(rows)-1):
   end=n if not static else n+1
   if (end-start)/fps>=.35:
    segment=rows[start:end];intervals.append(dict(start_frame=start,end_frame=end-1,start_s=start/fps,end_s=end/fps,duration_s=(end-start)/fps,kind='image_static' if all(x['state']=='static_image' for x in segment) else 'camera_approximately_static',note='Movimento global baixo; objetos podem se mover.'))
   start=None
 return intervals


def motion_segments(rows,fps):
 segments=[];step=max(1,round(fps/4))
 for start in range(0,len(rows),step):
  subset=rows[start:start+step];reliable=[r for r in subset if r['confidence']!='low' and not r['cut_candidate']]
  if any(r['cut_candidate'] for r in subset):kind='cut_window';dx=dy=zoom=0.
  elif len(reliable)<len(subset)/2:kind='uncertain_object_or_camera';dx=dy=zoom=0.
  else:
   dx=float(np.median([r['dx_image_px'] for r in reliable]));dy=float(np.median([r['dy_image_px'] for r in reliable]));zoom=float(np.median([r['zoom_pct'] for r in reliable]))
   if abs(dx)<.35 and abs(dy)<.35 and abs(zoom)<.14:kind='approximately_static'
   elif abs(zoom)>=.14:kind=('zoom_in_candidate' if zoom>0 else 'zoom_out_candidate')+':'+direction(dx,dy)
   else:kind='image_pan:'+direction(dx,dy)
  end=min(len(rows),start+step)
  if segments and segments[-1]['kind']==kind:
   segments[-1]['end_frame']=end-1;segments[-1]['end_s']=end/fps;segments[-1]['duration_s']=(end-segments[-1]['start_frame'])/fps
  else:segments.append(dict(start_frame=start,end_frame=end-1,start_s=start/fps,end_s=end/fps,duration_s=(end-start)/fps,kind=kind,median_dx_px_per_frame=dx,median_dy_px_per_frame=dy,median_zoom_pct_per_frame=zoom))
 for segment in segments:
  reliable=[r for r in rows[segment['start_frame']:segment['end_frame']+1] if r['confidence']!='low' and not r['cut_candidate']]
  for key,out in [('dx_image_px','median_dx_px_per_frame'),('dy_image_px','median_dy_px_per_frame'),('zoom_pct','median_zoom_pct_per_frame')]:
   segment[out]=float(np.median([r[key] for r in reliable])) if reliable else None
 return segments


def analyze(source,output):
 started=time.time();source=Path(source)
 slug=re.sub(r'[^a-z0-9]+','-',source.stem.lower()).strip('-').replace('-snapyt-app','')
 directory=output/slug;directory.mkdir(parents=True,exist_ok=True)
 for pattern in ['story-*.jpg','moments-*.jpg']:
  for old in directory.glob(pattern):old.unlink()
 cap=cv2.VideoCapture(str(source))
 if not cap.isOpened():raise RuntimeError('Não foi possível abrir '+str(source))
 fps=cap.get(cv2.CAP_PROP_FPS);width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT));expected=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
 sheets=Sheets(directory,'story',source.name,'6 amostras/s | numero do quadro original e tempo | imagens sem interpolacao')
 rows=[];prev=None;index=0;next_sample=0.;cuts=[]
 while True:
  ok,frame=cap.read()
  if not ok:break
  seconds=index/fps
  if seconds+1/(fps*2)>=next_sample:
   sheets.add(index,frame,seconds)
   next_sample+=1/6
  small=cv2.resize(frame,(202,round(height*202/width)),interpolation=cv2.INTER_AREA)
  gray=cv2.cvtColor(small,cv2.COLOR_BGR2GRAY)
  if prev is None:
   motion=dict(dx_image_px=0.,dy_image_px=0.,dx_pct_width=0.,dy_pct_height=0.,scale_ratio=1.,zoom_pct=0.,rotation_deg=0.,tracks=0,inliers=0,inlier_ratio=0.,coverage=0.,residual_px=None,confidence='low',pixel_diff=0.,histogram_change=0.,cut_candidate=False,image_direction='parado',inferred_camera_direction='indeterminado',state='first_frame')
  else:motion=estimate(prev,gray)
  row=dict(frame=index,time_s=round(seconds,6),pts_ms=round(cap.get(cv2.CAP_PROP_POS_MSEC),3),**motion)
  rows.append(row)
  if row['cut_candidate'] and (not cuts or index-cuts[-1]['frame']>2):cuts.append(dict(frame=index,time_s=seconds,confidence='high' if row['histogram_change']>.55 else 'medium',histogram_change=row['histogram_change'],pixel_diff=row['pixel_diff'],note='Corte candidato automático; precisa confirmar na folha de momentos.'))
  prev=gray;index+=1
  if index%900==0:print(source.name,index,'/',expected,flush=True)
 cap.release();sheets.flush()
 with (directory/'camera.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
 static=interval_rows(rows,fps)
 camera_segments=motion_segments(rows,fps)
 # Highest image motion and scale events, spaced >=2s; excluded immediate cuts.
 ranked=sorted((r for r in rows if r['confidence']!='low' and not r['cut_candidate']),key=lambda r:abs(r['zoom_pct'])*2+math.hypot(r['dx_image_px'],r['dy_image_px']),reverse=True)
 motions=[]
 for r in ranked:
  if all(abs(r['time_s']-e['time_s'])>2 for e in motions+cuts):
   motions.append(dict(frame=r['frame'],time_s=r['time_s'],kind=r['state'],zoom_pct=r['zoom_pct'],image_direction=r['image_direction'],confidence=r['confidence']))
  if len(motions)>=8:break
 important=sorted([dict(**c,kind='cut_candidate') for c in cuts]+motions,key=lambda x:x['frame'])
 # All original frames in a +/-0.4s window; overlap merged, no interpolation.
 selected=set()
 for e in important:
  center=e['frame'];radius=round(fps*.4)
  selected.update(range(max(0,center-radius),min(index,center+radius+1)))
 moments=Sheets(directory,'moments',source.name,'Todos os quadros originais em janelas +/-0,4s de cortes/movimentos selecionados')
 cap=cv2.VideoCapture(str(source));i=0;eventframes={e['frame']:e['kind'] for e in important}
 while True:
  ok,frame=cap.read()
  if not ok:break
  if i in selected:moments.add(i,frame,i/fps,eventframes.get(i,''))
  i+=1
 cap.release();moments.flush()
 summary=dict(cuts=len(cuts),important_events=len(important),static_intervals=len(static),static_seconds=round(sum(s['duration_s'] for s in static),3),story_samples=round(next_sample*6),important_frames=len(selected),analysis_seconds=round(time.time()-started,1))
 events=dict(source_name=source.name,fps=fps,frames=index,duration=index/fps,measurement_width=202,cuts=cuts,motion_events=motions,static_intervals=static,camera_segments=camera_segments,limitations=['Fluxo optico mede movimento da imagem, nao posicao fisica da camera.','Camera inferida usa direcao oposta ao movimento global da imagem; objetos animados podem dominar o ajuste.','Zoom e escala afim estimados podem ser movimento do objeto ou deformacao de IA.','Cortes sao candidatos; confirmar visualmente nas folhas de momentos.','Personagens repetidos podem causar alias de rastreamento e falso zoom mesmo com muitos inliers. Valores brutos preservados; transformacoes >1,2% escala/quadro ou >2% largura/altura/quadro rebaixadas para low e excluidas da agregacao. fit_confidence descreve so o ajuste; confidence operacional aplica esse filtro. Movimentos reais rapidos tambem podem cair em uncertain.','Medicoes em pixels referem-se a imagem reduzida para largura 202. Percentuais sao independentes da resolucao.','Textos e audio nao foram analisados por este script.'],summary=summary)
 (directory/'events.json').write_text(json.dumps(events,ensure_ascii=False,indent=2))
 report=['# '+source.name,'',f'{index} quadros | {fps:g} fps | {width}×{height} | {index/fps:.3f}s','',f'{len(sheets.paths)} folhas de historia a 6fps; {len(moments.paths)} folhas de todos os quadros nos momentos selecionados.','',f'{len(cuts)} cortes candidatos; {len(static)} intervalos de movimento global baixo ({summary["static_seconds"]}s somados).','', '## Cortes candidatos','', '| Quadro | Tempo | Confiança |','| ---: | --- | --- |']
 report.extend(f'| {c["frame"]} | {timestamp(c["time_s"])} | {c["confidence"]} |' for c in cuts)
 report+=['','## Intervalos parados ou quase parados','','| Início | Fim | Duração (s) | Tipo |','| --- | --- | ---: | --- |']
 report.extend(f'| {timestamp(s["start_s"])} | {timestamp(s["end_s"])} | {s["duration_s"]:.3f} | {s["kind"]} |' for s in static)
 report+=['','## Timeline de movimento global (janela de 0,267s)','','Direcoes dizem respeito ao movimento da imagem. Objetos podem dominar o ajuste.','','| Inicio | Fim | Estado | Mediana X/Y (px por quadro; largura202) | Zoom (% por quadro) |','| --- | --- | --- | --- | ---: |']
 for e in camera_segments:
  fmt=lambda value:'indeterminado' if value is None else f'{value:.3f}'
  report.append(f'| {timestamp(e["start_s"])} | {timestamp(e["end_s"])} | {e["kind"]} | {fmt(e["median_dx_px_per_frame"])}/{fmt(e["median_dy_px_per_frame"])} | {fmt(e["median_zoom_pct_per_frame"])} |')
 report+=['','## Limitações','']+['- '+l for l in events['limitations']]
 (directory/'report.md').write_text('\n'.join(report))
 result=dict(id=slug,source_name=source.name,source_path=str(source),duration=index/fps,fps=fps,width=width,height=height,frames=index,story_sheets=sheets.paths,important_sheets=moments.paths,camera_csv=str((directory/'camera.csv').relative_to(ROOT/'outputs')),events_json=str((directory/'events.json').relative_to(ROOT/'outputs')),report=str((directory/'report.md').relative_to(ROOT/'outputs')),summary=summary)
 print('DONE',source.name,summary,flush=True)
 return result


def build_bundle(directory):
 import html,zipfile
 index=json.loads((directory/'index.json').read_text())
 (directory/'LEIA-ME.md').write_text("""# Folhas e medições dos vídeos

story-*.jpg: seis quadros por segundo, sem interpolação; cada miniatura informa número do quadro original e tempo. moments-*.jpg: TODOS os quadros originais nas janelas de ±0,4s dos cortes candidatos e de oito movimentos selecionados por vídeo. Janelas sobrepostas são unidas. A seleção não afirma cobrir todo momento editorial importante; áudio e OCR complementam a análise.

camera.csv: uma linha por quadro; deslocamento X/Y da imagem, escala, rotação, pontos rastreados, inliers, cobertura e confiança. Pixels referem-se à largura202 de medição. events.json: cortes candidatos, intervalos aproximadamente parados e timeline resumida em janelas8quadros (0,267s). report.md: tabelas legíveis.

IMPORTANTE: fluxo óptico com ajuste afim RANSAC estima movimento da imagem, não a câmera física. Objetos animados e personagens repetidos podem provocar falso zoom mesmo com muitos inliers. fit_confidence avalia só o ajuste; confidence operacional rebaixa transformações de escala >1,2% por quadro ou deslocamento >2% largura/altura por quadro para low. Valores brutos são preservados; estimativas suspeitas ficam uncertain na agregação. Movimentos rápidos verdadeiros também podem ser marcados incertos. Direções da câmera são inferência oposta ao movimento global da imagem, sem garantia física.

Os arquivos de referência fornecidos são360x640 e202x360; upscale não recupera detalhe real. Estas folhas são evidência de análise, não material para republicação. Este script não transcreve nem faz OCR.
""")
 parts=['<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Folhas e câmera · CurioLab 3D</title><style>body{background:#161821;color:#eee;font:16px system-ui;max-width:1050px;margin:auto;padding:24px}a{color:#b3ef90}img{width:100%;height:auto}summary{cursor:pointer;padding:12px;background:#292e40;margin:6px 0}.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}figure{margin:0}figcaption{font-size:13px;padding:8px}</style><h1>Folhas de quadros e câmera</h1><p>6 quadros/s e todos os quadros originais nos momentos selecionados. Estimativas de câmera precisam de revisão.</p><p><a href="LEIA-ME.md">Método e limitações</a></p>']
 for video in index['videos']:
  parts+=['<h2>'+html.escape(video['source_name'])+'</h2>',f'<p>{video["frames"]} quadros · {video["fps"]:g}fps · {video["duration"]:.3f}s · {video["width"]}×{video["height"]} · {video["summary"]["cuts"]} cortes candidatos</p>',f'<p><a href="{video["id"]}/camera.csv">CSV por quadro</a> · <a href="{video["id"]}/events.json">Eventos JSON</a> · <a href="{video["id"]}/report.md">Relatório</a></p>']
  for key,label in [('story_sheets','História · 6fps'),('important_sheets','Momentos · todos os quadros')]:
   parts+=['<details><summary>'+label+f' · {len(video[key])} folhas</summary><div class="gallery">']
   for path in video[key]:
    rel=Path(path).relative_to(directory.relative_to(ROOT/'outputs')).as_posix()
    parts+=[f'<figure><a href="{rel}" target="_blank"><img loading="lazy" src="{rel}" alt="{label}"></a><figcaption>{html.escape(Path(rel).name)}</figcaption></figure>']
   parts+=['</div></details>']
 parts+=['</html>'];(directory/'index.html').write_text(''.join(parts))
 with zipfile.ZipFile(directory/'folhas-e-medidas.zip','w',zipfile.ZIP_DEFLATED) as archive:
  for path in directory.rglob('*'):
   if path.is_file() and path.suffix!='.zip':archive.write(path,path.relative_to(directory))


def main():
 p=argparse.ArgumentParser();p.add_argument('sources',nargs='*');p.add_argument('--output',type=Path,default=ROOT/'outputs/analysis');a=p.parse_args()
 sources=[Path(s) for s in a.sources] or sorted(Path('/workspace/attachments').rglob('*.mp4'))
 a.output=a.output.resolve()
 if not a.output.is_relative_to(ROOT/'outputs'):p.error('--output precisa ficar abaixo do diretório outputs do pacote.')
 a.output.mkdir(parents=True,exist_ok=True);results=[]
 for source in sources:
  results.append(analyze(source,a.output))
  (a.output/'index.json').write_text(json.dumps(dict(created_at=datetime.now(timezone.utc).isoformat(),videos=results),ensure_ascii=False,indent=2))
 build_bundle(a.output)
if __name__=='__main__':main()
