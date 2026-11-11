-- Mantém a autorização; explicita a subconsulta escalar sobre auth.jwt()
-- antes de extrair a claim, compatível com a verificação auth_rls_initplan.
ALTER POLICY leitura ON vrac_alunos.acessos USING (
 usuario_id = (SELECT auth.uid()) AND (SELECT vrac_app.active_session())
 AND COALESCE((SELECT auth.jwt())->>'is_anonymous','false') = 'false'
);
