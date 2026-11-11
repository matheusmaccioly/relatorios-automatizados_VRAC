-- Operador: somente banco de teste. Fixtures fictícias; rollback obrigatório.
BEGIN;
INSERT INTO auth.users (id, aud, role, email) VALUES
('10000000-0000-4000-8000-000000000020','authenticated','authenticated','alunos@example.invalid');
INSERT INTO auth.sessions (id,user_id) VALUES
('20000000-0000-4000-8000-000000000020','10000000-0000-4000-8000-000000000020');
INSERT INTO vrac_alunos.cargas
(id,liberada,periodo_inicio,periodo_fim,linhas,hash_conteudo,encoding,marcador_nulo,ajustes_individuais_informados)
VALUES ('30000000-0000-4000-8000-000000000020',true,20261,20262,5,repeat('a',64),'utf-8-sig','NULL',0),
('30000000-0000-4000-8000-000000000021',false,20261,20262,1,repeat('b',64),'utf-8-sig','NULL',0);
INSERT INTO vrac_alunos.acessos VALUES
('10000000-0000-4000-8000-000000000020','IND');
INSERT INTO vrac_alunos.eventos
(carga_id,linha,indicador,periodo_eixo,periodo_linha,aluno_id,departamento_curso,
 curso_codigo,ingresso_cadastro_nulo,ajustes_individuais_informados) VALUES
('30000000-0000-4000-8000-000000000020',1,'MATRICULADOS',20261,20261,repeat('A',64),'IND','001',0,0),
('30000000-0000-4000-8000-000000000020',2,'MATRICULADOS',20261,20261,repeat('A',64),'IND','002',0,0),
('30000000-0000-4000-8000-000000000020',3,'INGRESSANTES',20261,20262,repeat('A',64),'IND','001',0,0),
('30000000-0000-4000-8000-000000000020',4,'MATRICULADOS',20261,20261,repeat('B',64),'ECO','003',0,0),
('30000000-0000-4000-8000-000000000020',5,'FORMADOS',20262,20262,repeat('C',64),'IND',NULL,0,0);
DO $$ BEGIN
 IF has_schema_privilege('anon','vrac_alunos','USAGE')
 OR has_function_privilege('anon','public.vrac_alunos_geral(uuid,text[],integer,integer,jsonb)','EXECUTE')
 THEN RAISE EXCEPTION 'Acesso público indevido'; END IF;
END $$;
SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claims',
'{"sub":"10000000-0000-4000-8000-000000000020","role":"authenticated","session_id":"20000000-0000-4000-8000-000000000020","is_anonymous":false}',true);
DO $$ DECLARE r jsonb; BEGIN
 r := public.vrac_alunos_geral('30000000-0000-4000-8000-000000000020',ARRAY['IND'],20261,20262);
 IF r->'synthetic' <> 'false'::jsonb OR jsonb_array_length(r->'rows') <> 3
 OR EXISTS (SELECT 1 FROM jsonb_array_elements(r->'rows') e WHERE (e->>'quantidade')::integer <> 1)
 THEN RAISE EXCEPTION 'Contagem distinta/eixo/ausência incorretos'; END IF;
 IF (SELECT count(*) FROM vrac_alunos.eventos WHERE carga_id='30000000-0000-4000-8000-000000000020') <> 4
 THEN RAISE EXCEPTION 'RLS falhou'; END IF;
 IF public.vrac_alunos_options()->'departments' <> '["IND"]'::jsonb
 THEN RAISE EXCEPTION 'Opções fora do escopo'; END IF;
 r := public.vrac_alunos_filters('30000000-0000-4000-8000-000000000020',ARRAY['IND']);
 IF r->'filters'->'curso_codigo' @> '["003"]'::jsonb
 THEN RAISE EXCEPTION 'Filtro revelou outro departamento'; END IF;
 r := public.vrac_alunos_geral('30000000-0000-4000-8000-000000000020',ARRAY['IND'],20261,20262,
 '{"curso_codigo":["001","002"]}');
 IF (r->'rows'->1->>'quantidade')::integer <> 1 OR jsonb_array_length(r->'rows') <> 2
 THEN RAISE EXCEPTION 'Seleção múltipla somou alunos duplicados'; END IF;
 r := public.vrac_alunos_geral('30000000-0000-4000-8000-000000000020',ARRAY['IND'],20261,20262,'{"curso_codigo":null}');
 IF jsonb_array_length(r->'rows') <> 1 THEN RAISE EXCEPTION 'Filtro nulo falhou'; END IF;
 r := public.vrac_alunos_geral('30000000-0000-4000-8000-000000000020',ARRAY['IND'],20261,20262,'{"curso_codigo":""}');
 IF r->'rows' <> '[]'::jsonb THEN RAISE EXCEPTION 'Vazio virou nulo'; END IF;
 BEGIN
  PERFORM public.vrac_alunos_geral('30000000-0000-4000-8000-000000000020',ARRAY['IND','ECO'],20261,20262);
  RAISE EXCEPTION 'Recorte misto aceito';
 EXCEPTION WHEN insufficient_privilege THEN NULL; END;
 BEGIN
  PERFORM public.vrac_alunos_geral('30000000-0000-4000-8000-000000000021',ARRAY['IND'],20261,20262);
  RAISE EXCEPTION 'Carga bloqueada acessível';
 EXCEPTION WHEN insufficient_privilege THEN NULL; END;
 BEGIN
  PERFORM public.vrac_alunos_geral('30000000-0000-4000-8000-000000000020',ARRAY['IND'],20251,20262);
  RAISE EXCEPTION 'Fora de cobertura aceito';
 EXCEPTION WHEN invalid_parameter_value THEN NULL; END;
 BEGIN
  PERFORM public.vrac_alunos_geral('30000000-0000-4000-8000-000000000020',ARRAY['IND'],20261,20262,'{"aluno_id":"x"}');
  RAISE EXCEPTION 'Filtro livre aceito';
 EXCEPTION WHEN invalid_parameter_value THEN NULL; END;
 BEGIN
  UPDATE vrac_alunos.cargas SET liberada = true;
  RAISE EXCEPTION 'Escrita permitida';
 EXCEPTION WHEN insufficient_privilege THEN NULL; END;
END $$;
RESET ROLE;
DELETE FROM auth.sessions WHERE id = '20000000-0000-4000-8000-000000000020';
SET LOCAL ROLE authenticated;
DO $$ BEGIN
 IF EXISTS (SELECT 1 FROM vrac_alunos.eventos) THEN RAISE EXCEPTION 'Sessão revogada leu'; END IF;
END $$;
ROLLBACK;
