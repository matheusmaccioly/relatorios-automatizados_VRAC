SELECT department, teaching_department, period, teacher_id, class_id,
       curriculum_id, sharing_id, allocated_hours, students, classification
FROM vrac_sintetico.demo_allocations
WHERE department = %(department)s AND period = %(period)s
ORDER BY teacher_id, class_id
LIMIT 5001;
