#!/usr/bin/env python3
"""Export self-contained visual preview, separate from the executable studio."""
import base64,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    html=(ROOT/'web/index.html').read_text()
    css=(ROOT/'web/styles.css').read_text()
    js=(ROOT/'web/app.js').read_text()
    samples=[]
    for p in sorted((ROOT/'outputs/analysis').glob('*/story-001.jpg')):
        encoded=base64.b64encode(p.read_bytes()).decode()
        samples.append(dict(category='analysis',name=p.parent.name+'-story-001.jpg',url='data:image/jpeg;base64,'+encoded,size_bytes=p.stat().st_size))
    bootstrap='''
// This preview stores edits only in this tab and never runs a render or paid API.
const previewProjects=new Map(),previewAssets=new Map();
const previewSheets=SHEETS_PLACEHOLDER;
window.fetch=async(path,options={})=>{
 let body={};try{body=JSON.parse(options.body||'{}')}catch{}
 const ok=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json'}});
 if(path==='/api/status')return ok({tools:{ffmpeg:false,blender:false},mode:'visual_preview'});
 if(path==='/api/assets'&&options.method==='POST'){
  const id=crypto.randomUUID().replaceAll('-','');
  const extension=body.filename.split('.').pop().toLowerCase();
  const kind=['mp3','wav','m4a'].includes(extension)?'audio':'image';
  const mime=kind==='image'?(extension==='jpg'?'image/jpeg':'image/'+extension):'audio/mpeg';
  const asset={id,filename:body.filename,kind,url:'data:'+mime+';base64,'+body.data_base64};previewAssets.set(id,asset);return ok(asset,201);
 }
 if(path==='/api/assets')return ok({assets:[...previewAssets.values()]});
 if(path==='/api/analysis')return ok({files:previewSheets,index:null});
 if(path==='/api/projects'&&!options.method)return ok({projects:[...previewProjects.values()]});
 if(path.startsWith('/api/projects')&&options.method==='POST'&&!path.endsWith('/render')){
  const id=path==='/api/projects'?crypto.randomUUID().replaceAll('-',''):path.split('/')[3];
  const project={...body,id,title:body.topic};previewProjects.set(id,project);return ok(project);
 }
 if(path.startsWith('/api/projects/')&&!options.method)return ok(previewProjects.get(path.split('/')[3])||{});
 return ok({error:'Esta é uma prévia HTML. Execute o projeto local para renderizar, exportar e salvar arquivos permanentes.'},409);
};
'''.replace('SHEETS_PLACEHOLDER',json.dumps(samples,ensure_ascii=False))
    html=html.replace('<link rel="stylesheet" href="/styles.css">','<style>'+css+'\n.preview-banner{position:relative;z-index:50;background:#d9f27b;color:#252034;padding:12px 24px;font:600 13px/1.5 system-ui;text-align:center}.preview-banner strong{margin-right:12px}.app-shell{min-height:calc(100vh - 45px)}</style>')
    html=html.replace('<script src="/app.js" defer></script>','')
    html=html.replace('<body>','<body><div class="preview-banner"><strong>PRÉVIA HTML VISUAL</strong>Você pode explorar e editar nesta aba. Renderização MP4 e salvamento permanente funcionam no projeto executável.</div>')
    html=html.replace('href="/"','href="#workspace"').replace('href="/landing.html"','href="curiolab-apresentacao.html"').replace('href="/api/skill/download"','href="curiolab-3d-skill.zip"')
    html=html.replace('name=','name=')
    html=html.replace('</body>','<script>'+bootstrap+'\n'+js.replace('</script>','<\\/script>')+"\nsetTimeout(()=>document.getElementById('system-status').textContent='Prévia visual · exportação no projeto local',20);"+'</script></body>')
    target=ROOT/'outputs/curiolab-visual.html';target.write_text(html)
    landing=(ROOT/'web/landing.html').read_text().replace('<link rel="stylesheet" href="/styles.css">','<style>'+css+'</style>').replace('href="/"','href="curiolab-visual.html"').replace('href="/api/skill/download"','href="curiolab-3d-skill.zip"')
    (ROOT/'outputs/curiolab-apresentacao.html').write_text(landing)
    print(target)
if __name__=='__main__':main()
