## Extração individual pseudonimizada — 10/11/2026

Matheus solicitou identificadores fictícios consistentes entre consultas, preservando
linhas individuais para teste. Preparado pacote SQL local de leitura com HMAC e chave
privada preenchida apenas pelo operador fora do workspace. Pessoas e vínculos têm
IDs separados; nomes/identificadores diretos e dados pessoais desnecessários removidos.
Oferta compartilhada preservada; atributos analíticos restantes continuam restritos,
sem alegação de anonimização. Lista de pessoas e cadastro por vínculo separados.
[Pacote, execução e limites](operations/departamentos.local/pseudonimos/LEIA_ME.md).
Cinco testes offline passaram com dados sintéticos e primitivas de referência;
SQL Server, desempenho e integração não executados. App inalterado, sem conexão,
publicação ou avanço de fase. Não existe chave real no pacote nem dados reais lidos.

## Restrição de saída e conferência IND — 10/11/2026

Matheus informou que a consulta de cadastro mostra todos os docentes esperados
em IND. Confirmação humana de presença; não comprova exclusividade, unicidade,
horas ou outros departamentos. Solicitou saída sem dados sensíveis.
Preparado resumo local somente com total de vínculos distintos, sem registros
individuais. O pacote detalhado anterior contém dados pessoais e não atende à
restrição de compartilhamento; não enviar suas saídas ao agente. Hash de CPF não
é anonimização. Nenhum resultado individual foi recebido ou armazenado.
App e consultas detalhadas não foram alterados; nenhuma execução SQL Server.

## Unidades compartilhadas de oferta — 10/11/2026

Matheus informou que CPE e UCB oferecem disciplinas para vários cursos com docentes
de diferentes departamentos do CTC. Mantida seleção pela alocação atual do docente;
oferta compartilhada não muda sua unidade de seleção. As consultas locais de turmas
e horários já preservam oferta externa por vínculo. Documentados execução no SSMS,
parâmetros e conferência de turmas compartilhadas no guia local da matriz. Códigos
na fonte e inclusão dessas atividades nas Horas Reais ainda exigem conferência.
Somente documentação alterada; SQL/app inalterados, sem conexão ou avanço de fase.
Testes não repetidos nesta complementação; conferência estática dos blocos 06/10.

## Matriz e consultas comuns — 10/11/2026

Matheus definiu departamento pela alocação do docente e solicitou consultas iguais
para IND, Economia, Direito, Letras, Engenharia Elétrica e Informática. Preparados
matriz e SQL de leitura locais a partir do modelo fornecido em base, usando a
alocação atual e o recorte inicial de quadros/situações da extração IND anterior.
Cobertura desse recorte nos outros departamentos e seus códigos ainda precisam
ser conferidos. Histórico passa a representar a coorte atual neste pacote; o app
não foi alterado. Matrículas acadêmicas não têm fonte/relação suficiente no modelo
fornecido; vigências administrativas requerem evidência e classificação próprias.
[Entrega local, parâmetros e validação](operations/departamentos.local/MATRIZ.md).
Nenhuma conexão, execução SQL Server, integração, avanço de fase ou publicação.

**Feedback do PDF — 09/11/2026:** revisão de vocabulário, data em Brasília,
funis de carga, notas resumidas e cenário local de apresentação com 14 docentes.
Fixtures de teste preservadas; sem alteração de banco remoto, avanço de fase ou
publicação. [Entrega, comandos e pendências](guides/FEEDBACK_PDF.md).

# Plano de desenvolvimento

## Migração sintética e autenticação Supabase — 05/11/2026

