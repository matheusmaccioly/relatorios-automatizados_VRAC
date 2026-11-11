"""Integração institucional testada exclusivamente com registros fictícios."""

import io
import json
import time
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import pytest
from streamlit.testing.v1 import AppTest

from vrac.analyses.academic import AnalysisFilters, AnalysisKind, calculate
from vrac.analyses.academic_export import report_zip, table_csv
from vrac.analyses.export import detail_csv
from vrac.analyses.faculty_overview import OverviewFilters, compute_overview
from vrac.authorization import authorize_data_access
from vrac.db.institutional_faculty import adapt
from vrac.provenance import INSTITUTIONAL_SOURCE
from vrac.settings import DataMode, DemoSource, Settings
from vrac.supabase_auth import SupabaseSession, session_scope, verify_session

BATCH = "10000000-0000-4000-8000-000000000009"
LINK = "A" * 64
PERSON = "B" * 64
SETTINGS = Settings(data_mode=DataMode.PSEUDONYMIZED, demo_source=DemoSource.SUPABASE)
FILTERS = AnalysisFilters("2026.1", "2026.2", "2026.1")


@pytest.fixture
def parts():
    return {
        "cadastro": [
            dict(
                pessoa_id=PERSON,
                nome_ficticio="Docente exemplo",
                vinculo_id=LINK,
                departamento_alocacao="IND",
                quadro="PROF PRINCIPAL",
                categoria="C1",
                situacao="ATIVO",
                dupla_funcao="N",
                carga_semanal=40,
                titulacao=None,
                tempo_casa_anos=None,
                vinculo_extraordinario=None,
            )
        ],
        "horas_reais": [
            dict(
                departamento_alocacao="IND",
                vinculo_id=LINK,
                semestre=20261,
                quadro="PRINCIPAL",
                horas_contratuais=40,
                horas_reais=0,
            ),
            dict(
                departamento_alocacao="IND",
                vinculo_id=LINK,
                semestre=20262,
                quadro="PRINCIPAL",
                horas_contratuais=40,
                horas_reais=None,
            ),
        ],
        "historico_mensal": [
            dict(
                departamento_alocacao="IND",
                vinculo_id=LINK,
                pessoa_id=PERSON,
                ano=2026,
                mes=m,
                lote="3",
                ativo=1,
                excluido_a4=0,
                carga_horaria=40,
            )
            for m in (1, 1, 7, 8)
        ],
        "historico_cargos": [
            dict(
                departamento_alocacao="IND",
                vinculo_id=LINK,
                competencia="202500",
                quadro="PROF PRINCIPAL",
                categoria="C0",
            )
        ],
        "alocacoes": [],
        "eventos_funcoes": [],
    }


def source(parts):
    return adapt(parts, department="IND", batch=BATCH, periods=("2026.1", "2026.2"))


def test_opaque_links_null_zero_and_no_invented_fields(parts):
    data = source(parts)
    assert data.faculty.register[0].registration_int is None
    assert data.faculty.register[0].link_key == LINK
    overview = compute_overview(data.faculty, OverviewFilters())
    assert overview.total == 1
    assert (
        overview.detail[0].real_hours is None
    )  # último semestre nulo, não reutiliza zero anterior
    assert overview.detail[0].real_hours_semester == "2026.2"
    assert data.workloads[0].real_hours == 0
    assert data.faculty.register[0].degree is None
    assert data.faculty.source == INSTITUTIONAL_SOURCE


def test_numeric_competence_and_distinct_people_not_sum(parts):
    data = source(parts)
    assert "history" in data.available
    assert data.history[0].category == "C0"  # antecedente, não C1 do cadastro atual
    result = calculate(AnalysisKind.HISTORY, data, FILTERS)
    table = next(t for t in result.tables if t.key == "history")
    assert table.rows[0][1] == 1
    assert any("coorte" in note.lower() for note in result.notes)


