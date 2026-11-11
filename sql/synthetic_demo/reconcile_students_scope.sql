-- Referência independente R06. Fragmento fixo, usado somente pela rotina manual.
-- Cadastro do ingresso recortado apenas pelos departamentos efetivamente lidos.
WITH
departments AS (SELECT value FROM json_each_text(CAST(%(departments)s AS json))),
courses AS (SELECT value FROM json_each_text(CAST(%(courses)s AS json))),
qualifications AS (SELECT value FROM json_each_text(CAST(%(qualifications)s AS json))),
shifts AS (SELECT value FROM json_each_text(CAST(%(shifts)s AS json))),
levels AS (SELECT value FROM json_each_text(CAST(%(levels)s AS json))),
entry_kinds AS (SELECT value FROM json_each_text(CAST(%(entry_kinds)s AS json))),
entries AS (
    SELECT registration, MIN(entry_period) AS first_entry
    FROM vrac_sintetico.analysis_students
    WHERE department IN (SELECT value FROM departments) AND registration IS NOT NULL
    GROUP BY registration
),
source_rows AS (
    SELECT 'cadastro' AS origin, registration, department, course, qualification, shift,
           level, entry_period, period, status, entry_kind FROM vrac_sintetico.analysis_students
    WHERE department IN (SELECT value FROM departments)
    UNION ALL
    SELECT 'historico' AS origin, registration, department, course, qualification, shift,
           level, entry_period, period, status, entry_kind FROM vrac_sintetico.analysis_student_history
    WHERE department IN (SELECT value FROM departments)
),
filtered AS (
    SELECT * FROM source_rows
    WHERE (CAST(%(course)s AS text) IS NULL OR course = %(course)s)
      AND (NOT EXISTS (SELECT 1 FROM courses) OR course IN (SELECT value FROM courses))
      AND (NOT EXISTS (SELECT 1 FROM qualifications)
           OR COALESCE(NULLIF(qualification, ''), 'Não informado')
              IN (SELECT value FROM qualifications))
      AND (NOT EXISTS (SELECT 1 FROM shifts)
           OR COALESCE(NULLIF(shift, ''), 'Não informado') IN (SELECT value FROM shifts))
      AND (NOT EXISTS (SELECT 1 FROM levels)
           OR COALESCE(NULLIF(level, ''), 'Não informado') IN (SELECT value FROM levels))
      AND (NOT EXISTS (SELECT 1 FROM entry_kinds)
           OR COALESCE(NULLIF(entry_kind, ''), 'Não informado')
              IN (SELECT value FROM entry_kinds))
),
history AS (SELECT * FROM filtered WHERE origin = 'historico'),
current_students AS (SELECT * FROM filtered WHERE origin = 'cadastro'),
candidates AS (
    SELECT DISTINCT registration FROM history
    WHERE period = %(period)s AND status IN ('MT', 'MC') AND registration IS NOT NULL
),
-- Como o DAX do painel: sem cadastro não conta; ingresso em branco é comparado como 0.
eligible AS (
    SELECT c.registration FROM candidates c JOIN entries e ON c.registration = e.registration
    WHERE e.first_entry IS NULL OR e.first_entry <= %(period)s
),
enrollment_observed AS (
    SELECT 1 AS observed
    WHERE EXISTS (SELECT 1 FROM history WHERE period = %(period)s)
),
completions AS (
    SELECT registration, MIN(period) AS event FROM current_students
    WHERE status IN ('FR', 'TD') AND registration IS NOT NULL AND period IS NOT NULL
    GROUP BY registration
),
entrants AS (
    SELECT DISTINCT registration FROM history
    WHERE registration IS NOT NULL AND entry_period = %(period)s
      AND (period = %(period)s OR entry_kind = 'Dupla Diplomacao')
)
