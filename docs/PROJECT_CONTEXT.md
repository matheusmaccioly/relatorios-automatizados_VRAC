# Contexto do projeto VRAC

**4b, carga horária:** conferência offline e correções mínimas realizadas;
execução PostgreSQL sintético e confirmação de Matheus pendentes. A 4a permanece
concluída por seu aceite anterior. [Detalhes](guides/PROMPT4B_CARGA.md).

Atualizado em 03/11/2026. Fonte: [Guia de desenvolvimento](references/Guia_Desenvolvimento_VRAC_Codex.md). As instruções permanentes estão em [AGENTS.md](../AGENTS.md).

## Prompt 4a · conferência R06 — 03/11/2026

**4a concluída no escopo sintético.** Após a entrega, Matheus informou nesta
conversa: “tudo validado por mim e conciliado”. Aceite/conciliação registrados
como confirmação humana; sem nova execução PostgreSQL pelo agente ou inspeção de
relatório adicional. **4b, carga horária, é o próximo incremento**, ainda não iniciado.
Isso não declara integração institucional, homologação visual ou aceite de Talita.

Registro da execução anterior pelo agente:

Conferida somente a parcela offline de matrículas: quatro populações, filtros,
ausências, variações e correspondência de tabelas/gráficos/arquivos existentes.
Corrigidos detalhe FR/TD por código de curso e descrição de variação com atual
ausente. A busca do ingresso conserva o cadastro lido antes dos filtros acadêmicos;
não foram criadas equivalências nem transformado o cadastro em histórico.
[Conciliação e limites](guides/PROMPT4A_MATRICULAS.md): 38 cenários e 2.612 registros
offline sem divergência; referência SQL em SQLite não comprova PostgreSQL.

Rotina de leitura/conciliação sintética preparada para execução explícita por
Matheus, com leitor existente e referência SQL independente na mesma transação.
**PostgreSQL não executado pelo agente**; conciliação posteriormente confirmada
por Matheus, conforme registro acima.
Centro na origem PG não informado, bolsas por departamento sem vigência e formação
restrita ao cadastro continuam limitações explícitas. Talita revisa uso; fontes
institucionais somente na etapa final. Sem avanço a 4b, homologação ou publicação.

## Complemento da interface docente pelas capturas — 03/11/2026

Por solicitação de Matheus, a aba **Análise docente** reúne R01, os gráficos
mensais de total ativo e de ativos por quadro/semestre/mês da R03, a lista geral
e o detalhe de CH Real. Departamento/quadro são barras verticais em amarelo dos
tokens, categoria é horizontal e os valores aparecem nos gráficos. Unidades,
fonte dedicada das Horas Reais e calendário janeiro–julho/agosto–dezembro foram
preservados; mês observado sem elegíveis é zero, mês ausente permanece sem valor.

Centro precede e restringe Departamento nas duas entradas de análise. Todos os
departamentos respeita o centro; mudanças de filtros invalidam resultados e
arquivos anteriores. Centros em memória são fictícios. O PostgreSQL sintético
não fornece esse mapeamento e aparece como **Centro não informado**, sem relação
institucional presumida. Não houve conexão a banco nesta tarefa. As verificações
finais são registradas em [STATUS](STATUS.md). A revisão no navegador foi bloqueada
pela ferramenta por impossibilidade de verificar a URL no Windows. Sem homologação
visual, avanço de fase ou publicação.
Detalhes, arquivos e comandos no [complemento do guia docente](guides/PROMPT3_DOCENTES.md).
Os blocos seguintes preservam o histórico anterior.

## Origem de dados e sequência vigentes — 03/11/2026

Prompt 3 implementado no escopo docente sintético: composição por departamento,
comparação geral/QP por unidade, evolução com total distinto e pilhas separadas,
gráficos web Altair, tabelas/exportações equivalentes e limpeza de resultados.
R04/R05 reutilizados para apresentação; R06 sem alteração analítica. Sem conexão
PostgreSQL ou institucional nesta tarefa. [Entrega, limites e roteiro para Talita](guides/PROMPT3_DOCENTES.md).
Revisão interativa no navegador permanece pendente por bloqueio da ferramenta.

Prompt 2 concluído no escopo lógico/sintético: o
[mapa R01–R06](operations/SYNTHETIC_SOURCE_MAP.md) vincula conceitos aos leitores,
consultas e contratos existentes, separando DDL, observação da receita offline e
convenção analítica. O catálogo diferencia implementação conferida offline de
fontes institucionais pendentes. Conferência PostgreSQL desta revisão não executada
por certificado local ausente; sem fallback ou alteração de TLS. O Prompt 3
reutilizou mapa, R01, SQL/leitores, fixtures e testes no incremento descrito acima.

