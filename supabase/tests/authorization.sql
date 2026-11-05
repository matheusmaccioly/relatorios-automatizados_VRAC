-- Teste transacional: identidades e linhas sintéticas são revertidas ao final.
BEGIN;
INSERT INTO auth.users (id, aud, role, email) VALUES
('10000000-0000-4000-8000-000000000001','authenticated','authenticated','vrac-rls-test@example.invalid');
INSERT INTO auth.sessions (id, user_id) VALUES
('20000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000001');
INSERT INTO vrac_app.departments VALUES ('__RLS_TEST_A__'), ('__RLS_TEST_B__');
INSERT INTO vrac_app.access_grants VALUES
('10000000-0000-4000-8000-000000000001','__RLS_TEST_A__',true);
INSERT INTO vrac_app.workloads (scope_department,ordinal,department,semester,real_hours)
VALUES ('__RLS_TEST_A__',0,'__RLS_TEST_A__',20261,0),
       ('__RLS_TEST_A__',1,'__RLS_TEST_A__',20261,NULL),
       ('__RLS_TEST_B__',0,'__RLS_TEST_B__',20261,99);

DO $$ BEGIN
    IF has_schema_privilege('anon','vrac_app','USAGE') OR
       has_schema_privilege('authenticated','vrac_sintetico','USAGE') OR
       has_function_privilege('anon','public.vrac_options()','EXECUTE') THEN
        RAISE EXCEPTION 'Privilégios públicos indevidos';
    END IF;
END $$;

SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claims',
'{"sub":"10000000-0000-4000-8000-000000000001","role":"authenticated","is_anonymous":false,"session_id":"20000000-0000-4000-8000-000000000001"}', true);
DO $$ DECLARE data jsonb; BEGIN
    IF (public.vrac_options()->'departments') <> '["__RLS_TEST_A__"]'::jsonb THEN
        RAISE EXCEPTION 'Isolamento de departamentos falhou';
    END IF;
    data := public.vrac_snapshot(ARRAY['__RLS_TEST_A__']);
    IF jsonb_array_length(data->'workloads') <> 2 OR
       (data->'workloads'->0->'real_hours') <> '0'::jsonb OR
       (data->'workloads'->1->'real_hours') <> 'null'::jsonb THEN
        RAISE EXCEPTION 'Zero, nulo ou população alterados';
    END IF;
    BEGIN
        PERFORM public.vrac_snapshot(ARRAY['__RLS_TEST_B__']);
        RAISE EXCEPTION 'Departamento sem autorização foi consultado';
    EXCEPTION WHEN insufficient_privilege THEN NULL; END;
    BEGIN
        INSERT INTO vrac_app.access_grants VALUES
        ('10000000-0000-4000-8000-000000000001','__RLS_TEST_B__',true);
        RAISE EXCEPTION 'Usuário conseguiu elevar o próprio acesso';
    EXCEPTION WHEN insufficient_privilege THEN NULL; END;
    BEGIN
        UPDATE vrac_app.workloads SET real_hours=999;
        RAISE EXCEPTION 'Usuário conseguiu alterar dados';
    EXCEPTION WHEN insufficient_privilege THEN NULL; END;
END $$;

RESET ROLE;
DELETE FROM auth.sessions WHERE id='20000000-0000-4000-8000-000000000001';
SET LOCAL ROLE authenticated;
DO $$ BEGIN
    IF (public.vrac_options()->'departments') <> '[]'::jsonb THEN
        RAISE EXCEPTION 'Sessão revogada continua com acesso';
    END IF;
END $$;
RESET ROLE;
ROLLBACK;