Solicitação expressa de Matheus (D-035): dados e schema sintéticos migrados e
conciliados no Supabase, leitor integrado ao monólito Streamlit, login obrigatório
e autorização por departamento aplicados. Matheus confirmou login e cálculo.
Conferências e limites em [STATUS](STATUS.md) e [guia operacional](operations/SUPABASE.md).
A parcela de autenticação Supabase do Prompt 6 foi implementada no escopo sintético;
isso não conclui integração/autorização institucional, homologação ou publicação.
O processo Python continua no ambiente de hospedagem existente, sem reescrita de
frontend e sem deploy nesta tarefa. A base é um snapshot: não há replicação automática.

## Tabelas visuais e gráficos primeiro — 05/11/2026

Ajuste de apresentação sobre R01–R06, sem mudança de fase (D-033): indicador de carga com
símbolos, tabelas recolhidas sob os gráficos, quatro gráficos novos e rótulo não clicável de
Análise financeira, que não entra no escopo. Evidências no [STATUS](STATUS.md). Aceite de uso
e revisão visual seguem pendentes. Sem avanço de fase ou deploy.

## Aproximação ao design system da PUC-Rio — 04/11/2026

Incremento de apresentação sobre R01–R06, sem mudança de fase: tokens do site e do
portal (D-032), tela Início, filtros relevantes por análise, gráficos e exportações sob
demanda. Limites e evidências no [STATUS](STATUS.md);
[roteiro para Talita](guides/INTERFACE_E_GRAFICOS.md). Aceite de uso e revisão por
Matheus/responsável institucional seguem pendentes. Sem avanço de fase ou deploy.

## Revisão solicitada da interface e gráficos — 04/11/2026

Incremento de apresentação e usabilidade sobre R01–R06 existentes: referências
visuais do portal/site público, tema com tokens locais preservados, navegação em
etapas, refinamento/limpeza de filtros e gráficos interativos com unidades e
adaptação de largura. Nenhuma fórmula ou etapa de integração alterada. Testes e
limites no [STATUS](STATUS.md); [roteiro para Talita](guides/INTERFACE_E_GRAFICOS.md).
Aceite de uso e revisão por Matheus/responsável institucional seguem pendentes;
browser QA não comprovada por timeout das ferramentas. Sem avanço de fase/deploy.

## Prompt de feedback · revisão final sintética — 04/11/2026

Revisados os registros dos Prompts 3, 4a, 4b e 5 e os seis roteiros existentes.
Corrigidos estados de fonte indisponível na R05 e unidade do gráfico PNG R02;
orientações de uso e feedback foram atualizadas. A classificação, critérios e
limites estão na [revisão final](guides/REVISAO_FINAL_FEEDBACK.md); resultados de
verificação em [STATUS](STATUS.md). A preparação sintética não comprova acesso ou
resultados institucionais. Feedback operacional, conciliação 4b em PostgreSQL,
revisão de Talita e identidade visual continuam pendentes conforme impacto descrito.

## Prompt 5 · exportações e feedback — 04/11/2026

Conferência e ajustes locais dos formatos existentes, incluindo R01 no manifesto;
registro de feedback na sessão
com download manual CSV. Persistência, retenção e destino do backlog aguardam a
decisão do time (Q-008), confirmada como ainda não definida por Matheus. Avaliação
humana e conferência na origem PostgreSQL sintética permanecem pendentes; não é
necessário conectar à origem institucional para este incremento.
[Detalhes](guides/PROMPT5_VERIFICACOES.md).

## Prompt 4b · carga horária — 03/11/2026

Parcela offline conferida; execução PostgreSQL sintético e confirmação humana
pendentes. [Conciliação, limites e execução](guides/PROMPT4B_CARGA.md). A 4a
permanece concluída por aceite de Matheus. Sem início do Prompt 5 ou publicação.

## Prompt 4a · conferência de matrículas — 03/11/2026

**Concluída no escopo sintético por aceite de Matheus**, que confirmou nesta
conversa: “tudo validado por mim e conciliado”. Próximo incremento: **4b, carga
horária**, a executar em solicitação própria. Esta atualização registra o aceite;
não inicia a 4b nem publica a aplicação.

Execução técnica anterior pelo agente:

