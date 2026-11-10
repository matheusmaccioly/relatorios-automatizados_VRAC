-- SQL fixo de carga; parâmetros vinculados. Somente operador autorizado.

-- query: timeout
SET LOCAL statement_timeout = '120s';

-- query: batch
INSERT INTO vrac_docentes.cargas (id) VALUES (%s);

-- query: manifest
INSERT INTO vrac_docentes.arquivos (carga_id, conjunto, linhas, hash_conteudo) VALUES (%s,%s,%s,%s);

-- query: copy_cadastro
COPY vrac_docentes.cadastro (carga_id,linha,pessoa_id,nome_ficticio,vinculo_id,departamento_alocacao,quadro,categoria,situacao,dupla_funcao,carga_semanal) FROM STDIN;

-- query: verify_cadastro
SELECT pessoa_id,nome_ficticio,vinculo_id,departamento_alocacao,quadro,categoria,situacao,dupla_funcao,carga_semanal FROM vrac_docentes.cadastro WHERE carga_id=%s ORDER BY linha;

-- query: copy_horas_reais
COPY vrac_docentes.horas_reais (carga_id,linha,departamento_alocacao,vinculo_id,semestre,quadro,horas_contratuais,horas_reais) FROM STDIN;

-- query: verify_horas_reais
SELECT departamento_alocacao,vinculo_id,semestre,quadro,horas_contratuais,horas_reais FROM vrac_docentes.horas_reais WHERE carga_id=%s ORDER BY linha;

-- query: copy_historico_mensal
COPY vrac_docentes.historico_mensal (carga_id,linha,departamento_alocacao,vinculo_id,pessoa_id,ano,mes,lote,ativo,excluido_a4,carga_horaria) FROM STDIN;

-- query: verify_historico_mensal
SELECT departamento_alocacao,vinculo_id,pessoa_id,ano,mes,lote,ativo,excluido_a4,carga_horaria FROM vrac_docentes.historico_mensal WHERE carga_id=%s ORDER BY linha;

-- query: copy_historico_cargos
COPY vrac_docentes.historico_cargos (carga_id,linha,departamento_alocacao,vinculo_id,competencia,categoria,quadro) FROM STDIN;

-- query: verify_historico_cargos
SELECT departamento_alocacao,vinculo_id,competencia,categoria,quadro FROM vrac_docentes.historico_cargos WHERE carga_id=%s ORDER BY linha;

-- query: copy_historico_carga
COPY vrac_docentes.historico_carga (carga_id,linha,departamento_alocacao,vinculo_id,ano,mes,carga_horaria) FROM STDIN;

-- query: verify_historico_carga
SELECT departamento_alocacao,vinculo_id,ano,mes,carga_horaria FROM vrac_docentes.historico_carga WHERE carga_id=%s ORDER BY linha;

-- query: copy_alocacoes
COPY vrac_docentes.alocacoes (carga_id,linha,departamento_alocacao,vinculo_id,semestre,unidade_oferta,disciplina_id,turma_id,nivel,tipo,obrigatoria,horas_alocadas,compartilhada,vagas_ofertadas,vagas_preenchidas,professor_principal) FROM STDIN;

-- query: verify_alocacoes
SELECT departamento_alocacao,vinculo_id,semestre,unidade_oferta,disciplina_id,turma_id,nivel,tipo,obrigatoria,horas_alocadas,compartilhada,vagas_ofertadas,vagas_preenchidas,professor_principal FROM vrac_docentes.alocacoes WHERE carga_id=%s ORDER BY linha;

-- query: copy_eventos_funcoes
COPY vrac_docentes.eventos_funcoes (carga_id,linha,departamento_alocacao,vinculo_id,evento_id,ano,mes,descricao_id,papel_id) FROM STDIN;

-- query: verify_eventos_funcoes
SELECT departamento_alocacao,vinculo_id,evento_id,ano,mes,descricao_id,papel_id FROM vrac_docentes.eventos_funcoes WHERE carga_id=%s ORDER BY linha;
