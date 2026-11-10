"""Controles de aprofundamento sem rede, com dados exclusivamente sintéticos."""

from dataclasses import replace

import pytest

from vrac.analyses.academic import AnalysisFilters
from vrac.analyses.verification import (
    IDENTITY,
    RULE_ID,
    Context,
    Status,
    VerificationSession,
)
from vrac.settings import DataMode, DemoSource, Settings

SETTINGS = Settings(demo_source=DemoSource.POSTGRES)
FILTERS = AnalysisFilters("2025.1", "2025.2", "2025.2")
CONTEXT = Context(
    IDENTITY, "R04", FILTERS, "SINT-A", ("SINT-A",), (("department", "SINT-A"),), "snapshot-1"
)


def run(
    session,
    query,
    *,
    automatic=False,
    enabled=frozenset({RULE_ID}),
    applicable=True,
    budget=1,
    settings=SETTINGS,
):
    return session.run(
        settings,
        automatic=automatic,
        enabled=enabled,
        applicable=applicable,
        query=query,
        budget=budget,
    )


def test_decline_never_calls_query_and_basic_results_remain_untouched():
    session = VerificationSession()
    session.select(CONTEXT)
    basic = {"R04": 42}
    session.decide(False)
    assert (
        run(session, lambda _: pytest.fail("Consulta recusada executada")).status == Status.DECLINED
    )
    assert basic == {"R04": 42}


@pytest.mark.parametrize(
    "changed",
    [
        replace(CONTEXT, analysis="R06"),
        replace(CONTEXT, filters=replace(FILTERS, workload_period="2025.1")),
        replace(CONTEXT, reference="snapshot-2"),
        replace(CONTEXT, identity="outra-identidade"),
        replace(CONTEXT, rule_version="2"),
        replace(CONTEXT, departments=("SINT-B",)),
        replace(CONTEXT, source_arguments=(("department", "SINT-B"),)),
    ],
)
def test_changed_context_invalidates_approval_even_if_selection_is_restored(changed):
    session = VerificationSession()
    session.select(CONTEXT)
    session.decide(True)
    session.select(changed)
    session.select(CONTEXT)
    assert (
        run(session, lambda _: pytest.fail("Aprovação anterior reutilizada")).status
        == Status.SUGGESTED
    )


def test_rerun_uses_result_once_and_failure_does_not_become_success():
    session = VerificationSession()
    session.select(CONTEXT)
    calls = []
    session.decide(True)

    def query(context):
        calls.append(context)
        return 2

    assert run(session, query).status == Status.EXECUTED
    assert run(session, query).evidence == "2 registros de alocação sem classificação."
    assert len(calls) == 1
    session.select(replace(CONTEXT, reference="outra"))
    session.decide(True)

    def broken(_):
        raise RuntimeError("detalhes privados")

    assert run(session, broken).status == Status.FAILED
    assert run(session, query).status == Status.FAILED
    assert len(calls) == 1


def test_automatic_respects_enabled_budget_and_applicability():
    session = VerificationSession()
    session.select(CONTEXT)

    def forbidden(_):
        pytest.fail("Consulta fora do limite")

    assert run(session, forbidden, automatic=True, enabled=frozenset()).status == Status.SUGGESTED
    assert run(session, forbidden, automatic=True, budget=0).status == Status.SUGGESTED
    assert run(session, forbidden, automatic=True, budget=2).status == Status.SUGGESTED
    assert run(session, lambda _: 1, automatic=True).status == Status.EXECUTED
    session.select(replace(CONTEXT, reference="novo"))
    assert run(session, forbidden, automatic=True, applicable=False).status == Status.NOT_APPLICABLE
    session.select(replace(CONTEXT, reference="outro", departments=tuple(str(i) for i in range(6))))
    assert run(session, forbidden, automatic=True).status == Status.NOT_APPLICABLE


def test_snapshot_checks_do_not_invoke_additional_query_and_real_mode_is_blocked():
    from vrac.analyses.academic_fixture import load_fixture
    from vrac.analyses.academic_quality import inspect_source

    source = load_fixture("SINT-A")
    assert len(inspect_source(source)) == 10
    session = VerificationSession()
    session.select(CONTEXT)
    assert (
        run(session, lambda _: pytest.fail("Consulta adicional"), settings=Settings()).status
        == Status.NOT_APPLICABLE
    )
    session.select(replace(CONTEXT, reference="outra"))
    with pytest.raises(PermissionError):
        run(
            session,
            lambda _: 0,
            automatic=True,
            settings=Settings(data_mode=DataMode.REAL, demo_source=DemoSource.POSTGRES),
        )


