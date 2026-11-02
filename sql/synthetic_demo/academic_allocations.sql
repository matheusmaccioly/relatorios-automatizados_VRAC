SELECT department, teaching_department, registration, semester, discipline,
       class_id, allocated_hours, vacancies_filled, shared, classification
FROM vrac_sintetico.analysis_allocations
WHERE (%(department)s = 'Todos os departamentos' OR department = %(department)s)
ORDER BY semester, registration, class_id
LIMIT 5001;
