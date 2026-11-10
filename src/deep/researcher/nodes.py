from pydantic import BaseModel, Field
from typing import List


class ResearchOutput(BaseModel):
    topic: str
    sub_questions: List[str]
    findings: List[str]
    data_points: List[str]
    sources: List[str]


class AnalysisOutput(BaseModel):
    key_insights: List[str]
    patterns: List[str] = Field(description="Trends or recurring themes across findings")
    conclusions: List[str] = Field(description="Evidence-backed conclusions — no speculation")
    limitations: List[str] = Field(description="What is unknown, uncertain, or out of scope")
    summary: str = Field(description="2-3 paragraph synthesis of the entire analysis")


class CritiqueOutput(BaseModel):
    gaps: List[str] = Field(description="Missing facts or angles not yet covered")
    follow_up_questions: List[str] = Field(description="Specific questions the next research pass should answer")
    logical_issues: List[str] = Field(description="Flawed reasoning or unsupported leaps in the analysis")
    needs_deeper_research: bool = Field(description="True if gaps are significant enough to warrant another research pass")


class FactCheckOutput(BaseModel):
    is_verified: bool = Field(description="True only if every claim is grounded in the research")
    unverified_claims: List[str] = Field(description="Claims that are invented, exaggerated, or unsubstantiated")
    corrections: List[str] = Field(description="Corrected version of each unverified claim")
    confidence_score: int = Field(description="Overall factual confidence 1-10")
    verdict: str = Field(description="One-sentence audit summary")
