"""Organização das análises por área, usada pelas abas e pela página inicial.

Somente apresentação: códigos, nomes e textos. Nenhum cálculo ou acesso a dados.
"""

from dataclasses import dataclass

VIEW_KEY = "vrac-view"
FACULTY_PICKER = "docentes_analysis"
PANORAMA = "panorama"
ALL_FACULTY = "todas"
FACULTY_CODES = ("R01", "R02", "R03", "R04", "R05")
# O relatório completo calcula os seis roteiros juntos, inclusive matrículas, para o PDF.
COMPLETE_CODES = (*FACULTY_CODES, "R06")


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
            "Análise Geral dos professores",
            "Como está composto o corpo docente e como evoluiu o total de ativos?",
            "Professores por departamento, quadro e categoria funcional, com o histórico.",
        ),
        Analysis(
            "R02",
            "Comparação entre grupos de quadro",
            "Como um grupo de quadros se compara a outro?",
            "QP × Geral por departamento, ou dois grupos de quadros e categorias à escolha.",
        ),
        Analysis(
            "R03",
            "Histórico do departamento",
            "Como o quadro de professores evoluiu no período?",
            "Professores ativos por quadro, semestre e mês.",
        ),
        Analysis(
            "R05",
            "Gratificações e funções",
            "Quais professores recebem gratificação por função?",
            "Gratificações por função, departamento e mês, com a dupla função.",
        ),
        Analysis(
            "R04",
            "Carga horária dos professores",
            "Qual a carga horária de cada professor no semestre?",
            "Horas Reais, CH Contratada, Indicador de CH e turmas oferecidas.",
        ),
        Analysis(
            ALL_FACULTY,
            "Relatório completo",
            "Quer ver tudo de uma vez?",
            "Calcula todas as análises, inclusive alunos, e libera o PDF e o ZIP completos.",
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
            "Análise Geral dos alunos",
            "Como evoluíram os alunos matriculados, bolsistas, formados e ingressantes?",
            "As quatro séries do painel por curso, habilitação, turno, nível e ingresso.",
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
    return COMPLETE_CODES if code == ALL_FACULTY else (code,)
