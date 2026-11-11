-- Opções próprias de alunos; nenhum escopo docente/sintético usado para autorizar a RPC.
CREATE FUNCTION public.vrac_alunos_options() RETURNS jsonb
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = '' AS $$
WITH carga AS (
 SELECT * FROM vrac_alunos.cargas ORDER BY criada_em DESC,id DESC LIMIT 1
)
SELECT jsonb_build_object('origin','institucional_pseudonimizada','synthetic',false,
 'batch',(SELECT id FROM carga),
 'start',(SELECT periodo_inicio FROM carga),'end',(SELECT periodo_fim FROM carga),
 'departments',(SELECT COALESCE(jsonb_agg(d ORDER BY d),'[]'::jsonb) FROM (
  SELECT DISTINCT departamento_curso d FROM vrac_alunos.eventos
  WHERE carga_id=(SELECT id FROM carga)
 ) departamentos));
$$;
REVOKE ALL ON FUNCTION public.vrac_alunos_options() FROM PUBLIC,anon;
GRANT EXECUTE ON FUNCTION public.vrac_alunos_options() TO authenticated;

CREATE FUNCTION public.vrac_alunos_filters(p_carga uuid,p_departamentos text[])
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
  FROM vrac_alunos.eventos e CROSS JOIN LATERAL jsonb_each(jsonb_build_object(
   'sigla_centro',e.sigla_centro,'nivel',e.nivel,'subnivel',e.subnivel,
   'curso_codigo',e.curso_codigo,'curso',e.curso,'habilitacao_codigo',e.habilitacao_codigo,
   'habilitacao',e.habilitacao,'turno',e.turno,'forma_ingresso',e.forma_ingresso,
   'situacao_atual',e.situacao_atual)) f
  WHERE e.carga_id=p_carga AND e.departamento_curso=ANY(p_departamentos)
  GROUP BY key
 ) r;
 RETURN jsonb_build_object('origin','institucional_pseudonimizada','synthetic',false,
  'batch',p_carga,'filters',resultado);
END; $$;
REVOKE ALL ON FUNCTION public.vrac_alunos_filters(uuid,text[]) FROM PUBLIC,anon;
GRANT EXECUTE ON FUNCTION public.vrac_alunos_filters(uuid,text[]) TO authenticated;

-- Seleção múltipla combina valores do mesmo filtro por OU e campos distintos por E.
CREATE OR REPLACE FUNCTION public.vrac_alunos_geral(
 p_carga uuid, p_departamentos text[], p_inicio integer, p_fim integer,
 p_filtros jsonb DEFAULT '{}'::jsonb
) RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path = '' AS $$
DECLARE resultado jsonb;
BEGIN
 IF p_carga IS NULL OR p_departamentos IS NULL OR cardinality(p_departamentos) NOT BETWEEN 1 AND 8
 OR array_position(p_departamentos,NULL) IS NOT NULL
 OR NOT EXISTS (SELECT 1 FROM vrac_alunos.cargas c WHERE c.id = p_carga)
 OR EXISTS (SELECT 1 FROM unnest(p_departamentos) d WHERE NOT EXISTS
  (SELECT 1 FROM vrac_alunos.acessos a WHERE a.departamento_curso = d))
 THEN RAISE EXCEPTION 'Carga ou recorte indisponível' USING ERRCODE = '42501'; END IF;
 IF p_inicio IS NULL OR p_fim IS NULL OR p_inicio > p_fim
 OR p_inicio % 10 NOT IN (1,2) OR p_fim % 10 NOT IN (1,2)
 OR NOT EXISTS (SELECT 1 FROM vrac_alunos.cargas c WHERE c.id = p_carga
  AND p_inicio >= c.periodo_inicio AND p_fim <= c.periodo_fim)
 OR p_filtros IS NULL OR jsonb_typeof(p_filtros) <> 'object'
 THEN RAISE EXCEPTION 'Parâmetros inválidos' USING ERRCODE = '22023'; END IF;
 IF EXISTS (SELECT 1 FROM jsonb_each(p_filtros) f
  WHERE f.key NOT IN ('sigla_centro','centro','nivel','subnivel','curso_codigo','curso',
   'habilitacao_codigo','habilitacao','turno','forma_ingresso','situacao_atual')
  OR jsonb_typeof(f.value) NOT IN ('string','null','array')
  OR (jsonb_typeof(f.value) = 'array' AND (jsonb_array_length(f.value) NOT BETWEEN 1 AND 1000
   OR EXISTS (SELECT 1 FROM jsonb_array_elements(f.value) v WHERE jsonb_typeof(v) NOT IN ('string','null')))))
 THEN RAISE EXCEPTION 'Filtro indisponível' USING ERRCODE = '22023'; END IF;
 SELECT COALESCE(jsonb_agg(to_jsonb(r) ORDER BY r.periodo_eixo,r.indicador),'[]'::jsonb)
 INTO resultado FROM (
  SELECT e.periodo_eixo, e.indicador, count(DISTINCT e.aluno_id) AS quantidade
  FROM vrac_alunos.eventos e
  WHERE e.carga_id = p_carga AND e.departamento_curso = ANY(p_departamentos)
   AND e.periodo_eixo BETWEEN p_inicio AND p_fim
   AND NOT EXISTS (SELECT 1 FROM jsonb_each(p_filtros) f
    WHERE NOT EXISTS (SELECT 1 FROM jsonb_array_elements(
     CASE WHEN jsonb_typeof(f.value)='array' THEN f.value ELSE jsonb_build_array(f.value) END
    ) v WHERE (to_jsonb(e)->f.key) = v))
  GROUP BY e.periodo_eixo,e.indicador
 ) r;
 RETURN jsonb_build_object('origin','institucional_pseudonimizada','synthetic',false,
  'batch',p_carga,'rows',resultado,'unit','matriculas_distintas',
  'missing','ausencia_de_evento_nao_equivale_a_zero');
END; $$;
REVOKE ALL ON FUNCTION public.vrac_alunos_geral(uuid,text[],integer,integer,jsonb) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.vrac_alunos_geral(uuid,text[],integer,integer,jsonb) TO authenticated;
NOTIFY pgrst, 'reload schema';
