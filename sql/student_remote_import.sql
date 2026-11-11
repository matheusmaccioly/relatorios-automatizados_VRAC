-- Lote bloqueado durante toda a carga. Parâmetros preparados e escape pelo driver.
BEGIN;
SET LOCAL statement_timeout = '120s';
CREATE TEMP TABLE vrac_expected (LIKE vrac_alunos.eventos) ON COMMIT DROP;
PREPARE vrac_student_rows(uuid,bigint,jsonb) AS
INSERT INTO pg_temp.vrac_expected
SELECT $1, $2 + ordinal,
 r->>0, (r->>1)::integer, (r->>2)::integer, r->>3, r->>4,
 r->>5, r->>6, r->>7, r->>8, r->>9, r->>10, r->>11, r->>12,
 r->>13, r->>14, r->>15, (r->>16)::integer, (r->>17)::integer
FROM jsonb_array_elements($3) WITH ORDINALITY AS t(r,ordinal);
EXECUTE vrac_student_rows({{batch}},{{offset}},{{payload}});
DEALLOCATE vrac_student_rows;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM vrac_alunos.cargas WHERE id = {{batch}} AND NOT liberada)
 THEN RAISE EXCEPTION 'Carga inexistente ou liberada'; END IF;
END $$;
INSERT INTO vrac_alunos.eventos SELECT * FROM pg_temp.vrac_expected;
DO $$ BEGIN
 IF EXISTS (
  SELECT * FROM pg_temp.vrac_expected EXCEPT ALL
  SELECT * FROM vrac_alunos.eventos
  WHERE carga_id = {{batch}} AND linha > {{offset}} AND linha <= {{end}}
 ) OR EXISTS (
  SELECT * FROM vrac_alunos.eventos
  WHERE carga_id = {{batch}} AND linha > {{offset}} AND linha <= {{end}}
  EXCEPT ALL SELECT * FROM pg_temp.vrac_expected
 ) THEN RAISE EXCEPTION 'Conferência integral falhou'; END IF;
END $$;
COMMIT;