Executado somente o incremento de matrículas na parcela offline. R06 existente
reutilizada; corrigidos detalhe de formados por código e situação da variação
com atual ausente. [Registro, conciliação e comandos](guides/PROMPT4A_MATRICULAS.md).
38 cenários/2.612 comparações na fixture contra SQL independente em SQLite, sem
divergência. Testes offline não comprovam leitura efetiva de PostgreSQL.

Preparada conferência manual com SQL fixo parametrizado, total e curso, mesmas
fontes/filtros/transação REPEATABLE READ e identificação do snapshot. Conciliação
posteriormente confirmada por Matheus; o agente não executou essa rotina nem
inspecionou relatório adicional. Sem recarga, recriação ou alteração de
TLS. Talita revisa uso; DSI/DBA ficam para a etapa institucional final (D-028).
4b e outros prompts não iniciados neste incremento; sem publicação automática.

## Complemento docente solicitado pelas capturas — 03/11/2026

Implementado o ajuste da interface docente no escopo sintético autorizado: aba
Análise docente com composição R01, dois gráficos mensais R03 e listas geral/CH;
departamento e quadro em barras verticais amarelas dos tokens, categoria horizontal
e rótulos de valores. Os filtros Centro > Departamento nas duas entradas restringem
Todos os departamentos ao centro e invalidam resultados/arquivos após mudança.
Centros da memória são fictícios; o mapeamento PostgreSQL continua pendente e usa
Centro não informado. Não houve conexão a banco neste complemento.

Regras/unidades preservadas, incluindo pessoas distintas por mês, zero somente em
competência observada sem elegíveis, ausência sem valor e semestres janeiro–julho/
agosto–dezembro. Consultar [STATUS](STATUS.md) para o resultado das verificações
finais. A revisão no navegador foi bloqueada pela ferramenta por não conseguir
verificar a URL no Windows. Matheus/Talita revisam uso e filtros; Matheus/responsável institucional revisam a identidade, ainda sem
homologação. [Arquivos, comandos e limites](guides/PROMPT3_DOCENTES.md). Nenhuma
outra fase iniciada nem publicação realizada; o conteúdo seguinte é histórico.

## Prompt 3 docente — incremento de 03/11/2026

Implementadas as lacunas concretas R01–R03 no adaptador sintético existente:
composição por departamento, comparação geral/QP, histórico com total independente
e estado Parcial por cobertura; apresentação Altair reutiliza tabelas R01–R05 e
mantém PNG/CSV/ZIP. R06 e fórmulas de carga/funções preservados. Sem leitura de
PostgreSQL/SQL Server nesta tarefa. [Matriz e evidências](guides/PROMPT3_DOCENTES.md).
Revisão visual/interações dos gráficos no navegador ainda não comprovadas por
bloqueio da automação Windows. Próximo trabalho depende de solicitação; não foram
iniciados os Prompts 4–7 nem integração/autenticação/publicação.

## Sequência vigente — base sintética até a etapa final — 03/11/2026

Por orientação explícita de Matheus (D-028), usar o PostgreSQL sintético existente
em todo o desenvolvimento e preparação. Conexão, diagnóstico, inventário,
mapeamento físico e conferência institucionais ficam somente para a etapa final
do projeto e deploy. O roteiro do Prompt 1 está preparado, mas sua execução real
foi adiada; não constitui dependência para desenvolver os Prompts 2–5.

