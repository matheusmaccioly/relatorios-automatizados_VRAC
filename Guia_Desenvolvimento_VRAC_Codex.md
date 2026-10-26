# Desenvolvimento da PoC de Análises Acadêmicas da VRAC

Plano de execução, instruções para o Codex e proposta de disponibilização para Talita.

**Status:** proposta técnica para implementação e validação. O acesso ao banco foi recebido pelo desenvolvedor, mas a conectividade, as permissões, o esquema, as regras e a infraestrutura de publicação ainda não foram verificados neste material. Os nomes de módulos e documentos abaixo são propostas, não objetos já existentes na PUC-Rio.

**Decisão principal:** construir uma aplicação interna de análises acadêmicas com SQL e Python, sem LLM em execução. O Codex será uma ferramenta de apoio ao desenvolvimento, não uma dependência do aplicativo utilizado por Talita.

## Contexto do projeto

### Necessidade e usuária

Talita, da VRAC/PUC-Rio, consulta informações de docentes, carga horária e matrículas para apoiar avaliações departamentais, solicitações de contratação e transições de gestão. Hoje, parte do trabalho envolve consultar diferentes visões, ajustar filtros, conferir exceções e reunir gráficos e tabelas para os materiais institucionais.

O primeiro produto deverá preparar essas análises automaticamente e entregar resultados verificáveis para revisão humana. Talita não deverá precisar de Python, SQL, credenciais do banco ou Codex para utilizá-lo.

### Escopo confirmado para a PoC

- Consulta direta ao banco, sem dependência operacional do Power BI.
- Formulário com departamento, período e análises disponíveis.
- Consultas SQL previamente revisadas e processamento em Python.
- Composição do corpo docente, evolução das matrículas e análise de carga horária, conforme disponibilidade e validação das fontes.
- Verificações adicionais previamente programadas, nos modos automático e sob aprovação.
- Tabelas, gráficos, observações por regras fixas, fontes, filtros e limitações.
- Exportação dos insumos, sem montagem do relatório institucional final.
- Participação de Talita em ciclos curtos de demonstração, feedback, ajuste e nova validação.

### Exclusões

Não incluir LLM, chatbot, agentes em execução, geração dinâmica de SQL/Python, análise financeira, curva guia, relatórios finais automáticos ou decisões sobre contratação. Produção acadêmica, regras CAPES, projetos patrocinados, relação aluno/docente e classificação de contratações/desligamentos não são prioridades desta PoC e não devem entrar sem nova definição de escopo.

### Cuidados revelados na reunião de 21/10

A transcrição de origem é conversacional e contém ruídos. Tratar as observações abaixo como requisitos de verificação, não como documentação definitiva do banco.

1. Horas Reais não devem ser substituídas pela soma simples das horas registradas por disciplina. Compartilhamentos e currículos podem fazer os valores divergir.
2. Há uma pendência sobre o alcance interdepartamental do indicador agregado. O departamento do vínculo do docente e o departamento da disciplina precisam ser separados.
3. A reunião discutiu horas alocadas em turmas sem alunos. É necessário confirmar o momento de referência, o encerramento da matrícula e eventuais exceções. Não alterar o cálculo oficial silenciosamente.
4. A classificação de TCC/monografia pode estar incompleta. “Sem especificação” não significa automaticamente disciplina regular.
5. Mudanças de nome, abertura ou reestruturação de cursos afetam as séries de matrículas. A equivalência entre cursos exige informação institucional validada.
6. Contagem mensal de docentes não deve ser simplesmente somada para produzir uma contagem semestral. Afastamentos e movimentações afetam a interpretação.
7. Data de início de cargo não prova nova contratação; data de fim de cargo não prova desligamento da instituição.
8. Um valor incomum deve aparecer como situação para conferência, não como julgamento de produtividade ou necessidade automática de contratação.

### Hipóteses técnicas a validar

Considerar SQL Server como hipótese de trabalho pelo contexto de acesso do desenvolvedor. Confirmar o SGBD, servidor, porta, banco, autenticação e fontes autorizadas antes de concluir a integração. Não assumir que recebimento de credenciais prova conectividade ou autorização para publicar todos os dados.

Preferir um monólito modular: Streamlit para interface, Python para regras, pandas para tratamento, SQLAlchemy + pyodbc se SQL Server for confirmado e Matplotlib para gráficos exportáveis. Usar biblioteca de exportação XLSX apenas quando essa capacidade for implementada. Selecionar versões estáveis e compatíveis com o ambiente institucional e registrar dependências de forma reproduzível.

SQLite poderá ser usado, se aprovado, somente para metadados operacionais e feedback da aplicação. Esse armazenamento é separado dos bancos institucionais, que permanecerão somente leitura. Não replicar tabelas acadêmicas por conveniência.

## Plano de desenvolvimento

### Ordem proposta e critérios de passagem

