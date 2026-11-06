#!/usr/bin/env python3
"""OCR/audio evidence for user-supplied videos. No paid APIs, no invented words."""
import argparse,csv,json,os,re,subprocess,concurrent.futures
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def slug(p):
 return re.sub(r'[^a-z0-9]+','-',p.stem.lower()).strip('-')
def run(args,**kwargs):
 return subprocess.run(args,check=True,**kwargs)
def meta(p):
 return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
def write_json(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def audio(p,directory):
 out=directory/'audio.wav'
 if not out.exists():run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(p),'-vn','-ar','16000','-ac','1',str(out)])
 cmd=['ffmpeg','-hide_banner','-i',str(p),'-vn','-af','silencedetect=noise=-35dB:d=0.20,volumedetect','-f','null','-']
 result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=True)
 text=result.stderr
 starts=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',text)]
 ends=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',text)]
 pairs=[dict(start=s,end=next((e for e in ends if e>s),None)) for s in starts]
 levels={k:float(v) for k,v in re.findall(r'(mean_volume|max_volume): (-?[\d.]+) dB',text)}
 data=dict(status='measured',silence_threshold_db=-35,silence_min_duration_s=.2,silence_intervals=pairs,levels_db=levels,
  note='Medições de sinal; não identificam por si só música, voz, efeitos ou o que foi dito.',audio_path=str(out.relative_to(ROOT)))
 write_json(directory/'audio_measurements.json',data)
 return out,data

def ocr(p,directory,fps=6,caption_only=False):
 from PIL import Image,ImageEnhance,ImageFilter
 from tesserocr import PyTessBaseAPI,PSM
 os.environ['OMP_THREAD_LIMIT']='1'
 info=meta(p);stream=next(s for s in info['streams'] if s['codec_type']=='video')
 width,height=stream['width'],stream['height']
 # Keep native aspect and enlarge only inside OCR. fps6 gives ±167ms sampling uncertainty.
 cmd=['ffmpeg','-hide_banner','-loglevel','error','-threads','1','-i',str(p),'-vf',f'fps={fps}', '-f','rawvideo','-pix_fmt','rgb24','-']
 proc=subprocess.Popen(cmd,stdout=subprocess.PIPE)
 records=[];index=0;framebytes=width*height*3
 with PyTessBaseAPI(path=str(ROOT/'.local/tessdata'),lang='por',psm=PSM.SINGLE_LINE if caption_only else PSM.SPARSE_TEXT) as api:
  api.SetVariable('preserve_interword_spaces','1')
  while True:
   raw=proc.stdout.read(framebytes)
   if len(raw)!=framebytes:break
   img=Image.frombytes('RGB',(width,height),raw)
   if caption_only:
    img=img.crop((0,int(height*.64),width,int(height*.735))).resize((width*3,int(height*.095)*3),Image.Resampling.LANCZOS)
    img=img.convert('L').point(lambda x:0 if x>215 else 255)
   else:
    img=img.resize((width*2,height*2),Image.Resampling.LANCZOS)
   api.SetImage(img)
   text=api.GetUTF8Text().strip();confidence=api.MeanTextConf()
   lines=[' '.join(line.split()) for line in text.splitlines() if line.strip()]
   if lines:
    records.append(dict(time=round(index/fps,4),frame_index=round(index*30/fps),text='\n'.join(lines),confidence=confidence))
   index+=1
 proc.stdout.close();proc.wait()
 if proc.returncode:raise RuntimeError('ffmpeg não conseguiu extrair todos os quadros para OCR.')
 # Exact consecutive duplicates only: never treat OCR as corrected transcript.
 events=[]
 for r in records:
  if events and r['text']==events[-1]['text'] and r['time']-events[-1]['last_observed']<=2/fps:
   events[-1]['last_observed']=r['time'];events[-1]['end']=round(r['time']+1/fps,4)
  else:
   events.append(dict(start=r['time'],end=round(r['time']+1/fps,4),last_observed=r['time'],text=r['text'],confidence=r['confidence']))
 payload=dict(status='completed',source=p.name,sampling_fps=fps,total_samples=index,raw_ocr=True,
  method='white_caption_mask_single_line' if caption_only else 'full_frame_sparse_text',
  crop_y_fraction=[.64,.735] if caption_only else [0,1],
  timing_uncertainty_seconds=1/fps,note='OCR automático não revisado, fonte com baixa resolução. Erros e palavras incompletas são possíveis. Texto de tela não é transcrição de áudio.',events=events)
 basename='caption_text' if caption_only else 'onscreen_text'
 if caption_only:
  payload['review_note']='Faixa de legenda y64%–73,5%; OCR não é voz. Confiança Tesseract é heurística, não taxa medida de acerto.'
 write_json(directory/(basename+'.json'),payload)
 with (directory/(basename+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['start','end','last_observed','text','confidence']);w.writeheader();w.writerows(events)
 if caption_only:
  lines=['# Legendas visuais: OCR automático','','Não é transcrição de áudio. Amostragem±0,167s; somente confiança Tesseract≥70. Há palavras ausentes e erros.','']
  lines += [f"{e['start']:.3f}–{e['end']:.3f} | {e['text']} | {e['confidence']}" for e in events if e['confidence']>=70]
  (directory/'caption_sequence.md').write_text('\n'.join(lines),encoding='utf8')
 return payload

def transcribe(p,audio_path,directory,model_name,allow_download=False):
 try:
  from faster_whisper import WhisperModel
  model=WhisperModel(model_name,device='cpu',compute_type='int8',cpu_threads=4,num_workers=1,
      download_root=str(ROOT/'.local/models'),local_files_only=not allow_download)
  segments,info=model.transcribe(str(audio_path),language='pt',word_timestamps=True,vad_filter=True,beam_size=5,
      condition_on_previous_text=False)
  rows=[];segs=[]
  for seg in segments:
   segs.append(dict(start=seg.start,end=seg.end,text=seg.text))
   for word in seg.words or []:
    rows.append(dict(start=round(word.start,3),end=round(word.end,3),word=word.word.strip(),
      probability=round(word.probability,4),needs_review=word.probability<.7))
  data=dict(status='completed',source=p.name,language='pt',model=model_name,words=rows,segments=segs,
      note='Reconhecimento automático; tempos estimados pelo modelo, não alinhamento humano. Revisar palavras de baixa confiança.')
  write_json(directory/'transcript.json',data)
  with (directory/'words.csv').open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=['start','end','word','probability','needs_review']);w.writeheader();w.writerows(rows)
  (directory/'transcript.txt').write_text('\n'.join(s['text'].strip() for s in segs),encoding='utf8')
  return data
 except Exception as e:
  data=dict(status='blocked',source=p.name,model=model_name,reason='Modelo ASR local indisponível; download exige acesso ao host oficial do modelo.',
      error_type=type(e).__name__,required_hosts=['huggingface.co','cas-bridge.xethub.hf.co'],words=[],segments=[])
  write_json(directory/'transcript.json',data)
  return data

