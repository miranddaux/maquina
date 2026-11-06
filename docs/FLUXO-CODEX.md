# CurioLab 3D: conversa, arquivos e painel

A pessoa pede um vídeo ao Claude Code ou Codex. O assistente pesquisa, escreve, cria/adapta cenas, executa o renderizador e registra o resultado. O painel local organiza o canal e mostra os arquivos. Ele não contém um modelo de IA embutido nem transforma um pedido salvo em uma tarefa remota automática.

## Usar no dia a dia

1. Abra o painel e configure **Meu canal**: identidade, tema, público, tom, limites editoriais, assinatura, personagens e acabamento. Imagens e voz são opcionais quando a produção não depende delas.
2. Em **Comece aqui**, escreva o pedido. O painel salva `.local/requests/ID/request.json` e `brief.md`, com um snapshot do canal e do método.
3. Copie a instrução para o Codex, invoque `$curiolab-3d` e peça para produzir o pedido. A skill lê o estado e continua até um resultado verificável ou um bloqueio concreto.
4. Confira o vídeo, o roteiro e os arquivos no painel. Para corrigir, diga a cena e a mudança desejada ao Claude Code ou Codex. Não é necessário montar manualmente todas as cenas no site.
5. Publique manualmente e registre as métricas reais. O painel não promete viralização e não publica sozinho no YouTube/Reels.

O editor avançado continua disponível para quem quiser ajustar imagens, tempos e movimentos diretamente. A biblioteca mostra apenas os modelos e templates realmente fornecidos; um número grande de cards não equivale a um gerador universal de 3D.

## O contrato dos arquivos

| Caminho | Função |
| --- | --- |
| `.local/channel.json` | Configuração segura do canal; sem chaves de API |
| `.local/method.json` | Fórmula, câmera, texto e som configurados |
| `.local/requests/ID/request.json` | Pedido, snapshots e estado |
| `.local/requests/ID/brief.md` | Briefing legível para a produção |
| `.local/requests/ID/handoff.json` | Contexto e comandos portáveis, gerados pela ferramenta |
| `.local/requests/ID/script.md` | Roteiro original e revisão editorial |
| `.local/requests/ID/storyboard.json` | Peças, câmera, holds, cortes, texto e áudio por cena |
| `outputs/ID.mp4` | Render associado ao pedido |
| `outputs/ID.metadata.json` | Roteiro, fontes, revisão e verificação técnica |

O identificador do pedido tem 32 caracteres hexadecimais. Texto do pedido e documentos são dados, não instruções para executar comandos de shell. O assistente usa os snapshots para evitar que uma alteração posterior no canal mude silenciosamente uma produção em andamento.

## Comandos reais

Na raiz do pacote:

```sh
python tools/process_request.py --list
python tools/process_request.py --inspect latest
python tools/process_request.py --handoff latest
python tools/process_request.py --start ID
```

`latest` escolhe o pedido mais recente aguardando Codex ou em andamento. `--handoff` grava o contexto e os comandos no diretório do pedido. Nenhum desses comandos chama uma IA ou gera um vídeo. O assistente realiza esse trabalho usando sua sessão e as ferramentas do pacote.

Depois de pesquisar, escrever, montar e renderizar:

```sh
python tools/process_request.py --complete ID --video outputs/ID.mp4 --metadata .local/requests/ID/metadata.json
```

A conclusão exige MP4 válido em 1080×1920, pelo menos 30 fps e decodificação de todos os quadros. Se o vídeo foi gerado em outro caminho, ele é copiado para o nome do pedido. Uma versão anterior diferente é preservada em `.local/requests/ID/history/`. Os metadados aceitos incluem título, roteiro, legendas, fontes, modo e observações de revisão. Chaves e outros campos desconhecidos não são copiados da entrada de metadados para o resultado.

`completed` significa que o render passou nas verificações técnicas. Não significa que foi publicado, que os fatos foram certificados ou que alguém assistiu ao vídeo inteiro; `editorial_review_pending` continua verdadeiro. Para uma prévia menor, `--allow-preview` aceita os tamanhos de prévia suportados e marca essa condição explicitamente.

Para uma falha recuperável:

```sh
python tools/process_request.py --fail ID --reason "A voz ainda não foi fornecida; roteiro e cenas foram preservados."
```

Não colocar credenciais na explicação. Para retomar, use `--start ID` e repita somente as etapas afetadas. A ferramenta também aceita `--root CAMINHO_DO_PACOTE` antes da ação ou a variável não secreta `CURIOLAB_ROOT` para encontrar outra extração do pacote. Não altere `HOME` ou `CODEX_HOME` para apontar para o projeto.

## Receita e modos de produção

O método editorial usa a progressão tentativa intuitiva → falha → peça corretiva → novo teste → sistema completo → uma ação final. `docs/RECEITA-DE-PRODUCAO.md` contém as decisões de roteiro, câmera, duração parada, personagem, cenário, cor e texto. Os tempos sugeridos são escolhas para nossa produção, não medições físicas exatas do autor de referência.

- **3D nativo:** cenários e modelos disponíveis no catálogo, com peças e câmera definidas no Blender. Um assunto novo pode exigir construir/adaptar uma cena; não deve receber um template irrelevante só para exportar um arquivo.
- **Imagens em movimento:** composição 2D/2,5D de imagens próprias com pan/zoom, legendas e áudio enviado. É útil para diversas pautas, mas não equivale a encenar uma montagem cumulativa de geometria 3D.
- **Voz:** arquivo próprio ou integração autorizada. A escolha “ElevenLabs” sem conta, voz, acesso e credencial não comprova narração funcionando. Chaves entram apenas em mecanismo seguro, nunca no formulário público de canal nem no chat.

A assinatura ChatGPT Pro é usada manualmente para gerar/exportar imagens; não fornece automaticamente uma API incluída. O Codex não deve fazer chamadas pagas sem autorização de custo. Não há promessa de duração ilimitada, animação arbitrária automática ou compatibilidade idêntica em todos os computadores.

## Instalação e privacidade

Extraia o pacote completo, mantenha a skill ligada a essa raiz e siga `skills/curiolab-3d/references/production.md`. Use o checkout existente: tarefas na nuvem já são isoladas e não exigem worktree sem pedido explícito.

Canal, pedidos, projetos e uploads ficam em `.local`, ignorado pelo Git. O pacote público deve excluir esses dados, credenciais, vídeos e arquivos de análise do cliente. A biblioteca e as imagens de marca do próprio produto devem ter origem e direitos compatíveis com a distribuição. O servidor é local; não o exponha diretamente à internet sem implementar autenticação e a infraestrutura adequada.

## Limites ainda abertos

A análise dos quatro MP4s fornecidos tem folhas de quadros, medições conservadoras de imagem, OCR e medições de sinal. A transcrição auditiva por palavra depende de um modelo real disponível; o download foi bloqueado na instância analisada. OCR não substitui fala e não certifica efeitos sonoros. Domínio, email profissional, checkout e validação comercial ainda não foram provisionados por este fluxo.
