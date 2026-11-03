# Mapa lógico e representação sintética — R01–R06

Revisão de 03/11/2026, Prompt 2. Catálogo `phase2-synthetic-map-v5`.
Aplica D-022/D-027/D-028. Este é o mapa dos contratos existentes, sem novo
modelo de dados ou implementação de análises. O [catálogo](../ANALYSIS_CATALOG.md)
resume o uso e as lacunas por roteiro.

## Alcance e evidência

Complemento Prompt 3 — 03/11/2026: R01 também expõe distribuição por departamento
como **linhas com matrícula**, mesma unidade documental da categoria, diferente
do cartão/quadro distintos. R02 compara departamentos com matrículas distintas
e denominador geral próprio de cada unidade, preservando o geral do recorte.
Não somar unidades com matrícula sobreposta para reconstruí-lo. R03 sinaliza
Parcial quando faltam competências (7/5 meses), com total distinto separado das
pilhas por quadro. `FacultySource.real_hours_available` distingue indisponibilidade
da fonte de ausência/nulo no detalhe R01; a composição cadastral segue calculada.
Nenhuma fórmula R04–R06 ou projeção SQL foi alterada. [Detalhes e testes](../guides/PROMPT3_DOCENTES.md).
Sem nova observação PG nesta tarefa; evidência exclusivamente offline.

| Camada | Significado e estado nesta revisão |
|---|---|
| Conceito lógico | Pessoa, vínculo, competência, matrícula acadêmica, curso, carga e vigência usados nos cálculos abaixo |
| Representação sintética | Projeções `vrac_sintetico.analysis_*`, filtros `demo_*` e saídas SQL já existentes. Mapeadas por código/receita; testes offline conferidos conforme [STATUS](../STATUS.md) |
| Fonte institucional | **Pendente para a etapa final em todas as linhas deste mapa.** Nenhuma tabela, campo, chave, cardinalidade, unidade ou cobertura real confirmada |
| Conferência PostgreSQL desta revisão | **Não executada.** Psycopg preparado offline; leitor tentou conexão com `verify-full` e falhou por arquivo de certificado local ausente. Não houve leitura de registros, fallback, recriação de cluster ou alteração de TLS |

As projeções neutras são a interface sintética efetivamente referenciada pelos SQL
versionados. A expansão delas para nomes internos permanece nas receitas locais
`scripts/connect-synthetic-app.local.py` e `scripts/prepare-academic-analyses.local.py`.
Não copiar essa expansão para o dicionário institucional ou para arquivos públicos.
As duas consultas R01 já contêm seu mapeamento no repositório; este mapa usa seus
aliases de saída. Credenciais/configuração privada não foram abertas.

Convenções das tabelas seguintes:

- **D:** restrição explícita no DDL gerado/revisado, sem nova introspecção do servidor.
- **F:** convenção ou observação da receita com semente `20261030`, avaliada offline;
  não garante o conteúdo da instância PostgreSQL instalada.
- **C:** regra de consulta/contrato/cálculo existente; não cria PK, FK ou unicidade.
- **PG:** observação nesta instância PostgreSQL. **Nenhuma nesta revisão.**

O gerador [semantic_postgres.py](../../src/vrac/dev/semantic_postgres.py), função
`render_seed`, cria as 13 tabelas de origem sem PK/FK/UQ e com colunas anuláveis.
Views não acrescentam restrições de unicidade. Ausência de nulos na receita não
significa `NOT NULL`. As exceções D são os metadados e os dois suplementos abaixo.
Todos os nomes e tipos nesta página se referem exclusivamente à simulação.

## Entradas dos roteiros e filtros

| Roteiro / finalidade | Entradas reutilizáveis | Unidade e referência efetiva | Filtros e limites |
|---|---|---|---|
| R01 / situação geral | `RegisterRow` e `RealHoursRow`, `load_faculty_source`, `compute_overview` | Total/quadro: matrículas funcionais distintas; categoria: linhas com matrícula. Cadastro **atual**; horas no maior semestre **por vínculo** | Departamento atual; quadro, categoria, situação e dupla função. Não é foto histórica. Valores do filtro salvo de quadro do painel ausentes |
| R02 / geral e QP | Cadastro R01 em `AcademicSource.faculty.register`, `calculate_qp` | Matrículas funcionais distintas do cadastro atual; participação em % | Categoria; `qp_cadres` define só o numerador, sem reduzir geral. QP institucional ausente; grupo configurável é simulação |
| R03 / presença semestral | `analysis_history` → `HistoryRow`, `calculate_history` | Pessoas distintas na união de competências; janeiro–julho / agosto–dezembro | Departamento **histórico**, intervalo, situação A, lotes 3/4/7, exclusão A4 e seis quadros de `HISTORICAL_CADRES`; categoria recorta população. Filtro de quadro seleciona séries, preserva total |
| R04 / carga e alocações | `analysis_workloads`, `analysis_allocations`, `analysis_simulation_policy` | Horas por vínculo no **semestre único escolhido**, não máximo individual. Diferença em horas e razão em % somente na simulação compatível | Departamento da carga no semestre, quadro e categoria; alocações dos vínculos elegíveis. Categoria vem do cadastro atual, não é categoria histórica comprovada |
| R05 / funções | Cadastro R01, `analysis_functions`, `analysis_appointments`, política | Dupla função atual; eventos mensais no intervalo; vigências que o interceptam. Linhas de evento, vínculos distintos e pares sobrepostos são unidades separadas | Departamento atual para eventos, departamento do suplemento para atos; quadro/categoria via cadastro. Sem cadastro, eventos podem seguir sem esses filtros; com eles, resultado bloqueado |
| R06 / quatro séries acadêmicas | `analysis_students`, `analysis_student_history`, `analysis_scholarships` | Matrículas acadêmicas distintas por período/curso; não pessoas únicas | Departamento do curso; intervalo, códigos de curso, habilitação, turno, nível, forma de ingresso. Sem filtro de processo seletivo ou equivalência automática |

