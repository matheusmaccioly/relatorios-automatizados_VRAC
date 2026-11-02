# Estado da entrega

Atualizado em 02/11/2026 (consolidação para commit local). **Seis roteiros acadêmicos implementados sobre dados sintéticos, com gráficos, tabelas, conferências e exportações.**
**Conexão e inventário institucionais: NÃO VALIDADOS.** SQL Server confirmado por Matheus.
Fontes físicas e aceite funcional da aplicação continuam pendentes; as fórmulas
documentadas não exigem nova validação analítica. Fases 3/4a/4b executáveis na base
sintética; fase 5 parcialmente implementada; fases 6/7 institucionais não iniciadas.
Fase 0 e ferramentas do Prompt 1 preparadas. Conteúdo do guia original preservado;
`AGENTS.md` atualizado com a exigência de branding institucional.

## Consolidação para commit local — 02/11/2026

Matheus solicitou o commit das alterações pendentes. O conjunto reúne os roteiros
R01–R06, conexão e ferramentas do PostgreSQL sintético, gráficos, exportações,
ajustes visuais já registrados, testes e documentação. Nenhuma mudança funcional
adicional foi introduzida nesta tarefa; somente este registro foi atualizado.

Verificações repetidas antes do commit: Ruff e formatação aprovados; suíte offline
com `--basetemp .cache/pytest-precommit-20261102`: **304 passaram, 1 integração
institucional excluída**. `git diff --check` aprovado. Exclusões conferidas para
documentação semântica interna, mapeamentos, receitas `.local.py`, caches, carga SQL,
bancos e exportações geradas. Credenciais e arquivos do cluster ficam fora do Git.

Comandos de verificação: `.\.venv\Scripts\python.exe -m ruff check .`,
`.\.venv\Scripts\python.exe -m ruff format --check .` e
`.\.venv\Scripts\python.exe -m pytest -m 'not integration' -q --basetemp .cache/pytest-precommit-20261102`.
Não repetidos testes com PostgreSQL ou SQL Server, conferência visual, instalação
ou implantação; o pedido atual é exclusivamente consolidar o trabalho em commit.
Nenhum serviço foi reiniciado e nenhum push ou publicação foi solicitado.

Sem novos riscos ou bloqueios para o commit local. Permanecem os limites e as
pendências institucionais descritos abaixo para Matheus/DSI/DBA/Talita, sem nova
exigência de validação das fórmulas documentadas e sem avanço de fase nesta tarefa.

## Seis roteiros acadêmicos na base sintética — 30/10/2026

Matheus solicitou implementar todas as análises documentadas e gerar os dados
fictícios necessários para avançar a aplicação (D-027). A autorização amplia o
escopo anterior da D-026, que era somente composição docente. O modo real continua
bloqueado; nenhum dado institucional foi extraído ou consultado.

| Roteiro | Entrega sintética |
|---|---|
| R01 | Composição do cadastro atual preservada, com resumo, gráfico, lista e CSVs; integra o pacote completo. Resultados antigos são removidos se o conteúdo do cadastro mudar |
| R02 | Geral e grupo QP configurável, classificação ausente, demais e participação; denominador preservado. O grupo é simulação explícita, não definição institucional |
| R03 | Presença semestral por pessoa, séries por quadro, detalhe mensal e cobertura; identidade opaca, lotação histórica, lotes/exclusões e calendário janeiro–julho reproduzidos |
| R04 | Cargas oficiais por vínculo/semestre, contratada, distribuições, semáforo literal e alocações separadas; diferença/razão somente em unidades sintéticas declaradas; zeros/nulos preservados |
| R05 | Dupla função, registros de função e comprovações administrativas separados; vigências e sobreposições de papéis distintos, sem inferir por gratificação e sem valores financeiros |
| R06 | Quatro séries acadêmicas por período/curso: MT/MC, bolsistas elegíveis, FR/TD e ingresso com a exceção documentada; variação sem percentual na base zero, ausência sem zero fictício |

A aba **Análises por período** permite carregar o snapshot e executar um roteiro
ou os seis em conjunto, para um departamento ou todos. Oferece filtros em tabela,
avisos, gráficos com fontes/cores dos tokens institucionais, tabelas equivalentes,
CSV por tabela, PNG por gráfico e ZIP completo com manifesto JSON. As saídas
identificam demonstração, filtros, unidades, fonte, versão do cálculo, horário e
hash do snapshot. CSV preserva precisão numérica e protege fórmulas, inclusive
prefixos após espaços. Dez conferências programadas descrevem qualidade/cobertura
sem decisões de pessoal. Resultados são removidos ao mudar filtros ou atualizar
dados; falha na origem não aciona memória.

Preparação da base: sete novas views analíticas e duas tabelas suplementares
para convenções dimensionais e **15 atos/vigências totalmente fictícios**, com
casos administrativos/não administrativos e papéis sucessivos/simultâneos. A carga
original de 13 fontes, 406 colunas e 3.909 registros foi preservada. O script é
repetível sem duplicar atos. As unidades da simulação não comprovam a dimensão
institucional de Horas Reais. QP continua sem definição institucional; a seleção
de quadros é exibida e exportada como exemplo configurável.

Arquivos desta tarefa:

- `src/vrac/analyses/academic_data.py`, `academic_fixture.py`, `academic.py`,
  `academic_quality.py`, `academic_export.py`: entradas tipadas, cenários em memória,
  cálculos puros, conferências fechadas e exportações.
- `src/vrac/academic_ui.py`, `ui.py`, `charts.py`, `demo_data.py`,
  `db/synthetic_postgres.py`: interface dos roteiros, filtros/snapshot, gráficos e
  leitor. Savepoints isolam indisponibilidade de fontes independentes; inclusive
  falha no cadastro docente não bloqueia histórico ou fontes acadêmicas.
- `src/vrac/analyses/export.py`: proteção adicional contra fórmulas e precisão
  numérica preservada nos CSVs existentes; `analyses/__main__.py` diferencia o
  catálogo institucional da demonstração já executável.
- Nove arquivos `sql/synthetic_demo/academic_*.sql` na lista fechada do leitor,
  sempre com parâmetros vinculados e limite de saída. A conta continua de leitura
  com TLS `verify-full`; não há SQL arbitrário na interface.
- `tests/test_academic_analyses.py`, `test_academic_ui.py`, `test_academic_reader.py`:
  cálculos, gráfico/ZIP, fluxos de tela e falhas independentes.
- `.gitignore`/`.dockerignore` e documentação: README, contexto, plano, catálogo,
  arquitetura, decisões, próximos passos, índice, documentação SQL, guia PostgreSQL,
  este estado e novo `docs/guides/ANALISES_SINTETICAS.md`.
- `scripts/prepare-academic-analyses.local.py` e o SQL de preparação em `.cache/`
  permanecem locais/ignorados por conterem mapeamento interno. Nenhum commit ou
  push solicitado; alterações anteriores preservadas.

Verificações executadas:

- Ruff e formatação aprovados. Suíte offline em
  `.cache/pytest-all-analyses-delivery`: **304 passaram, 1 integração institucional
  excluída**. Testes cobrem deduplicação, múltiplos vínculos/lotes/bolsas, calendário,
  ingresso futuro, dupla diplomação, FR/TD sem HF, zero/nulo/ausência, base zero,
  vigências, grupos incompletos, parâmetros, precisão, proteção de células,
  snapshot, filtros, erro sem fallback e falha isolada de fontes.
- Integração explícita com PostgreSQL sintético pela conta de leitura e Streamlit
  AppTest: seis roteiros em conjunto, filtros e limpeza de resultados, departamento
  vazio, métricas, gráficos e botões de exportação passaram. As quatro séries de
  todos os seis semestres coincidiram com consultas SQL de referência independentes;
  o total de Horas Reais coincidiu com a fonte dedicada.
- Pacote demonstrativo em `.cache/synthetic-postgres/vrac-analises-demonstracao.zip`:
  **36 arquivos — 27 CSVs, 7 PNGs, manifesto e instruções**. PNGs das séries de
  alunos e funções renderizados e inspecionados, com texto e identificação visíveis.
- Instância do projeto na porta 8501 reiniciada para carregar os novos roteiros;
  `/_stcore/health` retornou HTTP 200. Aplicação e PostgreSQL permanecem iniciados.
- `git diff --check` e exclusões locais conferidos. Sem nova dependência ou serviço.

Comandos na instalação já preparada:

```powershell
.\.venv\Scripts\python.exe -m vrac.dev.postgres_runtime start
.\.venv\Scripts\python.exe scripts/prepare-academic-analyses.local.py
.\scripts\run-demo.cmd
.\.venv\Scripts\python.exe -m pytest -m 'not integration' -q --basetemp .cache/pytest-all-analyses-delivery
```

