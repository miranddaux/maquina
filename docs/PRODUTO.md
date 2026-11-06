# CurioLab 3D — projeto e limites da primeira versão

Nome provisório; verificar marca e disponibilidade do domínio antes de investir. Uma bancada simples de produção de curiosidades em português, com autoria e checagem humanas, para Shorts de YouTube. TikTok e Reels recebem adaptações depois de validar o primeiro formato.

## O que estamos construindo

1. Um estúdio local para organizar assunto, roteiro e cenas.
2. Uma demonstração de animação 3D procedural em Blender: rotação da Terra. O render local usa geometria real e FFmpeg para exportar MP4 vertical.
3. Uma skill instalável que orienta o Codex no processo editorial e no uso do renderizador.
4. Uma landing page original, com proposta de produto e preço de teste de R$ 37,90. Esse valor é uma hipótese comercial, sem checkout ativo.
5. Um experimento editorial de sete dias, seguido por até três vídeos explicativos com os resultados realmente observados.

A existência destas instruções não comprova uma integração. Consultar README, execução e testes para saber o que está validado. O primeiro template não converte qualquer roteiro em cenas automaticamente. Novos assuntos precisam de templates e validação; geração de imagens, vídeo por API e narração automática são extensões futuras até serem implementadas e testadas.

## Experiência de uso

Fluxo: escolher pauta → checar fatos → aprovar roteiro → revisar cenas → adicionar voz → renderizar → assistir ao MP4 inteiro → publicar manualmente → registrar métricas.

A interface deve explicar antes do render qual template será usado, se há narração e quais etapas são locais. Textos de roteiro e cenas são rascunhos editáveis. Estados úteis: salvo, aguardando revisão, renderizando, concluído e erro recuperável. Uma falha precisa indicar a etapa e como repetir sem perder o projeto. Evitar botões que anunciem integração indisponível como funcional.

## Identidade inicial

**CurioLab 3D:** laboratório divertido de perguntas pequenas e descobertas visuais. Paleta sugerida: violeta escuro, creme, verde-lima e amarelo. Formas arredondadas, textura retrô leve e tipografia legível. Mascote proposto: **Pingo**, um pequeno planeta curioso com olhos e um anel inclinado. O mascote aparece na marca e nas capas institucionais; os vídeos usam os elementos mais simples adequados à explicação. Não reproduzir o personagem, a marca, thumbnails ou roteiros do canal de referência.

Bio provisória: “Uma pergunta, uma descoberta. Curiosidades em animação 3D, com fontes na descrição.” Nome e identificador finais dependem de disponibilidade. Não anunciar títulos profissionais ou credenciais inexistentes.

## Domínio e e-mail profissional

Ainda não provisionados. Escolher e registrar um domínio disponível em conta do proprietário; selecionar provedor de e-mail; criar `oi@dominio-escolhido` ou `contato@dominio-escolhido`; configurar MX, SPF e DKIM conforme o provedor, depois DMARC; testar envio, recebimento e recuperação da conta. Senhas e chaves entram nos ajustes seguros do ambiente ou do provedor, nunca no Git ou no chat. Confirmar domínio e orçamento antes de qualquer compra. A landing não deve exibir endereço inventado como canal ativo.

## Modelo comercial a validar

O produto inicial é o pacote de skill + scripts locais + instruções. Não vender como serviço ilimitado de geração de vídeo. A página deve explicar requisitos de Blender, FFmpeg e Python, formatos suportados, limites dos templates, condições de atualização, suporte e eventuais custos separados de APIs. Licenciamento de dependências e assets precisa ser conferido antes da distribuição comercial; não incluir binários de terceiros automaticamente no download.

R$ 29,90 e R$ 37,90 são opções de teste, sem promessa de rentabilidade. Definir checkout, identificação do vendedor, entrega, termos, privacidade e atendimento/reembolso aplicáveis antes de abrir vendas. Não coletar leads com um formulário que não tenha destino funcional e informação de tratamento de dados.

## Custos e próximas decisões

- Demonstração local: não exige API paga; consome recursos da máquina. Sem cobrança automática externa.
- Voz ElevenLabs: único serviço de geração pago considerado pelo usuário nesta fase. Ainda não há conta ou voz escolhida; conferir plano e direitos de uso. Uma integração por API exige configuração segura de `ELEVENLABS_API_KEY` e `ELEVENLABS_VOICE_ID` e precisa estar implementada e testada antes de ser anunciada. Também é possível gerar voz na interface e baixar o áudio. Não pressupor franquia gratuita ou permissão comercial.
- Imagens: usar o ChatGPT Pro que o usuário já possui, por geração e exportação manual na interface. A assinatura não inclui automaticamente créditos de API. O render inicial não converte imagens em animação. Não depender de APIs pagas de imagem ou vídeo nesta fase.
- Domínio, hospedagem, e-mail e checkout: contratar depois da escolha do usuário.

O sucesso do experimento é produzir com consistência e medir o que aconteceu. Não há garantia de viralização, receita ou de atingir 1,5 milhão de visualizações em sete dias.
