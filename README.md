# CurioLab 3D — máquina local de vídeos

Ferramenta em português para criar projetos verticais, preparar roteiros e exportar MP4. Interface original com mascote, landing page de pré-lançamento e skill instalável para Codex. Esta versão tem ferramentas reais de edição e renderização; não possui um modelo que converta qualquer roteiro em animação 3D automaticamente.

## Comece pelo painel

**Instalação completa da skill:** extraia o pacote, abra a pasta no assistente e execute `python INSTALAR-SKILL.py`. O padrão instala para Codex e Claude Code apenas neste projeto, sem modificar credenciais ou perfis globais. Depois inicie uma nova sessão e use `$curiolab-3d` (Codex) ou `/curiolab-3d` (Claude Code). Execute `python tools/smoke_skill.py` para validar o fluxo com um MP4 Full HD novo, sem APIs pagas; detalhes em `docs/INSTALACAO.md`.

1. Leia `docs/INSTALACAO.md` e execute `python tools/doctor.py`.
2. No terminal da pasta extraída, abra o painel com `python tools/launch_panel.py` (Windows: `py -3 tools/launch_panel.py`; macOS/Linux: `python3 tools/launch_panel.py`). Os pacotes atuais não distribuem atalhos `.bat`/shell nem executáveis nativos.
3. Instale a skill no assistente escolhido: `python tools/doctor.py --install-skill --agent claude` ou `--agent codex`. Autentique sua conta no aplicativo do assistente; a skill não concede uma assinatura.
4. Em **Meu canal**, salve identidade, receita, personagem, cores RGB e voz. Há uma prévia3D real do perfil salvo. A roupa padrão é amarelo quente #E8BE45; os templates recebem o snapshot de branding.
5. Em **Comece aqui**, prepare o pedido. Leve a instrução ao Claude Code/Codex para pesquisar, escrever e produzir. O painel acompanha os arquivos e mostra os resultados em **Vídeos**.

O catálogo atual tem seis itens reais: três personagens paramétricos e três cenários3D (Casa, Terra e Sala). Não contém68modelos nem gera qualquer animação automaticamente. **Receita de criação** permite editar o método para pedidos futuros; os snapshots preservam os pedidos em andamento.

A conexão de voz ElevenLabs/OpenAI é implementada com consulta de vozes e geração separada. Chave fora do perfil, geração apenas por ação explícita, recebimento de áudio validado com ffprobe. Os testes usam respostas controladas e áudio real de teste; nenhuma conta do usuário foi autenticada nesta sessão. Falta validar a primeira geração com sua própria conta e acesso de rede. Não é uma alegação de API ilimitada ou incluída no ChatGPT Pro.

A interface principal é o painel; `/studio.html` mantém o editor avançado. Os lançadores e a instalação de skill em destino temporário foram testados no Linux desta máquina. As instalações nativas em Windows/macOS e a carga em contas reais de Claude Code/Codex ainda exigem validação no equipamento escolhido.

## Ver e executar

`outputs/curiolab-visual.html` é a prévia visual autocontida: abre sem instalar nada, permite explorar a interface e editar nesta aba. Não renderiza nem substitui o servidor. A aplicação executável requer Python3.12+, Blender4.3+, FFmpeg com libx264/libass. Não exige npm ou dependências Python para o estúdio.

```sh
cd /workspace/maquina
python app.py
```

O app escuta apenas na interface local, porta8000. O painel é a página inicial e `landing.html` é a apresentação. Não exponha este servidor diretamente à internet: não tem autenticação multiusuário.

## Produção

- **Imagens + movimentos:** qualquer pauta com imagens próprias. Envie PNG/JPG/WebP, edite legenda, tempo de entrada/saída e movimento por cena. A timeline deve começar em0, ser contínua e acabar na duração total (até180s). Composição2D com pan/zoom, não reconstrução3D. Prompts por cena podem ser copiados para gerar imagens manualmente no ChatGPT Pro; a assinatura não inclui API. O upload usa até30MB por arquivo.
- **Casa em montagem e Sala com circulação de ar:** geometria3D real, personagem original e peças que entram em sequência. Câmera e montagem são definidas em `engine/scene_house.py`; os controles de pan/zoom das imagens não alteram esse template. Até30s.
- **Terra:** geometria3D procedural, rotação ilustrativa. Até30s.
- **Saída:** FullHD1080×1920 a30fps ou prévia360×640. A fonte de imagens deve ter qualidade suficiente; aumentar resolução de referências pequenas não recupera detalhe.
- **Voz:** envie MP3/WAV/M4A autorizado, inclusive exportado do ElevenLabs. Não há voz automática sem arquivo. A narração não pode ser maior que o vídeo. O compositor normaliza a faixa e codifica AAC; sempre reveja a sincronização. Música/efeitos adicionais e legendas palavra por palavra sincronizadas com voz não são gerados automaticamente.

Projetos ficam em `.local/projects`, arquivos enviados em `.local/assets`, vídeos em `outputs`. Atualizar um projeto preserva seu identificador. Projetos legados continuam presentes. A publicação em YouTube/Reels é manual.

```sh
python engine/render.py --project engine/house_demo.json --output outputs/casa-fullhd.mp4 --full-hd
python engine/render.py --project engine/demo.json --output outputs/demo.mp4 --preview
python engine/slideshow.py --project caminho/projeto-resolvido.json --output outputs/video.mp4
```

