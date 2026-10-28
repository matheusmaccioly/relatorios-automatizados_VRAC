Você apoia o desenvolvimento de uma PoC interna de análises acadêmicas da VRAC/PUC-Rio. A usuária final é Talita. Leia docs/PROJECT_CONTEXT.md e docs/PLAN.md. Trabalhe somente na fase solicitada.

OBJETIVO
Entregar análises de docentes, matrículas e carga horária por formulário, tabelas, gráficos e exportações. A aplicação deve operar sem LLM, chatbot, agentes, geração dinâmica de código ou dependência de Power BI. O Codex é utilizado apenas no desenvolvimento.

FORA DO ESCOPO
Não implementar análises financeiras, relatório institucional completo, decisões sobre contratação, integração CAPES, produção acadêmica ou exploração livre de dados. Não transformar a PoC em uma plataforma genérica.

ARQUITETURA
Adotar monólito modular em Python. Preferir Streamlit, pandas e Matplotlib. Usar SQLAlchemy/pyodbc se SQL Server for confirmado. Consultas SQL devem estar em arquivos revisados e parâmetros devem ser vinculados, não concatenados. Não introduzir FastAPI, frontend separado, filas, Redis, Kubernetes ou serviços pagos sem necessidade demonstrada e decisão explícita.

BRANDING INSTITUCIONAL
Todo elemento visual do sistema deve seguir o branding da PUC-Rio, incluindo interface, cores, tipografia, marcas, ícones, gráficos, tabelas, estados de tela e futuras exportações. Antes de alterar apresentação visual, leia assets/branding/README.md e os materiais oficiais fornecidos em assets/branding/guidelines/.
Utilize somente arquivos, variantes e valores oficiais autorizados para este projeto. Não inventar logotipos, paletas, fontes ou assinaturas PUC-Rio/VRAC. Centralizar recursos e tokens de identidade para uso consistente na aplicação e nas exportações.
Enquanto os materiais oficiais não estiverem disponíveis, registrar a identidade visual como pendente e tratar o tema da demonstração como provisório. Não declarar conformidade ou homologação visual sem revisão registrada por Matheus e pelo responsável institucional pela identidade visual.

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
