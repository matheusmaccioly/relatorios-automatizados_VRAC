# Estado da entrega

Atualizado em 27/10/2026. **Prompt 2 preparado: catálogo e contratos lógicos com testes sintéticos.**
**Conexão e inventário institucionais: NÃO VALIDADOS.** SQL Server permanece hipótese.
Fontes físicas, fórmulas e aceite funcional continuam pendentes; a base documental
semântica foi incorporada ao catálogo. Fases 3–7 não iniciadas.
Fase 0 e ferramentas do Prompt 1 preparadas. Conteúdo do guia original preservado;
`AGENTS.md` atualizado com a exigência de branding institucional.

## Preparação do commit local — 28/10/2026

A pedido de Matheus, reunidas as alterações pendentes de catálogo, contratos,
documentação, estrutura de branding e consulta SQL de referência para commit local.
Os arquivos internos explicitamente ignorados permanecem fora do versionamento.
Nenhuma consulta SQL foi executada e nenhuma fonte ou regra institucional foi aprovada
por este registro. Não houve avanço de fase ou publicação.

Verificações repetidas: `.\scripts\check.cmd` concluiu com código 0, lock offline,
Ruff e formatação aprovados; **182 testes passaram e 1 integração foi excluída**.
`git diff --check` não encontrou erros de whitespace. Não executados testes de banco,
homologação funcional ou visual. As validações de Matheus, DSI, DBA e Talita descritas
neste documento permanecem pendentes.

## Revisão da base das análises — 27/10/2026

Matheus forneceu o caminho local de `docs/ANALISE_MODELOS_SEMANTICOS_VRAC.md` e autorizou
seu uso nesta revisão. O documento original foi preservado; os registros de inspeção
abaixo continuam como histórico da extração anterior.

- `config/analyses.yaml`: versão `phase2-semantic-baseline-v3`, baseada em documento
  detalhado disponível na revisão, com quatro variantes docentes, quatro acadêmicas
  de matrículas e uma de Horas Reais. Todas sem seleção institucional ou fonte SQL aprovada.
- `config/semantic_model_sources.local.yaml`: mapeamento local de 12 tabelas e 399
  definições de colunas, nomes/tipos declarados, referências de medidas e papéis
  candidatos. Qualificação por modelo impede presumir que objetos homônimos são iguais.
  Não contém dados pessoais, conexão ou expressões executáveis e não é carregado pelo runtime.
- Documento detalhado e mapeamento local excluídos do Git e do contexto Docker,
  respeitando a restrição de publicação do próprio documento. O catálogo distribuível
  funciona sem esses arquivos. Nenhum commit ou push foi realizado nesta revisão.
- `catalog.py`, `contracts.py` e CLI: variantes tipadas e validação de referências,
  modelo, fonte lógica, unidade, base temporal e seleção com aprovação. Pessoas,
  matrículas funcionais e matrículas acadêmicas têm significados distintos. Mudança
  de variante ou de base temporal impede conciliação automática mesmo com números iguais.
- Revisadas população atual versus histórica, coortes/trajetória, calendário incluindo
  julho, desempates, filtros de bolsas, fontes dedicadas de horas, duplicação de linhas
  e limites de RLS. Calendário e permissões não foram implementados por inferência.
- Atualizados catálogo documental, contexto, plano, decisões, README e índice.
  Preservadas as mudanças anteriores de organização, branding e fases 1/2.

Verificações desta revisão: `.\scripts\check.cmd` aprovou lock offline, Ruff, formatação
e **182 testes; 1 teste de integração não selecionado**. A CLI
`.\.venv\Scripts\python.exe -m vrac.analyses` carregou as três análises sem consultar
fontes. Mapeamento local conferido contra os cabeçalhos de tabelas/colunas e âncoras
das medidas; hash do documento preservado:
`84bd9e833627c1e562e0018a9fad2bf806b509a723fc0172866cbcc5f39f7372`.
Wheel construído offline e conferido: 35 arquivos, catálogo incorporado idêntico ao
YAML de origem e nove variantes carregadas diretamente do pacote. Documento interno
e mapeamento local ausentes do wheel. `git check-ignore` confirmou as duas exclusões;
`git diff --check` não encontrou erros de whitespace.

Não executados: conexão real, Power Query/M, DAX, RLS por usuário, conciliação de números,
homologação funcional/visual ou implantação. DBA confirma origem física, chave e
cardinalidade; Talita escolhe população, referência temporal e critérios; Matheus/DSI
validam acesso. Sem essa confirmação, os adaptadores reais continuam bloqueados.

