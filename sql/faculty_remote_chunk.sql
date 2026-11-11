-- Bloco da carga docente via CLI autenticada (layout v2). Lote bloqueado durante a carga.
-- {{table}} vem da lista fechada de layouts; payload serializado por psycopg.sql.Literal.
BEGIN;
SET LOCAL statement_timeout = '120s';
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM vrac_docentes.cargas WHERE id = {{batch}} AND NOT liberada)
 THEN RAISE EXCEPTION 'Carga inexistente ou liberada'; END IF;
END $$;
CREATE TEMP TABLE vrac_expected (LIKE vrac_docentes.{{table}}) ON COMMIT DROP;
PREPARE vrac_csv_rows(jsonb) AS
INSERT INTO pg_temp.vrac_expected
SELECT * FROM jsonb_populate_recordset(NULL::vrac_docentes.{{table}}, $1);
EXECUTE vrac_csv_rows({{payload}});
DEALLOCATE vrac_csv_rows;
INSERT INTO vrac_docentes.{{table}} SELECT * FROM pg_temp.vrac_expected;
DO $$ BEGIN
 IF EXISTS (
   SELECT * FROM pg_temp.vrac_expected
   EXCEPT ALL
   SELECT * FROM vrac_docentes.{{table}}
   WHERE carga_id = {{batch}} AND linha > {{offset}} AND linha <= {{end}}
 ) OR EXISTS (
   SELECT * FROM vrac_docentes.{{table}}
   WHERE carga_id = {{batch}} AND linha > {{offset}} AND linha <= {{end}}
   EXCEPT ALL
   SELECT * FROM pg_temp.vrac_expected
 ) THEN RAISE EXCEPTION 'Conferência integral falhou'; END IF;
END $$;
COMMIT;