def test_conflicting_cargo_blocks_only_history(parts):
    parts["historico_cargos"].append(dict(parts["historico_cargos"][0], categoria="OUTRA"))
    data = source(parts)
    assert calculate(AnalysisKind.HISTORY, data, FILTERS).status == "Bloqueado"
    assert compute_overview(data.faculty, OverviewFilters()).total == 1
    assert calculate(AnalysisKind.WORKLOAD, data, FILTERS).status != "Bloqueado"
    assert calculate(AnalysisKind.STUDENTS, data, FILTERS).status == "Bloqueado"


def test_csv_zip_and_pdf_identify_institutional_source(parts):
    from matplotlib import pyplot as plt
    from PIL import Image
    from pypdf import PdfReader

    from vrac.analyses.pdf_export import report_pdf
    from vrac.branding import load_branding
    from vrac.charts import academic_chart, figure_png

    data = source(parts)
    now = datetime.now(UTC)
    result = calculate(AnalysisKind.WORKLOAD, data, FILTERS)
    encoded = table_csv(result, result.tables[0], now).decode("utf-8-sig")
    assert "INSTITUCIONAIS PSEUDONIMIZADOS" in encoded
    assert "DADOS SINTÉTICOS" not in encoded
    overview = compute_overview(data.faculty, OverviewFilters())
    assert "Vínculo pseudonimizado" in detail_csv(overview, now).decode("utf-8-sig")
    package = report_zip([result], now)
    with ZipFile(io.BytesIO(package)) as archive:
        assert json.loads(archive.read("manifesto.json"))["synthetic"] is False
    pdf = report_pdf(package, load_branding(), selected=("R04",))
    text = "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages)
    assert "INSTITUCIONAL PSEUDONIMIZADA" in text
    assert "DADOS SINTÉTICOS" not in text
    for chart in result.charts:
        figure = academic_chart(result, chart, load_branding())
        try:
            assert not any("DADOS SINTÉTICOS" in t.get_text() for t in figure.texts)
            image = Image.open(io.BytesIO(figure_png(figure)))
            assert "PSEUDONIMIZADOS" in image.info["Description"]
        finally:
            plt.close(figure)


class Client:
    def __init__(self, parts):
        self.parts = parts
        self.allowed = ["IND"]
        self.fail = False
        self.calls = []
        self.auth = SimpleNamespace(
            get_user=lambda token: SimpleNamespace(
                user=SimpleNamespace(id="test", is_anonymous=False)
            )
        )
        self.postgrest = SimpleNamespace(auth=lambda token: None)

    def rpc(self, name, params=None):
        self.calls.append(name)
        if self.fail:
            raise RuntimeError("private error")
        if name == "vrac_docentes_options":
            data = dict(
                synthetic=False,
                origin="institucional_pseudonimizada",
                batch=BATCH,
                departments=self.allowed,
                periods=["2026.1", "2026.2"],
            )
        elif name == "vrac_docentes_rows":
            assert set(params["p_departamentos"]) <= set(self.allowed)
            rows = [
                dict(r, linha=i)
                for i, r in enumerate(self.parts[params["p_conjunto"]], 1)
                if i > params["p_apos"]
            ]
            data = dict(
                synthetic=False,
                origin="institucional_pseudonimizada",
                batch=BATCH,
                component=params["p_conjunto"],
                rows=rows[:1000],
            )
        else:
            raise AssertionError("Consulta de outra origem: " + name)
        return SimpleNamespace(execute=lambda: SimpleNamespace(data=data))


def identity(parts):
    return SupabaseSession(
        Client(parts),
        "test",
        "access-fixture",
        "refresh-fixture",
        time.time() + 3600,
        project_url="https://example.supabase.co",
        data_mode=DataMode.PSEUDONYMIZED,
    )


def test_auth_does_not_reuse_synthetic_permissions_and_no_fallback(parts):
    from vrac.demo_data import DemoDataError, load_faculty_source

    session = identity(parts)
    verify_session(session)
    with session_scope(session):
        assert authorize_data_access(SETTINGS).allowed
        assert not authorize_data_access(Settings(demo_source=DemoSource.SUPABASE)).allowed
        assert load_faculty_source(SETTINGS, department="IND").register[0].link_key == LINK
        session.client.fail = True
        with pytest.raises(DemoDataError):
            load_faculty_source(SETTINGS, department="IND")
    assert "vrac_snapshot" not in session.client.calls
    assert "vrac_options" not in session.client.calls