Orientações para Talita no [guia de uso](guides/ANALISES_SINTETICAS.md). Não executados:
SQL Server/KAPPA, conciliação com registros institucionais, autenticação institucional,
homologação de segurança/visual/usabilidade, publicação ou implantação. Fase 5
permanece parcial: feedback persistido e aprovações operacionais não foram criados.

Riscos/limites específicos: QP institucional, equivalências de curso, unidade real
de carga e comprovação administrativa institucional não foram inventados. Nas
simulações, convenções e evidências são explicitamente fictícias. Campos ausentes
continuam ausentes; fontes opcionais indisponíveis afetam somente suas métricas.
O catálogo institucional mantém estados históricos pendentes sem bloquear a
demonstração. Não há bloqueio para uso local sintético; Matheus/Talita podem avaliar
o fluxo e pedir ajustes concretos. DSI/DBA ainda precisam prover fontes físicas,
conta/escopos, autenticação e infraestrutura antes do acesso real. Não é necessária
uma nova rodada de aprovação das fórmulas já documentadas (D-022).

## Fase 3 — composição docente (R01 e geral da R02) — 30/10/2026

A pedido de Matheus, com escopo escolhido por ele (somente composição docente) e
origem PostgreSQL sintética. Implementação iniciada após a outra sessão concluir a
conexão da D-025; suas alterações foram preservadas.

| Arquivo | Alteração |
|---|---|
| `src/vrac/analyses/faculty_overview.py` | Cálculo puro da R01: contagem distinta de matrículas (cartão/quadro), contagem de linhas por categoria, Horas Reais do semestre mais recente por matrícula (A-M-009/010), semáforo literal A-CC-007 com comparação sem diferenciar maiúsculas, filtros fechados, estados vazio/filtro vazio, avisos e texto descritivo |
| `src/vrac/analyses/faculty_overview_fixture.py` | Cenários em memória: pessoa com dois vínculos, quadro ausente, horas zero/nulas/sem registro, quadro reconhecido e não reconhecido pelo semáforo, departamento vazio |
| `sql/synthetic_demo/faculty_register.sql`, `faculty_real_hours.sql` | Consultas revisadas com departamento vinculado; CPF sai do banco somente como hash opaco para o aviso de múltiplos vínculos |
| `src/vrac/db/synthetic_postgres.py`, `src/vrac/demo_data.py` | Duas consultas novas na lista fechada; mesmo snapshot e conferência de identidade sintética; sem fallback para memória |
| `src/vrac/analyses/export.py` | CSV de resumo e de lista de conferência com identificação DEMONSTRAÇÃO, filtros, origem, unidade, avisos e proteção contra fórmulas |
| `src/vrac/charts.py` | Barras Matplotlib de série única em azul, fontes locais, sem legenda, tabela equivalente ao lado |
| `src/vrac/ui.py`, `src/vrac/branding.py` | Aba "Situação geral do departamento" antes dos registros de demonstração; cálculo só por ação explícita; resultado removido ao mudar filtro ou departamento |
| `tests/test_faculty_overview.py`, `tests/test_postgres_demo_reader.py`, `tests/test_ui.py` | Fidelidade às regras, bordas do semáforo, zero/nulo/ausente, agregações dos visuais, filtros, exportação, parâmetros vinculados, CPF não exposto, tela; testes de tela passam a localizar widgets por chave |

Lacunas registradas apenas no resultado afetado: (1) QP sem regra documentada — geral
calculado; QP, demais e participação bloqueados; (2) valores do filtro salvo de quadro
da página não constam do inventário — todos os quadros exibidos, com aviso; (3) os
quadros sintéticos `PROF PRINCIPAL/HORISTA/SUPLEMENTAR` não correspondem aos nomes do
semáforo (`PRINCIPAL`, `COMPLEMENTAR TEMPO INTEGRAL/PARCIAL`) e recebem "Sem regra
definida", reproduzindo o painel sem equivalência presumida; (4) seletores de Status
CH, centro, carga semanal e tipo de vínculo da página não foram reproduzidos nesta entrega.

Verificações: Ruff e formatação aprovados; suíte offline com `--basetemp` da sessão:
**280 passaram, 2 falharam (ACL NTFS em `test_private_output.py`, mesmas falhas de
ambiente já registradas), 1 integração excluída**. Execução real contra o PostgreSQL
sintético local pela conta de leitura: SINT-A 9, SINT-B 8, SINT-C 8 matrículas e
SINT-VAZIO sem resultado numérico. Capturas da tela nos modos PostgreSQL e memória
(servidor temporário 8517, encerrado). O servidor da porta 8501 não foi alterado e
precisa ser reiniciado para exibir a nova aba.

Não executados: SQL Server/KAPPA, conciliação com o painel real, avaliação de Talita,
homologação visual. Matrículas (4a) e carga horária (4b) não iniciadas.

## Aplicação conectada ao PostgreSQL sintético — 30/10/2026

Por solicitação de Matheus (D-025), a demonstração Streamlit consulta a base
`vrac_sintetico` em `127.0.0.1:55432` para carregar filtros, registros docentes e
alocações por turma. A instância em <http://127.0.0.1:8501> foi reiniciada com essa
origem explícita e seu endpoint de saúde retornou HTTP 200. O banco e a aplicação
permanecem iniciados localmente. Nenhum acesso institucional foi realizado.

Alterações desta tarefa:

- `src/vrac/db/synthetic_postgres.py`: conexão fixa à fixture com Psycopg, conta
  de leitura, TLS `verify-full`, timeouts, identidade sintética conferida e
  snapshot consistente. Consultas em lista fechada, com filtros vinculados e
  limite de 5.000 linhas por tabela.
- `sql/synthetic_demo/`: cinco consultas genéricas de identificação, filtros e
  registros. O mapeamento interno está em quatro views da base sintética, preparado
  por `scripts/connect-synthetic-app.local.py` e `03-app-views.sql`, locais e ignorados.
- `src/vrac/demo_data.py`, `settings.py` e `synthetic.py`: escolha explícita entre
  memória e PostgreSQL, opções vindas da fonte, origem e horário de consulta no
  resultado. `VRAC_DEMO_SOURCE` é a terceira variável pública de configuração.
- `src/vrac/ui.py`: origem PostgreSQL identificada na tela e na tabela de filtros;
  falhas removem resultados anteriores, sem fallback. Estado vazio por tabela e
  por recorte. Vagas preenchidas não são rotuladas como alunos/matrículas únicas;
  a unidade das horas do modelo não é presumida.
- `pyproject.toml`/`uv.lock`: extra opcional `postgres`, Psycopg e componente binário
  fixados em 3.3.6. `scripts/bootstrap.cmd/.ps1` aceitam a opção PostgreSQL;
  `scripts/run-demo.cmd/.ps1` iniciam essa origem por padrão. Memória permanece
  disponível por `--memory` ou `-Source memory`, sem ativação por erro de conexão.
- Testes do leitor em `tests/test_postgres_demo_reader.py`; testes de tela,
  configuração e proteção offline ampliados em `tests/test_ui.py`,
  `tests/test_foundation.py` e `tests/conftest.py`.
- `.gitignore`, `.dockerignore`, exemplo de configuração, README, guia da prévia,
  guia PostgreSQL, documentação SQL, contexto, plano, próximos passos, decisões e
  este estado atualizados. Alterações anteriores de branding e interface preservadas.

Verificações executadas: Ruff e formatação aprovados; suíte offline com
`--basetemp .cache/pytest-connected-postgres-final`: **243 passaram, 1 integração
institucional excluída**. O bloqueio offline inclui agora o driver PostgreSQL nativo.
Testes cobrem identidade da base/conta/TLS, parâmetros, filtros inválidos, limites,
zero/nulo, recorte vazio, tabela vazia, erro sanitizado, remoção de resultados
anteriores e ausência de fallback.

Teste explícito contra a base sintética com o leitor e Streamlit AppTest passou:
quatro departamentos e seis semestres provenientes do PostgreSQL; `SINT-A / 2026.2`
exibiu **46 linhas docentes e 2 alocações**; troca de filtro removeu a prévia;
`SINT-B` preservou horas ausentes e `SINT-VAZIO` mostrou ausência sem total zero.
Conta de leitura e consultas fixas usadas em todo esse fluxo. SQL de projeção
instalado somente no cluster sintético desta entrega. Exclusões locais e
`git diff --check` conferidos.

Comandos (base e projeções desta instalação já preparadas):

