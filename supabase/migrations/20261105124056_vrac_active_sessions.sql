-- Valida a sessão no banco: logout/revogação impedem novas leituras imediatamente.
-- SECURITY DEFINER limitado a esta consulta em auth.sessions, nunca a dados acadêmicos.
CREATE FUNCTION vrac_app.active_session() RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS $$
    SELECT EXISTS (
        SELECT 1 FROM auth.sessions s
        WHERE s.id::text = (SELECT auth.jwt()->>'session_id')
          AND s.user_id = (SELECT auth.uid())
          AND (s.not_after IS NULL OR s.not_after > now())
    );
$$;
REVOKE ALL ON FUNCTION vrac_app.active_session() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION vrac_app.active_session() TO authenticated;

DO $$
DECLARE item text;
BEGIN
    FOREACH item IN ARRAY ARRAY[
        'access_grants','departments','dataset_metadata','register','real_hours',
        'history','workloads','allocations','functions','appointments',
        'students','student_history','scholarships','demo_faculty','demo_allocations'
    ] LOOP
        EXECUTE format(
            'CREATE POLICY require_active_session ON vrac_app.%I AS RESTRICTIVE '
            'FOR SELECT TO authenticated USING ((SELECT vrac_app.active_session()))', item
        );
    END LOOP;
END;
$$;
NOTIFY pgrst, 'reload schema';
