# PostgreSQL sintético para desenvolvimento

Os seis roteiros já utilizam essa base. Para calcular, filtrar e exportar os
resultados, seguir o [guia das análises sintéticas](../guides/ANALISES_SINTETICAS.md).
Depois de preparar a carga original e a conexão da tela, executar também
`.\.venv\Scripts\python.exe scripts/prepare-academic-analyses.local.py`.
Esse script instala as fontes adicionais e gera convenções dimensionais e
atos administrativos inteiramente fictícios, sem alterar a carga original.

Esta base reproduz a estrutura semântica acadêmica documentada com valores totalmente
fictícios. Não é preciso extrair registros do banco institucional para criá-la.
Não contém cópia de pessoas, matrículas ou valores reais. PostgreSQL é usado apenas
como ambiente de desenvolvimento solicitado por Matheus; o destino institucional
SQL Server permanece separado.

A carga inicial contém 13 tabelas, 406 colunas e 3.909 registros, com semente fixa
`20261030`. Abrange seis semestres (2024.1 a 2026.2), 24 pessoas docentes com 25 vínculos,
120 matrículas acadêmicas, três departamentos com dados e um departamento vazio.
Inclui múltiplos lotes de folha, mudança de quadro/departamento, duplicidade de
situação acadêmica, múltiplas bolsas, turmas compartilhadas, turmas vazias e
distinção entre zero, `NULL` e ausência de registro. Esses números são cenários de
teste definidos para a fixture, sem significado institucional.
Uma tabela adicional `dataset_metadata` identifica a versão, a semente e o caráter
sintético da base, sem alterar as colunas das 13 fontes do modelo.

## Arquivos e separação dos metadados

- `src/vrac/dev/semantic_postgres.py`: lê nomes e tipos dos dicionários acadêmicos
  locais e produz SQL PostgreSQL, sem conectar ao banco ou executar DAX.
- `src/vrac/dev/postgres_runtime.py`: prepara e inicia um PostgreSQL portátil local
  dedicado, com TLS, autenticação SCRAM e conta de leitura.
- `scripts/synthetic-postgres.local.py`: receita local dos cenários e seleção das
  tabelas. Contém metadados internos e está excluída do Git e do contexto Docker.
- `.cache/synthetic-postgres/bundle-v1/01-seed.sql`: criação do esquema e carga.
- `.cache/synthetic-postgres/bundle-v1/02-check.sql`: conferências técnicas dos cenários.
- `.cache/synthetic-postgres/bundle-v1/manifest.json`: semente, hash da documentação,
  hash da carga, contagens e campos mantidos sem valor.

A receita usa `docs/ANALISE_MODELOS_SEMANTICOS_VRAC.md`, já fornecido localmente.
Nem a receita nem os arquivos gerados entram no pacote da aplicação, Git ou Docker.
O gerador genérico e seus testes funcionam com dicionários fictícios, sem depender
da documentação interna. Não compartilhar a carga ou receita sem a liberação
específica dos metadados, mesmo que seus registros sejam sintéticos.

## Gerar novamente

Na raiz do projeto, com o ambiente Python existente:

```powershell
.\.venv\Scripts\python.exe scripts/synthetic-postgres.local.py
```

O diretório de saída deve ser novo; arquivos existentes não são sobrescritos.
Para comparar duas gerações, use um nome novo dentro da pasta permitida:

```powershell
.\.venv\Scripts\python.exe scripts/synthetic-postgres.local.py --output .cache/synthetic-postgres/bundle-comparacao
```

Mesma documentação, receita e semente produzem a mesma carga. Outra semente altera
somente os valores aleatórios previstos na receita, mantendo os casos de borda.
O gerador não lê CSVs, dumps ou registros do banco institucional.

## Iniciar o banco local

