# Configurar o KAPPA — passo a passo para Matheus

**Escopo atualizado em 03/11/2026 (D-028): execução adiada para a etapa final do
projeto e deploy.** Até lá, usar o PostgreSQL sintético existente. Não é necessário
preencher configuração real ou executar os comandos abaixo agora; este roteiro
permanece preparado para o operador na etapa final, sem bloquear os Prompts 2–5.

Servidor **KAPPA** e banco **PUC_OLAP** já estão preenchidos no
[modelo preparado](../../config/database.kappa.example.toml). Não precisa editar
o exemplo genérico nem os arquivos Python. A configuração ainda não está pronta
para conectar: faltam os detalhes abaixo, que não foram presumidos.

## 1. Fazer sua cópia privada

No Explorador de Arquivos, copie `config/database.kappa.example.toml` para uma pasta
privada local aprovada pela DSI, **fora deste projeto e de pastas sincronizadas**.
Renomeie a cópia para **dbconfig.toml**. Confira se o Windows não acrescentou `.txt`.
Abra essa cópia em um editor de texto e salve em **UTF-8 sem BOM**.

Não coloque usuário ou senha no modelo do repositório. Preencha apenas a cópia
privada, fora da sessão do agente. O agente não precisa ler esse arquivo.

## 2. Preencher os campos numerados

| Campo no arquivo | O que você precisa colocar | Onde obter |
|---|---|---|
| `port = 0` | Substitua `0` pela porta TCP numérica, sem aspas | DBA/DSI |
| `schemas = []` | Lista nominal autorizada, no formato `["NOME_1", "NOME_2"]` | DBA; não são nomes de tabelas nem o nome do banco |
| `driver = ""` | Nome exato do driver ODBC instalado, dentro das aspas | DSI |
| `auth_mode = ""` | `"windows"` ou `"sql_password"` | Mesmo método usado para entrar no SSMS |
| `scope_approved = false` | Troque por `true` depois de confirmar os detalhes do escopo, a execução e somente leitura com o DBA | Matheus + DBA |

**Se entra no SSMS com Autenticação do Windows:** use `auth_mode = "windows"` e
deixe `username` e `password` vazios.

**Se entra no SSMS com Autenticação do SQL Server:** use
`auth_mode = "sql_password"` e preencha `username` e `password` somente na cópia
privada. Mantenha as aspas. Strings TOML com aspas ou barras invertidas exigem escape;
se sua senha contiver esses caracteres, use uma string literal entre aspas simples
quando ela não contiver apóstrofo. Não envie a senha para obter ajuda.

As demais opções já estão prontas ou usam os limites padrão do programa. Não é
necessário preencher IP, connection string, TLS, timeouts ou variáveis de ambiente.
O código já exige criptografia e validação de certificado. O nome de conexão deve
corresponder ao certificado; eventual ajuste deve ser orientado pela DSI/DBA.

## 3. Pedir somente os detalhes que faltam

Você já informou que os schemas necessários estão autorizados. Não é necessário
recomeçar o pedido de acesso. Você pode copiar este texto e encaminhar pelo canal
institucional; nenhum envio foi feito pelo agente:

> Meu usuário já foi criado no SQL Server KAPPA, banco PUC_OLAP, e os schemas
> necessários à aplicação VRAC estão autorizados. Para preencher a configuração,
> preciso da porta TCP do endpoint autorizado, dos nomes exatos dos schemas/objetos
> liberados, do método de autenticação e do nome do driver ODBC recomendado e
> instalado. Podem confirmar também que minha conta é somente leitura nesses
> objetos, que posso executar o diagnóstico e inventário de metadados nesse recorte
> e que o certificado será validado com o nome KAPPA?

Enquanto não tiver a porta e a lista nominal de schemas, deixe os campos pendentes.
Não use uma porta padrão nem `dbo` por tentativa.

## 4. Roteiro operacional do Prompt 1 — 03/11/2026

**Preparado e conferido offline; diagnóstico e inventário reais continuam pendentes.**
Execute em PowerShell na raiz do projeto, em terminal separado da sessão do agente.
Substitua `<CAMINHO_PRIVADO>` por uma pasta local protegida, fora do projeto e de
pastas compartilhadas/sincronizadas. Não passe usuário ou senha nos comandos.

