# Próximos passos para avançar no desenvolvimento

Atualizado em 30/10/2026. Documento para Matheus, Talita e responsáveis pelas fontes.
Complementa o [plano](PLAN.md) e o [catálogo de análises](ANALYSIS_CATALOG.md).
Registra pendências; não constitui aprovação ou avanço de fase.

## Objetivo imediato

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
| 3 | Identificar fontes físicas, colunas, chaves e cobertura das definições escolhidas | DBA + Matheus | Dicionário sanitizado autorizado, com granularidade e vínculos entre fontes |
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

Matheus organiza uma conversa curta com Talita e o responsável pela fonte para
responder às perguntas acima e escolher um caso de conferência. Em paralelo,
solicita ao DBA/DSI os detalhes técnicos que faltam na configuração.

Esta documentação não envia mensagens, não executa conexão, não publica a aplicação
e não altera aprovações. O estado efetivo continua em [STATUS.md](STATUS.md).