| Fase | Objetivo | Entrega | Condição para avançar |
|---|---|---|---|
| 0 | Preparar o projeto e as proteções | Repositório, contexto, testes básicos e demonstração sintética | Projeto reproduzível, sem segredos e sem ligação automática ao banco |
| 1 | Confirmar acesso e conhecer as fontes | Scripts de diagnóstico e inventário autorizado | Desenvolvedor confirma conexão e DBA confirma escopo de leitura |
| 2 | Formalizar os cálculos | Catálogo de análises e mapeamento de dados | Primeira análise tem definição, fonte e exemplo de referência aprovados |
| 3 | Entregar uma análise de ponta a ponta | Composição docente, tabela, gráfico e interface inicial | Resultado conciliado e experiência avaliada por Talita |
| 4 | Ampliar com segurança | Matrículas e carga horária, separadamente | Cada módulo passa em seus testes e na validação funcional |
| 5 | Incluir verificações e exportações | Dois modos, arquivos para uso e feedback | Nenhum aprofundamento é executado sem a autorização exigida |
| 6 | Preparar acesso institucional | Autenticação, autorização, testes e homologação | DSI aprova exposição de dados reais e acesso de Talita |
| 7 | Publicar o piloto e acompanhar | Serviço interno, documentação e rotina de suporte | Talita executa casos reais; revisão decide ampliar, ajustar ou encerrar |

As fases não são uma fila sem retorno. Após 3, 4 e 5, demonstrar uma entrega pequena, registrar feedback e ajustar antes de ampliar. Solicitar o servidor, o mecanismo de login e a conta técnica desde a fase 0, em paralelo ao desenvolvimento.

Não assumir um prazo fechado de quatro semanas antes de validar conectividade, fontes, regras de carga horária e autenticação. Separar esforço de desenvolvimento de espera por acesso, decisões e validações institucionais.

### Primeira entrega vertical

Começar pela composição docente de um departamento e período aprovados: consulta, cálculo, tabela, gráfico, metadados e exportação inicial. Não construir três módulos completos antes de mostrar algo a Talita. Inicialmente, demonstrar a interface com dados sintéticos; as consultas reais são executadas pelo desenvolvedor no ambiente autorizado. A abertura de acesso autônomo com dados reais depende da fase de segurança.

### Requisitos comuns de qualidade

Cada resultado deve ter identificador da execução, análise, parâmetros, data/hora da extração, atualização da origem quando disponível, versão da consulta/regra, avisos e situação: válido, parcial ou bloqueado. Data da consulta não é necessariamente data de atualização dos dados.

Nulos, ausência de linha, zero e falha de consulta precisam ter significados distintos. Uma seção bloqueada não deve aparecer como valor zero nem impedir automaticamente a entrega das outras seções válidas.

Comparar resultados apenas com exemplos de mesmo recorte, regras e referência temporal. Não forçar o resultado atual do banco a coincidir com um relatório antigo caso a origem tenha sido corrigida depois.

Logs e hashes permitem rastrear uma execução, mas não garantem reproduzi-la se a fonte mudar. Reprodutibilidade histórica exata depende de versão ou snapshot autorizado. Não guardar cópias de dados pessoais automaticamente.

## Uso seguro do Codex

Criar um repositório privado autorizado. Manter o ambiente de código sem credenciais reais, dumps ou arquivos pessoais. O desenvolvedor executa as consultas reais fora da sessão do agente e fornece somente metadados ou resultados sanitizados cuja divulgação tenha sido autorizada.

Executar Codex localmente não deve ser interpretado como garantia de que o contexto lido pelo modelo permanece integralmente na rede da universidade. Configurar permissões do agente, sandbox e controles de rede. Um arquivo .gitignore protege o versionamento, não impede por si só a leitura de arquivos pelo agente.

Copiar o AGENTS.md e o contexto do projeto para a raiz/pasta docs do repositório. Conciliar com instruções existentes; não sobrescrever políticas institucionais. Enviar um prompt de fase por tarefa. Revisar mudanças, testes e pendências antes de avançar. Não permitir acesso irrestrito ou alterações no banco.

## Prompt-base — instruções permanentes do projeto

Salvar as instruções abaixo em AGENTS.md, conciliando com eventuais regras já existentes.

