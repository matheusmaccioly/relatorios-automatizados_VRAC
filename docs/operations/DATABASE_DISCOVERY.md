# Diagnóstico e descoberta do banco — fase 1

Atualizado em 27/10/2026. **Conexão e inventário: NÃO VALIDADOS.** SQL Server continua uma hipótese; o suporte preparado não confirma o ambiente da PUC-Rio. Não houve consulta real nesta sessão do agente. O aplicativo de demonstração continua separado destes comandos e não libera dados reais.

Os comandos abaixo são para Matheus executar manualmente **fora da sessão do agente**, no ambiente autorizado. Não enviar credenciais, configuração real, inventário bruto ou metadados internos no chat. O [guia](../references/Guia_Desenvolvimento_VRAC_Codex.md) e [AGENTS.md](../../AGENTS.md) continuam aplicáveis.

## Antes da execução real

1. Confirmar com DBA/DSI o SGBD, endpoint, porta, banco, autenticação, driver, schemas e permissão desta descoberta. Não tentar portas, servidores ou schemas por aproximação. Se não for SQL Server, registrar a diferença e manter a integração bloqueada.
2. Obter revisão administrativa do DBA sobre a conta: somente leitura nos objetos e recortes aprovados, sem privilégios de escrita ou administração. Não comprovar restrição executando escrita. `SELECT 1`, `ApplicationIntent=ReadOnly` e flags no TOML não provam ausência de privilégio de escrita.
3. Confirmar rede/VPN e certificado confiável com a DSI. A verificação manual de conectividade deve se limitar ao endpoint e à porta informados, sem varredura de DNS, rede, instâncias ou portas. Não alterar firewall ou elevar privilégios para contornar falhas.
4. Preparar diretório privado local **fora do workspace**, protegido por ACL NTFS aprovada. Não usar pasta pública, compartilhada ou sincronizada com serviço externo. Limitar acesso à identidade autorizada e aos responsáveis definidos pela DSI; revisar herança, usuários e grupos antes de armazenar a configuração. A DSI deve definir retenção e descarte.

## Preparar dependências

O suporte SQL Server é um extra opcional. No terminal local do projeto, o operador pode instalar as dependências Python com o bootstrap:

```powershell
.\scripts\bootstrap.cmd --sqlserver
```

Onde a execução de PowerShell for permitida, a alternativa é `scripts/bootstrap.ps1 -SqlServer`. Os scripts preservam as verificações de TLS e a política de execução. O extra equivale a `uv sync --locked --extra sqlserver`, usando o ambiente local do projeto. Não executar um `uv sync` sem o extra imediatamente depois, pois a sincronização pode removê-lo.

SQLAlchemy/pyodbc não instalam nem homologam o driver ODBC do sistema. A DSI deve preparar o driver compatível, arquitetura, autenticação e cadeia de certificados. Autenticação Windows usa a identidade do processo autorizado e depende da configuração institucional; não presumir que funcionará em outro sistema operacional ou em container.

## Criar a configuração privada

Copiar manualmente [database.example.toml](../../config/database.example.toml) para um arquivo chamado **`dbconfig.toml`** no diretório privado externo. Esse nome exato é obrigatório. Usar caminho absoluto local, arquivo UTF-8 sem BOM e tamanho máximo de 64 KiB. Editar somente essa cópia, fora da sessão do agente. O arquivo versionado deve permanecer com campos vazios e confirmações falsas.

| Campo | O que obter e registrar |
|---|---|
| `dbms`, `sqlserver_confirmed` | `mssql` e confirmação humana de SQL Server; não usar a flag para afirmar uma hipótese |
| `scope_approved` | Aprovação registrada da execução, banco e schemas; não substitui permissões reais |
| `server`, `port`, `database` | Endpoint, porta e um banco autorizados; `port = 0` no exemplo é inválido de propósito |
| `schemas` | Lista fechada de 1 a 8 schemas aprovados, com grafia exata fornecida pelo DBA; não há busca automática de schemas |
| `driver`, `auth_mode` | Nome exato do driver instalado; `windows` ou `sql_password`, conforme decisão institucional |
| `credentials` | Campos vazios em `windows`; usuário/senha somente na cópia externa privada em `sql_password` |
| Timeouts | Conexão: 10 s e consulta: 30 s no exemplo; revisar limites com DBA sem removê-los para contornar falhas |
| `metadata_row_limit` | 1000 linhas por consulta no exemplo, máximo 5000; limite não garante completude |

