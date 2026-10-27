# Plano de desenvolvimento

Atualizado em 27/10/2026. O [guia original](../Guia_Desenvolvimento_VRAC_Codex.md) define as fases; este documento organiza entregas, responsáveis e critérios de passagem. A fase 0 está preparada e a solicitação atual autoriza a implementação técnica do Prompt 1. A integração institucional continua pendente; fases 2–7 permanecem planejadas e não iniciadas.

Não há prazo fechado: acesso, fontes, regras e infraestrutura ainda dependem de validação. O esforço técnico deve ser registrado separadamente da espera por decisões institucionais. Nenhuma passagem de fase ou publicação é automática.

## Fase 0 — fundação e demonstração

**Estado:** fundação técnica concluída e verificada em Windows x64. Instalação local, lock e estilo aprovados; 20 testes offline passaram na fase 0. Evidências e verificações atuais em [STATUS.md](STATUS.md). **Responsável técnico:** Matheus, com apoio do Codex no código e nos testes offline. A fase 1 foi iniciada nesta solicitação; as fases 2–7 permanecem não iniciadas.

| Entrega | Critério de aceite |
|---|---|
| Contexto, plano, instruções permanentes e decisões | Documentos consistentes com o guia; hipóteses e pendências identificadas |
| Projeto Python modular e instalação reproduzível | Dependências registradas em `pyproject.toml` e `uv.lock`; instalação em ambiente limpo conferida ou limitação documentada |
| Configuração por ambiente e modo de dados | Desenvolvimento sintético como padrão; valores inválidos falham de forma explícita; modo real exige escolha explícita |
| Dados sintéticos com semente fixa | Docentes repetidos, vínculos diferentes, período vazio e carga compartilhada disponíveis para teste; nenhuma cópia institucional |
| Demonstração local em português | Marca DEMONSTRAÇÃO visível; filtros apresentados em tabela; ausência de resultados não é apresentada como zero |
| Bloqueio de dados reais | Autorização nega acesso sem mecanismo institucional; nenhuma conexão nem fallback sintético em modo real |
| Proteções e verificações | Exclusões de segredos, caches, exportações e dados privados; testes sintéticos e estilo executados sem banco; resultados registrados |
| Pendências institucionais | Lista de solicitações para DSI/DBA preparada, sem envio automático |

Antes do encerramento, registrar comandos de instalação, execução e validação, testes que passaram ou falharam, limitações e arquivos alterados. Não declarar instalação ou testes aprovados por mera existência dos arquivos.

## Fase 1 — preparação técnica e execução pelo operador

As ferramentas manuais de configuração, conexão, diagnóstico e inventário estão implementadas. Consultas fixas usam parâmetros vinculados, limites por schema e timeouts. SQL Server permanece hipótese; o operador deve confirmar SGBD e escopo. Saídas privadas ficam fora do workspace e mensagens de erro são sanitizadas.

O [roteiro de descoberta](DATABASE_DISCOVERY.md) contém comandos, revisão de privilégios e interpretação das limitações. O [dicionário sanitizado](SANITIZED_DATA_DICTIONARY.md) define o material autorizado esperado antes da fase 2. Consultas de qualidade/cardinalidade são apenas templates e não podem ser executadas pela CLI.

**Conexão e inventário institucionais: NÃO VALIDADOS.** A preparação de código não satisfaz o critério humano de passagem da fase 1. O operador deve executar os comandos em ambiente autorizado, o DBA confirmar escopos e privilégios de leitura e Matheus liberar somente material sanitizado. Nenhum resultado real foi inventado.

## Backlog das próximas fases

