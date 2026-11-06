# Paleta e ambientação CurioLab

Espaço de trabalho: sRGB; valores RGB abaixo são valores de tela, não intensidade de luz.

| Função | HEX | RGB | Uso |
| --- | --- | --- | --- |
| Amarelo da assinatura | #E8BE45 | 232, 190, 69 | Reconhecimento do personagem e foco da ação. Não usar como texto fino sobre fundo claro. |
| Azul de apoio | #285878 | 40, 88, 120 | Equilibra a roupa e separa pernas, objetos e ambiente. |
| Azul dos detalhes | #2E72B8 | 46, 114, 184 | Acento secundário; usar de forma consistente. |
| Castanho do cabelo | #34251E | 52, 37, 30 | Contraste para o rosto sem depender de preto puro. |
| Pele quente | #DFA16D | 223, 161, 109 | Material de pele; preservar durante mudanças de cenário e luz. |
| Destaque quente | #F2C94C | 242, 201, 76 | Etiquetas e botões com texto escuro; uma informação principal por vez. |

## Contraste calculado

A relação usa luminância relativa sRGB conforme a fórmula WCAG. Critério AA de texto normal: pelo menos4,5:1. Não aplicar esse limiar diretamente como regra de aparência de personagens.

| Primeiro plano | Fundo | Contraste | Texto normal AA |
| --- | --- | ---: | --- |
| #292238 | #F6F3E8 | 13.7:1 | passa |
| #292238 | #E8BE45 | 8.61:1 | passa |
| #FFFFFF | #E8BE45 | 1.77:1 | não passa |
| #E8BE45 | #182338 | 8.89:1 | passa |

## Psicologia e direção visual

- O amarelo quente é uma escolha de identidade, não uma garantia psicológica de atenção ou retenção.
- Contexto, cultura, iluminação, tarefa e combinação mudam a percepção; evite promessas universais sobre cor.
- 60/30/10 é uma orientação de hierarquia visual, não uma medida fixa encontrada em todos os vídeos.
- Mantenha os materiais do personagem; varie cenário e luz. Noite precisa de preenchimento para preservar rosto, olhos e silhueta.
- Contraste WCAG se aplica à leitura de texto e interface. Para personagens 3D, teste silhueta, valor tonal e enquadramento também.

## Três ambientes

Diurno: fundo azul suave e verde menos saturado; o personagem conserva a roupa amarela. Interior: neutros quentes, objetos azuis de apoio e luz preenchida. Noturno: fundo azul profundo e chão escuro, mantendo preenchimento no personagem; não escurecer tudo só para sinalizar noite. Os templates têm presets reais de ambiente; não são simulação fotométrica física.

O motor converte os valores sRGB do personagem para intensidades lineares de material; iluminação e sombra ainda alteram os pixels resultantes. Registre cores de material e ambiente no projeto para repetir a identidade.

## Fontes consultadas

- W3C CSS Color 4 — sRGB e conversão linear: https://www.w3.org/TR/css-color-4/ — consulted.
- W3C WCAG — Understanding Contrast Minimum: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html — consulted.
- Revisão científica de psicologia das cores — consulta pendente: https://pubmed.ncbi.nlm.nih.gov/23724991/ — network_blocked.

A consulta técnica foi feita nas fontes oficiais W3C mantidas no GitHub. A revisão de psicologia foi bloqueada pelo proxy. Assim, associações de calor, energia ou reconhecimento são propostas de design, não conclusões científicas novas nem previsão de viralização.