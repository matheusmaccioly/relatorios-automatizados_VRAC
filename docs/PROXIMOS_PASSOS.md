# Próximos passos para avançar no desenvolvimento

Atualizado em 29/10/2026. Documento para Matheus, Talita e responsáveis pelas fontes.
Complementa o [plano](PLAN.md) e o [catálogo de análises](ANALYSIS_CATALOG.md).
Registra pendências; não constitui aprovação ou avanço de fase.

## Objetivo imediato

Fechar a definição da primeira análise com Talita: **composição docente de um
departamento e período**. Não é necessário resolver todos os módulos agora.
Além de configurar a conexão, precisamos saber quem entra na contagem, qual é a
referência temporal e como conferir o resultado.

## O que falta e quem confirma

| Prioridade | Entrega necessária | Quem confirma | Evidência esperada |
|---|---|---|---|
| 1 | Definir se a contagem representa pessoas ou matrículas funcionais, situações incluídas e tratamento de múltiplos vínculos | Talita + responsável pela fonte | Definição escrita da população, unidade e deduplicação |
| 2 | Escolher foto em uma data ou presença em qualquer mês do semestre; definir QP e categorias | Talita + responsável pela fonte | Referência temporal, calendário e critérios de classificação aprovados |
| 3 | Identificar fontes físicas, colunas, chaves e cobertura das definições escolhidas | DBA + Matheus | Dicionário sanitizado autorizado, com granularidade e vínculos entre fontes |
| 4 | Preparar exemplo pequeno, sanitizado e autorizado, com resultado esperado no mesmo recorte | Talita + responsável pela fonte | Caso de referência com filtros, regra, data e contagens esperadas |
| 5 | Demonstrar o fluxo e conferir filtros, leitura dos resultados e downloads | Matheus + Talita | Feedback registrado e aceite funcional humano da entrega implementada |

A última linha acontece depois da implementação da primeira entrega. Não confundir
a aprovação prévia do significado do indicador com o aceite do fluxo funcionando.
Uma conferência numérica só é válida quando recorte, regra e referência temporal
são compatíveis. Contagens inteiras devem coincidir, sem relaxar tolerância para
forçar igualdade.

## Perguntas para a conversa com Talita

1. Para um departamento e período, quem deve entrar na contagem?
2. O total representa pessoas distintas ou matrículas funcionais?
3. Quer uma foto em uma referência específica ou a presença em qualquer mês do semestre?
4. Quais situações e tipos de vínculo entram ou ficam de fora?
5. Como tratar uma pessoa com mais de um vínculo ou mudanças de categoria/departamento?
6. O que define QP e quais categorias devem aparecer? Como tratar classificação ausente?
7. Qual resultado você usa hoje para conferir, e quais filtros e datas ele considera?

Pergunta inicial sugerida:

> Para um departamento e período, quem deve entrar na contagem e qual número você
> usa hoje para conferir?

Registrar respostas, responsável, data, versão da regra e referência autorizada.
Enquanto não houver confirmação, manter a regra identificada como proposta.

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

Conseguir conectar não comprova as regras analíticas, as chaves ou a cobertura.
A autorização dos schemas também não define, por si só, como contar docentes.

## O que já está construído — 29/10/2026

O fluxo da composição docente foi implementado com a regra de contagem como parâmetro
explícito. Isso muda a conversa com Talita: não é mais necessário escolher a regra para
ver o fluxo funcionando. A tela já executa filtros, cálculo, tabela, gráfico, metadados,
avisos e download, com dados fictícios.

As quatro candidatas documentadas estão disponíveis na tela, todas rotuladas
**NÃO APROVADA**:

1. Pessoas distintas, foto em uma data.
2. Pessoas distintas presentes em qualquer mês do período.
3. Matrículas funcionais na última referência de cada vínculo.
4. Matrículas funcionais no último mês do recorte.

Na demonstração, o mesmo recorte devolve números diferentes conforme a candidata — por
exemplo 2 pessoas contra 3 matrículas funcionais no mesmo departamento e período. Isso
é material de conversa: Talita pode ver a consequência de cada definição antes de
escolher, em vez de decidir no abstrato.

Enquanto a escolha não estiver registrada com data e evidência, o resultado aparece como
**parcial**, com as pendências nomeadas na tela e repetidas na exportação. Nenhum número
desta seção tem validade institucional, e o modo real continua bloqueado.

## Entrega esperada do Prompt 3

Com a definição da primeira análise registrada, construir o fluxo de composição
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

Matheus organiza uma conversa curta com Talita e o responsável pela fonte. Com o fluxo
já construído, a conversa pode ser feita **na frente da tela**: mostrar as quatro
candidatas no mesmo recorte, comparar os números que cada uma produz e registrar qual
corresponde ao que Talita usa hoje. Em paralelo, solicitar ao DBA/DSI os detalhes
técnicos que faltam na configuração.

Se a definição de Talita não corresponder a nenhuma das quatro candidatas, registrar a
regra descrita por ela; a camada de cálculo aceita uma regra nova sem reescrever o fluxo.

Esta documentação não envia mensagens, não executa conexão, não publica a aplicação
e não altera aprovações. O estado efetivo continua em [STATUS.md](STATUS.md).
