SELECT department, registration, semester, name, cadre, category, real_hours, contracted_hours
FROM vrac_sintetico.analysis_workloads
WHERE (%(department)s = 'Todos os departamentos' OR department = %(department)s)
ORDER BY semester, registration
LIMIT 5001;
