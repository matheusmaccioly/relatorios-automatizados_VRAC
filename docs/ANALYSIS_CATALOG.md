# Catálogo de análises e regras — Prompt 2

**Implementação sintética atual (D-027, 30/10/2026):** R01–R06 disponíveis na aplicação,
com cálculos, gráficos, tabelas, conferências e exportações. O
[guia dos roteiros](guides/ANALISES_SINTETICAS.md) descreve regras e limites. Os estados
de aprovação e fontes físicas do catálogo abaixo continuam históricos/institucionais;
não bloqueiam os executores sintéticos nem declaram integração real aprovada.
O grupo QP, unidades compatíveis e atos administrativos suplementares são simulações
explicitamente identificadas. Nenhuma nova regra institucional foi inventada.

**Diretriz vigente em 30/10/2026 (D-022): reproduzir os cálculos dos dashboards
existentes conforme a documentação disponível, sem nova validação das regras.**
Matheus dispensou a revalidação analítica; as exigências históricas de aprovação
abaixo não devem ser cobradas novamente para regras já documentadas. Lacunas ou
contradições concretas devem ser registradas no resultado afetado, sem criar regras.
Os estados `pending` dos contratos existentes ainda refletem a preparação anterior;
não foram alterados nesta tarefa documental e não representam nova exigência humana.
O dicionário físico continua não preenchido e a conectividade não foi comprovada.
Testes técnicos e controles de segurança permanecem aplicáveis. Nenhum cálculo ou
fase 3 foi implementado nesta atualização.

A definição estruturada fica em [config/analyses.yaml](../config/analyses.yaml).
Campos de fonte física permanecem `null`; nomes de fontes/chaves são conceitos propostos,
não nomes SQL confirmados. O documento interno `docs/ANALISE_MODELOS_SEMANTICOS_VRAC.md`
foi lido a pedido de Matheus e preservado. Seus nomes semânticos, tipos declarados e
referências foram organizados em `config/semantic_model_sources.local.yaml`: 12 tabelas,
399 definições de colunas, qualificadas por modelo. Ambos ficam excluídos do Git e do
contexto Docker e não são carregados pela aplicação. A documentação original restringe
publicação; sua colocação local não constitui liberação para GitHub.

O catálogo empacotável contém conceitos, limites e IDs de evidência. Seu carregamento
e os testes funcionam sem esses dois arquivos locais. Mapeamento físico, credenciais e
dados reais seguem o [dicionário sanitizado](operations/SANITIZED_DATA_DICTIONARY.md).

## Revisão da base semântica — 27/10/2026

As nove variantes abaixo são evidências do legado, não nove análises novas. Todas têm
seleção institucional `null`; nenhum resultado real foi liberado. `SemanticVariant`
vincula modelo, referências, fonte lógica, unidade, base temporal e limites. O loader
recusa modelo fora do escopo, referência cruzada entre modelos, fonte desconhecida,
unidade incompatível, variante duplicada e escolha sem aprovação completa.

| Análise / modelo | Variantes documentadas | Consequência para a definição |
|---|---|---|
| Docentes / A | Pessoas no contexto (A-M-028); pessoas por unidade histórica/RLS (A-M-029/034); matrículas funcionais na última referência por matrícula (A-M-017/018); matrículas no último mês global (A-M-027) | Pessoa e vínculo têm unidades distintas; contexto e referência temporal precisam acompanhar a comparação |
| Matrículas / B | Cadastro atual (B-M-033); situação por período com limite de ingresso (B-M-035); última situação por matrícula e coorte (B-M-049); população final de trajetória (B-M-127/128) | A situação por período é candidata para evolução histórica, sujeita a revisão; as outras populações não a substituem |
| Horas Reais / A | Fonte dedicada no maior semestre do contexto (A-M-009/010) | Unidade da variante permanece `null` até confirmação; verificar unicidade antes de reproduzir a soma documental |

Pontos que alteram a base das análises:

- Docentes: confirmar chave opaca de pessoa; a identificação pessoal usada pelo legado
  não será copiada para código nem exportações. Há múltiplos lotes de folha. Departamento
  atual, departamento histórico e unidade de RLS exigem distinção. O calendário encontrado
  inclui julho no primeiro semestre; outra expressão histórica usa regra diferente.
  Não transportar calendário ou desempate textual sem revisão.
- Matrículas: todas as quatro candidatas documentais contam matrículas acadêmicas,
  sem comprovação de pessoa única. Não herdar cobertura do calendário de bolsas nem
  conversão de ausência para zero. Mapas de programa/transferência não aprovam equivalência
  de curso. Prefixo de medida nova não comprova preferência institucional.
