# Revisão do feedback do PDF — 09/11/2026

Incremento de apresentação solicitado por Matheus, sem avanço de fase ou publicação.
Alterações locais anteriores foram preservadas.

## Resultado

- Textos visíveis da aplicação, gráficos, CSVs e PDF usam resultados em lugar de
  “indicadores”. Identificadores técnicos internos foram preservados quando necessários.
- Capa com data/hora em Brasília: `09/11/2026 às 12h00 (Brasília)` no exemplo fixo.
- Novo departamento `DEMO — Departamento exemplo`, com 14 vínculos fictícios,
  12 PROF PRINCIPAL e 2 PROF QCI, distribuídos em seis cargos diferentes.
  Não copia pessoas, matrículas ou uma unidade institucional da captura.
- R02: 14 no geral, 12 no grupo selecionado, 2 demais, 85,71% de participação.
  O cartão e a categoria de classificação ausente aparecem somente quando há ausências.
  A definição institucional de QP continua pendente e os quadros escolhidos ficam explícitos.
- Cargas reais e contratadas em funis de barras horizontais centralizadas, ordenadas
  por frequência. A largura conta vínculos; não representa etapas ou taxa de conversão.
- PDF sem páginas de hashes, execução e versões. Filtros permanecem em tabela;
  avisos resumidos de indisponibilidade e a ressalva de QP são mantidos. Notas integrais
  e rastreabilidade continuam na aplicação e no ZIP.
- Números do PDF exibem até duas casas decimais, sem alterar valores no ZIP.

## Uso local

O novo cenário está disponível somente na origem **memory**, em Análises disponíveis
ou Análise docente. Selecione o centro **Exemplo de apresentação** e o departamento
**DEMO — Departamento exemplo**. Todos os departamentos inclui também esse cenário.
As fixtures SINT-A/B/VAZIO continuam disponíveis para testar ausências e limites.
O banco Supabase/PostgreSQL não foi consultado nem alterado; na origem remota o novo
cenário não aparece. Não há fallback por erro de conexão.

```powershell
$env:VRAC_DEMO_SOURCE = 'memory'
.\.venv\Scripts\python.exe -m streamlit run app.py
.\.venv\Scripts\python.exe scripts/export-synthetic-pdf.py
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp tmp/pytest-feedback-complete
.\.venv\Scripts\python.exe -m ruff check src tests scripts/export-synthetic-pdf.py
```

PDF e ZIP: `output/pdf/relatorio-sintetico.pdf` e `.zip`. O exemplo mantém data fixa
para reprodução; downloads da aplicação usam a data da execução, convertida para Brasília.

## Arquivos deste incremento

- PDF: `analyses/pdf_slides.py`, `scripts/export-synthetic-pdf.py`.
- Cenário: `analyses/presentation_fixture.py`, `academic_fixture.py`,
  `faculty_overview_fixture.py`, `demo_data.py`, `department_hierarchy.py`.
- Cálculo/apresentação: `analyses/academic.py`, `charts.py`, `web_charts.py`.
- Vocabulário: `academic_ui.py`, `faculty_presentation.py`, `ui.py`, `ui_kit.py`,
  `indicators.py`, `branding.py`, `synthetic.py`, `analyses/academic_export.py`,
  `export.py`, `faculty_overview.py`, `references.py`, `synthetic_cases.py`,
  `workflows.py` e `config/analyses.yaml`.
- Testes: `test_presentation_feedback.py`, `test_pdf_export.py`,
  `test_department_hierarchy.py` e expectativas de rótulos em testes existentes.
- Documentação: este guia, STATUS, PROJECT_CONTEXT, PLAN e PDF_CONSOLIDADO.

## Revisões pendentes

Matheus e Talita precisam revisar o exemplo, a legibilidade dos funis e o nível de
resumo do PDF. O cenário é plausível para demonstração, não foi conciliado com um
 departamento real. Casos de ausência continuam explícitos quando existem na fonte.
Matheus e o responsável institucional devem revisar a aplicação visual; não há
homologação presumida. DSI/DBA: nenhuma ação nova nesta revisão; integração real e
mapeamento físico continuam na etapa final. Eventual atualização da base remota é
outro incremento, com escopo e execução próprios.

Não executados: conexão institucional, atualização/consulta do banco remoto,
publicação e revisão humana. Não houve inspeção de segredos ou diretórios privados.

## Verificação executada

- Suíte offline completa: **552 passaram, 1 falhou, 1 teste de integração excluído**.
  A falha era a expectativa de legenda interativa nos dois gráficos agora em funil.
  O teste foi atualizado para conferir os dados ordenados e a geometria de barras
  centralizadas. Após o ajuste final, os **13 testes** de composição/gráficos e
  cenário de apresentação passaram. A suíte completa não foi repetida após esse ajuste.
- PDF e cálculos acadêmicos, incluindo os novos testes de apresentação: **34 passaram**.
- Hierarquia e filtros de departamentos: **13 passaram**.
- Fluxo do cenário no AppTest: aprovado, cartões 14/12/2, sem erros.
- Ruff check e format --check: aprovados (97 arquivos formatados).
- PDF de 30 páginas gerado; todas as páginas renderizadas com Poppler e inspecionadas
  em prancha. Após corrigir as casas decimais e retirar a classificação ausente com zero,
  páginas 8 e 9 renderizadas novamente e conferidas ampliadas, sem sobreposição.
- Tentativas iniciais identificaram expectativas antigas de nomes e problemas de
  permissão no diretório temporário padrão. A execução registrada acima usou basetemp
  local e cache desativado. Nenhum teste de banco foi executado.
