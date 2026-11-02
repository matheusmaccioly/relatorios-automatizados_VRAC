SELECT department, distribution_department, registration, year, month, description, role
FROM vrac_sintetico.analysis_functions
WHERE (%(department)s = 'Todos os departamentos' OR department = %(department)s)
ORDER BY year, month, registration
LIMIT 5001;