```text
Você apoia o desenvolvimento de uma PoC interna de análises acadêmicas da VRAC/PUC-Rio. A usuária final é Talita. Leia docs/PROJECT_CONTEXT.md e docs/PLAN.md. Trabalhe somente na fase solicitada.

OBJETIVO
Entregar análises de docentes, matrículas e carga horária por formulário, tabelas, gráficos e exportações. A aplicação deve operar sem LLM, chatbot, agentes, geração dinâmica de código ou dependência de Power BI. O Codex é utilizado apenas no desenvolvimento.

FORA DO ESCOPO
Não implementar análises financeiras, relatório institucional completo, decisões sobre contratação, integração CAPES, produção acadêmica ou exploração livre de dados. Não transformar a PoC em uma plataforma genérica.

ARQUITETURA
Adotar monólito modular em Python. Preferir Streamlit, pandas e Matplotlib. Usar SQLAlchemy/pyodbc se SQL Server for confirmado. Consultas SQL devem estar em arquivos revisados e parâmetros devem ser vinculados, não concatenados. Não introduzir FastAPI, frontend separado, filas, Redis, Kubernetes ou serviços pagos sem necessidade demonstrada e decisão explícita.

SEGURANÇA
Não ler nem imprimir senhas, arquivos .env reais, secrets.toml real, dumps, diretórios privados ou variáveis de ambiente com segredos. Não pesquisar segredos na máquina. Não conectar automaticamente ao banco real; produzir scripts para execução pelo desenvolvedor autorizado fora da sessão do agente. Não enviar dados ou metadados internos para serviços externos sem autorização.
A conta de execução deve ter somente leitura sobre fontes aprovadas. Não executar CREATE, ALTER, DROP, INSERT, UPDATE, DELETE, MERGE, SELECT INTO ou procedimentos que alterem o banco institucional. Não testar comandos destrutivos no banco real. Melhorias de banco devem ser documentadas para o DBA, não aplicadas pelo agente.
Não criar consultas arbitrárias a partir da interface. Validar parâmetros e usar uma lista fechada de consultas. Não considerar uma verificação textual de SELECT ou ApplicationIntent=ReadOnly como controle de acesso suficiente.
Usar conexão criptografada e validação de certificado. Não resolver erro de conexão desligando TLS, aceitando qualquer certificado, abrindo firewall ou elevando permissões.
Credenciais e dados privados devem permanecer fora do workspace do agente e do Git. .gitignore e .dockerignore são proteções adicionais, não isolamento de segurança.
A interface não poderá compartilhar dados reais sem autenticação e autorização. Qualquer login simulado só poderá funcionar em desenvolvimento local com dados sintéticos. A conta de banco do desenvolvedor não será a conta definitiva do serviço.

CORREÇÃO ANALÍTICA
Não inventar tabelas, colunas, chaves, números, equivalências ou regras. Separar nomes lógicos de fontes físicas. Marcar pendências e bloquear somente o resultado afetado.
Não somar horas por disciplina para substituir Horas Reais. Não agregar meses por soma para contar professores no semestre. Não confundir registros de matrícula com alunos únicos. Não tratar mudanças de cargo como contratação. Não presumir equivalências entre cursos nem classificar TCC pelo nome automaticamente.
Não tratar zero, nulo e dado ausente como equivalentes. Não calcular variação percentual quando a base é zero. Não classificar baixa produtividade ou recomendar contratação a partir de métricas isoladas.
Textos devem ser templates descritivos preenchidos com dados validados. Verificações adicionais seguem regras programadas e limites explícitos, não IA.

DESENVOLVIMENTO
Inspecionar a estrutura antes de alterar arquivos, sem acessar diretórios privados. Preservar mudanças existentes. Implementar incrementos pequenos, tipagem nas interfaces, tratamento de erros e testes.
Manter dados sintéticos determinísticos, visivelmente identificados e separados dos dados reais. Em modo real, falhas nunca devem ativar dados fictícios silenciosamente.
Executar testes offline por padrão. Testes contra o banco devem ser explícitos e separados, executados pelo desenvolvedor. Não alegar que testes passaram se não foram executados.
A interface e a documentação para Talita devem estar em português, com termos simples e filtros apresentados em tabela. Preferir Análises disponíveis e Resultados calculados a nomenclaturas institucionais ainda não aprovadas.
Manter decisões e questões abertas registradas. Não declarar uma hipótese como validada sem confirmação humana registrada.

AO FINAL DE CADA TAREFA
Informar o que mudou; arquivos alterados; comandos de execução; testes executados e resultados; testes não executados; riscos; bloqueios; o que Matheus/DSI/DBA/Talita precisam validar. Atualizar o estado do projeto. Não avançar de fase nem publicar automaticamente.
```

## Prompt 0 — fundação e ambiente de desenvolvimento

```text
Leia AGENTS.md e docs/PROJECT_CONTEXT.md. Execute somente a fase 0.

Objetivo: preparar um projeto simples, testável e seguro, ainda sem acessar o banco institucional.

1. Inspecione o repositório e a versão de Python disponível. Preserve arquivos existentes. Se o diretório estiver vazio, crie o projeto; se houver código, proponha a menor adaptação necessária.
2. Estruture app.py, src/vrac/, sql/, config/, tests/, scripts/ e docs/. Separe configuração, acesso a dados, análises, verificações, gráficos, exportações e interface. Não gere dezenas de abstrações vazias.
3. Configure instalação reproduzível com dependências estáveis compatíveis, pytest e verificação de estilo. Documente comandos para desenvolvimento no Windows e o que dependerá da plataforma do servidor.
4. Crie exemplos de configuração sem valores reais. Credenciais reais serão inseridas pelo operador fora do workspace e não devem ser solicitadas no chat. Adicione .gitignore e .dockerignore para segredos, caches, exportações e dados privados.
5. Crie configuração explícita de ambiente e modo de dados. Desenvolvimento sintético deve ser o padrão. Modo real exige configuração explícita; nunca usar fallback silencioso para dados fictícios.
6. Crie dados sintéticos mínimos com semente fixa, sem copiar nomes ou registros da instituição. Devem permitir testes com docentes repetidos, diferentes vínculos, períodos sem dados e casos de carga compartilhada.
7. Prepare uma tela mínima identificada como DEMONSTRAÇÃO, sem autenticação fictícia habilitada para dados reais. Crie uma interface de autorização que negue acesso a dados reais enquanto o mecanismo institucional não estiver configurado.
8. Registre arquitetura inicial, decisões, pendências e critérios de aceite em docs. Inicie uma lista de solicitações para a DSI: servidor, autenticação, conta técnica de leitura e fontes permitidas.

ACEITE
O projeto instala em ambiente limpo, os testes sintéticos rodam sem banco ou internet e nenhum segredo está no código. Documente o que não pôde testar. Entregue comandos de execução e o resumo padrão do AGENTS.md. Não implemente ainda os cálculos reais.
```

