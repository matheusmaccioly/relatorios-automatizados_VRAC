-- Análise Geral: eventos classificados na extração; matrícula não é pessoa única.
-- Requer migrações anteriores de autenticação. Não libera cargas nem concede escopos.
CREATE SCHEMA vrac_alunos;
REVOKE ALL ON SCHEMA vrac_alunos FROM PUBLIC, anon, authenticated;
GRANT USAGE ON SCHEMA vrac_alunos TO authenticated;

CREATE TABLE vrac_alunos.cargas (
 id uuid PRIMARY KEY,
 criada_em timestamptz NOT NULL DEFAULT now(),
 origem text NOT NULL DEFAULT 'institucional_pseudonimizada'
  CHECK (origem = 'institucional_pseudonimizada'),
 liberada boolean NOT NULL DEFAULT false,
 periodo_inicio integer NOT NULL CHECK (periodo_inicio BETWEEN 10001 AND 99992 AND periodo_inicio % 10 IN (1,2)),
 periodo_fim integer NOT NULL CHECK (periodo_fim BETWEEN 10001 AND 99992 AND periodo_fim % 10 IN (1,2)),
 linhas bigint NOT NULL CHECK (linhas > 0),
 hash_conteudo text NOT NULL CHECK (hash_conteudo ~ '^[0-9a-f]{64}$'),
 encoding text NOT NULL CHECK (encoding IN ('utf-8-sig','utf-16','cp1252')),
 marcador_nulo text NOT NULL CHECK (length(btrim(marcador_nulo)) > 0 AND marcador_nulo NOT IN ('0','1')),
 ajustes_individuais_informados integer NOT NULL CHECK (ajustes_individuais_informados >= 0),
 CHECK (periodo_inicio <= periodo_fim)
);
CREATE TABLE vrac_alunos.acessos (
 usuario_id uuid NOT NULL REFERENCES auth.users(id),
 departamento_curso text NOT NULL CHECK (departamento_curso IN ('ADM','ECO','EDU','ELE','FIL','IND','INF','DIR')),
 PRIMARY KEY (usuario_id, departamento_curso)
);
CREATE TABLE vrac_alunos.eventos (
 carga_id uuid NOT NULL REFERENCES vrac_alunos.cargas(id),
 linha bigint NOT NULL CHECK (linha > 0),
 indicador text NOT NULL CHECK (indicador IN ('MATRICULADOS','BOLSISTAS_MATRICULADOS','FORMADOS','INGRESSANTES')),
 periodo_eixo integer NOT NULL CHECK (periodo_eixo BETWEEN 10001 AND 99992 AND periodo_eixo % 10 IN (1,2)),
 periodo_linha integer NOT NULL CHECK (periodo_linha BETWEEN 10001 AND 99992 AND periodo_linha % 10 IN (1,2)),
 aluno_id text NOT NULL CHECK (aluno_id ~ '^[0-9A-F]{64}$'),
 departamento_curso text NOT NULL CHECK (departamento_curso IN ('ADM','ECO','EDU','ELE','FIL','IND','INF','DIR')),
 sigla_centro text, centro text, nivel text, subnivel text,
 curso_codigo text, curso text, habilitacao_codigo text, habilitacao text,
 turno text, forma_ingresso text, situacao_atual text,
 ingresso_cadastro_nulo integer NOT NULL CHECK (ingresso_cadastro_nulo IN (0,1)),
 ajustes_individuais_informados integer NOT NULL CHECK (ajustes_individuais_informados >= 0),
 PRIMARY KEY (carga_id, linha),
 CHECK (indicador = 'INGRESSANTES' OR periodo_eixo = periodo_linha),
 CHECK (indicador IN ('MATRICULADOS','BOLSISTAS_MATRICULADOS') OR ingresso_cadastro_nulo = 0)
);
CREATE INDEX eventos_recorte ON vrac_alunos.eventos
 (carga_id, departamento_curso, periodo_eixo, indicador, aluno_id);

ALTER TABLE vrac_alunos.cargas ENABLE ROW LEVEL SECURITY;
ALTER TABLE vrac_alunos.cargas FORCE ROW LEVEL SECURITY;
ALTER TABLE vrac_alunos.acessos ENABLE ROW LEVEL SECURITY;
ALTER TABLE vrac_alunos.acessos FORCE ROW LEVEL SECURITY;
ALTER TABLE vrac_alunos.eventos ENABLE ROW LEVEL SECURITY;
ALTER TABLE vrac_alunos.eventos FORCE ROW LEVEL SECURITY;
REVOKE ALL ON ALL TABLES IN SCHEMA vrac_alunos FROM PUBLIC, anon, authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA vrac_alunos TO authenticated;
CREATE POLICY leitura ON vrac_alunos.acessos FOR SELECT TO authenticated USING (
 usuario_id = (SELECT auth.uid()) AND (SELECT vrac_app.active_session())
 AND COALESCE((SELECT auth.jwt()->>'is_anonymous'),'false') = 'false'
);
CREATE POLICY leitura ON vrac_alunos.cargas FOR SELECT TO authenticated USING (
 liberada AND EXISTS (SELECT 1 FROM vrac_alunos.acessos)
);
CREATE POLICY leitura ON vrac_alunos.eventos FOR SELECT TO authenticated USING (
 EXISTS (SELECT 1 FROM vrac_alunos.cargas c WHERE c.id = carga_id)
 AND EXISTS (SELECT 1 FROM vrac_alunos.acessos a WHERE a.departamento_curso = eventos.departamento_curso)
);

-- API fechada: filtros dimensionais de valor único ou NULL explícito; {} = Todos.
-- Sem preenchimento automático de ausências com zero e sem soma entre cursos/semestres.
CREATE FUNCTION public.vrac_alunos_geral(
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
  OR jsonb_typeof(f.value) NOT IN ('string','null'))
 THEN RAISE EXCEPTION 'Filtro indisponível' USING ERRCODE = '22023'; END IF;
 SELECT COALESCE(jsonb_agg(to_jsonb(r) ORDER BY r.periodo_eixo,r.indicador),'[]'::jsonb)
 INTO resultado FROM (
  SELECT e.periodo_eixo, e.indicador, count(DISTINCT e.aluno_id) AS quantidade
  FROM vrac_alunos.eventos e
  WHERE e.carga_id = p_carga AND e.departamento_curso = ANY(p_departamentos)
   AND e.periodo_eixo BETWEEN p_inicio AND p_fim
   AND NOT EXISTS (SELECT 1 FROM jsonb_each_text(p_filtros) f
    WHERE (to_jsonb(e)->>f.key) IS DISTINCT FROM f.value)
  GROUP BY e.periodo_eixo,e.indicador
 ) r;
 RETURN jsonb_build_object('origin','institucional_pseudonimizada','synthetic',false,
  'batch',p_carga,'rows',resultado,'unit','matriculas_distintas',
  'missing','ausencia_de_evento_nao_equivale_a_zero');
END; $$;
REVOKE ALL ON FUNCTION public.vrac_alunos_geral(uuid,text[],integer,integer,jsonb) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.vrac_alunos_geral(uuid,text[],integer,integer,jsonb) TO authenticated;
NOTIFY pgrst, 'reload schema';
