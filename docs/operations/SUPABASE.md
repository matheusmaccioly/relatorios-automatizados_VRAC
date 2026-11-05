# Supabase · demonstração sintética e acesso

Entrega de 05/11/2026, solicitada por Matheus (D-035). A aplicação continua no
monólito Python/Streamlit. Supabase fornece PostgreSQL e Auth; o processo Python
permanece no ambiente de execução da aplicação. Não houve publicação.

## O que foi migrado

| Item | Resultado conferido |
|---|---|
| Schema original `vrac_sintetico` | Exportado da origem local identificada como sintética, sem copiar usuários/senhas/roles da origem |
| Tabelas e dados originais | 16 tabelas, 3.926 linhas; contagem e hash de conteúdo por tabela iguais no destino |
| Recortes | Quatro departamentos, seis períodos; sem criar relações de centro ausentes |
| Projeções em `vrac_app` | 3.176 linhas dos contratos já usados por R01–R06; contagens conciliadas |
| Metadados | Marcador sintético, versão, semente, períodos e política de simulação preservados |
| Histórico de migrações | Duas migrações SQL registradas em `supabase_migrations.schema_migrations` |
| Primeiro acesso | Conta criada por Matheus, liberada para quatro departamentos; ele confirmou login e cálculo |

A exportação usa `pg_export_snapshot()` e o mesmo snapshot para schema/dados e
projeções. `pg_dump` usa a conta local de leitura, TLS `verify-full` e o passfile
externo existente, sem exibir credenciais. O pacote de transferência foi gerado em
uma pasta temporária externa ao workspace. Não foi lido pelo modelo nem incluído
no Git; o operador deve preservar uma cópia em armazenamento aprovado antes que
a pasta temporária seja eliminada pelo sistema. A origem local foi preservada.

O schema original não é exposto à aplicação. Projeções mantêm linhas e campos dos
contratos existentes, incluindo duplicidades, zero, nulo, datas e texto de matrícula.
O ordinal técnico preserva linhas repetidas; não representa uma chave institucional.
Não houve mudança de fórmula, deduplicação ou agregação para transferir dados.

## Executar

```powershell
.\scripts\bootstrap.cmd --postgres
.\scripts\run-demo.cmd
```

