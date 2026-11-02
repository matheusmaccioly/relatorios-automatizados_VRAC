-- R01: linhas de Horas Reais dos vínculos do departamento, todos os semestres.
-- Ligação documentada no painel: MATRICULA_PRF -> V_FUNCIONARIO.MATRICULAINT (M:1).
-- O semestre atual e a soma são calculados na aplicação, por matrícula.
SELECT h."MATRICULA_PRF" AS registration_int,
       h."SEMESTRE" AS semester,
       h."HORAS_REAIS" AS hours,
       h."QUADRO" AS cadre
FROM vrac_sintetico."V_HORAS_REAIS_PROF" AS h
WHERE h."MATRICULA_PRF" IN (
    SELECT f."MATRICULAINT"
    FROM vrac_sintetico."V_FUNCIONARIO" AS f
    WHERE f."DEPARTAMENTO" = %(department)s
)
ORDER BY h."MATRICULA_PRF", h."SEMESTRE"
LIMIT 5001;