def test_institutional_screen_calculates_without_synthetic_labels(monkeypatch, parts):
    monkeypatch.setenv("VRAC_DEMO_SOURCE", "supabase")
    monkeypatch.setenv("VRAC_DATA_MODE", "pseudonymized")
    session = identity(deepcopy(parts))
    verify_session(session)
    monkeypatch.setattr("vrac.auth_ui.require_login", lambda mode: session)
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30
    ).run()
    assert not app.exception
    app.button(key="overview_run").click().run()
    assert not app.exception
    assert app.session_state["overview_result"].total == 1
    captions = "\n".join(x.value for x in app.caption)
    assert "Dados fictícios" not in captions
    assert "DADOS SINTÉTICOS" not in captions
    assert any("PSEUDONIMIZADOS" in x.value for x in app.warning)
    # Sem seletor de origem: na hospedagem, a fonte é sempre a pseudonimizada.
    assert not any(box.label == "Origem dos dados" for box in app.selectbox)
    captured = {}
    from vrac import academic_ui

    original = academic_ui.report_zip

    def capture(*args, **kwargs):
        captured["results"] = args[0]
        captured["zip"] = original(*args, **kwargs)
        return captured["zip"]

    monkeypatch.setattr(academic_ui, "report_zip", capture)
    # Relatório completo em um clique no Início: calcula, empacota e entrega o PDF.
    app.button(key="home_complete").click().run(timeout=60)
    assert not app.exception and not app.error
    assert app.session_state["vrac-view"] == "Início"
    results = captured["results"]
    assert all(r.source == INSTITUTIONAL_SOURCE for r in results)
    assert next(r for r in results if r.kind == AnalysisKind.STUDENTS).status == "Bloqueado"
    with ZipFile(io.BytesIO(captured["zip"])) as archive:
        manifest = json.loads(archive.read("manifesto.json"))
        assert manifest["synthetic"] is False
        assert manifest["context"]["Origem"] == INSTITUTIONAL_SOURCE
        assert "PSEUDONIMIZADOS" in archive.read("R01/resumo.csv").decode("utf-8-sig")


def test_source_switch_clears_results_files_and_feedback(monkeypatch, parts):
    from vrac.supabase_auth import SupabaseConfig

    session = identity(parts)
    verify_session(session)
    monkeypatch.setattr(
        "vrac.auth_ui.load_supabase_config",
        lambda: SupabaseConfig("https://example.supabase.co", "sb_publishable_fixture"),
    )

    def verify(s):
        s.departments = ("IND",) if s.data_mode == DataMode.PSEUDONYMIZED else ("SINT",)
        s.batch = BATCH if s.data_mode == DataMode.PSEUDONYMIZED else ""
        s.verified_until = time.time() + 900

    monkeypatch.setattr("vrac.auth_ui.verify_session", verify)
    app = AppTest.from_string("""
import streamlit as st
from vrac.settings import DataMode
from vrac.auth_ui import require_login
mode = st.selectbox('Origem', ['pseudonymized', 'synthetic'], key='vrac_data_origin')
require_login(DataMode(mode))
""")
    app.session_state["vrac_auth_session"] = session
    app.run()
    app.session_state["overview_result"] = "old"
    app.session_state["vrac_artifact_cache"] = {"old": b"old"}
    app.session_state["feedback_records"] = ["old"]
    app.selectbox(key="vrac_data_origin").select("synthetic").run()
    assert not app.exception
    for key in ("overview_result", "vrac_artifact_cache", "feedback_records"):
        with pytest.raises(KeyError):
            app.session_state[key]
    assert app.session_state["vrac_auth_session"].data_mode == DataMode.SYNTHETIC