O SDK Supabase `2.34.0` é dependência principal, fixado em `uv.lock`: o Streamlit
Community Cloud instala pelo lock, sem extras.
O extra PostgreSQL é útil para manutenção/conferência da origem; a aplicação
com Supabase não exige PostgreSQL local nem senha de banco. O launcher usa
`127.0.0.1:8501`. Nesta entrega há uma instância local em
[127.0.0.1:8527](http://127.0.0.1:8527).

`run-demo.cmd --postgres` usa a origem local anterior; `--memory` usa a fixture
offline explicitamente. Não há troca de fonte em caso de falha. Na alternativa
PowerShell autorizada: `run-demo.ps1 -Source supabase`. Não alterar ExecutionPolicy;
para a CLI no PowerShell bloqueado, usar `npx.cmd`.

O arquivo `config/supabase.public.toml` contém somente URL e chave publicável.
Pode ser substituído pelas variáveis **públicas** `VRAC_SUPABASE_URL` e
`VRAC_SUPABASE_PUBLISHABLE_KEY`. O loader rejeita HTTP, destinos externos ao
Supabase hospedado e chaves administrativas. Não carrega `.env` nem `secrets.toml`.
Modo `real` permanece bloqueado; a sinalização de dados sintéticos foi preservada.

## Contas e autorização

1. O responsável cria a conta em **Authentication → Users → Add user → Create new user**,
   mantém a senha privada e registra o UUID. A aplicação não oferece cadastro nem envia convites.
2. A liberação administrativa é explícita. Para os quatro departamentos desta demonstração:

   ```powershell
   npx.cmd --yes supabase@3.0.0 login
   .\.venv\Scripts\python.exe -m vrac.dev.supabase_migration grant --user-id UUID_DO_USUARIO
   ```

3. Para restringir uma conta, o operador autorizado altera apenas suas liberações
   em `vrac_app.access_grants`, pelo painel SQL/Table Editor. A aplicação não possui
   ferramenta para elevar acesso, editar fontes ou administrar contas.

RLS consulta as liberações do próprio `auth.uid()`, rejeita Auth anônimo e exige
sessão existente/não vencida em `auth.sessions`. O schema original e o histórico
de migrações não têm acesso para `anon`/`authenticated`. As tabelas da aplicação
têm somente SELECT para usuários autenticados e RLS obrigatório. As RPCs são
`SECURITY INVOKER`; o helper de sessão tem acesso privilegiado somente à consulta
da sessão do próprio usuário, sem parâmetros e com `search_path` vazio.

O cliente Auth usa HTTPS com certificado validado, não usa `service_role` e não
persiste tokens em disco. Cada sessão Streamlit guarda seu próprio cliente/JWT.
A cada rerun, `get_user` e as liberações são consultados novamente. Mudança de
escopo, troca de conta ou logout elimina resultados, arquivos, widgets e feedback
da sessão. Ao fechar/recarregar a conexão do navegador pode ser necessário novo login.

Configurações aplicadas e conferidas: e-mail/senha habilitados, cadastro público e
Auth anônimo desabilitados, JWT de 900 s e mínimo de 12 caracteres para novas senhas.
Somente três propriedades diferiam e foram atualizadas; configurações remotas não
declaradas no arquivo foram preservadas. Não foi configurado SSO institucional.

No Supabase, **Baixar** prepara o arquivo após validar a sessão; **Salvar arquivo
preparado** faz o download no navegador. Limite de 25 MiB por arquivo. O link contém
os bytes, sem JWT e sem endpoint público de mídia. Arquivos já recebidos/baixados
pelo usuário permanecem sob sua guarda; logout não apaga cópias no navegador.

## Manutenção e conferência explícita

Usar CLI fixada em `3.0.0`; nela `--remote` seleciona explicitamente o destino.
Os comandos administrativos abaixo são separados dos testes offline:

```powershell
.\.venv\Scripts\python.exe -m vrac.dev.supabase_migration prepare
.\.venv\Scripts\python.exe -m vrac.dev.supabase_migration verify --bundle CAMINHO_EXTERNO_RETORNADO
.\.venv\Scripts\python.exe -m vrac.dev.supabase_migration rls-check
```

`prepare` apenas exporta a base local sintética, com conta de leitura e TLS.
`apply --bundle ...` aplica o pacote **somente em destino sem os schemas VRAC**,
em transação única: colisões falham sem apagar/sobrescrever objetos existentes.
Não reaplicar sobre o projeto já migrado. A aplicação não executa migrações em startup.
Os nomes/tipos institucionais e a receita local privada não são usados pelo novo leitor.

O pacote externo desta execução foi
`C:\Users\MATHEU~1\AppData\Local\Temp\vrac-supabase-transfer-zg3njphx`.
O manifesto e a conferência estão nessa pasta; não armazenar seu conteúdo no Git.

O teste SQL transacional cria identidade/sessão/linhas inteiramente fictícias,
testa isolamento, acesso sem permissão, distinção zero/nulo, negação de escrita
e perda de acesso após revogação. Ao final faz `ROLLBACK`, sem usuários/linhas de
teste permanentes ou mensagens de e-mail. A suíte pytest continua sem rede.

O comando `migration repair` ficou aguardando conexão direta e foi interrompido.
As migrações aplicadas foram registradas pela Management API, com o formato
verificado no [código oficial da CLI 3.0.0](https://github.com/supabase/cli/blob/v3.0.0/apps/cli/src/command-internal/migration-history.ts).
Não houve alteração de TLS, firewall ou de permissões da máquina para isso.

## Limites e validações restantes

- A base é um **snapshot**, sem replicação ou sincronização automática da origem.
  Mudanças posteriores exigem novo incremento de carga revisado. O script inicial
  não é uma rotina de atualização e não apaga os schemas existentes.
- A validação humana registrada cobre login e um cálculo, conforme confirmação
  de Matheus. Não equivale a conferir todas as análises/exportações, teclado,
  leitor de tela, múltiplos navegadores, recuperação de senha ou sessão longa.
- E01, que usa identidade local simulada e nova consulta ao PostgreSQL local,
  fica indisponível no Supabase. As dez conferências sobre o snapshot continuam.
- Feedback permanece temporário na sessão. Supabase não foi adotado como
  armazenamento operacional de feedback, e retenção/backup continuam pendentes.
- DSI/DBA validam fontes reais, escopos e operação antes da etapa institucional;
  Talita valida uso e exportações; Matheus/responsável institucional revisam a
  identidade visual. Não há homologação nem uso de dados institucionais inferido.
- Publicar o processo Streamlit no ambiente existente continua tarefa própria.
  Não foram provisionados serviços adicionais nem configurado hosting de frontend.

Referências consultadas: [Auth por senha](https://supabase.com/docs/guides/auth/passwords),
[RLS](https://supabase.com/docs/guides/database/postgres/row-level-security),
[mudanças da CLI v3](https://supabase.com/changelog/supabase-cli-v3) e
[runtime de Edge Functions](https://supabase.com/docs/guides/functions).
