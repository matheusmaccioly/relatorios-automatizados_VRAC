-- R01: cadastro atual de vínculos de um departamento, sem agregação nem filtro de tela.
-- O CPF não sai do banco: somente um hash opaco, usado para avisar múltiplos vínculos.
SELECT "DEPARTAMENTO" AS department,
       "MATRICULA" AS registration,
       "MATRICULAINT" AS registration_int,
       CASE WHEN "CPF" IS NULL THEN NULL ELSE md5("CPF") END AS person_key,
       "NOME" AS name,
       "QUADRO" AS cadre,
       "CARGO" AS category,
       "DESC_SITUACAO" AS status,
       "IND_DUPLA_FUNCAO" AS dual_role,
       "VINCULO_EXTRAORDINARIO" AS extraordinary,
       "CARGA_HORARIA_SEMANAL" AS weekly_hours,
       "Tempo de Casa (Anos)" AS tenure_years,
       "DESC_TITULACAO" AS degree
FROM vrac_sintetico."V_FUNCIONARIO"
WHERE "DEPARTAMENTO" = %(department)s
ORDER BY "MATRICULA"
LIMIT 5001;
