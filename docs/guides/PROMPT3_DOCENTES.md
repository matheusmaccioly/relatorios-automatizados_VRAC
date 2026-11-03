# Prompt 3 · Fechamento docente sintético — 03/11/2026

## Complemento solicitado pelas capturas — 03/11/2026

A aba **Análise docente** reúne a composição atual da R01, os dois gráficos
mensais da R03 e as listas de professores. Departamento e quadro usam barras
verticais lado a lado; categoria funcional usa barras horizontais abaixo.
Os valores ficam escritos nas barras e a cor vem do amarelo oficial selecionado
nos tokens, sem copiar a cor aproximada das capturas. As abas **Informações
gerais dos professores** e **CH Real dos professores em disciplinas** apresentam
os registros ordenados por nome; o detalhe mantém indicador, semestre, cargas,
titulação, tempo de casa, dupla função, vínculo extraordinário e estado da fonte.
O título do detalhe não altera a origem das Horas Reais: fonte dedicada no maior
semestre de cada matrícula, sem reconstrução pelas disciplinas.

Os filtros **Centro > Departamento** estão disponíveis na Análise docente e nas
Análises por período. Departamento oferece somente as unidades do centro escolhido;
**Todos os departamentos** reúne somente essas unidades. Trocar centro, departamento
ou outro filtro retira resultados e arquivos anteriores da respectiva consulta até
novo cálculo. As duas entradas mantêm consultas independentes; podem ser usadas
simultaneamente. A memória usa centros declaradamente fictícios; o leitor PostgreSQL sintético ainda não tem
mapeamento de centros e apresenta **Centro não informado**, sem inferir relações.

Se a atualização do histórico falhar, seu resultado e seus arquivos anteriores
são removidos, preservando a composição disponível. Intervalo inválido afeta
somente o histórico. Na memória, os filtros de período usam todos os semestres
da fixture acadêmica, independentes dos registros brutos da fundação.

As unidades e regras anteriores permanecem: R01 conta matrículas distintas no
cartão/quadro e linhas com matrícula em departamento/categoria; o histórico mensal
recalcula pessoas distintas por competência. Mês observado sem pessoa elegível é
zero; competência ausente permanece sem valor (`None`) e interrompe a linha.
Os gráficos são **Quantidade de professores ativos ao longo do tempo** e
**Professores ativos por quadro, semestre e mês**; o total é independente das
séries por quadro, que podem se sobrepor. O calendário docente continua janeiro–julho
no semestre 1 e agosto–dezembro no semestre 2; contagens mensais não são somadas
para reconstruir o total semestral. CSV/PNG/ZIP usam os mesmos resultados calculados.

Arquivos deste complemento, preservando as alterações anteriores:

| Grupo | Arquivos |
|---|---|
| Interface e apresentação | `src/vrac/ui.py`, `academic_ui.py`, `faculty_presentation.py`, `organisation_ui.py`, `web_charts.py` e `charts.py` no mesmo pacote |
| Hierarquia e leitura | `src/vrac/department_hierarchy.py`, `demo_data.py` e `db/synthetic_postgres.py` no mesmo pacote |
| Histórico mensal | `src/vrac/analyses/academic.py` |
| Verificação | `tests/test_department_hierarchy.py`, `test_department_hierarchy_ui.py`, `test_faculty_monthly.py`, `test_faculty_monthly_charts.py`, `test_faculty_page.py` e `test_faculty_presentation.py` na mesma pasta; regressões em `test_ui.py` e `test_faculty_completion.py` |
| Registro | Este guia, `docs/PROJECT_CONTEXT.md`, `docs/PLAN.md`, `docs/DECISIONS.md` (D-030) e registro final em `docs/STATUS.md` |

Uso deste complemento: abrir **Análise docente**, escolher Centro e Departamento,
quadro/categoria/situação/dupla função e o intervalo do histórico; clicar
**Calcular resultados**. Conferir a tabela de filtros e o cartão, os três gráficos
de composição, as abas de lista/CH Real e os dois gráficos mensais. Tabelas e
arquivos ficam nas respectivas exportações. O mesmo recorte pode ser consultado
em **Análises por período**, sem substituir a consulta da primeira aba.

Execução local sem banco: `.\scripts\run-demo.cmd --memory`. Verificação offline:
`.\scripts\check.cmd`. Consultar [STATUS](../STATUS.md) para as verificações
finais e os limites efetivamente registrados. A conferência visual no navegador foi bloqueada pela
ferramenta por não conseguir verificar a URL no Windows; não foram usados outros
mecanismos para contornar esse bloqueio. Não houve conexão a banco
nesta tarefa nem homologação visual. Matheus e Talita revisam o uso; Matheus e o
responsável institucional revisam a identidade. A relação de centros do PostgreSQL
permanece lacuna específica; DSI/DBA/time conferem a origem institucional na etapa
final. Não houve avanço de fase ou publicação. O restante deste guia preserva o
histórico do incremento anterior.

Escopo: composição, comparação e histórico R01–R03; apresentação dos resultados
existentes R04/R05. Sem incremento analítico de carga, alteração do roteiro R06,
conexão PostgreSQL/SQL Server, commit, publicação ou avanço de outra fase.
D-022/D-027/D-028 prevalecem sobre exigências históricas de nova aprovação geral.