```powershell
.\scripts\bootstrap.cmd --postgres
.\.venv\Scripts\python.exe -m vrac.dev.postgres_runtime start
.\.venv\Scripts\python.exe scripts/connect-synthetic-app.local.py
.\scripts\run-demo.cmd
```

Instruções e alternativa sem PostgreSQL no
[guia de execução](operations/SYNTHETIC_POSTGRES.md). Testes institucionais,
homologação visual/funcional por Talita, novas análises, gráficos e exportações
não foram executados ou implementados nesta tarefa. Não houve avanço automático
das fases analíticas, commit, push ou publicação.

Limites: a prévia preserva linhas mensais/lotes e vínculos; não é contagem de
docentes distintos. Horas Reais semestrais por vínculo reaparecem nas linhas
mensais e não podem ser somadas. Currículo e chave do grupo de compartilhamento
ficam ausentes porque a fonte consultada não os fornece; nenhuma chave foi
inventada. A demonstração depende do cluster local e do certificado/credenciais
gerados fora do workspace. Sem bloqueios para uso sintético local; Matheus pode
seguir com a primeira análise solicitada. Nenhuma revalidação analítica foi
solicitada a Talita; pendências de acesso institucional da DSI/DBA permanecem
separadas e não bloqueiam esta demonstração.

## PostgreSQL sintético para desenvolvimento — 30/10/2026

A pedido de Matheus (D-023), gerada e carregada uma base exclusivamente sintética
com as 13 fontes listadas a partir da documentação semântica acadêmica: **406 colunas,
3.909 registros**, semente `20261030`, seis semestres entre 2024.1 e 2026.2,
24 pessoas docentes com 25 vínculos e 120 matrículas acadêmicas. Existe ainda uma
tabela de identificação sintética com versão e semente. Nenhum registro real foi
extraído e nenhuma conexão institucional foi executada.

PostgreSQL portátil **18.6**, obtido da EDB indicada pelo site oficial do PostgreSQL,
executando em `127.0.0.1:55432`; banco/esquema `vrac_sintetico`. Arquivo de origem e
SHA-256 registrados em `.tools/postgres/download.json` (ignorado). Conta de consulta
`vrac_sintetico_reader` com `SELECT`, sem escrita/criação; conexão conferida com TLS
e `verify-full`. Credenciais aleatórias, certificado e cluster ficam fora do
workspace, em diretório temporário restrito criado exclusivamente para esta base.
Não foi instalado serviço do Windows. O cluster permanece iniciado após os testes.

Arquivos desta tarefa: `src/vrac/dev/__init__.py`,
`src/vrac/dev/semantic_postgres.py`, `src/vrac/dev/postgres_runtime.py`,
`tests/test_synthetic_postgres.py`, `.gitignore`, `.dockerignore`,
`docs/operations/SYNTHETIC_POSTGRES.md`, índice, contexto, plano, próximos passos,
decisões e este estado. Receita `scripts/synthetic-postgres.local.py` e pacote
`.cache/synthetic-postgres/bundle-v1/` contêm metadados internos e foram mantidos
locais, ignorados por Git/Docker. Alterações anteriores de interface/branding e
documentação foram preservadas.

Verificações executadas:

- Ruff e formatação aprovados; suíte offline: **225 passaram, 1 integração
  institucional excluída**, incluindo 14 testes do novo gerador/executor.
- Duas gerações com a mesma semente produziram SQL idêntico; outra semente mudou
  os valores previstos. Nomes e tipos são extraídos do documento, sem DDL físico
  presumido ou execução de DAX.
- Banco carregado e comparado ao manifesto: contagens das 13 fontes e 406 colunas
  coincidem. Relações dos cenários, duplicidade, múltiplos lotes e zero/nulo conferidos.
- Conexão da conta de leitura e permissões conferidas. Reinício do cluster e nova
  execução do comando de início passaram, preservando os registros.
- Tentativas de repetir a carga sobre o esquema existente e de carregar no banco
  local `postgres` foram recusadas; contagens preservadas e nenhum esquema criado
  nesse outro banco. Corrigida a comparação de loopback para usar `host(inet)`;
  o cast textual inclui máscara de rede. Corrigida também a espera por pipes
  herdados por processos do servidor no Windows.
- `git diff --check`; exclusões da receita, SQL e manifesto conferidas.

Comandos na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe scripts/synthetic-postgres.local.py
.\.venv\Scripts\python.exe -m vrac.dev.postgres_runtime start
.\.venv\Scripts\python.exe -m vrac.dev.postgres_runtime stop
.\.venv\Scripts\python.exe -m pytest -m 'not integration' --basetemp .cache/pytest-postgres-complete -q
```

O pacote inicial já existe: para regenerar, escolher saída nova com `--output`,
conforme o [guia de execução](operations/SYNTHETIC_POSTGRES.md). Não executados
integração institucional, conexão da tela Streamlit a PostgreSQL, homologação
funcional/visual ou publicação. A base é a preparação solicitada para os próximos
incrementos; fases analíticas não foram iniciadas automaticamente.

Limites: colunas periféricas e cálculos não reproduzidos ficam `NULL`, listados no
manifesto; não são zero. RLS, Power Query, DAX e auxiliares não foram integralmente
convertidos. Não há chaves institucionais presumidas. O diretório temporário depende
da retenção local do Windows e pode ser recriado a partir da carga. Nenhuma nova
validação de regras foi solicitada a Talita. Matheus poderá usar a base no próximo
incremento; pendências de DSI/DBA para uso institucional permanecem separadas e não
bloqueiam o desenvolvimento sintético. Sem commit, push ou publicação.

## Base dos cálculos — 30/10/2026

Matheus orientou reproduzir os dashboards existentes com base na documentação já
disponível, sem outro processo de validação das regras. Decisão registrada como
D-022 e refletida no contexto, plano, catálogo e próximos passos. Exigências
históricas de reaprovação analítica ficam substituídas por essa orientação.
Nenhum cálculo, estado de contrato ou controle de acesso foi alterado.

Verificação documental: `git diff --check`. Suíte de aplicação e testes de banco
não executados nesta tarefa, que altera somente documentação. Nenhum comando de
execução novo. Sem avanço de fase ou publicação. Risco técnico remanescente:
lacunas concretas na reprodução e no mapeamento físico devem ser registradas por
resultado. Matheus/DSI/DBA mantêm as pendências de configuração e acesso seguro;
não há nova validação de fórmulas solicitada a Talita.

## Layout institucional da demonstração — 30/10/2026

Matheus relatou a tela sem logo, sem fontes e só com azul. Causa: o servidor aberto
na porta 8501 fora iniciado em 27/10, antes do branding, e não recarrega código
(`fileWatcherType none`). Com autorização dele, encerrados os processos antigos das
portas 8501 (27/10) e 8515 (28/10) e iniciada a demo atual por `run-demo.cmd` na 8501.

A pedido de Matheus, a tela ficou mais institucional com os recursos já no repositório:
- **D-021:** amarelo `#F1BA2A` e cinza `#869597` pelo hex impresso, escolha de Matheus,
  pendente de revisão institucional. Acrescentados a `tokens.toml`, ao tema
  (`yellowColor`, `grayColor`, cores categóricas de gráficos) e aos READMEs de branding.
- `src/vrac/ui.py`: cabeçalho com assinatura colorida, sobretítulo "PUC-Rio · VRAC",
  título "Análises acadêmicas" em Literata azul e faixa azul/ciano/amarela; blocos
  com contorno cinza e borda superior azul; rodapé com o nome da instituição.
- `src/vrac/branding.py`: estilos em um template único preenchido só pelos tokens;
  títulos de seção com marca amarela; aviso de demonstração em amarelo; erros com
  borda preta. Texto pequeno continua preto (azul e cinza não têm contraste suficiente).
  A faixa tricolor é composição de layout, não elemento de marca.

Ajuste posterior no mesmo dia: Matheus apontou baixa visibilidade do preto sobre o azul
no botão principal. Texto do botão passou a branco em negrito (APCA ~Lc 70 contra ~Lc 37
do preto; a razão WCAG 2 favorece o preto, mas subestima esse caso). Azul inalterado.

Fundo da página: Matheus escolheu `#F5F5F0` (D-024, fora da prancha oficial). Token
`colors.background` e `backgroundColor` do tema; cabeçalho com assinatura, avisos e
blocos em branco com contorno cinza. O corpo das tabelas usa o fundo do tema.

