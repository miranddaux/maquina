# Análise crítica dos quatro vídeos fornecidos

Material analisado: os quatro MP4s enviados pelo usuário, e não uma reprodução presumida dos links anteriores. Inspeção visual por folhas de quadros, incluindo os começos, os encerramentos e as etapas de montagem; medições automáticas de imagem quadro a quadro; leitura de textos visíveis. Não é uma auditoria do projeto-fonte do autor: software, modelos, prompts e custos não podem ser identificados com certeza pelo MP4.

## Fonte e limites de precisão

| Arquivo | Assunto identificado na imagem | Quadros decodificados | Linha de vídeo | Resolução real |
| --- | --- | ---: | ---: | --- |
| Como-se-constroi-SnapYT.App.mp4 | Estádio de futebol | 4.208 | 140,267 s | 360×640, 30 fps |
| Como-uma-casa-SnapYT.App.mp4 | Estrutura e acabamento de casa | 5.055 | 168,500 s | 360×640, 30 fps |
| Como-construir-um-SnapYT.App.mp4 | Muro de arrimo | 4.281 | 142,700 s | 360×640, 30 fps |
| Como-um-paraquedas-SnapYT.App (1).mp4 | Evolução e segurança de um paraquedas | 5.129 | 170,967 s | 202×360, 30 fps |

A duração de contêiner/áudio é ligeiramente maior que a linha de quadros: 140,331; 168,555; 142,763; 171,015 s, respectivamente. Para cortes, usar número de quadro e sua apresentação; para áudio, o tempo da faixa. Os vídeos têm entre 2min20s e 2min51s. Não são demonstrações de 30 ou 45 segundos.

`outputs/analysis/index.json` relaciona as folhas a seis amostras por segundo, as folhas com todos os quadros nas janelas importantes, `camera.csv`, `events.json` e `report.md` de cada arquivo. O CSV preserva os quadros originais; as folhas de história mostram um em cada cinco quadros de uma fonte a 30 fps. OCR é texto de tela, não reconhecimento do que foi dito. O limite temporal de OCR a 6 fps é aproximadamente 167 ms; não é alinhamento de voz por palavra.

O fluxo óptico mede a imagem. Repetição de bonecos, água, árvores, legendas e inserção de peças podem enganar a inferência de câmera. Um zoom aparente também pode ser deslocamento do objeto. Por exemplo, o primeiro ajuste automático do estádio indicou escala excessiva entre personagens muito semelhantes; isso foi marcado como indeterminado na confiança operacional, preservando os valores brutos no CSV. Não converter esses números em distância focal ou metros de câmera.

## Resumo das medições automáticas

| Vídeo | Cortes candidatos | Intervalos com movimento global baixo | Soma desses intervalos | Maior intervalo por quadro |
| --- | ---: | ---: | ---: | ---: |
| Estádio | 49 | 53 | 48,000 s | 3,633 s |
| Casa | 21 | 75 | 104,667 s | 7,167 s |
| Muro | 8 | 57 | 58,933 s | 3,067 s |
| Paraquedas | 22 | 27 | 19,933 s | 1,867 s |

Os cortes são candidatos, incluindo transições e alterações rápidas de cenário; não foram todos certificados como cortes de edição. “Movimento global baixo” não garante câmera física parada. As janelas `camera_segments` agrupam leituras para navegação e podem juntar ou alargar intervalos; as durações da tabela vêm de `static_intervals`, calculados quadro a quadro. Na revisão de qualidade, 1.002/688/854/1.085 quadros de estádio/casa/muro/paraquedas, respectivamente, receberam advertência de movimento rápido ou padrões repetidos. Valores brutos nesses quadros não devem orientar uma câmera de produção sem revisão visual.

**Camada ainda pendente:** transcrição de voz, marcas por palavra falada e identificação auditiva de música/efeitos. O download do modelo de reconhecimento de fala foi bloqueado. A análise de sinal e a leitura de legendas não completam essa camada.

## O padrão que realmente se repete

