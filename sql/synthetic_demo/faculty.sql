-- Cada linha preserva mês, vínculo e lote do cenário; não agrega docentes ou horas.
SELECT department, period, reference_month, teacher_id, contract_id,
       employment_type, real_hours
FROM vrac_sintetico.demo_faculty
WHERE department = %(department)s AND period = %(period)s
ORDER BY reference_month, teacher_id, contract_id
LIMIT 5001;
