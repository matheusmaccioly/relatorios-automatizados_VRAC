**Revisão vigente de 09/11/2026:** o [feedback do PDF](FEEDBACK_PDF.md) substitui
as descrições abaixo sobre rastreabilidade no PDF e cenário de exemplo. O arquivo
atual tem 30 páginas, resultados e gráficos, data em Brasília e filtros sem o anexo
técnico. Os detalhes abaixo preservam o histórico de implementação.

# PDF consolidado — 09/11/2026

## Formato vigente: síntese visual em 16:9

Matheus pediu informação consolidada e gráficos, com apresentação próxima de um
PPT. Essa orientação substitui a inclusão de todas as tabelas no PDF descrita no
histórico abaixo. O download continua sendo **PDF**, sem novo formato PPTX.

O documento agora tem capa editorial, roteiro das análises escolhidas, cartões de
resultados e gráficos grandes. Cada resultado preserva valor, unidade e situação;
ausente não vira zero. A R01 obtém seu total e narrativa do resumo CSV existente.
R02–R06 usam métricas e narrativas do manifesto. Não há nova agregação nem IA.
Listas nominais, alocações individuais e registros históricos não entram no PDF.
Todas as tabelas continuam disponíveis no ZIP e na tela, sem alteração dos cálculos.
Filtros aplicáveis, fontes, versões, snapshots e avisos estão nas páginas finais.

Layout centralizado em `src/vrac/analyses/pdf_slides.py`: página 960 × 540 pt,
cartões com cores dos tokens, Rethink Sans, rótulos Literata e marca proporcional.
`pdf_export.py` valida a seleção e encaminha a renderização. O seletor de análises
foi mantido; `academic_ui.py` explica a diferença PDF/ZIP e evita o aviso de valor
inicial conflitante no multiselect. Nenhuma nova dependência.

Exemplos atualizados: `output/pdf/relatorio-sintetico.pdf`, **42 páginas** (25 de
apresentação e 17 de filtros/rastreabilidade), e
`output/pdf/relatorio-selecionado-R01-R06.pdf`, **16 páginas**.
Todas as 42 páginas do exemplo completo foram renderizadas e inspecionadas em
pranchas, com ampliação dos cartões. Sem cortes ou sobreposições observados.
As contagens de 74/18 páginas abaixo são históricas e foram substituídas.

Testes: 23 aprovados (PDF/interface); após o ajuste final de espaçamento, 14 testes
de PDF novamente aprovados. Verificam resultados, ausência de tabelas detalhadas,
16:9, gráficos, textos extensos, seleção e estados sem dados/indisponíveis. Ruff
check/format aprovados. Reprodução e comandos permanecem os mesmos abaixo.

Aplicação local reiniciada em `http://127.0.0.1:8520`, explicitamente com memória
sintética. Atualizar a página e preparar/baixar novamente. Não houve acesso a banco
ou publicação. Matheus e Talita revisam clareza; identidade continua pendente de
Matheus/responsável institucional. DSI/DBA seguem o planejamento existente.
Não foi executado download manual no ambiente publicado. Snapshots maiores podem
produzir mais páginas; textos de referência extensos continuam sem truncamento.

## Fluxo de uso e histórico

Em **Outras análises**, carregar os dados, conferir o recorte e clicar em
**Preparar relatório completo (R01–R06)**. A ação seleciona a visão conjunta,
apresenta todos os filtros e calcula os seis roteiros. Depois, clicar em
**Baixar relatório completo (PDF)**. Na sessão autenticada, usar o link
**Salvar arquivo preparado**. Não é necessário abrir/exportar cada análise.

Para um relatório menor, em **Análises que entram no PDF**, mantenha apenas as
análises desejadas e clique em **Baixar relatório das análises selecionadas (PDF)**.
É possível escolher uma ou várias, incluindo R01 isoladamente. As opções são as
análises já calculadas: use a preparação completa para disponibilizar R01–R06.
Sem seleção, o PDF não é liberado. A preparação completa restaura as seis opções.
O sumário, as seções e o nome do arquivo refletem a seleção; análises desmarcadas
não têm seus gráficos gerados para esse download. O ZIP continua seguindo o
conjunto calculado, sem ser alterado pela seleção exclusiva do PDF.

O PDF consome o mesmo pacote em memória do ZIP: CSVs, gráficos PNG, manifesto,
R01 explícita, métricas e textos existentes. O botão aparece para uma seleção
não vazia de análises calculadas. Uma alteração de filtros/origem invalida os resultados e downloads;
o mecanismo autenticado mantém bytes na sessão e revalida sua validade após
gerar o arquivo. Não há novo endpoint, cache compartilhado ou arquivo público.
Arquivos já baixados não podem ser revogados.

ReportLab foi adicionado às dependências e ao lock: geração Python local,
fontes TTF incorporadas, tabelas paginadas e texto extraível. Pypdf é dependência
de desenvolvimento para conferir conteúdo. PyMuPDF foi instalado apenas no
ambiente de conferência para renderização; não integra a aplicação.

