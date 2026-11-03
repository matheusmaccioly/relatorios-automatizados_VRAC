# Prompt 4b · conferência da carga sintética

Registro de 03/11/2026, sob D-022/D-027/D-028. **Parcela offline conferida;
PostgreSQL ainda pendente de execução explícita por Matheus.** Não há aceite
humano da 4b, homologação visual ou conciliação institucional. O aceite da 4a
continua registrado em [PROMPT4A_MATRICULAS.md](PROMPT4A_MATRICULAS.md).

## Regras e correções

R04 usa o semestre único do filtro, fonte dedicada e soma somente valores conhecidos
por matrícula funcional. A contratada é o único valor conhecido distinto; conflito
impede apenas a comparação do vínculo. Diferença é real menos contratada; razão é
real/contratada × 100, não variação. Zero na contratada só impede a razão. Política
deve estar disponível e habilitada, com unidades preenchidas e iguais. Unidades
sintéticas da receita: `h/semana (simulação)` para ambas; a execução real da rotina
registra os valores efetivamente lidos. Não há unidade declarada para alocações;
não há conversão nem confirmação institucional.

Corrigida a propagação da cobertura parcial: parcela nula junto de valor conhecido
já marcava o detalhe como parcial, mas o estado e o total poderiam parecer completos.
Agora também ficam parciais. Política indisponível ou unidade apenas com espaços
não libera comparação. O valor conhecido e demais análises são preservados.
Avisos informam origem atual da categoria, unidades e limitações das alocações.

Indicadores preservam os textos e limites de A-CC-007 por linha; estados diferentes
produzem **Indicadores distintos**, sem recalcular sobre a soma. `PROF PRINCIPAL`
não é convertido para `PRINCIPAL`. Rótulos não indicam produtividade ou contratação.
Ausência de registros não vira zero; todas as parcelas nulas continuam nulas.

As alocações são outra tabela, selecionada por vínculo e semestre, com os dois
departamentos separados. Linhas compartilhadas são preservadas: S/N não identifica
grupo, não autoriza deduplicação por turma ou rateio. Currículo, grupo e classificação
ausentes não são inferidos. Vagas preenchidas não são alunos únicos. Vagas zero
permanecem com suas horas e são ponto de conferência; a fonte não fornece data de
matrícula nem exceções para decidir o significado do zero.

## Conciliação e cobertura

`reconcile_workload.sql` calcula a referência independente por vínculo a partir
da projeção dedicada, com filtros vinculados e `SUM`/`COUNT` próprios. O teste
executa o SQL adaptado em SQLite em memória contra a fixture pública: isso verifica
aritmética e recortes, **não** PostgreSQL ou suas views. Também verifica que uma
alteração artificial no obtido é detectada. O relatório inclui cenário, vínculo,
medida, filtros, semestre, fonte, hash do conteúdo, esperado, obtido, diferença e
situação. Contagens e comparações numéricas são exatas nesta rotina; não há tolerância
ajustável. Precisão/arredondamento de horas institucionais seguem não definidos.

Exemplos offline de teste: no semestre 2026.1, vínculo V1 com parcelas 10 e nula,
contratada 20 repetida: reais 10, diferença −10, razão 50%, cobertura Parcial e
indicadores distintos. Vínculo V3 com reais 4 e contratada zero: diferença 4 e
razão ausente. Vínculo V4 com contratadas 8 e 9: contratada e comparação ausentes.
Vínculo apenas no semestre 2026.2 fica ausente do recorte. Esses valores são
fixtures pequenas, não observações da instância.

As consultas de produção fazem `LEFT JOIN` da carga ao cadastro atual e `JOIN`
de alocação à carga por vínculo e semestre. Sem unicidade garantida, cadastro com
vários correspondentes pode multiplicar Horas Reais; várias parcelas de carga podem
multiplicar alocações. A rotina conta linhas antes/depois e relacionamentos múltiplos,
sem suprimir parcelas. Ausência de correspondência no recorte departamental pode
significar vínculo em outro departamento, não necessariamente perda global.
Os testes preservam duas alocações para departamentos distintos, uma vaga zero e
outra nula, compartilhamento e classificação ausente. A comparação de linhas de
alocação usa a fonte carregada, não uma segunda consulta independente à origem;
indicadores são conferidos por expectativas manuais offline, não por SQL independente.

Filtros usam departamento da carga, quadro da carga e categoria do cadastro atual.
Centro restringe departamentos apenas com relação explícita; PostgreSQL continua
com Centro não informado. A tabela existente apresenta os filtros efetivos; mudança
de filtro ou falha de atualização invalida resultados e downloads. Falha da fonte
dedicada bloqueia R04; falha de alocações preserva horas com aviso; PostgreSQL não
ativa memória silenciosamente. Cobertura interdepartamental está limitada às linhas
disponíveis na projeção sintética e à seleção de vínculos.

## Execução explícita pelo desenvolvedor

```powershell
.\.venv\Scripts\python.exe -m vrac.dev.workload_reconciliation --execute --output .cache/prompt4b-postgres
```

Requer pasta nova e base sintética existente. Sem `--execute` não conecta. Reusa
leitor, metadados, conta de leitura, TLS `verify-full`, transação `REPEATABLE READ`
e snapshot; não inicia, recria ou carrega banco. Analisa cada departamento, Todos,
semestres disponíveis, quadros/categorias e combinação, com limite de 500 cenários
por recorte. Arquivo `conciliacao.json` contém hashes SQL, referências, linhas
comparadas e auditoria de cardinalidade. Código 0 indica somente que as comparações
numéricas executadas e verificações de cardinalidade não apresentaram divergência;
1 indica pendência ou divergência; 2 indica falta de opt-in ou saída indisponível.
Não equivale a aceite integral: revisar indicadores, cobertura, alocações e limites.
Falha é sanitizada, não há fallback ou alteração de TLS. Não há evidência de execução
PostgreSQL neste incremento até que Matheus a execute e registre o resultado.

## Responsáveis e limites

Testes offline executados (sem rede nem PostgreSQL):

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_workload_reconciliation.py tests/test_academic_analyses.py tests/test_academic_reader.py tests/test_academic_ui.py tests/test_postgres_demo_reader.py tests/test_department_hierarchy.py tests/test_department_hierarchy_ui.py tests/test_workflows.py --basetemp=.cache/pyt-4b-final -q -p no:cacheprovider --tb=short
.\.venv\Scripts\python.exe -m pytest tests/test_workload_reconciliation.py tests/test_academic_reader.py tests/test_academic_ui.py --basetemp=.cache/pyt-4b-presentation -q -p no:cacheprovider --tb=short
.\.venv\Scripts\python.exe -m pytest tests/test_workload_reconciliation.py --basetemp=.cache/pyt-4b-version -q -p no:cacheprovider --tb=short
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

Resultados: 105, 35 e 21 testes aprovados, respectivamente; a terceira rodada ocorreu
após atualizar a versão de cálculo da R04. Ruff e formatação aprovados. Não foram
executados PostgreSQL, testes institucionais, suíte integral ou revisão visual manual.

Matheus executa a rotina e acompanha as diferenças, permissões e cardinalidade;
Talita revisa clareza e uso dos filtros, avisos e arquivos. DSI/DBA tratam fontes,
unidades, cobertura e integração institucionais somente na etapa final. A simulação
não comprova essas características. Não foi exigida nova aprovação geral das fórmulas.
Testes e estado da execução ficam em [STATUS](../STATUS.md).
