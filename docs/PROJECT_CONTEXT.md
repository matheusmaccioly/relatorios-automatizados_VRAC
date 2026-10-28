# Contexto do projeto VRAC

Atualizado em 27/10/2026. Fonte: [Guia de desenvolvimento](references/Guia_Desenvolvimento_VRAC_Codex.md). As instruções permanentes estão em [AGENTS.md](../AGENTS.md).

## Objetivo e usuária

Talita, da VRAC/PUC-Rio, precisa consultar informações acadêmicas para avaliações departamentais e preparar insumos verificáveis. A aplicação deverá receber departamento, período e análises, executar consultas revisadas e apresentar tabelas, gráficos, filtros, fontes, limitações e exportações. A revisão e a decisão institucional permanecem humanas.

O aplicativo será interno, sem LLM, chatbot, agentes em execução, geração dinâmica de código ou dependência operacional de Power BI. Talita deverá utilizá-lo pelo navegador, sem instalar Python ou receber credenciais do banco. O Codex participa apenas do desenvolvimento.

## Escopo autorizado nesta entrega

A solicitação atual inclui revisar a base do Prompt 2 com a documentação semântica
fornecida por Matheus. O catálogo registra nove variantes para as três análises e um
mapeamento local excluído do Git organiza nomes e tipos de 12 tabelas. São objetos de
modelos Power BI, sem comprovação de origem SQL. O dicionário físico da fase 1 continua
não preenchido; fontes e regras permanecem propostas, sem seleção institucional e com
adaptadores reais bloqueados. A fase 0 e as ferramentas manuais da fase 1 estão preparadas;
a organização documental e o branding foram preservados. Não houve conexão real,
inventário institucional ou aceite funcional humano. Fases 3–7 não iniciadas.

Todo o sistema deve seguir a identidade visual institucional. Os materiais oficiais ficam
em [assets/branding/](../assets/branding/README.md). Logos, paleta, fontes e regras de uso
ainda não foram fornecidos; a aplicação do branding permanece pendente e o tema da
demonstração é provisório.

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
| SGBD | SQL Server é hipótese | Adaptador opcional preparado, condicionado à confirmação humana e à aprovação do escopo |
| Conectividade, credenciais e permissões | Não validadas nesta sessão | Nenhuma consulta real será executada pelo agente |
| Tabelas, colunas e medidas semânticas | Documentação local fornecida e mapeada; modelos A/B acadêmicos, C fora do escopo | Evidência de implementação; origem física, chaves, autorização e regras ainda exigem confirmação |
| Fórmulas e casos de referência | Não aprovados | Dados sintéticos não validam regras institucionais |
| Servidor, login e escopos de acesso | Não definidos pela DSI | Acesso autônomo com dados reais permanece bloqueado |
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
