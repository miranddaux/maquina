# Distribuição e alerta de antivírus

O usuário relatou um alerta do Windows para o ZIP 0.4.0-preview.1; a identificação da detecção ainda está pendente. Não recomendar esse pacote nem afirmar falso positivo. Leia SECURITY.md na raiz do motor para os fatos e limites da investigação.

O pacote de skill é agora somente textual: Markdown, JSON e YAML. Extraia a pasta curiolab-3d e copie para `.agents/skills/` no Codex ou `.claude/skills/` no Claude Code do projeto. Isso instala as instruções, sem executar arquivos. Reabra a sessão para carregá-las.

No ZIP textual, `references/production-recipe.md`, `palette-and-environment.md`, `installation-guide.md`, `nico-config.json` e `channel-brand.json` acompanham o método de roteiro, câmera, cores e a configuração da identidade. Esses arquivos são cópias informativas; o motor deve resolver os dados canônicos e o modelo aprovado na sua própria instalação antes de renderizar. Se os documentos `docs/` da raiz não existirem, leia estas cópias para planejar, sem fingir que o motor está instalado.

A geração de MP4 exige o motor CurioLab 3D separado, Python, Blender e FFmpeg. Abra o projeto do motor existente ou informe `CURIOLAB_ROOT` apenas com um caminho local válido. Se o motor não existir, explique o requisito; uma skill textual não inclui renderizador.

O motor usa instalação explícita por Python e distribui fontes/ativos, sem atalhos `.bat`/shell ou executáveis nativos. Não alterar nem desativar antivírus, não criar exceções e não orientar o usuário a executar um arquivo bloqueado. Não disfarçar extensões para contornar detecções. Uma soma SHA-256 e testes de render não certificam ausência de malware.

Sem o texto exato, pedir nome da detecção e arquivo afetado. Não prometer que retirar atalhos resolve um alerta que não foi identificado. As contas das APIs, certificados de assinatura e validação no Windows não são criados por esta skill.
