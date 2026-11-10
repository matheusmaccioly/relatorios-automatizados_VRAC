# Origens dos dados e publicação da PoC

A navegação por áreas da `main` é compartilhada pelas duas origens. Em Supabase,
use **Origem dos dados** antes de entrar ou durante a sessão:

| Origem | Conteúdo | Acesso |
| --- | --- | --- |
| Institucional pseudonimizada · professores | Fontes docentes autorizadas | Conta autenticada e permissão institucional por departamento |
| Demonstração sintética | Exemplos determinísticos de demonstração | Conta autenticada e permissão própria da demonstração |

A troca de origem limpa resultados, arquivos gerados e comentários da sessão.
Uma falha institucional nunca ativa exemplos sintéticos. CSV, PNG, ZIP e PDF
identificam a origem. Não se misturam origens no mesmo pacote.

No início, escolha uma análise e departamento em **Comece rápido**, ou abra
**Docentes**. O relatório completo mantém como bloqueadas as análises sem fonte:
a carga docente não fornece matrículas de alunos para R06. Campos ausentes,
limitações do histórico e regras ainda pendentes aparecem junto aos resultados.
Pseudonimização não transforma estes dados em dados sintéticos nem em dados públicos.

## Execução local

```powershell
$env:VRAC_DEMO_SOURCE = 'supabase'
$env:VRAC_DATA_MODE = 'pseudonymized'
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8530
```

Para exemplos locais, use `VRAC_DEMO_SOURCE=memory` e `VRAC_DATA_MODE=synthetic`.
Não é necessário incluir CSVs ou credenciais no repositório para consultar as
fontes já carregadas. O aplicativo usa a configuração pública e a sessão do usuário.

## Verificação e publicação

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=.cache/pytest-publicacao
.\.venv\Scripts\python.exe -m ruff check src tests app.py
.\.venv\Scripts\python.exe -m ruff format --check src tests app.py
```

Use uma pasta temporária nova quando houver restrições de permissão no Windows.
Os testes padrão são offline, com exemplos fictícios e rede bloqueada.
Testes SQL de autorização são separados e exigem execução autorizada.

A publicação existente usa `main` e `app.py` no Streamlit Community Cloud.
Após um envio autorizado, conferir a reconstrução da aplicação, a presença do
seletor e o login. Em uma sessão autorizada, selecionar a origem institucional,
conferir Docentes e as exportações, depois alternar para a demonstração.
Nenhum CSV, material de origem, registro individual ou script pontual de concessão
de acesso deve integrar o commit público. As migrações versionadas descrevem o
schema; publicar o código não deve executar novamente a importação.

Matheus e Talita ainda devem validar os resultados contra as fontes aprovadas;
DSI/DBA validam acesso, retenção e operação. Publicação não significa homologação
analítica ou visual.