def test_postgres_query_requires_same_snapshot_and_uses_fixed_bound_query(monkeypatch):
    from contextlib import contextmanager
    from types import SimpleNamespace

    from vrac.analyses.academic_fixture import load_fixture
    from vrac.db import synthetic_postgres as reader
    from vrac.demo_data import DemoDataError

    source = load_fixture("SINT-A")
    connection = object()
    calls = []

    @contextmanager
    def connected(_settings):
        yield connection, "versão"

    monkeypatch.setattr(reader, "_connection", connected)
    monkeypatch.setattr(reader, "_read_academic_source", lambda *args, **kwargs: source)
    monkeypatch.setattr(reader, "_options", lambda _: SimpleNamespace(departments=("SINT-A",)))

    def rows(conn, query, parameters):
        calls.append((conn, query, parameters))
        return [
            {"semester": 20252, "classification": None},
            {"semester": 20251, "classification": None},
            {"semester": 20252, "classification": "regular"},
        ]

    monkeypatch.setattr(reader, "_rows", rows)
    context = replace(CONTEXT, reference=source.fingerprint)
    assert reader.query_missing_classification(SETTINGS, context) == 1
    assert calls == [(connection, reader.Query.TEACHING_ALLOCATIONS, {"department": "SINT-A"})]
    assert "%(department)s" in reader._query(reader.Query.TEACHING_ALLOCATIONS)
    calls.clear()
    with pytest.raises(DemoDataError):
        reader.query_missing_classification(SETTINGS, replace(context, reference="alterada"))
    assert not calls


def test_ui_approval_decline_and_rerun_preserve_basic_results(monkeypatch):
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    from vrac.analyses.academic_fixture import load_fixture
    from vrac.demo_data import load_demo_options
    from vrac.department_hierarchy import hierarchy_for_departments

    options = load_demo_options(Settings())
    hierarchy = hierarchy_for_departments(
        options.departments, source="fixture", synthetic_centers=True
    )
    monkeypatch.setenv("VRAC_DEMO_SOURCE", "postgres")
    monkeypatch.setattr("vrac.ui.load_demo_options", lambda _: options)
    monkeypatch.setattr("vrac.ui.load_department_hierarchy", lambda _: hierarchy)
    monkeypatch.setattr(
        "vrac.ui.load_faculty_source",
        lambda _settings, **_scope: load_fixture("SINT-A").faculty,
    )
    monkeypatch.setattr("vrac.academic_ui.load_department_hierarchy", lambda _: hierarchy)
    monkeypatch.setattr(
        "vrac.academic_ui.load_academic_source",
        lambda _settings, **_scope: load_fixture("SINT-A"),
    )
    calls = []
    monkeypatch.setattr(
        "vrac.db.synthetic_postgres.query_missing_classification",
        lambda _settings, context: calls.append(context) or 3,
    )
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=60
    ).run()
    app.button(key="home_open_R04").click().run()
    app.button(key="suite_run").click().run()
    app.checkbox(key="suite_check_enable").check().run()
    app.button(key="suite_check_decline").click().run()
    assert not calls and app.session_state["suite_results"]
    assert app.session_state["suite_verification"].outcomes[RULE_ID].status == Status.DECLINED
    app.selectbox(key="suite_workload_period").select("2026.1").run()
    app.button(key="suite_run").click().run()
    app.checkbox(key="suite_check_enable").check().run()
    app.button(key="suite_check_approve").click().run()
    assert not calls
    assert app.session_state["suite_verification"].outcomes[RULE_ID].status == Status.APPROVED
    app.button(key="suite_check_execute").click().run()
    assert len(calls) == 1
    app.run()
    assert len(calls) == 1 and app.session_state["suite_results"] and not app.exception

    def fail_query(_settings, _context):
        raise RuntimeError("erro interno")

    monkeypatch.setattr("vrac.db.synthetic_postgres.query_missing_classification", fail_query)
    app.button(key="suite_load").click().run()
    app.button(key="suite_run").click().run()
    app.radio(key="suite_check_mode").set_value("Automático").run()
    app.checkbox(key="suite_check_enable").check().run()
    assert app.session_state["suite_verification"].outcomes[RULE_ID].status == Status.FAILED
    assert app.session_state["suite_results"] and not app.exception
    assert not any("erro interno" in item.value for item in app.markdown)
