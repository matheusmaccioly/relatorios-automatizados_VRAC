# Interface e gráficos

Roteiro atual da aplicação, após a aproximação ao design system (D-032, 04/11/2026) e as
tabelas visuais (D-033, 05/11/2026). A revisão anterior está preservada no fim, como histórico.

## Como abrir localmente

```powershell
.\.venv\Scripts\python.exe scripts/sync-branding.py
.\scripts\run-demo.cmd --memory 8545
```

Abra `http://127.0.0.1:8545`. Use o lançador `.cmd`: onde a execução de scripts
PowerShell está desabilitada, o `.ps1` é bloqueado. Sem porta, ele usa a 8501. Se a
aplicação já estiver em execução, reinicie-a para carregar o tema: o servidor não
recarrega código nem configuração sozinho.

## Caminhos para Talita

| Quero saber | Na tela Início | Filtros que aparecem |
|---|---|---|
| Como se distribuem os docentes e como evolui o total de ativos | Panorama docente | Centro, Departamento, semestres; Quadro, Categoria, Situação e Dupla função em Mais filtros |
| Como o grupo QP se compara ao geral | Grupo QP e geral | Centro, Departamento, Categorias e Quadros do grupo QP |
| Como o corpo docente evoluiu | Evolução docente | Centro, Departamento, semestres, Quadros e Categorias |
| Quais funções têm evidência | Funções | Centro, Departamento, semestres, Quadros e Categorias |
| Como se distribuem carga e alocações | Carga e alocações | Centro, Departamento, semestre da carga, Quadros e Categorias |
| Como evoluíram matrículas e alunos | Matrículas e alunos | Centro, Departamento, semestres, curso, habilitação, turno, nível e ingresso |
| Tudo de uma vez | Ver todas as análises | Todos os filtros |
| Conferir linhas sem consolidar | Bloco recolhido Conferir dados sintéticos, no fim de qualquer tela | Departamento e período fictícios |

Cada cartão abre a análise com a base carregada; basta ajustar os filtros e calcular.
Depois do cálculo, a tela vai sozinha até os resultados. Só aparecem os filtros que
afetam a análise; os demais ficam no valor inicial, e os usados continuam em tabela em
**Filtros usados neste resultado**. Trocar Centro ou Departamento recarrega a base e
limpa os resultados. A navegação continua visível ao rolar a página.

## Como ler as tabelas

Cada gráfico traz sua tabela recolhida em **Ver tabela do gráfico**, com o CSV. Tabelas sem
gráfico ficam em **Outras tabelas e arquivos**. Uma tabela pode alimentar dois gráficos e
então aparece nos dois. Nas listas por docente, nome, indicador e horas vêm primeiro.

| Símbolo | Indicador de carga | Destaque |
|---|---|---|
| ▼ | Abaixo do necessário | Amarelo claro |
| ● | Dentro do esperado | Sem destaque |
| ▲ | Acima do necessário | Amarelo claro |
| ▲▲ | Muito acima (verificar coord./múltiplas turmas) | Amarelo |
| ○ | Sem alocação (CH = 0) | Cinza |
| – | Sem CH (em branco) | Cinza |
| ? | Sem regra definida | Cinza |
| ≠ | Indicadores distintos | Cinza |
| | ausente (sem indicador) | Cinza |

O indicador reproduz a regra do painel e não avalia produtividade, por isso não há vermelho.
Na R06, a variação de matriculados usa ▲ ▼ ● para a direção, sem sugerir que subir é bom;
variação não calculável não recebe seta. Percentuais aparecem com uma casa decimal na tela,
e o CSV mantém a precisão calculada. Símbolos e destaques só existem na tela: CSV, ZIP e
PNG trazem o texto original da regra.

| Gráfico novo | Onde | O que mostra |
|---|---|---|
| Indicador de carga dos professores | R01 e Análise docente | Linhas do cadastro por estado do indicador |
| Indicador de carga por vínculo | R04 | Vínculos por estado do indicador |
| Participação do grupo simulado por departamento | R02, com mais de um departamento | Participação em %, ausente quando falta classificação |
| Matriculados por curso em (último período) | R06, com mais de um curso | Matriculados por curso; as barras não devem ser somadas |

As abas **Financeira (em breve)** e **Projetos patrocinados (em breve)** mostram apenas um
aviso: não há filtros, análises nem dados dessas áreas nesta prova de conceito (D-037).

## Como ler os gráficos

