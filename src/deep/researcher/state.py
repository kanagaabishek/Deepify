from typing_extensions import TypedDict
from typing import Optional
from deep.researcher.nodes import ResearchOutput, AnalysisOutput, CritiqueOutput, FactCheckOutput


class State(TypedDict, total=False):
    topic: str
    research: ResearchOutput
    analysis: AnalysisOutput
    critique: CritiqueOutput
    fact_check: FactCheckOutput
    iteration_count: int
    report: str
