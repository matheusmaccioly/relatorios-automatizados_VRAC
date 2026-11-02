SELECT registration, department, course, course_name, qualification, shift,
       level, entry_period, period, status, entry_kind
FROM vrac_sintetico.analysis_students
WHERE (%(department)s = 'Todos os departamentos' OR department = %(department)s)
ORDER BY registration
LIMIT 5001;