O estúdio resolve os IDs de assets para caminhos de imagem no projeto do compositor. Pelo CLI, as cenas usam `image_path`, `caption`, `start`, `end` e `motion`; áudio opcional em `narration_path`. Veja `engine/slideshow.py` para validação.

## Análise dos quatro vídeos fornecidos

O painel “Referências” abre as folhas de quadros e dados já produzidos. Galeria offline em `outputs/analysis/index.html`; pacote em `outputs/analysis/folhas-e-medidas.zip`.

- Folhas a6fps para leitura da história e todos os frames em janelas dos momentos selecionados.
- CSV por frame com fluxo óptico/escala/rotação, cortes candidatos, intervalos de baixo movimento e confiança. Isso não reconstrói com exatidão a câmera física; objetos animados, pouca textura e personagens repetidos podem invalidar estimativas.
- OCR da tela e das legendas em `outputs/ocr`, com confiança e incerteza temporal de aproximadamente0,167s. OCR não é transcrição de voz.
- Áudio extraído, volume e silêncio em `outputs/transcripts`. **A transcrição por palavra está bloqueada:** o download oficial do modelo de fala foi negado pelo proxy. Não foram inventadas falas nem sons.

Para reproduzir a análise, use as dependências locais específicas:

```sh
.local/analysis/bin/python tools/video_forensics.py
OMP_THREAD_LIMIT=1 .local/asr/bin/python tools/transcribe_videos.py --caption-only --workers 4
```

Só depois da liberação efetiva de rede e da disponibilidade do modelo:

```sh
.local/asr/bin/python tools/transcribe_videos.py --asr-only --allow-model-download
```

A coleta pública do YouTube também permanece bloqueada; `python tools/analyze_channel.py --download` fica preparado para quando o acesso for aplicado. Arquivos enviados pelo usuário já podem ser analisados sem depender do YouTube. Não confundir os canais DesconstruindoUniverso e DesmontandoOMundo.

## Skill e próximos passos comerciais

O botão “Baixar skill” monta o pacote com o estúdio, motor, skill e documentação. Não inclui credenciais, projetos privados, binários de terceiros ou créditos de API. Instalação em `skills/curiolab-3d/references/production.md`.

Há duas entregas: a skill textual (`curiolab-3d-skill-*.zip`) contém apenas Markdown/JSON/YAML; o motor (`curiolab-3d-runtime-*.zip`) contém Python, interface e ativos. A skill textual precisa de um motor instalado para gerar MP4. A versão 0.4.0-preview.1 foi retirada dos downloads atuais após relato de alerta do Windows; o nome da detecção ainda não foi fornecido. Integridade SHA-256 e testes funcionais não equivalem a liberação por antivírus. Leia `SECURITY.md`; não execute arquivos bloqueados nem desative proteções para instalar.

ElevenLabs via API é opcional em `integrations/elevenlabs.py`. Ainda não foi testado com conta real. Configure credenciais apenas em ajustes seguros, nunca no repositório; a chamada pode consumir créditos.

A landing não processa pagamentos nem coleta email. R$37,90 é hipótese de preço, sem checkout ativo. Domínio, email profissional, checkout, suporte e condições comerciais ainda precisam ser definidos antes de vender. O produto ainda não passou por validação com compradores.

Documentação: `docs/RECEITA-DE-PRODUCAO.md`, `docs/ANALISE-CRITICA-VIDEOS.md`, `docs/EXPERIMENTO-7-DIAS.md`, `docs/PRODUTO.md`.

A referência técnica de cor e contraste está em `docs/PALETA-E-AMBIENTACAO.md`; os valores medidos vêm de sRGB/WCAG. Associações psicológicas são hipóteses de design e não promessa de emoção ou viralização.

## NICO versionado (novo)

Módulo aditivo React19/Three.js/ReactThreeFiber/TypeScript em `mascot-studio`, compilado para `web/mascot-viewer`. O servidor Python e os projetos JSON existentes foram preservados. Configuração central, manifest e bloqueio de fontes em `shared/mascots/nico/1.0.0-candidate.1`. Modelos e prévias reais em `assets/mascots/nico/1.0.0-candidate.1`.

O personagem tem7animações,5.756triângulos e8materiais. Geometria, animação e componente são módulos separados. Produção exige versão aprovada e pin explícito; o candidato atual só é visualizado. Os originais PNG/JPG das referências ainda não chegaram como arquivos e estão registrados como pendentes, sem ativos fabricados.

O bancoSQL não existia na arquitetura inspecionada. `migrations/001_mascot_registry.sql` e o adaptador opcional estão preparados e testados em bancos temporários, sem aplicação na instância. Leia `docs/MASCOT-DATABASE-PROPOSAL.md` antes de aprovar qualquer migração.

Para editar o personagem: `cd mascot-studio && npm ci && npm test && npm run build`. Não altere fontes bloqueadas para redesenhar a mesma versão. Para avaliar o modelo sem instalar o projeto, use `outputs/nico-visual.html`, que incorpora o visualizador compilado. O canal escolhido pelo usuário se chama Nicolume; não confundir NICO (personagem) com CurioLab3D (produto).
