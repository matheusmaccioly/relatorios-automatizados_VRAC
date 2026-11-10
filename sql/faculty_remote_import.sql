-- Modelo fechado para a CLI autenticada. Payload é serializado por psycopg.sql.Literal
-- e passado como parâmetro da instrução preparada, nunca como identificador SQL.
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
   SELECT * FROM vrac_docentes.{{table}} WHERE carga_id = {{batch}}
 ) OR EXISTS (
   SELECT * FROM vrac_docentes.{{table}} WHERE carga_id = {{batch}}
   EXCEPT ALL
   SELECT * FROM pg_temp.vrac_expected
 ) THEN RAISE EXCEPTION 'Conferência integral falhou'; END IF;
END $$;
DROP TABLE pg_temp.vrac_expected;
PREPARE vrac_csv_manifest(uuid,text,bigint,text) AS
INSERT INTO vrac_docentes.arquivos(carga_id,conjunto,linhas,hash_conteudo)
VALUES ($1,$2,$3,$4);
EXECUTE vrac_csv_manifest({{batch}},{{component}},{{count}},{{hash}});
DEALLOCATE vrac_csv_manifest;
