# Prompt 4a · conferência de matrículas sintéticas

Registro de 03/11/2026. Escopo restrito à R06, conforme D-022/D-027/D-028.
**4a concluída no escopo sintético por aceite de Matheus**, que confirmou após
a entrega: “tudo validado por mim e conciliado”. A confirmação humana encerra a
pendência de aceite/conciliação; o agente não executou nova leitura PostgreSQL
nem inspecionou relatório adicional. Números e testes abaixo continuam sendo
evidência offline, sem atribuí-los à instância PostgreSQL.
Próximo incremento: **4b, carga horária**, ainda não iniciado nesta atualização.
Nenhuma conciliação institucional, aceite de Talita ou homologação visual declarada.

## Implementação reutilizada e correções

Foram inspecionadas as alterações locais existentes, preservadas, e os componentes:

| Componente | Papel existente / trabalho deste incremento |
|---|---|
| `analyses/academic.py::calculate_students` | Quatro populações, detalhe por código e variações já existentes; correções pontuais descritas abaixo |
| `academic_data.py::StudentRow/ScholarshipRow/AcademicSource` | Matrícula acadêmica, disponibilidade por fonte e hash do conteúdo; contratos preservados |
| `contracts.py`, `workflows.py` | Contratos lógicos e dependências; não substituem o executor atual da R06 |
| `db/synthetic_postgres.py`, `academic_students.sql`, `academic_student_history.sql`, `academic_scholarships.sql` | Leitura existente; SQL de produção preservado. Extraído `_read_academic_source` do corpo existente para compartilhar uma conexão com a referência |
| `academic_ui.py`, `charts.py`, `academic_export.py` | Filtros em tabela, quatro curvas, CSV/PNG/ZIP, snapshot e invalidação existentes; sem nova tela ou ajuste visual |
| Testes existentes e referência local `test-all-analyses.py` | Reutilizados os casos e as agregações independentes. O script local antigo usa outra conexão para a referência, só cobre totais e presume observação/ingresso conhecidos; não foi executado |

**Divergência corrigida:** formados no detalhe por curso reutilizavam o mínimo
FR/TD do conjunto de cursos e verificavam a matrícula em linhas de qualquer
situação do curso. Assim, FR no C1 podia aparecer no C2 com apenas MT; TD posterior
no C2 podia aparecer no ponto do C1. Agora cada detalhe aplica o mesmo recorte
da seleção individual de seu código e considera somente FR/TD para obter o mínimo.
O total continua sendo recalculado no conjunto selecionado; não é a soma dos cursos.

Também corrigida a descrição da variação quando a base é zero **e o atual está
ausente**: diferença e percentual continuam ausentes, com situação **Ausência de
dado**. **Base zero** é usada quando ambos os valores são conhecidos. A versão da
R06 passa a `academic-matriculas-v2`; regras de outras análises preservadas.

Os avisos da R06/CSV/manifesto explicitam ingresso desconhecido, a limitação temporal
das bolsas e a impossibilidade de reconstruir toda a formação histórica pelo cadastro.

## Populações conferidas

| População | Regra preservada / limite |
|---|---|
| Matriculados · B-M-035 | MT/MC no histórico do ponto; matrícula não nula e distinta; menor ingresso conhecido **no cadastro lido após o recorte departamental, antes de curso/habilitação e demais filtros acadêmicos**, menor ou igual ao ponto. Ingresso desconhecido de candidato impede o total daquele ponto/curso |
| Bolsistas matriculados · B-M-038 | Interseção dos elegíveis com existência de bolsa na matrícula/período; concessões repetidas não multiplicam. Falha de bolsas afeta somente esta curva |
| Formados · B-M-036 | FR/TD no cadastro filtrado, menor período por matrícula; detalhe usa seu código de curso. HF não incluído; não é histórico completo de eventos |
| Ingressantes · B-M-070 | Histórico filtrado, ingresso no ponto e período no ponto ou forma literal `Dupla Diplomacao`; matrículas distintas, independentemente das demais populações |
| Variação de matriculados | Atual − anterior; percentual = diferença/base × 100. Base zero impede percentual; ausência de base/atual impede ambos. Não soma estoques semestrais |

Matrículas acadêmicas não são pessoas únicas. Situações conflitantes são mantidas:
uma linha FR não elimina arbitrariamente uma linha MT/MC do mesmo período.
Zero observado, nulo, falta de observação e falha de leitura conservam seus efeitos
distintos. O eixo usa os períodos disponíveis; falta de observação num ponto desse
eixo permanece como lacuna na tabela/gráfico/exportação.

## Filtros efetivos

| Filtro | Aplicação e evidência |
|---|---|
| Centro | Restringe departamentos quando existe relação explícita. Fixture pública usa centros fictícios; PostgreSQL mantém **Centro não informado**, sem inferência institucional |
| Departamento do curso | Seleção individual e Todos os departamentos; conjunto efetivo limitado pelo centro. Consultas de produção vinculam o departamento |
| Intervalo inicial/final | Pontos disponíveis entre as referências; teste de intervalo menor e invalidação na tela |
| Curso | Código exato; seleção individual e múltipla, detalhe por código. Nomes semelhantes/iguais não unem séries |
| Habilitação | Recorta cada população; não recorta antecipadamente a busca do menor ingresso do cadastro lido |
| Turno / nível / forma de ingresso | Recortes próprios, isolados e combinados com curso e habilitação |

