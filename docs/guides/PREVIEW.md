# Como conferir a prévia

A prévia local fica em <http://127.0.0.1:8501> e utiliza somente dados sintéticos.
Para iniciá-la novamente, na raiz do projeto:

```powershell
.\scripts\run-demo.cmd
```

## Conferência da tela

1. Abrir o endereço no navegador e conferir o aviso **DEMONSTRAÇÃO — somente dados
   sintéticos, sem validade institucional**.
2. Selecionar **SINT-A** e **2026.1** e clicar em **Mostrar dados de demonstração**.
   Conferir a tabela de filtros, os registros docentes fictícios e as alocações
   fictícias por turma e currículo.
3. Alterar o departamento ou o período. A prévia anterior deve desaparecer até
   clicar novamente no botão; os dados anteriores não representam o novo filtro.
4. Selecionar **2026.2** e clicar novamente. Deve aparecer uma explicação de ausência
   de registros, sem apresentar zero como resultado calculado.

Os dados incluem docentes repetidos por mês/vínculo, valores ausentes, zero,
compartilhamento e atuação em outro departamento. São cenários de teste, não regras
ou números institucionais. Não há conexão institucional pela tela.

## Conferência da composição docente

A seção **Análises disponíveis · composição docente** fica abaixo da fixture. Nenhum
número dela tem validade institucional: a definição da contagem continua pendente.

1. Manter **SINT-A** e **2026.1**. Conferir o aviso de que a regra não está aprovada,
   com as pendências nomeadas.
2. Com a regra **Pessoas distintas presentes em qualquer mês do período**, clicar em
   **Calcular composição docente**. O total deve ser **2 pessoas**, com resultado
   **parcial**, filtros efetivos, origem, versões e avisos.
3. Trocar para **Matrículas funcionais na última referência de cada vínculo** e calcular
   de novo. O total deve ser **3 matrículas funcionais** no mesmo recorte. A diferença é
   a decisão que precisa ser tomada, não um erro.
4. Escolher a distribuição **Categoria do vínculo**. As parcelas somam 3 e o total é 2:
   conferir o aviso de que a mesma pessoa aparece em mais de uma categoria e que as
   parcelas não são partes exclusivas.
5. Escolher a distribuição **Quadro**. A fixture não informa quadro: conferir que tudo
   aparece em **Sem classificação na dimensão**, sem inferência e sem sair do total.
6. Voltar à regra **Pessoas distintas, foto em uma data** e comparar **01/03/2026** com
   **01/04/2026**. O total deve mudar de 2 para 1, porque a foto depende da data.
7. Selecionar **2026.2** e calcular. Deve aparecer o estado `vazio`, com a situação
   **Sem registros** e célula sem valor — nunca zero.
8. Trocar qualquer filtro depois de um cálculo. O resultado anterior deve desaparecer,
   para que nenhum número seja lido fora do seu recorte.
9. Baixar o CSV e o JSON e conferir que cada linha repete recorte, versões e avisos.

Para ver o bloqueio do modo real, em uma sessão separada, use o comando da seção
**Configuração e limites** do README. A tela deve recusar antes de carregar qualquer
dado, sem exibir a seção de análises.

## O que o Prompt 1 acrescentou

O Prompt 1 acrescenta ferramentas de diagnóstico e inventário para o desenvolvedor,
separadas da interface de Talita. A tela continua a demonstração da fundação.
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