| Gesto | Resultado |
|---|---|
| Passar o cursor numa linha | Linha-guia e valor de todas as séries daquele ponto |
| Passar o cursor numa barra | Valor, unidade e situação |
| Clicar numa barra (composição docente) | Destaca a barra; dois cliques limpam |
| Clicar na legenda | Destaca a série; Shift escolhe várias; dois cliques limpam |
| Ícone no canto do gráfico | Tela cheia |

O destaque não muda filtros, tabelas ou arquivos. Uma categoria única aparece como
número, sem gráfico; sua tabela e seu PNG continuam disponíveis. Nas linhas mensais, só
início, fim e extremos têm rótulo, e os demais meses aparecem ao passar o cursor. Nas
pilhas mensais, o número só aparece no segmento se couber; tabela e cursor mostram todos.

Lacunas indicam dados ausentes; zero é um valor observado. Em barras, um valor ausente
mantém a categoria no eixo com o texto "ausente", sem barra. Não some meses para obter
docentes do semestre nem as pilhas de quadros para obter pessoas distintas. Horas Reais
permanecem separadas de horas alocadas, e matrículas de alunos únicos. Nenhum gráfico
recomenda contratação ou classifica produtividade.

Arquivos PNG e o pacote ZIP são gerados no clique em baixar, e o pacote pode levar
alguns segundos. O pacote agora inclui os PNGs dos gráficos novos e o arquivo
`R06/student_courses_latest.csv`; `R04/indicators.csv` passou a seguir a ordem de leitura.
Os demais CSVs não mudaram.

## Limites

Mais de cinco séries repetem as cores da paleta: as linhas mantêm traços diferentes e a
legenda identifica cada uma, mas é preciso revisar o gráfico se isso ocorrer com dados
reais. A conferência automatizada foi feita em Chrome headless com memória sintética;
teclado, leitor de tela, Safari/Firefox e PostgreSQL sintético não foram exercitados.

| Revisão pendente | Responsável | O que conferir |
|---|---|---|
| Identidade visual | Matheus e responsável institucional | Paleta da D-032, marca monocromática, tipografia e componentes; divergência entre prancha e site; cabeçalho preto das tabelas e cores do indicador (D-033) |
| Uso | Matheus e Talita | Cartões e perguntas da tela Início, nomes das análises, filtros, leitura dos gráficos e downloads; símbolos do indicador e tabelas recolhidas |
| Escopo | Matheus | Se a sinalização "Análise financeira · Em breve" deve aparecer para Talita, dado que a análise segue fora da PoC |
| Integração final | Time/DSI/DBA conforme planejamento vigente | Sem requisito novo deste incremento |

Interface: `src/vrac/ui.py`, `academic_ui.py`, `faculty_presentation.py`,
`organisation_ui.py`, `ui_kit.py` e `indicators.py`. Gráficos: `web_charts.py` e `charts.py`.
Identidade: `branding.py`, `assets/branding/tokens.toml`, `.streamlit/config.toml`,
`scripts/sync-branding.py` e `static/branding/`. Testes em
`tests/test_interface_navigation.py` e `tests/test_table_presentation.py`.

---

## Histórico: revisão anterior de 04/11/2026