Na conferência local de 03/11: Python 3.12.15 de 64 bits, SQLAlchemy 2.1.6 e pyodbc
5.3.0 disponíveis; `ODBC Driver 18 for SQL Server` instalado. A presença do driver
não confirma qual foi autorizado para sua conexão. Não é necessário reinstalar.

Continuam sem registro público de preenchimento somente: **porta TCP, schemas
autorizados, método de autenticação, driver escolhido e confirmação de somente
leitura**. Se já os obteve, complete apenas sua cópia privada. Não envie credenciais
nem nomes físicos no chat, e não presuma porta ou schema.

| Passo | Ação | Comando | Resultado esperado |
|---|---|---|---|
| 1 | Conferir dependências Python e drivers locais; não abre conexão | `.\.venv\Scripts\python.exe -c "import sys, sqlalchemy, pyodbc; print(sys.version.split()[0]); print(sqlalchemy.__version__, pyodbc.version); print(pyodbc.drivers())"` | Python 3.12, imports disponíveis e driver autorizado instalado, compatível com a arquitetura do Python |
| 2 | Somente se faltar o ambiente/extra Python, preparar pelo lançador existente | `.\scripts\bootstrap.cmd --sqlserver` | Ambiente preparado; pular se o passo 1 já atender. O bootstrap não instala o driver do Windows; falta/incompatibilidade desse driver cabe à DSI |
| 3 | Aproveitar `dbconfig.toml` externo; se não existir, copiar manualmente `config/database.kappa.example.toml`, renomear e completar os cinco campos da seção 2 | Editor local: `notepad "<CAMINHO_PRIVADO>\dbconfig.toml"` | Arquivo com esse nome exato, caminho absoluto local, UTF-8 sem BOM; `scope_approved = true` só após confirmação concreta do escopo, da execução e de somente leitura. Credenciais somente na cópia privada quando o método exigir |
| 4 | Executar diagnóstico e interpretar o resultado antes de continuar | `.\scripts\diagnose-db.cmd --config "<CAMINHO_PRIVADO>\dbconfig.toml" --execute` | Código `0` e `result.status = "passed"` no relatório privado; registrar UUID. Se houver falha, corrigir somente a causa identificada antes de inventariar |
| 5 | Após revisar o diagnóstico bem-sucedido, executar inventário do mesmo escopo | `.\scripts\inventory-db.cmd --config "<CAMINHO_PRIVADO>\dbconfig.toml" --execute` | Novo UUID e relatório privado; código `0`, `3` ou falha conforme a seção 5. Sem extração de registros acadêmicos |
| 6 | Revisar ambos os relatórios localmente e preencher o retorno sanitizado da seção 6 | Editor local, sem copiar JSON para o chat ou Git | Retorno com data/UUID/código, categorias de erro, cobertura, limitações e somente fontes lógicas que puder identificar |

Imediatamente após cada lançador, consulte `$LASTEXITCODE` no mesmo PowerShell,
antes de executar outro programa. `--help` retorna `0` apenas pela ajuda;
chamar sem `--execute` retorna `2` e **não valida a configuração**.

Cada execução grava seu arquivo em
`<CAMINHO_PRIVADO>\vrac-discovery-private\<UUID>\diagnose.json` ou
`inventory.json`. Os UUIDs são distintos. Abra esses arquivos apenas localmente.
Falhas anteriores à gravação podem não deixar relatório nem UUID no console;
nesse caso, registre “não disponível”, sem presumir que houve consulta ao banco.

## 5. Códigos, falhas e limites

| Código | Como interpretar | Próxima ação |
|---|---|---|
| `0` | Diagnóstico `passed` ou inventário tecnicamente `valid` | Revisar o relatório; não comprova somente leitura nem completude |
| `1` | Operação falhou (`failed`) ou houve falha na saída/ferramenta/ambiente | Consultar categoria sanitizada se houver relatório; para erro de saída, conferir diretório local e permissões sem elevar privilégios |
| `2` | Execução recusada, argumentos/configuração inválidos ou confirmações pendentes | Conferir caminho absoluto externo, nome `dbconfig.toml`, formato e campos da cópia privada; sem `--execute` nenhum arquivo foi lido |
| `3` | Inventário `partial` | Revisar categorias, avisos e truncamentos; aproveitar apenas a evidência obtida, com as limitações registradas |
| `130` | Cancelamento pelo operador | Registrar interrupção; não tratar como conclusão |

