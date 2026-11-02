SELECT department, registration, role, start, "end", evidence, administrative
FROM vrac_sintetico.analysis_appointments
WHERE (%(department)s = 'Todos os departamentos' OR department = %(department)s)
ORDER BY registration, start, role
LIMIT 5001;
