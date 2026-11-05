# Revisão final e feedback · demonstração sintética

Revisão de 04/11/2026 dos registros dos Prompts 3, 4a, 4b e 5, do catálogo e
das implementações e testes existentes. Não há feedback individual novo de
Talita identificado nesses registros: as indicações específicas de Matheus,
correções e limitações registradas são tratadas abaixo. Comentários genéricos
não foram convertidos em novos requisitos. Os dados e as expectativas exercitados
são sintéticos; D-022 e D-027 orientam a reprodução das regras documentadas.

## Classificação e encaminhamento

| Item e classificação | Situação e impacto | Encaminhamento |
|---|---|---|
| R05: fonte de vigências indisponível — qualidade da fonte / usabilidade | A comparação podia dizer “sem evidência” e simultaneidade podia aparecer como calculada apesar da falha. | Corrigido: valores afetados ausentes, estados e aviso explícitos; demais resultados preservados. Critério: fonte consultada e vazia continua produzindo zero e “sem evidência”; fonte indisponível não. Matheus pode revisar a apresentação. |
| R02: unidade do PNG departamental — usabilidade | A tabela também contém percentuais, mas o gráfico mostra apenas contagens; o PNG herdava a unidade mista. | Corrigido: eixo e metadado do PNG usam a mesma unidade de contagem da tela. Critério: tabela mantém sua unidade mista e gráfico/PNG informam matrículas funcionais distintas. Matheus e Talita podem revisar clareza. |
| Nome da aba e orientações de feedback — usabilidade | Guia usava nome antigo e pedia filtros no comentário, incompatível com a orientação atual de não copiar dados acadêmicos. | Guia atualizado para a tela atual e identificação automática da execução. O CSV manual não é backlog compartilhado. |
| Fontes ausentes no pacote Python — usabilidade / instalação | Na instalação não editável, o módulo encontrava tokens e marca, mas os PNGs não encontravam as seis fontes configuradas. | Empacotados os arquivos originais fornecidos, sem mudança visual. Critério: instalar offline em ambiente isolado e gerar gráfico com as fontes; condições de distribuição seguem pendentes de revisão institucional. |
| Detalhe de formados R06 e variação com atual ausente — erro de cálculo/apresentação | Correções já registradas em [4a](PROMPT4A_MATRICULAS.md); total não soma cursos. | Preservadas; testes e conciliação offline existentes. Matheus registrou a conciliação e aceite da 4a no escopo sintético. |
| Carga com parcela nula e unidade ausente — qualidade da fonte / erro de estado | Corrigidas na [4b](PROMPT4B_CARGA.md); teste offline não comprova cardinalidade no PostgreSQL. | Preservar estado parcial e comparação bloqueada quando aplicável. Matheus pode executar a conciliação sintética preparada; não é aceite já registrado. |
| Cadastro atual, ingresso desconhecido, bolsa sem vigência por departamento, competências ausentes e cadastro/carga com possíveis multiplicações — qualidade da fonte | Afetam somente os resultados e pontos descritos nos guias; ausente não equivale a zero. | Manter avisos e bloqueios específicos; na etapa final, Matheus e responsáveis pela fonte/DBA conferem cobertura, chaves e cardinalidade institucional. |
| Grupo QP, equivalência de cursos, unidade institucional de carga, classificação TCC e limiares adicionais — regra pendente | Simulações identificadas não aprovam equivalências; falta de regra impede somente conclusão afetada. | Não inventar mapeamento, classificação ou limiar; responsáveis pela fonte/Matheus encaminham lacuna concreta quando necessária. |
| Feedback em sessão e CSV manual — usabilidade / decisão operacional | Registros não baixados se perdem ao encerrar sessão; comentário livre pode conter dados indevidos. | Time e Matheus definem persistência, retenção, proteção, backup e integração ao backlog (Q-008); não foi adotado SQLite. Talita avalia o uso. |
| Lentidão e interrupção da suíte anterior — desempenho / verificação | Houve teste de interface expirado e suíte interrompida; a falha anterior não foi diagnosticada. | Nesta rodada, a suíte completa terminou com 410 aprovados e um teste de integração excluído, em 899,97 s. A lentidão observada permanece sem causa determinada; nenhuma infraestrutura foi alterada. |
| Identidade visual e revisão de uso — usabilidade / validação externa | Tokens e recursos são aplicados conforme materiais fornecidos e decisões D-021/D-024; não há homologação visual. | Matheus e responsável institucional avaliam identidade; Talita avalia compreensão e arquivos. |
| Financeiro, relatório institucional completo, produtividade e recomendação de contratação — fora do escopo | Os roteiros não autorizam essas conclusões nem interpretação automática. | Manter fora da PoC. |

## Roteiro e limites de conferência

| Roteiro | Referência de revisão sintética |
|---|---|
| R01 | Cadastro atual; total e quadro por matrícula distinta, categoria/departamento por linhas com matrícula; fontes e estados de Horas Reais separados. |
| R02 | QP configurável e identificado como simulação; denominador próprio por unidade; classificação ausente e grupo não selecionado não viram conclusão. |
| R03 | Pessoas distintas por competência e união semestral; janeiro–julho/agosto–dezembro; pilhas podem se sobrepor; mês ausente não vira zero. |
| R04 | Fonte dedicada de Horas Reais, semestre do filtro, nulidade e unidade explícitas; alocações não substituem carga. |
| R05 | Evidências distintas para cadastro, registros e vigências; sem inferir função administrativa por gratificação ou contratação por mudança de cargo. |
| R06 | Quatro populações por matrícula acadêmica e período, cursos por código e variação sem divisão por base zero; falhas de fontes afetam apenas séries dependentes. |

As telas invalidam resultados e downloads quando o recorte muda; novo cálculo tem
identificador próprio. CSV/PNG/ZIP são gerados em memória e identificados como
sintéticos; contexto do PNG pode exigir leitor de metadados. O formulário não
copia filtros nem registros acadêmicos e orienta a não incluí-los no comentário.
Fontes reais, permissões, TLS, equivalências, cobertura e resultados institucionais
não são comprovados por esta revisão. Os comandos e resultados efetivos desta
rodada estão em [STATUS](../STATUS.md).
