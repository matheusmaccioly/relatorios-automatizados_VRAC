-- Opções de filtro de alunos pré-calculadas por lote e departamento (11/11/2026).
-- Motivo: com Direito, a expansão dos eventos em vrac_alunos_filters chegou a ~7 s
-- sem RLS, perto do limite de 8 s do papel authenticated. Mesmo resultado, mesma RLS
-- dos eventos, mesma assinatura e mesmo formato de resposta da RPC.

CREATE TABLE vrac_alunos.opcoes_filtros (
 carga_id uuid NOT NULL REFERENCES vrac_alunos.cargas(id),
 departamento_curso text NOT NULL CHECK (departamento_curso IN ('ADM','ECO','EDU','ELE','FIL','IND','INF','DIR')),
 chave text NOT NULL CHECK (chave IN ('sigla_centro','nivel','subnivel','curso_codigo','curso',
  'habilitacao_codigo','habilitacao','turno','forma_ingresso','situacao_atual')),
 valor text,
 UNIQUE NULLS NOT DISTINCT (carga_id, departamento_curso, chave, valor)
);
ALTER TABLE vrac_alunos.opcoes_filtros ENABLE ROW LEVEL SECURITY;
ALTER TABLE vrac_alunos.opcoes_filtros FORCE ROW LEVEL SECURITY;
REVOKE ALL ON vrac_alunos.opcoes_filtros FROM PUBLIC, anon, authenticated;
GRANT SELECT ON vrac_alunos.opcoes_filtros TO authenticated;
CREATE POLICY leitura ON vrac_alunos.opcoes_filtros FOR SELECT TO authenticated USING (
 EXISTS (SELECT 1 FROM vrac_alunos.cargas c WHERE c.id = opcoes_filtros.carga_id)
 AND EXISTS (SELECT 1 FROM vrac_alunos.acessos a
  WHERE a.departamento_curso = opcoes_filtros.departamento_curso)
);

-- Uma única definição do preenchimento, usada aqui e pelo carregador de novos lotes.
CREATE FUNCTION vrac_alunos.preencher_opcoes_filtros(p_carga uuid) RETURNS bigint
LANGUAGE sql SET search_path = '' AS $$
 WITH inseridas AS (
  INSERT INTO vrac_alunos.opcoes_filtros (carga_id, departamento_curso, chave, valor)
  SELECT DISTINCT e.carga_id, e.departamento_curso, f.key, f.value
  FROM (
   SELECT DISTINCT carga_id, departamento_curso, sigla_centro, nivel, subnivel, curso_codigo,
    curso, habilitacao_codigo, habilitacao, turno, forma_ingresso, situacao_atual
   FROM vrac_alunos.eventos WHERE carga_id = p_carga
  ) e CROSS JOIN LATERAL jsonb_each_text(jsonb_build_object(
   'sigla_centro',e.sigla_centro,'nivel',e.nivel,'subnivel',e.subnivel,
   'curso_codigo',e.curso_codigo,'curso',e.curso,'habilitacao_codigo',e.habilitacao_codigo,
   'habilitacao',e.habilitacao,'turno',e.turno,'forma_ingresso',e.forma_ingresso,
   'situacao_atual',e.situacao_atual)) f
  ON CONFLICT DO NOTHING
  RETURNING 1
 ) SELECT count(*) FROM inseridas;
$$;
REVOKE ALL ON FUNCTION vrac_alunos.preencher_opcoes_filtros(uuid) FROM PUBLIC, anon, authenticated;

SELECT vrac_alunos.preencher_opcoes_filtros(id) FROM vrac_alunos.cargas;

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
 -- jsonb ordena null antes de textos e textos pela collation padrão: NULLS FIRST + text.
 SELECT COALESCE(jsonb_object_agg(chave,opcoes),'{}'::jsonb) INTO resultado
 FROM (
  SELECT chave, jsonb_agg(to_jsonb(valor) ORDER BY valor NULLS FIRST) opcoes
  FROM (
   SELECT DISTINCT o.chave, o.valor FROM vrac_alunos.opcoes_filtros o
   WHERE o.carga_id=p_carga AND o.departamento_curso=ANY(p_departamentos)
  ) d
  GROUP BY chave
 ) r;
 RETURN jsonb_build_object('origin','institucional_pseudonimizada','synthetic',false,
  'batch',p_carga,'filters',resultado);
END; $$;
REVOKE ALL ON FUNCTION public.vrac_alunos_filters(uuid,text[]) FROM PUBLIC,anon;
GRANT EXECUTE ON FUNCTION public.vrac_alunos_filters(uuid,text[]) TO authenticated;

NOTIFY pgrst, 'reload schema';
