#!/usr/bin/env python3
"""Generate measured sRGB contrast and design roles for the shared channel palette."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
COLORS=[('shirt','Amarelo da assinatura','#E8BE45','Reconhecimento do personagem e foco da ação. Não usar como texto fino sobre fundo claro.'),('pants','Azul de apoio','#285878','Equilibra a roupa e separa pernas, objetos e ambiente.'),('shoes','Azul dos detalhes','#2E72B8','Acento secundário; usar de forma consistente.'),('hair','Castanho do cabelo','#34251E','Contraste para o rosto sem depender de preto puro.'),('skin','Pele quente','#DFA16D','Material de pele; preservar durante mudanças de cenário e luz.'),('accent_color','Destaque quente','#F2C94C','Etiquetas e botões com texto escuro; uma informação principal por vez.')]
def channels(value):return [int(value[i:i+2],16) for i in (1,3,5)]
def luminance(value):
 def linear(c):
  c=c/255
  return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
 c=[linear(v) for v in channels(value)]
 return c[0]*.2126+c[1]*.7152+c[2]*.0722

def contrast(a,b):
 x,y=sorted([luminance(a),luminance(b)])
 return (y+.05)/(x+.05)
def main():
 data={'title':'Paleta CurioLab: amarelo quente e contraste legível','working_space':'sRGB','colors':[{'key':key,'name':name,'hex':value,'rgb':channels(value),'role':role} for key,name,value,role in COLORS],
 'contrasts':[{'foreground':a,'background':b,'ratio':round(contrast(a,b),2),'normal_text_aa':contrast(a,b)>=4.5} for a,b in [('#292238','#F6F3E8'),('#292238','#E8BE45'),('#FFFFFF','#E8BE45'),('#E8BE45','#182338')]],
 'design_principles':['O amarelo quente é uma escolha de identidade, não uma garantia psicológica de atenção ou retenção.','Contexto, cultura, iluminação, tarefa e combinação mudam a percepção; evite promessas universais sobre cor.','60/30/10 é uma orientação de hierarquia visual, não uma medida fixa encontrada em todos os vídeos.','Mantenha os materiais do personagem; varie cenário e luz. Noite precisa de preenchimento para preservar rosto, olhos e silhueta.','Contraste WCAG se aplica à leitura de texto e interface. Para personagens 3D, teste silhueta, valor tonal e enquadramento também.'],
 'sources':[{'title':'W3C CSS Color 4 — sRGB e conversão linear','url':'https://www.w3.org/TR/css-color-4/','consulted_source':'https://raw.githubusercontent.com/w3c/csswg-drafts/main/css-color-4/Overview.bs','status':'consulted'}, {'title':'W3C WCAG — Understanding Contrast Minimum','url':'https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html','consulted_source':'https://raw.githubusercontent.com/w3c/wcag/main/understanding/20/contrast-minimum.html','status':'consulted'}, {'title':'Revisão científica de psicologia das cores — consulta pendente','url':'https://pubmed.ncbi.nlm.nih.gov/23724991/','status':'network_blocked','note':'Não foi usada como se tivesse sido lida nesta sessão.'}]}
 (ROOT/'web/color-guide.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
 lines=['# Paleta e ambientação CurioLab','','Espaço de trabalho: sRGB; valores RGB abaixo são valores de tela, não intensidade de luz.','','| Função | HEX | RGB | Uso |','| --- | --- | --- | --- |']
 for c in data['colors']:lines.append(f"| {c['name']} | {c['hex']} | {', '.join(map(str,c['rgb']))} | {c['role']} |")
 lines+=['','## Contraste calculado','','A relação usa luminância relativa sRGB conforme a fórmula WCAG. Critério AA de texto normal: pelo menos4,5:1. Não aplicar esse limiar diretamente como regra de aparência de personagens.','','| Primeiro plano | Fundo | Contraste | Texto normal AA |','| --- | --- | ---: | --- |']
 for c in data['contrasts']:lines.append(f"| {c['foreground']} | {c['background']} | {c['ratio']}:1 | {'passa' if c['normal_text_aa'] else 'não passa'} |")
 lines+=['','## Psicologia e direção visual','']+['- '+x for x in data['design_principles']]
 lines+=['','## Três ambientes','','Diurno: fundo azul suave e verde menos saturado; o personagem conserva a roupa amarela. Interior: neutros quentes, objetos azuis de apoio e luz preenchida. Noturno: fundo azul profundo e chão escuro, mantendo preenchimento no personagem; não escurecer tudo só para sinalizar noite. Os templates têm presets reais de ambiente; não são simulação fotométrica física.','','O motor converte os valores sRGB do personagem para intensidades lineares de material; iluminação e sombra ainda alteram os pixels resultantes. Registre cores de material e ambiente no projeto para repetir a identidade.','','## Fontes consultadas','']
 lines += [f"- {s['title']}: {s['url']} — {s['status']}." for s in data['sources']]
 lines+=['','A consulta técnica foi feita nas fontes oficiais W3C mantidas no GitHub. A revisão de psicologia foi bloqueada pelo proxy. Assim, associações de calor, energia ou reconhecimento são propostas de design, não conclusões científicas novas nem previsão de viralização.']
 (ROOT/'docs/PALETA-E-AMBIENTACAO.md').write_text('\n'.join(lines))
 print([(c['foreground'],c['background'],c['ratio']) for c in data['contrasts']])
if __name__=='__main__':main()
