#!/usr/bin/env python3
"""Image-based vertical compositor. Real pan/zoom, not generated 3D geometry."""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
from render import ass_time, subtitle_text

def load_project(path):
    project=json.loads(Path(path).read_text())
    if not isinstance(project,dict):raise ValueError('Projeto deve ser objeto JSON.')
    width,height=project.get('width',1080),project.get('height',1920)
    if (width,height) not in [(360,640),(720,1280),(1080,1920)]:raise ValueError('Resolução vertical não suportada.')
    scenes=project.get('scenes')
    if not isinstance(scenes,list) or not 1<=len(scenes)<=40:raise ValueError('Use entre 1 e 40 cenas.')
    cursor=0
    for scene in scenes:
        if not isinstance(scene,dict):raise ValueError('Cena inválida.')
        start,end=scene.get('start'),scene.get('end')
        if any(isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) for v in [start,end]):raise ValueError('Tempos inválidos.')
        if abs(start-cursor)>.02 or not .5<=end-start<=60:raise ValueError('As cenas devem ser contínuas, em ordem, com duração de 0,5 a 60s.')
        cursor=end
        if not Path(scene.get('image_path','')).is_file():raise ValueError('Imagem da cena não encontrada.')
        if scene.get('motion','zoom_in') not in ['zoom_in','zoom_out','pan_left','pan_right','static']:raise ValueError('Movimento não suportado.')
        if not isinstance(scene.get('caption',''),str) or len(scene.get('caption',''))>240:raise ValueError('Legenda deve ter até 240 caracteres.')
    if cursor>180:raise ValueError('Duração máxima: 180s.')
    if abs(float(project.get('duration',cursor))-cursor)>.02:raise ValueError('A duração do projeto deve coincidir com a última cena.')
    narration=project.get('narration_path')
    if narration:
        if not Path(narration).is_file():raise ValueError('Narração não encontrada.')
        duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(narration)],text=True))
        if duration>cursor+.25:raise ValueError(f'O áudio tem {duration:.1f}s, maior que o vídeo ({cursor:.1f}s). Ajuste a timeline para não cortar a fala.')
    return {**project,'width':width,'height':height,'fps':30,'duration':cursor}

def write_captions(project,path):
    head='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,DejaVu Sans,76,&H00FFFFFF,&H0000DFFF,&H00161220,&H80161220,-1,0,0,0,100,100,0,0,1,5,2,8,80,80,220,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    lines=[head]
    for scene in project['scenes']:
        text=scene.get('caption','').strip().upper()
        wrapped='\n'.join(textwrap.wrap(text,width=24,break_long_words=False))
        lines.append(f"Dialogue: 0,{ass_time(scene['start'])},{ass_time(scene['end'])},Main,,0,0,0,,{{\\fad(120,100)}}{subtitle_text(wrapped)}\n")
    path.write_text(''.join(lines),encoding='utf8')

def motion_filter(motion,frames,width,height):
    # Crop starts from oversized input; movement is deterministic across frames.
    step=.10/max(frames-1,1)
    if motion=='zoom_in':z=f'1+on*{step}';x='iw/2-iw/zoom/2';y='ih/2-ih/zoom/2'
    elif motion=='zoom_out':z=f'1.10-on*{step}';x='iw/2-iw/zoom/2';y='ih/2-ih/zoom/2'
    elif motion=='pan_left':z='1.10';x=f'(iw-iw/zoom)*(1-on/{max(frames-1,1)})';y='ih/2-ih/zoom/2'
    elif motion=='pan_right':z='1.10';x=f'(iw-iw/zoom)*on/{max(frames-1,1)}';y='ih/2-ih/zoom/2'
    else:z='1';x='iw/2-iw/zoom/2';y='ih/2-ih/zoom/2'
    return f"scale={width*2}:{height*2}:force_original_aspect_ratio=increase,crop={width*2}:{height*2},zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={width}x{height}:fps=30,setsar=1"

def render(project,output):
    output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    if output.suffix.lower()!='.mp4':raise ValueError('Saída deve ser MP4.')
    with tempfile.TemporaryDirectory(prefix='.composition-',dir=output.parent) as directory:
        tmp=Path(directory)
        for i,scene in enumerate(project['scenes']):
            frames=round((scene['end']-scene['start'])*30)
            filt=motion_filter(scene.get('motion','zoom_in'),frames,project['width'],project['height'])
            target=tmp/f'scene-{i:03}.mp4'
            print(json.dumps({'stage':'scene','scene':i+1,'total':len(project['scenes'])}),flush=True)
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-threads','2','-i',str(Path(scene['image_path']).resolve()),'-vf',filt,'-frames:v',str(frames),'-an','-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(target)],check=True)
        listing=tmp/'concat.txt'
        listing.write_text(''.join(f"file 'scene-{i:03}.mp4'\n" for i in range(len(project['scenes']))))
        subs=tmp/'captions.ass';write_captions(project,subs)
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(listing)]
        narration=project.get('narration_path')
        if narration:cmd+=['-i',str(Path(narration).resolve())]
        else:cmd+=['-f','lavfi','-i','anullsrc=r=48000:cl=stereo']
        # Filename in filter is fixed, evaluated in the temporary working directory.
        cmd+=['-vf','ass=captions.ass','-map','0:v:0','-map','1:a:0','-af','loudnorm=I=-16:TP=-1.5:LRA=11,apad','-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-t',str(project['duration']),'-movflags','+faststart',str(tmp/'complete.mp4')]
        subprocess.run(cmd,cwd=tmp,check=True)
        os.replace(tmp/'complete.mp4',output)
    print(json.dumps({'status':'complete','output':str(output),'width':project['width'],'height':project['height'],'duration':project['duration'],'silent':not bool(narration),'mode':'image_composition'}),flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',required=True);p.add_argument('--output',required=True)
    args=p.parse_args()
    try:render(load_project(args.project),args.output)
    except (ValueError,OSError,subprocess.CalledProcessError) as exc:p.exit(1,'Falha na composição: '+str(exc)+'\n')
if __name__=='__main__':main()
