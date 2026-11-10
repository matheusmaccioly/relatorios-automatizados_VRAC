-- Executar pelo operador em banco de teste; dados fictícios, rollback final.
BEGIN;
INSERT INTO auth.users (id, aud, role, email) VALUES
('10000000-0000-4000-8000-000000000002','authenticated','authenticated','csv-test@example.invalid');
INSERT INTO auth.sessions (id, user_id) VALUES
('20000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000002');
INSERT INTO vrac_docentes.cargas (id, liberada) VALUES
('30000000-0000-4000-8000-000000000002',true),
('30000000-0000-4000-8000-000000000003',false);
INSERT INTO vrac_docentes.acessos VALUES
('10000000-0000-4000-8000-000000000002','IND');
INSERT INTO vrac_docentes.horas_reais
(carga_id,linha,departamento_alocacao,vinculo_id,semestre,horas_reais) VALUES
('30000000-0000-4000-8000-000000000002',1,'IND',repeat('A',64),20261,0),
('30000000-0000-4000-8000-000000000002',2,'IND',repeat('A',64),20261,NULL),
('30000000-0000-4000-8000-000000000002',3,'ECO',repeat('B',64),20261,99);
DO $$ BEGIN
 IF has_schema_privilege('anon','vrac_docentes','USAGE')
 OR has_function_privilege('anon','public.vrac_docentes_page(uuid,text,text,bigint,integer)','EXECUTE')
 THEN RAISE EXCEPTION 'Acesso público indevido'; END IF;
END $$;
SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claims',
'{"sub":"10000000-0000-4000-8000-000000000002","role":"authenticated","is_anonymous":false,"session_id":"20000000-0000-4000-8000-000000000002"}',true);
DO $$ DECLARE data jsonb; BEGIN
 IF public.vrac_docentes_options()->'departments' <> '["IND"]'::jsonb
 OR public.vrac_docentes_options()->'synthetic' <> 'false'::jsonb
 THEN RAISE EXCEPTION 'Opções institucionais indevidas'; END IF;
 data := public.vrac_docentes_rows('30000000-0000-4000-8000-000000000002','horas_reais',ARRAY['IND'],0,1);
 IF jsonb_array_length(data->'rows') <> 1 THEN RAISE EXCEPTION 'Paginação por escopo falhou'; END IF;
 BEGIN
  PERFORM public.vrac_docentes_rows('30000000-0000-4000-8000-000000000002','horas_reais',ARRAY['IND','ECO']);
  RAISE EXCEPTION 'Recorte misto não autorizado passou';
 EXCEPTION WHEN insufficient_privilege THEN NULL; END;
 data := public.vrac_docentes_page('30000000-0000-4000-8000-000000000002','horas_reais','IND',0,1);
 IF data->'synthetic' <> 'false'::jsonb OR data->'rows'->0->'horas_reais' <> '0'::jsonb
 OR jsonb_array_length(data->'rows') <> 1 THEN RAISE EXCEPTION 'Primeira página incorreta'; END IF;
 data := public.vrac_docentes_page('30000000-0000-4000-8000-000000000002','horas_reais','IND',1,1000);
 IF data->'rows'->0->'horas_reais' <> 'null'::jsonb OR jsonb_array_length(data->'rows') <> 1
 THEN RAISE EXCEPTION 'Segunda página incorreta'; END IF;
 IF (SELECT count(*) FROM vrac_docentes.horas_reais WHERE carga_id='30000000-0000-4000-8000-000000000002') <> 2
 THEN RAISE EXCEPTION 'Isolamento direto falhou'; END IF;
 BEGIN
  PERFORM public.vrac_docentes_page('30000000-0000-4000-8000-000000000002','horas_reais','ECO');
  RAISE EXCEPTION 'Departamento indevido acessível';
 EXCEPTION WHEN insufficient_privilege THEN NULL; END;
 BEGIN
  PERFORM public.vrac_docentes_page('30000000-0000-4000-8000-000000000003','horas_reais','IND');
  RAISE EXCEPTION 'Carga não liberada acessível';
 EXCEPTION WHEN insufficient_privilege THEN NULL; END;
 BEGIN
  UPDATE vrac_docentes.cargas SET liberada = true;
  RAISE EXCEPTION 'Escrita permitida';
 EXCEPTION WHEN insufficient_privilege THEN NULL; END;
END $$;
RESET ROLE;
DELETE FROM auth.sessions WHERE id='20000000-0000-4000-8000-000000000002';
SET LOCAL ROLE authenticated;
DO $$ BEGIN
 IF EXISTS (SELECT 1 FROM vrac_docentes.horas_reais)
 THEN RAISE EXCEPTION 'Sessão revogada ainda lê'; END IF;
END $$;
RESET ROLE;
ROLLBACK;
