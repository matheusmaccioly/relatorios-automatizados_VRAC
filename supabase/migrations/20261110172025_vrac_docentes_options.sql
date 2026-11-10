-- Opções autorizadas para a origem institucional, sem consultar a base sintética.
CREATE FUNCTION public.vrac_docentes_options() RETURNS jsonb
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = '' AS $$
WITH carga AS (
 SELECT id FROM vrac_docentes.cargas ORDER BY criado_em DESC, id DESC LIMIT 1
), periodos AS (
 SELECT semestre FROM vrac_docentes.horas_reais WHERE carga_id = (SELECT id FROM carga)
 UNION
 SELECT ano * 10 + CASE WHEN mes <= 7 THEN 1 ELSE 2 END
 FROM vrac_docentes.historico_mensal WHERE carga_id = (SELECT id FROM carga)
)
SELECT jsonb_build_object(
 'synthetic',false,'origin','institucional_pseudonimizada',
 'batch',(SELECT id FROM carga),
 'departments',(SELECT COALESCE(jsonb_agg(departamento_alocacao ORDER BY departamento_alocacao),'[]'::jsonb)
                FROM vrac_docentes.acessos),
 'periods',(SELECT COALESCE(jsonb_agg((semestre/10)::text || '.' || (semestre%10)::text ORDER BY semestre),'[]'::jsonb)
            FROM periodos WHERE semestre IS NOT NULL)
);
$$;
REVOKE ALL ON FUNCTION public.vrac_docentes_options() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.vrac_docentes_options() TO authenticated;
NOTIFY pgrst, 'reload schema';

CREATE FUNCTION public.vrac_docentes_rows(p_carga uuid, p_conjunto text, p_departamentos text[],
 p_apos bigint DEFAULT 0, p_limite integer DEFAULT 1000)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path = '' AS $$
DECLARE resultado jsonb;
BEGIN
 IF p_limite IS NULL OR p_limite NOT BETWEEN 1 AND 1000 OR p_apos IS NULL OR p_apos < 0
 OR p_departamentos IS NULL OR cardinality(p_departamentos) NOT BETWEEN 1 AND 8
 OR p_conjunto IS NULL OR p_carga IS NULL
 OR EXISTS (SELECT 1 FROM unnest(p_departamentos) d WHERE d IS NULL OR NOT EXISTS
 (SELECT 1 FROM vrac_docentes.acessos a WHERE a.departamento_alocacao=d))
 OR NOT EXISTS (SELECT 1 FROM vrac_docentes.cargas WHERE id = p_carga)
 THEN RAISE EXCEPTION 'Carga ou recorte indisponível' USING ERRCODE = '42501'; END IF;
 CASE p_conjunto
 WHEN 'cadastro' THEN
 SELECT COALESCE(jsonb_agg(to_jsonb(r) - 'carga_id' ORDER BY linha), '[]'::jsonb) INTO resultado
 FROM (SELECT * FROM vrac_docentes.cadastro
 WHERE carga_id = p_carga AND departamento_alocacao = ANY(p_departamentos) AND linha > p_apos
 ORDER BY linha LIMIT p_limite) r;
 WHEN 'horas_reais' THEN
 SELECT COALESCE(jsonb_agg(to_jsonb(r) - 'carga_id' ORDER BY linha), '[]'::jsonb) INTO resultado
 FROM (SELECT * FROM vrac_docentes.horas_reais
 WHERE carga_id = p_carga AND departamento_alocacao = ANY(p_departamentos) AND linha > p_apos
 ORDER BY linha LIMIT p_limite) r;
 WHEN 'historico_mensal' THEN
 SELECT COALESCE(jsonb_agg(to_jsonb(r) - 'carga_id' ORDER BY linha), '[]'::jsonb) INTO resultado
 FROM (SELECT * FROM vrac_docentes.historico_mensal
 WHERE carga_id = p_carga AND departamento_alocacao = ANY(p_departamentos) AND linha > p_apos
 ORDER BY linha LIMIT p_limite) r;
 WHEN 'historico_cargos' THEN
 SELECT COALESCE(jsonb_agg(to_jsonb(r) - 'carga_id' ORDER BY linha), '[]'::jsonb) INTO resultado
 FROM (SELECT * FROM vrac_docentes.historico_cargos
 WHERE carga_id = p_carga AND departamento_alocacao = ANY(p_departamentos) AND linha > p_apos
 ORDER BY linha LIMIT p_limite) r;
 WHEN 'historico_carga' THEN
 SELECT COALESCE(jsonb_agg(to_jsonb(r) - 'carga_id' ORDER BY linha), '[]'::jsonb) INTO resultado
 FROM (SELECT * FROM vrac_docentes.historico_carga
 WHERE carga_id = p_carga AND departamento_alocacao = ANY(p_departamentos) AND linha > p_apos
 ORDER BY linha LIMIT p_limite) r;
 WHEN 'alocacoes' THEN
 SELECT COALESCE(jsonb_agg(to_jsonb(r) - 'carga_id' ORDER BY linha), '[]'::jsonb) INTO resultado
 FROM (SELECT * FROM vrac_docentes.alocacoes
 WHERE carga_id = p_carga AND departamento_alocacao = ANY(p_departamentos) AND linha > p_apos
 ORDER BY linha LIMIT p_limite) r;
 WHEN 'eventos_funcoes' THEN
 SELECT COALESCE(jsonb_agg(to_jsonb(r) - 'carga_id' ORDER BY linha), '[]'::jsonb) INTO resultado
 FROM (SELECT * FROM vrac_docentes.eventos_funcoes
 WHERE carga_id = p_carga AND departamento_alocacao = ANY(p_departamentos) AND linha > p_apos
 ORDER BY linha LIMIT p_limite) r;
 ELSE RAISE EXCEPTION 'Conjunto indisponível' USING ERRCODE = '22023';
 END CASE;
 RETURN jsonb_build_object('origin','institucional_pseudonimizada','synthetic',false,
 'batch',p_carga,'component',p_conjunto,'rows',resultado);
END; $$;
REVOKE ALL ON FUNCTION public.vrac_docentes_rows(uuid,text,text[],bigint,integer) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.vrac_docentes_rows(uuid,text,text[],bigint,integer) TO authenticated;
NOTIFY pgrst, 'reload schema';
