# Como conferir a prévia

A prévia local fica em <http://127.0.0.1:8501> e utiliza somente dados sintéticos.
Para iniciá-la novamente, na raiz do projeto:

```powershell
.\scripts\run-demo.cmd
```

## Conferência da tela

Em 30/10/2026, Matheus solicitou a ligação da demonstração ao PostgreSQL sintético
(D-025). Os comandos de início selecionam essa origem; a tela identifica
**PostgreSQL sintético** e carrega filtros e registros da base local. Preparação e
dependência opcional em [PostgreSQL sintético](../operations/SYNTHETIC_POSTGRES.md).
Os exemplos antigos em memória continuam disponíveis somente pela opção explícita
`.\scripts\run-demo.cmd --memory`.

1. Abrir o endereço no navegador e conferir o aviso **DEMONSTRAÇÃO — somente dados
   sintéticos, sem validade institucional**.
2. Selecionar **SINT-A** e **2026.1** e clicar em **Mostrar dados de demonstração**.
   Conferir a tabela de filtros, os registros docentes fictícios e as alocações
   fictícias por turma. Conferir **Origem: PostgreSQL sintético** na tabela de filtros.
3. Alterar o departamento ou o período. A prévia anterior deve desaparecer até
   clicar novamente no botão; os dados anteriores não representam o novo filtro.
4. Selecionar **SINT-VAZIO** e clicar novamente. Deve aparecer uma explicação de ausência
   de registros, sem apresentar zero como resultado calculado.

Os dados incluem docentes repetidos por mês/vínculo, valores ausentes, zero,
compartilhamento e atuação em outro departamento. São cenários de teste, não regras
ou números institucionais. Ainda não existem totais consolidados, gráficos das análises,
exportações ou conexão institucional pela tela.
Vagas preenchidas não são alunos únicos. A fonte consultada não fornece currículo
ou grupo de compartilhamento: esses campos ficam ausentes. Horas Reais reaparecem
nas linhas mensais; não somá-las. A unidade não é inferida nesta exibição.

## O que o Prompt 1 acrescentou

O Prompt 1 acrescenta ferramentas de diagnóstico e inventário para o desenvolvedor,
separadas da interface de Talita. A conexão PostgreSQL foi acrescentada posteriormente.
Para conferir a ajuda e os testes sem configuração real:

```powershell
.\scripts\diagnose-db.cmd --help
.\scripts\inventory-db.cmd --help
.\scripts\check.cmd
```

Sem `--execute`, os comandos de descoberta recusam a execução antes de ler a configuração.
O procedimento com banco real depende de confirmação de SGBD, escopo e privilégios com
DBA/DSI e é executado manualmente fora da sessão do agente. Consulte
[DATABASE_DISCOVERY.md](../operations/DATABASE_DISCOVERY.md). **Conexão e inventário: NÃO VALIDADOS.**

## Evidências desta revisão

O Prompt 2 acrescenta o [catálogo de definições e contratos](../ANALYSIS_CATALOG.md),
sem alterar a tela. Para conferir suas propostas offline, executar
`.\.venv\Scripts\python.exe -m vrac.analyses`. A implementação das análises na interface
permanece para uma solicitação de fase 3, com regras e branding validados.

Em 27/10/2026, a prévia foi iniciada e o endpoint local `/_stcore/health` respondeu
HTTP 200. Os testes automatizados da interface já cobrem os cenários acima; a suíte
da fase 1 registrou 117 testes aprovados e uma integração real excluída.

A verificação visual pelo Computer Use foi interrompida pela ferramenta: a aplicação
da política de URLs ainda não é suportada no navegador Windows atual. Por isso, não
há aceite visual automatizado ou avaliação de usabilidade por Talita nesta entrega.
