# PoC de análises acadêmicas da VRAC

Fundação de uma aplicação interna para apoiar Talita na preparação de análises de
docentes, matrículas e carga horária. **Fase 0: demonstração local exclusivamente sintética.**
O aplicativo funciona sem LLM e sem Power BI; nenhuma conexão institucional está implementada.

O [guia original](Guia_Desenvolvimento_VRAC_Codex.md) foi preservado. As instruções
permanentes estão em [AGENTS.md](AGENTS.md) e o plano em [docs/PLAN.md](docs/PLAN.md).

## Preparar no Windows

PowerShell 5.1 ou superior, Windows x64/ARM64 e acesso HTTPS aos distribuidores oficiais
são necessários para a primeira instalação. Não é necessário Python previamente instalado.

```powershell
.\scripts\bootstrap.cmd
.\scripts\check.cmd
.\scripts\run-demo.cmd
```

O bootstrap instala ferramentas apenas em `.tools/`, dependências em `.venv/` e cache
em `.cache/`, sem mudar o PATH ou o perfil do usuário. O `uv.lock` fixa as dependências
transitivas; `uv sync --locked` rejeita divergências. Após instalar, os testes funcionam
offline. Os comandos `.cmd` funcionam sem executar arquivos `.ps1`; esse Windows bloqueia
scripts PowerShell. As alternativas `.ps1` ficam disponíveis para ambientes que já autorizem
sua execução. Nenhum comando altera a política de execução ou desativa TLS. Se a política
institucional impedir downloads ou comandos batch, solicitar a forma aprovada pela DSI.

A demonstração fica em <http://127.0.0.1:8501>; `Ctrl+C` encerra o processo.
Use `SINT-A / 2026.1` para os exemplos e `2026.2` para o caso sem registros.
Trocar um filtro remove a prévia anterior até clicar novamente em **Mostrar dados de demonstração**.
Não existem cálculos institucionais, exportações ou login simulado nesta fase.

## Configuração e limites

Somente `VRAC_ENVIRONMENT` (`development`, `test`, `production`) e `VRAC_DATA_MODE`
(`synthetic`, `real`) são lidas. O padrão é `development` + `synthetic`.
`run-demo.cmd` e `run-demo.ps1` selecionam explicitamente esses valores para iniciar a demonstração local.
O exemplo [config/settings.example.toml](config/settings.example.toml) é documental,
sem leitura automática de arquivos. Modo real é negado antes de carregar dados;
configuração inválida gera erro e nunca ativa uma demonstração como alternativa.

Para verificar o bloqueio manualmente, em uma sessão separada:

```powershell
$env:VRAC_ENVIRONMENT = 'development'
$env:VRAC_DATA_MODE = 'real'
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Não colocar credenciais ou dados institucionais no workspace, `.env`, chat ou Git.
Arquivos de ignore evitam versionamento/acondicionamento acidental; não impedem a leitura
pelo agente. Fontes, regras, acesso real e publicação dependem das validações descritas
em [docs/DSI_REQUESTS.md](docs/DSI_REQUESTS.md).

## Desenvolvimento e continuidade

O pacote em `src/vrac/` separa configuração, autorização, dados fictícios e interface.
As camadas de SQL, cálculos, verificações, gráficos e exportação serão adicionadas
nos incrementos correspondentes, sem gerar implementações vazias agora.

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\python.exe -m pytest
```

Consulte [docs/STATUS.md](docs/STATUS.md) para verificações efetivamente executadas,
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) para a arquitetura e
[docs/PLAN.md](docs/PLAN.md) para os próximos incrementos. Repositório privado/autorizado,
infraestrutura do servidor e login institucional ainda precisam de confirmação humana.
Não há CI externa configurada ou publicação automática.
