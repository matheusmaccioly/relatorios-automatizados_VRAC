SELECT registration, period
FROM vrac_sintetico.analysis_scholarships
WHERE (%(department)s = 'Todos os departamentos' OR department = %(department)s)
ORDER BY period, registration
LIMIT 5001;
