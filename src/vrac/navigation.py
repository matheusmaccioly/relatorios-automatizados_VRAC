"""Organização das análises por área, usada pelas abas e pela página inicial.

Somente apresentação: códigos, nomes e textos. Nenhum cálculo ou acesso a dados.
"""

from dataclasses import dataclass

PANORAMA = "panorama"
ALL_FACULTY = "todas"
# Códigos que a opção "todas" calcula juntos, na ordem dos roteiros.
FACULTY_CODES = ("R01", "R02", "R03", "R04", "R05")


@dataclass(frozen=True, slots=True)
class Analysis:
    code: str
    name: str
    question: str
    description: str


@dataclass(frozen=True, slots=True)
class Area:
    key: str
    tab: str
    title: str
    summary: str
    color: str
    analyses: tuple[Analysis, ...] = ()

    @property
    def available(self) -> bool:
        return bool(self.analyses)

    def analysis(self, code: str) -> Analysis:
        return next(item for item in self.analyses if item.code == code)


FACULTY = Area(
    "docentes",
    "Docentes",
    "Docentes",
    "Composição do corpo docente, evolução no tempo, funções e carga horária.",
    "amarelo",
    (
        Analysis(
            PANORAMA,
            "Panorama docente",
            "Como se distribuem os docentes e como evolui o total de ativos?",
            "Composição do cadastro atual e histórico mensal no mesmo recorte.",
        ),
        Analysis(
            "R02",
            "Grupo QP e geral",
            "Como o grupo QP se compara ao corpo docente geral?",
            "Comparação por departamento com um grupo simulado e configurável.",
        ),
        Analysis(
            "R03",
            "Evolução docente",
            "Como o corpo docente evoluiu no período?",
            "Pessoas distintas por semestre e ativos a cada mês.",
        ),
        Analysis(
            "R05",
            "Funções",
            "Quais funções possuem evidência no período?",
            "Vigências por grupo de função no intervalo escolhido.",
        ),
        Analysis(
            "R04",
            "Carga horária",
            "Como se distribuem a carga horária e as alocações?",
            "Horas Reais e horas alocadas, cada uma com sua unidade e fonte.",
        ),
        Analysis(
            ALL_FACULTY,
            "Todas as análises docentes",
            "Quer ver tudo de uma vez?",
            "Calcula as análises docentes juntas e libera o pacote completo (ZIP).",
        ),
    ),
)
STUDENTS = Area(
    "alunos",
    "Alunos",
    "Alunos",
    "Evolução de matrículas e alunos por curso, habilitação, turno, nível e ingresso.",
    "preto",
    (
        Analysis(
            "R06",
            "Matrículas e alunos",
            "Como evoluíram as matrículas e os alunos?",
            "Séries por curso, habilitação, turno, nível e forma de ingresso.",
        ),
    ),
)
FINANCE = Area(
    "financeira",
    "Financeira (em breve)",
    "Financeira",
    "Esta área ainda não faz parte da demonstração. Nenhum dado financeiro é consultado.",
    "neutro",
)
PROJECTS = Area(
    "projetos",
    "Projetos patrocinados (em breve)",
    "Projetos patrocinados",
    "Esta área ainda não faz parte da demonstração. Nenhum dado de projetos é consultado.",
    "neutro",
)
AREAS = (FACULTY, STUDENTS, FINANCE, PROJECTS)


def area_of(code: str) -> Area:
    return next(area for area in AREAS if any(item.code == code for item in area.analyses))


def codes_for(code: str) -> tuple[str, ...]:
    """Roteiros que uma escolha calcula; o panorama tem tela própria."""
    return FACULTY_CODES if code == ALL_FACULTY else (code,)