Verificações: Ruff e formatação aprovados; suíte offline com `--basetemp` da sessão:
**209 passaram, 2 falharam (ACL NTFS em `test_private_output.py`, mesmas falhas de
ambiente já registradas acima), 1 integração excluída**. Capturas via Chrome headless
em `127.0.0.1:8501` nos estados inicial e com dados. Demo atualizada permanece em
execução na 8501. Não houve homologação visual nem avaliação de Talita.

## Melhoria de layout da demonstração — 30/10/2026

A pedido de Matheus, reorganizada a tela sintética sem alterar dados, regras, filtros
ou estados. Nenhuma fase avançou; o tema continua aplicado e com revisão pendente.

- `src/vrac/ui.py`: cabeçalho com assinatura e título lado a lado; filtros e botão
  na mesma linha dentro de um bloco "Análises disponíveis"; resultados em bloco
  próprio com abas para as duas tabelas e contagem de **linhas** (não docentes únicos).
  Nulos exibidos como "ausente", distintos de zero (antes o Streamlit mostrava "None",
  contrariando a legenda "célula vazia"). Números com vírgula decimal, alinhados à direita.
- `src/vrac/branding.py`: CSS só com azul/ciano/preto dos tokens — faixa azul no topo,
  avisos com contorno azul (antes sem contraste com o fundo), títulos de seção azuis
  (o seletor anterior era sobreposto pelo tema) e abas com sublinhado ciano.
- `assets/branding/tokens.toml`: largura de exibição do logo 240 → 200 (valor de
  layout, não tamanho mínimo oficial; o arquivo original não foi alterado).
- `scripts/sync-branding.py` e `.streamlit/config.toml`: `toolbarMode = "minimal"`,
  removendo o botão "Deploy" do Streamlit.
- `tests/test_ui.py`: novo teste de "ausente" distinto de zero nas duas tabelas.

Verificações: Ruff e formatação aprovados; suíte offline com `--basetemp` no
diretório temporário da sessão: **209 passaram, 2 falharam, 1 integração excluída**.
As 2 falhas (`test_private_output.py`, ACL NTFS) ocorrem igualmente sem estas
alterações (conferido com `git stash`) e decorrem do sandbox do agente bloquear o
diretório temporário padrão; Matheus deve repetir `.\scripts\check.cmd` localmente.
Capturas locais via Chrome headless em `127.0.0.1:8517` (estado inicial e com dados);
serviço encerrado. Não houve revisão de Talita nem homologação visual institucional.

## Consolidação para commit local — 29/10/2026

A pedido de Matheus, reunidas as alterações pendentes: contratos dos seis roteiros,
aplicação dos materiais de branding, modelo KAPPA sem credenciais e documentação de
configuração/próximos passos. Materiais internos explicitamente ignorados permanecem
fora do versionamento. As alterações anteriores foram preservadas.
Extensões AI, PDF, PNG, JPG e TTF marcadas como binárias em `.gitattributes` para
preservar os recursos originais, sem conversão de finais de linha ou diff textual.

Verificações repetidas: `.\scripts\check.cmd` concluiu com código 0; **210 testes
passaram e 1 integração foi excluída**, com lock offline, Ruff e formatação aprovados.
Tema gerado comparado aos tokens e seis fontes web comparadas byte a byte aos
originais. `git diff --check` sem erros de whitespace. Não executados conexão real,
inventário, homologação funcional/visual ou implantação. Porta, schemas nominais,
autenticação, driver e revisão de somente leitura dependem de Matheus/DBA/DSI;
regras e referência docente continuam dependendo de Talita e fonte. Nenhuma fase
foi avançada e nenhum push ou publicação foi solicitado nesta tarefa.

## Registro das informações de conexão — 28/10/2026

Complemento documental: criado `docs/PROXIMOS_PASSOS.md` a pedido de Matheus, com
prioridades, responsáveis, perguntas para Talita, caso de referência e condições
para o Prompt 3. Link adicionado ao índice `docs/README.md`. Verificados links
locais e `git diff --check`; sem alteração executável, a suíte não foi repetida.
Nenhuma conexão, aprovação, avanço de fase, publicação, commit ou push realizados.

Complemento solicitado por Matheus: criado `config/database.kappa.example.toml`,
modelo sem credenciais com servidor, banco e confirmação de SQL Server preenchidos.
Os campos pendentes estão numerados; timeouts e limites usam os padrões do código,
sem expor ajustes desnecessários. `docs/operations/CONFIGURAR_KAPPA.md` explica
cópia externa, autenticação, os cinco campos de configuração, dados a pedir ao DBA/DSI
e o comando de diagnóstico. O roteiro técnico aponta para esse caminho simplificado.
O índice `docs/README.md` também oferece acesso direto ao novo guia.
Nenhuma configuração privada foi criada ou lida, nem houve conexão. O modelo segue
intencionalmente incompleto até receber porta, schemas, driver e autenticação e
completar a confirmação de escopo; a autorização declarada foi preservada.

Verificações deste complemento: sintaxe TOML e compatibilidade com `DatabaseConfig`
usando apenas substituições sintéticas em memória; bloqueio do modelo incompleto;
`git diff --check`. Não repetida a suíte de aplicação por não haver alteração de
código executável. Testes reais permanecem reservados ao operador. Sem commit ou push.

Matheus solicitou atualizar a documentação com SQL Server KAPPA, endereço informado
`139.82.9.6`, banco `PUC_OLAP` e criação de seu usuário. Declarou que os schemas
necessários à aplicação estão autorizados, mas ainda não dispõe de porta TCP nem
dos nomes exatos dos schemas. Esses itens foram registrados como detalhes técnicos
pendentes, sem desconsiderar a autorização declarada e sem presumir `dbo` ou porta.
Método de autenticação, driver e revisão administrativa de somente leitura seguem
pendentes. O login de banco não equivale ao mecanismo de acesso futuro da usuária.

Atualizados `operations/DATABASE_DISCOVERY.md`, `operations/DSI_REQUESTS.md`,
`PROJECT_CONTEXT.md`, `PLAN.md`, `DECISIONS.md` e este estado. O exemplo
`config/database.example.toml` permanece genérico e nenhuma configuração real foi
criada ou lida. Alterações anteriores preservadas; nenhuma mudança de código ou fase.

Verificação documental: `git diff --check`, sem erros de whitespace. Suíte offline
não repetida por se tratar apenas de documentação. Não executados diagnóstico,
inventário, conexão real, testes de banco, commit ou push. Os comandos de execução
pelo operador continuam no roteiro; a configuração exige porta e schemas explícitos
antes de executar. Matheus/DBA/DSI devem completar esses valores e confirmar
autenticação, driver, TLS e privilégios. As regras analíticas ainda dependem de Talita
e dos responsáveis pelas fontes; nenhum aceite foi inferido desta atualização.

## Aplicação dos materiais de identidade visual — 28/10/2026

A pedido de Matheus, integrados os materiais adicionados a `assets/branding/` à
demonstração existente. Nenhuma regra analítica, fonte real ou fase foi liberada.

| Arquivos | Alteração |
|---|---|
| `assets/branding/tokens.toml`, `src/vrac/branding.py` | Centralização de logo, cores, fontes e estilos |
| `scripts/sync-branding.py`, `.streamlit/config.toml` | Geração de tema nativo Streamlit e caminhos locais de fontes |
| `static/branding/*.ttf` | Seis cópias byte a byte das fontes originais, somente recursos públicos |
| `src/vrac/ui.py` | Assinatura horizontal original, tipografia, título e indicação de revisão pendente |
| `pyproject.toml` | Inclusão dos tokens e logo usados pelo módulo no wheel |
| READMEs de branding e projeto, arquitetura, contexto, plano, decisões e estado | Origem, aplicação, comandos e limitações |

Lida e renderizada a única página da prancha EMoD de 23-10-18, fornecida junto aos
brasões RGB. PNG selecionado inspecionado; todos os originais preservados. Não foi
fornecido manual completo de interface. Amarelo/cinza têm divergência RGB/hex e não
foram aplicados aos componentes; azul/ciano coincidem. Hierarquia tipográfica e
dimensões são propostas de layout, não regras homologadas. Nenhum favicon foi criado.

Comandos: `.\.venv\Scripts\python.exe scripts/sync-branding.py` para gerar tema;
`.\scripts\run-demo.cmd` para abrir o serviço local; `.\scripts\check.cmd` para
verificações offline. **210 testes passaram e 1 integração foi excluída**; lock,
Ruff e formatação aprovados. Conferidas igualdade tema/tokens, existência do logo
e seis cópias de fontes idênticas. Wheel construído offline: 40 arquivos, tokens e
logo incluídos, cache e documentos internos ausentes. PyMuPDF usado isoladamente
em `.cache/branding-tools`, sem alteração das dependências ou lock da aplicação.