| Momento | Trabalho restante | Origem/evidência |
|---|---|---|
| Desenvolvimento | Prompt 2 concluído no escopo sintético por código/fixture e testes offline; conferência PostgreSQL não executada por certificado ausente. Prompts 3–4: conferir fluxos docentes, matrículas e carga; Prompt 5 e feedback: finalizar verificações, exportações e uso | [Mapa R01–R06](operations/SYNTHETIC_SOURCE_MAP.md), catálogo e leitores existentes; próximos prompts somente quando solicitados |
| Preparação da entrega | Prompt 7: versão, dependências e guia | Versão identificada como sintética; ambiente de deploy já existente |
| Etapa final e deploy | Prompt 1 real pelo operador; depois completar mapa físico/leitura institucional, conferir resultados e realizar deploy no procedimento existente | Execução humana autorizada, retorno sanitizado e verificações institucionais efetivamente registradas |
| Após deploy | Conferir fluxo entregue e registrar pendências | Origem/versão realmente utilizadas, sem presumir equivalência com a fixture |

No Todoist, as 11 tarefas foram mantidas: diagnóstico/inventário real transferido
de 03/11 para 12/11 na seção final, após a preparação da versão e antes do deploy.
As demais datas de trabalho permanecem. Prompt 2 deixa de depender do Prompt 1
institucional; nenhuma tarefa foi concluída por essa mudança de sequência.
Meta pessoal e reserva permanecem, sem garantia de que a integração final não
revele lacunas. Autenticação e assuntos relacionados continuam com o time.
Esta diretriz prevalece sobre dependências institucionais antecipadas nos registros
anteriores. Não inicia implementação de outro prompt nem autoriza conexão/deploy.

## Execução operacional por prompts — 02/11/2026

