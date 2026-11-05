# Prompt 5 · modos de conferência sintéticos

## Conferência do pacote e do feedback — 04/11/2026

O manifesto do ZIP agora identifica também R01 em `additional_analyses`, com
situação e, quando disponível, origem, versão e snapshot do cadastro. Antes, os
arquivos R01 podiam estar no pacote sem sua identificação na lista do manifesto.
As demais análises continuam em `analyses`; o contexto compartilhado registra
os filtros e a execução. A conferência automatizada do pacote produzido pela tela
usou uma seleção de quadro e período: comparou todas as linhas das tabelas dos
roteiros com os resultados calculados, referência e quadro com a seleção, snapshot
R01 com seu CSV, e execução, unidade e avisos nos metadados de um PNG.

Foram exercitados feedback nas duas telas, vínculo por execução, rerun, novo
cálculo e mudança de filtros. Os registros anteriores continuam na sessão com a
execução original; uma nova submissão é vinculada ao novo cálculo. As quatro
categorias, a proteção do CSV e a exigência de comentário foram verificadas com
dados sintéticos. O formulário alerta contra dados pessoais e acadêmicos, mas não
consegue garantir a sanitização do texto. O CSV e os registros em sessão continuam
temporários, sem persistência ou compartilhamento operacional. O time precisa
definir persistência, retenção, proteção, backup e integração ao backlog (Q-008).

Esta conferência é offline, com fonte sintética em memória. Não substitui uso de
Talita nem verifica PostgreSQL ou fontes institucionais. PNG pode ocultar metadados
em visualizadores comuns; o CSV e o manifesto são as referências para o contexto.
A suíte completa foi interrompida após lentidão e uma falha ainda não diagnosticada;
a bateria específica de seis testes passou, e o teste docente ampliado passou em
execução isolada. Resultados e comandos estão em [STATUS](../STATUS.md).

## Arquivos e feedback — incremento de 04/11/2026

Em **Análise docente** ou **Análises por período**, calcule um resultado e abra
**Registrar feedback desta execução**. Escolha útil, divergência, dificuldade ou
sugestão. Para útil o comentário é opcional; para as demais categorias, descreva
o ponto sem nomes, matrículas, valores ou outros dados pessoais/acadêmicos. O aviso
não consegue garantir que o texto esteja sanitizado: revise antes de encaminhá-lo.
O registro contém apenas identificador aleatório da execução, análise, situação,
datas, categoria e comentário; não copia filtros nem registros acadêmicos.

Registros acumulam apenas na sessão e podem ser baixados em CSV; não são enviados
automaticamente. O CSV é um meio manual provisório, não um backlog compartilhado;
quem baixa precisa protegê-lo e decidir seu encaminhamento. O time ainda não
definiu armazenamento, retenção, proteção e backup (Q-008, informado por Matheus
em 04/11). Ao encerrar a sessão, registros não baixados são perdidos. A solução
operacional definitiva e a incorporação ao backlog dependem dessa decisão; não foi
adotado SQLite nem feita escrita na origem sintética ou institucional.

Os downloads preservam CSV/PNG/ZIP existentes. CSV e manifesto incluem centro,
departamentos efetivos, filtros, execução e horários conhecidos; cada CSV também
informa unidade, situação, origem, versão, snapshot e avisos correspondentes.
O CSV das conferências passa pelo mesmo tratamento contra fórmulas. Números
negativos permanecem numéricos em CSV e valores preservam a precisão do cálculo;
a interface pode abreviar sua apresentação. Textos potencialmente interpretados
como fórmula recebem prefixo de proteção, e CSV usa UTF-8 com BOM. O PNG conserva
unidade e referência no desenho e contém contexto, execução, datas e avisos nos
metadados: visualizadores comuns podem não exibir esses metadados, portanto use o
CSV/manifesto para consultar o conjunto completo. Na tela docente, o horário de
extração não é registrado e assim é informado; não é deduzido do cálculo.

Os testes usam fixtures sintéticas em memória, incluindo leitura do CSV, do ZIP e
dos metadados PNG, acentos, proteção de fórmulas, precisão, categorias, vínculo,
rerun e troca de filtros. Não foi realizada leitura do PostgreSQL sintético nesta
sessão; ela permanece uma conferência separada pelo desenvolvedor. Nenhum teste
sintético valida fontes institucionais. Avaliação de Talita dos textos, arquivos e
utilidade, e revisão visual institucional continuam pendentes.

