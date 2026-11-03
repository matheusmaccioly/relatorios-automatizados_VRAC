# Próximos passos para avançar no desenvolvimento

Atualizado em 03/11/2026. Documento para Matheus, Talita e responsáveis pelas fontes.
Complementa o [plano](PLAN.md) e o [catálogo de análises](ANALYSIS_CATALOG.md).
Registra pendências; não constitui aprovação ou avanço de fase.

## Objetivo imediato

**Prompt 4a concluído no escopo sintético:** em 03/11, Matheus confirmou nesta
conversa “tudo validado por mim e conciliado”. Próximo incremento: **4b, carga
horária**, mediante solicitação própria, reutilizando o que já existe.
Nenhuma implementação da 4b iniciada nesta atualização documental.

Evidência anterior pelo agente: [registro R06](guides/PROMPT4A_MATRICULAS.md),
38 cenários/2.612 comparações sem divergência, correções pontuais em formados por
curso e descrição de variação ausente, testes de filtros/arquivos/lacunas.
Conciliação posteriormente confirmada por Matheus; nenhuma execução PostgreSQL
ou inspeção de relatório adicional ocorreu na sessão do agente.
Talita revisa clareza e uso. Não publicar automaticamente.
Fontes e integração institucionais permanecem para a etapa final e deploy.

**Prompt 3 implementado em 03/11:** composição/comparação/histórico docentes e
gráficos Altair, reutilizando R04/R05. [Entrega e roteiro](guides/PROMPT3_DOCENTES.md).
Revisar manualmente os gráficos em desktop/janela estreita e avaliar o uso com
Talita; automação do navegador bloqueada por política de URLs. Não houve leitura
PostgreSQL ou institucional. Outros prompts somente quando solicitados.
O parágrafo seguinte preserva o ponto de partida do Prompt 2.

**Prompt 2 concluído em 03/11:** [mapa R01–R06](operations/SYNTHETIC_SOURCE_MAP.md)
e catálogo alinhados à implementação, conferidos offline. A conexão de leitura
sintética não pôde ser conferida por certificado local ausente. O Prompt 3, quando
solicitado, poderá reutilizar R01, SQL/leitores, fixtures e testes sem inventário
institucional. Para futura conferência viva, recuperar o ambiente sintético pelo
procedimento existente, preservando TLS. Esta tarefa não avançou ao Prompt 3.

**Diretriz vigente (D-028): continuar na base sintética existente até a etapa final
do projeto e deploy.** Próximos prompts podem completar mapa lógico, fluxos,
verificações, exportações e feedback sem configuração real ou inventário
institucional. Diagnóstico/inventário reais, mapa físico e conferência institucional
ficam para a etapa final; as referências seguintes a esses itens têm esse momento.

Os seis roteiros já estão disponíveis sobre a base sintética (D-027), por solicitação
posterior de Matheus para implementar todas as análises documentadas. Começar pelo
[guia de uso](guides/ANALISES_SINTETICAS.md): carregar o snapshot, calcular os roteiros
e conferir tabelas e arquivos. A evolução agora envolve ajustes concretos de uso e,
se solicitado, preparação da integração institucional com DSI/DBA. Não pedir nova
aprovação de fórmulas documentadas. As descrições abaixo preservam o encaminhamento
anterior da primeira análise e devem ser lidas conforme este estado atual.

Matheus solicitou em 30/10/2026 uma base sintética em PostgreSQL a partir do modelo
semântico documentado (D-023). A preparação local está descrita no
[guia de PostgreSQL sintético](operations/SYNTHETIC_POSTGRES.md). Essa base será
usada nos próximos incrementos solicitados, sem exigir extração de dados reais.

A ligação da tela à base sintética foi solicitada e implementada na sequência
(D-025): filtros, registros docentes e alocações por turma já são consultados no
PostgreSQL. O próximo incremento analítico será construído sobre essa conexão,
conforme a solicitação de fase, sem exigir nova aprovação das regras documentadas.

Preparar a reprodução da primeira análise, **composição docente de um departamento
e período**, usando os dashboards existentes e as regras já documentadas. Conforme
orientação explícita de Matheus em 30/10/2026 (D-022), não é necessária nova validação
analítica nem rodada de perguntas a Talita para aprovar essas regras.

## O que falta e quem confirma

| Prioridade | Entrega necessária | Quem confirma | Evidência esperada |
|---|---|---|---|
| 1 | Localizar no dashboard e na documentação a unidade de contagem, situações e tratamento de vínculos | Matheus/Codex no desenvolvimento | Referência à regra existente, sem nova aprovação |
| 2 | Reproduzir referência temporal, calendário, QP e categorias do dashboard | Matheus/Codex no desenvolvimento | Implementação fiel às definições documentadas |
| 3 | Mapa lógico/sintético concluído por código e fixture; falta repetir conferência no PostgreSQL após recuperar certificado local. Fontes institucionais somente na etapa final | Matheus no próximo incremento sintético; DBA + Matheus somente na etapa real | Mapa versionável disponível; nenhuma correspondência real presumida |
| 4 | Conferir tecnicamente o código contra as regras documentadas com testes offline | Matheus/Codex no desenvolvimento | Testes técnicos; nenhum novo caso institucional exigido para aceitar a regra |
| 5 | Demonstrar o fluxo e conferir filtros, leitura dos resultados e downloads | Matheus + Talita | Feedback registrado e aceite funcional humano da entrega implementada |