Os filtros SQL de `academic_*.sql` vinculam `department`; aceitam um departamento
ou o valor fechado `Todos os departamentos`. As consultas R01 leem separadamente
cada departamento. Os filtros de período e demais dimensões são aplicados no
cálculo após a leitura. O leitor não recebe SQL arbitrário.

## Fontes, linhas, chaves e cobertura

### Docentes

| Fonte lógica / representação sintética | Linha, chaves e deduplicação | Temporalidade, cobertura e limites | Evidência |
|---|---|---|---|
| Departamento / `demo_departments.department` | Uma sigla por centro da receita; F: 4 valores distintos. Não há PK/UQ na fonte. A sigla é opção da demonstração, não chave institucional | Três departamentos com dados e `SINT-VAZIO`; opção usada em todos os roteiros | `departments.sql`; receita de conexão; `_options` |
| Calendário de opções / `demo_periods.period` | `DISTINCT` dos semestres da fonte dedicada, convertido de `AAAAS` para `AAAA.S`. Unicidade da saída por C | F: seis opções, 2024.1–2026.2. Não garante cobertura mensal, acadêmica ou completude do semestre | `periods.sql`; receita de conexão; `_periods` |
| Vínculo e cadastro atual / saída `faculty_register.sql` → `RegisterRow` | Uma linha cadastral por vínculo na F: 25, com `registration` e `registration_int` únicos observados offline. `person_key` representa 24 pessoas. Sem PK/FK/UQ D. R01/R02 deduplicam **matrícula textual**, não pessoa; R01 categoria preserva linhas | Departamento atual; não filtra ano/semestre. Campos cadastrais incompletos não impedem as demais métricas. Pessoa não é exibida; chave opaca serve a avisos de múltiplos vínculos | `faculty_register.sql`; `RegisterRow`; `compute_overview`; `test_overview_counts_registrations_and_preserves_missing_classification`, `test_duplicate_register_rows_follow_each_visual_aggregation` |
| Horas dedicadas do cadastro / saída `faculty_real_hours.sql` → `RealHoursRow` | Uma linha de origem por vínculo/semestre na F: 150; par (`registration_int`, `semester`) único **na receita**, sem UQ D. C: agrupa vínculo, escolhe máximo semestre e soma valores conhecidos desse ponto; não elimina linhas por suposta duplicidade | R01 lê todos os semestres dos vínculos do departamento atual. Horas repetidas nas linhas mensais da prévia não entram nesse cálculo. Maior semestre não é atualização da fonte | `faculty_real_hours.sql`; `current_real_hours`; `test_real_hours_use_latest_semester_per_registration_without_summing_semesters` |
| Histórico funcional / `analysis_history` → `HistoryRow` | Uma competência/vínculo/lote. F: 905 linhas; (`registration`, `reference_date`, `payroll_batch`) sem repetição nessa receita, não é PK D. C: contagem por `person_key` distinta em cada semestre e quadro; detalhe mantém lotes e vínculos | Lotação e quadro da competência; uma competência individual ausente e múltiplos lotes intencionais. Contagens mensais ou por quadro não somam pessoas do semestre. Sem identidade ou data, registro não entra na contagem | `academic_history.sql`; `HistoryRow`; `calculate_history`; `test_history_unions_people_and_keeps_overlapping_cadres_and_july_calendar` |

### Carga

