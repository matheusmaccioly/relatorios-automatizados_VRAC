# Usar as análises acadêmicas da demonstração

Atualizado em 30/10/2026. Os seis roteiros documentados estão disponíveis com
dados inteiramente fictícios. A aplicação funciona com regras programadas, sem
LLM ou geração dinâmica de consultas. Nenhum resultado tem validade institucional.

## Abrir e calcular

1. Abrir <http://127.0.0.1:8501> e conferir o aviso de demonstração e a origem
   **PostgreSQL sintético**.
2. A aba **Situação geral do departamento** mantém a consulta ao cadastro atual.
   Escolher o departamento, os filtros docentes e **Calcular resultados**.
3. Para executar todos os roteiros, abrir **Análises por período**. Manter
   **Todos os roteiros (R01–R06)** ou escolher um roteiro individual da R02 à R06.
4. Escolher um departamento ou **Todos os departamentos** e clicar em
   **Carregar ou atualizar dados**.
5. Escolher os filtros e clicar em **Calcular análises selecionadas**.
6. Conferir a tabela de filtros, os resultados por aba, os avisos e as tabelas
   equivalentes aos gráficos. Usar os botões de CSV, PNG ou pacote ZIP.

Alterar um filtro remove os resultados anteriores. **Atualizar dados** consulta
novamente a base; as análises usam o snapshot identificado na tela. Se a origem
falhar, os resultados anteriores são removidos. A aplicação não muda de origem
para esconder uma falha. `SINT-VAZIO` demonstra o caso sem registros.

## Filtros

| Filtro | Efeito |
|---|---|
| Departamento | Unidade atual na R01/R02 e funções; histórica na R03; do semestre nas cargas; do curso nas séries acadêmicas |
| Semestre inicial/final | Intervalo da presença histórica, eventos de função e séries acadêmicas |
| Semestre da carga horária | Referência única da R04, sem escolher um máximo diferente para cada professor |
| Quadros docentes | Séries exibidas na R03, preservando o total geral; população na R01/R04/R05 |
| Categoria funcional | Recorte docente na R01/R02/R03/R04/R05 |
| Quadros do grupo QP simulado | Define somente o grupo comparado, sem reduzir o denominador geral |
| Cursos | Filtra os códigos selecionados e mantém o detalhamento separado por curso |
| Habilitação, turno, nível e forma de ingresso | Aplicados às populações próprias de cada série acadêmica |

A R01/R02 usa cadastro atual; o intervalo não transforma o cadastro em foto
histórica. Situação e dupla função podem ser filtradas na tela própria da R01.
Os filtros efetivos acompanham os arquivos exportados.

## O que cada roteiro calcula

| Roteiro | Resultados e regra principal |
|---|---|
| R01 — situação geral | Matrículas funcionais distintas no cadastro, distribuição por quadro, linhas por categoria e lista de conferência, conforme os visuais do painel |
| R02 — geral e QP | Geral, grupo selecionado, classificação ausente, demais e participação. O grupo QP é uma simulação configurável, pois a composição institucional não consta dos materiais |
| R03 — histórico docente | Pessoas distintas na união das competências do semestre; séries por quadro, detalhe mensal e cobertura. Não soma meses para contar pessoas |
| R04 — carga horária | Horas Reais da fonte dedicada, carga contratada, distribuições, indicador literal do painel e alocações em tabela separada. Diferença/razão somente com unidades compatíveis declaradas na simulação |
| R05 — funções | Dupla função cadastral, registros de função, vínculos com evidência administrativa e sobreposição de vigências. Essas evidências não são equivalentes |
| R06 — evolução acadêmica | Matriculados MT/MC, bolsistas matriculados, formados FR/TD e ingressantes, por período e curso, com variação entre períodos sem percentual quando a base é zero |

Na R03, o calendário do painel inclui janeiro a julho no primeiro semestre e
agosto a dezembro no segundo. A população usa situação A, lotes 3/4/7, exclusão A4
e os seis quadros históricos documentados. Mudança de cargo não é contratação.
Uma pessoa pode participar de dois quadros no mesmo semestre: as séries não são
somadas para obter o total. A identidade da pessoa não é exibida.