- Carga: maior semestre selecionado não comprova semestre civil corrente ou atualização.
  Planejamento, horas contratuais e Horas Reais permanecem separados. Os dois planejamentos
  do modelo A são distintos; há relação muitos-para-muitos bidirecional com horários.
  Objetos homônimos entre A e B não autorizam junção automática.
- A inspeção não executou Power Query/M, DAX ou RLS. Relações inativas, filtros
  bidirecionais e tabelas desconectadas usadas por medidas precisam de revisão. O modelo C
  de projetos/financeiro permanece fora da implementação.

Os contratos distinguem identificadores de matrícula funcional e acadêmica, unidades
de pessoa e matrícula, base de contagem docente e bases temporais. A solicitação também
pode registrar `semantic_variant_id`; a comparação de referências recusa outra variante
ou outro recorte temporal mesmo quando os números coincidem. A presença desse ID não
executa nem aprova uma variante. O padrão docente anterior continua sendo pessoas.

## Prioridade e significado

### Roteiros detalhados solicitados em 28/10/2026

A especificação local `docs/ROTEIROS_ANALISES_VRAC.local.md` detalha o uso das famílias
abaixo em seis roteiros: situação geral, geral e QP, histórico semestral, carga,
dupla função e funções administrativas, e o gráfico geral de alunos. Os critérios
de dupla função, gratificação e cargo administrativo permanecem distintos até
aprovação de natureza e vigência. As quatro séries acadêmicas têm populações
próprias; os totais docentes exigem identidade e referência temporal compatíveis.

O documento e `docs/EVIDENCIAS_PAINEIS_VRAC.local.json` são internos, locais e
excluídos de Git/Docker. A implementação complementar do Prompt 2 associa os seis
roteiros às famílias em `config/analyses.yaml`, versão `phase2-workflows-v4`, preservando
as nove variantes sem seleção institucional. Os contratos em
[workflows.py](../src/vrac/analyses/workflows.py) contêm somente conceitos lógicos,
sem objetos físicos, expressões legadas ou carregamento dos arquivos internos.

| Roteiro | Contrato proposto | Fase do cálculo |
|---|---|---|
| R01 | Foto geral, distribuição por quadro e categoria | 3 |
| R02 | Geral, QP confirmado, classificação pendente, demais e participação | 3 |
| R03 | Presença semestral com departamento histórico | 3, incremento a revisar |
| R04 | Horas Reais, contratada, comparação e indicador separados | 4b |
| R05 | Dupla função, registro de função e confirmação administrativa separados | Encaixe pendente |
| R06 | Matriculados, bolsistas matriculados, formados e ingressantes independentes | 4a |

`WorkflowRequest` recebe pontos `AnalysisRequest` e métricas de uma lista fechada.
Exige filtros de escopo compatíveis, referências sem sobreposição, mesma unidade,
modo e filtros em toda a série. O período vem com datas explícitas: não há calendário
civil presumido. R01/R02 usam uma única foto. R02 recusa filtro global de quadro para
preservar o denominador; a seleção comparativa de QP dependerá de regra aprovada.
Filtro de processo seletivo continua indisponível até validar propagação (V20).

`plan_workflow()` expõe as dependências de cada métrica. `WORKFLOW_DECISIONS` registra
as 24 perguntas e responsáveis, todas pendentes. V22/V23 bloqueiam execução real;
V24 permanece critério de apresentação institucional. Nenhum plano executa cálculo.
Os cinco registros de aceite por família continuam sendo a evidência exigida para
passagem de fase; IDs de dependência não são uma segunda forma de liberar acesso.

`WorkflowResult` contém um `MetricResult` por métrica/período, com proveniência e
versões preservadas em `AnalysisResult`. Uma curva pode estar bloqueada e as demais
válidas, produzindo resultado geral parcial. Toda métrica solicitada exige estado
explícito; nenhuma ausência vira zero. Percentual conclusivo de QP exige geral
positivo, QP compatível e classificação completa. Versões do app e do template e
marca sintética acompanham a serialização. Não é uma exportação para planilha.

Os testes novos verificam esses contratos, bloqueio real, isolamento de curvas,
denominador QP, datas, filtros e serialização. Não executam as regras T01–T38 por
inteiro: cálculos docentes, funções, bolsas, ingresso, conclusão e cargas continuam
nas fases indicadas. Fixtures não aprovam regra institucional.

