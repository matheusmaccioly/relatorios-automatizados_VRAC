# Configurar o KAPPA — passo a passo para Matheus

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

## 4. Testar depois de preencher

Execute você mesmo em um terminal na raiz do projeto, fora da sessão do agente:

```powershell
.\scripts\bootstrap.cmd --sqlserver
```

Depois substitua **somente o caminho** abaixo pelo caminho absoluto da sua cópia
privada. Não coloque usuário ou senha no comando:

```powershell
.\scripts\diagnose-db.cmd --config "C:\PASTA_PRIVADA_APROVADA\dbconfig.toml" --execute
```

O caminho é ilustrativo; a pasta precisa existir, ser local e estar protegida.
O extra Python não instala o driver ODBC do Windows. Se houver erro de driver ou
certificado, peça o ajuste à DSI/DBA sem desabilitar TLS ou validação do certificado.

Sucesso nesse diagnóstico verifica a conexão naquele momento; não ativa dados reais
na demonstração. O inventário é um passo separado, descrito no
[roteiro técnico](DATABASE_DISCOVERY.md#executar-diagnóstico-e-inventário), após
confirmar o escopo. Não compartilhe a configuração preenchida ou saídas privadas.