| Fonte lógica / representação sintética | Linha, chaves e deduplicação | Temporalidade, cobertura e limites | Evidência |
|---|---|---|---|
| Carga dedicada / `analysis_workloads` → `WorkloadRow` | Uma linha de horas dedicada, enriquecida com categoria cadastral por vínculo. F: 150 linhas, (`registration`, `semester`) único; sem UQ D. C: soma Horas Reais por vínculo no semestre escolhido; contratada exige um único valor conhecido, sem somar repetições | Departamento da carga do semestre, quadro da carga, categoria atual. Zero e nulo presentes. Se a junção cadastral multiplicar linhas, a soma pode inflar; receita evita isso, banco não impõe | `academic_workloads.sql`; `WorkloadRow`; `calculate_workload`; `test_workload_uses_dedicated_rows_not_allocations_and_blocks_base_zero_ratio` |
| Alocação / `analysis_allocations` → `AllocationRow` | Uma alocação vínculo/semestre/disciplina/turma. F: 42 linhas; composto (`registration`, `semester`, `discipline`, `class_id`) único, sem PK D. Duas alocações podem compartilhar turma. C: **preserva linhas**, não rateia nem deduplica por turma | Lotação do vínculo obtida da carga do mesmo semestre; departamento da oferta separado. Vagas zero/nulas e classificação nula. Currículo e grupo de compartilhamento ausentes. Nunca alimenta Horas Reais | `academic_allocations.sql`; `AllocationRow`; `calculate_workload`; teste de carga acima |
| Política de simulação / tabela `analysis_simulation_policy` → `SimulationPolicy` | D: PK `singleton`, `CHECK singleton=1`; flags booleanas `NOT NULL` e `CHECK` verdadeiras; textos de unidade anuláveis. C: leitor aceita exatamente uma linha; contrato ignora singleton | Sem vigência institucional. Unidades iguais `h/semana (simulação)` e atos sintéticos são convenções suplementares. Sem política válida, não presume compatibilidade | `academic_policy.sql`; `SimulationPolicy`; receita acadêmica local; `calculate_workload` |

<a id="funcoes"></a>

### Funções

| Fonte lógica / representação sintética | Linha, chaves e deduplicação | Temporalidade, cobertura e limites | Evidência |
|---|---|---|---|
| Registro de função / `analysis_functions` → `FunctionRow` | Uma linha de evento mensal, F: 60. Identificador de movimento da fonte é único na receita, sem UQ D, e **não é projetado**; não existe chave de linha garantida no contrato. C: conta linhas e matrículas distintas separadamente; não deduplica (`registration`, `year`, `month`, `role`) | Departamento atual do vínculo e departamento de distribuição distintos. Ano/mês da ocorrência; mês inválido excluído do cálculo. Gratificação/descrição/papel não comprovam natureza administrativa. Valores financeiros não são selecionados | `academic_functions.sql`; `FunctionRow`; `calculate_functions`; `test_function_evidence_and_simultaneity_do_not_follow_gratification_or_dual_flag` |
| Vigência com evidência / tabela `analysis_appointments` → `AppointmentRow` | D: PK `evidence` (não nula), prefixo `SYN-ATO-`; departamento, matrícula, papel, início e flag administrativa `NOT NULL`; fim anulável, `CHECK` fim ≥ início. Nenhuma FK D. F: 5 atos por primeiro vínculo de cada um dos 3 departamentos com dados, 15 atos | Intervalos fictícios; 4 atos administrativos e 1 acadêmico por vínculo. C: seleciona `administrative`, recorta interseção de vigências e compara pares de papéis distintos por matrícula. Papéis sucessivos não são simultâneos | `academic_appointments.sql`; `AppointmentRow`; receita acadêmica local; teste de funções acima |

<a id="matriculas"></a>

### Matrículas

| Fonte lógica / representação sintética | Linha, chaves e deduplicação | Temporalidade, cobertura e limites | Evidência |
|---|---|---|---|
| Cadastro acadêmico / `analysis_students` → `StudentRow` | Uma última situação por matrícula na F: 120; `registration` único na receita, sem PK/UQ D. C: agrupa por matrícula para menor ingresso conhecido e menor período FR/TD; não conta linhas como pessoas | Estado atual/último estado gerado; ingresso e período são distintos. Dá o limite de ingresso à série histórica e a população de formados. Não substitui a situação de cada semestre | `academic_students.sql`; `StudentRow`; `calculate_students`; `test_student_series_deduplicate_apply_future_entry_and_keep_own_populations` |
| Situação acadêmica por período / `analysis_student_history` → `StudentRow` | Uma situação observada da matrícula no período; F: 408 linhas, 407 pares matrícula/período; um par tem duas situações. **Par não é chave única**, nem a fixture o trata assim. C: conjuntos de matrícula por curva/período/curso após elegibilidade | F: seis períodos, saída após formação/abandono em alguns casos. Sem linha no período não é zero. Departamento/curso são os da situação. Transferência e renomeação não criam equivalência | `academic_student_history.sql`; `StudentRow`; teste de séries acima; `test_unknown_entry_does_not_become_zero_and_course_filters_do_not_merge_courses` |
| Bolsa por matrícula/período / `analysis_scholarships` → `ScholarshipRow` | Uma linha de concessão/competência projetada em matrícula/período, enriquecida com departamento histórico. F: 354 linhas, 132 pares; 222 linhas adicionais intencionais; par **não é chave de linha**. C: usa existência do par em conjunto, sem junção multiplicadora de fatos | Departamento vem de pares distintos matrícula/departamento de **todo** o histórico, sem vigência na junção. F: um departamento por matrícula; mudanças de departamento podem ampliar a projeção. Bolsa só conta com matrícula elegível no mesmo período | `academic_scholarships.sql`; `ScholarshipRow`; `calculate_students`; teste de séries e `test_student_base_zero_and_missing_scholarship_only_affect_their_metrics` |

