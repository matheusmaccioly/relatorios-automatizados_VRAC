-- Sufixo separado: falha em bolsas não impede a referência das outras três curvas.
SELECT CASE WHEN EXISTS (SELECT 1 FROM enrollment_observed)
    THEN (
        SELECT COUNT(DISTINCT e.registration) FROM eligible e
        WHERE EXISTS (
            SELECT 1 FROM vrac_sintetico.analysis_scholarships b
            WHERE b.registration = e.registration AND b.period = %(period)s
              AND b.department IN (SELECT value FROM departments)
        )
    ) END AS "Bolsistas matriculados";
