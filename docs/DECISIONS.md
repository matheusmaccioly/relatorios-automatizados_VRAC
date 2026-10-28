# Decisões e questões abertas

Registro iniciado em 26/10/2026. “Adotada para a fundação” descreve uma decisão técnica desta entrega; não significa homologação da DSI nem aprovação de regra de negócio por Talita.

## Decisões

| ID | Estado | Decisão e motivo | Consequência |
|---|---|---|---|
| D-001 | Definida no guia | Aplicação interna sem LLM, chatbot, agentes ou geração dinâmica de SQL/Python | Não há dependência de inferência na operação; Codex apoia somente o desenvolvimento |
| D-002 | Adotada para a fundação | Monólito modular Python, com Streamlit, pandas e Matplotlib | Entregas pequenas; cálculo testável fora da interface; nenhuma API separada nesta fase |
| D-003 | Adotada para a fundação | Python 3.12, uv e lockfile, com ferramentas e ambiente locais ao projeto | Registrar versões resolvidas e testar instalação; plataforma institucional ainda precisa ser confirmada |
| D-004 | Adotada para a fundação | Demonstração sintética é o padrão; modo real é explícito e permanece bloqueado | Erros não ativam fixture silenciosamente; não há conexão institucional na fase 0 |
| D-005 | Definida no guia | Composição docente será a primeira análise completa | Matrículas e carga aguardam revisão da primeira entrega e serão incrementos separados |
| D-006 | Definida no guia | Consultas reais executadas pelo desenvolvedor autorizado fora da sessão do agente | Somente metadados e resultados sanitizados aprovados podem voltar ao contexto do agente |
| D-007 | Atualizada na fase 1 | Adaptador condicional SQL Server em extra opcional, sujeito à confirmação explícita de SGBD e escopo | Bibliotecas instaladas para testes offline não confirmam o ambiente institucional; nenhuma conexão real nesta entrega |
| D-008 | Definida no guia | Acesso real autônomo depende de autenticação, autorização, conta técnica restrita e homologação | Credenciais recebidas pelo desenvolvedor não liberam publicação nem definem o escopo de Talita |
| D-009 | Adotada para a fundação | Criar módulos de análises, verificações e exportações quando houver comportamento implementado | Evita abstrações vazias; suas responsabilidades já estão registradas na arquitetura |
| D-010 | Adotada na fase 1 em 27/10/2026 | CLI manual exige `--execute` antes de ler configuração externa; cada comando usa um banco e lista fechada de schemas aprovados | Não integrar diagnóstico/inventário à tela de Talita; não presumir porta, driver ou autenticação |
| D-011 | Adotada na fase 1 em 27/10/2026 | Pasta privada nova por execução fora do workspace, sem metadados físicos no console | Aplicar DACL de usuário no Windows ou modo 0700/0600 no POSIX antes de gravar; falha de proteção bloqueia a operação |
| D-012 | Adotada na fase 1 em 27/10/2026 | Qualidade/cardinalidade ficam como templates agregados desabilitados | Exigir revisão de objetos, filtros e custo antes de qualquer consulta fixa futura; nenhuma geração dinâmica de SQL |
| D-013 | Adotada em 27/10/2026 | Agrupar guias de uso, operação e referências em subpastas de `docs/`, com índice central | Preservar pontos de entrada de código e contexto/plano usados pelo agente; conteúdo do guia original mantido |
| D-014 | Requisito do usuário registrado em 27/10/2026 | Todo o sistema deve seguir o branding institucional da PUC-Rio; materiais centralizados em `assets/branding/` | Aplicação visual depende de arquivos e regras oficiais, sem inventar marcas, paleta ou fontes; tema atual provisório |
| D-015 | Adotada no Prompt 2 em 27/10/2026 | Sem metadados sanitizados aprovados, preparar catálogo e contratos lógicos com casos sintéticos | Fontes físicas não mapeadas, fórmulas propostas e adaptadores reais de análises bloqueados; nenhuma aprovação institucional inferida de testes |
| D-016 | Adotada no Prompt 2 em 27/10/2026 | Comparar contagens exatamente; horas exigem critério registrado; equivalências de curso precisam cobrir todo o período e ter aprovação | Sem relaxar tolerâncias para conciliar valores, substituir Horas Reais ou unir séries por nomes; fixtures não se aplicam ao modo real |
| D-017 | Revisão documental solicitada em 27/10/2026 | Basear o catálogo nos modelos acadêmicos A/B, com nove variantes sem escolha automática; manter documento interno e nomes semânticos detalhados em arquivos locais excluídos do Git | Modelo C fora da implementação; nomes de modelo não comprovam SQL; referência física, unidade de horas, calendário, RLS e aceite institucional continuam pendentes |

## Questões abertas

| ID | Questão | Quem precisa validar | Efeito enquanto pendente |
|---|---|---|---|
| Q-001 | Qual é o SGBD, autenticação, rede, porta e conjunto de fontes autorizado? | Matheus + DBA/DSI | Integração real indisponível; SQL Server continua hipótese |
| Q-002 | A conta de execução só pode ler os objetos e recortes aprovados? | DBA | Não declarar privilégio confirmado; não testar comandos de escrita |
| Q-003 | Qual população, granularidade e referência temporal definem composição docente? | Talita + responsável pelas fontes | Nenhum cálculo institucional aprovado |
| Q-004 | Matrícula significa inscrição, aluno único ou outra unidade? Quais equivalências de cursos têm vigência aprovada? | Talita + responsável pelas fontes | Série real e combinação de cursos aguardam contrato |
| Q-005 | Qual fonte define Horas Reais, unidade e cobertura interdepartamental? Como identificar compartilhamento? | Talita + responsável pelas fontes/DBA | Não substituir indicador por soma ou rateio |
| Q-006 | Qual data de matrícula e quais exceções regem turmas sem alunos? Onde está a classificação confiável de TCC? | Talita + responsável pelas fontes | Apenas registrar limitações; nenhuma exclusão ou inferência automática |
| Q-007 | Qual servidor, login institucional, grupo autorizado e escopo por departamento/análise/detalhe? | DSI + responsável pelo piloto | Acesso real autônomo e publicação bloqueados |
| Q-008 | SQLite operacional é permitido? Quais retenção, backup e regras de feedback/logs/exportações? | DSI + Matheus | Não persistir dados acadêmicos por conveniência; armazenamento ainda não adotado |
| Q-009 | Quais verificações e limiares Talita aprova? Qual orçamento de consulta? | Talita + Matheus + DBA | Verificações não aprovadas ficam desabilitadas |
| Q-010 | Quem opera, atualiza, restaura e presta suporte ao piloto? | DSI + responsável pelo piloto | Operação não pode ser declarada pronta |
| Q-011 | O repositório remoto é privado e autorizado? Quais materiais podem ser compartilhados no desenvolvimento com agente? | Matheus + responsável institucional | Manter apenas código e dados sintéticos; não presumir isolamento pela execução local |
| Q-012 | Quais manual, logos, paleta, fontes, ícones, templates e variantes são oficiais para o sistema? Quem valida a aplicação visual? | Matheus + responsável institucional pela identidade visual | Materiais e aplicação visual pendentes; não declarar conformidade institucional |

Ao resolver uma questão, registrar data, decisão, responsável pela validação e evidência sanitizada. Não substituir pendência por suposição nem registrar aprovação inexistente.
