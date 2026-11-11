-- Séries de alunos: filtros comparados por coluna (11/11/2026).
-- Motivo: to_jsonb(linha) por evento levava ~9,6 s com os filtros iniciais do painel,
-- acima do limite de 8 s do papel authenticated. Mesma assinatura, validações,
-- semântica (valor igual a um dos selecionados; null seleciona nulo) e resposta.
CREATE OR REPLACE FUNCTION public.vrac_alunos_geral(
 p_carga uuid, p_departamentos text[], p_inicio integer, p_fim integer,
 p_filtros jsonb DEFAULT '{}'::jsonb
) RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path = '' AS $$
DECLARE
 resultado jsonb;
 f_sigla_centro text[]; f_centro text[]; f_nivel text[]; f_subnivel text[];
 f_curso_codigo text[]; f_curso text[]; f_habilitacao_codigo text[]; f_habilitacao text[];
 f_turno text[]; f_forma_ingresso text[]; f_situacao_atual text[];
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
 -- Filtro ausente = NULL (todos); valor JSON null vira elemento NULL do array.
 SELECT
  max(v) FILTER (WHERE k='sigla_centro'), max(v) FILTER (WHERE k='centro'),
  max(v) FILTER (WHERE k='nivel'), max(v) FILTER (WHERE k='subnivel'),
  max(v) FILTER (WHERE k='curso_codigo'), max(v) FILTER (WHERE k='curso'),
  max(v) FILTER (WHERE k='habilitacao_codigo'), max(v) FILTER (WHERE k='habilitacao'),
  max(v) FILTER (WHERE k='turno'), max(v) FILTER (WHERE k='forma_ingresso'),
  max(v) FILTER (WHERE k='situacao_atual')
 INTO f_sigla_centro, f_centro, f_nivel, f_subnivel, f_curso_codigo, f_curso,
  f_habilitacao_codigo, f_habilitacao, f_turno, f_forma_ingresso, f_situacao_atual
 FROM (
  SELECT f.key AS k, ARRAY(SELECT jsonb_array_elements_text(
   CASE WHEN jsonb_typeof(f.value)='array' THEN f.value ELSE jsonb_build_array(f.value) END)) AS v
  FROM jsonb_each(p_filtros) f
 ) s;
 SELECT COALESCE(jsonb_agg(to_jsonb(r) ORDER BY r.periodo_eixo,r.indicador),'[]'::jsonb)
 INTO resultado FROM (
  SELECT e.periodo_eixo, e.indicador, count(DISTINCT e.aluno_id) AS quantidade
  FROM vrac_alunos.eventos e
  WHERE e.carga_id = p_carga AND e.departamento_curso = ANY(p_departamentos)
   AND e.periodo_eixo BETWEEN p_inicio AND p_fim
   AND (f_sigla_centro IS NULL OR e.sigla_centro = ANY(f_sigla_centro)
        OR (e.sigla_centro IS NULL AND array_position(f_sigla_centro, NULL) IS NOT NULL))
   AND (f_centro IS NULL OR e.centro = ANY(f_centro)
        OR (e.centro IS NULL AND array_position(f_centro, NULL) IS NOT NULL))
   AND (f_nivel IS NULL OR e.nivel = ANY(f_nivel)
        OR (e.nivel IS NULL AND array_position(f_nivel, NULL) IS NOT NULL))
   AND (f_subnivel IS NULL OR e.subnivel = ANY(f_subnivel)
        OR (e.subnivel IS NULL AND array_position(f_subnivel, NULL) IS NOT NULL))
   AND (f_curso_codigo IS NULL OR e.curso_codigo = ANY(f_curso_codigo)
        OR (e.curso_codigo IS NULL AND array_position(f_curso_codigo, NULL) IS NOT NULL))
   AND (f_curso IS NULL OR e.curso = ANY(f_curso)
        OR (e.curso IS NULL AND array_position(f_curso, NULL) IS NOT NULL))
   AND (f_habilitacao_codigo IS NULL OR e.habilitacao_codigo = ANY(f_habilitacao_codigo)
        OR (e.habilitacao_codigo IS NULL AND array_position(f_habilitacao_codigo, NULL) IS NOT NULL))
   AND (f_habilitacao IS NULL OR e.habilitacao = ANY(f_habilitacao)
        OR (e.habilitacao IS NULL AND array_position(f_habilitacao, NULL) IS NOT NULL))
   AND (f_turno IS NULL OR e.turno = ANY(f_turno)
        OR (e.turno IS NULL AND array_position(f_turno, NULL) IS NOT NULL))
   AND (f_forma_ingresso IS NULL OR e.forma_ingresso = ANY(f_forma_ingresso)
        OR (e.forma_ingresso IS NULL AND array_position(f_forma_ingresso, NULL) IS NOT NULL))
   AND (f_situacao_atual IS NULL OR e.situacao_atual = ANY(f_situacao_atual)
        OR (e.situacao_atual IS NULL AND array_position(f_situacao_atual, NULL) IS NOT NULL))
  GROUP BY e.periodo_eixo,e.indicador
 ) r;
 RETURN jsonb_build_object('origin','institucional_pseudonimizada','synthetic',false,
  'batch',p_carga,'rows',resultado,'unit','matriculas_distintas',
  'missing','ausencia_de_evento_nao_equivale_a_zero');
END; $$;
REVOKE ALL ON FUNCTION public.vrac_alunos_geral(uuid,text[],integer,integer,jsonb) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.vrac_alunos_geral(uuid,text[],integer,integer,jsonb) TO authenticated;
NOTIFY pgrst, 'reload schema';