Os quatro começam com **“Se”**, sem vinheta e sem apresentação do narrador. A primeira situação já está visível. O mecanismo é uma experiência causal: tentar uma solução simples, vê-la falhar, acrescentar a peça que resolve aquela falha e descobrir o próximo problema. As peças ficam acumuladas no mesmo mundo. Isso gera uma pergunta implícita: “o que ainda falta para funcionar?”.

A construção é mostrada como mudança de estado, não como uma coleção de imagens soltas. Rebobinar e acelerar são convenções gráficas explícitas: setas duplas, linhas horizontais e retorno à situação anterior. Setas coloridas representam água, força, ar ou direção. O corte no solo/estrutura permite enxergar o mecanismo oculto. O resultado completo só é nomeado e comemorado perto do fim.

### Textos observados nas aberturas

São leituras das legendas visíveis, não transcrições certificadas de áudio:

- Estádio: “Se você tem dois times, uma bola, já tem uma partida de futebol”; a imagem passa dos dois grupos para o campo aberto. Em seguida, buraco e torção do pé apresentam a primeira falha.
- Casa: “Se você levantar quatro paredes de tijolo em um quadrado, você não vai ter um quarto. Vai ter um monte de entulho.” A falha é demonstrada até aproximadamente 6 s, seguida de rebobina.
- Muro: “Se você cortar o barranco do lado da sua casa pra fazer uma vaga pro seu carro, você não vai ter uma garagem...” O carro aparece no local e o solo cede com chuva por volta de 6 s.
- Paraquedas: boneco à porta do avião no início; saída, queda, mochila e números de velocidade/altura aparecem nos primeiros segundos. A palavra “Se” é visível em 0 s. A frase completa exige revisão da voz; não foi inventada a partir dos objetos.

## 1. Estádio de futebol

### Montagem e encenação

As janelas abaixo localizam etapas observadas. Não afirmam que cada peça entra exatamente na primeira borda do intervalo; a conferência fina usa as folhas 6 fps e os quadros completos dos momentos.

| Janela aproximada | Peça/acontecimento visível | Forma de apresentação e função |
| --- | --- | --- |
| 0–7 s | Dois times, bola, campo de terra, buraco, jogador caído | Grupos em primeiro plano, depois plano aberto e falha física. A bola e a queda dão uma ação legível ao problema. |
| 7–12 s | Máquina niveladora e grama | Rolo atravessa o terreno; cobertura verde substitui a terra. Um elemento é introduzido e testado antes do seguinte. |
| 12–22 s | Jogada, temporal, poças, bola na água | Personagens demonstram benefício da grama; iluminação escurece com a chuva e o campo muda de estado. |
| 22–33 s | Corte do solo, pedra, areia, canos perfurados, água | Corte transversal expõe camadas; pequenas esferas e setas azuis mostram a saída da água. Textos visíveis: “PEDRA”, “AREIA”, “CANOS FURADOS”, “SISTEMA DE DRENAGEM”. |
| 33–46 s | Torcedores e arquibancada | O público surge em volta e depois se eleva em degraus. Compara quem não enxerga com quem consegue ver. |
| 46–56 s | Peso da multidão e base de sustentação | Seta vermelha grande e detalhe de pilar no solo transformam carga abstrata em elemento visual. |
| 56–79 s | Sol, pilares, cobertura, cabos | Teto corrige calor; suporte visível incomoda a visão; cobertura suspensa e cabos resolvem o bloqueio. Exemplo de cadeia de problemas, e não lista arbitrária. |
| 79–109 s | Sombra sobre grama, lâmpadas de crescimento, refletores e sombras de jogadores | Alterna vista geral, vista do campo e detalhe. O cenário passa também por noite. Rótulos visíveis incluem “LÂMPADAS DE CRESCIMENTO”, “SEM CANTO ESCURO”, “QUATRO SOMBRAS”. |
| 109–131 s | Multidão, saída, túneis/vomitórios, acessibilidade | O problema muda de estrutura para circulação e uso. Vistas altas tornam a quantidade de público legível; detalhes localizam acessos. |
| 131–140 s | Aspersores, campo completo e pedido de comentário | Retoma humor com personagem molhado, revela o conjunto e encerra sobre o próprio campo. |

### Câmera, enquadramento e texto