No diagnóstico, revisar `result.status` e, em falha, `result.category`. No
inventário, revisar `result.status`, `result.coverage`, `result.limits` e as
categorias `objects`, `columns`, `keys`, `foreign_keys` de cada item de
`result.schemas`. Cada categoria tem `status`, `coverage`, `truncated` e
`warnings`; uma falha pode ter `error.category`. `not_executed` significa que a
consulta foi interrompida preventivamente após falha anterior, não ausência de fonte.

`truncated = true` indica corte da categoria pelo limite; chaves compostas e FKs
podem estar incompletas. Uma categoria vazia ou com omissões também pode tornar o
inventário parcial mesmo sem truncamento. **Cobertura permanece `unknown` mesmo
com estado `valid`**: metadados não visíveis continuam desconhecidos. Não inferir
inexistência, unicidade, granularidade ou relações pela ausência de linhas.

O limite padrão é 1000 linhas por categoria/schema, com até quatro consultas por
schema e oito schemas explícitos; a ferramenta busca uma linha adicional para
detectar truncamento. A inicialização do dialeto pode fazer verificações internas.
Não ampliar schemas/limites, consultar outros bancos ou executar novas consultas
para completar lacunas automaticamente. Registre o ponto específico para o DBA.

As categorias sanitizadas orientam correções pontuais:

- `dependency`/`driver`: conferir extra Python ou driver e arquitetura aprovados.
- `configuration`: corrigir somente os campos/formato/caminho da cópia privada.
- `network`: conferir endpoint/porta fornecidos e rede/VPN com a DSI, sem varredura.
- `certificate`: corrigir cadeia, validade ou correspondência de nome com DSI/DBA.
- `authentication`: conferir método e conta no ambiente privado, sem trocar por conta privilegiada.
- `permission`: DBA confere o escopo de leitura específico, sem conceder privilégios pela ferramenta.
- `timeout`/`unknown`: investigar a etapa no ambiente autorizado; a categoria não prova a causa e não justifica remover limites.

Manter `Encrypt=yes` e `TrustServerCertificate=no`. `SELECT 1`,
`ApplicationIntent=ReadOnly` e `scope_approved` não comprovam ausência de escrita:
a confirmação administrativa de somente leitura permanece necessária. Não testar
escrita, alterar firewall ou executar templates de qualidade/cardinalidade.

## 6. Modelo curto do retorno sanitizado

Preencher somente após revisar os arquivos localmente, com divulgação autorizada.
Não enviar configuração real, JSON bruto, caminhos privados, nomes físicos ou
registros individuais. Use “desconhecido”, “não executado” ou “não disponível”
quando aplicável. O modelo não contém resultados de execução real.

```text
Data/fuso da execução: <...>
Diagnóstico: UUID <...>; saída <...>; estado <...>; erro sanitizado <categoria/nenhum>.
Inventário: UUID <...>; saída <...>; estado <...>; erro sanitizado <categoria/nenhum>.
Cobertura: unknown; categorias consultadas <...>; falhas/não executadas <...>.
Truncamentos e limitações: <categoria e alcance lógico, sem nomes físicos>.
Fontes lógicas identificadas: <docente/vínculo/referência temporal/departamento/
  matrícula-aluno-curso/Horas Reais/alocação; por fonte, identificada ou desconhecida>.
Somente leitura e escopo: <confirmados ou pendentes; data e referência sanitizada>.
Revisão local/divulgação deste retorno: <data, função e referência permitida>.
```

Para preparar o material do Prompt 2, mantenha o mapa físico externo e use o
[dicionário sanitizado](SANITIZED_DATA_DICTIONARY.md) somente para conceitos,
tipos/chaves lógicos e limitações efetivamente identificados. Não invente o
mapeamento a partir dos nomes. As fórmulas já documentadas não precisam de nova
validação (D-022); lacunas técnicas afetam apenas a fonte/resultado correspondente.
**Prompt 1 real adiado para a etapa final e deploy. Não aguardar esse retorno para desenvolver na base sintética; nenhum outro prompt foi executado nesta atualização de escopo.**