## Prompt 1 — conexão segura e descoberta do banco

```text
Leia AGENTS.md, docs/PROJECT_CONTEXT.md e o estado da fase 0. Execute somente a fase 1.

Objetivo: preparar diagnóstico e inventário para que o desenvolvedor identifique fontes reais autorizadas. Não conectar ao banco nesta sessão do Codex.

1. Confirme, a partir de informações aprovadas disponíveis, o SGBD esperado. Caso SQL Server seja apenas hipótese, registre isso e deixe a conexão configurável sem fabricar fatos.
2. Implemente um módulo de conexão. Para SQL Server, use SQLAlchemy/pyodbc, criptografia e validação de certificado, credenciais externas, timeout de conexão, timeout de consulta e descarte adequado de conexões. Não presumir a porta nem o método de autenticação. Não usar conta privilegiada ou reutilizar credenciais pessoais em publicação.
3. Crie um diagnóstico, executado manualmente pelo desenvolvedor, que separe configuração ausente, nome/rede/VPN/porta, driver, certificado, autenticação e permissões. Não executar varredura de rede. A prova de conexão deve usar SELECT 1 sem imprimir connection string, identidade ou registros.
4. Crie inventário restrito aos bancos e schemas autorizados: views/tabelas, colunas, tipos e relações declaradas. Metadados não visíveis devem ser classificados como desconhecidos, não como inexistentes. Não extrair linhas pessoais nem consultar o banco inteiro.
5. Produza saídas locais privadas por padrão. Gere um modelo de dicionário sanitizado, que o desenvolvedor poderá preencher e liberar ao Codex. Diferencie nomes lógicos de nomes físicos reais.
6. Prepare consultas diagnósticas delimitadas de qualidade e cardinalidade, mas deixe a execução desabilitada até aprovação dos objetos, filtros e orçamento de consulta. Não usar SELECT *, contagens globais repetidas ou amostras individuais sem necessidade.
7. Documente a revisão de privilégios com o DBA. Somente SELECT e limites em código não provam que a conta não pode escrever. Não testar escrita para comprovar ausência de permissão. Não criar views ou índices.
8. Teste conexão, timeout e sanitização de erros com mocks. Testes de integração reais devem estar marcados e não rodar na suíte padrão.

ACEITE
Entregar scripts executáveis, instruções de uso e lista exata do material sanitizado necessário para a próxima fase. Se não houve execução real, declarar conexão e inventário como NÃO VALIDADOS. Não inventar nomes de tabelas.
```

## Prompt 2 — catálogo de análises e regras de negócio

```text
Leia AGENTS.md e os metadados sanitizados aprovados da fase 1. Execute somente a fase 2. Na ausência deles, implemente contratos lógicos e testes sintéticos, mas mantenha os adaptadores reais bloqueados.

Objetivo: tornar explícito o significado de cada cálculo antes de implementá-lo.

1. Crie config/analyses.yaml e docs/ANALYSIS_CATALOG.md. Para cada análise, registrar: identificador, pergunta respondida, população, granularidade, unidade, fonte lógica/física, chaves, parâmetros, filtros, fórmula, exceções, período, responsável, versão e status de validação.
2. Priorize composição docente. Depois, evolução das matrículas e carga horária. Não adicionar relação aluno/docente, financeiro, CAPES ou movimentação funcional ao escopo.
3. Diferencie departamento do vínculo do docente, departamento da disciplina, curso e programa. Não usar nomes como chave nem equiparar entidades sem evidência.
4. Documente: docente distinto versus registro; foto em uma data versus presença em qualquer mês do semestre; aluno único versus matrícula; horas semanais versus semestrais; fonte oficial de Horas Reais versus detalhamento planejado por disciplina.
5. Trate atuação em outro departamento, compartilhamentos, turmas sem alunos, TCC sem classificação e mudanças de curso como regras pendentes quando a fonte não permitir confirmá-las. Nunca corrigir a métrica oficial silenciosamente.
6. Para séries de matrículas, preveja tabela de equivalências de cursos com vigência, fonte e aprovação humana. Sem equivalência aprovada, manter séries separadas e sinalizar a limitação.
7. Crie contratos tipados de solicitação e resultado. O resultado deve conter dados, unidades, período, filtros efetivos, origem, datas de extração/atualização, versões, avisos e situação válida/parcial/bloqueada. Não incluir credenciais.
8. Crie casos sintéticos para nulos, zeros, duplicidade, semestre parcial, denominador zero e fontes com datas distintas. Defina estrutura para exemplos de referência que serão conferidos por Talita; não fabricar validação.
9. Defina tolerâncias explicitamente: contagens inteiras devem coincidir no mesmo recorte; arredondamento de horas requer critério acordado. Não ajustar tolerância apenas para fazer teste passar.

ACEITE
Uma análise pode avançar para implementação real somente quando fonte, granularidade, cálculo e critério de comparação estiverem registrados. A aprovação funcional deve ser humana. Entregue uma lista curta de decisões pendentes para Talita e para o responsável pelos dados.
```

