# Estado da entrega

## Conexão sintética indisponível na demonstração — 03/11/2026

A tentativa orientada de iniciar a aplicação na porta 8516 recebeu relato de
“acesso negado”; não havia processo ouvindo nessa porta na verificação posterior.
Matheus informou depois que o navegador mostrou `ERR_CONNECTION_REFUSED`: o
serviço não estava ouvindo. Preparado `scripts/run-demo-8516.cmd` para iniciar a
demonstração pelo ambiente do próprio desenvolvedor, sem depender da política de
scripts PowerShell; execução e conexão pela interface ainda precisam de confirmação.
Nenhuma permissão foi alterada.

A aplicação na porta 8515 informou falha ao consultar o PostgreSQL sintético.
Observado um processo `postgres` ouvindo em `127.0.0.1:55432` e o driver
`psycopg` disponível no ambiente da aplicação. Esses indícios não confirmam
identidade do banco, certificado, autenticação ou consulta bem-sucedida. Matheus
executou a verificação de presença: certificado e arquivo de autenticação estão
presentes; a existência não comprova validade ou acesso. Preparado diagnóstico
manual sanitizado `python -m vrac.dev.synthetic_connection_diagnostic --execute`,
que usa a conexão sintética fixa de leitura e não imprime exceções, credenciais,
caminhos nem dados acadêmicos. Matheus executou o comando e informou
`CONEXAO_E_OPCOES_OK`: conexão, identidade sintética e opções foram conferidas no
processo dele; a falha anterior da aplicação na 8515 ainda requer verificação no
contexto em que ela foi iniciada.
Cinco testes offline e Ruff dos arquivos novos passaram; sem `--execute`, o
diagnóstico não conecta. O agente não acessou arquivos privados nem executou a
conexão, alteração de TLS, reinício ou reconstrução.

## Demonstração local em porta alternativa — 03/11/2026

A porta 8501 já tinha um serviço Streamlit com resposta de saúde `ok`; sua
identidade não foi confirmada nem o processo interrompido. Iniciada a demonstração
atual em `127.0.0.1:8515` com `scripts/run-demo.ps1 -Port 8515`; endpoint de saúde
retornou `ok`. Essa verificação não confirma conexão PostgreSQL, conteúdo da
interface ou conciliação de resultados. Nenhum teste de software, consulta a banco,
acesso institucional ou publicação foi realizado nesta operação.

## Prompt 5 · modos de conferência sintéticos — 03/11/2026

Implementado incremento experimental de modos para E01: habilitação explícita,
aprovação ou recusa, execução automática limitada, estados, vínculo de identidade
simulada/análise/filtros/regra/referência e preservação do resultado por sessão.
A E01 consulta somente a origem PostgreSQL sintética, revalidando o snapshot na
mesma transação de leitura; C01–C10 continuam conferências do snapshot. Falha ou
recusa não bloqueia análises básicas. Catálogo E01 versionado; regras institucionais
e limiar não foram habilitados. [Uso, limites e critérios](guides/PROMPT5_VERIFICACOES.md).

Verificações: suíte offline `pytest -m 'not integration'` com **397 aprovados e
1 excluído**, incluindo testes dos modos, mudanças de contexto, rerun, falha,
consulta parametrizada simulada e interface. Ruff check e format passaram em
`src tests app.py scripts` (79 arquivos). A tentativa de `ruff format --check .`
falhou por erro interno do Ruff ao percorrer diretórios com acesso negado; a
verificação nos diretórios de código citados passou. Após acrescentar a asserção
de não aplicabilidade na R01, o teste específico da interface passou (1 teste).
Sem PostgreSQL sintético
nesta revisão: o certificado havia sido registrado como ausente na conferência
anterior e sua disponibilidade não foi reavaliada em diretório privado; o leitor
depende também de arquivo de credencial. Matheus pode conferir com
`.\scripts\run-demo.cmd`, seguindo o guia. Não se acessou base institucional ou
segredos; nenhum resultado sintético valida origem real.

Prompt 5 permanece **parcial**: XLSX/SVG, exportação da E01, feedback associado à
execução/backlog, armazenamento operacional e metadados completos de C01–C10 não
foram implementados neste incremento. Avaliação humana e conferência abrangente
das exportações permanecem pendentes. Q-008/Q-009 registram armazenamento,
retenção e orçamento/limiares; templates não aprovados continuam desabilitados.
A execução PostgreSQL e confirmação humana do Prompt 4b seguem pendentes e afetam
a confiança na carga, sem bloquear o controle experimental. Matheus confere os
dois modos e a 4b; Talita avalia clareza, evidências, limitações e arquivos; DSI e
DBA tratam autenticação, retenção e fontes reais apenas na etapa final. Sem nova
aprovação geral de fórmulas, publicação ou avanço de fase.

## Prompt 4b · carga horária sintética — 03/11/2026

Conferência **offline parcial**, sem execução PostgreSQL pelo agente nem aceite
humano da 4b. O aceite da 4a permanece preservado. Corrigidos estado e total quando
havia parcela nula, bloqueio de unidades em branco/política ausente e avisos sobre
categoria atual, unidades e limitações das alocações. Referência SQL independente e
auditoria de cardinalidade preparadas para execução explícita por Matheus no mesmo
snapshot. [Regras, evidências e comando](guides/PROMPT4B_CARGA.md).

Rodada offline: **105 testes passaram** (carga, análises, leitores, interface,
hierarquia e workflows); após ampliar testes de falha por fonte, **27 passaram**
nos arquivos de carga e leitor. Ruff check e formatação passaram. A conferência
SQLite não comprova PostgreSQL; auditoria da instância e confirmação de Matheus
permanecem pendentes. Talita revisa clareza e uso; DSI/DBA tratam origem e integração
institucionais na etapa final. Sem Prompt 5, publicação ou acesso institucional.