## Lacunas conferidas antes da implementação

| Análise/referência | Implementação existente | Lacuna comprovada | Ajuste | Verificação |
|---|---|---|---|---|
| R01, visão geral | Cadastro, cartão, quadro, categoria, lista e CSV | Sem distribuição por departamento; tela de roteiros só mostrava quadro | Departamento, quadro, categoria e lista nas duas entradas; seleção individual de R01 | Duplicidade: total/quadro distintos; categoria/departamento contam linhas com matrícula; CSV |
| R02, comparação geral/QP | Conjuntos e denominador protegido | Sem tabela/gráfico entre departamentos | Mesmas contagens por departamento; participação no geral da própria unidade | Dois departamentos, múltiplos vínculos, repetição, classificação ausente, grupo não selecionado e ZIP |
| R03, evolução | União de pessoas no semestre e detalhe mensal | Gráfico estático; faltavam barras empilhadas; cobertura incompleta podia dizer Calculado | Total independente, pilhas por quadro com aviso de sobreposição e estado Parcial por competências faltantes | Julho, lotes repetidos, pessoa em dois quadros, meses ausentes e dados dos gráficos |
| R04/R05, referências individuais | Carga/indicador, eventos, vigências e tabelas | Gráficos da interface eram PNGs | Altair sobre as mesmas tabelas; PNG separado | Especificações, unidades e valores de cada série; testes analíticos existentes |
| Filtros/estado | Ação explícita e invalidação local | R01 podia manter seleção de outro departamento; falha global preservava objetos de outras abas; falha de horas bloqueava cadastro R01 | Limpeza de seleções inválidas e resultados de todas as abas; horas indisponíveis sem remover composição | AppTest, cursor fictício, troca de origem, recarga e fonte opcional indisponível |

## Referências e unidades

- **R01:** cadastro atual; cartão/quadro contam matrículas funcionais distintas.
  Categoria e departamento reproduzem a contagem de linhas com matrícula dos
  visuais documentados (agregador 5), inclusive repetições. A distribuição por
  departamento pode diferir da comparação R02, cuja unidade é distinta.
  Horas Reais mantêm o maior semestre por vínculo. A lista identifica valor,
  nulo na fonte, ausência de registro e fonte indisponível, além do semestre.
- **R02:** cadastro atual, com categoria aplicada igualmente a geral e QP. O
  seletor Quadros docentes não recorta esta população; somente o seletor de QP
  define o numerador simulado. Classificação ausente impede participação e
  demais conclusivos. Grupo não selecionado é indisponível, nunca zero.
  Uma matrícula em mais de um departamento conta uma vez no geral do recorte;
  não somar linhas departamentais para reconstruí-lo.
- **R03:** pessoas distintas na união de competências elegíveis; janeiro–julho
  e agosto–dezembro; situação A, lotes 3/4/7, exclusão A4 e seis quadros
  documentados. Categoria histórica recorta população; quadro seleciona séries.
  As pilhas exibem presenças por quadro, com sobreposição possível. Sua altura
  **não é total de pessoas**. O total distinto tem gráfico e coluna próprios.
  Cobertura inferior a 7/5 competências gera Parcial; mês ausente não vira zero.
- **R04/R05:** fórmulas preservadas. R04 usa o semestre escolhido e fonte dedicada;
  R05 distingue cadastro atual, eventos no intervalo e vigências interceptadas.
  Não há inferência administrativa por cargo/gratificação. Unidades comparáveis
  e atos administrativos adicionais continuam fictícios.

As cinco referências de experiência foram tratadas pelas descrições fornecidas:
visão geral, evolução empilhada, comparação departamental, carga individual e
funções com tempo. Números/nomes de capturas não foram usados como expectativas.
As fórmulas vêm do catálogo, mapa e documentação docente local já existentes.
Permanece a lacuna do filtro salvo de quadro registrada no catálogo; não se criou
equivalência para o semáforo ou definição institucional de QP.

## Apresentação interativa

Decisão D-029: Altair 6.3 declarado diretamente no projeto e lock, já instalado
como dependência de Streamlit. `web_charts.py` transforma cada `ResultTable` em
dados longos, sem agregação adicional ou troca de nulo por zero. Não há URL de
dados ou fonte externa. Interface com largura do contêiner, barras horizontais
para rótulos extensos, legenda inferior em uma coluna e fontes/cores dos tokens
locais. O tema automático do Streamlit é desligado somente nos gráficos para
preservar esses tokens. Importação do Altair adiada até a geração do gráfico.

Hover mostra valor, categoria/período, série e unidade. Clique na legenda destaca
séries; Shift seleciona várias. Nas distribuições simples, clique destaca a barra
e duplo clique limpa. São mudanças locais de opacidade, sem filtros de dados,
rerun de cálculo, alteração de denominadores, tabelas ou downloads. Tabelas
equivalentes continuam acessíveis; PNG/CSV/ZIP usam os resultados calculados.

