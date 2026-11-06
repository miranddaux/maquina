# Alerta do Windows e distribuição

O usuário relatou que o Windows marcou o ZIP 0.4.0-preview.1 como vírus. Ainda não informou o texto exato, o nome da ameaça, o componente que bloqueou ou o arquivo interno apontado. A causa está **sem confirmação**. Não classificar como falso positivo nem como malware confirmado sem evidência.

SHA-256 do pacote relatado: `130377315a9714f62b1814ade3e3ce2e06313a34eda5d4ffcc46be687686780b`.

A versão 0.4.0-preview.1 foi retirada dos downloads atuais. O registro e a versão no histórico Git permanecem para investigação. Não execute uma cópia bloqueada.

## Mudança de distribuição

- A skill textual contém somente Markdown, JSON e YAML, sem scripts, JavaScript ou modelos binários.
- O motor é distribuído separadamente, em código-fonte, com interface e ativos necessários. Não inclui atalhos `.bat`, `.cmd`, `.ps1`, `.sh`, executáveis Windows, bibliotecas nativas, compactação com senha ou dependências instaladas.
- Instalação e abertura do painel exigem comandos explícitos. Não há instalação automática ao extrair, mudança de antivírus, elevação para administrador ou alteração de inicialização do sistema.
- Os arquivos do motor continuam legíveis no repositório. A interface compilada inclui as fontes TypeScript correspondentes e os avisos de terceiros.
- O manifesto SHA-256 detecta alteração de arquivos. Ele não constitui assinatura de editor, análise antivírus ou garantia de segurança.

## Identificar o alerta

Se a detecção veio da Segurança do Windows, consulte **Proteção contra vírus e ameaças → Histórico de proteção**. Registre o nome da ameaça, o arquivo afetado e a ação tomada. Se o aviso veio do navegador ou SmartScreen, registre esse texto também. Aviso de reputação e detecção de ameaça são resultados diferentes; o texto do alerta permite distinguir.

Não use “Executar assim mesmo”, exceções no Defender, desativação de proteção ou renomeação de arquivos para instalar uma cópia bloqueada. Mantenha-a em quarentena. Não compartilhe credenciais ou caminhos com dados pessoais ao relatar o problema.

## Limites da validação atual

O ambiente de desenvolvimento é Linux. Não dispõe de Microsoft Defender/SmartScreen nem de outro motor antivírus instalado. As verificações executadas aqui são revisão do código, regras de conteúdo do ZIP, verificação de integridade e testes funcionais. A nova distribuição ainda não foi liberada por um teste no Windows.

Se a investigação confirmar um falso positivo, a análise do fornecedor poderá ser solicitada em https://www.microsoft.com/wdsi/filesubmission . Isso requer uma submissão deliberada, feita pelo responsável, e não garante aprovação.
