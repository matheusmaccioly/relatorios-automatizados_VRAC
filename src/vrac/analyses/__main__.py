"""Conferência offline das definições; sem integração com interface ou banco."""

from vrac.analyses.catalog import load_catalog, pending_decisions
from vrac.analyses.workflows import WORKFLOWS, phase3_blockers
from vrac.settings import DataMode


def main() -> int:
    catalog = load_catalog()
    print(f"Catálogo {catalog.version}: referências da integração institucional.")
    print("R01–R06 disponíveis na demonstração sintética, com gráficos e exportações (D-027).")
    print("Estado sintético do catálogo refere-se a testes offline; esta CLI não testa o banco.")
    detailed = sum(item.detailed_document_available for item in catalog.documentary_evidence)
    print(
        f"Base documental: {len(catalog.documentary_evidence)} registro(s) de evidência; "
        f"{detailed} documento(s) detalhado(s) usado(s) na revisão."
    )
    for item in catalog.analyses:
        pending = len(pending_decisions(item))
        print(
            f"{item.priority}. {item.id}: {item.validation_status} (institucional); "
            f"{pending} registros históricos pendentes"
        )
        print(f"   Sintético: {item.synthetic_status}; mapa: {item.synthetic_mapping_reference}")
        print(
            f"   {len(item.semantic_variants)} variante(s) documentada(s); "
            "seleção institucional pendente."
        )
    print("Roteiros documentados (estados institucionais não bloqueiam a demonstração):")
    for workflow in WORKFLOWS:
        print(f"   {workflow.identifier}: {workflow.title}; fase {workflow.phase}")
        for metric in workflow.metrics:
            print(f"      {metric.identifier}: pendências {', '.join(metric.decisions)}")
    print(
        "Registros históricos/institucionais (D-022 dispensa reaprovar fórmulas): "
        f"{', '.join(phase3_blockers(catalog))}."
    )
    if not phase3_blockers(catalog, mode=DataMode.SYNTHETIC):
        print("Prompt 3 sintético sem dependência do inventário institucional (D-028).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