Serviço temporário em `127.0.0.1:8515`: saúde e página inicial responderam HTTP 200;
Rethink Sans Regular e Literata Semibold também responderam 200. O serviço anterior
da porta 8501 não foi alterado; o serviço temporário 8515 foi encerrado ao concluir.
AppTest verificou filtros, vazio, bloqueio real e erro
de configuração com a nova apresentação. Computer Use interrompeu a revisão antes
da captura do navegador porque não conseguiu confirmar a URL atual; nenhuma revisão
visual da aplicação é declarada concluída.

Não executados: conexão real, homologação funcional/visual, exportações novas,
implantação, commit ou push. Matheus e responsável institucional devem revisar a
aplicação, confirmar amarelo/cinza, hierarquia, tamanhos mínimos, favicon e condições
de distribuição das fontes. Talita deve avaliar legibilidade e uso. Pendências de
fontes/chaves do DBA e de acesso da DSI permanecem; fases 3–7 não iniciadas.

## Implementação complementar do Prompt 2 — 28/10/2026

Usada a especificação encontrada em `docs/ROTEIROS_ANALISES_VRAC.local.md`; o caminho
singular sem sufixo informado na solicitação não existe. Preservadas as alterações
documentais e exclusões já presentes. Nenhum arquivo interno foi incluído no pacote.

- `config/analyses.yaml` e `catalog.py`: versão `phase2-workflows-v4`, associação
  fechada dos seis roteiros às três famílias e rejeição de associação incompatível.
- `contracts.py`: papéis separados de departamento histórico e distribuição,
  quadro/categoria, situação e entidades acadêmicas; percentual docente previsto
  para o contrato de participação, sem calcular ou aprovar regra de QP.
- `workflows.py`: contratos de solicitação e resultado por período/métrica,
  planejamento de dependências, 24 decisões pendentes com responsáveis, filtros
  fechados, proteção do denominador QP e estados independentes das quatro curvas.
  Sem SQL, conexão, cálculo de indicadores ou detalhe pessoal na implementação.
- `__main__.py`: CLI lista roteiros, dependências e impedimentos ao Prompt 3.
- `tests/test_workflows.py`: 28 testes de contratos e cenários sintéticos, incluindo
  bolsa bloqueada sem afetar outras curvas, períodos sobrepostos, filtro QP,
  departamento histórico, cobertura incompleta, base zero e ausência de fallback real.
- Atualizados catálogo documental, contexto, plano, decisões e este estado.

Comando de validação: `.\scripts\check.cmd` — **210 testes passaram, 1 integração
excluída**, lock offline, Ruff e formatação aprovados. CLI de conferência:
`.\.venv\Scripts\python.exe -m vrac.analyses`. A suíte anterior tinha 182 testes;
os novos casos validam contratos, não aprovação ou execução das 38 regras de aceite.

Não executados: testes reais, consultas, conciliação institucional, novas telas,
homologação funcional/visual, implantação, commit ou push. Matheus autorizou avanço
condicional ao Prompt 3; fonte, população, identidade, referência temporal, fórmula
e caso de comparação docente continuam sem aprovação. A fase 3 não foi iniciada.
Talita e fonte validam os conceitos e exemplo; DBA confirma chaves/fontes/cobertura;
Matheus registra evidências; DSI valida acesso e escopos. Branding permanece pendente.

## Roteiros detalhados das análises — 28/10/2026 (registro anterior)

A pedido de Matheus, preparada documentação funcional detalhada para traduzir as
análises indicadas nos dois painéis em roteiros do aplicativo. A entrega permanece
documental, dentro da fase 2. Nenhum cálculo, consulta de análise, tela, dependência
ou contrato executável foi alterado. Fases 3–7 continuam não iniciadas.

O arquivo interno `docs/ROTEIROS_ANALISES_VRAC.local.md` tem seis roteiros: situação
geral do departamento, geral e QP, histórico semestral, carga horária, dupla função
e funções administrativas, e o gráfico geral de alunos. Inclui filtros em tabela,
regras encontradas e propostas, sequência de uso, saídas, templates descritivos,
contratos lógicos, exportações propostas, 24 decisões pendentes e 38 casos de aceite
futuros. Casos descritos não são testes executados nem regras homologadas.

O inventário interno `docs/EVIDENCIAS_PAINEIS_VRAC.local.json` registra cinco páginas
e 59 visuais com consulta, incluindo seletores, IDs, títulos, campos, agregadores,
filtros resumidos e hashes dos PBIX. Inspeção estática local somente dos JSON de
`Report/definition/`; sem leitura do DataModel, conexões, credenciais ou registros.
As fórmulas vêm da referência semântica preexistente e foram cruzadas por nome com
os visuais; o DAX binário dos PBIX não foi reextraído nesta entrega.

Especificação e inventário ficam excluídos do Git e do contexto Docker, como as
demais referências internas. Não houve commit, push, envio a serviços externos ou
publicação. O catálogo empacotável permanece com três famílias e nove variantes.

| Arquivo alterado ou criado | Finalidade |
|---|---|
| `docs/ROTEIROS_ANALISES_VRAC.local.md` — local, ignorado | Especificação funcional detalhada para Talita e desenvolvimento |
| `docs/EVIDENCIAS_PAINEIS_VRAC.local.json` — local, ignorado | Rastreabilidade de páginas e visuais dos dois painéis |
| `.gitignore`, `.dockerignore` | Excluir os dois novos artefatos internos |
| `docs/ANALYSIS_CATALOG.md` | Relacionar roteiros documentais às famílias existentes, sem mudar runtime |
| `docs/PROJECT_CONTEXT.md`, `docs/PLAN.md` | Registrar escopo documental atual e preservar limites de fase |
| `docs/DECISIONS.md` | Registrar D-018, sem aprovação institucional presumida |
| `docs/README.md` | Apontar documentos locais e explicar indisponibilidade em outros clones |
| `docs/STATUS.md` | Registrar entrega, verificações, limites e validações necessárias |

### Verificações desta documentação

| Verificação executada | Resultado |
|---|---|
| Script Python inline via `.\.venv\Scripts\python.exe -` | Aprovado: UTF-8, cercas de código, seis roteiros, 24 decisões, 38 casos futuros, 18 links locais/âncoras, estrutura JSON, cinco páginas e 59 visuais conferidos nos PBIX |
| Hashes SHA-256 dos dois PBIX e da referência semântica | Conferidos; fontes preservadas e correspondentes ao inventário |
| Revisão paralela de docentes e alunos | Correspondências semânticas revisadas; regras legadas separadas de propostas |
| Revisão crítica independente | Corrigidos tratamento de QP com classificação incompleta e um link sem âncora; sem alteração do documento original |
| `git check-ignore -- docs/ROTEIROS_ANALISES_VRAC.local.md docs/EVIDENCIAS_PAINEIS_VRAC.local.json` | Ambos ignorados; exclusões Docker também conferidas |
| `git diff --check` | Aprovado, sem erros de whitespace |

Comando para abrir a documentação a partir da raiz:
`Invoke-Item .\docs\ROTEIROS_ANALISES_VRAC.local.md`.
Para validar a leitura do inventário:
`.\.venv\Scripts\python.exe -m json.tool .\docs\EVIDENCIAS_PAINEIS_VRAC.local.json > $null`.
Nenhum desses comandos consulta o banco ou executa análises.

**Não executados:** suíte da aplicação, DAX, Power Query, refresh, banco real,
conciliação numérica, RLS por usuário, homologação funcional/visual ou implantação.
Não houve mudança de comportamento executável que justificasse repetir a suíte.
Os 182 testes registrados na entrega anterior continuam evidência histórica.

**Riscos e bloqueios:** composição atual e presença histórica não são a mesma
população; QP sem classificação completa não permite participação conclusiva;
unidade e unicidade de Horas Reais permanecem pendentes; dupla função/gratificação
não comprovam cargo administrativo; séries acadêmicas têm populações distintas.
Não há fonte física, regra, acesso ou branding homologados por esta documentação.

**Validação necessária:** Talita e responsáveis pelas fontes aprovam população,
unidade, QP, calendário, quatro curvas acadêmicas e critérios/vigência de funções;
DBA confirma objetos, chaves, cardinalidade, cobertura e leitura autorizada; DSI
valida autenticação, escopos, TLS, cache e exportação; Matheus registra decisões,
casos sanitizados e a próxima fase autorizada. Matheus e responsável institucional
validam o branding antes da apresentação visual. As 24 decisões detalhadas ficam
no documento local; pendências bloqueiam apenas resultados dependentes.

## Preparação do commit local — 28/10/2026

