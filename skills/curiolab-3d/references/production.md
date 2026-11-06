# Produção local e instalação

## Instalação da skill

Extraia o pacote completo CurioLab 3D para um diretório permanente. Execute `python INSTALAR-SKILL.py --agent both --scope project`. O instalador confere a integridade do ZIP extraído e registra a skill em `.agents/skills/curiolab-3d` (Codex) e `.claude/skills/curiolab-3d` (Claude Code). O motor em `engine/` e o painel devem permanecer nesta pasta. Reabra a sessão para carregar a skill; use `$curiolab-3d` ou `/curiolab-3d` conforme o assistente. `--scope user` instala deliberadamente para toda a conta; não substitua uma instalação diferente sem backup.

Ao instalar a skill fora do projeto, informe ao Codex a raiz do pacote ou configure `CURIOLAB_ROOT` com esse caminho em sua sessão. Não altere `HOME` nem `CODEX_HOME` para apontar para o projeto. O pacote deve permanecer acessível e suas dependências devem estar instaladas.

## Requisitos

Python 3, Blender e FFmpeg/ffprobe disponíveis no PATH, espaço para frames intermediários e MP4 e recursos de CPU. Consulte o README do pacote para as versões efetivamente testadas. O render pode consumir tempo mesmo sem API paga. Não distribuir os executáveis de terceiros no ZIP automaticamente.

## Fluxo executável inicial

Na raiz do pacote, o comando abaixo usa o template de rotação da Terra:

```sh
python3 engine/render.py --project engine/demo.json --output outputs/demo.mp4 --preview
ffprobe -v error -show_entries stream=codec_name,width,height -show_entries format=duration -of json outputs/demo.mp4
```

Use um nome de saída novo para preservar trabalho anterior. Leia `python3 engine/render.py --help` para limites atuais. A prévia é curta e não comprova que um episódio narrado de 30 segundos já esteja pronto. A locução opcional é um arquivo local passado por `--narration`; confira os tempos e o som no MP4 resultante.

## ChatGPT Pro para imagens

A assinatura existente pode ser usada pelo usuário para criar imagens na interface do ChatGPT, respeitando os limites do produto. Ela não fornece automaticamente acesso, créditos ou automação pela API. Preparar prompts e importar arquivos exportados manualmente evita depender de uma API de imagens paga. O renderizador inicial usa geometria procedural; não há promessa de importação automática de imagens para animação.

O mascote dos vídeos é o NICO versionado: moletom amarelo, mochila/calça azul-marinho, cabelo geométrico e tênis branco com sola laranja. Carregue o modelo canônico conforme o pin aprovado. Não gere outro mascote por prompt a cada episódio. A versão candidata pode ser avaliada em prévia explícita; não a declare aprovada automaticamente. O planeta da interface é um elemento gráfico do painel, não o personagem dos episódios.

## ElevenLabs

A conta e a voz ainda precisam ser escolhidas pelo usuário. Verifique os termos e preços atuais do plano antes de usar comercialmente. Pela interface: criar locução em português com roteiro revisado, ouvir, corrigir pronúncias e baixar MP3/WAV. Só usar `ELEVENLABS_API_KEY` e `ELEVENLABS_VOICE_ID` quando existir integração funcional documentada no pacote; guardar a chave em mecanismo seguro e conferir a presença sem revelar valores. Custos e tentativas pagas exigem orçamento; ausência de configuração não bloqueia a demonstração silenciosa.

## Recuperar falhas

- Blender ou FFmpeg ausente: instalar a dependência por origem confiável, mantendo verificação de TLS/assinaturas.
- Erro de projeto: conferir JSON e parâmetros suportados; não alterar fatos ou roteiro só para passar a validação.
- Render lento: usar `--preview` e a duração do exemplo; não iniciar vários renders concorrentes sem recursos.
- Sem áudio: confirmar que um arquivo de voz foi fornecido, que existe e que o MP4 contém stream de áudio.
- Saída incompleta: preservar logs e arquivos úteis, corrigir a causa e repetir somente a etapa afetada.

## Fluxo por conversa e pedidos persistidos

O painel é a vitrine e o organizador dos arquivos. O Codex é quem realiza a pesquisa, o roteiro, as cenas e a execução. Leia `docs/FLUXO-CODEX.md` na raiz do pacote e consulte pedidos reais com:

```sh
python tools/process_request.py --list
python tools/process_request.py --handoff latest
```

Um pedido salvo está aguardando Codex, não uma chamada automática de IA. Depois de assumir o pedido, registrar andamento, produzir e revisar o episódio, use `--complete ID --video outputs/ID.mp4 --metadata .local/requests/ID/metadata.json`. A ferramenta valida MP4, resolução/taxa de quadros e decodificação antes de mudar o estado. O render verificado ainda exige revisão editorial e publicação separadas.

A configuração de personagem e canal deve chegar ao projeto de render e ser inspecionada no resultado. Consulte a implementação atual dos templates para campos aceitos. A lista de `engine/catalog.json` descreve o conteúdo realmente fornecido; não pressupor o mesmo inventário de outro produto. Não distribuir a pasta `.local`, vídeos e referências particulares no pacote de venda.
