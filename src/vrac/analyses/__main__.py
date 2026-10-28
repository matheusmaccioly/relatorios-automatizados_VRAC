"""Conferência offline das definições; sem integração com interface ou banco."""

from vrac.analyses.catalog import load_catalog, pending_decisions


def main() -> int:
    catalog = load_catalog()
    print(f"Catálogo {catalog.version}: propostas lógicas; adaptadores de análises bloqueados.")
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
