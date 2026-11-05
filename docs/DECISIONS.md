# Decisões e questões abertas

Registro iniciado em 26/10/2026. “Adotada para a fundação” descreve uma decisão técnica desta entrega; não significa homologação da DSI nem aprovação de regra de negócio por Talita.

## Decisões

**D-035 — migração e autenticação Supabase, Matheus, 05/11/2026:** Matheus solicitou
migrar dados, schemas e aplicação e configurar Supabase Auth. Autorizado transferir
a base sintética existente ao projeto indicado, preservando o monólito Streamlit e
as fórmulas. O schema original permanece sem acesso pelas contas da aplicação;
projeções tipadas R01–R06 são lidas por duas RPCs fixas sob RLS por departamento.
Supabase Auth verifica a identidade, uma lista administrativa define o escopo e uma
verificação restrita de `auth.sessions` invalida leituras após revogação. Cadastro
público desativado; aplicação usa apenas chave publicável e JWT individual.
Uma conta criada por Matheus foi liberada para os quatro departamentos sintéticos;
ele confirmou: “Entrei e consegui calcular”. A solicitação substitui a atribuição
anterior de autenticação exclusivamente ao time neste incremento. Não autoriza
transferir fontes institucionais, publicar a aplicação ou declarar homologação.
[Operação, testes e limitações](operations/SUPABASE.md).

**D-034 — conferência fora do menu, Matheus, 05/11/2026:** a pedido de Matheus, Conferir dados
sintéticos deixa de ser aba e passa a bloco recolhido no fim de todas as telas, acima do
rodapé. Conteúdo, filtros e regras da tela não mudam.

**D-033 — tabelas visuais, gráficos primeiro e item financeiro, Matheus, 05/11/2026:**
Matheus pediu tabelas mais visuais, conversão de tabelas em gráficos e uma aba não clicável
de Análise financeira com "em breve", deixando a ponderação ao agente. Decidido:
(1) o indicador de carga recebe símbolo e fundo somente na tela; CSV, ZIP, PNG e o texto da
regra não mudam. (2) Nenhum estado usa vermelho: o indicador não avalia produtividade, e
abaixo ou acima do esperado não é erro. A direção é dada pelo símbolo, o estado pelo texto;
fundo só com tokens existentes, e "Dentro do esperado" fica sem destaque. Essas associações
de cor são proposta, pois cores semânticas seguem pendentes (Q-012). (3) Tabela que alimenta
gráfico fica recolhida no cartão dele, em **Ver tabela do gráfico**, com o mesmo CSV;
tabela sem gráfico fica em **Outras tabelas e arquivos**, e sem nenhum gráfico ela abre
expandida. (4) Barras com valor nulo continuam no eixo com o texto "ausente"; antes a
categoria desaparecia. (5) **Análise financeira é só um rótulo do menu:** não é aba, não
abre conteúdo, não recebe foco e não consulta dados. Isso não amplia o escopo: análises
financeiras seguem fora da PoC, e implementá-las exige decisão explícita própria.
(6) Cabeçalho das tabelas em preto com texto branco, para separar título e dados.