Após acrescentar verificações de gráfico/CSV/ZIP e invalidação do semestre da carga,
**35 testes passaram** nos arquivos de carga, leitor e interface. A auditoria SQL
de cardinalidade não foi executada em PostgreSQL nesta sessão. Após a atualização
da versão de cálculo para `academic-carga-v2`, **21 testes de carga passaram**.

## Aceite de Matheus · 4a concluída — 03/11/2026

Matheus confirmou nesta conversa: **“tudo validado por mim e conciliado”**.
Registrados o aceite e a conciliação da **4a no escopo sintético**. A pendência de
confirmação por Matheus fica encerrada; **4b, carga horária, é o próximo incremento**,
sem implementação iniciada nesta atualização documental.

Evidência: declaração humana posterior à entrega abaixo. O agente não executou
nova leitura PostgreSQL nem inspecionou relatório adicional. Os números/testes
anteriores conservam sua identificação offline; não se atribui a confirmação a
uma saída específica da rotina nem se declara conciliação institucional, aceite
de Talita ou homologação visual institucional.

Somente documentação atualizada: estado, plano, contexto, decisões, próximos passos,
guia R06, catálogo, mapa, guias e índice. Sem testes de aplicação/banco nesta
atualização; verificação por `git diff --check`. Permanecem os limites conhecidos
de Centro, bolsas e cadastro, sem impedir a sequência sintética. Talita revê uso;
DSI/DBA tratam integração institucional na etapa final. Os blocos abaixo registram
a execução anterior pelo agente, antes desta confirmação.

## Prompt 4a · matrículas — 03/11/2026

**Parcela offline conferida; leitura/conciliação PostgreSQL pendente de execução
pelo desenvolvedor.** [Registro verificável da R06](guides/PROMPT4A_MATRICULAS.md)
com regras, filtros em tabela, conciliação, arquivos, comandos e responsáveis.
Mudanças locais anteriores preservadas; sem avanço para carga horária ou publicação.

Corrigido o detalhe de formados por código: FR/TD de um curso não se propaga a
linhas MT/MC de outro; o mínimo é obtido no recorte do respectivo curso, como na
seleção individual. Total recalculado sem somar cursos. Na variação com base zero
e atual ausente, a situação passa a Ausência de dado. Versão R06
`academic-matriculas-v2`. Acrescentados avisos de ingresso desconhecido, formação
pelo cadastro e projeção de bolsas por departamento sem vigência temporal.

Preparada rotina explícita `python -m vrac.dev.student_reconciliation --execute`:
reutiliza leitor e conta sintéticos, TLS/validação e uma transação REPEATABLE READ
para produção e referência SQL independente; registra total/curso, esperado,
obtido, diferença, filtros, fonte, hashes e snapshot. Não executada nesta sessão;
não houve leitura de segredos, partida/recriação de cluster ou recarga de dados.

Conciliação offline da fixture pública: **38 cenários, 2.612 comparações, 2.553
Confere e 59 Ausente em ambas, sem divergência**, por SQL independente em SQLite
em memória. Isso não comprova leitura PostgreSQL. Artefato completo em
`.cache/pyt-4a-reference/test_fixture_all_individual_an0/conciliacao-offline.json`;
o comando consolidado do guia gera outra cópia no seu `--basetemp`.

| Verificação final do incremento 4a | Resultado efetivamente observado |
|---|---|
| Rodada pertinente: 11 arquivos de testes de R06, leitores, UI, hierarquia e contratos | **128 aprovados**, código 0, em **143,66 s**; comando completo no guia |
| Ajuste final da gravação do CSV da rotina manual no Windows | Gravação em bytes evita CR duplicado; teste confere BOM UTF-8, linhas, ausência e proteção contra fórmulas |
| Reexecução do arquivo de referência após esse ajuste e inclusão do teste de CSV | **11 aprovados**, código 0, em **27,76 s**; `--basetemp=.cache/pyt-4a-csv-final`. A rodada de 11 arquivos não foi repetida após esse ajuste específico |
| Ruff | `ruff check src tests` aprovado; `ruff format --check src tests`: **73 arquivos já formatados** |
| Whitespace | `git diff --check` aprovado; avisos CRLF/LF não são falhas |
| PostgreSQL e instituição | Não executados; rotina apenas preparada e testada offline, inclusive compartilhamento de conexão e falhas sanitizadas |

Rodada intermediária: 55 testes passaram e um novo teste falhou por import ausente;
import corrigido, arquivo de referência reexecutado com **9 testes aprovados**.
Os dois testes novos de tela R06 passaram na rodada intermediária. A rodada
inicial menor teve 37 aprovados. Nenhuma dessas rodadas é teste PostgreSQL.

**Pendências:** Matheus executa a leitura/conciliação na base existente; o registro
anterior de certificado ausente não foi reavaliado. Talita revisa clareza e uso;
Centro permanece não informado na origem PG sem relação explícita. Bolsas por
departamento não reconstituem vigência/transferências; formados do cadastro não
representam todo o histórico. DSI/DBA e time tratam integração/fontes/acesso
institucionais somente na etapa final. Sem nova aprovação geral de fórmulas.

Os blocos seguintes preservam o histórico das tarefas anteriores.

## Interface docente conforme as capturas — 03/11/2026

Implementado o complemento solicitado por Matheus na mesma fase docente sintética.
A aba **Análise docente** reúne cartão de quantidade, barras verticais por
Departamento/Quadro, barras horizontais por Categoria Funcional, lista geral,
detalhe de CH Real e os dois gráficos mensais de ativos. Cores e fontes vêm dos
tokens locais; nomes e valores das capturas não foram copiados para a demonstração.
A referência de Horas Reais continua sendo a fonte dedicada no maior semestre por
matrícula. Não há equivalência presumida de quadros para o indicador de carga.

