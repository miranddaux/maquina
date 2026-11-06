# CurioLab 3D · skill completa

Pacote de teste 0.4.0-preview.1 para o canal Nicolume, com o NICO versionado.

1. Baixe o ZIP desta pasta e extraia todos os arquivos em uma pasta permanente.
2. Instale Python 3.12+, Blender 4.3+ e FFmpeg/ffprobe se ainda não tiver. Veja docs/INSTALACAO.md.
3. Abra a pasta extraída no Codex ou Claude Code.
4. Execute `python INSTALAR-SKILL.py --agent both --scope project` (ou abra INSTALAR-SKILL.bat no Windows).
5. Inicie uma nova sessão. Use `$curiolab-3d` no Codex ou `/curiolab-3d` no Claude Code.
6. Execute `python tools/smoke_skill.py` para produzir e verificar um MP4 Full HD novo sem APIs pagas.
7. Abra o painel com `python tools/launch_panel.py`.

A skill inclui roteiro, storyboard, paleta, regras de câmera, modelos, motor, painel, referências, instalador e manifesto SHA-256. O NICO candidato tem geometria, paleta e animações fixadas; não é recriado por vídeo. Os originais das referências ainda precisam ser arquivados antes da aprovação de produção. SQL é apenas proposta, nunca aplicado pelo instalador.

O relatório e os vídeos nesta pasta foram produzidos com uma instalação limpa do ZIP no Linux. Vozes ElevenLabs/OpenAI exigem conta, credenciais e créditos próprios; não foram chamadas neste teste. Skill não autentica o assistente nem inclui assinaturas. Windows/macOS e autenticação real ainda precisam de teste no equipamento escolhido. Os vídeos demonstram o teste técnico e estão sem narração.