A tabela existente de filtros registra Centro, Departamento, departamentos efetivos,
origem e dimensões selecionadas. Os arquivos da R06 registram o rótulo do escopo,
filtros, versão e hash do conteúdo. Quadro, categoria, QP e semestre da carga são
campos compartilhados do formulário: não alteram as populações acadêmicas.
Não foi acrescentado processo seletivo ou equivalência automática.

## Conciliação offline efetivamente executada

A referência SQL usa `COUNT(DISTINCT ...)`, mínimos e existência, separadamente do
cálculo Python de produção. O teste executa esses SQLs em **SQLite em memória**,
adaptando apenas parâmetros e a função de leitura JSON. Isso confere a lógica da
referência e as entradas tipadas, **sem comprovar sintaxe, views, TLS, privilégios ou
leitura no PostgreSQL**. Há ainda expectativas manuais pequenas e um teste que
injeta obtido = 999, esperando detectar esperado = 1 e diferença = 998.

Fixture pública `academic-memory-v1`; origem **Memória**, intervalo 2024.1–2026.2.
38 cenários entre Todos os departamentos, SINT-A, SINT-B e SINT-VAZIO, incluindo
seleções individuais, múltiplas e combinação das cinco dimensões. **2.612 registros:
2.553 Confere, 59 Ausente em ambas, nenhuma divergência.** Cada registro contém
cenário, população, filtros, período, curso/total, fonte, versões, snapshot do
conteúdo, esperado, obtido, diferença e situação. Inclui diferenças/percentuais
entre pontos, calculados a partir da referência independente.

Exemplos efetivamente observados, sem filtros acadêmicos adicionais:

| Cenário / período | População | Esperado | Obtido | Diferença | Situação |
|---|---|---:|---:|---:|---|
| Todos os departamentos / 2024.1 | Matriculados | 6 | 6 | 0 | Confere |
| Todos os departamentos / 2024.1 | Bolsistas matriculados | 2 | 2 | 0 | Confere |
| Todos os departamentos / 2025.1 | Formados | 2 | 2 | 0 | Confere |
| Todos os departamentos / 2026.2 | Ingressantes | 6 | 6 | 0 | Confere |
| SINT-A / 2026.2 | Matriculados | 16 | 16 | 0 | Confere |
| SINT-A / 2026.2 | Bolsistas matriculados | 5 | 5 | 0 | Confere |
| SINT-B / 2026.1 | Formados | 1 | 1 | 0 | Confere |
| SINT-VAZIO / 2024.1 | Matriculados | ausente | ausente | não calculável | Ausente em ambas |

Hashes do conteúdo lido, suficientes para distinguir esta fixture da receita PG:

| Recorte | SHA-256 |
|---|---|
| Todos os departamentos | `cbcca6418681c006709cbee9c4d611267fb9ffa0e8635952de629cda65ea4c18` |
| SINT-A | `f1302bc55615ff8745ffd11df754c700a0f7864f69285cd7287d6386424f1736` |
| SINT-B | `9c33f5bddf702ae1cd99324caef31dec22231b7677c64eadfa466459cb143565` |
| SINT-VAZIO | `34bef8673c0b7bd0d1d154225a5628a13c7215a665b817f34b1b0b79fcc35416` |

O arquivo completo é gerado pelo teste
`test_fixture_all_individual_and_combined_filters_against_sql`, em
`<basetemp>/test_fixture_all_individual_an0/conciliacao-offline.json`.
Artefato local ignorado pelo Git; os casos, SQLs, comandos e este resumo são versionáveis.

## Leitura PostgreSQL preparada; aceite humano posterior

Rotina `vrac.dev.student_reconciliation`, exclusiva do desenvolvedor. Usa a
configuração segura existente, loopback, banco/conta sintéticos, TLS `verify-full`,
validação de metadados e `REPEATABLE READ`. Reutiliza o leitor existente e executa
as duas referências SQL fechadas **na mesma conexão/transação**, inclusive entre
departamentos. Cada referência usa savepoint; falha na referência de bolsas não
apaga a conferência das outras três curvas.

SQLs em `sql/synthetic_demo/reconcile_students_*.sql`: fragmento comum de recorte,
contagens, bolsas e identificação do snapshot. Filtros são parâmetros vinculados,
incluindo seleções JSON; nenhum SQL vem da tela. A rotina percorre os departamentos
disponíveis e cenários individuais/combinações, total e curso, até 100 cenários por
recorte. Conserva os limites/timeouts do leitor e do banco existentes.

**Somente Matheus/desenvolvedor**, com a base existente já disponível:

```powershell
.\.venv\Scripts\python.exe -m vrac.dev.student_reconciliation --execute --output .cache/prompt4a-postgres
```