A pedido de Matheus, reunidas as alterações pendentes de catálogo, contratos,
documentação, estrutura de branding e consulta SQL de referência para commit local.
Os arquivos internos explicitamente ignorados permanecem fora do versionamento.
Nenhuma consulta SQL foi executada e nenhuma fonte ou regra institucional foi aprovada
por este registro. Não houve avanço de fase ou publicação.

Verificações repetidas: `.\scripts\check.cmd` concluiu com código 0, lock offline,
Ruff e formatação aprovados; **182 testes passaram e 1 integração foi excluída**.
`git diff --check` não encontrou erros de whitespace. Não executados testes de banco,
homologação funcional ou visual. As validações de Matheus, DSI, DBA e Talita descritas
neste documento permanecem pendentes.

## Revisão da base das análises — 27/10/2026

Matheus forneceu o caminho local de `docs/ANALISE_MODELOS_SEMANTICOS_VRAC.md` e autorizou
seu uso nesta revisão. O documento original foi preservado; os registros de inspeção
abaixo continuam como histórico da extração anterior.

- `config/analyses.yaml`: versão `phase2-semantic-baseline-v3`, baseada em documento
  detalhado disponível na revisão, com quatro variantes docentes, quatro acadêmicas
  de matrículas e uma de Horas Reais. Todas sem seleção institucional ou fonte SQL aprovada.
- `config/semantic_model_sources.local.yaml`: mapeamento local de 12 tabelas e 399
  definições de colunas, nomes/tipos declarados, referências de medidas e papéis
  candidatos. Qualificação por modelo impede presumir que objetos homônimos são iguais.
  Não contém dados pessoais, conexão ou expressões executáveis e não é carregado pelo runtime.
- Documento detalhado e mapeamento local excluídos do Git e do contexto Docker,
  respeitando a restrição de publicação do próprio documento. O catálogo distribuível
  funciona sem esses arquivos. Nenhum commit ou push foi realizado nesta revisão.
- `catalog.py`, `contracts.py` e CLI: variantes tipadas e validação de referências,
  modelo, fonte lógica, unidade, base temporal e seleção com aprovação. Pessoas,
  matrículas funcionais e matrículas acadêmicas têm significados distintos. Mudança
  de variante ou de base temporal impede conciliação automática mesmo com números iguais.
- Revisadas população atual versus histórica, coortes/trajetória, calendário incluindo
  julho, desempates, filtros de bolsas, fontes dedicadas de horas, duplicação de linhas
  e limites de RLS. Calendário e permissões não foram implementados por inferência.
- Atualizados catálogo documental, contexto, plano, decisões, README e índice.
  Preservadas as mudanças anteriores de organização, branding e fases 1/2.

Verificações desta revisão: `.\scripts\check.cmd` aprovou lock offline, Ruff, formatação
e **182 testes; 1 teste de integração não selecionado**. A CLI
`.\.venv\Scripts\python.exe -m vrac.analyses` carregou as três análises sem consultar
fontes. Mapeamento local conferido contra os cabeçalhos de tabelas/colunas e âncoras
das medidas; hash do documento preservado:
`84bd9e833627c1e562e0018a9fad2bf806b509a723fc0172866cbcc5f39f7372`.
Wheel construído offline e conferido: 35 arquivos, catálogo incorporado idêntico ao
YAML de origem e nove variantes carregadas diretamente do pacote. Documento interno
e mapeamento local ausentes do wheel. `git check-ignore` confirmou as duas exclusões;
`git diff --check` não encontrou erros de whitespace.

Não executados: conexão real, Power Query/M, DAX, RLS por usuário, conciliação de números,
homologação funcional/visual ou implantação. DBA confirma origem física, chave e
cardinalidade; Talita escolhe população, referência temporal e critérios; Matheus/DSI
validam acesso. Sem essa confirmação, os adaptadores reais continuam bloqueados.

## Análise documental de modelo semântico — 27/10/2026

- A pedido de Matheus, realizada inspeção local, somente leitura, de um PBIX
  explicitamente indicado, para explicar estrutura, fórmulas e possibilidades de
  simplificação. A explicação foi entregue na conversa; o arquivo não foi alterado.
- Metadados, relacionamentos e expressões foram inspecionados sem atualizar fontes,
  conectar ao banco ou exportar registros pessoais. Nenhum conteúdo interno foi
  incluído em consultas externas ou copiado para o repositório.
- Usado interpretador temporário separado com PBIXRay, sem alterar dependências da
  aplicação. A listagem resumida do extrator omitia relacionamentos com tabelas
  calculadas; a inspeção da base de metadados embutida corrigiu essa limitação.
- Verificações executadas: leitura da estrutura ZIP, inventário de metadados e
  revisão estática de expressões e caminhos de filtro. Não executados: avaliação
  DAX, atualização, conciliação de totais, testes de RLS por usuário ou suíte da
  aplicação, pois não houve alteração de código.
- Regras encontradas no arquivo são evidência de implementação, sem aprovação
  institucional presumida. Talita e o responsável pelos dados devem validar
  população, identidade de pessoa/vínculo, períodos e critérios de carga; Matheus
  e DSI devem conferir propagação de acesso; DBA deve confirmar fontes e chaves.
- Nenhuma fase avançou, fonte física foi homologada ou publicação foi realizada.

### Complemento: documentação consolidada dos três modelos

- A pedido de Matheus, a inspeção foi ampliada aos dois PBIX adicionais indicados
  pelo usuário. Gerado um Markdown consolidado em pasta própria de Downloads,
  fora do repositório, com os três modelos, explicações, propostas, dicionário,
  relacionamentos, DAX, regras de acesso, páginas e propriedades semânticas.
- Conteúdo interno não foi incorporado ao Git. Identificadores individuais em
  fórmulas e nomes pessoais de papéis foram mascarados; literais textuais de RLS
  foram substituídos por marcadores estáveis no documento.
- Verificação estrutural: **aprovada** para cobertura de 1.841 colunas, 152
  relacionamentos e 333 medidas; 1.028 expressões DAX não vazias reproduzidas com
  os tratamentos documentados; links internos, cercas de código e UTF-8 conferidos.
  Contagens incluem estruturas automáticas de datas; não são números institucionais.
- Comandos de extração, complemento e geração com Python/PBIXRay 0.15.5 estão
  registrados no próprio artefato. Ambiente de inspeção separado; nenhuma mudança
  nas dependências da aplicação ou nos PBIX originais.
- Não executados: Power Query/M, avaliação DAX, atualização, banco institucional,
  conciliação de totais, testes de acesso por usuário, suíte da aplicação ou
  homologação visual. Somente documentação foi alterada no repositório.
- Pendências: Talita e responsáveis pelas fontes validam conceitos, exceções e
  períodos; Matheus/DSI validam acesso e vigência; DBA confirma fontes físicas,
  chaves e granularidades. As regras encontradas não foram homologadas.
- Projetos patrocinados e análises financeiras foram documentados como referência
  solicitada; continuam fora da implementação atual. Nenhuma fase avançou.

## Entrega do Prompt 2

- [Catálogo estruturado](../config/analyses.yaml) e [definições de negócio](ANALYSIS_CATALOG.md)
  para composição docente, evolução de matrículas e carga horária, nesta ordem.
  População, granularidade, unidade, chaves, parâmetros, filtros, fórmula descritiva,
  exceções, período, responsável, versões e comparação registrados como propostas.
- Fonte física não mapeada; cinco áreas de aprovação humana pendentes por análise:
  fonte, granularidade, cálculo, comparação e aceite funcional. O dicionário sanitizado
  da fase 1 permanece modelo não preenchido; nenhuma tabela ou coluna foi inventada.
- Contratos tipados de solicitação e resultado, entidades com papéis distintos,
  unidades, filtros efetivos, UUID, datas por origem, versões, avisos e estados.
  Nulo, zero, ausência de registros, não calculável e falha permanecem distintos.
- `blocked_result()` retorna motivos e dados vazios, sem consulta, cálculo ou fallback.
  Resultados reais válidos/parciais são recusados nesta fase, inclusive após mudar
  flags do catálogo. Não existe adaptador de análise real nem SQL de análise novo.
- Referências de comparação e equivalências de cursos com vigência, fonte e registro
  de aprovação; mapas sintéticos não se aplicam a modo real. Séries permanecem
  separadas diante de pendência, conflito, vigência incompleta ou cadeia não revisada.
- Contagens com igualdade exata, sem tolerância ajustável; horas dependem de critério
  explícito de arredondamento. Conferência de referência não aprova funcionalmente
  uma análise e não força resultados atuais a coincidir com uma origem antiga.