Incremento solicitado por Matheus sobre as análises já implementadas. O portal
HTML fornecido e o [site público da PUC-Rio](https://www.puc-rio.br/) orientaram a
apresentação. A aplicação continua um monólito Streamlit com dados sintéticos,
sem LLM, novos serviços ou alteração das fórmulas.

## O que mudou

- Cabeçalho mais leve, títulos e ações em preto, destaque amarelo na navegação e
  nos resultados. Rethink Sans em corpo/títulos; Literata na identificação editorial.
- Filtros essenciais e etapas explícitas; refinamentos opcionais agrupados, com
  resumo do recorte e ações de limpeza. Alterações removem resultados e arquivos
  anteriores. A limpeza do formulário por período mantém a base já carregada.
- Guia por pergunta para escolher R01–R06; estados indicam o próximo passo.
- Gráficos web Altair também na R06, com unidades nos eixos, detalhes em português
  ao passar o cursor e destaque por barra/legenda. Linhas usam pontos e traços;
  dados, tabelas, CSV/PNG/ZIP e feedback mantêm os contratos existentes.
- Largura automática, rótulos adaptados ao espaço, legendas abaixo dos gráficos e
  ajustes de espaçamento para telas estreitas. Rótulos sobrepostos podem ser
  ocultados; dados e detalhes permanecem disponíveis nos gráficos/tabelas.

Marca, arquivos de fontes e paleta foram preservados. As cores do portal/site
divergem dos tokens autorizados; a revisão não as substitui nem representa
homologação. Ver [referências de identidade](../../assets/branding/guidelines/README.md).

## Como abrir localmente

O comando abaixo seleciona explicitamente a fixture sintética em memória:

```powershell
.\.venv\Scripts\python.exe scripts/sync-branding.py
.\scripts\run-demo.ps1 -Source memory -Port 8522
```

Abra `http://127.0.0.1:8522`. Se a aplicação já estiver em execução, reinicie-a
após sincronizar o tema. Para PostgreSQL sintético, o operador pode usar o
lançador existente com `-Source postgres`, com sua configuração externa; essa
origem não foi conectada na revisão. Não há fallback silencioso entre origens.

## Caminhos para Talita

| Objetivo | Caminho | Filtros principais |
|---|---|---|
| Consultar composição e evolução docente | Análise docente → definir recorte → Calcular resultados | Centro, Departamento e intervalo do histórico; refinamentos opcionais de quadro, categoria, situação e dupla função |
| Consultar matrículas | Análises por período → R06 → Carregar ou atualizar dados → definir filtros → Calcular análises selecionadas | Semestres, curso, habilitação, turno, nível e forma de ingresso |
| Consultar carga horária | Análises por período → R04 → carregar → definir referência → calcular | Departamento, semestre da carga e quadros |
| Comparar quadros, histórico ou funções | Análises por período → escolher R02, R03 ou R05 → carregar → filtrar → calcular | Referências e refinamentos descritos no formulário |
| Conferir linhas sem consolidar | Conferir dados sintéticos → selecionar departamento/período → Mostrar dados de demonstração | Departamento fictício e período fictício |

Os filtros utilizados aparecem em tabela. Cadastro atual e histórico são
referências diferentes; filtros de situação/dupla função na visão docente
recortam apenas o cadastro atual. Limpar filtros restaura o recorte inicial e
exige um novo cálculo. Uma mudança de Centro continua restringindo Departamento.

Passe o cursor sobre pontos/barras para consultar os valores completos. Nos
gráficos de composição, clique em uma barra para destacar e clique duas vezes
para limpar. Nos gráficos com várias séries, clique nos itens da legenda para
destacar. Esse destaque não modifica tabelas nem os arquivos exportados. Para
alterar o recorte da análise, use os filtros e calcule novamente.

Lacunas indicam dados ausentes; zero é um valor observado. Não some meses para
obter docentes do semestre ou as pilhas de quadros para obter pessoas distintas.
Horas Reais permanecem separadas de horas alocadas; matrículas e alunos únicos
mantêm unidades próprias. Nenhum gráfico recomenda contratação ou classifica
produtividade.

## Verificação e limites

As evidências dos testes offline e comandos estão no [estado do projeto](../STATUS.md).
O servidor local respondeu `ok` em sua rota de saúde usando memória sintética.
A ferramenta de navegador falhou duas vezes por timeout; a alternativa Computer
Use também falhou em `list_apps`, inclusive após reinicialização. Não foi possível
inspecionar a interface ou exercitar a interação real no navegador.

Responsividade e interação foram verificadas nos contratos dos gráficos e nos
testes Streamlit, sem comprovação visual em viewport real. Não houve conexão
PostgreSQL/SQL Server, teste institucional, teste da suíte completa nesta revisão
ou publicação.

| Revisão pendente | Responsável | O que conferir |
|---|---|---|
| Identidade visual | Matheus e responsável institucional | Tipografia, hierarquia, marca, cores já autorizadas e componentes; resolver divergência da paleta web antes de adotar novos valores |
| Uso no navegador | Matheus e Talita | Desktop e tela estreita; filtros, foco pelo teclado, legendas/destaque, leitura de valores, limpeza e downloads |
| Integração final | Time/DSI/DBA conforme planejamento vigente | Sem requisito novo deste incremento; fontes, autorização e acesso real continuam na etapa final |

## Arquivos deste incremento

Interface: `src/vrac/ui.py`, `src/vrac/academic_ui.py`, `src/vrac/web_charts.py`.
Identidade: `src/vrac/branding.py`, `assets/branding/tokens.toml`,
`.streamlit/config.toml`, `assets/branding/README.md` e `guidelines/README.md`.
Testes: `tests/test_interface_navigation.py`, `tests/test_academic_ui.py` e
`tests/test_student_ui.py`. Registros: este guia, `docs/STATUS.md`,
`docs/PROJECT_CONTEXT.md`, `docs/PLAN.md` e `docs/DECISIONS.md`.
Alterações anteriores presentes no checkout foram preservadas.
