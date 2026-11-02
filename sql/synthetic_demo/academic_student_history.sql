SELECT registration, department, course, course_name, qualification, shift,
       level, entry_period, period, status, entry_kind
FROM vrac_sintetico.analysis_student_history
WHERE (%(department)s = 'Todos os departamentos' OR department = %(department)s)
ORDER BY period, registration
LIMIT 5001;
