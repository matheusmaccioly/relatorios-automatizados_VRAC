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
| D-018 | Detalhamento documental solicitado em 28/10/2026 | Preparar seis roteiros funcionais a partir das páginas e visuais dos dois painéis indicados; manter especificação e inventário internos somente locais, excluídos de Git/Docker | Evidências de visual e fórmulas documentais separadas de propostas; dupla função, gratificação e cargo administrativo não são equivalências presumidas; nenhum cálculo, contrato executável ou fase nova liberados |

## Complemento dos contratos — 28/10/2026

D-019: implementar somente os contratos lógicos dos seis roteiros nesta entrega,
com dependências e estados por métrica. As três famílias e nove variantes permanecem;
R05 não libera análises financeiras e seu encaixe de implementação segue pendente.
A autorização de Matheus para o Prompt 3 é condicional: faltam definição docente,
fonte, referência e aceite humano. Nenhum status institucional foi promovido.
Detalhes e filtros não aprovados continuam indisponíveis. Nenhum novo SQL foi criado
sem fonte física confirmada; a consulta de referência já existente não foi executada.

## Fluxo docente com regra parametrizada — 29/10/2026

D-021: implementar o fluxo de ponta a ponta da composição docente mantendo a regra como
parâmetro explícito, em vez de esperar a definição institucional para começar. Motivo:
as quatro combinações de população e referência temporal já estão documentadas; construir
o mecanismo em torno delas não escolhe nenhuma e permite demonstrar o fluxo a Talita
antes do aceite. Consequência: `CANDIDATE_FACULTY_RULES` mantém as quatro candidatas com
status `pending`, sem data e sem evidência; o resultado é no máximo parcial enquanto
houver pendência; `VALID` exige aprovação registrada com data e evidência, período
completo e todos os dados observados. Modo real continua bloqueado sem consultar o
repositório. Nenhuma variante foi selecionada, nenhuma fonte física foi mapeada e
nenhum aceite funcional foi registrado. Se Talita definir uma população ou referência
temporal fora das quatro candidatas, a regra correspondente precisará ser implementada;
o mecanismo e as camadas permanecem válidos.

D-022: a distribuição por categoria não é apresentada como partes exclusivas do total.
Quando a mesma identidade aparece em mais de uma categoria, o fluxo conta a sobreposição
e emite aviso, sem ratear, redistribuir ou ajustar o total. Classificação ausente é
contada em métrica própria, nunca inferida nem excluída do total.

## Questões abertas

D-020 — 28/10/2026: aplicar os materiais RGB e tipográficos fornecidos por Matheus
à demonstração existente, com fonte única de tokens e fontes servidas localmente.
Preservar os logos e seu respiro. Usar azul/ciano cujos RGB e hex coincidem; manter
amarelo/cinza pendentes nos componentes devido às divergências da prancha. Corpo em
Rethink Sans e títulos em Literata são proposta, sem aprovação institucional presumida.
Não criar favicon ou assinatura VRAC. Revisão no navegador interrompida pelo Computer
Use por impossibilidade de verificar a URL; nenhuma automação de navegador posterior.

| ID | Questão | Quem precisa validar | Efeito enquanto pendente |
|---|---|---|---|
| Q-001 | SQL Server, KAPPA e PUC_OLAP informados em 28/10; conta criada e autorização dos schemas declaradas por Matheus. Quais porta, schemas/objetos nominais, autenticação, driver e permissões efetivas? | Matheus + DBA/DSI | Integração real indisponível até completar configuração e registrar diagnóstico pelo operador; não presumir porta ou schemas |
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
