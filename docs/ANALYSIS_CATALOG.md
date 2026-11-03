# Catálogo de análises e regras — Prompt 2

Atualizado em 03/11/2026. R01–R06 estão implementados na demonstração sintética
(D-027). O Prompt 2 completou seu mapa e alinhou os estados. O Prompt 3 acrescenta
composição/comparação por departamento e gráficos web docentes, sem recriar os
cálculos R04/R05 nem alterar R06; [entrega e limites](guides/PROMPT3_DOCENTES.md).
As fórmulas documentadas são a referência vigente (D-022),
sem nova aprovação geral. Conexão, inventário e fontes institucionais permanecem
pendentes para a etapa final (D-028), sem bloquear desenvolvimento sintético.

A definição estruturada está em [config/analyses.yaml](../config/analyses.yaml),
versão `phase2-synthetic-map-v5`. O
[mapa lógico/sintético](operations/SYNTHETIC_SOURCE_MAP.md) detalha cada entrada,
campo, transformação, chave, granularidade, unidade, referência temporal, relação,
cardinalidade, nulabilidade, cobertura e evidência de consulta/contrato/teste.
O [guia de uso](guides/ANALISES_SINTETICAS.md) descreve a demonstração para Talita.

## Três camadas e estados

| Camada / campo | Estado e significado |
|---|---|
| Conceito lógico | Significado usado pelo cálculo: pessoa, vínculo, matrícula acadêmica, competência, curso, horas ou evidência administrativa |
| Representação sintética | Projeções e aliases de consultas já usados pelo leitor; mapa vinculado por `synthetic_mapping_reference` em cada família |
| `synthetic_status: implemented_offline_verified` | Implementado e conferido offline; **não** é declaração de leitura PostgreSQL nesta revisão |
| Conferência PostgreSQL em 03/11 | Não executada: leitor com TLS `verify-full` não encontrou o certificado local. Driver preparado offline, sem fallback ou alteração de TLS |
| `physical_source_reference: null` | Fonte **institucional** ainda não mapeada; não preencher com projeções da simulação |
| `selected_semantic_variant: null` e `validation_status: pending` | Seleção/validação institucional não registradas; não descrevem disponibilidade dos cálculos sintéticos nem exigem reaprovar fórmulas documentadas |
| Lacuna específica | Registrada abaixo com seu efeito limitado ao resultado correspondente |

DDL declarado, observação da receita offline e convenção do cálculo são distinguidos
no mapa. Nenhuma cardinalidade foi observada no servidor nesta revisão. As tabelas
básicas geradas não têm PK/FK/UQ; uma chave única na receita não vira restrição DDL.

Os mapeamentos detalhados para nomes internos continuam locais e ignorados, nas
receitas e em `config/semantic_model_sources.local.yaml`. Documentação semântica,
roteiros e inventário de visuais internos não foram copiados para este catálogo.
Os arquivos versionados funcionam sem esses materiais. O
[dicionário sanitizado institucional](operations/SANITIZED_DATA_DICTIONARY.md)
permanece modelo não preenchido.

## Seis roteiros disponíveis

