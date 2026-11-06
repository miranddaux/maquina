# CurioLab 3D

Use a skill `skills/curiolab-3d/SKILL.md` e leia README.md antes de operar. O painel é um espelho dos arquivos e preferências, não um agente autônomo embutido. Pedidos ficam em `.local/requests`. Use o checkout existente; não crie worktree sem pedido explícito.

Preserve material do usuário. Nunca leia, imprima ou copie `.local/credentials` para projetos, logs, briefing ou pacotes. Para voz, use o serviço documentado com credenciais configuradas, sem expor valores. Geração por API pode consumir créditos e exige autorização do usuário. Não simule áudio, pesquisa, render ou métricas.

A roupa padrão do personagem é amarelo quente #E8BE45; o snapshot `branding` leva cores, personagem, acabamento e ambiente ao render. Leia `docs/PALETA-E-AMBIENTACAO.md` e `docs/RECEITA-DE-PRODUCAO.md`. Só marque um pedido concluído depois de `tools/process_request.py complete` validar o MP4 real.