## Prompt 3 — primeira análise de ponta a ponta

```text
Leia AGENTS.md e o catálogo da fase 2. Execute somente a fase 3.

Objetivo: construir a primeira entrega utilizável: composição do corpo docente de um departamento e período, com consulta, cálculo, tabela, gráfico e interface inicial.

1. Use exclusivamente as fontes e regras aprovadas. Implemente a consulta parametrizada em arquivo SQL. Aceite apenas filtros válidos e autorizados. Se o mapeamento físico não estiver confirmado, entregue o adaptador sintético e bloqueie claramente o real.
2. Separe repositório de dados, função de cálculo e apresentação. O cálculo deve ser testável sem Streamlit. Evite duplicidade de docentes por vínculos, disciplinas ou períodos conforme o contrato, sem eliminar registros arbitrariamente.
3. Implemente seleção de departamento e período, botão Gerar análise e estados: pronto, executando, sem dados, parcial, bloqueado e erro. Alterar um filtro não deve disparar uma consulta automaticamente nem conservar um resultado como se fosse do filtro novo.
4. Apresente total, distribuição por vínculo, tabela e gráfico de barras. Inclua tabela de filtros usados, período, extração, atualização da fonte quando conhecida e limitações.
5. Não exibir números fictícios em modo real. Demonstração deve estar marcada em todas as telas e arquivos. Não usar conta simulada para liberar dados reais; consultas reais de validação devem ser executadas pelo desenvolvedor no ambiente autorizado.
6. Disponibilize download inicial do gráfico e da tabela, aplicando proteção contra conteúdo interpretado como fórmula. Mantenha dados e arquivos restritos à sessão.
7. Crie testes de cálculo, parametrização, duplicidade, vazio e mudança de filtros. Prepare rotina de conciliação com o exemplo de referência de Talita, utilizando os mesmos filtros e a mesma referência temporal.
8. Prepare um roteiro curto para demonstrar a experiência a Talita: encontrar o departamento, gerar, interpretar a tabela de filtros, baixar o gráfico e relatar dificuldade. Registrar feedback não equivale a aprovar automaticamente regras de negócio.

ACEITE
Fluxo sintético completo funciona; ligação real só é declarada validada após teste humano registrado. Não desenvolver os outros módulos antes de revisar esta primeira entrega. Documente diferenças e feedback em vez de mascará-los.
```

## Prompt 4 — matrículas e carga horária

```text
Leia AGENTS.md, o catálogo e o feedback da fase 3. Execute a fase 4 em dois incrementos independentes: matrículas primeiro; carga horária depois. Pare ao final de cada incremento para revisão.

MATRÍCULAS
1. Implementar série por curso e período de acordo com a definição validada de aluno/matrícula. Deduplicar apenas pelas chaves e critérios documentados.
2. Calcular variação absoluta e percentual sem tratar ausência como zero. Quando a base for zero, informar que a variação percentual não é calculável; quando o período estiver incompleto, sinalizar.
3. Usar somente equivalências de cursos aprovadas e vigentes. Mostrar alterações de composição das séries; não somar cursos como se fossem equivalentes apenas por semelhança do nome.
4. Gerar gráfico, tabela histórica e observações objetivas por template, sem causalidade ou previsão inventada.

CARGA HORÁRIA
5. Ler a fonte validada de Horas Reais sem substituí-la por soma do detalhamento. Mostrar Horas Reais e alocação por disciplina em visões distintas, com a unidade de cada medida.
6. Selecionar docentes pelo vínculo institucional quando essa for a definição aprovada e recuperar atuação interdepartamental somente dentro das permissões autorizadas. Explicar eventual cobertura incompleta.
7. Tratar compartilhamentos apenas com regra ou identificador confiável. Quando não houver informação suficiente, não deduzir nem ratear horas.
8. Turmas com zero alunos devem produzir informação para conferência, considerando data de matrícula e exceções. Não excluir do valor oficial por iniciativa do código.
9. Tipificação ausente deve aparecer como ausência de classificação. Não inferir TCC automaticamente a partir do nome.
10. Gerar tabela por docente/disciplina e comparações previstas, sem ranking de produtividade ou recomendação de contratação.

QUALIDADE E ACEITE
Criar testes específicos para cursos renomeados, períodos ausentes, matrículas duplicadas, atuação em dois departamentos, componentes compartilhados e turmas vazias. Registrar conciliação separada para cada módulo. Se a carga horária estiver bloqueada, a aplicação deve continuar entregando as análises válidas de docentes e matrículas, com a seção indisponível explicada.
```