## Dicionário dos campos projetados

Tipos abaixo vêm do dicionário usado pelo gerador e dos casts das receitas, **não de
introspecção PG**. `bigint` chega como `int`, `integer` como `int`, `text` como `str`,
timestamp como `datetime`, date como `date`. As anotações `float | None` dos contratos
de carga também recebem os inteiros desta receita, sem conversão de unidade.
Todos os campos das origens básicas permitem SQL `NULL` por D; transformações e
junções podem produzir nulos adicionais. Os contratos não validam DDL.

| Contrato / campos | Significado, tipo e transformação sintética | Nulabilidade, unidade ou limitação |
|---|---|---|
| `RegisterRow.department`, `registration`, `registration_int` | Departamento atual `text`; matrícula textual `text`; chave de ligação numérica `bigint`, campos da consulta R01 | F: não nulos; equivalência texto/número só é convenção da receita (sem zeros à esquerda) |
| `RegisterRow.person_key` | `md5` do identificador **fictício** textual, preservando nulo; saída `text` | Identidade de pessoa para aviso de múltiplos vínculos, sem exibição; não é anonimização aprovada para dados reais |
| `RegisterRow.name`, `cadre`, `category`, `status`, `dual_role` | Campos cadastrais `text`, sem inferência; quadro, cargo/categoria, descrição da situação, S/N | F: preenchidos. Nome não é chave; dupla função não é natureza administrativa |
| `RegisterRow.extraordinary`, `degree` | Vínculo extraordinário e titulação, `text` | F: todos nulos; filtros/análises não inventam valores |
| `RegisterRow.weekly_hours`, `tenure_years` | Carga semanal e tempo de casa, `bigint` | Unidades cadastrais horas/semana e anos, sem conversão. F: tempo de casa todo nulo; carga não confirma unidade de Horas Reais |
| `RealHoursRow.registration_int`, `semester`, `hours`, `cadre` | Vínculo `bigint`, semestre `bigint` no formato `AAAAS`, horas `bigint`, quadro `text` da fonte dedicada | F: 6 horas nulas, zero em dois vínculos da mesma pessoa a cada semestre. Unidade institucional desconhecida; R01 não aplica conversão |
| `HistoryRow.department` | `text`, sigla obtida da relação entre competência e centro | Departamento **histórico**, não cadastro atual |
| `HistoryRow.person_key`, `registration`, `reference_date` | Hash `md5` com nulo preservado; vínculo `text`; referência `timestamp without time zone` | Pessoa não se confunde com matrícula; timestamp de competência não é data de extração |
| `HistoryRow.cadre`, `category`, `status`, `payroll_batch`, `leave_code` | `text`: quadro/cargo vigentes, situação, lote, afastamento ajustado | F: 869 afastamentos nulos e 36 A4; nulo não é A4 e passa pela condição Python `!= 'A4'`. Não presumir regra de ausência institucional |
| `WorkloadRow.department`, `registration`, `semester` | Departamento da fonte de horas `text`; vínculo numérico convertido para `text`; semestre `bigint` | Semestre da carga, distinto da foto cadastral e da competência mensal |
| `WorkloadRow.name`, `cadre`, `category` | Nome/quadro da carga `text`; categoria `text` do cadastro por `LEFT JOIN` | Categoria pode faltar se não houver cadastro; não reconstrói cargo histórico |
| `WorkloadRow.real_hours`, `contracted_hours` | `bigint`, valores independentes da fonte dedicada | F: reais têm 6 nulos e zeros; contratadas preenchidas. R04 usa unidade da política, sem extrapolar para instituição |
| `AllocationRow.department`, `teaching_department`, `registration`, `semester` | Lotação do vínculo da carga `text`; oferta `text`; vínculo numérico convertido a `text`; semestre `bigint` | Junção vínculo + semestre; lotação e oferta não intercambiáveis |
| `AllocationRow.discipline`, `class_id`, `shared`, `classification` | `text`, código de disciplina, chave textual de turma/semestre gerada, S/N e classificação da origem | F: `class_id` inclui período, disciplina e turma; não presumir isso na instituição. 6 classificações nulas; S/N não identifica grupo compartilhado |
| `AllocationRow.allocated_hours`, `vacancies_filled` | `bigint`, carga atribuída por disciplina e vagas preenchidas | F: 6 vagas nulas e 6 linhas com zero. Vagas não são alunos únicos; unidade da alocação não foi homologada nem equiparada à carga dedicada |
| `FunctionRow.department`, `distribution_department`, `registration`, `description`, `role` | `text`: departamento atual, sigla do centro de distribuição via `LEFT JOIN`, vínculo, descrição e papel | Anuláveis na origem; distribuição pode faltar. Não há campo de valor financeiro no contrato |
| `FunctionRow.year`, `month` | Texto de ano/mês convertido por cast SQL para `integer` | F: valores válidos; texto inválido falha na fonte de funções, sem afetar outras leituras |
| `AppointmentRow.department`, `registration`, `role`, `evidence`, `administrative` | `text`, `text`, `text`, `text` e `boolean`; campos suplementares fictícios | D: não nulos. `evidence` é PK, não prova institucional; flag distingue ato administrativo do acadêmico |
| `AppointmentRow.start`, `end` | Datas `date`, vigência explícita suplementar | D: início não nulo; fim pode ser nulo (aberto). C: fim inclusivo, começo do período seguinte exclusivo |
| `StudentRow.registration` (cadastro e histórico) | `bigint`, matrícula acadêmica | F: não nula; contagem distinta da matrícula, sem chave de pessoa na entrada do cálculo |
| `StudentRow.department`, `course`, `course_name` | `text`, departamento do curso, código e descrição; aliases distintos de origem convergem no contrato | F: 3 cursos, um por departamento. Código filtra/separa séries; nome não une cursos |
| `StudentRow.qualification`, `shift`, `level`, `status`, `entry_kind` | `text`, habilitação (descrição), turno, nível, situação e forma de ingresso | F: preenchidos. Filtros usam valores projetados, não identificadores institucionais inventados |
| `StudentRow.entry_period`, `period` | `bigint` no formato `AAAAS`; ingresso versus período da situação | Anuláveis D. No cadastro, período é o último gerado; no histórico é o ponto da situação. Ingresso ausente afeta matriculados/bolsistas, sem virar zero |
| `ScholarshipRow.registration`, `period` | Matrícula `bigint`; chave de período `double precision` convertida por SQL para `bigint` | F: chaves integrais; cast não comprova validade de futuros decimais. Departamento só filtra SQL; não integra `ScholarshipRow` |
| `SimulationPolicy.real_hours_unit`, `contracted_hours_unit` | `text`, ambos `h/semana (simulação)` nesta receita | D: anuláveis; só diferença/razão dependem de igualdade explícita e `synthetic_units=True` |
| `SimulationPolicy.synthetic_units`, `synthetic_appointments` | `boolean`, flags suplementares verdadeiras | D: `NOT NULL` e checks; contrato vazio usa `False` e unidades `None`, nunca inventa metadados |
| `dataset_metadata.synthetic`, `version`, `seed` | `boolean`, `text`, `bigint`, identidade da fixture | D: não nulos; `CHECK synthetic`; sem PK/singleton D. C: leitor exige uma linha com versão esperada |
| Saída de `metadata.sql`: `database_name`, `role_name`, `transaction_read_only`, `ssl` | `text`, `text`, `text`, `boolean`, calculados pelo servidor para a sessão | C: leitor exige banco/conta esperados, leitura `on` e SSL verdadeiro; sem inferir atualização ou privilégio de escrita pela resposta |

