-- Referência da R04: somente projeção dedicada; nenhuma soma de alocações.
WITH departments AS (SELECT value FROM json_each_text(CAST(%(departments)s AS json))),
cadres AS (SELECT value FROM json_each_text(CAST(%(cadres)s AS json))),
categories AS (SELECT value FROM json_each_text(CAST(%(categories)s AS json)))
SELECT registration, SUM(real_hours) AS hours,
       COUNT(*) AS parcels, COUNT(real_hours) AS known,
       COUNT(DISTINCT contracted_hours) AS contracts, MIN(contracted_hours) AS contracted
FROM vrac_sintetico.analysis_workloads
WHERE department IN (SELECT value FROM departments) AND semester = %(semester)s
  AND registration IS NOT NULL AND registration <> ''
  AND (NOT EXISTS (SELECT 1 FROM cadres) OR COALESCE(NULLIF(cadre, ''), 'Não informado') IN (SELECT value FROM cadres))
  AND (NOT EXISTS (SELECT 1 FROM categories) OR COALESCE(NULLIF(category, ''), 'Não informado') IN (SELECT value FROM categories))
GROUP BY registration ORDER BY registration;
