-- Auditoria de cardinalidade sintética, sem remover linhas ou presumir duplicidade ilegítima.
WITH departments AS (SELECT value FROM json_each_text(CAST(%(departments)s AS json))),
h AS (
 SELECT * FROM vrac_sintetico."V_HORAS_REAIS_PROF"
 WHERE "SEMESTRE" = %(semester)s AND "DEPTO_PROF" IN (SELECT value FROM departments)
),
registrations AS (
 SELECT "MATRICULA_PRF" AS registration, COUNT(*) AS n FROM h GROUP BY "MATRICULA_PRF"
),
cadastre AS (
 SELECT "MATRICULAINT" AS registration, COUNT(*) AS n
 FROM vrac_sintetico."V_FUNCIONARIO" GROUP BY "MATRICULAINT"
),
planning AS (
 SELECT p.*, (SELECT COUNT(*) FROM h WHERE h."MATRICULA_PRF" = p."MATRICULA_PROFESSOR") AS matches
 FROM vrac_sintetico."V_PLANEJAMENTO" p WHERE p."ANO_SEMESTRE" = %(semester)s
)
SELECT (SELECT COUNT(*) FROM h) AS horas_origem,
       (SELECT COUNT(*) FROM vrac_sintetico.analysis_workloads WHERE semester = %(semester)s AND department IN (SELECT value FROM departments)) AS horas_projecao,
       (SELECT COUNT(*) FROM h LEFT JOIN cadastre c ON c.registration = h."MATRICULA_PRF" WHERE c.n > 1) AS horas_cadastro_multiplo,
       (SELECT COUNT(*) FROM h LEFT JOIN cadastre c ON c.registration = h."MATRICULA_PRF" WHERE c.n IS NULL) AS horas_sem_cadastro,
       (SELECT COUNT(*) FROM registrations WHERE n > 1) AS vinculos_multiplas_parcelas,
       (SELECT COUNT(*) FROM planning WHERE matches > 0) AS alocacoes_com_vinculo,
       (SELECT COUNT(*) FROM planning WHERE matches > 1) AS alocacoes_multiplos_destinos,
       (SELECT COUNT(*) FROM planning WHERE matches = 0) AS alocacoes_sem_vinculo_no_recorte,
       (SELECT COUNT(*) FROM vrac_sintetico.analysis_allocations WHERE semester = %(semester)s AND department IN (SELECT value FROM departments)) AS alocacoes_projecao;
