# Contexto do projeto VRAC

Atualizado em 26/10/2026. Fonte: [Guia de desenvolvimento](../Guia_Desenvolvimento_VRAC_Codex.md). As instruções permanentes estão em [AGENTS.md](../AGENTS.md).

## Objetivo e usuária

Talita, da VRAC/PUC-Rio, precisa consultar informações acadêmicas para avaliações departamentais e preparar insumos verificáveis. A aplicação deverá receber departamento, período e análises, executar consultas revisadas e apresentar tabelas, gráficos, filtros, fontes, limitações e exportações. A revisão e a decisão institucional permanecem humanas.

O aplicativo será interno, sem LLM, chatbot, agentes em execução, geração dinâmica de código ou dependência operacional de Power BI. Talita deverá utilizá-lo pelo navegador, sem instalar Python ou receber credenciais do banco. O Codex participa apenas do desenvolvimento.

## Escopo autorizado nesta entrega

Planejamento do projeto e fase 0: estrutura, ambiente reproduzível, configuração explícita, dados sintéticos determinísticos, demonstração local, proteção de acesso real e testes offline. Não implementar cálculos institucionais, conexão real ou publicação nesta fase. A conclusão técnica depende das verificações efetivamente executadas pelo responsável pelo setup; não representa aceite institucional.

As próximas entregas, mediante solicitação de cada fase, priorizam composição docente, depois matrículas e carga horária. Verificações adicionais serão determinísticas e terão catálogo fechado, limites e aprovação quando exigida.

## Exclusões

Não desenvolver análise financeira, curva guia, relatório institucional final automático, recomendações de contratação, CAPES, produção acadêmica, projetos patrocinados, relação aluno/docente ou classificação de contratação/desligamento. Não ampliar para exploração livre de dados ou plataforma genérica.

## Estado das evidências

| Item | Situação | Consequência |
|---|---|---|
| Guia e instruções do projeto | Disponíveis neste repositório | Orientam esta fase |
| SGBD | SQL Server é hipótese | Confirmar antes de escolher o adaptador real |
| Conectividade, credenciais e permissões | Não validadas nesta sessão | Nenhuma consulta real será executada pelo agente |
| Tabelas, colunas, chaves e fontes autorizadas | Não fornecidas em material sanitizado aprovado | Nenhum nome físico será inventado |
| Fórmulas e casos de referência | Não aprovados | Dados sintéticos não validam regras institucionais |
| Servidor, login e escopos de acesso | Não definidos pela DSI | Acesso autônomo com dados reais permanece bloqueado |
| Visibilidade e autorização do repositório remoto | Não verificadas | Matheus deve confirmar repositório privado autorizado antes de compartilhar material interno |

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

Consulte o [plano](PLAN.md), a [arquitetura](ARCHITECTURE.md), as [decisões](DECISIONS.md) e as [solicitações para a DSI](DSI_REQUESTS.md).
