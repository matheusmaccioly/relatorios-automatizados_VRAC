# PoC de análises acadêmicas da VRAC

Aplicação interna para apoiar Talita nas análises de docentes, matrículas e carga
horária. **Os seis roteiros documentados estão disponíveis em demonstração local
exclusivamente sintética**, com PostgreSQL, filtros, tabelas, gráficos, conferências
programadas e exportações CSV/PNG/ZIP. Não há dependência de LLM ou Power BI.
O modo institucional permanece bloqueado; SQL Server foi confirmado por Matheus,
mas conexão e inventário institucionais não foram executados pelo agente.

Para usar todos os roteiros, abrir a aba **Análises por período**, escolher o
departamento, **Carregar ou atualizar dados** e **Calcular análises selecionadas**.
O [guia das análises sintéticas](docs/guides/ANALISES_SINTETICAS.md) explica filtros,
regras, simulações explícitas e arquivos exportados.

O [guia original](docs/references/Guia_Desenvolvimento_VRAC_Codex.md) foi preservado. As instruções
permanentes estão em [AGENTS.md](AGENTS.md) e o plano em [docs/PLAN.md](docs/PLAN.md).

## Organização do repositório

```text
assets/branding/    Materiais oficiais e referências de identidade visual da PUC-Rio
config/            Exemplos de configuração sem valores reais
docs/              Contexto, plano, arquitetura, decisões e estado do projeto
  guides/          Roteiros de uso e conferência da prévia
  operations/      Descoberta do banco, dicionário sanitizado e solicitações à DSI
  references/      Guia original de desenvolvimento
scripts/           Preparação, verificações e execução no Windows
sql/               Consultas revisadas e modelos de qualidade desabilitados
src/vrac/          Código da aplicação e ferramentas de descoberta
tests/             Testes offline e integração manual separada
app.py             Entrada da demonstração Streamlit
```

O [índice da documentação](docs/README.md) reúne os roteiros e referências do projeto.

## Branding da PUC-Rio

Todo o sistema deve seguir a identidade institucional, inclusive telas, gráficos,
tabelas e futuras exportações. Adicione os materiais oficiais em
[assets/branding/](assets/branding/README.md): logos, ícones, fontes, manuais, templates
e a paleta registrada no modelo de tokens.

Os materiais recebidos em 28/10/2026 já foram aplicados à demonstração: assinatura
horizontal RGB, Rethink Sans no corpo e Literata nos títulos, com fontes locais.
O tema é gerado a partir de `assets/branding/tokens.toml`; após alterar os tokens,
execute `.\.venv\Scripts\python.exe scripts/sync-branding.py` e reinicie o app.
A revisão institucional e a conferência no navegador continuam pendentes.
Consulte as divergências da paleta em [guidelines](assets/branding/guidelines/README.md).

## Preparar no Windows

PowerShell 5.1 ou superior, Windows x64/ARM64 e acesso HTTPS aos distribuidores oficiais
são necessários para a primeira instalação. Não é necessário Python previamente instalado.

```powershell
.\scripts\bootstrap.cmd --postgres
.\scripts\check.cmd
.\scripts\run-demo.cmd
```

O bootstrap instala ferramentas apenas em `.tools/`, dependências em `.venv/` e cache
em `.cache/`, sem mudar o PATH ou o perfil do usuário. O `uv.lock` fixa as dependências
transitivas; `uv sync --locked` rejeita divergências. Após instalar, os testes funcionam
offline. Os comandos `.cmd` funcionam sem executar arquivos `.ps1`; esse Windows bloqueia
scripts PowerShell. As alternativas `.ps1` ficam disponíveis para ambientes que já autorizem
sua execução. Nenhum comando altera a política de execução ou desativa TLS. Se a política
institucional impedir downloads ou comandos batch, solicitar a forma aprovada pela DSI.

A demonstração fica em <http://127.0.0.1:8501>; `Ctrl+C` encerra o processo.
O [roteiro da prévia](docs/guides/PREVIEW.md) orienta a conferência da tela e explica o que mudou no Prompt 1.
O comando de demonstração usa o PostgreSQL sintético local. Sua preparação está no
[guia da base sintética](docs/operations/SYNTHETIC_POSTGRES.md), incluindo as projeções
de leitura da aplicação. Com a base já preparada, iniciá-la antes da tela:

```powershell
.\.venv\Scripts\python.exe -m vrac.dev.postgres_runtime start
.\scripts\run-demo.cmd
```

Use `SINT-A / 2026.2` para os exemplos e `SINT-VAZIO` para o caso sem registros.
Trocar um filtro remove a prévia anterior até clicar novamente em **Mostrar dados de demonstração**.
Não existem cálculos institucionais, exportações ou login simulado nesta fase.
Para usar explicitamente os exemplos originais sem PostgreSQL, executar
`.\scripts\run-demo.cmd --memory`. Essa opção permite conferir a tela em uma
instalação sem os materiais locais do modelo; falhas do banco nunca a ativam.