| Ordem / identificador | Pergunta e população proposta | Granularidade e unidade | Estado |
|---|---|---|---|
| 1 · `composicao_docente` | Docentes distintos do departamento e distribuição por vínculo; população depende de situação/vigência/afastamento aprovados | Pessoa é distinta de vínculo e registro temporal. Saída proposta por departamento/período/categoria; unidade: docentes distintos | Fonte, base temporal, classificação e referência pendentes |
| 2 · `evolucao_matriculas` | Evolução por curso/período; definir se conta matrícula/inscrição ou aluno único e quais situações entram | Matrícula, aluno, componente, curso e programa são conceitos distintos. Unidades alternativas: matrículas ou alunos distintos; percentual derivado somente após regra aprovada | Unidade, situações, equivalências e apresentação percentual pendentes |
| 3 · `carga_horaria` | Horas Reais oficiais e alocação detalhada dos docentes com cobertura autorizada | Medida oficial e detalhe por turma/currículo em visões separadas. Unidade semanal ou semestral deve ser confirmada por medida | Fonte oficial, unidade, cobertura e arredondamento pendentes |

Cada entrada YAML registra pergunta, população, granularidade, unidade, fontes lógicas,
referência física, chaves lógicas, parâmetros, filtros, fórmula descritiva, exceções,
período, responsável, versão, comparação e status. Cinco áreas de decisão precisam
de evidência humana: fonte, granularidade, cálculo, comparação e aceite funcional.
Todas permanecem `pending`; teste ou edição de flag não equivale a aprovação.

## Composição docente: primeira definição a aprovar

- **Pessoa x registro:** contar pessoas distintas depende da chave institucional de
  pessoa e do recorte. Vínculos, disciplinas e meses podem multiplicar linhas.
- **Foto x presença no semestre:** a foto requer data explícita; presença em qualquer
  mês requer recorte temporal explícito. São indicadores diferentes. Somar contagens
  mensais não produz uma contagem semestral de docentes distintos.
- **Departamento:** selecionar o departamento do vínculo quando essa for a regra
  aprovada; o departamento da disciplina é outra referência e não o substitui.
- **Distribuição por vínculo:** uma pessoa pode ter mais de um vínculo/categoria.
  Definir classificação exclusiva ou explicar sobreposição. Não somar categorias
  como se fossem partição antes dessa decisão.
- **Exceções:** vigências, afastamentos e situações precisam vir de fonte confiável.
  Não tratar início/fim de cargo como contratação/desligamento.

Nenhuma destas propostas autoriza deduplicação arbitrária ou mudança da métrica oficial.

## Matrículas e equivalências de cursos

A fórmula proposta de variação absoluta é quantidade atual menos anterior. O percentual
será `100 × diferença / anterior` somente quando a base for conhecida e não zero.
Uma base zero produz estado **não calculável**, não percentual zero. Ausência de linha,
erro e período incompleto exigem aviso próprio. Nenhum cálculo dessa série é executado
nesta fase; o critério de apresentação percentual continua pendente.

`EntityKey` diferencia departamento do vínculo, departamento da disciplina, departamento
do curso, curso e programa. A identidade usa tipo e identificador, sem comparação por
nome. Alteração de nome não cria automaticamente um curso novo, e nomes semelhantes
não autorizam unir identificadores diferentes.

O contrato `CourseEquivalence` e o [modelo documental](../config/course_equivalences.example.yaml)
registram curso de origem/destino, início/fim de vigência, fonte e versão, status,
responsável, data e evidência da revisão. O plano de séries mantém cursos separados
quando faltar equivalência aprovada que cubra **todo** o período, quando houver
sobreposição ambígua ou cadeia/ciclo não revisados. Não agrega números de matrícula.
Mapas sintéticos nunca se aplicam em modo real.

## Carga horária: medidas e pendências

Horas Reais devem ser obtidas da fonte oficial aprovada. Detalhamento planejado por
disciplina não é seu substituto. Não somar esse detalhe para corrigir o indicador,
inferir compartilhamento ou ratear horas sem regra/identificador confiável.

Horas semanais e semestrais são unidades distintas: a lista no catálogo apresenta
possibilidades a confirmar, não uma conversão autorizada. Não presumir número de semanas.
Atuação interdepartamental depende de cobertura; turmas sem alunos dependem de data de
matrícula e exceções; tipificação ausente permanece ausência, sem inferir TCC pelo nome.
Cada pendência bloqueia ou limita somente o resultado afetado, sem mascará-la como zero.

## Solicitação, resultado e proveniência

Os contratos em `src/vrac/analyses/contracts.py` não dependem de Streamlit ou conexão:

| Contrato | Conteúdo |
|---|---|
| `AnalysisRequest` | Análise da lista fechada, período com datas e completude, filtros tipados, modo de dados, base temporal/data de foto e unidade de matrícula |
| `MetricDatum` | Métrica, unidade, valor, situação do dado e dimensões; variação absoluta é identificada separadamente da quantidade total |
| `SourceReference` | Fonte lógica, versão, extração e atualização próprias; não contém credenciais, servidor ou connection string |
| `AnalysisResult` | Solicitação efetiva, UUID, criação, dados, unidades, origens, versões de catálogo/regra/consulta, avisos e situação `valido`/`parcial`/`bloqueado` |