- Sete casos determinísticos: duplicidade, nulo, zero, ausência, semestre parcial,
  denominador zero e fontes com datas distintas. Expectativas de fixtures não são
  números institucionais ou aprovação de Talita.
- PyYAML 6.0.3 acrescentado e travado no `uv.lock`; 51 pacotes resolvidos para
  desenvolvimento. Catálogo incluído no wheel e carregado sem conexão ao banco.
- Reorganização e pasta de branding anteriores preservadas. Nenhuma alteração visual;
  materiais oficiais continuam pendentes para a futura interface da fase 3.

## Verificações executadas no Prompt 2

| Verificação | Resultado |
|---|---|
| `.\scripts\check.cmd` | Código 0; lock offline, Ruff e formatação aprovados; **161 testes passaram, 1 integração real excluída** |
| Novos testes da fase 2 | 44 casos cobrindo contratos, unidades, bloqueios, proveniência, igualdade de contagens, critério de horas, referências e equivalências |
| Leitura YAML | Lista fechada, prioridades e campos validados; tags executáveis, campos duplicados, escopo extra e aprovações incompletas recusados com mensagem sanitizada |
| Resultados parciais | Preservam nulos e períodos incompletos com aviso; resultado vazio ou incompleto não pode ser válido; métricas/origens ambíguas são recusadas |
| Casos sintéticos | Determinísticos e identificados; percentual com base zero não numérico; fixture não pode virar aceite funcional humano |
| Referências | Mesmo recorte/regra/origem; atualização desconhecida ou modificada bloqueia comparação automática; extração e atualização têm significados separados |
| `.\.venv\Scripts\python.exe -m vrac.analyses` | Código 0; três definições `pending`, cinco decisões pendentes por definição; nenhuma consulta ou cálculo executado |
| Wheel offline | Gerado e inspecionado: 35 arquivos; catálogo idêntico ao YAML do repositório e carregado pelo recurso empacotado; cache, ferramentas e configuração privada ausentes |

Não executados: conexão real, inventário real, cálculo de análises, conciliação com
referência de Talita, homologação funcional/visual, implantação ou execução de integração.
O guia permite esta preparação sem metadados aprovados; isso não conclui a validação
institucional da fase 1 nem autoriza avançar à fase 3 automaticamente.

## Arquivos do Prompt 2

| Grupo | Arquivos criados ou ajustados |
|---|---|
| Contratos e definições | `src/vrac/analyses/{__init__,__main__,contracts,catalog,references,courses,synthetic_cases}.py` |
| Catálogo e modelos | `config/analyses.yaml`, `config/reference_case.example.yaml`, `config/course_equivalences.example.yaml` |
| Dependências e distribuição | `pyproject.toml`, `uv.lock` |
| Testes | `tests/test_analysis_catalog.py`, `tests/test_analysis_contracts.py`, `tests/test_analysis_references.py` |
| Documentação | `docs/ANALYSIS_CATALOG.md`, `README.md`, índice, contexto, plano, arquitetura, decisões, prévia e este estado |

