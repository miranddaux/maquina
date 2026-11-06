#!/usr/bin/env python3
"""Self-contained panel preview. Never sends keys or simulates a paid render."""
import base64,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from panel_state import PanelState
from app import mascot_catalog

def data_url(path,mime):return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()
def main():
    # Keep the advanced editor available as a separate visual page.
    subprocess.run([sys.executable,str(ROOT/'tools/export_editor_visual.py')],check=True)
    (ROOT/'outputs/curiolab-editor-visual.html').write_bytes((ROOT/'outputs/curiolab-visual.html').read_bytes())
    store=PanelState(ROOT);models=store.models()
    for model in models['models']:
        p=ROOT/'web'/model.get('thumbnail','').lstrip('/')
        if p.is_file():model['thumbnail']=data_url(p,'image/png')
    videos=store.videos()
    videos['videos']=[v for v in videos['videos'] if v['id'] in ['sala-amarela-fullhd','casa-fullhd']]
    for video in videos['videos']:
        video['url']=data_url(ROOT/'outputs'/(video['id']+'.mp4'),'video/mp4')
    videos['count']=len(videos['videos'])
    readiness=store.readiness()
    for check in readiness['checks']:check['detail']+=' Verificação do ambiente desta demonstração, não deste navegador.'
    mascots=mascot_catalog()
    for mascot in mascots['mascots']:
        for version in mascot['versions']:
            version['viewer_url']='nico-visual.html'
            for view,url in list(version['preview_urls'].items()):
                path=ROOT/'assets/mascots'/url.removeprefix('/mascot-assets/')
                version['preview_urls'][view]=data_url(path,'image/png')
    snapshot={'mascots':mascots,'channel':store.channel(),'method':store.method(),'models':models,'videos':videos,'readiness':readiness}
    html=(ROOT/'web/panel.html').read_text();css=(ROOT/'web/panel.css').read_text();js=(ROOT/'web/panel.js').read_text()
    bootstrap='''
window.__CURIOLAB_VISUAL_PREVIEW__=true;
const PREVIEW=SNAPSHOT;
const requestMemory=[];const assetMemory=[];
window.fetch=async(path,options={})=>{
 let body={};try{body=JSON.parse(options.body||'{}')}catch{}
 const response=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json'}});
 const post=options.method==='POST';
 if(path.startsWith('/api/voice/'))return response({error:'Conexões e geração de voz funcionam no aplicativo executável. Não cole chaves nesta prévia visual.'},409);
 if(path==='/api/channel'){if(post){PREVIEW.channel={...PREVIEW.channel,...body};}return response(PREVIEW.channel);}
 if(path==='/api/method'){if(post)PREVIEW.method={...PREVIEW.method,...body};return response(PREVIEW.method);}
 if(path==='/api/method/reset')return response(PREVIEW.method);
 if(path==='/api/readiness')return response(PREVIEW.readiness);
 if(path==='/api/mascots')return response(PREVIEW.mascots);
 if(path==='/api/models')return response(PREVIEW.models);
 if(path==='/api/videos')return response(PREVIEW.videos);
 if(path==='/api/assets'&&post){const extension=body.filename.split('.').pop().toLowerCase();const asset={id:crypto.randomUUID().replaceAll('-',''),filename:body.filename,kind:'image',url:'data:image/'+(extension==='jpg'?'jpeg':extension)+';base64,'+body.data_base64};assetMemory.push(asset);return response(asset);}
 if(path==='/api/assets')return response({assets:assetMemory});
 if(path==='/api/requests'&&post){const id=crypto.randomUUID().replaceAll('-','');const item={id,prompt:body.prompt,status:'awaiting_codex',brief:'Pedido desta prévia visual: '+body.prompt,handoff:'No aplicativo executável, prepare este pedido para Claude Code ou Codex: '+body.prompt,instruction:'Este pedido existe só nesta aba da prévia; use o aplicativo para criar os arquivos permanentes.'};requestMemory.unshift(item);return response(item,201);}
 if(path==='/api/requests')return response({requests:requestMemory,count:requestMemory.length});
 if(path==='/color-guide.json')return response(COLOR_GUIDE);
 return response({error:'Esta prévia HTML mostra a interface. Para usar arquivos, integrações e exportação, abra o pacote executável.'},409);
};
'''.replace('SNAPSHOT',json.dumps(snapshot,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')).replace('COLOR_GUIDE',(ROOT/'web/color-guide.json').read_text())
    html=html.replace('<link rel="stylesheet" href="/panel.css">','<style>'+css+'\n.visual-banner{background:#F2C94C;color:#292238;padding:12px 20px;font:600 13px/1.5 system-ui;text-align:center;position:relative;z-index:5}.shell{min-height:calc(100vh - 45px)}</style>')
    html=html.replace('<script src="/panel.js" defer></script>','')
    html=html.replace('<body>','<body><div class="visual-banner">PRÉVIA HTML · Explore o painel e os vídeos reais desta sessão. Alterações ficam nesta aba. Integrações, arquivos permanentes e novos renders exigem o aplicativo. Não cole chaves nesta prévia.</div>')
    html=html.replace('href="/studio.html"','href="curiolab-editor-visual.html"').replace('href="/api/skill/download"','href="curiolab-3d-skill.zip"')
    def document_link(match):
        path=ROOT/'docs'/match.group(1)
        return 'href="'+(data_url(path,'text/plain;charset=utf-8') if path.is_file() else '#ajuda')+'"'
    html=re.sub(r'href="/docs/([^"?]+)"',document_link,html)
    html=html.replace('href="/api/channel/export"','href="'+ 'data:application/json;base64,'+base64.b64encode(json.dumps(snapshot['channel'],ensure_ascii=False,indent=2).encode()).decode()+'"')
    html=html.replace('</body>','<script>'+bootstrap+'\n'+js.replace('</script>','<\\/script>')+"\nsetTimeout(()=>{document.getElementById('connection-state').textContent='Prévia visual · dados da demonstração';document.getElementById('voice-api-key').disabled=true;},50);"+'</script></body>')
    target=ROOT/'outputs/curiolab-visual.html';target.write_text(html)
    print('Painel visual autocontido:',target)
if __name__=='__main__':main()