Matheus esclareceu que está usando o **PostgreSQL sintético existente** e que a
**conexão real ocorrerá somente na etapa final do projeto e deploy** (D-028).
Desenvolvimento, mapeamento lógico, análises, verificações, exportações, feedback
e preparação da versão continuam nessa base. Não solicitar configuração real ou
execução do diagnóstico/inventário institucional como próximo passo agora.

O Prompt 1 institucional foi adiado para a etapa final; sua preparação offline
permanece disponível, sem declarar execução ou conclusão. O Prompt 2 poderá
trabalhar com o mapa lógico/sintético e os Prompts 3–5 com essa mesma origem, sem
depender de inventário real. Isso altera a sequência, não executa esses prompts.
Fontes físicas institucionais, adaptação do leitor e conferência dos resultados
reais ficam para a etapa final, antes do uso real no deploy existente.

Testes sintéticos não validam conexão, chaves, cobertura ou resultados da origem
institucional. Quando chegar essa etapa, o operador autorizado executará os
comandos reais fora da sessão do agente, preservando TLS, validação de certificado,
escopo e somente leitura; somente retorno sanitizado autorizado será compartilhado.
Autenticação e assuntos relacionados permanecem com o time de desenvolvimento.
Os encaminhamentos anteriores de conexão imediata devem ser lidos conforme esta
diretriz; lacunas reais não bloqueiam os incrementos sintéticos.

## Orientação operacional — 02/11/2026

Matheus quer controlar a execução pelos prompts já existentes no guia, aproveitando
o que foi implementado, com poucas reuniões e sem transformar encaminhamentos
institucionais em etapas obrigatórias de cada incremento. Pendências externas serão
tratadas por ele ao longo do trabalho e devem ter impacto concreto registrado.

Matheus informou que **o ambiente de deploy já existe** e que **autenticação e
assuntos relacionados ficam com o time de desenvolvimento**. O Prompt 6 é
responsabilidade desse time, não uma lista de implementação para Matheus. Isso
registra a divisão de trabalho informada, sem declarar infraestrutura ou acesso
tecnicamente validados. O deploy continua em uma tarefa geral do Prompt 7, adequada
ao procedimento existente. Os controles necessários ao uso real continuam aplicáveis
quando a integração do time for disponibilizada; não impedem o avanço sintético
nem a preparação dos artefatos.