## Relações e risco de multiplicação

São relações **da receita de demonstração**, não relações institucionais confirmadas.
As cardinalidades F foram calculadas sobre as linhas geradas, antes de instalar SQL;
nenhum teste de cardinalidade foi executado no PostgreSQL nesta revisão.

| Relação / finalidade | Junção e cardinalidade F/C | D, risco e tratamento |
|---|---|---|
| Pessoa → vínculos (R01/R02/R03) | F: 24 → 25; uma pessoa com dois vínculos. Mesma identidade fictícia gera mesmo hash entre cadastro e histórico | Sem PK/FK D; não juntar por nome. R01/R02 contam vínculo; R03 pessoa |
| Competência → departamento histórico (R03) | Junção interna pela chave de centro da receita; F: 905 → 905, nenhum órfão ou múltiplo destino | Sem UQ/FK D. Centro repetido multiplica histórico, ausente remove linha. Contagem distinta pode esconder multiplicação; detalhe não |
| Cadastro → Horas Reais (R01) | Semijunção `IN` por vínculo numérico do cadastro; F: 25 vínculos → 150 linhas de horas | Não é junção por pessoa; `IN` evita multiplicação por cadastro repetido. Horas repetidas são somadas conforme medida, não descartadas |
| Carga → cadastro para categoria (R04) | `LEFT JOIN` pelo vínculo numérico; F: 150 → 150, máximo 1 destino | Sem UQ/FK D; duplicação de cadastro pode inflar soma de reais. Carga sem cadastro preservada com categoria nula |
| Planejamento → carga do semestre (R04/prévia) | Junção interna vínculo **e semestre**; F: 42 → 42, todos com um destino | Sem UQ/FK D; carga duplicada multiplica alocações, ausente as remove. Não unir somente pela matrícula |
| Evento de função → cadastro (R05) | Junção interna pela matrícula textual; F: 60 → 60, um destino por evento | Sem UQ/FK D; cadastro repetido multiplica eventos e altera contagem de linhas; evento sem cadastro não aparece na view |
| Evento → departamento de distribuição (R05) | `LEFT JOIN` pela chave de centro de distribuição; F: 60 → 60, um destino | Sem UQ/FK D; centro repetido multiplica, centro ausente mantém nulo. Não usar distribuição como lotação |
| Ato → vínculo (R05) | Suplemento guarda matrícula textual; C: teste de pertencimento ao conjunto cadastral, ou conjunto de evidências se cadastro indisponível e sem filtros | Sem FK D. PK do ato não garante vínculo existente. Combinações de atos podem produzir vários pares por vínculo; total de simultâneos usa matrículas distintas |
| Cadastro acadêmico → histórico (R06) | F: 120 matrículas → 408 situações, 407 pares matrícula/período. C: mapa de menor ingresso por matrícula e conjuntos por curva, sem junção de fatos | Sem PK/FK D; duas situações no mesmo período não viram dois matriculados. Não eliminar arbitrariamente uma situação conflitante |
| Bolsa → matrícula/departamento do histórico (R06) | View liga bolsa a pares `DISTINCT` matrícula/departamento, sem período. F: só um departamento por matrícula; 354 → 354 | Sem FK D; matrícula em dois departamentos replica linhas da bolsa. Distinção do par matrícula/período impede contagem dupla, mas cobertura temporal por departamento fica limitada |
| Matriculados → bolsas (R06) | C: semijunção lógica por (`registration`, `period`), 354 registros → 132 pares de bolsa na F | Não somar bolsas ou percentuais. Intersectar com elegíveis do período e curso; ausência da fonte afeta só bolsistas |
| Curso → séries (R06) | C: agrupa por código; nenhuma junção por nome ou mapa de equivalência instalado | Cursos e programas não são equiparados. Pessoa com várias matrículas pode contar várias vezes; total é recalculado, não soma de pessoas ou estoques |

