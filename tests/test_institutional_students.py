"""Integração de alunos exclusivamente com respostas fictícias e sem rede."""

import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from vrac.db.institutional_students import FILTERS, calculate, load_filters, load_options
from vrac.demo_data import DemoDataError, DemoOptions
from vrac.provenance import INSTITUTIONAL_SOURCE
from vrac.settings import DataMode
from vrac.supabase_auth import SupabaseSession, session_scope

BATCH = "30000000-0000-4000-8000-000000000099"


class Client:
    def __init__(self):
        self.fail = False
        self.allowed = ["IND", "ECO"]
        self.calls = []
        self.rows = [
            {"periodo_eixo": 20261, "indicador": "MATRICULADOS", "quantidade": 2},
            {"periodo_eixo": 20261, "indicador": "BOLSISTAS_MATRICULADOS", "quantidade": 1},
            {"periodo_eixo": 20262, "indicador": "INGRESSANTES", "quantidade": 1},
        ]

    def rpc(self, name, params=None):
        self.calls.append((name, params))
        if self.fail:
            raise RuntimeError("Resposta privada fictícia")
        data = {"origin": "institucional_pseudonimizada", "synthetic": False, "batch": BATCH}
        if name == "vrac_alunos_options":
            data.update(departments=self.allowed, start=20261, end=20262)
        elif name == "vrac_alunos_filters":
            assert set(params["p_departamentos"]) <= set(self.allowed)
            data["filters"] = {key: [None, "", "Valor fictício  "] for key in FILTERS}
        elif name == "vrac_alunos_geral":
            assert set(params["p_departamentos"]) <= set(self.allowed)
            data.update(rows=self.rows, unit="matriculas_distintas")
        else:
            raise AssertionError("RPC inesperada")
        return SimpleNamespace(execute=lambda: SimpleNamespace(data=data))


@pytest.fixture
def session():
    return SupabaseSession(
        Client(),
        "fixture",
        "fixture-token",
        "fixture-refresh",
        time.time() + 3600,
        departments=("IND", "ECO"),
        verified_until=time.time() + 900,
        data_mode=DataMode.PSEUDONYMIZED,
        batch=BATCH,
    )


def test_reader_preserves_missing_and_bound_multiselect(session):
    with session_scope(session):
        options = load_options()
        assert load_filters(options, ("IND",))["curso"] == (None, "", "Valor fictício  ")
        result = calculate(options, ("IND",), 20261, 20262, {"curso": [None, "Valor fictício  "]})
        assert result.tables[0].rows == (
            ("2026.1", 2, 1, None, None),
            ("2026.2", None, None, None, 1),
        )
        assert session.client.calls[-1][1]["p_filtros"] == {"curso": [None, "Valor fictício  "]}
        assert result.source == INSTITUTIONAL_SOURCE
        assert any("Direito" in note for note in result.notes)
        with pytest.raises(DemoDataError):
            calculate(options, ("DIR",), 20261, 20262, {})
        with pytest.raises(DemoDataError):
            calculate(options, ("IND",), 20261, 20262, {"aluno_id": ["X"]})
        session.client.rows.append(session.client.rows[0])
        with pytest.raises(DemoDataError):
            calculate(options, ("IND",), 20261, 20262, {})


def test_reader_rejects_synthetic_and_failure(session):
    with session_scope(session):
        session.data_mode = DataMode.SYNTHETIC
        with pytest.raises(DemoDataError):
            load_options()
        session.data_mode = DataMode.PSEUDONYMIZED
        session.client.fail = True
        with pytest.raises(DemoDataError) as error:
            load_options()
        assert "privada" not in str(error.value)


def screen(monkeypatch, session):
    monkeypatch.setattr("vrac.db.institutional_students.current_session", lambda: session)
    return AppTest.from_string(
        """
from vrac.branding import load_branding
from vrac.student_general_ui import render
render(load_branding(), active=True)
""",
        default_timeout=30,
    ).run()


def test_ui_filters_exports_and_failure_clear_old_results(monkeypatch, session):
    app = screen(monkeypatch, session)
    assert not app.exception
    # Seleção salva no painel: Curso/Programa sem vazio, nulo e DOMÍNIO ADICIONAL.
    assert app.multiselect(key="institutional_students_curso").value == [2]
    app.button(key="institutional_students_run").click().run()
    assert not app.exception
    assert session.client.calls[-1][1]["p_filtros"]["curso"] == ["Valor fictício  "]
    assert len(app.get("vega_lite_chart")) == 1
    # Mesmo padrão das análises docentes: PNG no cartão, CSV na tabela e ZIP no topo.
    assert {d.key for d in app.get("download_button")} == {
        "institutional_students_R06_png_0",
        "institutional_students_R06_student_general_csv",
        "institutional_students_download_all",
    }
    assert not any("_download_pdf" in d.key for d in app.get("download_button"))
    assert any(e.label == "Filtros usados neste resultado" for e in app.expander)
    app.multiselect(key="institutional_students_curso").select(0).run()
    assert not app.exception
    assert not app.get("download_button")
    app.button(key="institutional_students_run").click().run()
    assert session.client.calls[-1][1]["p_filtros"]["curso"] == ["Valor fictício  ", None]
    assert any(list(t.value.columns) == ["Filtro", "Valor"] for t in app.table)
    session.client.fail = True
    app.run()
    assert not app.exception and app.error
    assert not app.get("download_button")
    with pytest.raises(KeyError):
        app.session_state["institutional_students_result"]