| Fase e estado | Próximo incremento executável | Evidência necessária para avançar | Validação |
|---|---|---|---|
| 1 — ferramentas preparadas; validação institucional pendente | Adaptador condicional opcional, CLI manual, inventário restrito e testes offline implementados; confirmar SGBD e executar diagnóstico fora da sessão do agente | Matheus registra conexão no ambiente autorizado; DBA confirma conta de leitura e objetos permitidos; material sanitizado aprovado fica disponível | Matheus + DBA; DSI para rede/TLS |
| 2 — não iniciada | Formalizar primeiro a composição docente em catálogo, contratos lógicos, mapeamento e casos sintéticos; registrar fórmulas e granularidade | Definição, fonte, recorte temporal, chaves e exemplo de referência aprovados; pendências bloqueiam apenas o resultado afetado | Talita + responsável pelas fontes/DBA + Matheus |
| 3 — não iniciada | Entregar composição docente de ponta a ponta: filtros, consulta parametrizada revisada, cálculo separado da interface, tabela, gráfico, metadados e exportação inicial | Testes de duplicidade, vazio e mudança de filtros; conciliação com caso de mesmo recorte e data; demonstração e feedback registrados | Matheus + Talita |
| 4a — não iniciada | Implementar matrículas por curso/período, com definição validada de matrícula/aluno, ausências e equivalências vigentes | Série conciliada; base zero sem percentual; cursos renomeados e períodos ausentes cobertos por testes | Talita + responsável pelas fontes + Matheus |
| 4b — não iniciada | Implementar Horas Reais e detalhamento em visões distintas; validar atuação interdepartamental, compartilhamentos, classificação e turmas vazias | Conciliação própria de carga; unidade e cobertura explícitas; nenhuma regra oficial alterada silenciosamente | Talita + responsável pelas fontes + Matheus |
| 5 — não iniciada | Criar catálogo fechado de verificações, estados de aprovação, exportações e feedback; avaliar armazenamento operacional separado | Recusa não executa consulta; mudança de filtros/dados invalida aprovação; rerun não duplica; arquivos preservam filtros, avisos e proteção contra fórmulas | Matheus + Talita; DSI para armazenamento/retenção |
| 6 — não iniciada | Integrar login aprovado, aplicar autorização antes de consultar/recuperar/exportar e testar isolamento de sessão | Homologação de autenticação, escopos, conta técnica, HTTPS, cache e retenção; aceite de segurança e funcional registrado | DSI + DBA + Talita + Matheus |
| 7 — não iniciada | Preparar serviço interno, configuração de operação, suporte, atualização, retorno de versão e guia de uso | Responsável autoriza publicação; operador confirma implantação; Talita conclui casos acordados; suporte e recuperação definidos | DSI/operador + Talita + Matheus |

Na fase 1, os scripts são preparados pelo agente e executados manualmente pelo desenvolvedor autorizado fora da sessão. Conexão e inventário permanecem **NÃO VALIDADOS** até haver evidência humana registrada. Não testar escrita para verificar permissão.

A fase 4 tem dois incrementos: revisar matrículas antes de iniciar carga horária. A fase 7 começa pela preparação; publicar exige autorização explícita do responsável. Sem infraestrutura aprovada, manter demonstrações acompanhadas com dados sintéticos.

## Revisões e critérios comuns

Após cada entrega das fases 3, 4a, 4b e 5: demonstrar, registrar feedback sanitizado, separar erro técnico de regra pendente e pedido fora do escopo, priorizar o menor ajuste autorizado e testar novamente. Feedback de usabilidade não equivale à aprovação de fórmula.

Cada análise deve ser testável sem Streamlit. A suíte padrão permanece offline; testes reais serão separados e explícitos. A comparação de resultados exige os mesmos filtros, regras e referência temporal. Histórico exato depende de fonte versionada ou snapshot autorizado; logs e hashes isolados não garantem reprodução.

## Pendências que orientam o próximo trabalho

| Pendência | Responsável por encaminhar/validar | Momento necessário |
|---|---|---|
| Confirmar repositório privado autorizado e política de compartilhamento com o agente | Matheus + responsável institucional | Antes de compartilhar material interno |
| SGBD, autenticação, rede, TLS, fontes e privilégios de leitura | Matheus + DBA/DSI | Fase 1 |
| Definição de composição docente e caso de referência sanitizado | Talita + responsável pelas fontes | Fase 2 |
| Semântica de matrículas, equivalências de cursos e regras de carga | Talita + responsável pelas fontes | Antes de cada incremento da fase 4 |
| Servidor, identidade institucional, autorização e conta técnica | DSI + DBA | Solicitar desde a fase 0; concluir antes do acesso real autônomo |
| Limiar das verificações, retenção e uso de SQLite operacional | Talita + DSI + Matheus | Fase 5, conforme decisão |
| Canal de suporte, operador e autorização de publicação | DSI + responsável pelo piloto | Fases 6 e 7 |

As [solicitações para a DSI](DSI_REQUESTS.md) são um roteiro preparado para Matheus. Sua existência não registra envio, aprovação ou provisionamento.
