# Origens dos dados e publicação da PoC

A navegação por áreas da `main` é compartilhada pelas duas origens. Desde a D-039, a
hospedagem (Supabase) usa sempre a origem institucional pseudonimizada, sem seletor;
a demonstração sintética fica na execução local em memória:

| Origem | Conteúdo | Acesso |
| --- | --- | --- |
| Institucional pseudonimizada · professores | Fontes docentes autorizadas | Conta autenticada e permissão institucional por departamento |
| Demonstração sintética | Exemplos determinísticos de demonstração | Conta autenticada e permissão própria da demonstração |

A troca de origem limpa resultados, arquivos gerados e comentários da sessão.
Uma falha institucional nunca ativa exemplos sintéticos. CSV, PNG, ZIP e PDF
identificam a origem. Não se misturam origens no mesmo pacote.

No início, escolha uma análise e departamento em **Comece rápido**, ou abra
**Docentes**. O relatório completo mantém como bloqueadas as análises sem fonte:
a carga docente não fornece matrículas de alunos para R06. Campos ausentes,
limitações do histórico e regras ainda pendentes aparecem junto aos resultados.
Pseudonimização não transforma estes dados em dados sintéticos nem em dados públicos.

## Execução local

```powershell
$env:VRAC_DEMO_SOURCE = 'supabase'
$env:VRAC_DATA_MODE = 'pseudonymized'
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8530
```

Para exemplos locais, use `VRAC_DEMO_SOURCE=memory` e `VRAC_DATA_MODE=synthetic`.
Não é necessário incluir CSVs ou credenciais no repositório para consultar as
fontes já carregadas. O aplicativo usa a configuração pública e a sessão do usuário.

