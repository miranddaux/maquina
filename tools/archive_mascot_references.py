#!/usr/bin/env python3
"""Archive original user-supplied image bytes without changing approved model versions."""
import argparse,hashlib,json,os,shutil,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from mascot_registry import MascotRegistry

def main():
 p=argparse.ArgumentParser();p.add_argument('--mascot',default='nico');p.add_argument('--version',required=True);p.add_argument('--reference',action='append',type=Path,required=True)
 a=p.parse_args();registry=MascotRegistry(ROOT);config=registry.load(a.mascot,a.version)
 if config['status']!='candidate':p.error('Referências de versões aprovadas são imutáveis; crie outra versão.')
 if len(a.reference)!=2:p.error('Forneça os dois arquivos originais com --reference repetido.')
 target=ROOT/'assets/mascots'/a.mascot/a.version/'references';records=[]
 for index,source in enumerate(a.reference,1):
  data=source.read_bytes();extension=source.suffix.lower()
  if len(data)>32*1024*1024:p.error('Cada referência deve ter até32MiB.')
  if not ((extension=='.png' and data.startswith(b'\x89PNG\r\n\x1a\n')) or (extension in ['.jpg','.jpeg'] and data.startswith(b'\xff\xd8\xff'))):p.error('Use PNG/JPG originais válidos.')
  digest=hashlib.sha256(data).hexdigest();path=target/f'reference-{index:02}{extension}'
  if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()!=digest:p.error('Um arquivo diferente já existe nesse caminho; nada será sobrescrito.')
  records.append({'kind':'reference','path':str(path.relative_to(ROOT)),'sha256':digest,'status':'archived_original','original_name':source.name})
 if records[0]['sha256']==records[1]['sha256']:p.error('As duas referências devem ser arquivos diferentes.')
 target.mkdir(parents=True,exist_ok=True)
 for source,record in zip(a.reference,records):
  destination=ROOT/record['path']
  if not destination.exists():shutil.copy2(source,destination)
 manifest_path=ROOT/'shared/mascots'/a.mascot/a.version/'manifest.json';manifest=json.loads(manifest_path.read_text())
 manifest['assets']=[r for r in manifest.get('assets',[]) if r.get('kind')!='reference']+records
 fd,temp=tempfile.mkstemp(prefix='.manifest-',dir=manifest_path.parent)
 try:
  with os.fdopen(fd,'w') as f:json.dump(manifest,f,ensure_ascii=False,indent=2)
  os.replace(temp,manifest_path)
 finally:
  if os.path.exists(temp):os.unlink(temp)
 registry.load(a.mascot,a.version)
 print('Dois originais arquivados byte a byte; modelo continua candidato até aprovação visual.')
if __name__=='__main__':main()