def process(p,args):
 ident=slug(p);ad=ROOT/'outputs/transcripts'/ident;od=ROOT/'outputs/ocr'/ident
 ad.mkdir(parents=True,exist_ok=True);od.mkdir(parents=True,exist_ok=True)
 wav=ad/'audio.wav'
 if not args.caption_only:wav,signal=audio(p,ad)
 text=None
 if not args.asr_only:text=ocr(p,od,args.ocr_fps,args.caption_only)
 speech=transcribe(p,wav,ad,args.model,args.allow_model_download) if not args.skip_asr and not args.caption_only else dict(status='not_run')
 print(json.dumps(dict(video=ident,ocr_samples=text['total_samples'] if text else None,speech=speech['status']),ensure_ascii=False),flush=True)
 return dict(id=ident,source=p.name,ocr_path=str((od/'onscreen_text.json').relative_to(ROOT)),
   transcript_path=str((ad/'transcript.json').relative_to(ROOT)),audio_path=str(wav.relative_to(ROOT)),speech_status=speech['status'])

def main():
 ap=argparse.ArgumentParser();ap.add_argument('videos',nargs='*',type=Path)
 ap.add_argument('--ocr-fps',type=int,default=6);ap.add_argument('--model',default='small')
 ap.add_argument('--caption-only',action='store_true');ap.add_argument('--skip-asr',action='store_true');ap.add_argument('--asr-only',action='store_true')
 ap.add_argument('--allow-model-download',action='store_true');ap.add_argument('--workers',type=int,default=2)
 args=ap.parse_args();videos=args.videos or sorted(Path('/workspace/attachments').rglob('*.mp4'))
 if not 1<=args.ocr_fps<=12:ap.error('OCR fps precisa estar entre 1 e 12.')
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
  results=list(pool.map(lambda p:process(p,args),videos))
 root=ROOT/'outputs/transcripts';root.mkdir(parents=True,exist_ok=True)
 write_json(root/('caption_index.json' if args.caption_only else 'index.json'),dict(videos=results,note='Arquivos enviados pelo usuário. Métricas YouTube não estão contidas no MP4.'))
if __name__=='__main__':main()