def test_law_is_available_and_academic_code_jur_never_queried(parts, monkeypatch):
    from vrac.db import institutional_faculty as reader
    from vrac.demo_data import DemoDataError, load_department_hierarchy
    from vrac.department_hierarchy import ALL_DEPARTMENTS

    session = identity(parts)
    session.client.allowed = ["IND", "DIR", "JUR"]
    verify_session(session)
    scopes = []

    def records(*, batch, component, departments):
        scopes.append(departments)
        return parts[component]

    monkeypatch.setattr(reader, "load_scope", records)
    with session_scope(session):
        assert reader.load_options(SETTINGS).departments == ("IND", "DIR")
        assert load_department_hierarchy(SETTINGS).centers == ("CCS", "CTC")
        reader.load_faculty_source(SETTINGS, department=ALL_DEPARTMENTS)
        reader.load_academic_source(SETTINGS, department=ALL_DEPARTMENTS)
        assert scopes and all(scope == ("IND", "DIR") for scope in scopes)
        reader.load_faculty_source(SETTINGS, department="DIR")
        assert scopes[-1] == ("DIR",)
        for load in (reader.load_faculty_source, reader.load_academic_source):
            with pytest.raises(DemoDataError):
                load(SETTINGS, department="JUR")
        assert session.departments == ("IND", "DIR", "JUR")


def test_layout_v2_history_by_department_and_readable_names(parts):
    parts["cadastro"][0].update(
        titulacao="DOUTORADO", tempo_casa_anos=12, vinculo_extraordinario="N"
    )
    departed = "B" * 64
    parts["historico_mensal"].append(
        dict(parts["historico_mensal"][0], vinculo_id=departed, pessoa_id="C" * 64, ano=2022)
    )
    parts["historico_cargos"].append(dict(parts["historico_cargos"][0], vinculo_id=departed))
    parts["alocacoes"] = [
        dict(
            departamento_alocacao="IND",
            vinculo_id=LINK,
            semestre=20261,
            unidade_oferta="CPE",
            disciplina_id="D" * 64,
            turma_id="E" * 64,
            nivel="GRA",
            tipo="PROJETO",
            obrigatoria="Sim",
            horas_alocadas=3,
            compartilhada="Não",
            vagas_ofertadas=30,
            vagas_preenchidas=17,
            professor_principal=1,
            disciplina_codigo="ENG1149",
            disciplina_nome="PROJETO DE GRADUACAO",
            turma="3VA",
            creditos=3,
            horas_distancia=0,
            horas_extensao=0,
        )
    ]
    parts["eventos_funcoes"] = [
        dict(
            departamento_alocacao="IND",
            vinculo_id=LINK,
            evento_id="F" * 64,
            ano=2026,
            mes=3,
            descricao_id="A" * 64,
            papel_id="B" * 64,
            gratificacao="DIRETOR DE DEPARTAMENTO",
            papel="DIRECAO",
            departamento_distribuicao="IND",
        )
    ]
    # Funcionário sem cargo docente na folha: excluído como no painel, sem bloquear.
    parts["historico_mensal"].append(
        dict(parts["historico_mensal"][0], vinculo_id="E" * 64, pessoa_id="F" * 64)
    )
    data = source(parts)
    assert "history" in data.available
    register = data.faculty.register[0]
    assert (register.degree, register.tenure_years, register.extraordinary) == (
        "DOUTORADO",
        12,
        "N",
    )
    assert "history_by_department" in data.available
    assert any("departamento de cada competência" in note for note in data.faculty.notes)
    history = calculate(AnalysisKind.HISTORY, data, FILTERS)
    assert not any("coorte" in note.lower() for note in history.notes)
    assert next(t for t in history.tables if t.key == "history").rows[0][1] == 1
    workload = calculate(AnalysisKind.WORKLOAD, data, FILTERS)
    detail = next(t for t in workload.tables if t.key == "allocation_detail").rows[0]
    assert detail[4:8] == ("ENG1149", "PROJETO DE GRADUACAO", "3VA", 3)
    functions = calculate(AnalysisKind.FUNCTIONS, data, FILTERS)
    by_function = next(t for t in functions.tables if t.key == "by_function").rows
    assert by_function == (("DIRETOR DE DEPARTAMENTO", 1),)