**D-032 — referência do design system, Matheus, 04/11/2026:** Matheus informou que o
[site público](https://www.puc-rio.br/) e `portal_solucoes_puc.html` são o que há de
mais próximo do design system da PUC-Rio e pediu que o front-end siga essas normas.
Na interface e nas exportações, isso **substitui a D-021 e o trecho da D-031** que
mantinham a paleta anterior: amarelo passa a `#FFB52F`, com `#E08C07`, `#BF6000`,
`#7817B1`, `#00A2AC`, `#BE002D`, `#1F1F1F`, `#CDCAC1` e `#F5F5F0` do
[CSS público](https://www.puc-rio.br/styles/index_puc_tapume.css), além de `#333333`,
`#EBEBE4` e `#FFF1D2` do portal. Azul `#0081AD` e ciano `#00B7DD` seguem a prancha. A
marca passa à variante oficial horizontal monocromática, sobre o fundo da página, como
no site e no portal. Para gráficos, a ordem fixa é `#0081AD`, `#E08C07`, `#7817B1`,
`#00A2AC`, `#BF6000`, aprovada no validador de paleta (luminosidade, croma, daltonismo e
vizinhas); `#E08C07` fica abaixo de 3:1 sobre branco, por isso legenda e tabela são
obrigatórias. Vermelho fica reservado a erros.

Site e portal continuam sendo referências, não um manual aprovado: a prancha EMoD segue
como fonte das assinaturas e a divergência entre ela e o site é conhecida. A troca não
é homologação; Q-012 segue aberta. Reverter exige apenas editar `tokens.toml` e rodar
`scripts/sync-branding.py`. Nenhuma fórmula, SQL ou fonte de dados foi alterada.

**D-031 — revisão de interface solicitada por Matheus, 04/11/2026:** aproximar a
apresentação de `portal_solucoes_puc.html` e do site público da PUC-Rio, melhorar
filtros/caminhos e gráficos responsivos/interativos na aplicação Streamlit existente.
As referências orientam composição e uso; não são instruções executáveis nem
evidência de um design system integralmente aprovado. Preservar cores e arquivos
autorizados. Títulos/corpo em Rethink Sans, Literata na identificação editorial,
ações pretas e acentos amarelos são proposta local desta revisão.

A paleta do portal/site difere dos tokens e não os substitui. Fontes são locais;
não incorporar scripts/CDNs do HTML. Manter contratos analíticos, SQL, fontes e
exports existentes. A R06 passa à apresentação Altair, como os demais gráficos,
com PNG preservado. Nenhum novo serviço, conexão a banco ou publicação.
Matheus e o responsável institucional revisam a identidade; Talita revisa o uso.
[Entrega, execução e limites](guides/INTERFACE_E_GRAFICOS.md).

**Aceite do Prompt 4a — 03/11/2026:** Matheus declarou nesta conversa “tudo validado
por mim e conciliado”. Encerrar a 4a no escopo sintético com essa confirmação
humana e manter a 4b (carga horária) como próximo incremento, sem iniciá-la nesta
atualização. A declaração não é nova execução PostgreSQL pelo agente, evidência
de uma saída específica da rotina, homologação institucional ou aceite de Talita.
Preservar testes offline e limitações registrados; sem nova aprovação geral das
fórmulas ou antecipação da integração institucional.

**Registro técnico do Prompt 4a — 03/11/2026:** aplicado o escopo solicitado de
matrículas, sob D-022/D-027/D-028. Nenhuma nova regra analítica aprovada ou exigida.
Correções limitadas ao detalhe FR/TD no recorte do código do curso e à descrição
da variação com atual ausente. Conferência offline separada de leitura PostgreSQL,
que fica para execução explícita pelo desenvolvedor. Referência independente e
leitor existente devem compartilhar transação/snapshot; não usar números antigos
da documentação como prova da base. Bolsas por departamento continuam sem vigência
temporal e Centro permanece não informado sem relação explícita. Sem carga/recriação
de banco, relaxamento de TLS, avanço para 4b ou publicação.
[Evidências e limitações](guides/PROMPT4A_MATRICULAS.md).

**D-030 — interface docente solicitada por Matheus, 03/11/2026:** reproduzir os
tipos de gráficos e os detalhes das seis capturas na aba Análise docente, com
filtros dependentes Centro > Departamento. As capturas orientam a apresentação;
nomes e números não viram dados de demonstração. R01 mantém suas unidades e
Horas Reais da fonte dedicada; R03 acrescenta contagens distintas mensais,
sem somar meses ou quadros para obter totais. A opção Todos os departamentos
respeita o centro escolhido e os arquivos identificam o escopo efetivo.

O contrato público PostgreSQL sintético não fornece relação de centros; exibir
Centro não informado até o mapeamento estar disponível. Centros da fixture em
memória são simulações explícitas para conferir a cascata, sem vínculo presumido
com centros institucionais. Somente essa lacuna de filtro permanece limitada.
Identidade usa os tokens locais já escolhidos; revisão institucional permanece
pendente. Sem conexão a banco, alteração de fórmulas de carga ou publicação.
[Arquivos, execução e limites](guides/PROMPT3_DOCENTES.md).

**D-029 — Prompt 3, 03/11/2026:** apresentação web docente com Altair 6.3,
dependência direta já existente no lock via Streamlit. Mesmas tabelas calculadas
alimentam hover, destaque local de séries/barras e tabelas equivalentes; seleção
visual não altera população, denominadores, totais ou exportações. Matplotlib
permanece nos PNGs. Tokens/fontes locais, sem frontend ou serviço adicional.
R03 mostra total distinto separado das pilhas de presenças por quadro, cuja
sobreposição é explicitada. Escopo analítico R01–R03, reaproveitando R04/R05;
R06 preservado. Sem conexão PostgreSQL/institucional nesta tarefa. Revisão visual
dos gráficos no navegador não concluída por bloqueio da ferramenta de automação;
nenhuma homologação presumida. [Evidências e roteiro](guides/PROMPT3_DOCENTES.md).

**D-028 — orientação explícita de Matheus em 03/11/2026:** usar o PostgreSQL
sintético existente durante o desenvolvimento e preparação da versão. Conexão,
diagnóstico, inventário e integração/conferência institucionais somente na etapa
final do projeto e deploy. O Prompt 1 real fica adiado; não bloqueia mapa
lógico/sintético do Prompt 2 nem análises, verificações e feedback dos Prompts 3–5.
Preservar ferramentas e testes offline já preparados, sem declarar execução ou
conclusão institucional. No final, completar o mapa físico/leitor e conferir
resultados no ambiente autorizado antes do uso real. Operador executa comandos
reais fora da sessão do agente; manter TLS, validação de certificado, escopo e
somente leitura. Autenticação e assuntos relacionados permanecem com o time de
desenvolvimento. A mudança reorganiza o trabalho, sem autorizar conexão ou deploy
agora, revalidar fórmulas documentadas ou converter evidência sintética em real.

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
| D-021 | Escolha de Matheus em 30/10/2026 | Usar amarelo `#F1BA2A` e cinza `#869597` (hex impresso na prancha EMoD 23-10-18) na interface: amarelo em realces e aviso de demonstração, cinza em contornos | Divergência RGB/hex resolvida por decisão do projeto, não por confirmação institucional; texto pequeno permanece preto por contraste; revisão do responsável pela identidade visual pendente (Q-012) |
| D-022 | Orientação explícita de Matheus em 30/10/2026 | Os cálculos serão baseados nos dashboards existentes e no que já está documentado, sem necessidade de nova validação das regras | Substitui exigências anteriores de reaprovação analítica para essas regras; reproduzir o comportamento documentado e registrar somente lacunas concretas por resultado. Testes técnicos, segurança e limites de fase permanecem aplicáveis; não implica homologação institucional ou conexão validada |
| D-023 | Solicitação explícita de Matheus em 30/10/2026 | Gerar dados e banco PostgreSQL totalmente sintéticos a partir do modelo semântico documentado para apoiar os próximos passos | Ambiente portátil local separado do SQL Server institucional, carga determinística, TLS e conta de leitura; metadados detalhados e carga ignorados no Git/Docker. Sem extrair dados reais, converter todo o Power BI ou avançar automaticamente às próximas fases |
| D-024 | Escolha de Matheus em 30/10/2026 | Fundo da página em `#F5F5F0`; cabeçalho com assinatura, avisos e blocos de conteúdo sobre branco | Cor fora da prancha oficial, registrada como decisão do projeto e não como cor institucional; revisão do responsável pela identidade visual pendente (Q-012) |
| D-025 | Solicitação explícita de Matheus em 30/10/2026 | Conectar a demonstração Streamlit ao PostgreSQL sintético local para carregar filtros, registros docentes e alocações por turma | Driver opcional Psycopg; SQL fixo parametrizado; views locais com mapeamento interno ignorado no Git; conta de leitura, TLS e timeouts. Erros removem resultados anteriores e não ativam memória. Modo institucional bloqueado; sem novos cálculos ou avanço automático das demais fases |
| D-026 | Solicitação explícita de Matheus em 30/10/2026 | Iniciar a fase 3 somente com a composição docente: R01 reproduz a página Análise Geral (cadastro atual, contagem de matrículas funcionais, Horas Reais do semestre mais recente e semáforo literal); R02 entrega o geral e bloqueia QP | QP não tem regra documentada (V03) e fica bloqueado; filtro salvo de quadro da página não tem valores no inventário e é exibido como lacuna; quadros sintéticos `PROF *` não recebem faixa do semáforo, sem equivalência presumida; matrículas e carga (fases 4a/4b) não iniciadas |

## Ampliação autorizada — 30/10/2026

**D-027 — solicitação explícita de Matheus:** implementar todos os roteiros acadêmicos
documentados e gerar dados fictícios complementares para avançar o máximo possível.
Substitui o limite anterior da D-026 de somente composição docente. R01–R06 passam a
ter cálculo e apresentação sintéticos, com conferências e exportações. Não autoriza
consulta institucional, publicação, análise financeira ou decisões sobre pessoal.

QP é um grupo configurável de simulação, sem equivalência institucional presumida.
Unidades comparáveis e quinze atos/vigências fictícios são dados suplementares
identificados, preservando a carga original. A classificação administrativa depende
de evidência e vigência explícitas, não de gratificação ou nome de cargo. O acesso
da aplicação continua somente leitura com TLS; preparação de dados ocorre apenas
no script local de desenvolvimento. Regras já documentadas seguem a D-022, sem nova
rodada de validação analítica. Revisão institucional/visual não foi presumida.

## Complemento dos contratos — 28/10/2026

D-019: implementar somente os contratos lógicos dos seis roteiros nesta entrega,
com dependências e estados por métrica. As três famílias e nove variantes permanecem;
R05 não libera análises financeiras e seu encaixe de implementação segue pendente.
A autorização de Matheus para o Prompt 3 é condicional: faltam definição docente,
fonte, referência e aceite humano. Nenhum status institucional foi promovido.
Detalhes e filtros não aprovados continuam indisponíveis. Nenhum novo SQL foi criado
sem fonte física confirmada; a consulta de referência já existente não foi executada.

## Questões abertas

Atualização de 30/10/2026: pela D-022, Q-003 a Q-006 deixam de exigir nova aprovação
das regras já documentadas. Suas perguntas servem apenas para localizar definições
nos dashboards e documentos; registrar pendência somente onde houver lacuna concreta.
O mapeamento físico necessário à implementação continua técnico. As demais questões
mantêm seus escopos; nenhuma nova validação analítica deve ser criada por este registro.

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
| Q-013 | Qual relação explícita entre Centro e Departamento deve ser exposta pela origem sintética e, na etapa final, pela origem institucional? | Matheus + responsável pela fonte; DBA na integração final | PostgreSQL mostra Centro não informado; a cascata em memória usa centros declaradamente fictícios. Nenhuma relação institucional é presumida |

Ao resolver uma questão, registrar data, decisão, responsável pela validação e evidência sanitizada. Não substituir pendência por suposição nem registrar aprovação inexistente.