## Verificação e publicação

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=.cache/pytest-publicacao
.\.venv\Scripts\python.exe -m ruff check src tests app.py
.\.venv\Scripts\python.exe -m ruff format --check src tests app.py
```

Use uma pasta temporária nova quando houver restrições de permissão no Windows.
Os testes padrão são offline, com exemplos fictícios e rede bloqueada.
Testes SQL de autorização são separados e exigem execução autorizada.

A publicação existente usa `main` e `app.py` no Streamlit Community Cloud.
Após um envio autorizado, conferir a reconstrução da aplicação e o login. Em uma sessão autorizada,
conferir Docentes, as exportações e o relatório completo do Início.
Nenhum CSV, material de origem, registro individual ou script pontual de concessão
de acesso deve integrar o commit público. As migrações versionadas descrevem o
schema; publicar o código não deve executar novamente a importação.

Matheus e Talita ainda devem validar os resultados contra as fontes aprovadas;
DSI/DBA validam acesso, retenção e operação. Publicação não significa homologação
analítica ou visual.


### Atualizações do código na hospedagem

A configuração compartilhada usa `server.fileWatcherType=auto`, para observar
mudanças nos módulos importados. Os atalhos locais podem continuar desativando
essa observação por argumento de linha de comando. A versão do pacote nesta
entrega é `0.1.6`, consistente em `pyproject.toml` e `uv.lock`.

A [documentação de configuração do Streamlit](https://docs.streamlit.io/develop/api-reference/configuration/config.toml)
explica que `none` desativa a observação de arquivos. A mudança no arquivo de
dependências aciona a resolução do ambiente conforme a
[documentação do Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/upgrade-streamlit).
Conferir o resultado no navegador; um push aceito sozinho não comprova atualização
do aplicativo em execução.

## Análise Geral de alunos — versão 0.1.2

Após o login, abra **Alunos → Análise temporal → Análise Geral**. A consulta
usa somente os departamentos autorizados para a sessão e apresenta séries por
semestre, filtros acadêmicos, tabela e exportações CSV e PNG, seguindo as
classificações da página de referência do PBIP. Direito permanece pendente;
a identificação JUR ainda requer conferência e não foi convertida em outra sigla.

A publicação não amplia permissões nem recarrega o lote. Validar com Matheus e
Talita a consulta autenticada, os filtros e as exportações no ambiente web.
O cabeçalho contém o atributo técnico `data-vrac-release="0.1.6"` para conferir
a versão efetivamente renderizada, sem exibir informações internas.

## Centros e departamentos nas análises institucionais

O cadastro compartilhado em `src/vrac/department_hierarchy.py` associa somente
os departamentos disponíveis e autorizados ao seu centro atual:

| Centro | Departamentos do recorte |
|---|---|
| CCS — Centro de Ciências Sociais | ADM, DIR, ECO |
| CTCH — Centro de Teologia e Ciências Humanas | EDU, FIL |
| CTC — Centro Técnico Científico | ELE, IND, INF |

Conferido em 11/11/2026 no [diretório oficial de centros da PUC-Rio](https://www.puc-rio.br/english/departaments/centers_departaments.html)
e nas colunas de centro da fonte de alunos. Não descreve alterações históricas
de vinculação. Novos departamentos sem cadastro permanecem em “Centro não informado”.
O cadastro nunca adiciona departamentos ao acesso do usuário.

Desde a versão 0.1.5, Direito integra docentes e alunos no CCS: DIR no RH e JUR no
sistema acadêmico, exportado como DIR. JUR nunca aparece como opção.
Centro restringe os departamentos nas análises e acompanha os filtros exportados;
a troca de centro invalida resultados e arquivos do recorte anterior.

Alteração incluída na publicação autorizada da versão 0.1.3. Não exige recarga do Supabase.
Validar com Matheus/Talita os recortes CCS/CTCH/CTC antes da homologação.

## Padronização da interface — versão 0.1.4

Alunos passou a seguir o mesmo padrão de tela de Docentes: etapas de filtro,
Calcular resultados, filtros usados em tabela, bloco Baixar relatório (ZIP), cartão
do gráfico com PNG e tabela recolhida com CSV, e limites no ícone de informação.
O PDF de alunos não é oferecido nesta versão, porque o modelo atual não reproduz
todos os filtros aplicados. Docentes recebeu ajustes de consistência nos cartões e
nos filtros usados. Sem mudança de cálculo, consulta, permissão ou schema; não exige
recarga do Supabase. Padrão descrito em [Interface e gráficos](INTERFACE_E_GRAFICOS.md).

## Fidelidade aos painéis e Direito — versão 0.1.5

As análises seguem os painéis de referência (D-040/D-041):
- **Docentes:** Análise Geral com Situação inicial ATIVO e filtro de página do painel;
  Comparação entre grupos de quadro (Grupo A × Grupo B; padrão QP = PROF PRINCIPAL ×
  Geral); Histórico do departamento pela folha desde 2022; Carga horária com Horas Reais
  em ordem decrescente, Indicador de CH e turmas oferecidas com disciplina legível;
  Gratificações e funções por função, departamento e mês.
- **Alunos:** filtros iniciais do painel (Nível sem Mestrado/Doutorado; Curso/Programa
  sem vazio/DOMÍNIO ADICIONAL) e séries com os nomes do painel; Direito incluído.

Exige a migração `20261111190000_vrac_docentes_layout_v2` (colunas opcionais) e os
lotes v2 liberados; a versão 0.1.4 não lê docentes institucionais após essa migração.
Pessoa e vínculo seguem pseudonimizados. Validar com Matheus e Talita os números
contra capturas do painel de um departamento autorizado.

## Correção de Alunos com Direito — versão 0.1.6

A 0.1.5 recusava a lista de departamentos de alunos quando ela passou a conter DIR
("Análise de alunos indisponível"). A leitura agora usa a mesma lista fechada dos
docentes (oito departamentos; JUR continua recusado). A migração
`20261111210000_vrac_alunos_opcoes_filtros` pré-calcula as opções de filtro por lote e
departamento, com a mesma RLS dos eventos e resposta idêntica à anterior (conferida em
todos os recortes ao aplicar); a consulta de filtros caiu de ~6,9 s para ~26 ms. O
carregador de alunos preenche essas opções em novas cargas.
