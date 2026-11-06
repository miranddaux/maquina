# Instalar e usar o CurioLab 3D

O pacote contém um painel local, modelos procedurais, renderizadores e uma skill para Claude Code ou Codex. A conversa acontece no assistente escolhido; o painel acompanha os arquivos. Ele não contém uma assinatura desses assistentes nem créditos de voz.

## 1. Extraia o pacote completo

Descompacte o ZIP em uma pasta permanente de sua conta. Não mova apenas o arquivo SKILL.md: o motor e o painel precisam continuar juntos. Faça backup de uma versão anterior antes de trocar. Seus projetos e credenciais ficam em `.local`; não publique essa pasta.

## 2. Prepare as ferramentas

- Python 3.12 ou superior: https://www.python.org/downloads/ . No Windows, marque a opção de adicionar Python ao PATH ou use o lançador `py`.
- Blender: https://www.blender.org/download/ . O render foi validado nesta máquina com Blender4.3.2. O diagnóstico aceita4.3+, mas outras versões precisam de um teste de render.
- FFmpeg e ffprobe: https://ffmpeg.org/download.html . Escolha uma distribuição indicada pelo projeto, com libx264 e libass; mantenha assinatura/checksum/TLS. Os dois executáveis devem estar na mesma pasta acessível pelo sistema.

**Windows:** instale o Python e o Blender. Extraia o pacote FFmpeg indicado pelo site oficial e acrescente sua pasta `bin` ao PATH, ou use `C:\ffmpeg\bin`. Feche e reabra o terminal depois de alterar PATH. O lançador também procura instalações usuais do Blender em Program Files.

**macOS:** instale Python e Blender pelas fontes oficiais. Instale FFmpeg pelo método oficial recomendado ou pelo seu gerenciador de pacotes confiável. O lançador procura Blender em `/Applications/Blender.app` e ferramentas nos diretórios usuais do Homebrew. Não desative verificações do macOS para contornar falhas; corrija a instalação.

**Linux:** use o gerenciador de pacotes da sua distribuição para Python/FFmpeg e uma distribuição Blender compatível. Confira as versões antes de usar o pacote da distribuição, que pode ser anterior a4.3. Não execute scripts remotos sem inspecioná-los.

No terminal, dentro da pasta do pacote:

```sh
python tools/doctor.py
```

Em sistemas que usam `python3`, substitua `python` por `python3`. O diagnóstico confere a presença e a versão real das ferramentas, codificador H.264 e filtro de legendas. O painel pode abrir antes de Blender/FFmpeg estarem prontos, mas a exportação precisa deles.

## 3. Abra o painel

No Windows, abra `ABRIR-PAINEL.bat`. No macOS/Linux, execute `bash ABRIR-PAINEL.sh`. Alternativa pelo terminal:

```sh
python tools/launch_panel.py
```

Mantenha a janela do lançador aberta durante o uso. O painel usa somente conexão local. Se houver uma instância CurioLab em execução, o lançador a reutiliza; se a porta estiver ocupada por outro programa, procura uma livre. `--no-browser` inicia sem abrir navegador, e `--check-only` apenas diagnostica.

## 4. Escolha Claude Code ou Codex

Instale e autentique o assistente de sua preferência seguindo sua documentação oficial:

- Claude Code: https://code.claude.com/docs/en/quickstart
- Codex: https://developers.openai.com/codex/

O CurioLab não instala nem conecta sua conta de IA automaticamente. Abra a pasta completa do pacote como projeto no assistente. Depois, instale a skill:

```sh
python INSTALAR-SKILL.py --agent both --scope project
```

No Windows, `INSTALAR-SKILL.bat` encontra Python/py. No macOS/Linux, use `bash INSTALAR-SKILL.sh`. Os lançadores padrão instalam para ambos os assistentes dentro do projeto e não mudam o perfil global. É possível selecionar `--agent codex` ou `--agent claude`.

A skill vai para `.agents/skills/curiolab-3d` no Codex e `.claude/skills/curiolab-3d` no Claude Code. Cada cópia guarda `CURIOLAB_ROOT.txt` com a pasta completa. Repetir a instalação idêntica não sobrescreve nada. Uma versão diferente exige `--replace`, preservando backup. O ZIP traz `PACKAGE-MANIFEST.json`: arquivos alterados ou ausentes impedem a instalação, sem ocultar a falha.

Para testar o fluxo real após instalar:

```sh
python tools/smoke_skill.py
```

Esse comando abre um servidor apenas local, cria um pedido novo, renderiza uma Casa em 3D por 3s a 1080×1920/30fps, decodifica o MP4, conclui o pedido e confere a galeria. Logs e relatório ficam em `.local/smoke/ID`. Não usa APIs pagas nem publica nas redes. `python INSTALAR-SKILL.py --test` combina instalação e teste. Playwright/Chromium são opcionais para `python tools/smoke_skill.py --with-nico`, que também captura o NICO candidato em prévia explícita.

Instalação global opcional:

```sh
python tools/doctor.py --install-skill --agent claude
```

Ou, para Codex:

```sh
python tools/doctor.py --install-skill --agent codex
```

A instalação cria um ponteiro local para a pasta do pacote. Se já existir uma skill, a operação recusa sobrescrever. `--replace-skill` preserva backup antes de atualizar. Reabra a sessão; invoque `/curiolab-3d` no Claude Code ou `$curiolab-3d` no Codex. Uma instalação em destino temporário e os lançadores foram testados no Linux desta sessão; a execução nativa em Windows/macOS e o carregamento em uma conta real de cada assistente ainda precisam ser conferidos no seu computador.

## 5. Configure Meu canal

Preencha nome, identificador, assunto e público. Esses campos são configurações locais: não registram nome nas redes. Revise a receita editorial. Escolha personagem, acabamento e ambiente; confira as cores RGB/HEX. Use imagens próprias para logo/capa. Salve e reabra a página para verificar persistência.

## 6. Conecte a voz, se quiser

Há três caminhos disponíveis: enviar áudio pronto, ElevenLabs ou OpenAI API. ChatGPT Pro e a assinatura de Claude Code/Codex não significam créditos das APIs de voz.

Para ElevenLabs, crie sua conta, escolha um plano adequado ao uso pretendido e gere uma chave na área de desenvolvedores. Permita a consulta de vozes e Text to Speech conforme a documentação e sua necessidade. No painel, abra **Meu canal → Conectar API de voz**, escolha o provedor e cole a chave no campo protegido. Não envie a chave em chat.

O servidor guarda a chave fora do perfil do canal, em `.local/credentials`. No Linux, arquivo0600 e diretório0700; essa proteção não é cifragem. Não coloque a pasta em repositórios, páginas públicas ou pacotes de venda. Sistemas Windows/macOS precisam de verificação local das permissões. O ZIP exportado pelo aplicativo exclui `.local`.

“Salvar chave e testar” faz uma consulta autenticada de leitura. Depois, consulte a lista de vozes e selecione o identificador. Salve as preferências do canal. Uma leitura bem-sucedida não garante saldo nem acesso ao modelo de síntese.

**Gerar amostra usando meus créditos** é uma ação separada: ela pode consumir créditos. Confira texto e conta antes de clicar. O arquivo de áudio é validado com ffprobe antes de aparecer no painel. Se a chamada for negada, leia a etapa indicada: autenticação, permissão/rede ou créditos. Não desative TLS nem troque uma chave que já funciona sem diagnóstico.

A API OpenAI é opcional e usa sua própria chave e cobrança, separadas do ChatGPT. Você também pode gerar voz fora do painel e enviar MP3/WAV/M4A no editor. Nenhuma conta de voz foi fornecida nesta sessão, portanto o fluxo autenticado de produção ainda não foi validado com um provedor real. Os testes do contrato usaram respostas controladas e áudio real de teste, sem cobranças.

## 7. Faça o primeiro vídeo

Em Comece aqui, descreva a pergunta e prepare um pedido. O painel salva o briefing e oferece uma instrução para levar ao Claude Code/Codex. Isso é uma fila de pedidos, não uma IA executando silenciosamente dentro do site. Peça ao assistente para ler o pedido, revisar fatos, escrever roteiro e planejar cenas. A skill usa `tools/process_request.py` para registrar etapas e só conclui o pedido após validar o MP4.

Para testar o motor sem API, peça uma prévia da Casa ou da Sala. No editor de cenas, os templates nativos permitem exportar até30s; o modo imagens compõe até180s. Escolha FullHD1080×1920. Voz não é gerada só por salvar o roteiro: envie áudio ou gere pela integração configurada. A narração precisa caber na duração do vídeo.

Assista ao arquivo inteiro: texto, enquadramento, peças, continuidade, voz e fatos. O painel não publica automaticamente nas redes. Copie o arquivo final para seu celular ou ferramenta de publicação.

## Antes de vender

Valide o fluxo na sua máquina e com a sua conta. Teste uma instalação limpa nos sistemas que pretende atender, uma geração de voz autenticada, um episódio completo e a recuperação de backup. Defina escopo da biblioteca, suporte, custos externos e condições de venda. O painel funcionar neste ambiente não comprova esses testes comerciais.

## Visualizador permanente do NICO

O pacote inclui o visualizador React/Three.js já compilado. Consumidores não precisam instalar Node para abrir o painel e avaliar o NICO; é necessário navegador com WebGL2 ativo. Use Meu canal → NICO versionado → Abrir prévia3D. Modelos candidatos são separados de produção. A versão atual aguarda aprovação visual e os arquivos originais das duas referências para arquivamento.

Para desenvolvimento do módulo: `cd mascot-studio`, `npm ci`, `npm test`, `npm run build`. O build verifica o bloqueio das fontes; mudanças de geometria, animação ou configuração exigem uma nova versão deliberada. O comando usa lockfile; não atualize dependências ou modelos silenciosamente.

A migração SQL é somente uma proposta para revisão. O instalador não cria um banco nem assume credenciais. As APIs de voz continuam exigindo conta e teste autenticado do usuário; o novo visualizador não muda esse requisito.
