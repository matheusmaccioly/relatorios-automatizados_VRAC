-- query: timeout
SET LOCAL statement_timeout = '120s';
-- query: batch
INSERT INTO vrac_alunos.cargas
(id, periodo_inicio, periodo_fim, linhas, hash_conteudo, encoding, marcador_nulo,
 ajustes_individuais_informados)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s);
-- query: copy
COPY vrac_alunos.eventos
(carga_id, linha, indicador, periodo_eixo, periodo_linha, aluno_id, departamento_curso,
 sigla_centro, centro, nivel, subnivel, curso_codigo, curso, habilitacao_codigo, habilitacao,
 turno, forma_ingresso, situacao_atual, ingresso_cadastro_nulo, ajustes_individuais_informados)
FROM STDIN;
-- query: verify
SELECT indicador, periodo_eixo, periodo_linha, aluno_id, departamento_curso,
 sigla_centro, centro, nivel, subnivel, curso_codigo, curso, habilitacao_codigo, habilitacao,
 turno, forma_ingresso, situacao_atual, ingresso_cadastro_nulo, ajustes_individuais_informados
FROM vrac_alunos.eventos WHERE carga_id = %s ORDER BY linha;
