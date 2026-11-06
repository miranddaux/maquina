# Aquisição e análise das referências

## Alvos distintos

- Short solicitado: `https://www.youtube.com/shorts/P337IKPsixQ`.
- Canal solicitado na etapa atual: `https://www.youtube.com/@DesmontandoOMundo/shorts`.
- As capturas enviadas anteriormente mostram **Desconstruindo Universo**, identificador `@DesconstruindoUniverso`. Não presumir que seja o mesmo canal. Não misturar métricas das capturas com as do canal atual.

O canal que publicou o Short específico ainda precisa ser identificado nos metadados reais. Um link ou uma captura não comprova as ferramentas usadas na produção.

## Situação observada nesta sessão

O operador principal instalou yt-dlp **2026.10.26** e tentou acessar o Short. A tentativa falhou com erro do túnel do proxy HTTP 403. As adições de destinos de rede foram salvas no rascunho, mas o operador confirmou que a política da instância ainda não refletia essas alterações naquele momento. Uma configuração salva não prova acesso aplicado.

**Nenhum download do vídeo, contador de visualizações, likes, duração, inspeção do conteúdo ou transcrição foi confirmado nesta etapa.** Não há análise visual concluída. A ferramenta abaixo prepara a coleta para repetir depois da aplicação de uma mudança relevante na rede; não contorna o proxy ou a política.

## Ferramenta implementada

`tools/analyze_channel.py` usa subprocessos sem shell e yt-dlp, com verificação TLS preservada. O padrão coleta apenas metadados do Short alvo e até oito Shorts da listagem do canal, deduplicando IDs. O alvo pode ser um nono vídeo se estiver fora desses oito. Não representa análise de todo o canal nem seleção garantida de vídeos mais populares. A ordem é a devolvida pela listagem do YouTube; conferir os IDs retornados.

Na raiz do projeto:

```sh
python3 tools/analyze_channel.py --metadata-only
```

Para baixar os vídeos autorizados para análise local, limitados a 720p:

```sh
python3 tools/analyze_channel.py --download
```

Opções úteis: `--limit 3`, `--target URL`, `--channel URL`, `--yt-dlp CAMINHO`, `--output DIRETORIO` e `--timeout 60`. `--limit` aceita de um a oito. O executável padrão é `.local/tools/bin/yt-dlp`; a instalação depende do ambiente. O download exige FFmpeg quando houver combinação de streams. Erros de autenticação ou rede devem ser diagnosticados antes de repetir; não pedir cookies pessoais automaticamente nem desativar TLS.

Cada execução cria um subdiretório novo em `outputs/references/`, com horário UTC no nome:

- `metadata.json`: metadados normalizados, título, canal retornado, duração, views, likes, data de upload quando disponível e instante UTC da consulta por vídeo; inclui tentativas e categorias de falha.
- `metrics.csv`: campos adequados à comparação, com proteção contra fórmulas em títulos vindos de terceiros.
- `report.md`: o que foi obtido e o que ainda não foi inspecionado; inclui uma tabela de timeline para preenchimento após assistir.
- Arquivos de vídeo: apenas com `--download`; o status só vira `downloaded` se o processo concluir e existir arquivo não vazio no diretório esperado.

Likes ou views ausentes ficam `null` no JSON e em branco no CSV; não são zero. Contadores são uma fotografia pública no instante da coleta, não métricas privadas do YouTube Studio. O download não implica que alguém já tenha assistido ao arquivo. Os relatórios não guardam URLs assinadas de streams, conteúdo de legendas ou transcrições integrais. Os nomes dos idiomas de legendas eventualmente oferecidos são preservados como metadados; isso não significa que foram baixadas.

Falhas retornam código diferente de zero, inclusive quando parte da coleta funcionou. Os resultados parciais são preservados. Os erros armazenados usam categorias como `access_denied`, `network_failure` e `timeout`, sem despejar saídas potencialmente sensíveis do extrator.

## Inspeção após download

1. Confirmar o uploader do Short e a identidade do canal listado.
2. Conferir metadados de arquivo, dimensões, áudio e duração pelo ffprobe.
3. Assistir ao arquivo inteiro e registrar abertura, ritmo de cortes, enquadramento, relações entre voz e imagem, estilo das legendas e encerramento.
4. Criar uma timeline resumida de observações com intervalos reais. Não adivinhar falas nem distribuir palavras uniformemente pela duração.
5. Separar observações (“a câmera aproxima do objeto”) de hipóteses (“pode ter sido feito em Blender”). Software, modelo de IA e prompts só podem ser identificados com evidência explícita.
6. Traduzir o padrão editorial em um roteiro e storyboard originais para o CurioLab; não reproduzir o vídeo ou sua identidade.

## Tempos por palavra e direitos

O analisador de aquisição não implementa reconhecimento de fala ou alinhamento de palavras. Timestamps reais exigem áudio acessível e transcritor/alinhador apropriado; devem ser revisados quanto a confiança, pronúncias e sincronização. Não apresentar uma tabela de palavras com tempos inventados.

Para vídeos de terceiros acessados por link, entregar análise resumida da estrutura e do estilo; não reproduzir a transcrição integral. Se o usuário enviar um arquivo de áudio/vídeo para transformação, a etapa de transcrição pode ser implementada sobre esse arquivo enviado. Download para análise local não fornece autorização de republicação de imagens, áudio, roteiros ou legendas.

## Verificação local realizada

Três testes automatizados passaram sem rede: preservação de métricas ausentes versus zero, proteção do CSV contra fórmula de título e persistência apenas dos campos permitidos sem URLs assinadas ou texto de transcrição. O modo `--fixture ARQUIVO.json` permite testar o fluxo de relatórios sem rede e marca os resultados como **fixture local**, nunca como observação do YouTube. Não combina com `--download`.

```sh
python3 -m unittest discover -s tools -p 'test_*.py' -v
```

Esses testes validam a preparação dos dados, não a extração real do YouTube. A coleta e a análise do conteúdo continuam pendentes até haver acesso funcional.