## Prompt 5 — verificações adicionais, exportações e feedback

```text
Leia AGENTS.md, os resultados aprovados e o feedback das fases anteriores. Execute somente a fase 5.

Objetivo: implementar aprofundamentos determinísticos, exportações utilizáveis e registro de feedback. Não criar IA, SQL dinâmico ou investigação aberta.

1. Crie um catálogo fechado e versionado de verificações. Cada uma deve indicar dados necessários, condição de disparo, consulta autorizada, texto explicativo, evidência, limitações e custo máximo de execução.
2. Comece com poucas verificações acordadas: turmas com horas e zero alunos; classificação de disciplina ausente; variação de matrículas acima de um limiar aprovado. O primeiro caso depende da data adequada; o terceiro não terá limiar institucional inventado.
3. Diferencie verificar um resultado já disponível de executar uma consulta adicional. Se o modo for sob aprovação, a consulta de aprofundamento só poderá acontecer depois da autorização de Talita.
4. Modele estados sugerida, aprovada, recusada, executada, falhou e não aplicável. Vincule a autorização ao usuário autorizado, análise, parâmetros, versão da regra e referência dos dados. Alterações invalidam a autorização anterior.
5. No modo automático, execute somente verificações habilitadas e dentro de limites. No modo sob aprovação, rejeitar não deve impedir a entrega das análises básicas. Evite repetição a cada rerun da interface.
6. Exiba pontos para conferência, não diagnósticos conclusivos. Toda observação deve mostrar o motivo, a evidência e a limitação.
7. Implemente exportações CSV/XLSX e PNG/SVG conforme dependências aprovadas. Incluir filtros, datas, unidades, versões e avisos. Não montar PDF/PPTX institucional final. Proteger células textuais não confiáveis contra fórmulas sem transformar números negativos legítimos em texto indevidamente.
8. Crie armazenamento operacional separado dos bancos de origem, usando SQLite apenas se aprovado. Registrar metadados de execução, status e feedback; não salvar dados acadêmicos brutos por padrão. Proteger armazenamento e backups.
9. Feedback deve permitir útil, divergência, dificuldade e sugestão, associado à execução. Alertar para não inserir dados pessoais em texto livre. Talita não poderá editar regras técnicas pela tela.
10. Testar que rejeição nunca executa a consulta, nova seleção invalida aprovação, rerun não duplica execução e arquivos refletem exatamente os filtros do resultado mostrado.

ACEITE
Os dois modos funcionam sem LLM; exportações são conferidas e o feedback alimenta um backlog de melhorias. Regras não aprovadas permanecem desabilitadas ou explicitamente experimentais em ambiente de teste.
```

## Prompt 6 — autenticação, autorização e homologação

```text
Leia AGENTS.md e os documentos de infraestrutura aprovados pela DSI. Execute somente a fase 6.

Objetivo: preparar acesso autônomo de Talita com dados reais, sem depender de proteção apenas na interface.

1. Levante o mecanismo institucional efetivamente disponível. Preferir OIDC integrado ao Streamlit quando aprovado, ou um proxy institucional autenticado. Não presumir Microsoft Entra, criar login próprio ou inventar parâmetros do provedor.
2. Separar autenticação e autorização. Somente identidades/grupos explicitamente autorizados poderão consultar análises e baixar arquivos. Não liberar acesso só porque o e-mail pertence à universidade. Não hardcodar nome ou e-mail de Talita sem configuração aprovada.
3. Em OIDC, conferir as configurações do provedor e a política de sessão da DSI. Em proxy, aceitar identidade apenas de origem confiável, remover cabeçalhos forjados e impedir acesso direto à porta da aplicação.
4. Aplicar autorização antes da consulta, antes da exportação e na recuperação de resultados. Definir escopo por departamento, análise e nível de detalhe; usar fonte com escopo restrito quando possível. O acesso amplo do desenvolvedor não representa o acesso da usuária final.
5. Remover qualquer bypass de demonstração em ambiente real. Falha ou ausência de autenticação/autorização deve negar acesso, sem fallback.
6. Definir conta técnica de leitura e armazenamento de segredos no servidor. Não registrar senhas, connection strings, nomes pessoais ou dados brutos em logs. Logs devem permitir rastreabilidade com mínima informação necessária.
7. Evitar cache global de dados restritos. Preferir estado/cache por sessão ou chave que inclua escopo de autorização e política validada. Limpar resultados e arquivos em logout, expiração e mudança de escopo. Não confiar só em ocultar botões.
8. Revisar HTTPS, certificados, limites de consultas, proteção de arquivos e retenção. Não executar teste de escrita no banco real. Adotar uma verificação de dependências compatível com a política institucional.
9. Executar testes offline de acesso negado, troca de usuário, mudança de departamento, exportação sem permissão, sessão expirada, cache, falha de banco e mensagens sanitizadas. Testes com autenticação/banco reais serão feitos pelo operador em homologação autorizada.
10. Preparar checklist para Talita conferir os mesmos casos de referência: números, gráficos, filtros, limitações e esforço de uso. Registrar divergências, correções e aceites sem inventar aprovação.

ACEITE
Não declarar pronto para acesso real sem validação de segurança da DSI e aceite funcional registrado. Entregar a lista de bloqueios externos e o que já foi efetivamente testado. Permissão de leitura da conta deve ser confirmada pelo responsável pelo banco.
```