## Análise documental de modelo semântico — 27/10/2026

- A pedido de Matheus, realizada inspeção local, somente leitura, de um PBIX
  explicitamente indicado, para explicar estrutura, fórmulas e possibilidades de
  simplificação. A explicação foi entregue na conversa; o arquivo não foi alterado.
- Metadados, relacionamentos e expressões foram inspecionados sem atualizar fontes,
  conectar ao banco ou exportar registros pessoais. Nenhum conteúdo interno foi
  incluído em consultas externas ou copiado para o repositório.
- Usado interpretador temporário separado com PBIXRay, sem alterar dependências da
  aplicação. A listagem resumida do extrator omitia relacionamentos com tabelas
  calculadas; a inspeção da base de metadados embutida corrigiu essa limitação.
- Verificações executadas: leitura da estrutura ZIP, inventário de metadados e
  revisão estática de expressões e caminhos de filtro. Não executados: avaliação
  DAX, atualização, conciliação de totais, testes de RLS por usuário ou suíte da
  aplicação, pois não houve alteração de código.
- Regras encontradas no arquivo são evidência de implementação, sem aprovação
  institucional presumida. Talita e o responsável pelos dados devem validar
  população, identidade de pessoa/vínculo, períodos e critérios de carga; Matheus
  e DSI devem conferir propagação de acesso; DBA deve confirmar fontes e chaves.
- Nenhuma fase avançou, fonte física foi homologada ou publicação foi realizada.

### Complemento: documentação consolidada dos três modelos

- A pedido de Matheus, a inspeção foi ampliada aos dois PBIX adicionais indicados
  pelo usuário. Gerado um Markdown consolidado em pasta própria de Downloads,
  fora do repositório, com os três modelos, explicações, propostas, dicionário,
  relacionamentos, DAX, regras de acesso, páginas e propriedades semânticas.
- Conteúdo interno não foi incorporado ao Git. Identificadores individuais em
  fórmulas e nomes pessoais de papéis foram mascarados; literais textuais de RLS
  foram substituídos por marcadores estáveis no documento.
- Verificação estrutural: **aprovada** para cobertura de 1.841 colunas, 152
  relacionamentos e 333 medidas; 1.028 expressões DAX não vazias reproduzidas com
  os tratamentos documentados; links internos, cercas de código e UTF-8 conferidos.
  Contagens incluem estruturas automáticas de datas; não são números institucionais.
- Comandos de extração, complemento e geração com Python/PBIXRay 0.15.5 estão
  registrados no próprio artefato. Ambiente de inspeção separado; nenhuma mudança
  nas dependências da aplicação ou nos PBIX originais.
- Não executados: Power Query/M, avaliação DAX, atualização, banco institucional,
  conciliação de totais, testes de acesso por usuário, suíte da aplicação ou
  homologação visual. Somente documentação foi alterada no repositório.
- Pendências: Talita e responsáveis pelas fontes validam conceitos, exceções e
  períodos; Matheus/DSI validam acesso e vigência; DBA confirma fontes físicas,
  chaves e granularidades. As regras encontradas não foram homologadas.
- Projetos patrocinados e análises financeiras foram documentados como referência
  solicitada; continuam fora da implementação atual. Nenhuma fase avançou.

## Entrega do Prompt 2

- [Catálogo estruturado](../config/analyses.yaml) e [definições de negócio](ANALYSIS_CATALOG.md)
  para composição docente, evolução de matrículas e carga horária, nesta ordem.
  População, granularidade, unidade, chaves, parâmetros, filtros, fórmula descritiva,
  exceções, período, responsável, versões e comparação registrados como propostas.
- Fonte física não mapeada; cinco áreas de aprovação humana pendentes por análise:
  fonte, granularidade, cálculo, comparação e aceite funcional. O dicionário sanitizado
  da fase 1 permanece modelo não preenchido; nenhuma tabela ou coluna foi inventada.
- Contratos tipados de solicitação e resultado, entidades com papéis distintos,
  unidades, filtros efetivos, UUID, datas por origem, versões, avisos e estados.
  Nulo, zero, ausência de registros, não calculável e falha permanecem distintos.
- `blocked_result()` retorna motivos e dados vazios, sem consulta, cálculo ou fallback.
  Resultados reais válidos/parciais são recusados nesta fase, inclusive após mudar
  flags do catálogo. Não existe adaptador de análise real nem SQL de análise novo.