Centro precede e restringe Departamento nas duas entradas. Todos os departamentos
recorta somente o centro selecionado; seleções incompatíveis são retiradas.
Mudanças de filtros invalidam os resultados e arquivos da respectiva consulta.
As entradas mantêm estados independentes e podem exibir resultados simultaneamente.
Recalcular após falha do histórico remove sua versão anterior e preserva a composição.
Intervalo inválido bloqueia somente o histórico. A memória oferece todos os semestres
da fixture acadêmica; os filtros do cadastro atual não redefinem a população histórica.

Os meses conservam pessoas distintas, zeros observados e ausências como valores
separados. O total mensal é independente dos quadros; as pilhas podem se sobrepor.
Contagens mensais não são somadas para obter pessoas no semestre. Mantido o calendário
janeiro–julho/agosto–dezembro. Tabelas, CSV e PNG usam os mesmos resultados; a entrada
por período continua oferecendo o ZIP. O cartão/quadro R01 conta matrículas distintas;
departamento/categoria mantêm a contagem de linhas com matrícula documentada.

**Lacuna específica:** o contrato público do PostgreSQL sintético não fornece a
relação de centros; exibe Centro não informado. A memória usa dois centros
explicitamente fictícios. D-030/Q-013 registram a decisão e a pendência em
[DECISIONS](DECISIONS.md). Nenhuma relação institucional foi inferida.

Arquivos desta tarefa e roteiro para Talita no
[complemento do guia docente](guides/PROMPT3_DOCENTES.md), incluindo os módulos
`faculty_presentation.py`, `organisation_ui.py`, `department_hierarchy.py`, as
adaptações de UI/leitura/gráficos/histórico, seis novos arquivos de teste e as
regressões em `test_ui.py` e `test_faculty_completion.py`. Mudanças locais
preexistentes foram preservadas. Contexto, plano, decisões e este estado atualizados.

### Verificações desta tarefa

| Execução | Resultado efetivamente observado |
|---|---|
| Verificações focadas dos incrementos | Testes analíticos mensais, dados/PNG/Altair, detalhes docentes e hierarquia/leitores/UI executados offline pelos agentes; resultados aprovados nas rodadas focadas |
| Rodada integral `scripts/check.cmd` | Lock offline e Ruff aprovados; **343 testes passaram, 3 falharam e 1 de integração foi excluído**, em 472,75 s. Não declarada como suíte integral aprovada |
| Causa das três falhas | Duas preparações de saída fictícia falharam porque o argumento absoluto Windows em `PYTEST_ADDOPTS` perdeu as barras, gerando caminho duplicado e longo; uma execução AppTest excedeu o limite antigo de 20 s |
| Correções de verificação | Comando passou a usar caminho relativo curto em `.cache`; AppTest R01 alinhado ao limite de 60 s dos demais fluxos. Nenhum controle de segurança foi alterado. Dois testes de saída privada também passaram isoladamente (3,08 s) |
| Reexecução de arquivos e telas | **23 testes passaram**, código 0, em 259,63 s: sete de saída privada, treze de UI e três da página docente, incluindo os três casos que haviam falhado. Suíte integral não repetida após essa reexecução |
| Ruff e whitespace finais | `ruff check .`, `ruff format --check src tests` e `git diff --check` aprovados; os avisos CRLF/LF não são erros |
| PNG e materiais de marca | Prancha oficial e dois PNGs mensais sintéticos inspecionados. Corrigida apresentação fracionária no eixo de pessoas; rótulos de mês/semestre e valores preservados |
| Navegador | Prévia explícita em memória iniciada em `127.0.0.1:8517`; Computer Use bloqueou a inspeção por não conseguir verificar a URL no Windows. Não se contornou o bloqueio por outro mecanismo |

Rodadas intermediárias também encontraram mocks antigos da API departamental,
asserções que presumiam gráfico semestral/Altair sem camadas e um seletor de
histórico limitado aos períodos da fixture de registros brutos. Foram corrigidos
sem mudar regras institucionais ou usar valores das capturas como expectativas.
A primeira tentativa integral esbarrou ainda na permissão da pasta temporária
padrão do Windows; não foram alteradas suas permissões.

Comandos para executar a demonstração sem banco e conferir o projeto:

```powershell
.\scripts\run-demo.cmd --memory
.\scripts\check.cmd
```

