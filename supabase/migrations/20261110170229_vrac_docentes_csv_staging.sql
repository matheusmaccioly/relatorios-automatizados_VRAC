-- Origem institucional pseudonimizada. Executar somente pelo operador autorizado.
-- Requer as duas migrações de autenticação existentes; não expor este schema na Data API.
CREATE SCHEMA vrac_docentes;
REVOKE ALL ON SCHEMA vrac_docentes FROM PUBLIC, anon, authenticated;
GRANT USAGE ON SCHEMA vrac_docentes TO authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA vrac_docentes REVOKE ALL ON TABLES FROM PUBLIC, anon, authenticated;
CREATE TABLE vrac_docentes.cargas (
 id uuid PRIMARY KEY,
 criado_em timestamptz NOT NULL DEFAULT now(),
 origem text NOT NULL DEFAULT 'institucional_pseudonimizada' CHECK (origem = 'institucional_pseudonimizada'),
 liberada boolean NOT NULL DEFAULT false
);
CREATE TABLE vrac_docentes.arquivos (
 carga_id uuid NOT NULL REFERENCES vrac_docentes.cargas(id),
 conjunto text NOT NULL,
 linhas bigint NOT NULL CHECK (linhas >= 0),
 hash_conteudo text NOT NULL CHECK (hash_conteudo ~ '^[0-9a-f]{64}$'),
 PRIMARY KEY (carga_id, conjunto)
);
CREATE TABLE vrac_docentes.acessos (
 usuario_id uuid NOT NULL REFERENCES auth.users(id),
 departamento_alocacao text NOT NULL CHECK (departamento_alocacao IN ('ADM','ECO','EDU','ELE','FIL','IND','INF','DIR')),
 PRIMARY KEY(usuario_id, departamento_alocacao)
);
CREATE TABLE vrac_docentes.cadastro (
 carga_id uuid NOT NULL REFERENCES vrac_docentes.cargas(id),
 linha bigint NOT NULL CHECK (linha > 0),
 pessoa_id text CHECK (pessoa_id ~ '^[0-9A-F]{64}$'),
 nome_ficticio text,
 vinculo_id text NOT NULL CHECK (vinculo_id ~ '^[0-9A-F]{64}$'),
 departamento_alocacao text NOT NULL CHECK (departamento_alocacao IN ('ADM','ECO','EDU','ELE','FIL','IND','INF','DIR')),
 quadro text,
 categoria text,
 situacao text,
 dupla_funcao text,
 carga_semanal numeric,
 PRIMARY KEY(carga_id, linha)
);
CREATE INDEX ON vrac_docentes.cadastro (carga_id, departamento_alocacao, linha);
CREATE INDEX ON vrac_docentes.cadastro (carga_id, departamento_alocacao, vinculo_id);
CREATE TABLE vrac_docentes.horas_reais (
 carga_id uuid NOT NULL REFERENCES vrac_docentes.cargas(id),
 linha bigint NOT NULL CHECK (linha > 0),
 departamento_alocacao text NOT NULL CHECK (departamento_alocacao IN ('ADM','ECO','EDU','ELE','FIL','IND','INF','DIR')),
 vinculo_id text NOT NULL CHECK (vinculo_id ~ '^[0-9A-F]{64}$'),
 semestre integer CHECK (semestre IN (20261,20262)),
 quadro text,
 horas_contratuais numeric,
 horas_reais numeric,
 PRIMARY KEY(carga_id, linha)
);
CREATE INDEX ON vrac_docentes.horas_reais (carga_id, departamento_alocacao, linha);
CREATE INDEX ON vrac_docentes.horas_reais (carga_id, departamento_alocacao, vinculo_id);
CREATE TABLE vrac_docentes.historico_mensal (
 carga_id uuid NOT NULL REFERENCES vrac_docentes.cargas(id),
 linha bigint NOT NULL CHECK (linha > 0),
 departamento_alocacao text NOT NULL CHECK (departamento_alocacao IN ('ADM','ECO','EDU','ELE','FIL','IND','INF','DIR')),
 vinculo_id text NOT NULL CHECK (vinculo_id ~ '^[0-9A-F]{64}$'),
 pessoa_id text CHECK (pessoa_id ~ '^[0-9A-F]{64}$'),
 ano integer,
 mes integer CHECK (mes BETWEEN 1 AND 12),
 lote text,
 ativo integer CHECK (ativo IN (0,1)),
 excluido_a4 integer CHECK (excluido_a4 IN (0,1)),
 carga_horaria numeric,
 PRIMARY KEY(carga_id, linha)
);
CREATE INDEX ON vrac_docentes.historico_mensal (carga_id, departamento_alocacao, linha);
CREATE INDEX ON vrac_docentes.historico_mensal (carga_id, departamento_alocacao, vinculo_id);
CREATE TABLE vrac_docentes.historico_cargos (
 carga_id uuid NOT NULL REFERENCES vrac_docentes.cargas(id),
 linha bigint NOT NULL CHECK (linha > 0),
 departamento_alocacao text NOT NULL CHECK (departamento_alocacao IN ('ADM','ECO','EDU','ELE','FIL','IND','INF','DIR')),
 vinculo_id text NOT NULL CHECK (vinculo_id ~ '^[0-9A-F]{64}$'),
 competencia text,
 categoria text,
 quadro text,
 PRIMARY KEY(carga_id, linha)
);
CREATE INDEX ON vrac_docentes.historico_cargos (carga_id, departamento_alocacao, linha);
CREATE INDEX ON vrac_docentes.historico_cargos (carga_id, departamento_alocacao, vinculo_id);
CREATE TABLE vrac_docentes.historico_carga (
 carga_id uuid NOT NULL REFERENCES vrac_docentes.cargas(id),
 linha bigint NOT NULL CHECK (linha > 0),
 departamento_alocacao text NOT NULL CHECK (departamento_alocacao IN ('ADM','ECO','EDU','ELE','FIL','IND','INF','DIR')),
 vinculo_id text NOT NULL CHECK (vinculo_id ~ '^[0-9A-F]{64}$'),
 ano integer,
 mes integer CHECK (mes BETWEEN 1 AND 12),
 carga_horaria numeric,
 PRIMARY KEY(carga_id, linha)
);
CREATE INDEX ON vrac_docentes.historico_carga (carga_id, departamento_alocacao, linha);
CREATE INDEX ON vrac_docentes.historico_carga (carga_id, departamento_alocacao, vinculo_id);
CREATE TABLE vrac_docentes.alocacoes (
 carga_id uuid NOT NULL REFERENCES vrac_docentes.cargas(id),
 linha bigint NOT NULL CHECK (linha > 0),
 departamento_alocacao text NOT NULL CHECK (departamento_alocacao IN ('ADM','ECO','EDU','ELE','FIL','IND','INF','DIR')),
 vinculo_id text NOT NULL CHECK (vinculo_id ~ '^[0-9A-F]{64}$'),
 semestre integer CHECK (semestre IN (20261,20262)),
 unidade_oferta text,
 disciplina_id text CHECK (disciplina_id ~ '^[0-9A-F]{64}$'),
 turma_id text CHECK (turma_id ~ '^[0-9A-F]{64}$'),
 nivel text,
 tipo text,
 obrigatoria text,
 horas_alocadas numeric,
 compartilhada text,
 vagas_ofertadas integer,
 vagas_preenchidas integer,
 professor_principal integer CHECK (professor_principal IN (0,1)),
 PRIMARY KEY(carga_id, linha)
);
CREATE INDEX ON vrac_docentes.alocacoes (carga_id, departamento_alocacao, linha);
CREATE INDEX ON vrac_docentes.alocacoes (carga_id, departamento_alocacao, vinculo_id);
CREATE TABLE vrac_docentes.eventos_funcoes (
 carga_id uuid NOT NULL REFERENCES vrac_docentes.cargas(id),
 linha bigint NOT NULL CHECK (linha > 0),
 departamento_alocacao text NOT NULL CHECK (departamento_alocacao IN ('ADM','ECO','EDU','ELE','FIL','IND','INF','DIR')),
 vinculo_id text NOT NULL CHECK (vinculo_id ~ '^[0-9A-F]{64}$'),
 evento_id text CHECK (evento_id ~ '^[0-9A-F]{64}$'),
 ano integer,
 mes integer CHECK (mes BETWEEN 1 AND 12),
 descricao_id text CHECK (descricao_id ~ '^[0-9A-F]{64}$'),
 papel_id text CHECK (papel_id ~ '^[0-9A-F]{64}$'),
 PRIMARY KEY(carga_id, linha)
);
CREATE INDEX ON vrac_docentes.eventos_funcoes (carga_id, departamento_alocacao, linha);
CREATE INDEX ON vrac_docentes.eventos_funcoes (carga_id, departamento_alocacao, vinculo_id);
ALTER TABLE vrac_docentes.cargas ENABLE ROW LEVEL SECURITY;
ALTER TABLE vrac_docentes.cargas FORCE ROW LEVEL SECURITY;
REVOKE ALL ON vrac_docentes.cargas FROM PUBLIC, anon, authenticated;
GRANT SELECT ON vrac_docentes.cargas TO authenticated;
CREATE POLICY leitura ON vrac_docentes.cargas FOR SELECT TO authenticated USING (
 (liberada AND EXISTS (SELECT 1 FROM vrac_docentes.acessos)) AND (SELECT vrac_app.active_session())
 AND COALESCE((SELECT auth.jwt()->>'is_anonymous'), 'false') = 'false'
);
ALTER TABLE vrac_docentes.arquivos ENABLE ROW LEVEL SECURITY;
ALTER TABLE vrac_docentes.arquivos FORCE ROW LEVEL SECURITY;
REVOKE ALL ON vrac_docentes.arquivos FROM PUBLIC, anon, authenticated;
ALTER TABLE vrac_docentes.acessos ENABLE ROW LEVEL SECURITY;
ALTER TABLE vrac_docentes.acessos FORCE ROW LEVEL SECURITY;
REVOKE ALL ON vrac_docentes.acessos FROM PUBLIC, anon, authenticated;
GRANT SELECT ON vrac_docentes.acessos TO authenticated;
CREATE POLICY leitura ON vrac_docentes.acessos FOR SELECT TO authenticated USING (
 (usuario_id = (SELECT auth.uid())) AND (SELECT vrac_app.active_session())
 AND COALESCE((SELECT auth.jwt()->>'is_anonymous'), 'false') = 'false'
);
ALTER TABLE vrac_docentes.cadastro ENABLE ROW LEVEL SECURITY;
ALTER TABLE vrac_docentes.cadastro FORCE ROW LEVEL SECURITY;
REVOKE ALL ON vrac_docentes.cadastro FROM PUBLIC, anon, authenticated;
GRANT SELECT ON vrac_docentes.cadastro TO authenticated;
CREATE POLICY leitura ON vrac_docentes.cadastro FOR SELECT TO authenticated USING (
 (EXISTS (SELECT 1 FROM vrac_docentes.acessos a WHERE a.departamento_alocacao = cadastro.departamento_alocacao)
 AND EXISTS (SELECT 1 FROM vrac_docentes.cargas c WHERE c.id = cadastro.carga_id)) AND (SELECT vrac_app.active_session())
 AND COALESCE((SELECT auth.jwt()->>'is_anonymous'), 'false') = 'false'
);
ALTER TABLE vrac_docentes.horas_reais ENABLE ROW LEVEL SECURITY;
ALTER TABLE vrac_docentes.horas_reais FORCE ROW LEVEL SECURITY;
REVOKE ALL ON vrac_docentes.horas_reais FROM PUBLIC, anon, authenticated;
GRANT SELECT ON vrac_docentes.horas_reais TO authenticated;
CREATE POLICY leitura ON vrac_docentes.horas_reais FOR SELECT TO authenticated USING (
 (EXISTS (SELECT 1 FROM vrac_docentes.acessos a WHERE a.departamento_alocacao = horas_reais.departamento_alocacao)
 AND EXISTS (SELECT 1 FROM vrac_docentes.cargas c WHERE c.id = horas_reais.carga_id)) AND (SELECT vrac_app.active_session())
 AND COALESCE((SELECT auth.jwt()->>'is_anonymous'), 'false') = 'false'
);
ALTER TABLE vrac_docentes.historico_mensal ENABLE ROW LEVEL SECURITY;
ALTER TABLE vrac_docentes.historico_mensal FORCE ROW LEVEL SECURITY;
REVOKE ALL ON vrac_docentes.historico_mensal FROM PUBLIC, anon, authenticated;
GRANT SELECT ON vrac_docentes.historico_mensal TO authenticated;
CREATE POLICY leitura ON vrac_docentes.historico_mensal FOR SELECT TO authenticated USING (
 (EXISTS (SELECT 1 FROM vrac_docentes.acessos a WHERE a.departamento_alocacao = historico_mensal.departamento_alocacao)
 AND EXISTS (SELECT 1 FROM vrac_docentes.cargas c WHERE c.id = historico_mensal.carga_id)) AND (SELECT vrac_app.active_session())
 AND COALESCE((SELECT auth.jwt()->>'is_anonymous'), 'false') = 'false'
);
ALTER TABLE vrac_docentes.historico_cargos ENABLE ROW LEVEL SECURITY;
ALTER TABLE vrac_docentes.historico_cargos FORCE ROW LEVEL SECURITY;
REVOKE ALL ON vrac_docentes.historico_cargos FROM PUBLIC, anon, authenticated;
GRANT SELECT ON vrac_docentes.historico_cargos TO authenticated;
CREATE POLICY leitura ON vrac_docentes.historico_cargos FOR SELECT TO authenticated USING (
 (EXISTS (SELECT 1 FROM vrac_docentes.acessos a WHERE a.departamento_alocacao = historico_cargos.departamento_alocacao)
 AND EXISTS (SELECT 1 FROM vrac_docentes.cargas c WHERE c.id = historico_cargos.carga_id)) AND (SELECT vrac_app.active_session())
 AND COALESCE((SELECT auth.jwt()->>'is_anonymous'), 'false') = 'false'
);
ALTER TABLE vrac_docentes.historico_carga ENABLE ROW LEVEL SECURITY;
ALTER TABLE vrac_docentes.historico_carga FORCE ROW LEVEL SECURITY;
REVOKE ALL ON vrac_docentes.historico_carga FROM PUBLIC, anon, authenticated;
GRANT SELECT ON vrac_docentes.historico_carga TO authenticated;
CREATE POLICY leitura ON vrac_docentes.historico_carga FOR SELECT TO authenticated USING (
 (EXISTS (SELECT 1 FROM vrac_docentes.acessos a WHERE a.departamento_alocacao = historico_carga.departamento_alocacao)
 AND EXISTS (SELECT 1 FROM vrac_docentes.cargas c WHERE c.id = historico_carga.carga_id)) AND (SELECT vrac_app.active_session())
 AND COALESCE((SELECT auth.jwt()->>'is_anonymous'), 'false') = 'false'
);
ALTER TABLE vrac_docentes.alocacoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE vrac_docentes.alocacoes FORCE ROW LEVEL SECURITY;
REVOKE ALL ON vrac_docentes.alocacoes FROM PUBLIC, anon, authenticated;
GRANT SELECT ON vrac_docentes.alocacoes TO authenticated;
CREATE POLICY leitura ON vrac_docentes.alocacoes FOR SELECT TO authenticated USING (
 (EXISTS (SELECT 1 FROM vrac_docentes.acessos a WHERE a.departamento_alocacao = alocacoes.departamento_alocacao)
 AND EXISTS (SELECT 1 FROM vrac_docentes.cargas c WHERE c.id = alocacoes.carga_id)) AND (SELECT vrac_app.active_session())
 AND COALESCE((SELECT auth.jwt()->>'is_anonymous'), 'false') = 'false'
);
ALTER TABLE vrac_docentes.eventos_funcoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE vrac_docentes.eventos_funcoes FORCE ROW LEVEL SECURITY;
REVOKE ALL ON vrac_docentes.eventos_funcoes FROM PUBLIC, anon, authenticated;
GRANT SELECT ON vrac_docentes.eventos_funcoes TO authenticated;
CREATE POLICY leitura ON vrac_docentes.eventos_funcoes FOR SELECT TO authenticated USING (
 (EXISTS (SELECT 1 FROM vrac_docentes.acessos a WHERE a.departamento_alocacao = eventos_funcoes.departamento_alocacao)
 AND EXISTS (SELECT 1 FROM vrac_docentes.cargas c WHERE c.id = eventos_funcoes.carga_id)) AND (SELECT vrac_app.active_session())
 AND COALESCE((SELECT auth.jwt()->>'is_anonymous'), 'false') = 'false'
);
-- Paginação por ordinal; nenhuma consulta arbitrária ou inferência analítica.
CREATE FUNCTION public.vrac_docentes_page(p_carga uuid, p_conjunto text, p_departamento text,
 p_apos bigint DEFAULT 0, p_limite integer DEFAULT 1000)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path = '' AS $$