Os binários portáteis Windows ficam em `.tools/postgres/pgsql/bin/`, fora do Git.
Versão executada nesta entrega: **18.6**, com origem e hash do arquivo registrados
localmente em `.tools/postgres/download.json`.
Sua origem é o [arquivo oficial de binários da EDB](https://www.enterprisedb.com/download-postgresql-binaries),
indicado pela [página de download do PostgreSQL para Windows](https://www.postgresql.org/download/windows/).
O OpenSSL que acompanha Git for Windows é usado para o certificado da demonstração.
Não é instalado serviço do Windows nem alterado PostgreSQL já existente na máquina.

```powershell
.\.venv\Scripts\python.exe -m vrac.dev.postgres_runtime start
```

Na primeira execução, o comando cria um cluster novo e carrega a base. Depois, pode
ser repetido para iniciar ou conferir a mesma base sem duplicar registros. A porta
é fixa em `55432`; se estiver ocupada, a inicialização falha sem encerrar outro
processo ou reutilizar outro servidor. A carga SQL também exige banco com nome
`vrac_sintetico` e conexão local e recusa esquema já existente.

| Campo | Valor |
|---|---|
| Servidor | `127.0.0.1` |
| Porta | `55432` |
| Banco | `vrac_sintetico` |
| Esquema | `vrac_sintetico` |
| Usuário de consulta | `vrac_sintetico_reader` |
| Dados | Exclusivamente sintéticos |
| TLS do cliente | `verify-full`, com certificado local específico |

O comando informa o caminho de `pg_service.conf`, sem mostrar senhas. As credenciais
são novas e aleatórias e permanecem em um diretório temporário com acesso restrito,
fora do workspace e do Git. O diretório do cluster também fica ali. Não copiar esses
arquivos para o repositório. O certificado local dura 365 dias; ao expirar, precisa
ser renovado antes de reconectar, preservando a validação do certificado.

Para consultar com `psql`, configure o caminho **informado pelo comando** e use o serviço:

```powershell
$env:PGSERVICEFILE = '<caminho informado para pg_service.conf>'
.\.tools\postgres\pgsql\bin\psql.exe -X 'service=vrac_sintetico' -c 'SELECT * FROM vrac_sintetico.dataset_metadata;'
```

Para encerrar somente esse cluster, preservando a carga:

```powershell
.\.venv\Scripts\python.exe -m vrac.dev.postgres_runtime stop
```

## Conectar a aplicação à base sintética

Implementado em 30/10/2026, por solicitação de Matheus (D-025). A tela existente
consulta filtros, registros docentes e alocações por turma com a conta de leitura.
Não é preciso copiar senhas, configurar SQL Server ou inserir dados reais.

Preparação, na raiz do projeto:

```powershell
.\scripts\bootstrap.cmd --postgres
.\.venv\Scripts\python.exe -m vrac.dev.postgres_runtime start
.\.venv\Scripts\python.exe scripts/connect-synthetic-app.local.py
.\scripts\run-demo.cmd
```

O driver Psycopg é opcional, registrado no extra `postgres` e fixado em `uv.lock`.
O bootstrap prepara as dependências; os binários portáteis e a carga já descritos
neste guia precisam existir antes do comando de início do banco.
Na instalação local desta entrega, a preparação das projeções já foi executada.
O comando `connect-synthetic-app.local.py` pode ser repetido: ele instala quatro
views de leitura na fixture, sem recriar ou duplicar os registros.
Esse script e `03-app-views.sql` ficam locais/ignorados por conter mapeamento interno.
Os nomes genéricos das views são contratos da demonstração, não fontes institucionais.

O lançador define `VRAC_ENVIRONMENT=development`, `VRAC_DATA_MODE=synthetic` e
`VRAC_DEMO_SOURCE=postgres`. Na tela em <http://127.0.0.1:8501>, conferir
**Origem dos dados: PostgreSQL sintético**, selecionar filtros e clicar no botão.
O recorte inicial `SINT-A / 2026.2` apresenta 46 linhas docentes e 2 alocações;
essas linhas não representam contagem de docentes únicos. `SINT-VAZIO` cobre o
estado sem registros. A aplicação não lê configurações ou credenciais institucionais.

O leitor usa cinco arquivos SQL fixos em `sql/synthetic_demo/`, valores vinculados,
TLS `verify-full`, host/banco/conta restritos à fixture local, transação de leitura
com snapshot consistente, limite de 5.000 linhas por tabela e timeouts explícitos.
Não cria objetos ou modifica a base a partir da interface. Antes da leitura,
confere identidade sintética, versão, conta, TLS e transação somente leitura.
Se o banco, driver ou projeção estiver indisponível, apresenta erro sanitizado e
remove resultados anteriores. Nunca ativa a memória como alternativa automática.

Para iniciar deliberadamente a demonstração original sem PostgreSQL, usar
`.\scripts\run-demo.cmd --memory` ou `run-demo.ps1 -Source memory` em ambiente
que autorize scripts PowerShell. A variável `VRAC_DEMO_SOURCE` aceita somente
`memory` e `postgres`; o padrão do módulo de configuração permanece `memory` para
execuções offline, enquanto os lançadores escolhem `postgres` explicitamente.

Na projeção PostgreSQL, currículo e grupo de compartilhamento ficam `NULL` porque
a fonte não informa essas chaves. A lotação docente das alocações vem do período,
separada do departamento da disciplina. Vagas preenchidas não são alunos únicos.
Horas Reais por semestre/vínculo reaparecem nas linhas mensais e não devem ser
somadas. Nenhuma unidade semanal ou semestral é presumida a partir do tipo numérico.

## Verificações técnicas e limites

O início confere a carga, metadados sintéticos, relações essenciais da fixture,
cenários de deduplicação, zero/nulo e a conexão TLS da conta de leitura. Esta conta
tem `SELECT` nas tabelas, sem permissão de escrita ou criação no esquema; o padrão
de transação somente leitura é uma proteção adicional. Os comandos não usam a
configuração do SQL Server e não herdam variáveis de conexão PostgreSQL existentes.

Os tipos são os do modelo semântico, sem presumir o DDL físico institucional.
Não são criadas chaves ou equivalências institucionais por suposição. O manifesto
lista colunas sempre `NULL` e colunas calculadas documentadas. DAX, RLS, Power Query,
auxiliares e todas as regras do Power BI não foram convertidos integralmente.
Campos periféricos, financeiros e cálculos ainda não reproduzidos ficam ausentes;
essa ausência não deve ser interpretada como zero. As Horas Reais sintéticas são
geradas independentemente do detalhamento de disciplinas.

O banco está ligado às tabelas e filtros da demonstração existente. Novas análises,
gráficos e exportações continuam sujeitos ao incremento solicitado. Não é serviço
institucional: o diretório temporário pode ser removido pelo sistema; a carga pode
ser recriada pelos arquivos locais. Não há necessidade de nova validação analítica
de fórmulas já documentadas (D-022). Lacunas concretas de conversão serão tratadas
no resultado afetado quando cada análise for implementada.
