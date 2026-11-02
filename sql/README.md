# Consultas e modelos SQL

## Demonstração PostgreSQL sintética

Os roteiros R02–R06 acrescentam nove consultas `academic_*.sql` para histórico,
carga, alocações, funções, vigências, cadastro/situação acadêmica, bolsas e
convenções de simulação. Cada consulta tem parâmetros vinculados, limite de saída
e nome fechado no leitor. Os mapeamentos físicos e os INSERTs de atos fictícios
ficam no script local de preparação, fora do Git/Docker. A interface não cria
objetos nem insere registros. A conta usada pelo aplicativo continua somente leitura.

`synthetic_demo/` contém a lista fechada de sete consultas da tela: identificação
da base, departamentos, períodos, registros docentes, alocações e, para a R01,
`faculty_register.sql` e `faculty_real_hours.sql`, com departamento vinculado. São contratos
genéricos das views da fixture local, sem nomes de fontes físicas institucionais.
Departamento e período usam parâmetros Psycopg vinculados; não há SQL recebido da
interface nem interpretação de texto como regra de acesso. As permissões da conta
sintética são conferidas separadamente. A instalação das views e seu mapeamento
interno permanecem locais, em script e SQL ignorados por Git/Docker, conforme o
[guia da base sintética](../docs/operations/SYNTHETIC_POSTGRES.md).

## Descoberta institucional — histórico da fase 1

Fase 1: SQL Server continua hipótese; conexão e inventário estão **NÃO VALIDADOS**.
Os comandos de diagnóstico e inventário são documentados em
[DATABASE_DISCOVERY.md](../docs/operations/DATABASE_DISCOVERY.md) para execução manual por Matheus
fora da sessão do agente. Não armazenar resultados, credenciais, nomes físicos internos
ou configurações reais nesta pasta.

## Consultas fixas da descoberta

`diagnostics/connection_probe.sql` contém a prova `SELECT 1`. O adaptador SQLAlchemy
pode executar metadados internos de inicialização do dialeto antes dessa prova.

Os quatro arquivos de `catalog/` são a lista fechada do inventário: objetos,
colunas/tipos, chaves e relações declaradas. Schema, schemas permitidos e limite
são valores vinculados; nomes de fontes institucionais não são inventados nem
interpolados. Consultar somente o banco da conexão aprovada, sem enumerar bancos.
As consultas também são empacotadas no wheel e testadas por compilação, sem banco.

## Qualidade — modelos desabilitados

Os arquivos em `quality/*.sql.template` não são executáveis da aplicação e não são
carregados pela CLI `vrac.db`:

| Modelo | Resultado agregado preparado para revisão |
|---|---|
| `duplicate_keys.sql.template` | Distribuição de repetições por chave lógica não nula, sem devolver chaves individuais |
| `missing_values.sql.template` | Linhas no recorte e nulos em uma coluna lógica; soma nula quando não há linhas |
| `relationship_cardinality.sql.template` | Distribuição de filhos distintos por chave em uma fonte; não comprova FK/PK |

Os tokens `{{APPROVED_*}}` representam identificadores ainda não mapeados. Não há
renderizador automático. Departamento, período e limite de grupos são valores
vinculados (`:department`, `:period`, `:max_groups` quando aplicável), não strings
concatenadas. As chaves simples destes modelos não autorizam adaptar chaves compostas
por concatenação nem inventar junções.

Distribuição vazia, isoladamente, não distingue recorte sem linhas de ausência de
repetições ou de chaves não nulas. Interpretar junto da contagem e dos nulos do
mesmo recorte aprovado; não preencher o resultado com zero por conveniência.

Antes de uma futura execução: revisar objetos/colunas/chaves, filtros, timeout,
orçamento de leitura/agrupamento e permissão com o DBA; produzir um arquivo fixo revisado
fora do workspace quando contiver nomes internos. `TOP` limita saída, não custo.
O [exemplo de configuração](../config/quality_checks.example.toml) mantém todas as
verificações e aprovações falsas. Alterar suas flags não faz a CLI executar qualidade.

Não usar `SELECT *`, contagens globais ou amostras individuais. Dados ausentes não
provam inexistência. As consultas de análises só entram após mapeamento e revisão,
em lista fechada e com conta de leitura administrativamente confirmada pelo DBA.