Incremento local de 03/11/2026. As dez conferências C01–C10 leem o snapshot já
carregado e não executam consulta de aprofundamento. A E01 v1 é um experimento
desabilitado por padrão: conta alocações sem classificação nos departamentos e
semestre selecionados. Não identifica TCC, não interpreta produtividade e não
representa regra institucional. O recorte considera todas as alocações desses
departamentos e semestre, independentemente de quadro ou categoria; os demais
filtros continuam vinculados à autorização. Zero alunos e variação por limiar não
foram habilitados como novas regras institucionais (Q-006 e Q-009).

Na tela **Análises por período**, carregue a origem PostgreSQL sintética, calcule
R04 ou todos os roteiros e abra **Pontos para conferência adicionais**. Habilite
E01 explicitamente. Em **Sob aprovação**, autorize e depois execute, ou recuse; em
**Automático**, a habilitação inicia a consulta. A recusa, a falha e a ausência de
aplicabilidade mantêm as análises básicas. O estado e o resultado ficam na sessão;
alterar seleção, filtros, departamentos, versão, referência ou identidade descarta
a autorização, inclusive se a seleção anterior for retomada. Atualizar a origem
também reinicia a sessão da conferência. Uma falha exige atualizar os dados antes
de tentar de novo. A identidade é uma constante simulada, restrita pelo mesmo
controle de modo sintético local da demonstração; não é autenticação institucional.

O catálogo do aprofundamento é fechado e versionado; C01–C10 permanecem funções
fechadas anteriores, sem os metadados completos de catálogo previstos no Prompt 5.
A E01 reutiliza a consulta revisada
`academic_allocations.sql`, com parâmetro vinculado de departamento; o semestre é
validado e aplicado aos registros retornados. Antes da releitura, a aplicação refaz
o snapshot na mesma transação `REPEATABLE READ` e compara a referência completa;
divergência ou fonte indisponível interrompe a verificação. Há limite de uma
verificação, cinco departamentos, 5.000 alocações e no máximo 61 comandos de
leitura por tentativa, incluindo revalidação; cada comando tem timeout de 5 s e
a conexão, 3 s. Não há prazo global de 5 s para o conjunto. Nenhum resultado é
reexecutado no rerun para a mesma sessão e referência. A comparação de hash não
transforma a origem em histórico versionado.

## Abrangência e pendências do Prompt 5

| Critério | Evidência e limite |
|---|---|
| Modos, autorização, estados e limites | Implementados para E01 experimental; testes offline e interface simulada. Conferência no PostgreSQL sintético ainda pendente. C01–C10 ainda não têm todos os metadados do catálogo previsto no guia. |
| Pontos descritivos | E01 apresenta motivo, contagem e limitação. C01–C10 apresentam motivo, ocorrências e tratamento sobre o snapshot. |
| Exportações | CSV/PNG/ZIP conferidos offline conforme incremento acima. XLSX/SVG não foram criados; exportação da decisão e resultado E01 não foi implementada. Conferência humana e na origem PostgreSQL sintética permanecem pendentes. |
| Feedback e armazenamento operacional | Formulário e CSV temporário associados à execução disponíveis; não há persistência ou backlog compartilhado. Armazenamento, retenção e backup dependem de Q-008. |
| Aceite humano | Demonstração, avaliação de Talita e registro de feedback sanitizado pendentes. Não há confirmação institucional nem validação visual. |

O Prompt 4b tem testes e conciliação offline, mas sua execução no PostgreSQL
sintético e confirmação de Matheus seguem pendentes. Essa dependência afeta a
confiança na carga analisada, não o controle de autorização da E01. D-022 e D-027
seguem aplicáveis, sem nova aprovação geral das fórmulas.

Para conferência manual pelo desenvolvedor, com o PostgreSQL sintético existente,
configuração e certificados já preparados:

```powershell
.\scripts\run-demo.cmd
```

Confirme a origem exibida; execute os dois modos, inclusive recusa, troca de filtro,
recarga, falha e rerun, e verifique que análises básicas permanecem disponíveis.
Se a origem ou o certificado não estiver disponível, registre a falha: não ativar
fallback, ler segredos, modificar TLS ou acessar base institucional. Para a
conciliação 4b, use o comando de [Prompt 4b](PROMPT4B_CARGA.md). A conferência
sintética não valida fontes, permissões ou resultados reais.