Por orientação de Matheus, o controle das próximas ações está em
[11 tarefas no Todoist](https://app.todoist.com/app/project/6hvgC82GJR7Fgc9R),
com link para o trecho correspondente do
[guia de prompts](references/Guia_Desenvolvimento_VRAC_Codex.md), ponto de partida,
trabalho restante e resultado esperado. Este plano substitui a organização inicial
de 25 tarefas com reuniões e encaminhamentos institucionais detalhados.

- Prompt 2: completar o mapa lógico e o catálogo na base sintética; execução real
  do Prompt 1 adiada para a etapa final conforme D-028.
- Prompt 3 e incrementos 4a/4b: concluir os fluxos e conferências sintéticos de
  docentes, matrículas e carga, preservando os cálculos já implementados.
- Prompt 5: completar modos das verificações, conferir exportações e concluir
  feedback; prompt de feedback: ajustes concretos e revisão técnica final.
- Prompt 7: preparar versão/guia; na etapa final executar o Prompt 1 real,
  completar a integração/conferência institucional, realizar o deploy em uma
  tarefa geral e conferir o fluxo entregue no ambiente já disponível.

Prompt 0 já concluído. **Prompt 6, autenticação e assuntos relacionados são do
time de desenvolvimento**, sem tarefas de implementação correspondentes para
Matheus. Usar a integração entregue pelo time quando disponível; não criar novas
etapas de provisionamento ou reuniões obrigatórias por incremento. Questões
externas serão encaminhadas por Matheus ao longo do trabalho, registrando somente
o efeito concreto sobre a execução. Isso não declara controles de acesso testados
nem permite uso real sem esses controles.

Datas de trabalho: 03–13/11/2026; meta pessoal de entrega em 13/11, com 14–15/11
como reserva e sem deadline institucional. O planejamento não executa prompts,
não avança fases nem autoriza publicação automaticamente. Diretrizes atuais de
Matheus e D-022/D-027 prevalecem sobre trechos históricos dos prompts.

## Entrega atual — todos os roteiros sintéticos, 30/10/2026

D-027 registra a autorização de Matheus para implementar todos os roteiros já
documentados e completar os dados fictícios necessários. R01–R06 agora têm fluxo
de demonstração, gráficos e exportações; histórico, matrículas e carga usam as
regras documentadas. QP, comparação dimensional e comprovações administrativas
adicionais são simulações declaradas, sem inferência de regra institucional.
Conferências programadas e pacote de exportação antecipam a parte local da fase 5.
O [guia das análises](guides/ANALISES_SINTETICAS.md) orienta o uso. Critérios de
acesso institucional e publicação das fases 6/7 não foram cumpridos ou simulados.

## Diretriz vigente — 30/10/2026

Conforme orientação de Matheus (D-022), os dashboards existentes e a documentação
já disponível definem os cálculos. As exigências de nova aprovação de fórmulas,
populações e referências presentes no histórico deste plano ficam substituídas
pela reprodução das regras documentadas. Não exigir rodada adicional de validação
analítica ou novo caso de referência para aceitar essas regras. Testes offline
devem conferir a fidelidade do código a elas; informação ausente ou contraditória
deve ser registrada somente para o resultado afetado, sem inventar uma solução.

Continuam aplicáveis as dependências técnicas de fontes físicas e acesso seguro,
os requisitos de interface e a execução apenas da fase solicitada. Esta atualização
documental não inicia outra fase nem declara integração ou homologação concluídas.
Os critérios abaixo refletem o histórico até esta decisão.

Complemento autorizado em 30/10/2026 (D-023): preparar PostgreSQL sintético a partir
da documentação semântica local, com carga determinística e conta de leitura. É uma
base de desenvolvimento para os próximos incrementos, sem migração do SQL Server,
conexão institucional ou início automático das fases analíticas. Execução e limites
no [guia da base sintética](operations/SYNTHETIC_POSTGRES.md).

Conexão solicitada na sequência (D-025): a demonstração consulta filtros e suas duas
tabelas no PostgreSQL sintético local, com conta de leitura, TLS e parâmetros
vinculados. Esta entrega liga a base à tela existente; não implementa os cálculos
das fases 3/4 nem amplia o escopo para outras análises. O modo real segue bloqueado.

Atualizado em 28/10/2026. O [guia original](references/Guia_Desenvolvimento_VRAC_Codex.md) define as fases; este documento organiza entregas, responsáveis e critérios de passagem. A solicitação atual detalha documentalmente os roteiros da fase 2 a partir dos dois painéis indicados. Contratos lógicos e testes sintéticos anteriores permanecem preparados enquanto os metadados aprovados da fase 1 não estiverem disponíveis. A integração institucional continua pendente e as fases 3–7 não foram iniciadas.

Não há prazo fechado: acesso, fontes, regras e infraestrutura ainda dependem de validação. O esforço técnico deve ser registrado separadamente da espera por decisões institucionais. Nenhuma passagem de fase ou publicação é automática.

## Fase 0 — fundação e demonstração

**Estado:** fundação técnica concluída e verificada em Windows x64. Instalação local, lock e estilo aprovados; 20 testes offline passaram na fase 0. Evidências e verificações atuais em [STATUS.md](STATUS.md). **Responsável técnico:** Matheus, com apoio do Codex no código e nos testes offline. As ferramentas da fase 1 estão preparadas e os contratos da fase 2 foram iniciados por solicitação; fases 3–7 não iniciadas.

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

**D-028 — 03/11/2026:** ferramentas preparadas; execução institucional adiada para
a etapa final e deploy. Não exigir a configuração/saída real para os incrementos
sintéticos. O parágrafo seguinte registra detalhes técnicos para esse momento futuro.

As ferramentas manuais de configuração, conexão, diagnóstico e inventário estão implementadas. Consultas fixas usam parâmetros vinculados, limites por schema e timeouts. Em 28/10/2026, Matheus confirmou SQL Server, servidor KAPPA e banco PUC_OLAP, informou usuário criado e declarou autorizados os schemas necessários à aplicação. Porta TCP e lista nominal dos schemas ainda não estão disponíveis; autenticação, driver e permissões efetivas também precisam ser registrados. Saídas privadas ficam fora do workspace e mensagens de erro são sanitizadas.

O [roteiro de descoberta](operations/DATABASE_DISCOVERY.md) contém comandos, revisão de privilégios e interpretação das limitações. O [dicionário sanitizado](operations/SANITIZED_DATA_DICTIONARY.md) define o material autorizado para o mapeamento institucional na etapa final, sem dependência para o Prompt 2 sintético. Consultas de qualidade/cardinalidade institucionais são apenas templates e não podem ser executadas pela CLI.

**Conexão e inventário institucionais: NÃO VALIDADOS.** A preparação de código não satisfaz o critério humano de passagem da fase 1. O operador deve executar os comandos em ambiente autorizado, o DBA confirmar escopos e privilégios de leitura e Matheus liberar somente material sanitizado. Nenhum resultado real foi inventado.

## Fase 2 — catálogo e contratos lógicos

**Prompt 2 atual — 03/11/2026:** mapa lógico/sintético concluído para R01–R06,
com campos, tipos, chaves, deduplicação, relações, unidades, temporalidade e evidências
em [SYNTHETIC_SOURCE_MAP.md](operations/SYNTHETIC_SOURCE_MAP.md). Catálogo
`phase2-synthetic-map-v5` distingue implementação conferida offline de fonte
institucional pendente. Leitura PostgreSQL não conferida nesta revisão: certificado
local ausente; sem fallback ou mudança de TLS. Prompt 3 poderá reutilizar R01,
leitores/consultas, fixtures e testes, sem depender de inventário real ou reaprovação
das fórmulas documentadas. Não iniciado nesta tarefa. A API `phase3_blockers` separa
modo sintético de modo real, cujo bloqueio permanece. Os parágrafos seguintes são
**histórico da preparação de 28/10**, substituídos por D-022/D-027/D-028 quando houver
conflito com o escopo atual; não são condições adicionais para o Prompt 3 sintético.

Complemento implementado em 28/10: contratos dos seis roteiros, validação de filtros
e pontos temporais, dependências por métrica e resultados com estados independentes.
Catálogo `phase2-workflows-v4`, mantendo três famílias e nove variantes. A CLI lista
os roteiros e `phase3_blockers()` mostra as condições ainda pendentes. A autorização
condicional de Matheus para o Prompt 3 foi considerada, mas faltam regras docentes,
fonte, recorte e referência aprovados. Nenhum cálculo da fase 3 foi iniciado.
Os detalhes a seguir registram a preparação documental anterior.

Em 28/10/2026, a documentação local `docs/ROTEIROS_ANALISES_VRAC.local.md` detalha
seis roteiros: situação geral, geral e QP, histórico semestral, carga, dupla função
e funções administrativas, e o gráfico geral de alunos. Há filtros em tabela,
regras encontradas versus propostas, 24 decisões pendentes e 38 casos de aceite
futuros. O inventário local identifica cinco páginas e seus visuais. Esses arquivos
internos estão excluídos do Git/Docker; não ampliam o catálogo executável nem aprovam
regras, dados ou acesso. O encaixe do detalhamento de funções no plano ainda precisa
ser decidido, sem início de implementação ou avanço automático de fase.

[config/analyses.yaml](../config/analyses.yaml) e [ANALYSIS_CATALOG.md](ANALYSIS_CATALOG.md)
registram definições propostas, priorizando composição docente. Contratos de solicitação,
resultado, origem, comparação e equivalência de cursos estão implementados com casos
sintéticos; não calculam as análises nem conectam ao banco. Todos os status institucionais
permanecem pendentes e os adaptadores reais continuam bloqueados.

A revisão solicitada por Matheus incorporou a documentação detalhada dos modelos
semânticos: nove variantes acadêmicas, ainda sem escolha institucional. Mapeamento
local de tabelas/colunas permanece excluído do Git e separado do catálogo empacotável.
Para docentes, aprovar pessoas versus matrículas funcionais e a referência temporal;
para matrículas, escolher entre cadastro, período, última situação e trajetória;
para horas, confirmar fonte física, unicidade e unidade da medida dedicada. A inspeção
semântica não substitui o inventário físico ou a autorização de acesso da fase 1.

Para avançar, Talita e os responsáveis pelos dados precisam registrar fonte, população,
granularidade, fórmula, referência de comparação e aceite funcional humano da primeira
análise. A lista curta de decisões está no catálogo. Sem essa evidência, não declarar
integração validada nem iniciar implementação real ou a fase 3 automaticamente.

## Backlog das próximas fases

| Fase e estado | Próximo incremento executável | Evidência necessária para avançar | Validação |
|---|---|---|---|
| 1 — ferramentas preparadas; institucional somente na etapa final | Executar roteiro real pelo operador naquele momento; não é tarefa imediata | Conexão, escopo, privilégios e retorno sanitizado efetivamente registrados | Matheus + DBA; DSI/time para acesso/TLS |
| 2 — mapa lógico/sintético concluído; institucional pendente | Reutilizar mapa, contratos e leitores no próximo prompt solicitado; futura conferência PG depende de restaurar certificado sintético | Testes offline e observação da receita registrados; nenhuma origem real confirmada, sem nova aprovação geral de fórmulas | Matheus no desenvolvimento; DBA/DSI somente na integração final |
| 3 — implementada em demonstração sintética (D-027) | R01, comparação QP configurável e presença semestral disponíveis; avançar a integração somente com fontes físicas autorizadas | Testes offline e conferências na fixture; composição institucional de QP permanece lacuna específica | Matheus + Talita para uso; DBA/DSI para origem real |
| 4a — implementada em demonstração sintética (D-027) | Quatro séries acadêmicas, filtros por curso, ausências, variações e exportações; nenhuma equivalência automática | Comparação com SQL independente na fixture; ingresso futuro, bolsas repetidas e base zero cobertos | Matheus + Talita para uso; fonte institucional antes do modo real |
| 4b — implementada em demonstração sintética (D-027) | Horas Reais, contratada, indicador literal e alocações separados; comparação apenas em unidades sintéticas declaradas | Conferência com fonte dedicada; zeros/nulos e semáforo testados; sem rateio ou substituição por disciplinas | Matheus + Talita para uso; unidade institucional permanece específica |
| 5 — implementação local parcial (D-027) | Dez conferências sobre snapshot e E01 experimental; CSV/PNG/ZIP e feedback temporário em sessão disponíveis; armazenamento e backlog ainda indefinidos | Testes offline e fluxo simulado; [limites e conferência PostgreSQL pendente](guides/PROMPT5_VERIFICACOES.md); não há autorização institucional | Matheus e time para solução operacional; Talita para uso; DSI/DBA na etapa institucional |
| 6 — não iniciada | Integrar login aprovado, aplicar autorização antes de consultar/recuperar/exportar e testar isolamento de sessão | Homologação de autenticação, escopos, conta técnica, HTTPS, cache e retenção; aceite de segurança e funcional registrado | DSI + DBA + Talita + Matheus |
| 7 — não iniciada | Preparar serviço interno, configuração de operação, suporte, atualização, retorno de versão e guia de uso | Responsável autoriza publicação; operador confirma implantação; Talita conclui casos acordados; suporte e recuperação definidos | DSI/operador + Talita + Matheus |

Na fase 1, os scripts são preparados pelo agente e executados manualmente pelo desenvolvedor autorizado fora da sessão. Conexão e inventário permanecem **NÃO VALIDADOS** até haver evidência humana registrada. Não testar escrita para verificar permissão.

A fase 4 tem dois incrementos: revisar matrículas antes de iniciar carga horária. A fase 7 começa pela preparação; publicar exige autorização explícita do responsável. Sem infraestrutura aprovada, manter demonstrações acompanhadas com dados sintéticos.

## Revisões e critérios comuns

Em 28/10/2026, materiais de marca e fontes fornecidos foram integrados à demonstração
existente, por solicitação de Matheus. Tokens, tema gerado e fontes locais estão
implementados; não houve avanço analítico de fase. Prancha RGB conferida, sem manual
completo de interface. Persistem divergências de amarelo/cinza, regras não documentadas,
conferência no navegador e revisão institucional. Nenhuma homologação foi presumida.

Todo elemento visual deve seguir o branding da PUC-Rio. Antes de implementar ou revisar
telas, gráficos e exportações, obter os materiais oficiais em
[assets/branding/](../assets/branding/README.md) e registrar a origem/versão e o responsável
pela validação. A demonstração mantém tema provisório até essa aplicação ser conferida.
Incluir conformidade visual nos critérios das demonstrações e da homologação do piloto.

Após cada entrega das fases 3, 4a, 4b e 5: demonstrar, registrar feedback sanitizado, separar erro técnico de regra pendente e pedido fora do escopo, priorizar o menor ajuste autorizado e testar novamente. Feedback de usabilidade não equivale à aprovação de fórmula.

Cada análise deve ser testável sem Streamlit. A suíte padrão permanece offline; testes reais serão separados e explícitos. A comparação de resultados exige os mesmos filtros, regras e referência temporal. Histórico exato depende de fonte versionada ou snapshot autorizado; logs e hashes isolados não garantem reprodução.

## Pendências que orientam o próximo trabalho

| Pendência | Responsável por encaminhar/validar | Momento necessário |
|---|---|---|
| Confirmar repositório privado autorizado e política de compartilhamento com o agente | Matheus + responsável institucional | Antes de compartilhar material interno |
| SGBD, autenticação, rede, TLS, fontes e privilégios de leitura | Matheus + DBA/DSI | Fase 1 |
| Mapeamento e conferência de composição docente real; reproduzir regras documentadas | Matheus + responsável pelas fontes/DBA | Etapa final, sem reaprovação geral de fórmulas ou dependência para o sintético |
| Equivalências vigentes, unidade de carga e lacunas concretas da fonte real | Matheus + responsável pelas fontes/DBA | Somente resultado afetado na integração final; simulações explícitas disponíveis |
| Servidor, identidade institucional, autorização e conta técnica | DSI + DBA | Solicitar desde a fase 0; concluir antes do acesso real autônomo |
| Limiar das verificações, retenção e uso de SQLite operacional | Talita + DSI + Matheus | Fase 5, conforme decisão |
| Canal de suporte, operador e autorização de publicação | DSI + responsável pelo piloto | Fases 6 e 7 |

As [solicitações para a DSI](operations/DSI_REQUESTS.md) são um roteiro preparado para Matheus. Sua existência não registra envio, aprovação ou provisionamento.


## 2026-11-10 — Conciliação da navegação com a origem institucional

A pedido de Matheus, integrada à navegação por áreas da main a origem docente
institucional pseudonimizada, com seletor explícito, autenticação e autorização
própria. A demonstração sintética continua separada. Trocar a origem limpa os
resultados e arquivos da sessão; falhas não acionam dados fictícios.
Exportações identificam a natureza dos dados. Análises sem fontes permanecem
bloqueadas, inclusive R06 na origem docente. Não há avanço de fase ou homologação.

Publicação web autorizada explicitamente nesta tarefa. CSVs, materiais de origem
e registros operacionais individuais permanecem locais. Mudanças locais anteriores
foram preservadas e há uma cópia recuperável no stash. Ver
[guia de origens e publicação](guides/ORIGENS_E_PUBLICACAO.md) para uso e comandos.
Validação analítica segue pendente com Matheus/Talita; acesso e operação com DSI/DBA.

Validação desta conciliação: 593 testes offline passaram, 1 teste de integração
excluído; Ruff e formatação aprovados. A primeira execução foi interrompida por
permissões na pasta temporária padrão do Windows; a execução completa em pasta
própria passou. Porta local 8530 reiniciada e conferida com seletor institucional
e login. Testes de banco não foram repetidos nesta conciliação de front.
