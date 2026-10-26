# Solicitações para DSI e DBA

Preparado em 26/10/2026 para encaminhamento por Matheus. **Nenhuma solicitação foi enviada por esta documentação e nenhum item foi aprovado ou provisionado nesta sessão.** A fase 0 pode continuar com dados sintéticos enquanto as respostas são obtidas.

## Informações e decisões necessárias

| ID | Solicitação | Responsável esperado | Critério de resposta |
|---|---|---|---|
| INF-01 | Ambiente para homologação e piloto interno | DSI | Servidor/VM/container permitido, sistema operacional, recursos, proprietário e rotina de atualização definidos |
| INF-02 | Endereço e acesso HTTPS | DSI | DNS, certificado, renovação, proxy e suporte às conexões da interface definidos; porta direta da aplicação restrita |
| INF-03 | Rede e conectividade autorizada | DSI + DBA | Rede/VPN, destinos, portas e política de saída necessários informados por canal aprovado; sem varredura de rede |
| IAM-01 | Mecanismo institucional de autenticação | DSI | OIDC ou proxy efetivamente disponível, parâmetros operacionais, política de sessão, logout e expiração aprovados |
| IAM-02 | Política de autorização | DSI + responsável pelo piloto + Talita | Identidades/grupos, departamentos, análises e níveis de detalhe permitidos; negar por padrão; domínio de e-mail isolado não libera acesso |
| DB-01 | Confirmação do SGBD e autenticação do banco | DBA + Matheus | Produto, ambiente, método de autenticação e requisitos de driver documentados; não presumir SQL Server ou porta |
| DB-02 | Conta técnica independente da conta pessoal | DBA + DSI | Identidade de serviço e somente leitura nas fontes aprovadas, com comprovação administrativa do escopo; sem teste de escrita |
| DB-03 | Fontes e metadados permitidos | DBA + responsável pelas fontes | Lista delimitada de bancos/schemas/objetos, granularidade permitida e regras de divulgação de metadados ao desenvolvimento |
| DB-04 | TLS e certificados | DSI + DBA | Cadeia confiável, nomes válidos, instalação e renovação definidos; não aceitar certificado arbitrário nem desativar criptografia |
| DB-05 | Orçamento e comportamento das consultas | DBA + Matheus | Limites de tempo, volume, concorrência e horários; procedimento para falha e revisão de desempenho |
| SEC-01 | Segredos e rotação | DSI | Mecanismo fora do Git e do workspace do agente, acesso do serviço, troca e revogação definidos; valores não devem ser enviados no chat |
| SEC-02 | Homologação de segurança e exposição | DSI + responsável pelo piloto | Critérios e responsáveis para liberar dados reais, testes de acesso negado e isolamento de sessões acordados |
| OPS-01 | Persistência operacional e retenção | DSI + Matheus | Decisão sobre SQLite ou alternativa, armazenamento de feedback/metadados, prazos, exclusão, backup e restauração; sem réplica acadêmica por conveniência |
| OPS-02 | Operação e suporte | DSI + responsável pelo piloto | Operador, canal de incidentes, logs mínimos, atualização, retorno à versão anterior e responsáveis por certificado/credenciais |
| GOV-01 | Uso do repositório e material de desenvolvimento | Matheus + responsável institucional | Repositório privado autorizado e política de uso de agentes/compartilhamento sanitizado confirmados |

A documentação versionada não deve conter senhas, connection strings reais, identidades pessoais, dumps ou endereços internos sem autorização. Respostas sensíveis ficam no canal institucional aprovado; trazer ao projeto apenas o resumo sanitizado necessário.

## Sequência de validação

1. Desde a fase 0, Matheus encaminha infraestrutura, login, conta técnica e fontes permitidas. Não há envio automático pelo agente.
2. Na fase 1, o DBA delimita o inventário; Matheus executa o diagnóstico no ambiente autorizado e registra apenas a evidência sanitizada aprovada.
3. Antes da fase 6, concluir autenticação, escopos, conta de serviço, TLS, sessão, exportações e retenção. Autenticar uma identidade não concede autorização ampla.
4. Antes de publicar, obter autorização explícita do responsável, concluir homologação e definir operador, suporte e recuperação.

## Registro de resposta

Para cada ID, registrar: situação (pendente, em análise ou aprovado), data, responsável, decisão e referência à evidência permitida. Todos os itens começam **pendentes**. Uma resposta não substitui as demais: conectividade não prova autorização; conta de leitura não autoriza publicar todos os dados; servidor disponível não significa segurança homologada.

Consulte as [questões abertas](DECISIONS.md) e os [critérios de passagem](PLAN.md) antes de avançar.
