-- Layout docente v2 (11/11/2026): colunas dos painéis de referência, todas opcionais.
-- Cargas anteriores continuam válidas com NULL nas novas colunas (ausência, não zero).
-- RLS, RPCs e permissões não mudam: vrac_docentes_rows devolve to_jsonb(linha) e o
-- leitor confere o conjunto exato de colunas de cada layout.
-- Pessoa e vínculo seguem pseudonimizados; disciplina, turma e gratificação são
-- nomes de catálogo/folha, não dados pessoais (decisão de Matheus em 11/11/2026).

ALTER TABLE vrac_docentes.cadastro
 ADD COLUMN titulacao text,
 ADD COLUMN tempo_casa_anos numeric CHECK (tempo_casa_anos IS NULL OR tempo_casa_anos >= 0),
 ADD COLUMN vinculo_extraordinario text;

ALTER TABLE vrac_docentes.alocacoes
 ADD COLUMN disciplina_codigo text,
 ADD COLUMN disciplina_nome text,
 ADD COLUMN turma text,
 ADD COLUMN creditos numeric CHECK (creditos IS NULL OR creditos >= 0),
 ADD COLUMN horas_distancia numeric CHECK (horas_distancia IS NULL OR horas_distancia >= 0),
 ADD COLUMN horas_extensao numeric CHECK (horas_extensao IS NULL OR horas_extensao >= 0);

ALTER TABLE vrac_docentes.eventos_funcoes
 ADD COLUMN gratificacao text,
 ADD COLUMN papel text,
 ADD COLUMN departamento_distribuicao text;

NOTIFY pgrst, 'reload schema';
