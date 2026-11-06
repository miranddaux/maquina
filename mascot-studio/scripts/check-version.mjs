import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const root=path.resolve(import.meta.dirname,'../..');
const lockPath=path.join(root,'shared/mascots/nico/1.0.0-candidate.1/source-lock.json');
const lock=JSON.parse(fs.readFileSync(lockPath,'utf8'));
for(const [relative,expected] of Object.entries(lock.files)){
 const file=path.resolve(root,relative);
 if(!file.startsWith(root+path.sep))throw new Error('Caminho inválido no registro.');
 const actual=crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
 if(actual!==expected)throw new Error(`Fonte versionada alterada: ${relative}. Crie e revise uma nova versão; não redesenhe uma versão existente.`);
}
console.log(`Fontes bloqueadas: ${lock.id}@${lock.version} (${Object.keys(lock.files).length} arquivos).`);
