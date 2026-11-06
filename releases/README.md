# CurioLab 3D · downloads atualizados

**O ZIP 0.4.0-preview.1 foi retirado dos downloads atuais após relato de alerta do Windows. A identificação da detecção está pendente. Não execute uma cópia bloqueada.** Leia SECURITY.md e WINDOWS-ALERT.json. As distribuições abaixo não têm liberação por antivírus confirmada.

## Skill textual (aproximadamente 30 KB)

`curiolab-3d-skill-0.4.0-preview.2.zip` contém somente Markdown, JSON e YAML: instruções, receita de roteiro/câmera, paleta, referência de configuração do NICO e identidade do canal. Não contém scripts, interface executável ou modelos binários.

Extraia a pasta `curiolab-3d`. Copie-a para `.agents/skills/` no projeto do Codex ou `.claude/skills/` no Claude Code. Inicie uma nova sessão e use `$curiolab-3d` ou `/curiolab-3d`. Essa instalação de documentos não roda um instalador. Gerar vídeo exige o motor separado.

## Motor e painel (aproximadamente 5,8 MB)

`curiolab-3d-runtime-0.4.0-preview.2.zip` contém código Python, fontes da interface, visualizador compilado, NICO e modelos. Não distribui atalhos `.bat`/shell, executáveis nativos, dependências instaladas ou credenciais. Instalação e abertura são explícitas, no terminal da pasta extraída:

```sh
python INSTALAR-SKILL.py --agent both --scope project
python tools/launch_panel.py
```

No Windows, a alternativa é `py -3` no lugar de `python`. Leia docs/INSTALACAO.md. Python 3.12+, Blender 4.3+ e FFmpeg/ffprobe são requisitos separados; não são instalados silenciosamente. Não execute arquivos que o Windows tenha bloqueado nem altere o antivírus para instalar.

## Verificações e limites

Os arquivos `.sha256` e PACKAGE-MANIFEST.json permitem conferir integridade. Testes automatizados conferem o conteúdo dos pacotes e rejeitam executáveis disfarçados. O teste funcional no Linux cria um MP4 1080×1920/30fps sem API paga. Nenhuma dessas verificações substitui Microsoft Defender/SmartScreen. O motivo do alerta original e a aceitação no Windows continuam pendentes do texto da detecção e de validação nesse sistema.

NICO continua candidato para prévia explícita; referências originais e aprovação de produção estão pendentes. ElevenLabs/OpenAI exigem conta e créditos próprios. Não há publicação automática nem migração SQL aplicada.