def test_ui_scope_change_invalidates_and_empty_is_not_zero(monkeypatch, session):
    app = screen(monkeypatch, session)
    app.button(key="institutional_students_run").click().run()
    session.client.allowed = ["IND"]
    app.run()
    assert not app.exception and not app.get("download_button")
    assert app.multiselect(key="institutional_students_departments").value == ["IND"]
    session.client.rows = []
    app.button(key="institutional_students_run").click().run()
    assert not app.exception and app.info
    assert app.session_state["institutional_students_result"].tables[0].rows[0][1:] == (None,) * 4


def test_real_navigation_routes_to_general(monkeypatch, session):
    monkeypatch.setenv("VRAC_DEMO_SOURCE", "supabase")
    monkeypatch.setenv("VRAC_DATA_MODE", "pseudonymized")
    monkeypatch.setattr("vrac.auth_ui.require_login", lambda mode: session)
    monkeypatch.setattr(
        "vrac.ui.load_demo_options",
        lambda settings: DemoOptions(
            ("IND", "ECO"), ("2026.1", "2026.2"), "2026.2", INSTITUTIONAL_SOURCE
        ),
    )
    monkeypatch.setattr("vrac.ui._faculty_area", lambda *args, **kwargs: None)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30)
    app.session_state["vrac-view"] = "Alunos"
    app.run()
    assert not app.exception
    app.button(key="institutional_students_run").click().run()
    assert not app.exception and app.get("vega_lite_chart")
    assert any("Como evoluíram as matrículas no período?" in x.value for x in app.markdown)
    assert any(x.value == "Resultados calculados" for x in app.subheader)
    assert not any(name == "vrac_snapshot" for name, _ in session.client.calls)


def test_quick_start_respects_department_and_pending_rights(monkeypatch, session):
    app = screen(monkeypatch, session)
    app.session_state["alunos_department"] = "IND"
    app.session_state["alunos_autorun"] = True
    app.run()
    assert not app.exception
    assert app.session_state["institutional_students_result"].department == "IND"
    app.session_state["alunos_department"] = "DIR"
    app.session_state["alunos_autorun"] = True
    app.run()
    assert not app.exception and app.warning
    assert not app.get("download_button")


def test_full_axis_png_preserves_semesters_and_zero_baseline(session):
    from vrac.branding import load_branding
    from vrac.charts import academic_chart, render_png
    from vrac.db.institutional_students import StudentOptions

    with session_scope(session):
        result = calculate(
            StudentOptions(BATCH, ("IND",), 20151, 20262), ("IND",), 20151, 20262, {}
        )

    def build():
        figure = academic_chart(result, result.charts[0], load_branding())
        axis = figure.axes[0]
        assert len(axis.get_xticklabels()) == 24
        assert all(label.get_rotation() == 45 for label in axis.get_xticklabels())
        assert axis.get_ylim()[0] == 0
        return figure

    assert render_png(build).startswith(b"\x89PNG")


def test_center_limits_students_and_discards_previous_exports(monkeypatch, session):
    app = screen(monkeypatch, session)
    app.button(key="institutional_students_run").click().run()
    assert app.get("download_button")
    app.selectbox(key="institutional_students_center").select("CTC").run()
    assert not app.exception and not app.get("download_button")
    assert app.multiselect(key="institutional_students_departments").options == ["IND"]
    app.button(key="institutional_students_run").click().run()
    assert not app.exception and app.get("download_button")
    params = [p for name, p in session.client.calls if name == "vrac_alunos_geral"][-1]
    assert params["p_departamentos"] == ["IND"]
    assert params["p_filtros"]["sigla_centro"] == ["CTC"]
    app.selectbox(key="institutional_students_center").select("CCS").run()
    assert not app.get("download_button")
    assert app.multiselect(key="institutional_students_departments").value == ["ECO"]


def test_default_selection_reproduces_dashboard_saved_slicers():
    from vrac.db.institutional_students import default_selection

    levels = ("Doutorado", "Graduação", None, "Mestrado", "Aluno Extraordinário")
    assert default_selection("nivel", levels) == [1, 2, 4]
    courses = (None, "", "DOMÍNIO ADICIONAL", "ENGENHARIA")
    assert default_selection("curso", courses) == [3]
    # Sem valor excluído, o filtro continua em Todos (nenhum parâmetro enviado).
    assert default_selection("curso", ("ENGENHARIA",)) is None
    assert default_selection("turno", ("Diurno", None)) is None


def test_law_department_is_accepted_and_shown_in_ccs(monkeypatch, session):
    # Regressão 0.1.5: o lote com Direito devolve DIR; a lista fechada deve aceitá-lo.
    session.client.allowed = ["ADM", "DIR", "ECO", "IND"]
    with session_scope(session):
        assert load_options().departments == ("ADM", "DIR", "ECO", "IND")
    app = screen(monkeypatch, session)
    assert not app.exception and not app.error
    app.selectbox(key="institutional_students_center").select("CCS").run()
    assert app.multiselect(key="institutional_students_departments").options == [
        "ADM",
        "DIR",
        "ECO",
    ]
    app.button(key="institutional_students_run").click().run()
    assert not app.exception and not app.error
    assert "DIR" in session.client.calls[-1][1]["p_departamentos"]


def test_unknown_or_academic_code_is_refused(session):
    session.client.allowed = ["IND", "JUR"]
    with session_scope(session), pytest.raises(DemoDataError):
        load_options()