O [planejamento no Todoist](https://app.todoist.com/app/project/6hvgC82GJR7Fgc9R)
foi reduzido a 11 tarefas operacionais, vinculadas aos Prompts 1–5, feedback e 7.
Prompt 0 já concluído e seis roteiros sintéticos são o ponto de partida. A meta
pessoal permanece 13/11/2026, com 14–15/11 como reserva, sem deadline institucional.
As referências históricas a infraestrutura não definida devem ser lidas conforme
esta atualização; não solicitar novo provisionamento como pendência presumida.

## Diretriz vigente para os cálculos — 30/10/2026

Matheus determinou que os cálculos devem reproduzir os dashboards existentes e as
regras já documentadas, sem nova validação ou aprovação dessas regras. Essa decisão
(D-022) substitui as exigências anteriores de revalidação das fórmulas registradas
abaixo. Não criar regras alternativas nem exigir novo caso de referência como
condição para aceitar as definições documentadas. Se faltar informação para reproduzir
um cálculo, registrar a lacuna concreta e limitar seu efeito ao resultado afetado.

Testes técnicos de fidelidade da implementação permanecem aplicáveis. A decisão
não comprova conexão ou mapeamento físico e não altera os requisitos de segurança,
a revisão visual ou a fase autorizada. Os registros datados anteriores descrevem
o histórico e devem ser lidos conforme esta diretriz.

## Objetivo e usuária

Talita, da VRAC/PUC-Rio, precisa consultar informações acadêmicas para avaliações departamentais e preparar insumos verificáveis. A aplicação deverá receber departamento, período e análises, executar consultas revisadas e apresentar tabelas, gráficos, filtros, fontes, limitações e exportações. A revisão e a decisão institucional permanecem humanas.

O aplicativo será interno, sem LLM, chatbot, agentes em execução, geração dinâmica de código ou dependência operacional de Power BI. Talita deverá utilizá-lo pelo navegador, sem instalar Python ou receber credenciais do banco. O Codex participa apenas do desenvolvimento.

## Escopo autorizado nesta entrega

Em 30/10/2026, Matheus autorizou implementar todas as análises documentadas e gerar
os dados fictícios necessários para avançar a aplicação (D-027). Esse pedido amplia
o limite anterior da D-026: os roteiros R01–R06 estão implementados na demonstração,
incluindo histórico docente, matrículas, carga, funções, gráficos, conferências e
exportações. QP configurável, unidades comparáveis e atos administrativos adicionais
são simulações explícitas; não foram convertidos em regras institucionais aprovadas.
O [guia de uso](guides/ANALISES_SINTETICAS.md) descreve o resultado atual. Os registros
seguintes preservam as entregas anteriores; fases 3/4 e parte da 5 foram implementadas
somente na base sintética. Integração, autenticação e publicação institucionais continuam
pendentes; não houve consulta ao SQL Server real.

Matheus solicitou em 30/10/2026 conectar a aplicação ao PostgreSQL sintético (D-025).
A demonstração existente agora carrega filtros, registros docentes e alocações por
turma com consultas fixas parametrizadas e conta de leitura. Os lançadores selecionam
essa origem explicitamente; falhas removem resultados anteriores, sem fallback para
memória. O modo institucional continua bloqueado e não foram acrescentados cálculos
ou análises de outras fases. Detalhes no guia da base sintética abaixo.

Em 30/10/2026, Matheus solicitou gerar dados e banco sintéticos em PostgreSQL a partir
do modelo semântico já documentado (D-023). Esta entrega prepara essa base local para
os próximos passos; não troca o destino SQL Server institucional nem implementa novas
análises. Gerador e executor ficam em `vrac.dev`; receita com nomes internos e carga
ficam locais e ignoradas. O [guia de PostgreSQL sintético](operations/SYNTHETIC_POSTGRES.md)
descreve execução, cenários e limites. Os parágrafos seguintes preservam o histórico.

A solicitação atual detalha os roteiros das análises docentes e do gráfico geral de
alunos indicados por Matheus, dentro da preparação documental da fase 2. O documento
local `docs/ROTEIROS_ANALISES_VRAC.local.md` organiza seis roteiros, filtros, regras,
resultados, decisões e casos de aceite; o inventário local de evidências identifica
as páginas e os visuais dos dois PBIX. Ambos ficam excluídos do Git e do contexto
Docker. Nenhuma regra foi aprovada, análise implementada ou fase avançada nesta revisão.

Na implementação complementar solicitada em 28/10, os seis roteiros passaram a ter
contratos tipados de solicitação, planejamento e resultado por métrica/período.
As famílias YAML referenciam os roteiros e a CLI expõe suas dependências. As 24
decisões continuam pendentes. Não foram implementados cálculos nem novas telas.
Matheus autorizou seguir ao Prompt 3 se não houver interferência; como as regras
docentes e o aceite humano ainda não estão registrados, a fase 3 permanece pendente.

O catálogo registra nove variantes para as três análises e um
mapeamento local excluído do Git organiza nomes e tipos de 12 tabelas. São objetos de
modelos Power BI, sem comprovação de origem SQL. O dicionário físico da fase 1 continua
não preenchido; fontes e regras permanecem propostas, sem seleção institucional e com
adaptadores reais bloqueados. A fase 0 e as ferramentas manuais da fase 1 estão preparadas;
a organização documental e o branding foram preservados. Não houve conexão real,
inventário institucional ou aceite funcional humano. Fases 3–7 não iniciadas.

Todo o sistema deve seguir a identidade visual institucional. Os materiais oficiais ficam
em [assets/branding/](../assets/branding/README.md). Em 28/10, Matheus forneceu
assinaturas RGB, prancha EMoD de 23-10-18 e fontes Literata/Rethink Sans. A demonstração
usa esses arquivos com tokens centralizados e fontes locais. Amarelo/cinza têm
divergências RGB/hex no material e não foram aplicados aos componentes. Regras de
interface não documentadas, revisão no navegador e homologação visual permanecem
pendentes; aplicação dos materiais não significa conformidade institucional aprovada.

As próximas entregas, mediante solicitação de cada fase, priorizam composição docente, depois matrículas e carga horária. Verificações adicionais serão determinísticas e terão catálogo fechado, limites e aprovação quando exigida.

O [catálogo da fase 2](ANALYSIS_CATALOG.md) explicita as definições propostas e as
decisões para Talita e os responsáveis pelos dados. Testes ou comparação de fixtures
não aprovam uma regra institucional nem autorizam avançar automaticamente à fase 3.

## Exclusões

Não desenvolver análise financeira, curva guia, relatório institucional final automático, recomendações de contratação, CAPES, produção acadêmica, projetos patrocinados, relação aluno/docente ou classificação de contratação/desligamento. Não ampliar para exploração livre de dados ou plataforma genérica.

## Estado das evidências

| Item | Situação | Consequência |
|---|---|---|
| Guia e instruções do projeto | Disponíveis neste repositório | Orientam esta fase |
| SGBD e destino | Matheus confirmou SQL Server, servidor KAPPA e banco PUC_OLAP em 28/10/2026 | Destino informado; porta, autenticação, driver e certificado ainda exigem confirmação |
| Conta e autorização | Matheus informou usuário criado e autorização dos schemas necessários à aplicação | Lista nominal de schemas/objetos e revisão administrativa de somente leitura pendentes; nenhuma credencial registrada |
| Conectividade e permissões efetivas | Não validadas nesta sessão | Nenhuma consulta real será executada pelo agente |
| Tabelas, colunas e medidas semânticas | Documentação local fornecida e mapeada; modelos A/B acadêmicos, C fora do escopo | Evidência de implementação; origem física, chaves, autorização e regras ainda exigem confirmação |
| Fórmulas documentadas e referências | Reprodução vigente por D-022, sem nova aprovação geral; testes sintéticos não são conciliação institucional | Lacuna concreta afeta somente seu resultado; referência real será conferida na etapa final |
| Servidor do aplicativo, login institucional e escopos da usuária | Ambiente de deploy já existente informado por Matheus; autenticação e assuntos relacionados com o time; integração não verificada | Desenvolvimento sintético segue; acesso autônomo real permanece bloqueado até integração autorizada |
| Repositório remoto | API confirmou repositório privado em 27/10, com envio de código autorizado por Matheus | Compartilhamento de fontes/metadados internos continua sujeito a liberação específica; Git privado não substitui essa aprovação |

O guia menciona uma reunião de 21/10 e materiais de referência. Esses materiais não foram incorporados como fontes verificadas nesta entrega. As observações transcritas no guia são questões a validar, não um dicionário definitivo do banco.

## Regras que não podem ser presumidas

- Docentes distintos não equivalem à quantidade de vínculos ou à soma de contagens mensais.
- Registros de matrícula não equivalem necessariamente a alunos únicos.
- Departamento do vínculo e departamento da disciplina são entidades distintas; a cobertura interdepartamental depende da fonte e da permissão.
- Horas Reais devem vir da fonte oficial aprovada. Somar disciplinas não substitui esse indicador; compartilhamentos não serão rateados sem regra confiável.
- Turmas com zero alunos exigem referência de matrícula e exceções validadas. Não excluir suas horas do valor oficial por iniciativa do código.
- Classificação ausente não autoriza inferência de TCC, monografia ou disciplina regular.
- Cursos renomeados ou reestruturados só serão combinados mediante equivalência institucional aprovada e vigente.
- Datas de cargo não provam contratação nem desligamento. Valores incomuns são pontos para conferência, sem julgamento de produtividade.

Zero, nulo, ausência de registros e erro devem permanecer distintos. Variação percentual com base zero não será calculada. Resultados futuros precisam identificar filtros efetivos, unidade, execução, extração, atualização da origem quando conhecida, versões, avisos e situação válida, parcial ou bloqueada.

## Limites de segurança

Credenciais, dumps e dados pessoais ficam fora do workspace do agente e do Git. O desenvolvedor autorizado executará consultas reais fora desta sessão e fornecerá somente material sanitizado cuja divulgação esteja autorizada. Arquivos de exclusão do Git e de imagens são proteções adicionais; não isolam arquivos contra leitura.

A aplicação real dependerá de autenticação e autorização institucionais, conta técnica de leitura com escopo confirmado pelo DBA, TLS e validação de certificado. Demonstração sintética não libera modo real. Falhas de configuração ou de dados não podem ativar dados fictícios silenciosamente.

Consulte o [plano](PLAN.md), a [arquitetura](ARCHITECTURE.md), as [decisões](DECISIONS.md) e as [solicitações para a DSI](operations/DSI_REQUESTS.md).