Os cortes entre os dois times e o campo aberto estão visualmente confirmados nas folhas iniciais em torno dos quadros 40 (1,333 s) e 79 (2,633 s). A passagem para o corte subterrâneo no quadro 680 (22,667 s) também é uma mudança evidente de vista. A alternância mais útil é **aberto para contexto → detalhe para mecanismo → aberto para comprovar**. A câmera não precisa orbitar em toda fala: a água e as novas peças já movimentam a imagem.

O campo ocupa o centro, enquanto as arquibancadas emolduram suas bordas. O gramado, a camisa amarela e o uniforme roxo separam times e funções com facilidade. A regra dos terços ajuda a deixar céu/contexto acima, mas a ação importante é frequentemente centralizada. O texto de narração fica na região inferior central; termos técnicos recebem rótulos adicionais. Em um celular, três elementos textuais simultâneos podem competir.

**CTA diretamente visível:** “COMENTE ‘GOL’” no final, presente por volta de 137,5–140 s. É curto, tem uma única ação e usa uma palavra ligada ao assunto. O momento exato de entrada pode ser lido nas folhas finais; o áudio do convite ainda deve ser conferido antes de tratá-lo como transcrição.

### Crítica

A força está em mostrar a relação entre infraestrutura e experiência do público. Há continuidade espacial e reuso de ativos. A fragilidade é a densidade: drenagem, cobertura, iluminação, crescimento da grama, evacuação e acessibilidade disputam o mesmo episódio. Para um piloto de um minuto, escolher uma cadeia menor. A multidão repetida sugere escala, mas os clones ficam evidentes; variar três ou quatro poses, silhuetas e tempos de movimento melhora a percepção de qualidade sem precisar modelar dezenas de personagens únicos.

## 2. Casa

| Janela aproximada | Peças/acontecimentos | Apresentação e função |
| --- | --- | --- |
| 0–6 s | Pedreiro, paredes de tijolo, colapso | A câmera abre enquanto paredes crescem em volta do personagem. A conclusão intuitiva é desmentida por entulho. |
| 6–23 s | Rebobina, terra fofa, fundações, apoios e estrutura horizontal | Setas vermelhas explicam peso; corte no solo revela o que as paredes escondiam. Madeira de forma/estrutura e concreto aparecem por camadas. |
| 23–43 s | Umidade, barreira/impermeabilização, caminho da água, mancha na parede | Esferas azuis representam água no solo. Corte e comparação demonstram a peça invisível e seu efeito. |
| 43–60 s | Tijolos, cimento, areia, água e argamassa | Pequeno painel de ingredientes apresenta material antes do resultado. Paredes ganham juntas e continuidade. |
| 60–76 s | Peso do teto, vigas/pilares e amarração | Vermelho marca carga/problema; amarelo destaca a nova estrutura. A câmera mantém o conjunto para que seja possível comparar antes e depois. |
| 76–100 s | Janela, verga e rachadura | Plano de parede e detalhe junto à abertura explicam concentração de carga. Rótulos observados: “30 cm”, “VERGA”, “SEM VERGA”. |
| 100–124 s | Chuva, armação de telhado, telhas, furos/canos/conduítes | O telhado muda o estado de exposição à chuva. Depois o vídeo entra nas instalações e revestimento. |
| 124–145 s | Reboco, piso, ferramenta de compactação e acabamento interno | Mostra tanto superfícies internas quanto externas, mantendo o mesmo personagem. |
| 145–159 s | Caixa d’água, tubulação, fachada pronta, cachorro | A câmera sai da casa e revela instalações superiores. O cachorro funciona como quebra cômica antes da comemoração. |
| 159–168,5 s | Personagem celebrando, casa pronta e CTA | Resultado legível num plano aberto; pedido de comentário em duas categorias. |

**CTA visível:** “SABIA? COMENTE ‘PEDREIRO’ / NÃO SABIA? COMENTE ‘SERVENTE’”, observado aproximadamente de 164 a 168 s. Ele conecta a ação de comentar à autoavaliação do espectador. A formulação pode gerar participação, mas também é uma hierarquia um pouco depreciativa; para nossa marca, uma escolha entre explicações ou próximos temas é mais acolhedora.