A lista curta de decisões para Talita e para os responsáveis pelos dados está no
[catálogo](ANALYSIS_CATALOG.md#decisões-curtas-para-validação-humana). Matheus deve
liberar somente material sanitizado autorizado e manter o mapa físico privado externo.

## Organização do repositório e branding — 27/10

- Documentação agrupada: prévia em `docs/guides/`, descoberta/dicionário/solicitações
  DSI em `docs/operations/` e guia original em `docs/references/`. O conteúdo do guia
  foi preservado e os links relativos foram ajustados.
- [Índice da documentação](README.md) e mapa do repositório no README principal,
  mantendo contexto, plano e estado nos caminhos estáveis de `docs/`.
- Criada [assets/branding/](../assets/branding/README.md), com pastas para logos,
  ícones, fontes, manuais e templates e um modelo documental de tokens de identidade.
- Branding PUC-Rio obrigatório registrado nas instruções, contexto, plano,
  arquitetura e decisões. Nenhum logo, cor, fonte ou variante oficial foi presumido.
- Matheus deve adicionar os materiais oficiais e identificar o responsável
  institucional que validará a aplicação visual. O tema atual permanece provisório;
  o modelo de tokens não é carregado pela aplicação e a interface não foi redesenhada.
- Esta manutenção altera organização e documentação; código, SQL executável,
  dependências e comandos de execução permanecem nos mesmos caminhos.

Verificações desta manutenção: links locais, sintaxe TOML, integridade do guia e diff.
A suíte de aplicação não foi repetida, pois o comportamento executável não foi alterado;
os 117 testes da fase 1 continuam como registro histórico, não como nova execução.

## Entrega da fase 1

- Extra opcional `sqlserver`: SQLAlchemy 2.1.6 e pyodbc 5.3.0 no lock; 50 pacotes
  resolvidos no ambiente de desenvolvimento. Instalar bibliotecas não confirma SGBD.
- Configuração externa explícita em `dbconfig.toml`, sem busca de credenciais ou
  leitura automática de `.env`. Endpoint, porta, banco, schemas, driver e autenticação
  precisam ser informados pelo operador; confirmações de SGBD e escopo são obrigatórias.
- CLI e atalhos manuais `diagnose-db.cmd`/`inventory-db.cmd`. Sem `--execute`, não
  há leitura da configuração, importação do adaptador ou tentativa de conexão.
- Adaptador lazy com SQLAlchemy/pyodbc, TLS e certificado validados, escape ODBC,
  timeout de login e consulta, descarte de recursos e mensagens fixas de erro.
  Logs exclusivos do engine/pool impedem emissão de erros brutos durante limpeza.
- Prova `SELECT 1` em arquivo revisado e quatro consultas fixas de catálogo,
  limitadas ao banco e schemas aprovados, com parâmetros vinculados e truncamento.
  Visibilidade é sempre desconhecida; ausência de metadados não significa inexistência.
- Saídas externas em subpasta UUID nova, protegida antes da consulta: DACL NTFS do
  usuário no Windows; diretório 0700 e arquivo 0600 no POSIX. Nenhum nome físico no console.
- Modelos agregados de qualidade/cardinalidade desabilitados, sem renderização ou
  execução pela CLI; revisão de objetos, filtros e custo permanece obrigatória.
- [Roteiro de execução](operations/DATABASE_DISCOVERY.md), revisão de privilégios pelo DBA e
  [dicionário sanitizado](operations/SANITIZED_DATA_DICTIONARY.md) com material exato para a fase 2.

## Verificações executadas na fase 1

| Verificação | Resultado |
|---|---|
| `.\scripts\bootstrap.cmd --sqlserver` | Código 0; instalação opcional conforme lock, sem alterar política de execução ou driver do sistema |
| `.\scripts\check.cmd` | Código 0; lock offline, Ruff e formatação aprovados; **117 testes passaram, 1 integração real excluída** |
| Configuração/conexão por mocks | Validação estrita, confirmações, caminhos externos, timeouts, escape ODBC, TLS, fechamento e descarte em falhas |
| Erros e logs de limpeza | Categorias sanitizadas; teste de NullPool real com DBAPI fictícia confirma que falhas de reset/close não expõem mensagem bruta |
| Inventário por mocks e compilação MSSQL | Escopos, TOP/IN vinculados, limite de consultas, truncamento, cobertura desconhecida, relações/tipos externos omitidos e resultados parciais |
| CLI por mocks | Ajuda e bloqueio sem opt-in, autorização antes de dados, saída protegida antes do banco e mensagens sem caminhos/SQL/identidade |
| Saída privada em arquivos temporários sintéticos | Proteção NTFS executada neste Windows, gravação exclusiva, recusa de sobrescrita e interrupção antes de dados quando ACL falha |
| Regressão da demonstração | Filtros, vazio, configuração inválida e modo real bloqueado continuam cobertos; timeout do AppTest ajustado para 15 s na inicialização local |
| Driver nativo na suíte padrão | `pyodbc.connect`, `pyodbc.drivers`, `Engine.connect` e rede bloqueados; testes usam somente mocks/DBAPI fictícia |
| CLI instalada e atalhos `--help` | Código 0; nenhum arquivo privado ou banco acessado |
| Wheel offline | Gerado e inspecionado: 27 arquivos, cinco consultas fixas incluídas; ferramentas locais, cache e configuração privada ausentes |
| Instalação base isolada sem extra | `uv sync --locked --offline --no-dev --no-editable`: 42 pacotes; CLI e SQL empacotado verificados sem SQLAlchemy/pyodbc |
| Exclusões e diff | Configuração real, saídas e cache ignorados; exemplos/código versionáveis; `git diff --check` sem erros |
| Bootstrap `.ps1` alterado | Sintaxe conferida pelo parser; execução não feita devido à política existente |

A primeira tentativa auxiliar de instalar o wheel offline por resolução aberta de `uv pip`
não encontrou metadados de índice no cache. A instalação base foi então conferida usando
o lock com `uv sync --locked --offline`, sem liberar rede ou alterar dependências.

Não foram executados: leitura de configuração real, enumeração de drivers reais,
conexão institucional, inventário real, consultas de qualidade, integração real,
revisão de privilégios no banco, homologação DSI/Talita ou implantação. O teste de
integração marcado exige seleção explícita, `--run-db-integration` e `--db-config`
externo; permanece reservado ao operador fora da sessão do agente.

## Arquivos da fase 1

| Grupo | Arquivos criados ou ajustados |
|---|---|
| Descoberta | `src/vrac/db/{__init__,__main__,config,errors,connection,diagnostic,inventory,private_io,cli}.py` |
| SQL revisado | `sql/diagnostics/connection_probe.sql`, quatro arquivos de `sql/catalog/`, três templates de `sql/quality/` e `sql/README.md` |
| Configuração | `config/database.example.toml`, `config/quality_checks.example.toml`, `pyproject.toml`, `uv.lock`, `.gitignore`, `.dockerignore` |
| Comandos | `scripts/diagnose-db.cmd`, `scripts/inventory-db.cmd`, `scripts/bootstrap.cmd`, `scripts/bootstrap.ps1`, `scripts/check.cmd` e `scripts/check.ps1` |
| Testes | `tests/test_db_{cli,config,connection,integration,inventory}.py`, `tests/test_private_output.py`, `tests/conftest.py`, `tests/test_ui.py` |
| Documentação | `README.md`, `docs/operations/DATABASE_DISCOVERY.md`, `docs/operations/SANITIZED_DATA_DICTIONARY.md`, contexto, plano, arquitetura, decisões e este estado |

## Fundação preparada na fase 0 — registro de 26/10

- Contexto, plano por fases, arquitetura, decisões e solicitações para DSI/DBA.
- Python 3.12.15 gerenciado em `.tools/python`, uv 0.13.5 em `.tools/uv` e `.venv` local.
- `pyproject.toml` e `uv.lock`: 48 pacotes resolvidos/instalados, incluindo o projeto.
  Versões principais: Streamlit 1.66.1, pandas 3.1.0, Matplotlib 3.11.2,
  pytest 9.1.1 e Ruff 0.17.2. Backend de construção Hatchling 1.32.4 fixado.
- Configuração pública estrita; demonstração sintética como padrão e dados reais sempre negados.
- Exemplos determinísticos com docentes repetidos por mês/vínculo, ausência, zero,
  período vazio, compartilhamento, classificação ausente e atuação interdepartamental.
- Tela em português, marca DEMONSTRAÇÃO, ação explícita, filtros em tabela e remoção
  da prévia quando a seleção muda. Nenhum cálculo institucional está implementado.
- Exclusões Git/Docker e convenções de edição; nenhum segredo ou dado institucional
  foi necessário para construir ou testar esta entrega.

## Verificações da fase 0 — registro de 26/10

| Verificação | Resultado |
|---|---|
| Instalação inicial com `.venv` inexistente | Python baixado localmente e 48 pacotes instalados pelo lock, com HTTPS e validação normal de certificados |
| Integridade do executável uv baixado | SHA256 do arquivo comparado com o hash fixado do release oficial |
| `.\scripts\bootstrap.cmd` após a instalação inicial | Código 0; Python existente reconhecido; 48 pacotes conferidos por `uv sync --locked` |
| `.\scripts\check.cmd` | Código 0; lock conferido offline, estilo e formatação aprovados; **20 testes passaram** |
| Configuração e autorização | Padrões seguros, lista pública de variáveis, configuração inválida sanitizada e acesso real negado nos três ambientes |
| Dados e interface via AppTest | Determinismo, cenários extremos, ausência distinta de zero, seleção fechada, ação explícita, troca de filtros e modo real bloqueado |
| Isolamento da suíte | Conexões normais bloqueadas, inclusive loopback; somente IPC interno de `socketpair` permitido para asyncio no Windows |
| `.\scripts\run-demo.cmd` | Serviço iniciou somente em `127.0.0.1:8501`, com telemetria desativada e sem abrir navegador |
| Saúde e página inicial do serviço local | `/_stcore/health`: HTTP 200, `ok`; `/`: HTTP 200 |
| Exclusões Git | Credenciais exemplificativas, ambientes, cache e dados privados ignorados; configuração de exemplo e código continuam versionáveis |
| Sintaxe dos scripts `.ps1` | Parser PowerShell aprovou; execução bloqueada pela política existente do Windows |

A primeira instalação usou comandos diretos revisados, pois este Windows não executa
`.ps1`. Os comandos `.cmd` são a interface de uso principal; não alteram ExecutionPolicy,
PATH, perfil ou registro do Windows. A demonstração foi iniciada somente para conferência
local, sem publicação ou acesso institucional.

## Limites e verificações não executadas

- Bootstrap completo partindo também de `.tools` vazia pela implementação `.cmd` ainda
  não foi repetido; a instalação inicial fez download com hash validado e criou `.venv`
  limpa, e a execução posterior do launcher foi verificada. O fluxo de download inclui
  também comparação com o `.sha256` oficial.
- Windows ARM64 e ambiente do servidor não foram testados; suporte previsto precisa
  ser conferido na plataforma efetivamente aprovada.
- Revisão visual em navegador e avaliação de usabilidade por Talita ainda não realizadas;
  os testes de interface executados foram automatizados via AppTest. Em 27/10, a prévia
  local respondeu HTTP 200, mas o Computer Use interrompeu a revisão visual por falta
  de suporte à política de URLs no navegador Windows atual. Roteiro em [PREVIEW.md](guides/PREVIEW.md).
- Sem conexão ao banco, credenciais, inventário, consultas reais, conciliação funcional,
  autenticação institucional, teste de segurança em homologação ou implantação.
- SQL Server permanece hipótese. Em 27/10, Matheus autorizou o envio ao remoto GitHub
  configurado; a API confirmou `matheusmaccioly/relatorios-automatizados_VRAC` como privado.
  Esse envio de código e dados sintéticos não representa implantação do aplicativo
  nem autorização para compartilhar fontes ou metadados institucionais.

## Validações externas e próximo incremento

| Responsável | Pendência |
|---|---|
| Matheus | Confirmar repositório privado/autorizado; executar diagnóstico/inventário fora da sessão do agente; revisar e liberar somente material sanitizado |
| DSI | Servidor/plataforma, rede, HTTPS, login institucional, autorização, segredos, retenção e operação |
| DBA | SGBD, autenticação, fontes e escopos aprovados, conta técnica de leitura e limites de consulta |
| Talita | Avaliar a demonstração e, antes dos cálculos reais, aprovar definições e caso de referência da composição docente |

Próximos passos: confirmar SGBD e escopos com DSI/DBA e executar manualmente as ferramentas
da fase 1, fora da sessão do agente; obter o dicionário sanitizado e o aceite humano das
definições e da referência de composição docente antes da implementação real.
A lista detalhada está em [DSI_REQUESTS.md](operations/DSI_REQUESTS.md). Nenhuma pendência foi
tratada como aprovação nem exige modificar o cálculo oficial para avançar.

## Arquivos da fundação — registro de 26/10

| Grupo | Arquivos |
|---|---|
| Instruções e setup | `AGENTS.md`, `README.md`, `pyproject.toml`, `uv.lock`, `.python-version`, `.editorconfig`, `.gitattributes`, `.gitignore`, `.dockerignore`, `.streamlit/config.toml` |
| Aplicação | `app.py`, `src/vrac/__init__.py`, `settings.py`, `authorization.py`, `synthetic.py`, `ui.py` no mesmo pacote |
| Configuração e SQL | `config/settings.example.toml`, `sql/README.md` |
| Comandos Windows | `scripts/bootstrap.cmd`, `check.cmd`, `run-demo.cmd`; alternativas `bootstrap.ps1`, `check.ps1`, `run-demo.ps1` e `uv-env.ps1` na mesma pasta |
| Testes | `tests/conftest.py`, `test_foundation.py`, `test_ui.py`, `test_offline.py` |
| Documentação | `docs/PROJECT_CONTEXT.md`, `PLAN.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `DSI_REQUESTS.md`, `STATUS.md` |

O arquivo `docs/references/Guia_Desenvolvimento_VRAC_Codex.md` já existia e foi mantido sem alterações.