DECLARE resultado jsonb;
BEGIN
 IF p_limite IS NULL OR p_limite NOT BETWEEN 1 AND 1000 OR p_apos IS NULL OR p_apos < 0
 OR p_departamento IS NULL OR p_conjunto IS NULL OR p_carga IS NULL
 OR NOT EXISTS (SELECT 1 FROM vrac_docentes.acessos WHERE departamento_alocacao = p_departamento)
 OR NOT EXISTS (SELECT 1 FROM vrac_docentes.cargas WHERE id = p_carga)
 THEN RAISE EXCEPTION 'Carga ou recorte indisponível' USING ERRCODE = '42501'; END IF;
 CASE p_conjunto
 WHEN 'cadastro' THEN
 SELECT COALESCE(jsonb_agg(to_jsonb(r) - 'carga_id' ORDER BY linha), '[]'::jsonb) INTO resultado
 FROM (SELECT * FROM vrac_docentes.cadastro
 WHERE carga_id = p_carga AND departamento_alocacao = p_departamento AND linha > p_apos
 ORDER BY linha LIMIT p_limite) r;
 WHEN 'horas_reais' THEN
 SELECT COALESCE(jsonb_agg(to_jsonb(r) - 'carga_id' ORDER BY linha), '[]'::jsonb) INTO resultado
 FROM (SELECT * FROM vrac_docentes.horas_reais
 WHERE carga_id = p_carga AND departamento_alocacao = p_departamento AND linha > p_apos
 ORDER BY linha LIMIT p_limite) r;
 WHEN 'historico_mensal' THEN
 SELECT COALESCE(jsonb_agg(to_jsonb(r) - 'carga_id' ORDER BY linha), '[]'::jsonb) INTO resultado
 FROM (SELECT * FROM vrac_docentes.historico_mensal
 WHERE carga_id = p_carga AND departamento_alocacao = p_departamento AND linha > p_apos
 ORDER BY linha LIMIT p_limite) r;
 WHEN 'historico_cargos' THEN
 SELECT COALESCE(jsonb_agg(to_jsonb(r) - 'carga_id' ORDER BY linha), '[]'::jsonb) INTO resultado
 FROM (SELECT * FROM vrac_docentes.historico_cargos
 WHERE carga_id = p_carga AND departamento_alocacao = p_departamento AND linha > p_apos
 ORDER BY linha LIMIT p_limite) r;
 WHEN 'historico_carga' THEN
 SELECT COALESCE(jsonb_agg(to_jsonb(r) - 'carga_id' ORDER BY linha), '[]'::jsonb) INTO resultado
 FROM (SELECT * FROM vrac_docentes.historico_carga
 WHERE carga_id = p_carga AND departamento_alocacao = p_departamento AND linha > p_apos
 ORDER BY linha LIMIT p_limite) r;
 WHEN 'alocacoes' THEN
 SELECT COALESCE(jsonb_agg(to_jsonb(r) - 'carga_id' ORDER BY linha), '[]'::jsonb) INTO resultado
 FROM (SELECT * FROM vrac_docentes.alocacoes
 WHERE carga_id = p_carga AND departamento_alocacao = p_departamento AND linha > p_apos
 ORDER BY linha LIMIT p_limite) r;
 WHEN 'eventos_funcoes' THEN
 SELECT COALESCE(jsonb_agg(to_jsonb(r) - 'carga_id' ORDER BY linha), '[]'::jsonb) INTO resultado
 FROM (SELECT * FROM vrac_docentes.eventos_funcoes
 WHERE carga_id = p_carga AND departamento_alocacao = p_departamento AND linha > p_apos
 ORDER BY linha LIMIT p_limite) r;
 ELSE RAISE EXCEPTION 'Conjunto indisponível' USING ERRCODE = '22023';
 END CASE;
 RETURN jsonb_build_object('origin','institucional_pseudonimizada','synthetic',false,
 'batch',p_carga,'component',p_conjunto,'rows',resultado);
END; $$;
REVOKE ALL ON FUNCTION public.vrac_docentes_page(uuid,text,text,bigint,integer) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.vrac_docentes_page(uuid,text,text,bigint,integer) TO authenticated;
NOTIFY pgrst, 'reload schema';