## Prompt 7 — publicação interna e operação do piloto

```text
Leia AGENTS.md, a proposta de disponibilização e o checklist da fase 6. Execute somente a preparação da fase 7. Não publicar sem autorização explícita do responsável.

Objetivo: permitir que Talita acesse o piloto pelo navegador em endereço institucional, sem instalar ferramentas e sem depender do computador do desenvolvedor.

1. Confirmar o ambiente aprovado: servidor/VM/container institucional, sistema operacional, autenticação do banco e mecanismo de login. Não presumir que autenticação Windows funcionará sem configuração em container Linux. Registrar a opção escolhida.
2. Preparar um serviço simples de aplicação. Usar container somente se o ambiente o suportar e a autenticação estiver testada; caso contrário, documentar execução supervisionada conforme o padrão institucional. Não adicionar orquestração complexa.
3. Preparar publicação em HTTPS, atrás da proteção institucional, com suporte às conexões necessárias da interface. Restringir a porta da aplicação e não expor o banco. Não sugerir túnel público ou hospedagem pública por conveniência.
4. Disponibilizar segredos no servidor por mecanismo aprovado; nunca embuti-los em imagem, Git, arquivo público ou navegador. Confirmar conta de serviço independente do login pessoal do desenvolvedor.
5. Configurar reinício, verificação de saúde sem dados sensíveis, limites, rotação de logs e desativação de telemetria não necessária. Não incluir analytics externo. Documentar tráfego de saída necessário, como banco e provedor de identidade.
6. Definir persistência e backup apenas dos dados operacionais aprovados. Exportações devem ser temporárias ou geradas em memória, sem pasta pública. Documentar retenção, remoção e restauração.
7. Criar manual operacional: instalar, configurar, atualizar, testar, voltar à versão anterior, trocar credenciais/certificados, diagnosticar falha e acionar suporte. Separar instruções para operador e usuária.
8. Criar guia de Talita em português: acessar, escolher parâmetros, gerar, conferir, autorizar aprofundamento, baixar e informar problemas. Identificar o ambiente como piloto.
9. Preparar roteiro de teste no computador de Talita: acesso autorizado, acesso negado de outra identidade, gráficos, download, logout, mudança de filtros e indisponibilidade do banco. Incluir VPN/rede institucional quando exigida pela DSI.
10. Iniciar um ciclo controlado de feedback: demonstrar, usar, registrar problemas, priorizar, corrigir, testar regressões e reapresentar. Mudanças de regra de negócio exigem nova validação funcional.

ACEITE
O operador confirma implantação e acesso; Talita conclui os casos combinados; existem responsáveis, backup operacional e retorno à versão anterior. Registrar exatamente o que não foi executado. Se infraestrutura ou login não estiverem disponíveis, entregar os artefatos e manter publicação bloqueada.
```

## Prompt de feedback — repetir após cada demonstração

```text
Leia AGENTS.md, a versão atual, os critérios aprovados e o feedback sanitizado fornecido nesta tarefa. Não inferir novos requisitos a partir de comentários vagos.

1. Classifique cada item como erro de cálculo, regra de negócio pendente, qualidade da fonte, usabilidade, desempenho ou solicitação fora do escopo.
2. Diferencie o que pode ser corrigido em código do que depende de decisão de Talita/DSI/DBA. Não alterar métrica oficial para aproximar o número de uma expectativa não validada.
3. Proponha o menor incremento útil. Registre motivo, impacto, critério de aceite e responsável pela validação.
4. Implemente somente os itens desta rodada que tenham autorização e critério claros. Para regra ainda indefinida, crie pendência e teste desabilitado com justificativa, não uma regra inventada.
5. Execute regressões e prepare demonstração do antes/depois com dados sintéticos ou material aprovado. Verifique se o ajuste altera resultados, filtros, exportações ou permissões.
6. Atualize documentação e versão da regra quando necessário. Encerrar com mudanças, testes, bloqueios e perguntas objetivas restantes. Não ampliar o escopo nem publicar automaticamente.
```