## Populações, ausências e dependências por resultado

| Resultado | Regra C e deduplicação | Zero, nulo, ausência/falha e lacuna específica |
|---|---|---|
| R01 total/quadro/categoria | Matrículas não vazias; total e quadro distintos, categoria por linha | Cadastro vazio/filtro sem linhas retorna `empty_source`/`empty_filters`, total `None`. Quadro/categoria nulos aparecem como Não informado. Filtro salvo do painel não conhecido |
| R01 horas/semáforo | Soma dos valores conhecidos no máximo semestre do vínculo; status único das linhas desse ponto | Zero é Sem alocação; todas as parcelas nulas → nulo; nenhuma linha → ausência. Mistura de parcelas nulas/conhecidas soma conhecidas, sem inventar parcela. Semáforo literal por nomes reconhecidos; `PROF *` não é convertido em `PRINCIPAL` |
| R02 QP/demais/participação | Geral distinto; grupo selecionado; desconhecidos fora do grupo; participação só com classificação completa, grupo selecionado e geral positivo | QP configurável é simulação. Sem grupo ou classificação completa, métricas dependentes ficam indisponíveis; geral permanece. Base zero não gera percentual |
| R03 presença | União de pessoas elegíveis por semestre; meses observados contam cobertura de fonte, não presença de cada docente | Sem observações → `None`; observações sem elegíveis → zero. Cobertura incompleta gera aviso (7/5 meses esperados); estado global Calculado não garante cobertura completa de cada pessoa. Nulo de afastamento não equivale a afastado |
| R04 horas e comparação | Agrupa vínculo no semestre; soma conhecidas; contratada apenas se um valor conhecido distinto; indicador único por grupo | Todas nulas → `None`; soma com parcela nula é marcada Parcial no detalhe; nenhuma linha não é zero. Conflito contratual bloqueia comparação daquele vínculo. Unidade incompatível/ausente bloqueia diferença/razão; contratada zero bloqueia razão. Alocações não corrigem reais |
| R05 três evidências | Dupla função S atual; linhas de eventos no intervalo; atos administrativos que interceptam intervalo; pares com papéis distintos sobrepostos | Cadastro, função e ato não são equivalentes. Ato inexistente não comprova ausência administrativa institucional. Sem fonte, a métrica correspondente fica `None`/Parcial; com filtros cadastrais e sem cadastro, R05 bloqueia |
| R06 matriculados (B-M-035) | `MT/MC` no histórico do ponto; matrícula não nula; menor ingresso **do cadastro lido, sem filtros de curso/habilitação** ≤ ponto; conjunto de matrículas | Sem histórico/cadastro, sem observação ou ingresso desconhecido de candidato → `None`; observação sem elegíveis → zero. Não transforma cadastro atual em histórico |
| R06 bolsistas (B-M-038) | Interseção de matriculados elegíveis com existência de bolsa matrícula/período | Fonte de bolsas ausente bloqueia só a curva; nenhuma bolsa elegível com população observada → zero |
| R06 formados (B-M-036) | Cadastro filtrado FR/TD; menor período por matrícula no recorte; detalhe por código aplica seu próprio recorte, como seleção individual; HF não acrescentado | Depende do cadastro atual e da condição de observação usada em `count_at`; não reconstrói todos os eventos históricos de formação. Total recalculado, sem somar cursos. Falta de cadastro afeta formados, matriculados e bolsistas |
| R06 ingressantes (B-M-070) | Histórico filtrado: ingresso = ponto e (período = ponto ou forma `Dupla Diplomacao`); matrícula distinta | População independente da bolsa/formação; sem histórico bloqueia esta curva. Sem observação nem candidato → `None` |
| R06 variação | Só matriculados entre pontos consecutivos disponíveis: atual − anterior; percentual = diferença/base × 100 | Base zero → percentual `None`, razão Base zero. Base/atual ausente → diferença e percentual `None`. Não soma estoques nem aplica equivalências por nome |