Reexecução que evita o problema local de caminho/permissão, sem alterar a aplicação:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_private_output.py tests/test_ui.py tests/test_faculty_page.py --basetemp=.cache/pyt-docentes-final -q -p no:cacheprovider --tb=short
```

**Não executados:** conexão ou conferência na instância PostgreSQL, banco institucional,
teste de integração excluído, hover/responsividade/download manual no navegador,
autenticação, deploy ou homologação visual/funcional. Não houve commit, push,
publicação, alteração de TLS, acesso a credenciais ou avanço para outra fase.
Matheus/Talita revisam uso, filtros e exportações; Matheus e o responsável pela
identidade visual revisam a apresentação; a relação de centros requer fonte explícita.
DSI/DBA/time conferem fontes, permissões, TLS e acesso institucional na etapa final.
Não se pede nova aprovação geral das fórmulas já documentadas.

**Artefatos temporários:** o argumento Windows incorreto gerou duas pastas locais
não rastreadas, com os nomes abaixo, contendo somente fixtures dos testes. A revisão
automática rejeitou a remoção recursiva por política de execução; as pastas foram
preservadas e não fazem parte dos arquivos de entrega:

- `UsersmatheusacciolyDocumentsGitHubrelatorios-automatizados_VRAC.cachepytest-docentes-final-20261103/`
- `UsersmatheusacciolyDocumentsGitHubrelatorios-automatizados_VRAC.cachepytest-docentes-final-20261103-b/`

O conteúdo seguinte preserva o histórico anterior.

Atualizado em 03/11/2026 (D-028: base sintética durante o desenvolvimento; conexão real somente na etapa final e deploy). **Seis roteiros acadêmicos implementados sobre dados sintéticos, com gráficos, tabelas, conferências e exportações.**
**Conexão e inventário institucionais: NÃO VALIDADOS.** SQL Server confirmado por Matheus.
Fontes físicas e aceite funcional da aplicação continuam pendentes; as fórmulas
documentadas não exigem nova validação analítica. Fases 3/4a/4b executáveis na base
sintética; fase 5 parcialmente implementada; fases 6/7 institucionais não iniciadas.
Fase 0 e ferramentas do Prompt 1 preparadas. Conteúdo do guia original preservado;
`AGENTS.md` atualizado com a exigência de branding institucional.

## Prompt 3 · Fechamento docente sintético — 03/11/2026

**Implementado e conferido offline; exploração visual dos gráficos no navegador
pendente.** Mudanças preexistentes do Prompt 2 preservadas. Matriz das lacunas,
arquivos deste incremento, definições, comandos e roteiro para Talita em
[PROMPT3_DOCENTES.md](guides/PROMPT3_DOCENTES.md). Não houve avanço aos outros
prompts, commit, push, deploy ou publicação.

- R01: distribuição por departamento, quadro e categoria, lista e CSV nas duas
  entradas da aplicação; seleção individual no formulário de roteiros. Total e
  quadro contam matrículas distintas; categoria/departamento contam linhas com
  matrícula, conforme visuais documentados. Horas preservam máximo por vínculo;
  valor, nulo, falta de registro e fonte indisponível são identificados na lista.
- R02: tabela e gráfico geral/QP por departamento, sem alterar o denominador
  geral de cada recorte. QP não selecionado não vira zero; classificação ausente
  impede participação conclusiva. Não somar departamentos sobrepostos.
- R03: pessoas distintas na união de competências, sem soma mensal; total em
  gráfico próprio e barras empilhadas por quadro, explicitamente sobrepostas.
  Cobertura menor que 7/5 meses agora produz Parcial. Fórmulas preservadas.
- Apresentação: Altair direto no projeto/lock, com largura do contêiner, hover e
  destaque local de séries/barras; tokens/fontes locais. Mesmas tabelas calculadas
  alimentam gráficos e arquivos. Matplotlib mantém PNG; R04/R05 reaproveitados,
  R06 sem alteração de cálculo ou apresentação. D-029 registra a escolha.
- Estado: origem/modo/falha global retiram objetos das abas; recarga e filtros
  retiram resultados/downloads até nova geração. Seleções R01 fora do domínio
  são limpas ao trocar departamento. Categoria só histórica gera vazio na R01
  sem bloquear outros roteiros. Horas indisponíveis afetam só seu detalhe R01.

| Verificação executada | Resultado |
|---|---|
| `scripts/check.cmd` — rodada final | Código 0; **320 testes passaram, 1 de integração excluído**, 93,97 s; rede e drivers bloqueados pela fixture offline |
| Lock offline, Ruff check e Ruff format | Aprovados; 53 pacotes resolvidos, 90 arquivos formatados conforme verificação, Altair mantido em 6.3.0 |
| Novos testes e regressões docentes | Unidades por visual, duplicidades, múltiplos vínculos, comparação departamental, QP/denominadores, julho, competências faltantes, sobreposição, dados dos gráficos, fonte opcional, parâmetros vinculados, invalidação e CSV/ZIP |
| PNG e exportações | Regressões offline de geração; dados de gráficos conferidos contra tabelas e expectativas sintéticas pequenas. Sem download manual no navegador |
| Prancha oficial e tokens | README/guidelines/tokens lidos; renderização local da prancha conferida. Sem homologação visual |
| Navegador local | Prévia explícita em memória na porta 8516; página inicial observada estreita e maximizada. Tentativa de geração interrompida pelo Computer Use: política de URLs ainda não suportada neste navegador Windows |

Rodadas intermediárias identificaram um timeout na importação inicial (Altair
passou a ser importado somente ao gerar), nome incorreto do componente na
asserção AppTest (corrigido para `vega_lite_chart`) e conexão fictícia antiga sem
`transaction()` (objeto atualizado para o isolamento por fonte). A última suíte
completa acima passou; esses erros não foram ocultados ou tratados como sucesso.
O primeiro lock fora do ambiente de cache do projeto falhou por permissão/cache;
o lock foi gerado e conferido offline com `.cache/uv`, conforme os scripts existentes.

**Não executados:** conexão/conferência PostgreSQL; conexão, diagnóstico, inventário
ou SQL Server; teste de integração excluído; hover, seleção de séries e responsividade
dos gráficos no navegador; abertura manual dos downloads; autenticação, homologação
visual/funcional ou publicação. Não se recriou cluster/carga/views nem se alterou TLS.
AppTest e especificações Altair aprovadas não comprovam comportamento visual real.

QP configurável, unidades comparáveis e atos administrativos seguem simulações;
valores do filtro salvo de quadro continuam lacuna específica de conciliação com
o painel. Resultados sintéticos não validam fontes institucionais. Matheus deve
revisar o incremento e repetir a exploração visual; Talita avalia consulta e
exportação; responsável institucional revisa identidade visual. DBA/DSI/time
conferem fontes, leitura, TLS e acesso na etapa final. Sem nova aprovação geral
das fórmulas documentadas, conforme D-022/D-027/D-028.

## Relatório de bordo para comunicação assíncrona — 03/11/2026

Consolidado no chat um relatório para copiar no Notion, com entregas sintéticas,
trabalho em revisão, próximos passos, datas de planejamento, responsáveis e riscos.
Fontes: contexto, plano, decisões, guias, histórico deste estado e leitura do
projeto no Todoist. A consulta confirmou **11 tarefas abertas em quatro seções**;
datas são metas de trabalho, não comprovação de execução ou prazo institucional.
Nenhuma tarefa foi alterada e nenhum conteúdo foi publicado no Notion.

O mapa lógico/catálogo tem alterações locais preexistentes em revisão; não foi
declarada conclusão do Prompt 2 nem validação dessas alterações nesta tarefa.
Os seis roteiros seguem como entrega sintética registrada; fase 5 parcial.
D-022/D-027/D-028 prevalecem sobre trechos históricos: sem nova aprovação geral
das fórmulas; conexão real somente na etapa final; autenticação com o time.

Arquivo alterado nesta tarefa: somente `docs/STATUS.md`, preservando as mudanças
anteriores. Sem novo comando de aplicação; comandos existentes no guia de uso.
Verificação documental: `git diff --check -- docs/STATUS.md`. Testes de software,
bancos, execução da aplicação, revisão visual e deploy não repetidos. Resultados
de 304 testes em 02/11 e 97 em 03/11 são registros históricos, não novas execuções.

Sem novo bloqueio para desenvolvimento sintético. Permanecem a revisão de uso por
Talita, revisão visual por Matheus/responsável institucional e, na etapa final,
fontes/escopo de leitura pelo DBA e acesso/TLS/autenticação pelo time/DSI. Integrar
dados reais no final pode revelar lacunas e afetar as metas de 12–13/11. Não houve
avanço de implementação, conexão institucional, commit, push ou publicação.

## Prompt 2 — mapa lógico/sintético concluído — 03/11/2026

**Concluído no escopo solicitado, com conferência por código, receita e testes
offline.** [Mapa R01–R06](operations/SYNTHETIC_SOURCE_MAP.md) e
[catálogo](ANALYSIS_CATALOG.md) vinculam cada entrada às projeções/consultas,
contratos e testes existentes, com granularidade, chaves/deduplicação, relações,
tipos/nulabilidade, unidades, temporalidade, filtros e limitações. Restrições DDL,
observações da receita e convenções analíticas estão identificadas separadamente.
Nenhuma observação da receita é apresentada como evidência do PostgreSQL instalado.

`config/analyses.yaml` passou a `phase2-synthetic-map-v5`, com
`synthetic_status: implemented_offline_verified` e referência ao mapa por família.
Campos de fonte/seleção/validação **institucionais** permanecem `null`/`pending`.
Não foram preenchidos com nomes sintéticos ou promovidos a aprovação. QP,
unidades comparáveis e atos administrativos permanecem simulações explícitas.
O catálogo e a CLI descrevem os executores já existentes, sem tratar contratos
de planejamento anteriores como ausência das análises. `phase3_blockers` aceita
modo explícito: sintético sem dependência institucional; padrão real preserva
bloqueios. Teste cobre essa separação e rejeição de modo inválido.

**Conferência PostgreSQL não executada:** primeira tentativa parou antes da conexão
por Psycopg ausente; dependência existente no lock instalada offline (Psycopg e
Psycopg binary 3.3.6). Nova tentativa pelo leitor fixo de leitura, TLS `verify-full`,
identificou arquivo de certificado local ausente. Não houve leitura de registros,
verificação de chaves/cardinalidade na instância, fallback, início/recriação de
cluster, instalação de views/carga ou alteração de TLS. Configurações e credenciais
privadas/institucionais não foram abertas nem impressas; o driver usa o mecanismo
de conexão sintética já preparado. A classificação auxiliar imprimiu somente
categorias fixas de erro.

**Observado offline na receita, semente 20261030:** 24 pessoas/25 vínculos, 905 linhas
de histórico docente, 150 linhas de carga, 42 alocações, 60 eventos de função,
120 matrículas cadastrais, 408 situações acadêmicas (407 pares matrícula/período)
e 354 bolsas (132 pares). Relações necessárias entre histórico/centro, carga/cadastro,
planejamento/carga e funções/cadastro/distribuição não multiplicam nem perdem linhas
na receita avaliada. Isso não demonstra PK/FK/UQ, conteúdo instalado ou cobertura
institucional. Suplemento de 15 atos e política foram conferidos por receita/DDL,
sem instalação ou consulta. Mapeamentos detalhados e relatório permaneceram locais
em `.cache/prompt2-map/`, ignorados por Git/Docker; nenhuma cópia de nomes internos
novos foi incorporada ao mapa versionável.

| Comando/verificação desta tarefa | Resultado |
|---|---|
| `.tools/uv/uv.exe sync --locked --offline --extra postgres --extra sqlserver` com cache/Python locais e configuração externa desativada | Código 0; adicionou somente os dois pacotes Psycopg já travados; lock inalterado; sem rede |
| `.venv/Scripts/python.exe .cache/prompt2-map/check_mapping.py` | Sem relatório PG: primeira tentativa sem driver; segunda interrompida na conexão por certificado ausente |
| `.venv/Scripts/python.exe .cache/prompt2-map/connection_status.py` | Código 0; classificador fixo `OperationalError`, certificado/arquivo ausente; sem erro bruto |
| `.venv/Scripts/python.exe .cache/prompt2-map/profile_fixture.py` | Código 0; avalia `build(20261030)` da receita local, sem banco; relatório agregado `fixture-profile.json` local |
| `.\scripts\check.cmd` | Lock offline, Ruff e formatação aprovados; **306 passaram, 1 integração institucional excluída**, 56,84 s |
| `.venv/Scripts/python.exe -m vrac.analyses` | Código 0; três famílias, nove variantes documentais e seis roteiros; estados institucionais separados do sintético; nenhuma conexão |
| `.venv/Scripts/python.exe -m pytest tests/test_analysis_catalog.py tests/test_workflows.py tests/test_semantic_baseline.py -q` após ajustes finais no YAML | **64 passaram**, código 0; separação sintético/institucional e integridade das variantes preservadas |
| Ruff nos cinco arquivos Python alterados | Código 0; lint e formatação aprovados após ajuste final da CLI |
| `.venv/Scripts/python.exe .cache/prompt2-map/check_docs.py` | Código 0; **100 links locais, nenhuma falha**, incluindo âncoras do mapa e compatibilidade do catálogo |
| `git diff --check` e `git check-ignore` dos auxiliares locais | Sem erro de whitespace; script e relatório detalhado confirmados ignorados |

O primeiro `check.cmd` interrompeu por formatação da assinatura de `phase3_blockers`;
`ruff format src/vrac/analyses/workflows.py` corrigiu e a execução acima passou.
Revisão de links locais identificou uma âncora histórica removida do catálogo;
âncora de compatibilidade restaurada para preservar o acesso à seção vigente.
Um comando auxiliar de classificação teve erro de sintaxe por aspas PowerShell;
foi substituído pelo script local, sem acesso adicional ou mudança na aplicação.

**Arquivos desta tarefa:** novo `docs/operations/SYNTHETIC_SOURCE_MAP.md`;
`docs/ANALYSIS_CATALOG.md`, `config/analyses.yaml`,
`src/vrac/analyses/{catalog,workflows,__main__}.py`,
`tests/test_analysis_catalog.py`, `tests/test_workflows.py`,
`docs/{PLAN,PROJECT_CONTEXT,PROXIMOS_PASSOS,README,STATUS}.md` e
`docs/operations/{SANITIZED_DATA_DICTIONARY,SYNTHETIC_POSTGRES}.md`. Alterações locais que já existiam
foram preservadas; demais arquivos modificados anteriormente não são desta tarefa.
Sem alteração de SQL, cálculos, telas, exportações, dependências declaradas ou lock.

**Reutilização pelo Prompt 3:** mapa por entrada/fonte, R01 (`compute_overview`),
leitores `load_faculty_source`/`load_academic_source`, SQL fixo, contratos, fixtures
e testes existentes. Não precisa executar Prompt 1 real nem reaprovar fórmulas.
Prompt 3 não iniciado; sem commit, push ou publicação.

**Lacunas/riscos:** certificado local ausente impede somente conferência viva agora;
unicidade da receita não é restrição do banco; duplicação de cadastro/carga poderia
multiplicar views; bolsa/departamento não tem vigência na junção. Permanecem filtro
salvo R01, QP institucional, unidades institucionais, evidências administrativas reais,
aluno único, equivalências, compartilhamento/classificação e processo seletivo,
com efeito específico registrado no mapa. Atualização por fonte não disponível.

**Não executados:** leitura/conciliação PostgreSQL, integração real, inventário,
consultas/escrita institucionais, inspeção de configuração privada, revisão visual,
homologação com Talita/identidade visual, instalação de dados, deploy/publicação.
No próximo incremento sintético solicitado, Matheus poderá recuperar a fixture pelo
procedimento existente e repetir leitura/conferência com conta de leitura e TLS.
Somente na etapa final Matheus/DBA mapearão fontes, chaves, tipos, unidades, cobertura
e permissões institucionais; DSI/time integrarão acesso/autenticação. Talita poderá
avaliar o uso da aplicação; nenhuma reunião ou nova aprovação geral de fórmulas
é necessária para concluir este Prompt 2.

## Escopo e Todoist atualizados — banco real somente no final — 03/11/2026

**Diretriz registrada (D-028):** Matheus esclareceu que trabalha com o PostgreSQL
sintético existente. Conexão, diagnóstico, inventário, mapa físico e conferência
institucionais foram reservados à etapa final do projeto e deploy. Não solicitar
configuração/execução real agora nem tratar esse retorno como bloqueio dos
incrementos sintéticos. A preparação offline do Prompt 1 permanece disponível;
sua execução real foi adiada, sem conclusão ou validação presumida.

**Executado no planejamento:** atualizado e relido o
[projeto no Todoist](https://app.todoist.com/app/project/6hvgC82GJR7Fgc9R),
com descrição do projeto, quatro seções e 11 tarefas ajustadas. Diagnóstico e
inventário real transferidos de 03/11 para **12/11**, na seção final, após preparar
a versão/guia e antes da integração/conferência institucional e deploy. Prompt 2
passa ao mapa lógico/sintético sem depender desse inventário; Prompts 3–5 e feedback
usam a base sintética. A tarefa geral de deploy inclui completar mapa físico,
leitura e conferência institucionais nessa etapa. Demais datas, responsáveis,
prioridades e IDs preservados; nenhuma tarefa criada, removida ou concluída.
Releitura confirmou 11 tarefas abertas, sem paginação restante, descrições e datas
compatíveis com as alterações e quatro seções atualizadas. Nenhuma mensagem ou
comentário foi enviado a terceiros; somente planejamento sanitizado no projeto
pessoal, não compartilhado.

**Documentação alterada nesta atualização:** `README.md`, `docs/README.md`,
`docs/PROJECT_CONTEXT.md`, `docs/PLAN.md`, `docs/PROXIMOS_PASSOS.md`,
`docs/DECISIONS.md`, este estado, `docs/operations/CONFIGURAR_KAPPA.md`,
`docs/operations/DATABASE_DISCOVERY.md` e
`docs/operations/SANITIZED_DATA_DICTIONARY.md`. Guias institucionais sinalizados
como procedimentos futuros; instrução de aguardar retorno real agora substituída.
Alterações locais anteriores preservadas; nenhum código ou consulta alterado.

**Verificações:** comparação/releitura do conector e revisão documental;
`git diff --check` aprovado. Sem novos comandos de aplicação. Testes de software,
conexão sintética/real, diagnóstico/inventário, instalação e deploy não executados
nesta atualização de escopo. Os 97 testes do registro anterior são evidência
histórica, não uma nova execução.

**Pendente/riscos:** desenvolver os próximos incrementos somente quando
solicitados; fontes e resultados institucionais continuam não validados.
A integração concentrada no final pode revelar lacunas de mapeamento, tipos,
cobertura ou acesso, sem garantia de absorção nas datas de trabalho. Na etapa
final, Matheus executará/revisará o material real; DBA confirmará escopo/somente
leitura e DSI/time tratarão acesso, driver, TLS e autenticação. Nada disso é
requisito novo para o desenvolvimento sintético atual. Não se exige ação ou nova
validação de fórmulas por Talita nesta atualização. Sem conexão, leitura privada,
avanço de implementação, commit, push ou publicação.

## Prompt 1 — roteiro conferido offline — 03/11/2026 (registro anterior)

**Encaminhamento de execução imediata substituído pela D-028 acima; executar o
roteiro institucional somente na etapa final e deploy.** As verificações offline
abaixo permanecem como evidência da preparação realizada.

**Preparado:** revisão das ferramentas existentes, exemplos públicos, SQL fixo e
lançadores; roteiro em ordem, códigos de saída, interpretação de resultados e
modelo de retorno sanitizado em
[CONFIGURAR_KAPPA.md](operations/CONFIGURAR_KAPPA.md#4-roteiro-operacional-do-prompt-1--03112026).
O [dicionário sanitizado](operations/SANITIZED_DATA_DICTIONARY.md) foi alinhado ao
SQL Server já confirmado e à D-022, sem exigir nova validação das fórmulas.
Nenhum defeito concreto encontrado nas ferramentas; nenhum código, dependência
ou consulta foi alterado. Mudanças locais anteriores em plano/contexto/estado
preservadas. Arquivos desta tarefa: este estado e os dois guias vinculados.

**Executado offline:**

- `.\scripts\diagnose-db.cmd --help`, `.\scripts\inventory-db.cmd --help` e
  `.\.venv\Scripts\python.exe -m vrac.db --help`: códigos `0`, sem configuração
  ou conexão. Conferidos argumentos `--config`, `--output-dir` e `--execute`.
- Versões por metadados locais: Python 3.12.15 de 64 bits, SQLAlchemy 2.1.6,
  pyodbc 5.3.0 e pytest 9.1.1 disponíveis. Consulta local `pyodbc.drivers()`:
  driver legado `SQL Server` e `ODBC Driver 18 for SQL Server` instalados.
  Não comprova driver institucional escolhido, conectividade ou TLS do destino.
  A primeira tentativa auxiliar de listar versões teve erro de sintaxe no comando;
  foi corrigida, com nova execução de código `0`. Sem instalação/reinstalação.
- `.\.venv\Scripts\python.exe -m pytest tests/test_db_cli.py tests/test_db_config.py tests/test_db_connection.py tests/test_db_inventory.py tests/test_private_output.py -q --basetemp .cache/pytest-prompt1-20261103`:
  **97 passaram**, código `0`. Rede e conexões nativas bloqueadas pela fixture
  offline; somente mocks, DBAPI fictícia e arquivos temporários sintéticos.
- Comando de dependências do roteiro executado literalmente, código `0`;
  revisão do diff e `git diff --check` sem erros de whitespace.

**Pendente:** Matheus completar sua cópia privada externa `dbconfig.toml` e
executar manualmente diagnóstico, interpretar a saída e só então inventariar.
Os comandos reais estão no roteiro e não foram executados pelo agente.
Continuam sem evidência de preenchimento: porta TCP, lista nominal dos schemas
autorizados, autenticação, driver escolhido e confirmação administrativa de
somente leitura/escopo. Obter somente detalhes ainda ausentes com DBA/DSI, sem
reabrir a investigação do destino ou pedir credenciais no chat.

Riscos concretos: driver instalado não comprova TLS/rede/autenticação; inventário
tecnicamente válido ainda tem cobertura `unknown`; truncamento pode fragmentar
chaves. Não ampliar escopo ou reduzir proteções para completar lacunas.
Matheus revisará saídas apenas localmente e entregará o retorno sanitizado;
DBA confirma somente leitura e escopo; DSI trata eventual falha específica de
driver/rede/certificado. Nenhuma ação nova de Talita é exigida neste Prompt 1.

**Não executados:** configuração real, diagnóstico/inventário institucionais,
integração real, consultas de qualidade, escrita, suíte completa da aplicação,
instalação, deploy ou publicação. Nenhuma saída privada institucional foi lida.
Conexão e inventário continuam **NÃO VALIDADOS**; Prompt 1 **não concluído**,
aguardando retorno sanitizado. Sem avanço ao Prompt 2, commit ou push.

## Revisão operacional das tarefas por prompt — 02/11/2026

Matheus corrigiu o foco do planejamento: executar os prompts existentes, evitar
muitas reuniões e amarras institucionais e tratar encaminhamentos externos ao
longo do trabalho. Informou que já possui o ambiente de deploy e que autenticação
e assuntos relacionados ficam com o time de desenvolvimento.

O [projeto no Todoist](https://app.todoist.com/app/project/6hvgC82GJR7Fgc9R)
foi reorganizado de **25 para 11 tarefas operacionais**, em quatro seções:
Prompts 1–2/dados, Prompts 3–4/análises, Prompt 5 e feedback/finalização e
Prompt 7/entrega. Onze tarefas existentes foram reaproveitadas e atualizadas;
14 tarefas redundantes de coordenação/implementação atribuída ao time foram
removidas, sem marcá-las como trabalho concluído. Nenhuma tarefa nova foi criada.

Cada tarefa tem link direto ao prompt do guia, indicação do que já está pronto,
trabalho restante, resultado esperado e sequência técnica. As referências são os
Prompts 1 (linha 155), 2 (175), 3 (196), 4 (216), 5 (239), 7 (283) e feedback (305)
de `docs/references/Guia_Desenvolvimento_VRAC_Codex.md`. Prompt 0 já concluído;
Prompt 6 é responsabilidade do time de desenvolvimento e ficou registrado no
contexto, sem tarefa de implementação para Matheus.

Reuniões por etapa e provisionamento de novo ambiente deixaram a lista de execução.
Feedback pontual e conferência do fluxo foram incorporados à finalização, sem nova
aprovação geral das fórmulas documentadas. A disponibilidade do ambiente foi informada
por Matheus, não testada nesta sessão. Segurança e acesso continuam necessários ao
uso real; sua entrega cabe ao time e não bloqueia o avanço sintético ou a preparação.
O [deploy](https://app.todoist.com/app/task/6hvgCWGWmrJ2r9M2) continua em uma tarefa
geral em 12/11; conferência final em 13/11. Meta pessoal 13/11, reserva 14–15/11,
sem deadline institucional.

Arquivos atualizados: `docs/PROJECT_CONTEXT.md`, `docs/PLAN.md` e `docs/STATUS.md`.
Verificações: releitura das tarefas no conector para conferir contagem, referências,
datas e remoção de dependências antigas. Nenhum teste de software, banco, acesso,
infraestrutura ou deploy foi executado; não há novos comandos de execução.
Permanecem como verificações futuras a leitura institucional pelo operador, a
integração de acesso entregue pelo time e a conferência funcional da versão.
Não houve implementação, avanço de fase, commit, publicação ou mensagem a terceiros.

## Planejamento inicial de conclusão no Todoist — 02/11/2026 (histórico)

**Substituído pela revisão operacional acima.** O registro abaixo preserva a
organização inicial; não deve ser usado como checklist atual.

Matheus solicitou organizar as tarefas restantes e concluir o projeto no máximo
na semana seguinte, sem deadline institucional confirmado. Foi criado o projeto
[VRAC · Análises acadêmicas](https://app.todoist.com/app/project/6hvgC82GJR7Fgc9R),
dentro de **trabalho ep/puc**, com **25 tarefas abertas** em cinco seções:
escopo/dependências, integração institucional, acesso/operação seguros,
revisões/qualidade e entrega/deploy. Cada tarefa tem prioridade, data de trabalho,
critério de conclusão e, quando aplicável, dependências com links entre tarefas.

As datas de 03 a 13/11/2026 são metas pessoais de planejamento, sem uso do campo
de deadline: entrega principal em **sexta-feira, 13/11**, com **14–15/11 como
reserva**. A conclusão integral depende de respostas e homologações externas;
o prazo não comprova disponibilidade de fontes, infraestrutura ou aprovações.

O trabalho sintético já implementado foi registrado no contexto do projeto,
sem recriar tarefas para desenvolver os seis roteiros. O planejamento contempla:

- Matheus encaminhar acessos, fontes e agendas; DBA confirmar escopo e somente
  leitura; DSI definir identidade, autorização, ambiente, segredos e operação.
- Operador executar diagnóstico/inventário fora da sessão do agente, liberar
  somente material sanitizado e conferir a integração em ambiente autorizado.
- Mapear fontes e implementar o leitor analítico institucional: o adaptador SQL
  Server existente atende descoberta, não a leitura institucional dos roteiros.
- Resolver somente lacunas concretas de QP, unidades de carga, evidência
  administrativa e equivalências quando necessárias. D-022 continua dispensando
  nova aprovação das fórmulas documentadas.
- Rever uso com Talita, identidade visual com Matheus e responsável institucional,
  segurança com DSI/DBA, arquivos exportados, desempenho e regressão técnica.
- Reconciliar a documentação histórica, decidir tratamento mínimo de feedback e
  retenção, preparar guia/operação e registrar o aceite da entrega.

Conforme solicitado, o deploy ficou em uma única tarefa geral:
[Planejar e realizar o deploy do projeto](https://app.todoist.com/app/task/6hvgCWGWmrJ2r9M2),
prevista para 12/11, sem presumir tecnologia ou procedimento. A tarefa depende de
segurança, regressão e passagem de operação e exige liberação de publicação.
Piloto e fechamento estão previstos para 13/11; pendências devem manter responsável,
impacto e próxima ação, sem declarar conclusão por prazo.

Verificações desta tarefa: criação e releitura pelo conector do Todoist confirmaram
25 tarefas e cinco seções; datas, prioridades e dependências foram conferidas,
sem ciclos ou dependência planejada após a tarefa correspondente. Somente
planejamento sanitizado foi enviado ao projeto pessoal, não compartilhado.
Nenhuma mensagem foi enviada a Talita/DSI/DBA e nenhuma credencial, dado acadêmico,
nome físico de fonte ou endereço interno foi transferido ao Todoist.

Arquivo alterado no repositório: `docs/STATUS.md`. Não há novo comando de execução
da aplicação; os comandos existentes continuam nos guias. Testes de software,
banco institucional/sintético, instalação, revisão visual e implantação não foram
executados neste planejamento. Os 304 testes registrados abaixo são evidência da
tarefa anterior, não nova execução. Nenhuma fase foi implementada, commit criado
ou aplicação publicada nesta tarefa.

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

### Prévia local — 03/11/2026

A pedido de Matheus, PostgreSQL sintético iniciado com verificações aprovadas e conta somente leitura. Streamlit já respondia em http://127.0.0.1:8501; endpoint de saúde retornou HTTP 200 (ok). Nova instância recusada porque a porta está ocupada. Sem alteração de código, avanço de fase ou publicação. Suíte de testes e conferência funcional no navegador não executadas nesta operação; Matheus pode conferir os roteiros na prévia.
# Higiene de configurações — 03/11/2026

Novos arquivos YAML, YML e TOML são ignorados por padrão, com exceções para
exemplos e configurações essenciais do projeto. Arquivos já rastreados continuam
versionados; o `.gitignore` não remove arquivos do histórico nem protege segredos.