| Roteiro / família | Regra e unidade efetivamente implementadas | Entradas e referência | Estado / lacuna específica |
|---|---|---|---|
| R01 / `composicao_docente` | Total e quadro: matrículas funcionais distintas; categoria/departamento: linhas com matrícula. Horas dedicadas, semestre e estado da fonte no detalhe | Cadastro atual; Horas Reais no maior semestre por vínculo. [Mapa docentes](operations/SYNTHETIC_SOURCE_MAP.md#docentes) | Implementado/conferido offline. Horas indisponíveis afetam somente seu detalhe. Valores do filtro salvo de quadro do painel ausentes; sem reconstrução histórica pelo intervalo |
| R02 / `composicao_docente` | Geral, grupo QP selecionado, classificação ausente, demais e participação; comparação por departamento; denominador geral preservado em cada recorte | Cadastro atual, categoria e seleção de quadros do grupo | Implementado/conferido offline. **QP configurável é convenção da simulação**; composição institucional pendente |
| R03 / `composicao_docente` | Pessoas distintas na união das competências; lotes 3/4/7, situação A, exclusão A4, seis quadros documentados | Histórico e departamento da competência; janeiro–julho / agosto–dezembro; categoria e séries por quadro | Implementado/conferido offline. Não soma meses ou quadros sobrepostos; cobertura parcial gera aviso |
| R04 / `carga_horaria` | Horas Reais da fonte dedicada, contratadas, distribuições e indicador literal; alocações em tabela separada | Semestre único escolhido; lotação da fonte de horas, categoria do cadastro atual. [Mapa carga](operations/SYNTHETIC_SOURCE_MAP.md#carga) | Implementado/conferido offline. **Unidades comparáveis são convenção sintética**; unidade institucional e chave de compartilhamento pendentes |
| R05 / `composicao_docente` | Dupla função atual, linhas de função, vínculos com evidência administrativa e sobreposição de papéis separados | Cadastro, eventos mensais e suplemento de atos/vigências no intervalo. [Mapa funções](operations/SYNTHETIC_SOURCE_MAP.md#funcoes) | Implementado/conferido offline. **Atos e vigências são fictícios**; gratificação e cargo não confirmam natureza administrativa |
| R06 / `evolucao_matriculas` | Quatro curvas de matrículas acadêmicas distintas: matriculados MT/MC; bolsistas elegíveis; formados FR/TD; ingressantes com exceção documentada de dupla diplomação | Histórico, cadastro atual e bolsas por matrícula/período. [Mapa matrículas](operations/SYNTHETIC_SOURCE_MAP.md#matriculas) | Implementado/conferido offline. Não é aluno único. Sem equivalência automática de curso nem filtro de processo seletivo |

**Prompt 4a — 03/11/2026:** [conferência R06](guides/PROMPT4A_MATRICULAS.md),
com 38 cenários/2.612 comparações offline sem divergência. Corrigido detalhe FR/TD
por código (mesmo recorte da seleção individual) e descrição de variação quando
atual ausente. Fonte de ingresso continua sendo o cadastro lido antes dos filtros
acadêmicos; bolsas por departamento sem vigência e formação pelo cadastro têm
limites explícitos. Referência SQL/leitor compartilham snapshot na rotina preparada;
conciliação posteriormente confirmada por Matheus nesta conversa (“tudo validado
por mim e conciliado”), encerrando a 4a sintética. Nenhuma nova execução PostgreSQL
pelo agente ou inspeção de relatório adicional. Não é conciliação institucional.

A prioridade das famílias continua docentes, matrículas e carga. A implementação
de funções não inclui valores financeiros nem decisões sobre pessoal. As variantes
documentais abaixo não são nove análises novas ou seleção automática de regras.

## Filtros efetivos

| Filtro | Aplicação |
|---|---|
| Departamento | Atual em R01/R02 e eventos de função; histórico em R03; da carga no semestre em R04; do curso em R06 |
| Intervalo inicial/final | Competências R03, eventos/vigências R05 e séries R06; não converte cadastro R01/R02 em foto histórica |
| Semestre da carga | R04 usa uma única referência explícita; R01 conserva o máximo por vínculo de sua medida |
| Quadro/categoria | Recorte docente; R03 preserva total e seleciona séries por quadro. QP seleciona só o grupo comparado |
| Situação/dupla função | Disponíveis na tela própria R01 |
| Curso | Código, sem unir por nome; totais e curvas recalculados, não soma de estoques |
| Habilitação, turno, nível, ingresso | Populações próprias R06; limite de ingresso de matriculados vem do cadastro lido, conforme código documentado no mapa |

SQL fixa departamento com parâmetros vinculados; demais filtros são aplicados pelos
cálculos sobre as entradas tipadas. Filtros/arquivos mostram origem e limitações.
Vagas preenchidas não são alunos únicos; departamento da oferta não é lotação.

## Ausências e lacunas com efeito limitado

| Situação | Comportamento existente |
|---|---|
| Zero observado | Mantido; por exemplo carga zero ou observação acadêmica com nenhum elegível |
| Nulo de campo | Preservado, sem virar zero. Soma dedicada usa parcelas conhecidas; R04 sinaliza parcela nula e contrato conflitante no detalhe |
| Nenhuma linha | Sem dados/lacuna; não comprova total zero nem ausência institucional de função |
| Fonte indisponível | Leitor registra erro sanitizado e remove sua disponibilidade; resultados independentes continuam. Sem bolsas, só bolsistas é afetado |
| Base zero | Variação percentual/razão não calculável; diferença absoluta acadêmica continua possível quando ambos os valores são conhecidos |
| Quadro/categoria desconhecidos | Não informado; sem inferir equivalência. Classificação QP incompleta impede participação conclusiva |
| TCC/classificação ou compartilhamento ausentes | Não inferir pelo nome, excluir horas ou ratear. Currículo e chave do grupo compartilhado não são criados |
| Equivalência de curso ausente | Séries separadas por código; `CourseEquivalence` exige vigência, fonte e revisão antes de eventual uso. Nenhum mapa está aplicado ao R06 |

Detalhes de preenchimento, deduplicação, filtros e dependências por curva estão nas
tabelas do mapa. Horas semanais/semestrais não são convertidas por número presumido
de semanas. Indicador literal não avalia produtividade ou necessidade de contratação.
Mudança de cargo não é contratação/desligamento.

## Contratos e execução que o Prompt 3 pode reutilizar

| Componente existente | Papel e limite |
|---|---|
| `RegisterRow`, `RealHoursRow`, `FacultySource` | Entradas R01, separando pessoa/vínculo e carga dedicada |
| `AcademicSource` e linhas de `academic_data.py` | Histórico, cargas, alocações, funções, atos, cadastro/histórico acadêmico, bolsas e política; disponibilidade por fonte |
| `load_faculty_source` / `load_academic_source` | PostgreSQL sintético somente leitura, TLS, identidade verificada, snapshot por chamada e limites; sem configuração institucional |
| `compute_overview` / `calculate` | Executores atuais usados na tela, testáveis sem Streamlit; `FacultyOverview` / `CalculatedAnalysis` são as saídas efetivas |
| `AnalysisRequest/Result` / `WorkflowRequest/Result` | Contratos lógicos anteriores com unidades, filtros, versões, datas, estados e serialização. Não são o adaptador de execução dos roteiros atuais |
| `plan_workflow()` / `blocked_result()` | Planejamento/preparação preservados; `adaptador_nao_implementado` não descreve os executores sintéticos atuais |
| `phase3_blockers(catalog, mode=DataMode.SYNTHETIC)` | Sem dependência documental institucional para Prompt 3 sintético. Padrão/`REAL` preserva bloqueios; não testa conexão nem libera acesso |

Identificadores lógicos de pessoa, matrícula funcional/acadêmica, departamento do
vínculo/da disciplina/do curso e programa continuam distintos. Períodos explícitos,
unidades, UUID, datas e proveniência dos contratos anteriores permanecem; números
reais válidos/parciais continuam recusados. Uma fixture não recebe aceite funcional
humano. Nenhum estado sintético autoriza adaptador real, login ou publicação.

## Evidência documental preservada

As nove variantes do YAML registram leituras diferentes dos modelos A/B, sem copiar
expressões ou nomes físicos restritos. Referência institucional continua pendente.

| Família | Variantes / evidências | Distinção preservada |
|---|---|---|
| Docentes | Pessoas no contexto (A-M-028); unidade histórica/RLS (A-M-029/034); última referência por matrícula funcional (A-M-017/018); último mês global (A-M-027) | Pessoa, vínculo, contexto, última referência e RLS não são intercambiáveis |
| Matrículas | Cadastro atual (B-M-033); situação por período com ingresso (B-M-035); última situação/coorte (B-M-049); população final de trajetória (B-M-127/128) | R06 usa as quatro medidas explicitadas no mapa; variantes não substituem suas populações |
| Horas Reais | Fonte dedicada no maior semestre do contexto (A-M-009/010) | R01 máximo por vínculo; R04 semestre escolhido. Não confirma unidade, unicidade institucional ou atualização |

Inspeção semântica não executou DAX, Power Query/M ou RLS nem comprovou DDL SQL.
Equivalências, auxiliares e relações muitos-para-muitos do modelo não são herdadas
automaticamente. Modelo C/financeiro permanece fora do escopo.

Os cinco registros `decisions` por família e V01–V24 conservam o histórico da
preparação. Os `pending` não constituem uma nova lista de aprovação analítica.
D-022 prevalece sobre as perguntas históricas de fórmula/população já documentadas;
D-027 autoriza os cenários sintéticos; D-028 adia a integração institucional.
Não promover essas flags a `approved` para liberar uma demonstração.

<a id="decisões-curtas-para-validação-humana"></a>

## Conferências e próximos responsáveis

Contagens de referência usam igualdade exata; não relaxar tolerância para fazer
coincidir. `compare_reference_case()` exige mesmo recorte/regra/unidade e versões
de origem compatíveis; extração diferente não comprova atualização. Horas reais
institucionais ainda exigirão precisão/arredondamento documentados, sem conversão
presumida. Aritmética sintética não equivale a conciliação institucional.

`synthetic_contract_cases()` mantém duplicidade, nulo, zero, ausência, semestre
parcial, base zero e datas distintas. As fixtures analíticas e seus testes já
cobrem os cálculos, bolsas repetidas, julho, funções e cargas separadas. Datas de
carregamento, execução e atualização de fonte são distintas; a última não está
disponível na receita. Resultados e comandos desta revisão estão em
[STATUS.md](STATUS.md).

```powershell
.\scripts\check.cmd
.\.venv\Scripts\python.exe -m vrac.analyses
```

O Prompt 3 reutilizou mapa, leitor R01, SQL, executores, fixtures e testes existentes,
sem executar o Prompt 1 real nem ler PostgreSQL nesta tarefa. Recuperar o certificado
da fixture é necessário para futura conferência viva, mantendo TLS; isso não é
requisito institucional nem pedido de credencial. Não foi iniciada essa recuperação.

Na etapa final, Matheus/DBA preencherão o mapeamento físico autorizado e conferirão
chaves, tipos, cobertura, unidades e resultados reais; DSI/time integrarão acesso e
autenticação. Talita avaliará uso e limites da aplicação nos incrementos solicitados.
Não se solicita reunião, inventário real ou nova aprovação geral de fórmulas agora.
