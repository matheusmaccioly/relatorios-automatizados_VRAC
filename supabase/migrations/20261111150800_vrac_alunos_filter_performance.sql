-- Reduz dimensões repetidas antes de expandir filtros; preserva RLS e nulos.
CREATE OR REPLACE FUNCTION public.vrac_alunos_filters(p_carga uuid,p_departamentos text[])
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path = '' AS $$
DECLARE resultado jsonb;
BEGIN
 IF p_carga IS NULL OR p_departamentos IS NULL OR cardinality(p_departamentos) NOT BETWEEN 1 AND 8
 OR array_position(p_departamentos,NULL) IS NOT NULL
 OR NOT EXISTS (SELECT 1 FROM vrac_alunos.cargas WHERE id=p_carga)
 OR EXISTS (SELECT 1 FROM unnest(p_departamentos) d WHERE NOT EXISTS
  (SELECT 1 FROM vrac_alunos.acessos a WHERE a.departamento_curso=d))
 THEN RAISE EXCEPTION 'Carga ou recorte indisponível' USING ERRCODE='42501'; END IF;
 SELECT COALESCE(jsonb_object_agg(key,opcoes),'{}'::jsonb) INTO resultado
 FROM (
  SELECT key,jsonb_agg(DISTINCT value ORDER BY value) opcoes
  FROM (
   SELECT DISTINCT sigla_centro,nivel,subnivel,curso_codigo,curso,habilitacao_codigo,
    habilitacao,turno,forma_ingresso,situacao_atual
   FROM vrac_alunos.eventos
   WHERE carga_id=p_carga AND departamento_curso=ANY(p_departamentos)
  ) e CROSS JOIN LATERAL jsonb_each(jsonb_build_object(
   'sigla_centro',e.sigla_centro,'nivel',e.nivel,'subnivel',e.subnivel,
   'curso_codigo',e.curso_codigo,'curso',e.curso,'habilitacao_codigo',e.habilitacao_codigo,
   'habilitacao',e.habilitacao,'turno',e.turno,'forma_ingresso',e.forma_ingresso,
   'situacao_atual',e.situacao_atual)) f
  GROUP BY key
 ) r;
 RETURN jsonb_build_object('origin','institucional_pseudonimizada','synthetic',false,
  'batch',p_carga,'filters',resultado);
END; $$;
REVOKE ALL ON FUNCTION public.vrac_alunos_filters(uuid,text[]) FROM PUBLIC,anon;
GRANT EXECUTE ON FUNCTION public.vrac_alunos_filters(uuid,text[]) TO authenticated;


NOTIFY pgrst, 'reload schema';
