-- Sufixo fixo da referência R06; não consulta bolsas.
SELECT
    CASE WHEN EXISTS (SELECT 1 FROM enrollment_observed)
         THEN (SELECT COUNT(*) FROM eligible) END AS "Matriculados",
    CASE WHEN EXISTS (SELECT 1 FROM history WHERE period = %(period)s)
               OR EXISTS (SELECT 1 FROM current_students WHERE period = %(period)s)
         THEN (SELECT COUNT(*) FROM completions WHERE event = %(period)s) END AS "Formados",
    CASE WHEN EXISTS (SELECT 1 FROM history WHERE period = %(period)s)
               OR EXISTS (SELECT 1 FROM entrants)
         THEN (SELECT COUNT(*) FROM entrants) END AS "Ingressantes";