A última linha acontece depois da implementação e trata do uso da aplicação.
Os testes técnicos devem preservar recorte, regra e referência temporal do dashboard.
Contagens inteiras devem coincidir, sem relaxar tolerância para forçar igualdade.

## Referências a localizar nos materiais existentes

1. Para um departamento e período, quem deve entrar na contagem?
2. O total representa pessoas distintas ou matrículas funcionais?
3. Quer uma foto em uma referência específica ou a presença em qualquer mês do semestre?
4. Quais situações e tipos de vínculo entram ou ficam de fora?
5. Como tratar uma pessoa com mais de um vínculo ou mudanças de categoria/departamento?
6. O que define QP e quais categorias devem aparecer? Como tratar classificação ausente?
7. Qual resultado você usa hoje para conferir, e quais filtros e datas ele considera?

Esta lista orienta a leitura dos materiais, sem exigir nova conversa de validação.
Registrar a referência documental de cada regra. Se houver lacuna ou contradição,
identificá-la concretamente e limitar seu efeito ao resultado afetado.

## Conexão e fontes de dados

**Execução institucional somente na etapa final e deploy (D-028).** Não completar
configuração real nem executar diagnóstico/inventário como próximo passo agora.
O desenvolvimento usa a conexão PostgreSQL sintética já implementada.

Servidor e banco foram informados por Matheus, assim como a criação de seu usuário
e a autorização dos schemas necessários. Ainda faltam porta TCP, lista nominal de
schemas, autenticação, driver e confirmação administrativa de somente leitura.
O [guia simplificado de configuração](operations/CONFIGURAR_KAPPA.md) já contém o
modelo preparado e os campos que precisam ser completados.

Depois de completar a configuração, Matheus executa diagnóstico e inventário no
ambiente autorizado, fora da sessão do agente, conforme o
[roteiro técnico](operations/DATABASE_DISCOVERY.md). Somente material sanitizado e
autorizado deve retornar ao desenvolvimento. Credenciais e inventário bruto
permanecem privados e fora do repositório.

Conseguir conectar não comprova chaves ou cobertura física. As regras de contagem
serão reproduzidas dos dashboards conforme a D-022.

## Entrega esperada do Prompt 3

Quando a fase 3 for solicitada, construir o fluxo de composição
docente com repositório de dados, cálculo separado da interface, filtros de
departamento/período, tabela, gráfico e download inicial. Incluir fontes, datas,
filtros efetivos, unidades, limitações e estados de pronto, execução, vazio,
parcial, bloqueio e erro.

O fluxo sintético deve ser visivelmente identificado e não pode aparecer como
resultado real. Se o mapeamento físico continuar pendente, o adaptador real deve
permanecer bloqueado. A ligação real só poderá ser declarada validada após teste
humano registrado. Testes sintéticos não aprovam regras institucionais.

Antes disso, é possível continuar a preparação e os testes sintéticos dos contratos.
Não iniciar os cálculos com regras presumidas nem avançar para matrículas e carga
antes de revisar a primeira entrega docente.

## Identidade visual e preparação do piloto

A identidade visual já foi aplicada aos materiais disponíveis. Falta conferir a
tela no navegador e revisar a aplicação com Matheus e o responsável institucional.
Talita deve avaliar legibilidade e uso. Divergências e regras visuais ainda não
documentadas estão registradas em [branding](../assets/branding/README.md).

Autenticação institucional, autorização da usuária, hospedagem, conta definitiva
do serviço e operação precisam ser encaminhadas com a DSI/DBA. São necessárias
para o acesso real e piloto; não impedem a demonstração local com dados sintéticos.
A conta de banco do desenvolvedor não será automaticamente a conta do serviço.

## Próxima ação prática

Seguir, quando solicitado, ao trabalho restante do Prompt 2 sobre o mapa
lógico/sintético e depois aos incrementos dos Prompts 3–5 e feedback nessa base.
Reproduzir fórmulas documentadas sem nova validação geral ou reunião obrigatória.
Manter o roteiro institucional disponível para a etapa final, sem solicitar sua
execução agora nem tratar a ausência de retorno real como bloqueio do desenvolvimento.

Esta documentação não envia mensagens, não executa conexão, não publica a aplicação
e não altera aprovações. O estado efetivo continua em [STATUS.md](STATUS.md).