Na R06, as regras são as medidas B-M-035, B-M-038, B-M-036 e B-M-070, respectivamente.
O ingresso futuro é excluído da população de matriculados. Bolsas repetidas não
multiplicam bolsistas. O evento de formado vem do cadastro e de seu menor período
FR/TD; HF não foi acrescentado. Ingressantes preservam a exceção documentada de
dupla diplomação. Nenhuma renomeação de curso foi transformada em equivalência.

## Ler ausências e simulações

- **Ausente** é diferente de zero. Um período sem observações mantém lacunas nas
  curvas. Zero aparece quando há observação com contagem elegível igual a zero.
- **Parcial** identifica cobertura incompleta ou uma métrica indisponível. Uma
  fonte de bolsas indisponível não bloqueia as outras séries.
- **Grupo QP simulado** utiliza somente a seleção exibida e exportada. O exemplo
  inicial não define uma equivalência institucional entre nomes de quadro.
- As unidades comparáveis de carga e as comprovações administrativas adicionais
  foram criadas explicitamente para a simulação. Não confirmam a unidade ou a
  natureza administrativa dos dados institucionais.
- Horas Reais não são substituídas por horas de disciplinas. As linhas mensais da
  aba de registros podem repetir o valor semestral e não devem ser somadas.
- Vagas preenchidas não são alunos únicos. Currículo e grupo de compartilhamento
  ausentes não são inventados; o indicador de compartilhamento da fonte é exibido
  separadamente no detalhamento da R04.
- O semáforo reproduz o texto do painel. Não é avaliação de produtividade,
  suficiência de pessoal ou recomendação de contratação.

## Conferências e arquivos

**Qualidade e cobertura dos dados** contém dez conferências programadas, com
contagens de chaves ausentes, múltiplos lotes, registros acadêmicos repetidos,
classificação ausente, cargas nulas/negativas e vigências inválidas. Elas descrevem
o snapshot e não são aprovações institucionais. Fonte indisponível não é exibida
como zero ocorrências.

Cada CSV usa UTF-8, separador `;`, identificação de demonstração, filtros, origem,
unidades, avisos, horário e hash do snapshot. Textos que poderiam virar fórmulas
ao abrir em planilha são protegidos. O ZIP reúne CSVs, gráficos PNG, conferências,
manifesto JSON e instruções. Os arquivos são gerados em memória, sem salvar dados
acadêmicos de usuários no servidor. A R01 mantém a referência própria de cadastro
atual no pacote completo.

Os gráficos usam as fontes locais e cores dos tokens de identidade existentes.
Revisão de identidade visual e avaliação de uso por Talita continuam pendentes;
não foi declarada homologação visual ou institucional.

## Preparação e limites de operação

Na instalação já preparada, iniciar o banco e a aplicação:

```powershell
.\.venv\Scripts\python.exe -m vrac.dev.postgres_runtime start
.\scripts\run-demo.cmd
```

Ao preparar novamente a carga, instalar também as projeções dos roteiros:

```powershell
.\.venv\Scripts\python.exe scripts/connect-synthetic-app.local.py
.\.venv\Scripts\python.exe scripts/prepare-academic-analyses.local.py
```

Os scripts de mapeamento são locais e ignorados por Git/Docker. O segundo cria
sete views analíticas e dois conjuntos suplementares: convenções de unidade e
quinze atos/vigências fictícios. A carga original das 13 fontes é preservada.
As execuções são repetíveis sem duplicar os atos. Nenhum valor financeiro é lido
para as análises.

O guia [PostgreSQL sintético](../operations/SYNTHETIC_POSTGRES.md) descreve o cluster,
TLS, conta de leitura e dependências. O modo real continua bloqueado. Integração
institucional, autenticação, hospedagem, operação e publicação dependem da DSI/DBA
e não foram substituídas por uma simulação de login. Nenhuma publicação foi feita.
