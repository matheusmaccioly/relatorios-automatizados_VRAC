"""Contratos de configuração, autorização e cenários sintéticos da fase 0."""

from collections.abc import Iterator, Mapping

import pytest

from vrac.authorization import AccessDenied, authorize_data_access, require_data_access
from vrac.settings import ConfigurationError, DataMode, Environment, Settings, load_settings
from vrac.synthetic import load_demo_data, select_demo_data


def test_settings_defaults_read_only_public_configuration() -> None:
    class PublicConfigurationOnly(Mapping[str, str]):
        def __getitem__(self, key: str) -> str:
            assert key in {"VRAC_ENVIRONMENT", "VRAC_DATA_MODE"}
            raise KeyError(key)

        def __iter__(self) -> Iterator[str]:
            raise AssertionError("Não enumerar variáveis de ambiente.")

        def __len__(self) -> int:
            raise AssertionError("Não inspecionar variáveis fora da lista pública.")

    settings = load_settings(PublicConfigurationOnly())
    assert settings == Settings(Environment.DEVELOPMENT, DataMode.SYNTHETIC)
    assert authorize_data_access(settings).allowed


@pytest.mark.parametrize(
    "configuration",
    [
        {"VRAC_ENVIRONMENT": "valor-sensivel-de-teste"},
        {"VRAC_DATA_MODE": "valor-sensivel-de-teste"},
        {"VRAC_ENVIRONMENT": "production"},
    ],
)
def test_invalid_configuration_fails_without_echoing_values(configuration: dict[str, str]) -> None:
    with pytest.raises(ConfigurationError) as error:
        load_settings(configuration)
    assert "valor-sensivel-de-teste" not in str(error.value)


@pytest.mark.parametrize(
    "configuration",
    [{"environment": "development"}, {"data_mode": "synthetic"}],
)
def test_direct_settings_cannot_bypass_validation(configuration: dict[str, str]) -> None:
    with pytest.raises(ConfigurationError):
        Settings(**configuration)  # type: ignore[arg-type]


@pytest.mark.parametrize("environment", list(Environment))
def test_real_access_is_denied_before_synthetic_data_can_be_created(
    environment: Environment,
) -> None:
    settings = load_settings({"VRAC_ENVIRONMENT": environment.value, "VRAC_DATA_MODE": "real"})
    assert not authorize_data_access(settings).allowed
    with pytest.raises(AccessDenied):
        require_data_access(settings)
    with pytest.raises(AccessDenied):
        load_demo_data(settings)


def test_synthetic_data_is_deterministic_and_covers_required_edge_cases() -> None:
    data = load_demo_data(Settings())
    assert data == load_demo_data(Settings())
    assert data == load_demo_data(Settings(), seed=21)
    assert data.synthetic
    repeated_teacher = [row for row in data.faculty if row.teacher_id == "SYN-DOC-001"]
    assert len({row.reference_month for row in repeated_teacher}) > 1
    assert len({row.contract_id for row in repeated_teacher}) > 1
    assert len({row.employment_type for row in data.faculty}) > 1
    shared = [row for row in data.allocations if row.sharing_id == "SH01"]
    assert len(shared) > 1
    assert len({row.curriculum_id for row in shared}) > 1
    assert any(row.department != row.teaching_department for row in data.allocations)
    assert any(row.students == 0 for row in data.allocations)
    assert any(row.students is None for row in data.allocations)
    assert any(row.classification is None for row in data.allocations)


def test_filtering_preserves_missing_values_zero_and_empty_period() -> None:
    data = load_demo_data(Settings())
    selected = select_demo_data(data, department="SINT-A", period="2026.1")
    assert selected.faculty and selected.allocations
    assert all(row.department == "SINT-A" and row.period == "2026.1" for row in selected.faculty)
    assert all(
        row.department == "SINT-A" and row.period == "2026.1" for row in selected.allocations
    )
    assert any(row.real_hours is None for row in selected.faculty)
    assert any(row.real_hours == 0 for row in selected.faculty)
    empty = select_demo_data(data, department="SINT-A", period="2026.2")
    assert empty.faculty == ()
    assert empty.allocations == ()
    assert empty.synthetic


@pytest.mark.parametrize(
    ("department", "period"), [("departamento-inexistente", "2026.1"), ("SINT-A", "1900.1")]
)
def test_filters_accept_only_the_closed_demo_selection(department: str, period: str) -> None:
    with pytest.raises(ValueError):
        select_demo_data(load_demo_data(Settings()), department=department, period=period)
