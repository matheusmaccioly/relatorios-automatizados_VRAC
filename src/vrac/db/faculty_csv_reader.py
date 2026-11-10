"""Contrato paginado institucional; integração às telas é uma etapa explícita."""

from uuid import UUID

from vrac.demo_data import DemoDataError
from vrac.dev.faculty_csv import DEPARTMENTS, LAYOUTS
from vrac.supabase_auth import current_session


def load_component(*, batch: UUID, component: str, department: str) -> tuple[dict, ...]:
    return _load(batch=batch, component=component, departments=(department,), single=True)


def load_scope(*, batch: UUID, component: str, departments: tuple[str, ...]) -> tuple[dict, ...]:
    return _load(batch=batch, component=component, departments=departments, single=False)


def _load(
    *, batch: UUID, component: str, departments: tuple[str, ...], single: bool
) -> tuple[dict, ...]:
    """Consulta fixa com JWT da sessão; RLS limita o departamento em cada página."""
    if component not in LAYOUTS or not departments or not set(departments) <= DEPARTMENTS:
        raise DemoDataError("Conjunto ou departamento indisponível.")
    rows: list[dict] = []
    after = 0
    try:
        while True:
            data = (
                current_session()
                .client.rpc(
                    "vrac_docentes_page" if single else "vrac_docentes_rows",
                    {
                        "p_carga": str(batch),
                        "p_conjunto": component,
                        **(
                            {"p_departamento": departments[0]}
                            if single
                            else {"p_departamentos": list(departments)}
                        ),
                        "p_apos": after,
                        "p_limite": 1000,
                    },
                )
                .execute()
                .data
            )
            if (
                data["synthetic"] is not False
                or data["origin"] != "institucional_pseudonimizada"
                or data["batch"] != str(batch)
                or data["component"] != component
            ):
                raise ValueError
            page = data["rows"]
            if not isinstance(page, list) or len(page) > 1000:
                raise ValueError
            for row in page:
                if (
                    not isinstance(row["linha"], int)
                    or row["linha"] <= after
                    or row["departamento_alocacao"] not in departments
                    or set(row) != {"linha", *LAYOUTS[component].columns}
                ):
                    raise ValueError
                after = row["linha"]
                rows.append(row)
            if len(rows) > 100_000:
                raise ValueError  # falhar explicitamente, nunca retornar recorte truncado
            if len(page) < 1000:
                return tuple(rows)
    except Exception:
        raise DemoDataError(
            "Carga institucional indisponível ou incompatível; "
            "nenhum dado de demonstração foi carregado."
        ) from None