Sem `--execute`, exibe ajuda e termina sem conexão. Exige pasta nova e não
sobrescreve evidências. Grava `conciliacao.json` e, quando há registros,
`conciliacao.csv`, com valores esperados/obtidos, diferenças, pendências, limites,
horários UTC, versão, hashes dos SQLs de produção/referência e snapshot PostgreSQL.
Retorno 0 indica comparações concluídas; 1 indica divergência/pendência; 2 indica
falta da opção explícita ou saída já existente/indisponível.

Não inicia nem recria cluster, não executa carga, não lê configuração institucional
e não alterna para memória. Falha de conexão gera registro sanitizado de pendência,
sem exceção bruta ou credenciais. Não contornar erro de certificado; Matheus deve
tratar a disponibilidade pelo procedimento existente fora desta conferência.
O registro anterior de certificado ausente não foi reavaliado nesta tarefa.

**Limitação de bolsas:** a projeção existente liga bolsa a pares distintos de
matrícula/departamento do histórico, **sem período nessa relação**. Matrícula em
mais de um departamento pode projetar a mesma bolsa em ambos. A interseção com
elegíveis no ponto e a deduplicação não comprovam vigência departamental histórica;
não foram inventadas datas nem reconstruídas transferências.

## Testes, arquivos e próximos responsáveis

Testes novos em `test_student_reconciliation.py` e `test_student_ui.py` complementam
os existentes: duplicidades/conflitos, ingresso futuro/nulo/desconhecido, menor
ingresso fora dos filtros acadêmicos, exceção literal de dupla diplomação, bolsas
repetidas/ausentes, FR/TD versus HF, ausência versus zero, base zero, cursos
semelhantes separados e combinação de filtros. Conferidos os valores das quatro
linhas Matplotlib, lacunas, conteúdo dos CSVs/manifesto e os bytes PNG/CSV no ZIP.
AppTest confere filtros em tabela e remoção de resultados/downloads por alteração
de cada filtro acadêmico, intervalo, Centro/Departamento e falha de atualização.

Execução offline pertinente:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_student_reconciliation.py tests/test_student_ui.py tests/test_academic_analyses.py tests/test_academic_reader.py tests/test_academic_ui.py tests/test_postgres_demo_reader.py tests/test_department_hierarchy.py tests/test_department_hierarchy_ui.py tests/test_analysis_contracts.py tests/test_analysis_references.py tests/test_workflows.py --basetemp=.cache/pyt-4a-verified -q -p no:cacheprovider --tb=short
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

**128 testes aprovados em 143,66 s** na rodada pertinente acima. Na revisão final,
a gravação do CSV de conciliação passou a bytes para evitar `CR` duplicado no
Windows. Depois dessa alteração e do teste de codificação/ausências/proteção contra
fórmulas: **11 testes de referência aprovados em 27,76 s**, comando abaixo.
A rodada pertinente não foi repetida após esse ajuste específico. Ruff aprovado
e 73 arquivos já formatados; `git diff --check` aprovado.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_student_reconciliation.py --basetemp=.cache/pyt-4a-csv-final -q -p no:cacheprovider --tb=short
```

Resultado consolidado das execuções em [STATUS](../STATUS.md). Rodada intermediária
teve uma falha no novo teste por import ausente; corrigido e teste reexecutado.
Nenhuma falha foi encoberta como resultado aprovado.

Arquivos deste incremento: `src/vrac/analyses/academic.py`,
`src/vrac/db/synthetic_postgres.py`, `src/vrac/dev/student_reconciliation.py`,
quatro `sql/synthetic_demo/reconcile_students_*.sql`, os dois arquivos de teste
acima e documentação: este guia, `ANALISES_SINTETICAS.md`, `STATUS.md`, `PLAN.md`,
`PROJECT_CONTEXT.md`, `PROXIMOS_PASSOS.md`, `DECISIONS.md`, `ANALYSIS_CATALOG.md`,
`operations/SYNTHETIC_SOURCE_MAP.md`, `operations/SYNTHETIC_POSTGRES.md` e o índice.
Outras alterações locais preexistentes não são entregas deste incremento.

**Não executados pelo agente:** leitura/conciliação PostgreSQL, teste institucional, revisão
manual no navegador de download/responsividade, suíte integral do repositório,
homologação visual/funcional, autenticação ou publicação. A parcela offline não
comprova leitura efetiva PostgreSQL; a conclusão da 4a incorpora a declaração
posterior de Matheus, sem afirmar execução/inspeção adicional pelo agente.

Matheus confirmou validação/conciliação e acompanha eventuais divergências; Talita revê
clareza, filtros, uso e arquivos. DSI/DBA tratam fontes físicas, mapeamentos,
privilégios e conferência institucionais **somente na etapa final e deploy**.
Relação Centro > Departamento na origem PG continua ausente. Formação e bolsas
conservam os limites descritos. Não se pede nova aprovação geral das fórmulas.
**Incremento 4a encerrado no escopo sintético por aceite de Matheus; 4b é a próxima
tarefa. Nenhuma implementação da 4b ou publicação nesta atualização.**