Períodos recebem datas explícitas; não há calendário institucional presumido. Nulo,
zero observado, ausência de registros, não calculável e falha têm estados distintos.
Contagens são inteiros; horas/percentuais usam `Decimal`, serializado como texto para
preservar precisão. Variação absoluta pode ser negativa; total negativo não é aceito
pelo contrato proposto. Exceções oficiais futuras exigem revisão da definição.

Um resultado bloqueado não carrega números. `blocked_result()` não consulta fontes,
não calcula nem usa fallback; registra extração/atualização desconhecidas como `None`,
em vez de inventar datas. A data de criação da execução não é extração da fonte.
Resultados reais válidos/parciais continuam recusados pelos contratos nesta fase,
mesmo que alguém modifique flags do catálogo. Não existe adaptador de análise real.

## Referências e critérios de comparação

O [modelo de referência](../config/reference_case.example.yaml) não contém números
institucionais ou aprovação fabricada. `ReferenceCase` vincula expectativa ao pedido,
versão da regra e datas/versões de cada origem, com identificação sintética explícita.
Referências institucionais aprovadas exigem agregados autorizados e registro de revisão
humana; uma fixture não pode receber aceite funcional humano.

`compare_reference_case()` exige o mesmo recorte, regra e situação válida, além de
origens com versão/atualização compatíveis. Mudança da data de extração, isoladamente,
não prova mudança da origem. Atualização desconhecida ou diferente bloqueia a comparação
automática; investigar a referência sem ajustar a origem para um relatório antigo.

| Valor | Critério |
|---|---|
| Contagem inteira | Igualdade exata; tolerâncias absoluta e relativa zero, sem parâmetro para relaxá-las |
| Horas | Comparação bloqueada até registrar casas decimais, modo de arredondamento, responsável, data e evidência; nenhuma tolerância padrão presumida |
| Percentual | Critério de apresentação/comparação ainda pendente; base zero nunca é valor numérico |
| Nulo, ausência ou falha | Não comparar como zero; situação bloqueada/não comparável |

O arredondamento de teste é marcado sintético e não vale para fonte real. Uma comparação
que coincide não altera status de aprovação. Logs, datas e versões não garantem reprodução
histórica exata se a fonte foi corrigida sem snapshot autorizado.

## Casos sintéticos e conferência offline

`synthetic_contract_cases()` produz sete casos determinísticos: registros repetidos de
pessoa, valor nulo, zero observado, ausência de linhas, semestre parcial, denominador
zero e fontes com datas de extração/atualização distintas. As expectativas são declarações
de fixtures, sem implementar cálculos das análises e sem aprovação institucional.

```powershell
.\scripts\bootstrap.cmd --sqlserver
.\scripts\check.cmd
.\.venv\Scripts\python.exe -m vrac.analyses
```

O extra SQL Server apenas mantém disponíveis os testes opcionais da fase 1; o catálogo
da fase 2 não precisa dele. PyYAML foi acrescentado para ler o YAML com construtores
seguros, rejeitando chaves duplicadas e escopo desconhecido. Catálogo inválido não executa
análise. A referência do parser é a [documentação oficial do PyYAML](https://pyyaml.org/wiki/PyYAMLDocumentation).

## Decisões curtas para validação humana

**Talita, começando por composição docente:**

1. Aprovar pessoa ou matrícula funcional e referência temporal entre as variantes
   documentadas; confirmar calendário, incluindo julho, e tratamento de empates.
2. Definir categorias de vínculo, sobreposição, afastamentos e exclusões.
3. Fornecer caso agregado autorizado do mesmo recorte/regra/data para contagem exata.
4. Para os próximos módulos, escolher a população acadêmica e confirmar unidade,
   unicidade e arredondamento das horas.

**Responsável pelos dados/DBA, com Matheus:**

1. Liberar dicionário sanitizado com fontes lógicas, granularidade, chaves e cardinalidades;
   manter o mapeamento físico privado externo e confirmar a leitura autorizada.
2. Documentar datas de atualização, cobertura, situações, unidades, nulos e exceções.
3. Confirmar fonte oficial de Horas Reais, compartilhamentos/classificação e equivalências
   de cursos vigentes com aprovação; não deduzir relações ausentes.

Somente após registrar fonte, granularidade, fórmula, comparação e aceite funcional humano
uma análise poderá avançar à implementação real. Matheus autorizou condicionalmente
o Prompt 3 nesta solicitação. A condição ainda depende de identidade, população,
referência, regra e caso de comparação docente aprovados. `phase3_blockers()` expõe
as pendências; nenhuma fase é avançada automaticamente. Esta entrega não altera a
tela nem aplica branding, não publica e não acessa o banco.
