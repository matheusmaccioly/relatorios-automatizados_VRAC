# Prompt 5 · modos de conferência sintéticos

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
| Exportações | CSV/PNG/ZIP existentes, com testes offline de filtros, referência e proteção de fórmulas. XLSX e SVG não foram identificados; exportação da decisão e do resultado E01 não foi implementada. Conferência de todos os arquivos e formatos para aceite permanece pendente. |
| Feedback e armazenamento operacional | Não há formulário, persistência ou backlog alimentado por feedback neste incremento. SQLite, retenção e backup dependem de Q-008; nenhuma base operacional foi criada. Categorias, aviso de dados pessoais e associação à execução permanecem pendentes. |
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