Os estados da implementação (`FacultyOverview`, `CalculatedAnalysis`) são os usados
na tela. Os contratos lógicos anteriores (`AnalysisRequest/Result`, `WorkflowRequest/Result`)
continuam disponíveis para validação/serialização, mas **não são o adaptador de execução**
dos seis cálculos. `plan_workflow()` e `blocked_result()` conservam respostas de preparação,
incluindo `adaptador_nao_implementado`; não consultar esses planos para concluir que os
executores `compute_overview`/`calculate` estão ausentes. `phase3_blockers(...,
mode=DataMode.SYNTHETIC)` não cobra pendências institucionais; o padrão real continua
bloqueado. Nenhuma dessas funções libera acesso real.

Históricos alternativos de cargo/carga, planejamento corrente e horários também
existem na carga original, mas não são entradas dos seis executores atuais. Não
foram criadas junções adicionais para completar conceitos que os leitores não usam.

## Leitura, proveniência e prévia existente

[synthetic_postgres.py](../../src/vrac/db/synthetic_postgres.py) fixa loopback, banco,
conta `vrac_sintetico_reader`, TLS `verify-full`, timeout e transação somente leitura
com `REPEATABLE READ`. Valida versão/semente sintética, identidade, SSL e modo de
transação com [metadata.sql](../../sql/synthetic_demo/metadata.sql). Isso complementa,
sem substituir, os privilégios preparados na conta. Não foi testada escrita.
Consultas retornam no máximo 5.001 linhas para detectar excesso do limite de 5.000;
filtros têm limite de 1.000. Estouro não publica um resultado truncado.

`load_academic_source` lê cadastro, horas e os oito componentes em savepoints
independentes no mesmo snapshot de sua chamada. `available` distingue uma fonte
lida vazia de fonte indisponível; `errors` registra mensagens sanitizadas. Não há
fallback de PostgreSQL para `academic_fixture.load_fixture`. A memória é uma
seleção explícita para testes/demonstração e **não reproduz todos os valores da
receita PostgreSQL**.

| Prévia existente / finalidade | Granularidade e campos | Risco e evidência |
|---|---|---|
| `demo_faculty` → `FacultyRecord` / tabela de registros | Departamento histórico, período `text`, competência `YYYY-MM`, pessoa fictícia `teacher_id`, matrícula `contract_id`, quadro `employment_type` (`text`); `real_hours` (`bigint`, anulável) | Histórico liga centro por chave e horas por vínculo+semestre (`LEFT JOIN`). Pode repetir horas semestrais em meses/lotes; não somar. Pessoa fictícia aqui não recebe hash; nunca reutilizar como proteção para origem real. `faculty.sql`, receita de conexão, `test_records_keep_months_zero_null_and_bound_filters` |
| `demo_allocations` → `TeachingAllocation` / detalhe de prévia | Departamento do vínculo e da oferta, período `text`, pessoa fictícia, `class_id`; `allocated_hours` e `students` (`bigint`, anuláveis); `classification` (`text`); `curriculum_id`/`sharing_id` = `NULL::text` | Planejamento liga cadastro por vínculo numérico e carga por vínculo+semestre; sem PK/FK D, risco multiplicador de ambos. F: 42 linhas e chaves de alocação descritas acima, sem deduplicação C. `students` é alias de vagas, não pessoa distinta. `allocations.sql` |