A estrutura fica mais legível porque há trechos longos com movimento global baixo: uma janela medida de 84,200–91,367 s dura 7,167 s na análise quadro a quadro. Isso coincide com a explicação de parede/abertura. A imagem não precisa estar congelada: textos e peças mudam no mesmo enquadramento. O reagrupamento em janelas de análise pode apontar intervalos um pouco diferentes; usar `static_intervals` para a medida por quadro e `camera_segments` para visão resumida.

**Crítica visual:** parede vermelha, terreno bege, concreto cinza e personagem amarelo oferecem códigos materiais intuitivos. Tijolos muito pequenos geram textura intensa e moiré em baixa resolução. Para melhorar, renderizar nativamente em 1080×1920, suavizar a repetição da textura e reservar detalhe fino para planos próximos. Amarelo destaca o novo pilar, mas quando capacete, roupa, rótulo e peça são todos amarelos a hierarquia diminui. O personagem precisa continuar sendo escala humana, sem disputar a explicação.

## 3. Muro de arrimo

| Janela aproximada | Peças/acontecimentos | Apresentação e função |
| --- | --- | --- |
| 0–8 s | Barranco, corte no terreno, vaga, carro, chuva e deslizamento | Primeira experiência falha muito cedo. O mesmo carro torna a consequência concreta. |
| 8–23 s | Rebobina e muro simples pressionado pelo solo | Setas vermelhas laterais mostram empuxo. O retorno temporal permite comparar a nova tentativa. |
| 23–39 s | Solo firme, fundação/base e seção do muro | Câmera aproxima da parte enterrada; setas apontam forças e a geometria da base. |
| 39–54 s | Armadura de aço e lados da estrutura | Ferros se apresentam antes do volume de concreto. Destaque amarelo permite vê-los através/antes do fechamento. Rótulos distinguem “LADO QUE VOCÊ VÊ” e “LADO DA TERRA”. |
| 54–74 s | Base no chão, pressão e chuva atrás do muro | Seção mantém a relação espacial; azul começa a representar água e vermelho permanece associado a força. |
| 74–99 s | Furos/saídas, drenagem, camada de brita e cano perfurado | Água azul anima o caminho. Materiais entram sucessivamente, com plano próximo para enxergar o que está oculto. |
| 99–126 s | Conjunto pronto, carros, fissura/junta e dilatação | Volta à rua e explica o desempenho do muro. O entorno muda de problema, mas a mesma estrutura serve de referência. |
| 126–137 s | Canaleta, grade, grama e portão | Acabamentos e circulação fecham a montagem. Textos locais identificam cada peça. |
| 137–142,7 s | Confete, vista pronta, personagem frontal e CTA comercial | O vídeo muda do assunto para a produção de conteúdo; o CTA já é uma ponte para vender/ensinar. |

**CTA diretamente visível:** “COMENTA ‘CRIADOR’” e “se você quer que eu te ensine a criar um vídeo inteiro desses em um dia”, observado nos quadros de aproximadamente 138–142 s. Não é o mesmo objetivo do CTA “GOL”: captura interesse na ferramenta, não apenas na curiosidade. Misturar esses dois objetivos em todos os vídeos mudaria a percepção de um canal de ciência/curiosidade.

O detector assinalou oito cortes candidatos. Isso não significa só oito mudanças narrativas: muitas peças, rotações e aberturas são construídas dentro do mesmo plano. O episódio depende mais da transformação do cenário do que de cortar constantemente. Um intervalo de movimento global baixo medido em 58,800–61,367 s dura 2,567 s; há um de 3,067 s no fechamento. Tratar as setas/água animadas como movimento de câmera seria um erro.

**Crítica:** este é o exemplo mais útil para a nossa máquina. Preserva um palco, introduz uma causa, torna o invisível visível e só depois coloca o acabamento. O principal risco é explicar forças com setas ambíguas: cada direção precisa ter legenda e convenção estável. O aspecto cartoon não dispensa consistência causal. A peça técnica não deve mudar de proporção ou posição quando a câmera gira. A animação é um modelo didático, não um projeto executivo de engenharia.

## 4. Paraquedas