- Referências de comparação e equivalências de cursos com vigência, fonte e registro
  de aprovação; mapas sintéticos não se aplicam a modo real. Séries permanecem
  separadas diante de pendência, conflito, vigência incompleta ou cadeia não revisada.
- Contagens com igualdade exata, sem tolerância ajustável; horas dependem de critério
  explícito de arredondamento. Conferência de referência não aprova funcionalmente
  uma análise e não força resultados atuais a coincidir com uma origem antiga.
- Sete casos determinísticos: duplicidade, nulo, zero, ausência, semestre parcial,
  denominador zero e fontes com datas distintas. Expectativas de fixtures não são
  números institucionais ou aprovação de Talita.
- PyYAML 6.0.3 acrescentado e travado no `uv.lock`; 51 pacotes resolvidos para
  desenvolvimento. Catálogo incluído no wheel e carregado sem conexão ao banco.
- Reorganização e pasta de branding anteriores preservadas. Nenhuma alteração visual;
  materiais oficiais continuam pendentes para a futura interface da fase 3.

## Verificações executadas no Prompt 2

| Verificação | Resultado |
|---|---|
| `.\scripts\check.cmd` | Código 0; lock offline, Ruff e formatação aprovados; **161 testes passaram, 1 integração real excluída** |
| Novos testes da fase 2 | 44 casos cobrindo contratos, unidades, bloqueios, proveniência, igualdade de contagens, critério de horas, referências e equivalências |
| Leitura YAML | Lista fechada, prioridades e campos validados; tags executáveis, campos duplicados, escopo extra e aprovações incompletas recusados com mensagem sanitizada |
| Resultados parciais | Preservam nulos e períodos incompletos com aviso; resultado vazio ou incompleto não pode ser válido; métricas/origens ambíguas são recusadas |
| Casos sintéticos | Determinísticos e identificados; percentual com base zero não numérico; fixture não pode virar aceite funcional humano |
| Referências | Mesmo recorte/regra/origem; atualização desconhecida ou modificada bloqueia comparação automática; extração e atualização têm significados separados |
| `.\.venv\Scripts\python.exe -m vrac.analyses` | Código 0; três definições `pending`, cinco decisões pendentes por definição; nenhuma consulta ou cálculo executado |
| Wheel offline | Gerado e inspecionado: 35 arquivos; catálogo idêntico ao YAML do repositório e carregado pelo recurso empacotado; cache, ferramentas e configuração privada ausentes |

Não executados: conexão real, inventário real, cálculo de análises, conciliação com
referência de Talita, homologação funcional/visual, implantação ou execução de integração.
O guia permite esta preparação sem metadados aprovados; isso não conclui a validação
institucional da fase 1 nem autoriza avançar à fase 3 automaticamente.

## Arquivos do Prompt 2

| Grupo | Arquivos criados ou ajustados |
|---|---|
| Contratos e definições | `src/vrac/analyses/{__init__,__main__,contracts,catalog,references,courses,synthetic_cases}.py` |
| Catálogo e modelos | `config/analyses.yaml`, `config/reference_case.example.yaml`, `config/course_equivalences.example.yaml` |
| Dependências e distribuição | `pyproject.toml`, `uv.lock` |
| Testes | `tests/test_analysis_catalog.py`, `tests/test_analysis_contracts.py`, `tests/test_analysis_references.py` |
| Documentação | `docs/ANALYSIS_CATALOG.md`, `README.md`, índice, contexto, plano, arquitetura, decisões, prévia e este estado |