Matplotlib continua gerando PNGs, incluindo barras agrupadas/empilhadas conforme
a especificação; R06 conserva sua apresentação existente. Referências técnicas:
[seleção por legenda no Altair](https://altair-viz.github.io/gallery/interactive_legend.html)
e [componente Streamlit](https://docs.streamlit.io/develop/api-reference/charts/st.altair_chart).
Aplicação dos tokens não declara homologação visual.

## Execução e evidências

Arquivos deste incremento (mudanças anteriores do Prompt 2 preservadas):

| Grupo | Arquivos |
|---|---|
| Apresentação e fluxo | `src/vrac/web_charts.py` (novo), `ui.py`, `academic_ui.py`, `charts.py` no mesmo pacote |
| Cálculo/exportação docente | `src/vrac/analyses/academic.py`, `faculty_overview.py`, `export.py` no mesmo pacote |
| Fonte sintética | `src/vrac/demo_data.py`, `src/vrac/db/synthetic_postgres.py` |
| Dependência | `pyproject.toml`, `uv.lock` (Altair direto, sem troca de versão) |
| Testes | `tests/test_faculty_completion.py` (novo), `test_academic_reader.py`, `test_postgres_demo_reader.py`, `test_academic_ui.py`, `test_ui.py` |
| Documentação | Este guia (novo), `docs/guides/ANALISES_SINTETICAS.md`, `docs/ANALYSIS_CATALOG.md`, `docs/operations/SYNTHETIC_SOURCE_MAP.md`, `docs/DECISIONS.md`, `docs/PROJECT_CONTEXT.md`, `docs/PLAN.md`, `docs/PROXIMOS_PASSOS.md`, `docs/STATUS.md` |

Testes e resultados finais estão no registro atual de [STATUS](../STATUS.md).
Comandos usados para verificação offline:

```powershell
.\scripts\check.cmd
.\.venv\Scripts\python.exe -m pytest tests/test_faculty_completion.py tests/test_academic_reader.py tests/test_academic_ui.py tests/test_ui.py -q
git diff --check
```

Para repetir uma demonstração sem banco (porta padrão livre):

```powershell
.\scripts\run-demo.cmd --memory
```

Nesta tarefa a prévia foi iniciada separadamente, somente em memória, na porta
8516, com `VRAC_DEMO_SOURCE=memory`, `VRAC_DATA_MODE=synthetic` e
`VRAC_ENVIRONMENT=development`, por:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8516 --server.headless true --server.fileWatcherType none --browser.gatherUsageStats false
```

**Navegador, evidência separada:** página inicial observada em janela estreita
e maximizada, origem Memória e aviso DEMONSTRAÇÃO visíveis. A ferramenta Computer
Use interrompeu a tentativa de clicar para gerar: a verificação de política de
URLs não é suportada neste navegador Windows. Não foram comprovados hover,
seleção de séries nem adaptação dos gráficos no navegador. AppTest e validação
de especificações não substituem essa conferência visual. Não se contornou o
bloqueio por outro mecanismo. A prancha oficial foi conferida pela renderização
local já existente em `.cache/branding-review/page-1.png`.

## Roteiro curto para Talita

1. Conferir DEMONSTRAÇÃO e a origem. Em Situação geral, escolher departamento
   (ou Todos os departamentos), quadro, categoria, situação e dupla função.
   Seleção vazia significa todos. Clicar **Calcular resultados**.
2. Ler a tabela de filtros, unidade e referência atual. Conferir cartão,
   distribuições e lista. Observar o estado e semestre próprio das Horas Reais.
3. Em Análises por período, escolher R02 e Todos os departamentos; clicar
   **Carregar ou atualizar dados**. Escolher a categoria e o grupo QP simulado;
   clicar **Calcular análises selecionadas**. Conferir a tabela departamental.
4. Escolher R03 e o intervalo; gerar novamente. Explorar a legenda e o hover.
   Conferir o total distinto separado das pilhas e a cobertura mensal na tabela.
5. Se necessário, abrir R04 para o semestre da carga ou R05 para eventos/vigências.
   Ler limitações das simulações. Baixar CSV, PNG ou pacote ZIP e conferir filtros
   e valores com a tela. Mudar filtro remove resultados/arquivos até nova geração.
6. Relatar dificuldade ou divergência indicando roteiro, filtros e snapshot, sem
   incluir dados pessoais. Feedback de uso não equivale a aprovação institucional.

## Limites e validações restantes

Sem conferência na instância PostgreSQL, acesso institucional ou teste de deploy.
Nenhum cluster/view/carga foi recriado. As consultas continuam fixas e vinculadas,
conta de leitura e TLS com certificado; nenhum comando de SQL Server foi executado.
Teste sintético não comprova mapeamento físico, cobertura ou resultado institucional.

Matheus deve repetir a exploração dos gráficos em desktop/janela estreita e revisar
o incremento. Talita avalia uso, filtros e exportações. Matheus e responsável pela
identidade visual revisam a apresentação, ainda sem homologação. DBA/DSI/time
conferem fontes, leitura, TLS, acesso e autenticação somente na etapa final.
Não se exige nova aprovação geral das fórmulas já documentadas.
