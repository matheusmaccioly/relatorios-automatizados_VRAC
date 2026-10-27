# Estado da entrega

Atualizado em 27/10/2026. **Prompt 1 implementado para execução manual pelo operador.**
**Conexão e inventário institucionais: NÃO VALIDADOS.** SQL Server permanece hipótese.
Fase 0 preparada; fases 2–7 não iniciadas. O guia original e `AGENTS.md` foram preservados.

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
- [Roteiro de execução](DATABASE_DISCOVERY.md), revisão de privilégios pelo DBA e
  [dicionário sanitizado](SANITIZED_DATA_DICTIONARY.md) com material exato para a fase 2.

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
| Documentação | `README.md`, `docs/DATABASE_DISCOVERY.md`, `docs/SANITIZED_DATA_DICTIONARY.md`, contexto, plano, arquitetura, decisões e este estado |

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
  de suporte à política de URLs no navegador Windows atual. Roteiro em [PREVIEW.md](PREVIEW.md).
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

Próximo passo da fase 1: confirmar SGBD e escopos com DSI/DBA e executar manualmente
as ferramentas preparadas, fora da sessão do agente, com registro humano do resultado.
A lista detalhada está em [DSI_REQUESTS.md](DSI_REQUESTS.md). Nenhuma pendência foi
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

O arquivo `Guia_Desenvolvimento_VRAC_Codex.md` já existia e foi mantido sem alterações.
