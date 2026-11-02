"""Conferência offline das definições; sem integração com interface ou banco."""

from vrac.analyses.catalog import load_catalog, pending_decisions
from vrac.analyses.workflows import WORKFLOWS, phase3_blockers


def main() -> int:
    catalog = load_catalog()
    print(f"Catálogo {catalog.version}: referências da integração institucional.")
    print("R01–R06 disponíveis na demonstração sintética, com gráficos e exportações (D-027).")
    detailed = sum(item.detailed_document_available for item in catalog.documentary_evidence)
    print(
        f"Base documental: {len(catalog.documentary_evidence)} registro(s) de evidência; "
        f"{detailed} documento(s) detalhado(s) usado(s) na revisão."
    )
    for item in catalog.analyses:
        pending = len(pending_decisions(item))
        print(f"{item.priority}. {item.id}: {item.validation_status}; {pending} decisões pendentes")
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
        "Pendências documentais para integração institucional: "
        f"{', '.join(phase3_blockers(catalog))}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