## Disponibilizacao para Talita

### Recomendação

Publicar uma aplicação web interna em infraestrutura administrada pela DSI. Talita entra pelo navegador, autentica-se pelo mecanismo institucional, seleciona departamento/período/análises e recebe os resultados. Ela não recebe credenciais do banco e não instala Python ou Codex.

Fluxo proposto: navegador de Talita -> acesso HTTPS e login institucional -> aplicação de análises no servidor -> consultas de leitura às fontes aprovadas.

O login identifica a usuária. A autorização define quais análises, departamentos e níveis de detalhe ela pode acessar. A conta técnica do banco deve ser restrita independentemente da proteção da tela. As permissões anteriormente existentes nos painéis não devem ser presumidas na nova aplicação.

### Caminho de disponibilização

| Momento | Onde funciona | Como Talita participa |
|---|---|---|
| Desenvolvimento | Ambiente do desenvolvedor, com demonstração sintética | Avalia telas e materiais em demonstrações acompanhadas |
| Homologação | Servidor interno de teste com controles de acesso | Executa casos conhecidos e registra divergências |
| Piloto restrito | Serviço interno monitorado, independente do computador do desenvolvedor | Usa nas demandas combinadas e envia feedback |
| Expansão | Somente após decisão conjunta | Novos departamentos, análises e usuários com regras/permissões definidas |

Sem servidor aprovado, manter demonstrações acompanhadas. Não transformar o notebook do desenvolvedor em hospedagem definitiva e não abrir acesso público improvisado.

### Experiência da usuária

Uma tela inicial com departamento, período, análises e modo de verificações adicionais; resultados organizados em corpo docente, matrículas, carga horária e pontos para conferência; tabela de filtros; datas e limitações; download de tabelas e gráficos; botão para relatar problema.

Preferir termos simples: Análises disponíveis, Gerar análises, Pontos para conferência, Como este resultado foi calculado e Baixar tabela. Não apresentar “agente”, “pipeline”, “prompt” ou SQL à usuária final.

Um resultado antigo deve continuar identificado com os filtros efetivos da execução. Alterar os campos da tela não pode fazer a interface aparentar que os resultados foram recalculados. Aprovações de aprofundamento não podem ser reaproveitadas após mudar filtros ou dados.

### Decisões operacionais a obter da DSI

Servidor e sistema operacional; DNS e HTTPS; rede/VPN; provedor de login; identidade/grupo de Talita; fontes e escopos permitidos; método de autenticação do SQL; conta técnica; canal de suporte; retenção de feedback/logs/exportações; responsável por atualizar e restaurar o serviço.

Não são perguntas para interromper o início do projeto: diagnóstico, testes sintéticos e definição das análises podem começar enquanto essas decisões são encaminhadas.

### Custo e continuidade

O aplicativo não terá cobrança de tokens porque não usará LLM. O uso do Codex durante o desenvolvimento é separado da operação do sistema. Infraestrutura existente pode evitar contratação de um novo serviço, mas ainda existem horas de desenvolvimento, validação, administração e suporte. Não prometer custo total zero.

Não definir uma compra de GPU ou serviço de inferência para esta PoC. Não adquirir hospedagem pública antes de avaliar a infraestrutura institucional disponível.

### Critérios de sucesso do piloto

Resultados conciliados com casos aprovados; nenhuma análise apresentada como válida quando está bloqueada; rastreabilidade de filtros e regras; nenhum aprofundamento sem aprovação no modo correspondente; exportações reutilizáveis; acesso autorizado e suporte definidos; redução de esforço avaliada a partir do tempo real das tarefas de Talita.

A aprovação de um piloto não significa que toda a universidade foi homologada. Ampliar em ciclos pequenos e testar os novos recortes.

## Referências e limites deste material

As regras de negócio derivam do contexto fornecido pelo usuário e da transcrição da reunião de 21/10 (Texto colado.txt). A referência de relatório do DEM não substitui validação das fontes e do período dos dados. As escolhas de arquitetura e implantação são recomendações deste plano, não políticas já confirmadas da PUC-Rio.

Documentação técnica consultada em 26/10/2026, a conferir novamente durante implementação:

- Instruções de projeto no Codex: https://developers.openai.com/codex/guides/agents-md
- Codex CLI: https://developers.openai.com/codex/cli
- Aprovações e segurança do agente: https://learn.chatgpt.com/docs/agent-approvals-security
- Autenticação Streamlit: https://docs.streamlit.io/develop/concepts/connections/authentication
- Cache e isolamento Streamlit: https://docs.streamlit.io/develop/concepts/architecture/caching
- SQLAlchemy com SQL Server: https://docs.sqlalchemy.org/en/20/dialects/mssql.html
- Configuração ODBC/TLS SQL Server: https://learn.microsoft.com/en-us/sql/connect/odbc/dsn-connection-string-attribute

Este pacote contém planejamento e prompts; não contém um aplicativo implementado. Não houve conexão ao banco da PUC-Rio, teste de credenciais ou implantação nesta conversa.