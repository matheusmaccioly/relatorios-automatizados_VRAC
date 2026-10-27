# Modelo de dicionário sanitizado — entrega da fase 1

Atualizado em 27/10/2026. **MODELO NÃO PREENCHIDO; fontes, conexão, inventário e regras NÃO VALIDADOS.** Os termos abaixo são nomes lógicos propostos, sem correspondência física confirmada. Não são tabelas, colunas ou chaves existentes na PUC-Rio.

Matheus deve preencher e revisar este material antes de liberar sua leitura pelo agente. Manter `dbconfig.toml`, o inventário bruto e o mapa lógico → físico em diretório privado externo. Cada execução gera sua subpasta UUID privada, com `diagnose.json` ou `inventory.json`; consultar os arquivos localmente sem copiá-los para este modelo. Não colar servidor, banco/schema/objeto/coluna física, identidade, senha, connection string, registros individuais ou exemplos identificáveis. Se algum nome físico for indispensável a uma tarefa posterior, obter autorização específica antes de fornecê-lo; este modelo não concede essa autorização.

## Registro da liberação

| Campo | Preencher com material aprovado |
|---|---|
| Versão/data desta entrega sanitizada | Pendente |
| Responsável pela revisão | Pendente; usar função ou identificação cuja divulgação seja autorizada |
| Autorização de divulgação ao desenvolvimento com agente | Pendente; referência sanitizada e escopo permitido |
| SGBD confirmado | Pendente; SQL Server continua hipótese até confirmação |
| Diagnóstico executado por Matheus | Não executado nesta sessão; registrar data, resultado sanitizado e limitações |
| Inventário executado e cobertura | Não executado nesta sessão; registrar alcance, truncamentos e itens desconhecidos sem nomes físicos |
| UUID das execuções e evidência sanitizada | Pendente; UUID pode vincular o registro, sem revelar caminhos dos relatórios privados |
| Conta e escopo de leitura revistos pelo DBA | Pendente; evidência administrativa sanitizada, sem identidade ou senha |
| Objetos físicos e filtros aprovados | Mapa privado externo; registrar aqui somente quais fontes lógicas estão cobertas |

“Aprovado” exige data, responsável e evidência permitida. Resultado de mock ou fixture não aprova origem real. Ausência de metadado visível deve continuar desconhecida. Mesmo um inventário com estado técnico `valid` mantém cobertura `unknown`; distinguir sucesso da consulta de completude e aprovação institucional.

## Fontes lógicas a identificar

Preencher uma ficha por fonte. Não presumir que cada conceito tem uma única fonte física nem que uma fonte atende a todos os conceitos.

| Conceito lógico | Pergunta para o responsável pela fonte | Estado inicial |
|---|---|---|
| Docente | Qual chave lógica identifica uma pessoa sem expor nome, matrícula funcional ou outro identificador real? | Desconhecido |
| Vínculo docente | Como distinguir pessoa, vínculo, cargo, vigência, afastamento e movimentação? | Desconhecido |
| Referência temporal docente | Uma linha representa mês, foto em uma data ou presença no semestre? Como tratar períodos parciais? | Desconhecido |
| Departamento do vínculo | Qual referência define o pertencimento institucional e sua vigência? | Desconhecido |
| Departamento da disciplina | Como distinguir o departamento da oferta daquele do vínculo? Há cobertura interdepartamental autorizada? | Desconhecido |
| Matrícula/aluno/curso | A unidade é inscrição, matrícula por componente ou aluno único? Qual período e situação entram no recorte? | Desconhecido |
| Equivalência de cursos | Existe fonte institucional com vigência e aprovação para renomeações/reestruturações? | Desconhecido |
| Horas Reais | Qual fonte oficial, população, unidade e referência temporal definem o indicador? | Desconhecido |
| Alocação por turma/currículo | Qual granularidade e quais identificadores confiáveis distinguem compartilhamentos? | Desconhecido |
| Matrícula da turma e classificação | Qual data de encerramento/referência, exceções e classificação confiável de TCC/monografia? | Desconhecido |
| Atualização e cobertura | Quando a origem é atualizada, quais recortes cobre e como indicar correções históricas? | Desconhecido |

## Ficha de uma fonte lógica

Copiar a ficha sem introduzir nomes físicos ou dados individuais:

| Atributo | Valor aprovado ou “desconhecido” |
|---|---|
| Identificador lógico neutro da fonte | A definir |
| Pergunta atendida/população e exclusões | A definir |
| Responsável pela definição | A definir |
| Granularidade exata de uma linha | A definir |
| Chaves lógicas e se são simples/compostas | A definir |
| Chaves declaradas visíveis x unicidade apenas observada | A definir; não confundir as duas evidências |
| Tipos, precisão/escala, unidade e nulabilidade por campo lógico | A definir |
| Significado de nulo, zero, ausência de linha e erro | A definir |
| Filtros lógicos autorizados e suas vigências | A definir |
| Referência temporal e tratamento de semestre parcial | A definir |
| Data de extração x atualização da fonte | A definir; não presumir igualdade |
| Cobertura departamental/interdepartamental e limitações | A definir |
| Evidência agregada de qualidade e recorte aprovado | Não executada; aprovação própria necessária |
| Situação: aprovado, parcial ou bloqueado | Bloqueado até validação |
| Versão/data/responsável/evidência da aprovação | Pendente |

## Relações lógicas

Para cada relação necessária, registrar fonte lógica de origem/destino, chaves lógicas, cardinalidade esperada e observada, nulabilidade, vigência e risco de multiplicação de linhas. Diferenciar FK/PK/UQ declarada e visível de hipótese de junção. Não juntar por semelhança de nomes nem assumir relação 1:1.

Truncamento do inventário pode devolver apenas parte das colunas de uma chave composta ou FK. Não registrar esse fragmento como chave completa nem utilizá-lo para contratos de deduplicação/junção sem confirmação do DBA.

Em especial, esclarecer docente → vínculos → meses, vínculo → departamento, disciplina → departamento, alocação → turma/currículo/compartilhamento e matrícula → curso/período. A menção destes conceitos não confirma que exista uma relação física disponível ou autorizada.

## Primeira entrega necessária para a fase 2

Priorizar composição docente: fonte lógica, pessoa versus registro/vínculo, população, granularidade temporal, chave de deduplicação aprovada, filtros e categorias de vínculo, exclusões, unidade, atualização e limitações. Talita e o responsável pela fonte devem aprovar um caso de referência do mesmo recorte e data, com apenas valores agregados cuja divulgação tenha sido autorizada.

Para matrículas e carga, manter pendentes as definições ainda não aprovadas. Não somar contagens mensais de docentes, substituir Horas Reais pela soma de disciplinas, deduzir TCC pelo nome, equiparar cursos ou inferir contratação por datas de cargo. Regras e tolerâncias serão formalizadas na fase 2; este dicionário não as implementa.

Antes de entregar ao agente, Matheus deve confirmar que o conteúdo é necessário à tarefa, está sanitizado, tem divulgação autorizada e distingue fatos, hipóteses e lacunas. As instruções operacionais estão em [DATABASE_DISCOVERY.md](DATABASE_DISCOVERY.md).
