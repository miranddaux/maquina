# Registro versionado do NICO: proposta de banco

**Estado: proposta para revisão; nenhuma migração aplicada.**

O projeto atual usa `app.py` e `panel_state.py` em Python, com configurações JSON em `.local`. Não foi encontrado um banco SQL existente, esquema de projetos SQL ou credenciais de banco. Esses dados continuam preservados. O registro por arquivos funciona sem SQL e sem credenciais.

## Fonte de verdade e aprovação

Cada versão tem `shared/mascots/<id>/<versão>/config.json` e `manifest.json`. O manifesto fixa o SHA-256 do JSON canônico (UTF-8, chaves ordenadas, sem espaços), e cada arquivo de modelo/referência disponível tem seu próprio hash. Referências que existem apenas como imagens na conversa têm estado `pending_original_bytes`: isso não afirma que os arquivos originais foram salvos.

As imagens recebidas definem a direção visual. `1.0.0-candidate.1` é uma versão candidata do modelo procedural; não significa que a renderização 3D já foi aprovada. Alterar proporções, geometria, animação ou paleta exige outra versão e novos previews. A aprovação deve gerar uma versão nova com estado `approved`, preservando a candidata anterior. Não editar uma versão publicada para mudar seu estado.

Um projeto novo registra explicitamente `id`, `version`, `config_sha256`, `geometry_version` e `animation_version`. O renderizador resolve essa versão exata. Não existe resolução automática por `latest`, regeneração do personagem por vídeo, substituição de versão ausente ou migração silenciosa de perfis antigos. Hash divergente interrompe a operação. O catálogo informa versões inválidas para correção.

## Migração proposta

O arquivo `migrations/001_mascot_registry.sql` propõe três tabelas SQLite:

| Tabela | Conteúdo |
| --- | --- |
| `mascot_versions` | Configuração completa imutável, estado, versões e hash. |
| `mascot_assets` | Caminhos de arquivos realmente existentes e seus hashes. |
| `video_mascots` | Versão e hash congelados para cada vídeo/projeto. |

Chaves compostas impedem associar um vídeo a outro hash/versão de geometria ou animação. Triggers impedem atualizar ou apagar o histórico. A proposta não assume uma tabela de vídeos já existente; o vínculo com uma tabela real deve ser ajustado depois de inspecionar o banco escolhido. Não contém `DROP`, alterações de tabelas existentes ou importação automática de dados.

Antes de aplicar: escolher e inspecionar o banco real, conferir conflitos de nomes, revisar a proposta e autorizar a migração. Depois da autorização, fazer backup, aplicar em transação, verificar as três tabelas/chaves/triggers e importar apenas versões explicitamente selecionadas. Se já existir um banco PostgreSQL ou outro SQL, adaptar e revisar o dialeto; não presumir credenciais ou criar um SQLite paralelo silenciosamente.

## Integração disponível

```python
registry = MascotRegistry(project_root)
catalog = registry.catalog()
snapshot = registry.pin('nico', '1.0.0-candidate.1')
config = registry.resolve(snapshot)
# Para saída que exige aprovação visual:
# config = registry.resolve(snapshot, require_approved=True)
```

`SqliteMascotStore(caminho_existente, approved_schema=True)` só abre um arquivo já existente com as três tabelas propostas; sem aprovação explícita ou esquema presente, falha sem criar banco ou executar DDL. `register_version()` copia metadados validados para SQL e rejeita alterações de uma identidade existente. `assign_video()` fixa a associação sem sobrescrever vídeo anterior. Esse adaptador é opcional e não é ativado no início do programa.

Testes usam diretórios e bancos temporários isolados; aplicar DDL nesses testes não representa uma migração dos dados do produto.

## Ativação opcional após revisão

A integração do aplicativo fica desligada por padrão. Depois de revisar e aprovar a migração em um banco SQLite existente, configure `CURIOLAB_MASCOT_SQLITE_PATH` com o caminho do arquivo e `CURIOLAB_MASCOT_SCHEMA_APPROVED=1`. Esses valores não são credenciais. O adaptador exige que o arquivo e as três tabelas já existam; não cria banco nem executa migrações.

Com ativação explícita, exports com mascote aprovado registram a versão e o pin pelo ID do MP4, e a ferramenta de conclusão de pedidos faz o mesmo. Falhas de integridade não substituem a versão nem sobrescrevem histórico. Enquanto esse modo não for autorizado/configurado, o registro versionado em arquivos continua ativo.
