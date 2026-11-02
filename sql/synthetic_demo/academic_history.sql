SELECT department, person_key, registration, reference_date,
       cadre, category, status, payroll_batch, leave_code
FROM vrac_sintetico.analysis_history
WHERE (%(department)s = 'Todos os departamentos' OR department = %(department)s)
ORDER BY reference_date, registration
LIMIT 5001;