As cores, fontes e marca são obtidas de `Branding` e seus tokens. A adaptação
documental está centralizada em `analyses/pdf_export.py`: A4 paisagem, corpo
10 pt, tabelas 9 pt, cabeçalhos repetidos e blocos de até seis colunas com número
de linha para relacionar tabelas largas. A marca permanece proporcional e inteira.
Não há tema de identidade independente. Homologação institucional permanece pendente.

## Exemplo e reprodução offline

`output/pdf/relatorio-sintetico.pdf`: exemplo determinístico completo, 74 páginas,
2024.1–2026.2, carga 2026.1, QP simulado PROF PRINCIPAL e todos os departamentos
da fixture em memória. ZIP de conferência na mesma pasta. A data fixa identifica
o exemplo reproduzível; na aplicação a execução usa a data real em UTC.

```powershell
.\.venv\Scripts\python.exe scripts/export-synthetic-pdf.py
.\.venv\Scripts\python.exe -m pytest tests/test_pdf_export.py tests/test_supabase.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_academic_ui.py tests/test_academic_analyses.py tests/test_feedback_exports.py -q
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Arquivos de implementação: `src/vrac/analyses/pdf_export.py`,
`src/vrac/academic_ui.py`, `src/vrac/ui_kit.py`, `pyproject.toml`, `uv.lock`.
Reprodução: `scripts/export-synthetic-pdf.py`; testes: `tests/test_pdf_export.py`.
Alterações locais anteriores em `.gitignore` e `docs/STATUS.md` preservadas.

## Conferência e revisão de Outras análises

O relatório foi renderizado integralmente (74 páginas), inspecionado em pranchas
de páginas e com ampliação da tabela de Horas Reais e do gráfico de 36 competências.
Acentos, fontes locais, repetição de cabeçalhos e rodapés sintéticos estão presentes.
A primeira versão repetia contexto em cada tabela: foi reduzido a uma ocorrência
por análise, mantendo unidades e limitações específicas junto de cada tabela.
Tabelas largas ganharam número de linha, pois repetir apenas o departamento não
identificava univocamente seus registros. Valores não foram arredondados novamente.

Resultados finais: 33 testes existentes de interface/análises/exportação aprovados;
28 de PDF e segurança aprovados; 1 adicional de expiração durante a geração aprovado.
Total de 62 aprovações nas execuções finais. Ruff check e format aprovados nos cinco
arquivos Python alterados/criados. A extração de texto extenso foi conferida por
palavras, pois o extrator insere os rodapés entre fragmentos de páginas diferentes.
Não houve perda de palavras. O PDF contém os valores das tabelas, inclusive zero
e ausente, e o estado das Horas Reais distingue nulo na fonte de sem registro.

Revisão da tarefa `6hxChPJ2vCPg9QFR`, após o PDF:

| Achado | Tratamento |
|---|---|
| Exportação selecionada podia ser confundida com completa | Ação explícita R01–R06 e PDF somente no conjunto completo |
| Referências de cadastro, intervalo e carga diferem | Sumário explicita referências; filtros não aplicáveis ficam fora da tabela de filtros do PDF |
| R02 repete resultados na tabela de comparação | Mantido: tabela permite conferir situação e unidade; sem remoção de resultado |
| R03 tem detalhe extenso | Mantido integralmente, paginado, sem somar competências |
| Nomes e ordem R01–R06 correspondem ao catálogo | Mantidos; não houve evidência para renomear ou reordenar |
| Identificadores técnicos de CSV eram pouco claros no documento | PDF usa títulos de tabela existentes; R01 usa Composição docente e Lista de conferência |

A correspondência foi conferida com os mesmos objetos calculados da interface,
CSV do ZIP e extração textual do PDF. O AppTest executa o fluxo da tela sem
acesso ao banco. Não foi executada sessão manual no navegador nem download
no ambiente publicado. Não houve acesso institucional ou teste de banco.
O volume e a performance com snapshots maiores que a fixture ainda precisam de
conferência; o limite existente de 25 MiB do download autenticado foi preservado.
O relatório longo é consequência da inclusão das tabelas detalhadas, não um resumo.

Complemento de seleção em 09/11/2026: alterados `academic_ui.py`, `pdf_export.py`,
`tests/test_pdf_export.py`, este guia e `docs/STATUS.md`. Exemplo adicional
`output/pdf/relatorio-selecionado-R01-R06.pdf`, com 18 páginas, renderizado e
inspecionado integralmente. A seleção modifica apenas a composição do documento,
sem novos filtros analíticos, fórmulas ou dependências. Testes cobrem R01 isolada,
R06 isolada, combinação R02/R06, seleção vazia/inválida/indisponível, seleção na
tela, restauração do conjunto completo e invalidação por filtros.
Resultado desta execução: **23 testes aprovados**, Ruff check/format e
`git diff --check` aprovados.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_pdf_export.py tests/test_academic_ui.py -q
```

Matheus revisa implementação/testes; Talita revisa uso e clareza; Matheus e o
responsável institucional revisam a identidade. DSI/DBA seguem o planejamento
institucional vigente. Sem aceite humano presumido, conclusão de tarefas no
Todoist, preparação da versão/guia ou publicação.
