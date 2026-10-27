# Arquitetura inicial

Atualizado em 27/10/2026. Escopo técnico: demonstração sintética da fase 0 e ferramentas manuais da fase 1, sem conexão institucional validada. O desenho segue o [contexto](PROJECT_CONTEXT.md) e o [plano](PLAN.md).

## Organização

Adotar um monólito modular em Python: Streamlit apresenta a interface; funções Python contêm comportamento testável; pandas trata tabelas; Matplotlib será usado nos gráficos exportáveis. Não introduzir API separada, frontend adicional, filas ou infraestrutura distribuída nesta PoC.

| Caminho | Responsabilidade na fundação |
|---|---|
| `app.py` | Entrada da aplicação Streamlit |
| `src/vrac/settings.py` | Configuração explícita de ambiente e modo de dados; rejeição de opções inválidas |
| `src/vrac/authorization.py` | Contrato de autorização e negação de acesso a dados reais enquanto a integração institucional estiver ausente |
| `src/vrac/synthetic.py` | Dados mínimos determinísticos e identificados como fictícios; nenhum acesso ao banco |
| `src/vrac/ui.py` | Demonstração em português, filtros e apresentação dos dados sintéticos |
| `config/` | Exemplos de configuração sem credenciais ou nomes físicos institucionais |
| `sql/` | Local reservado para consultas revisadas de fases futuras; nenhuma consulta institucional na fase 0 |
| `tests/` | Testes offline de configuração, autorização, dados sintéticos e interface |
| `scripts/` | Rotinas de preparação e execução local |
| `docs/` | Contexto, planejamento, decisões, critérios e pendências |

Separar acesso a dados, análises, verificações, gráficos e exportações conforme cada capacidade for implementada. Não criar módulos vazios para antecipar todas as fases. As funções de cálculo não dependerão de Streamlit. Consultas reais ficarão em arquivos SQL revisados, com parâmetros vinculados e uma lista fechada de operações.

## Ambiente reproduzível

O setup fixa Python 3.12.15 e uv 0.13.5, com dependências e ferramentas de desenvolvimento registradas em `pyproject.toml` e versões resolvidas em `uv.lock`. O ambiente virtual fica em `.venv`; a instalação gerenciada local de Python fica em `.tools/python` e o cache em `.cache/uv`. Esses diretórios são locais e não entram no Git.

A instalação inicial exige acesso às fontes públicas de ferramentas e pacotes. Após instaladas as dependências, a suíte sintética deve executar sem banco ou internet. Os comandos efetivamente verificados ficam no README e no registro de estado da entrega.

Python do servidor, sistema operacional, driver ODBC e método de autenticação do banco dependem da DSI. O setup Windows de desenvolvimento não comprova compatibilidade de implantação. SQLAlchemy e pyodbc são dependências do extra opcional `sqlserver`, preparado na fase 1. Sua instalação não confirma o SGBD: criação do engine exige confirmação e escopo aprovados. Biblioteca XLSX será adicionada quando a exportação correspondente for implementada.

## Fluxo da fase 0

1. Carregar somente a configuração não sensível prevista pela aplicação.
2. Validar ambiente e modo explicitamente.
3. Aplicar autorização antes de disponibilizar dados.
4. Em demonstração sintética local, carregar a fixture determinística e identificar a tela como DEMONSTRAÇÃO.
5. Em solicitação de modo real, negar acesso: não há adaptador institucional, login ou escopo aprovado.

Não há conexão automática, login fictício liberando dados reais, SQL arbitrário ou troca silenciosa de modo em caso de falha. O bloqueio do modo real faz parte da fundação e não constitui implementação da autenticação institucional da fase 6.

## Dados e apresentação

A fixture utiliza identificadores e rótulos artificiais; permite exercitar repetição de docentes, diferentes vínculos, períodos sem dados e alocações compartilhadas. Números e chaves da fixture não representam tabelas ou regras da PUC-Rio. A demonstração não calcula indicadores institucionais nem concilia resultados reais.

Resultados futuros manterão filtros efetivos junto aos dados; alterar a seleção da tela não poderá apresentar um resultado antigo como recalculado. Dados ausentes, nulos, zeros e falhas terão significados distintos. Extração e atualização da origem serão datas separadas. Exportações e verificações futuras carregarão os mesmos filtros, versões e avisos da execução exibida.

## Descoberta manual — fase 1

O pacote `src/vrac/db/` é separado da UI e de sua autorização. `config.py` valida a cópia externa privada; `connection.py` prepara SQLAlchemy/pyodbc sem conexão durante importação; `errors.py` classifica falhas com mensagens fixas. `diagnostic.py` prova `SELECT 1`; `inventory.py` executa somente o catálogo revisado em `sql/catalog/`. `cli.py` exige execução explícita, registra identificador/datas e usa `private_io.py` para proteger a saída antes de tocar o banco.

A configuração define um endpoint, uma porta, um banco, autenticação, driver e de um a oito schemas; nenhum desses valores é descoberto por varredura. TLS é fixo, há timeout de login e de consulta antes das instruções iniciais do dialeto, e o pool da SQLAlchemy/pyodbc é desativado para descartar conexões ao encerrar o comando. Logs privados do engine/pool não devem expor exceções brutas.

São até quatro consultas de catálogo por schema, com parâmetros vinculados, limite de saída e truncamento explícito. SQLAlchemy pode executar instruções internas de inicialização do dialeto além desse catálogo. Visibilidade permanece desconhecida; uma consulta sem linhas não demonstra inexistência. Chaves e relações podem estar incompletas, inclusive quando o limite interromper uma chave composta.

Os SQL revisados também são incluídos no wheel por `force-include`, para leitura da mesma lista fechada de consultas fora do checkout. `sql/quality/` contém somente templates não executáveis; não há renderizador nem comando que os rode. O [roteiro operacional](DATABASE_DISCOVERY.md) descreve validação do DBA e os materiais sanitizados para a fase 2.

## Limites entre ambientes

Credenciais e arquivos privados permanecem fora do workspace do agente. Exemplos versionados não terão valores reais. `.gitignore` e `.dockerignore` reduzem inclusão acidental, mas não substituem controle de acesso ou isolamento.

Antes de permitir dados reais: autenticar pela solução aprovada, autorizar por identidade, departamento, análise e detalhe, confirmar conta técnica de leitura, TLS e certificado, controlar a recuperação de resultados e a exportação, e homologar sessões e retenção. Não haverá cache global de dados restritos por conveniência.

O serviço pretendido é interno, atrás de HTTPS e proteção institucional, independente do computador do desenvolvedor. Container, OIDC, proxy autenticado e SQLite operacional são possibilidades sujeitas à decisão registrada; nenhum foi adotado como infraestrutura institucional confirmada.

## Referências técnicas verificadas

- [Instalação oficial do uv](https://docs.astral.sh/uv/getting-started/installation/): distribuição standalone com versão fixa, também disponível nos releases oficiais.
- [Lock e sincronização do uv](https://docs.astral.sh/uv/concepts/projects/sync/): `sync --locked` usa o lock versionado e rejeita mudanças na resolução.
- [Armazenamento local do uv](https://docs.astral.sh/uv/reference/storage/): configuração dos diretórios de Python e cache.
- [AppTest do Streamlit](https://docs.streamlit.io/develop/api-reference/app-testing): testes da interface sem abrir navegador.

As referências orientam a implementação técnica; não validam infraestrutura ou regras institucionais.