A versão/semente vem dos metadados; `AcademicSource.fingerprint` identifica o conteúdo
lido e filtros/exportações preservam esse snapshot. Tempo de carregamento/execução
não é atualização da origem. Não há data de atualização por fonte na receita nem
garantia de reconstituição histórica após mudanças. A R01 própria e a aba por período
podem vir de chamadas diferentes: cada chamada tem seu snapshot, não há promessa de
transação única entre abas.

## Evidências e reprodução

**Prompt 4a — 03/11:** [registro R06](../guides/PROMPT4A_MATRICULAS.md) distingue
2.612 comparações offline na fixture/SQLite de conferência PostgreSQL não executada.
Rotina manual `vrac.dev.student_reconciliation --execute` reutiliza o corpo do
leitor existente (`_read_academic_source`) e referências SQL fechadas na mesma
conexão/transação REPEATABLE READ; não inicia/recarrega banco. Comparação total/curso,
filtros e snapshots são registrados. Matheus confirmou posteriormente nesta conversa
“tudo validado por mim e conciliado”, encerrando a 4a sintética; sem nova execução
PostgreSQL pelo agente ou inspeção de relatório adicional. Limite temporal de bolsas por departamento
permanece; agora explícito também nos avisos da R06 e suas exportações.

As referências de SQL desta página estão em [sql/synthetic_demo](../../sql/synthetic_demo/).
Contratos: [academic_data.py](../../src/vrac/analyses/academic_data.py),
[faculty_overview.py](../../src/vrac/analyses/faculty_overview.py).
Cálculos: [academic.py](../../src/vrac/analyses/academic.py).
Fixtures em memória: [academic_fixture.py](../../src/vrac/analyses/academic_fixture.py) e
[faculty_overview_fixture.py](../../src/vrac/analyses/faculty_overview_fixture.py).
Os testes citados estão em [test_academic_analyses.py](../../tests/test_academic_analyses.py),
[test_faculty_overview.py](../../tests/test_faculty_overview.py) e
[test_postgres_demo_reader.py](../../tests/test_postgres_demo_reader.py); isolamento de
falhas em [test_academic_reader.py](../../tests/test_academic_reader.py).

Nesta máquina, a avaliação da receita foi feita com
`.\.venv\Scripts\python.exe .cache/prompt2-map/profile_fixture.py`; resultado agregado
em `.cache/prompt2-map/fixture-profile.json`. Script/relatório são locais, ignorados,
contêm o vínculo detalhado com as origens internas e não integram a distribuição.
Não foi instalado DDL ou carga durante esta revisão. `check_mapping.py` no mesmo
diretório tentou usar as consultas/leitores existentes e parou na conexão; **não
produziu relatório de verificação PostgreSQL**. A classificação auxiliar identificou
certificado ausente sem imprimir erro bruto ou conteúdo privado.

Comandos versionados reutilizáveis, offline:

```powershell
.\scripts\check.cmd
.\.venv\Scripts\python.exe -m vrac.analyses
```

A recuperação futura da fixture segue [SYNTHETIC_POSTGRES.md](SYNTHETIC_POSTGRES.md),
preservando `verify-full` e somente leitura no aplicativo. Após restaurar o ambiente
local, repetir as leituras de R01–R06 e registrar PG separado de F. Não interpretar
os testes com mocks como leitura do servidor.

## Lacunas e reutilização pelo Prompt 3

O Prompt 3 poderá reutilizar os contratos/leitores/SQL fixos, a R01 já implementada,
as fixtures e seus testes, além das chaves/granularidades/filtros deste mapa.
Não depende do Prompt 1 real nem de nova aprovação geral de fórmulas. Esta tarefa
não executou o Prompt 3, não alterou telas/exportações e não publicou a aplicação.

Permanecem específicas: filtro salvo de quadro da R01, composição institucional de QP,
unidades de carga comparáveis, natureza administrativa e vigências reais, identidade
de aluno único, equivalências de cursos e filtro de processo seletivo. Cobertura
interdepartamental da simulação e siglas de departamentos não confirmam cobertura
autorizada real. Compartilhamento sem chave e TCC sem classificação permanecem
indeterminados. Certificado sintético ausente limita somente a conferência viva.

O [dicionário institucional](SANITIZED_DATA_DICTIONARY.md) continua **não preenchido**.
Matheus/DBA tratarão fontes, chaves, tipos, unidades, temporalidade e escopo real
somente na etapa final; DSI/time tratarão acesso/autenticação. Talita poderá avaliar
uso e limitações da entrega no incremento solicitado, sem reaprovar fórmulas
documentadas. Nenhuma dessas pendências bloqueia o Prompt 3 sintético.