| Janela aproximada | Peças/acontecimentos | Apresentação e função |
| --- | --- | --- |
| 0–6 s | Avião, personagem, mochila e queda livre | Ação imediata, com altitude e velocidade em dois painéis superiores. Números dão uma escala de risco que os outros vídeos não usam. |
| 6–26 s | Lençol improvisado, ar e fracasso | Corpo, tecido e setas azuis tornam o arrasto legível. A tentativa é insuficiente e existe retorno temporal. |
| 26–48 s | Velame arredondado, náilon, cordas e problemas de descida | Materiais e formato mudam. Vistas distantes mostram trajetória; vistas próximas mostram o personagem. |
| 48–64 s | Saída central/chaminé e vento | Vista por cima torna o detalhe da abertura compreensível. A inclinação e a aproximação das árvores representam perda de controle. |
| 64–101 s | Duas camadas, células, cordas e controle | O velame ganha forma retangular/asa. Setas apresentam avanço e comandos; a câmera alterna vista geral e detalhe das linhas. |
| 101–132 s | Nova queda, pilotinho, abertura e defeito | Rebobina e aceleração reiniciam o experimento. Um objeto pequeno inicia a abertura do conjunto maior. |
| 132–158 s | Emaranhamento, incapacitação, mochila/reserva e acionamento automático | Close da mochila e transparência/corte revelam mecanismo oculto. Estrelas junto à cabeça acrescentam linguagem cômica à emergência. |
| 158–171 s | Aproximação, pouso, confete e assinatura de marca | Volta ao plano largo do campo e termina perto do personagem. Nas legendas finais aparecem “Se”, “Você”, “Gostou”, depois o nome da marca. |

O HUD é persistente e transforma a narrativa em uma espécie de simulação/jogo. Há três faixas de informação: números acima, mecanismo no centro e palavra da narração abaixo. O personagem costuma ficar centralizado para que a câmera e a paisagem ofereçam continuidade. Nuvens, solo e cordas criam referências de movimento; por isso um enquadramento que acompanha o boneco pode ter personagem quase parado e fundo em deslocamento.

Apenas 19,933 s foram classificados como movimento global baixo pelos limiares quadro a quadro, cerca de 11,7% da linha de vídeo. Não interpretar isso como câmera em movimento em todos os outros 88,3%: tecido, personagem e partículas também se movem. A amostra é mais dinâmica que a casa, mas o número exato de movimentos físicos de câmera não é recuperável do MP4.

**Final visível:** em 168,667 s aparece “Se”; 168,833 “Você”; 169,000 “Gostou”; em 170 s o nome “Desmontando”. Não há convite grande de comentário como no estádio. O verbo do pedido final de voz não foi certificado pela leitura dessas imagens. Não completar a fala por suposição.

**Crítica:** HUD ajuda a entender causa e efeito, mas os números precisam obedecer às mudanças de tempo; a rebobina deve ser inequívoca para evitar que uma altitude que aumenta pareça erro. O arquivo tem só 202×360 pixels, reduzindo muito a leitura das cordas e painéis. Simples upscale para 1080×1920 deixaria o arquivo maior, sem recuperar essas informações. Para nossa versão, renderizar os elementos e a tipografia na resolução final. Evitar que as cordas escondam o rosto ou que o personagem perca contraste sobre terreno verde.

## Paleta, branding e composição: diagnóstico transversal

### Personagem

Há uma linguagem coerente de boneco: cabeça arredondada/facetada, olhos pretos simples, boca pequena, torso volumoso, membros cilíndricos, mãos simplificadas e poucos materiais. Casa e muro usam trabalhador com capacete e roupa amarela/azul. O estádio varia cabelos e tons de pele e distingue equipes por amarelo/preto e roxo/branco. O paraquedista mantém silhueta semelhante e troca acessórios conforme a situação. Isso cria continuidade; não demonstra que os quatro foram produzidos com uma ferramenta ou projeto idêntico.

Para nossa marca, reter a simplicidade e a clareza, mas criar rosto, proporções, roupa e assinatura próprios. O mascote institucional não precisa entrar em todo experimento. Um personagem genérico consistente, com cinco poses úteis, é melhor que um herói complexo gerado de novo em cada imagem.

### Regra dos terços e ambientação