A aplicação não carrega `.env` ou `secrets.toml` para estes comandos. Não fornecer URL de conexão, senha ou identidade na linha de comando. TLS e validação de certificado permanecem obrigatórios; não utilizar `TrustServerCertificate=yes` nem desativar criptografia.

## Executar diagnóstico e inventário

Na raiz do repositório, esta consulta à ajuda é segura e não precisa de configuração real:

```powershell
.\.venv\Scripts\python.exe -m vrac.db --help
.\.venv\Scripts\python.exe -m vrac.db diagnose --help
.\.venv\Scripts\python.exe -m vrac.db inventory --help
```

Os atalhos `scripts/diagnose-db.cmd` e `scripts/inventory-db.cmd` aceitam os mesmos argumentos dos respectivos subcomandos. Chamá-los sem `--execute` também mantém a execução bloqueada; os atalhos não acrescentam essa autorização automaticamente.

Nos exemplos seguintes, substituir `<ARQUIVO_EXTERNO>` pelo caminho absoluto da cópia privada cujo nome final é `dbconfig.toml`. Sem `--execute`, o comando bloqueia antes de ler o arquivo, carregar dependências de banco ou abrir rede; **não é uma validação da configuração**:

```powershell
.\.venv\Scripts\python.exe -m vrac.db diagnose --config '<ARQUIVO_EXTERNO>'
```

Somente após as aprovações e fora da sessão do agente, Matheus poderá executar:

```powershell
.\.venv\Scripts\python.exe -m vrac.db diagnose --config '<ARQUIVO_EXTERNO>' --execute
.\.venv\Scripts\python.exe -m vrac.db inventory --config '<ARQUIVO_EXTERNO>' --execute
```

O diretório-base de saída padrão é `vrac-discovery-private` ao lado da configuração externa. Para outro diretório-base privado aprovado, passar `--output-dir '<DIRETORIO_EXTERNO>'`, com caminho absoluto local e pai já existente. Configuração e saída devem ficar fora do workspace. Não usar UNC, unidade de rede ou diretório público/sincronizado.

Cada execução cria uma subpasta nova com seu UUID e grava nela `diagnose.json` ou `inventory.json`, sem sobrescrever uma execução anterior. Antes de qualquer dado, a nova subpasta recebe DACL NTFS protegida com acesso somente ao usuário do processo; em Unix, diretório `0700` e arquivo `0600`. A ferramenta não modifica a ACL de diretórios-base existentes. Isso não substitui a revisão prévia do diretório, da ACL, da conta e da política de retenção pela DSI. Falha em proteger a saída interrompe a operação antes de consultar o banco.

O console identifica a execução pelo UUID, sem revelar o caminho privado. As mensagens devem permanecer sanitizadas, sem servidor, identidade, connection string, registros ou traceback bruto. Os JSON locais privados podem conter nomes físicos de metadados: não os versionar, anexar ao chat ou compartilhar automaticamente. Um erro sanitizado não autoriza imprimir a exceção original para investigar; acionar o DBA/DSI pelo canal aprovado.

| Código de saída | Significado |
|---|---|
| `0` | Diagnóstico `passed` ou inventário tecnicamente `valid`; não comprova privilégios ou completude |
| `1` | Falha da operação ou da preparação/gravação privada |
| `2` | Execução recusada, argumentos ou configuração inválidos/não aprovados |
| `3` | Inventário parcial; revisar avisos no JSON privado |
| `130` | Cancelamento pelo operador |

## Interpretar os resultados

A instrução explícita da prova de conexão é `SELECT 1`; o dialeto SQLAlchemy também pode executar verificações internas de compatibilidade ao abrir a conexão. Esses resultados internos não são impressos nem usados como inventário. Sucesso confirma essa conexão e a prova naquele momento; não confirma o conjunto completo de permissões, o inventário, a atualização da origem ou a publicação do aplicativo.

| Categoria de falha | Próxima verificação autorizada |
|---|---|
| Configuração | Campos obrigatórios, confirmações e escopo; revisar a cópia privada sem expor valores |
| Dependências/driver | Extra Python, driver aprovado e compatibilidade de arquitetura; instalação com DSI |
| Nome/rede/VPN/porta | Endpoint específico fornecido e acesso institucional; nenhuma varredura |
| Certificado/TLS | Cadeia, nome do certificado e validade com DSI/DBA; não relaxar validação |
| Autenticação | Método, identidade e condição da conta com responsáveis; não trocar para conta privilegiada |
| Permissões | Escopo administrativo confirmado pelo DBA; não executar escrita ou conceder acesso pela ferramenta |
| Timeout ou falha não conclusiva | Distinguir rede, autenticação lenta e consulta com DBA/DSI; categoria pode ser ambígua e não prova a causa |