A lista curta de decisões para Talita e para os responsáveis pelos dados está no
[catálogo](ANALYSIS_CATALOG.md#decisões-curtas-para-validação-humana). Matheus deve
liberar somente material sanitizado autorizado e manter o mapa físico privado externo.

## Organização do repositório e branding — 27/10

- Documentação agrupada: prévia em `docs/guides/`, descoberta/dicionário/solicitações
  DSI em `docs/operations/` e guia original em `docs/references/`. O conteúdo do guia
  foi preservado e os links relativos foram ajustados.
- [Índice da documentação](README.md) e mapa do repositório no README principal,
  mantendo contexto, plano e estado nos caminhos estáveis de `docs/`.
- Criada [assets/branding/](../assets/branding/README.md), com pastas para logos,
  ícones, fontes, manuais e templates e um modelo documental de tokens de identidade.
- Branding PUC-Rio obrigatório registrado nas instruções, contexto, plano,
  arquitetura e decisões. Nenhum logo, cor, fonte ou variante oficial foi presumido.
- Matheus deve adicionar os materiais oficiais e identificar o responsável
  institucional que validará a aplicação visual. O tema atual permanece provisório;
  o modelo de tokens não é carregado pela aplicação e a interface não foi redesenhada.
- Esta manutenção altera organização e documentação; código, SQL executável,
  dependências e comandos de execução permanecem nos mesmos caminhos.

Verificações desta manutenção: links locais, sintaxe TOML, integridade do guia e diff.
A suíte de aplicação não foi repetida, pois o comportamento executável não foi alterado;
os 117 testes da fase 1 continuam como registro histórico, não como nova execução.

## Entrega da fase 1

- Extra opcional `sqlserver`: SQLAlchemy 2.1.6 e pyodbc 5.3.0 no lock; 50 pacotes
  resolvidos no ambiente de desenvolvimento. Instalar bibliotecas não confirma SGBD.
- Configuração externa explícita em `dbconfig.toml`, sem busca de credenciais ou
  leitura automática de `.env`. Endpoint, porta, banco, schemas, driver e autenticação
  precisam ser informados pelo operador; confirmações de SGBD e escopo são obrigatórias.
- CLI e atalhos manuais `diagnose-db.cmd`/`inventory-db.cmd`. Sem `--execute`, não
  há leitura da configuração, importação do adaptador ou tentativa de conexão.
- Adaptador lazy com SQLAlchemy/pyodbc, TLS e certificado validados, escape ODBC,
  timeout de login e consulta, descarte de recursos e mensagens fixas de erro.
  Logs exclusivos do engine/pool impedem emissão de erros brutos durante limpeza.
- Prova `SELECT 1` em arquivo revisado e quatro consultas fixas de catálogo,
  limitadas ao banco e schemas aprovados, com parâmetros vinculados e truncamento.
  Visibilidade é sempre desconhecida; ausência de metadados não significa inexistência.
- Saídas externas em subpasta UUID nova, protegida antes da consulta: DACL NTFS do
  usuário no Windows; diretório 0700 e arquivo 0600 no POSIX. Nenhum nome físico no console.
- Modelos agregados de qualidade/cardinalidade desabilitados, sem renderização ou
  execução pela CLI; revisão de objetos, filtros e custo permanece obrigatória.
- [Roteiro de execução](operations/DATABASE_DISCOVERY.md), revisão de privilégios pelo DBA e
  [dicionário sanitizado](operations/SANITIZED_DATA_DICTIONARY.md) com material exato para a fase 2.

## Verificações executadas na fase 1

| Verificação | Resultado |
|---|---|
| `.\scripts\bootstrap.cmd --sqlserver` | Código 0; instalação opcional conforme lock, sem alterar política de execução ou driver do sistema |
| `.\scripts\check.cmd` | Código 0; lock offline, Ruff e formatação aprovados; **117 testes passaram, 1 integração real excluída** |
| Configuração/conexão por mocks | Validação estrita, confirmações, caminhos externos, timeouts, escape ODBC, TLS, fechamento e descarte em falhas |
| Erros e logs de limpeza | Categorias sanitizadas; teste de NullPool real com DBAPI fictícia confirma que falhas de reset/close não expõem mensagem bruta |
| Inventário por mocks e compilação MSSQL | Escopos, TOP/IN vinculados, limite de consultas, truncamento, cobertura desconhecida, relações/tipos externos omitidos e resultados parciais |
| CLI por mocks | Ajuda e bloqueio sem opt-in, autorização antes de dados, saída protegida antes do banco e mensagens sem caminhos/SQL/identidade |
| Saída privada em arquivos temporários sintéticos | Proteção NTFS executada neste Windows, gravação exclusiva, recusa de sobrescrita e interrupção antes de dados quando ACL falha |
| Regressão da demonstração | Filtros, vazio, configuração inválida e modo real bloqueado continuam cobertos; timeout do AppTest ajustado para 15 s na inicialização local |
| Driver nativo na suíte padrão | `pyodbc.connect`, `pyodbc.drivers`, `Engine.connect` e rede bloqueados; testes usam somente mocks/DBAPI fictícia |
| CLI instalada e atalhos `--help` | Código 0; nenhum arquivo privado ou banco acessado |
| Wheel offline | Gerado e inspecionado: 27 arquivos, cinco consultas fixas incluídas; ferramentas locais, cache e configuração privada ausentes |
| Instalação base isolada sem extra | `uv sync --locked --offline --no-dev --no-editable`: 42 pacotes; CLI e SQL empacotado verificados sem SQLAlchemy/pyodbc |
| Exclusões e diff | Configuração real, saídas e cache ignorados; exemplos/código versionáveis; `git diff --check` sem erros |
| Bootstrap `.ps1` alterado | Sintaxe conferida pelo parser; execução não feita devido à política existente |

A primeira tentativa auxiliar de instalar o wheel offline por resolução aberta de `uv pip`
não encontrou metadados de índice no cache. A instalação base foi então conferida usando
o lock com `uv sync --locked --offline`, sem liberar rede ou alterar dependências.

Não foram executados: leitura de configuração real, enumeração de drivers reais,
conexão institucional, inventário real, consultas de qualidade, integração real,
revisão de privilégios no banco, homologação DSI/Talita ou implantação. O teste de
integração marcado exige seleção explícita, `--run-db-integration` e `--db-config`
externo; permanece reservado ao operador fora da sessão do agente.

## Arquivos da fase 1

| Grupo | Arquivos criados ou ajustados |
|---|---|
| Descoberta | `src/vrac/db/{__init__,__main__,config,errors,connection,diagnostic,inventory,private_io,cli}.py` |
| SQL revisado | `sql/diagnostics/connection_probe.sql`, quatro arquivos de `sql/catalog/`, três templates de `sql/quality/` e `sql/README.md` |
| Configuração | `config/database.example.toml`, `config/quality_checks.example.toml`, `pyproject.toml`, `uv.lock`, `.gitignore`, `.dockerignore` |
| Comandos | `scripts/diagnose-db.cmd`, `scripts/inventory-db.cmd`, `scripts/bootstrap.cmd`, `scripts/bootstrap.ps1`, `scripts/check.cmd` e `scripts/check.ps1` |
| Testes | `tests/test_db_{cli,config,connection,integration,inventory}.py`, `tests/test_private_output.py`, `tests/conftest.py`, `tests/test_ui.py` |
| Documentação | `README.md`, `docs/operations/DATABASE_DISCOVERY.md`, `docs/operations/SANITIZED_DATA_DICTIONARY.md`, contexto, plano, arquitetura, decisões e este estado |

## Fundação preparada na fase 0 — registro de 26/10

- Contexto, plano por fases, arquitetura, decisões e solicitações para DSI/DBA.
- Python 3.12.15 gerenciado em `.tools/python`, uv 0.13.5 em `.tools/uv` e `.venv` local.
- `pyproject.toml` e `uv.lock`: 48 pacotes resolvidos/instalados, incluindo o projeto.
  Versões principais: Streamlit 1.66.1, pandas 3.1.0, Matplotlib 3.11.2,
  pytest 9.1.1 e Ruff 0.17.2. Backend de construção Hatchling 1.32.4 fixado.
- Configuração pública estrita; demonstração sintética como padrão e dados reais sempre negados.
- Exemplos determinísticos com docentes repetidos por mês/vínculo, ausência, zero,
  período vazio, compartilhamento, classificação ausente e atuação interdepartamental.
- Tela em português, marca DEMONSTRAÇÃO, ação explícita, filtros em tabela e remoção
  da prévia quando a seleção muda. Nenhum cálculo institucional está implementado.
- Exclusões Git/Docker e convenções de edição; nenhum segredo ou dado institucional
  foi necessário para construir ou testar esta entrega.

## Verificações da fase 0 — registro de 26/10

| Verificação | Resultado |
|---|---|
| Instalação inicial com `.venv` inexistente | Python baixado localmente e 48 pacotes instalados pelo lock, com HTTPS e validação normal de certificados |
| Integridade do executável uv baixado | SHA256 do arquivo comparado com o hash fixado do release oficial |
| `.\scripts\bootstrap.cmd` após a instalação inicial | Código 0; Python existente reconhecido; 48 pacotes conferidos por `uv sync --locked` |
| `.\scripts\check.cmd` | Código 0; lock conferido offline, estilo e formatação aprovados; **20 testes passaram** |
| Configuração e autorização | Padrões seguros, lista pública de variáveis, configuração inválida sanitizada e acesso real negado nos três ambientes |
| Dados e interface via AppTest | Determinismo, cenários extremos, ausência distinta de zero, seleção fechada, ação explícita, troca de filtros e modo real bloqueado |
| Isolamento da suíte | Conexões normais bloqueadas, inclusive loopback; somente IPC interno de `socketpair` permitido para asyncio no Windows |
| `.\scripts\run-demo.cmd` | Serviço iniciou somente em `127.0.0.1:8501`, com telemetria desativada e sem abrir navegador |
| Saúde e página inicial do serviço local | `/_stcore/health`: HTTP 200, `ok`; `/`: HTTP 200 |
| Exclusões Git | Credenciais exemplificativas, ambientes, cache e dados privados ignorados; configuração de exemplo e código continuam versionáveis |
| Sintaxe dos scripts `.ps1` | Parser PowerShell aprovou; execução bloqueada pela política existente do Windows |

A primeira instalação usou comandos diretos revisados, pois este Windows não executa
`.ps1`. Os comandos `.cmd` são a interface de uso principal; não alteram ExecutionPolicy,
PATH, perfil ou registro do Windows. A demonstração foi iniciada somente para conferência
local, sem publicação ou acesso institucional.

## Limites e verificações não executadas

- Bootstrap completo partindo também de `.tools` vazia pela implementação `.cmd` ainda
  não foi repetido; a instalação inicial fez download com hash validado e criou `.venv`
  limpa, e a execução posterior do launcher foi verificada. O fluxo de download inclui
  também comparação com o `.sha256` oficial.
- Windows ARM64 e ambiente do servidor não foram testados; suporte previsto precisa
  ser conferido na plataforma efetivamente aprovada.
- Revisão visual em navegador e avaliação de usabilidade por Talita ainda não realizadas;
  os testes de interface executados foram automatizados via AppTest. Em 27/10, a prévia
  local respondeu HTTP 200, mas o Computer Use interrompeu a revisão visual por falta
  de suporte à política de URLs no navegador Windows atual. Roteiro em [PREVIEW.md](guides/PREVIEW.md).
- Sem conexão ao banco, credenciais, inventário, consultas reais, conciliação funcional,
  autenticação institucional, teste de segurança em homologação ou implantação.
- SQL Server permanece hipótese. Em 27/10, Matheus autorizou o envio ao remoto GitHub
  configurado; a API confirmou `matheusmaccioly/relatorios-automatizados_VRAC` como privado.
  Esse envio de código e dados sintéticos não representa implantação do aplicativo
  nem autorização para compartilhar fontes ou metadados institucionais.

## Validações externas e próximo incremento

| Responsável | Pendência |
|---|---|
| Matheus | Confirmar repositório privado/autorizado; executar diagnóstico/inventário fora da sessão do agente; revisar e liberar somente material sanitizado |
| DSI | Servidor/plataforma, rede, HTTPS, login institucional, autorização, segredos, retenção e operação |
| DBA | SGBD, autenticação, fontes e escopos aprovados, conta técnica de leitura e limites de consulta |
| Talita | Avaliar a demonstração e, antes dos cálculos reais, aprovar definições e caso de referência da composição docente |

Próximos passos: confirmar SGBD e escopos com DSI/DBA e executar manualmente as ferramentas
da fase 1, fora da sessão do agente; obter o dicionário sanitizado e o aceite humano das
definições e da referência de composição docente antes da implementação real.
A lista detalhada está em [DSI_REQUESTS.md](operations/DSI_REQUESTS.md). Nenhuma pendência foi
tratada como aprovação nem exige modificar o cálculo oficial para avançar.

## Arquivos da fundação — registro de 26/10

| Grupo | Arquivos |
|---|---|
| Instruções e setup | `AGENTS.md`, `README.md`, `pyproject.toml`, `uv.lock`, `.python-version`, `.editorconfig`, `.gitattributes`, `.gitignore`, `.dockerignore`, `.streamlit/config.toml` |
| Aplicação | `app.py`, `src/vrac/__init__.py`, `settings.py`, `authorization.py`, `synthetic.py`, `ui.py` no mesmo pacote |
| Configuração e SQL | `config/settings.example.toml`, `sql/README.md` |
| Comandos Windows | `scripts/bootstrap.cmd`, `check.cmd`, `run-demo.cmd`; alternativas `bootstrap.ps1`, `check.ps1`, `run-demo.ps1` e `uv-env.ps1` na mesma pasta |
| Testes | `tests/conftest.py`, `test_foundation.py`, `test_ui.py`, `test_offline.py` |
| Documentação | `docs/PROJECT_CONTEXT.md`, `PLAN.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `DSI_REQUESTS.md`, `STATUS.md` |

O arquivo `docs/references/Guia_Desenvolvimento_VRAC_Codex.md` já existia e foi mantido sem alterações.