## Diagnóstico e inventário — Prompt 1

O [roteiro de descoberta](docs/operations/DATABASE_DISCOVERY.md) descreve configuração privada externa,
aprovações do DBA/DSI, instalação opcional e execução manual fora da sessão do agente.
O extra prepara o adaptador condicional SQL Server; não instala driver ODBC nem confirma SGBD:

```powershell
.\scripts\bootstrap.cmd --sqlserver
.\scripts\diagnose-db.cmd --help
.\scripts\inventory-db.cmd --help
.\scripts\check.cmd
```

Sem `--execute`, os comandos não leem configuração nem abrem conexão. Configuração exige
arquivo `dbconfig.toml` absoluto, fora do workspace, e confirmações explícitas de SGBD e
escopo. Saídas ficam em uma nova pasta privada por execução, também fora do workspace.
Não inserir credenciais nos exemplos versionados, no chat ou em argumentos de comando.

O inventário usa consultas fixas de metadados, por schema, com limites e avisos de cobertura.
As consultas de qualidade/cardinalidade permanecem como templates desabilitados. Matheus
deve fornecer somente o [dicionário sanitizado autorizado](docs/operations/SANITIZED_DATA_DICTIONARY.md)
para a fase seguinte. A demonstração continua negando acesso a dados reais.

## Catálogo e contratos — Prompt 2

A base foi revista com a documentação semântica fornecida: nove variantes para as três
análises distinguem pessoas, matrículas funcionais/acadêmicas, referências temporais
e Horas Reais. Nomes de tabelas/colunas ficam em mapeamento interno local excluído do
Git e do pacote. Modelos semânticos não comprovam fontes SQL; seleção institucional,
origem física e regras continuam pendentes. Detalhes no catálogo abaixo.

O [catálogo de análises](docs/ANALYSIS_CATALOG.md) registra as propostas de composição
docente, evolução de matrículas e carga horária, nesta ordem. As definições ficam em
[config/analyses.yaml](config/analyses.yaml), com fonte física não mapeada e cinco áreas
de decisão humana pendentes por análise.

```powershell
.\.venv\Scripts\python.exe -m vrac.analyses
```

Esse comando apenas confere as definições, sem consultar fontes ou calcular indicadores.
Contratos tipados preservam unidades, filtros, datas e situações do resultado; casos
sintéticos testam os limites. Modelos de referência e de equivalência de cursos ficam
em `config/`. Adaptadores reais de análises estão bloqueados. A tela da demonstração
permanece na fundação; sua evolução faz parte da fase 3, com regras e branding aprovados.

## Configuração e limites

Somente `VRAC_ENVIRONMENT` (`development`, `test`, `production`) e `VRAC_DATA_MODE`
(`synthetic`, `real`) são lidas. O padrão é `development` + `synthetic`.
`run-demo.cmd` e `run-demo.ps1` selecionam explicitamente esses valores para iniciar a demonstração local.
O exemplo [config/settings.example.toml](config/settings.example.toml) é documental,
sem leitura automática de arquivos. Modo real é negado antes de carregar dados;
configuração inválida gera erro e nunca ativa uma demonstração como alternativa.

Para verificar o bloqueio manualmente, em uma sessão separada:

```powershell
$env:VRAC_ENVIRONMENT = 'development'
$env:VRAC_DATA_MODE = 'real'
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Não colocar credenciais ou dados institucionais no workspace, `.env`, chat ou Git.
Arquivos de ignore evitam versionamento/acondicionamento acidental; não impedem a leitura
pelo agente. Fontes, regras, acesso real e publicação dependem das validações descritas
em [docs/DSI_REQUESTS.md](docs/operations/DSI_REQUESTS.md).

## Desenvolvimento e continuidade

O pacote em `src/vrac/` separa configuração, autorização, dados fictícios e interface.
O pacote `src/vrac/db/` contém ferramentas de descoberta e o leitor restrito da
fixture PostgreSQL. `analyses/` contém os cálculos puros, conferências e exportações;
`academic_ui.py` apresenta os roteiros e `charts.py` aplica a identidade aos gráficos.

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\python.exe -m pytest
```

Consulte [docs/STATUS.md](docs/STATUS.md) para verificações efetivamente executadas,
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) para a arquitetura e
[docs/PLAN.md](docs/PLAN.md) para os próximos incrementos. Repositório privado/autorizado,
infraestrutura do servidor e login institucional ainda precisam de confirmação humana.
Não há CI externa configurada ou publicação automática.