O inventário consulta somente metadados do banco configurado e dos schemas explicitamente aprovados: tabelas/views, colunas/tipos/nulabilidade e chaves PK/UQ/FK declaradas quando visíveis. Não extrai linhas acadêmicas, definições completas de views/procedimentos ou amostras pessoais; não percorre outros bancos.

O orçamento do catálogo é de até quatro consultas por schema e até oito schemas, com timeout por consulta e limite de linhas por consulta. Esse máximo de 32 consultas não inclui verificações internas de inicialização do dialeto SQLAlchemy. Se houver truncamento, erro ou restrição de visibilidade, o material é parcial/desconhecido: não aumentar o escopo ou repetir consultas globais automaticamente. Pedir ao DBA um recorte ou metadado autorizado mais específico.

O limite de linhas pode cortar colunas de uma chave composta ou de uma FK. Um fragmento truncado não é uma chave completa e não pode orientar deduplicação ou junção na fase 2 sem confirmação do DBA.

Metadados invisíveis e relações não retornadas são **desconhecidos**, não inexistentes. A cobertura é sempre registrada como `unknown`, inclusive quando as consultas têm estado `valid`. Tipos personalizados fora dos schemas aprovados ficam ocultos; FKs só entram quando origem e destino pertencem ao escopo. Relações declaradas não demonstram a granularidade de uma view ou as regras de negócio; ausência de PK/FK visível não autoriza deduplicação ou joins por nomes. A visibilidade depende das permissões da identidade, conforme a [documentação da Microsoft](https://learn.microsoft.com/en-us/sql/relational-databases/security/metadata-visibility-configuration?view=sql-server-ver17).

## Testes: offline e integração explícita

`scripts/check.cmd` executa a suíte padrão offline, com banco e rede bloqueados. Testes marcados `integration` ficam fora dessa suíte. Selecionar apenas a marca não libera a conexão: a integração exige também as duas opções explícitas abaixo e a configuração externa aprovada.

Somente Matheus, fora da sessão do agente e após as aprovações, poderá executar:

```powershell
.\.venv\Scripts\python.exe -m pytest -m integration --run-db-integration --db-config '<ARQUIVO_EXTERNO>'
```

Essa integração executa a prova de conexão, não o inventário completo nem teste de escrita. Não foi executada nesta entrega. Preferir os comandos de diagnóstico/inventário para obter um relatório privado associado ao UUID; o teste de integração não substitui esse registro operacional.

## Qualidade e cardinalidade: execução ainda desabilitada

[quality_checks.example.toml](../../config/quality_checks.example.toml) e os [templates SQL](../../sql/README.md) apenas preparam a revisão. A CLI `vrac.db` **não carrega nem executa** essas verificações, mesmo que alguém altere suas flags. Tokens `{{APPROVED_*}}` são identificadores lógicos ainda sem mapeamento; não há renderizador ou SQL gerado pela interface.

Antes de qualquer execução futura: DBA/Matheus aprovam objetos, chave, colunas, departamento/período, parâmetros vinculados, timeout e orçamento; revisam uma consulta fixa; registram a aprovação fora do workspace quando contiver nomes internos. Identificadores SQL não são parâmetros de valor: sua substituição exige revisão do arquivo, nunca concatenação de entradas da usuária. `TOP` limita a saída, não o custo de leitura e agrupamento. Não executar contagens globais, `SELECT *`, amostras individuais ou novas consultas só porque o resultado foi vazio.

## Material necessário para a fase 2

Matheus deve revisar os arquivos privados e preencher separadamente o [dicionário sanitizado](SANITIZED_DATA_DICTIONARY.md), com autorização para divulgação. Não copiar o inventário físico automaticamente. Registrar data e resultado sanitizado do diagnóstico, cobertura/limitações do inventário, escopo confirmado pelo DBA e evidência de autorização do material entregue. A fase 2 só tratará como aprovados os campos cuja confirmação humana estiver registrada.

Referências técnicas consultadas em 27/10/2026: [ODBC/TLS — Microsoft](https://learn.microsoft.com/en-us/sql/connect/odbc/dsn-connection-string-attribute?view=sql-server-ver17) e [SQL Server/pyodbc — SQLAlchemy](https://docs.sqlalchemy.org/en/20/dialects/mssql.html#pyodbc). Essas referências não descrevem a configuração institucional.