O estilo usa centralização funcional com frequência. O objeto precisa ser compreendido primeiro; não vale deslocá-lo só para obedecer a uma regra. Terços servem para distribuir céu, horizonte, palco e espaços de texto. O ambiente tem casas coloridas, árvores facetadas, morros suaves, céu limpo, luz diurna e sombras marcadas; chuva/noite são mudanças narrativas, não decorativas. A densidade do fundo é baixa o bastante para a nova peça se destacar, exceto nas arquibancadas.

### Cor e regra 60/30/10

Não há evidência de uma aplicação literal e fixa de 60/30/10 nos quatro vídeos. Cor é principalmente material e função: solo castanho, concreto cinza, vegetação verde, céu azul, água azul, ameaça/força vermelha, destaque técnico amarelo e contorno de texto preto.

Uma quantização exploratória de todas as amostras esparsas a cada cinco segundos, reduzidas para 64×114 e agrupadas em oito cores, deu estes centros dominantes. São agrupamentos de pixels do quadro inteiro, incluindo texto e áreas escuras; não são tintas exatas de material nem medição de áreas semânticas:

| Vídeo | Três centros de cor mais frequentes | Participações aproximadas |
| --- | --- | --- |
| Estádio | #886F4E, #4CAF4E, #A4BAA3 | 16,0%; 15,9%; 14,1% |
| Casa | #B49D80, #7D8888, #863722 | 19,2%; 14,0%; 13,1% |
| Muro | #6E5746, #95998F, #A6B7A9 | 16,0%; 15,3%; 11,8% |
| Paraquedas | #869F60, #B2CFDE, #5C97A8 | 32,7%; 22,3%; 14,6% |

Resultados locais: `outputs/visual-review/palettes.json`. Cores de acento pequenas podem ser mescladas pelo agrupamento; a ausência de um amarelo no topo não significa que não exista amarelo no vídeo.

**Aplicação recomendada para o CurioLab:** 60% de fundo calmo, 30% de objeto/contexto e 10% de destaque ativo. Isso é uma regra de hierarquia sugerida, não um resultado medido nos exemplos. Azul para fluxo de água/ar, vermelho para problema e amarelo ou lima para a peça nova precisam ter funções definidas. Cor sozinha não basta: setas, rótulos e formas também comunicam o significado.

### Tipografia

Palavras da narração aparecem uma a uma, geralmente em branco com contorno preto. O termo-chave pode virar amarelo; etiquetas secundárias surgem perto da peça. O CTA usa texto maior no topo. Essa hierarquia é funcional, mas às vezes a mesma palavra aparece na legenda e no rótulo simultaneamente. Na nossa versão, manter uma legenda curta e reservar rótulos para o nome técnico ou a unidade. Preparar textos para leitura em tela pequena desde o início.

## Som: o que foi efetivamente medido

Há áudio nos quatro arquivos. Extração WAV e análise de sinal foram executadas. `volumedetect` indicou média de −16,8 dBFS no estádio e no muro e −17,0 dBFS na casa e no paraquedas; pico de −1,5 dBFS nos quatro. Esses valores **não são LUFS** e não identificam instrumento, voz, música ou efeito.

No limiar de −35 dB e duração mínima de 0,2 s, não foram encontradas pausas no estádio e no paraquedas. Casa e muro têm apenas uma pausa curta no final dos arquivos. Isso sugere sinal quase contínuo; não prova fala sem pausas, pois música/ruído pode preencher o fundo. A identificação do que se ouve, transcrição e alinhamento de voz por palavra permanecem separados da leitura visual/OCR até haver ASR ou escuta validada. Não foram inventados sons de impacto, transição, chuva ou uma marca de sintetizador.

## O que deve entrar na máquina

A máquina precisa representar estados e causas, não apenas armazenar um prompt por cena. Cada etapa exige: peça que entra; problema que a motiva; ação visual; posição e escala; câmera; hold de leitura; texto; áudio; critério de revisão. A mesma base de cenário deve ser reaproveitada. O motor de montagem de imagens com zoom/pan é útil como formato 2,5D e prototipação; ele não substitui automaticamente os cortes estruturais, a geometria acumulativa e as simulações que estas referências mostram.
