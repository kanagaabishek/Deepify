from pydantic import BaseModel
from typing import List


class Researcher(BaseModel):
    topic: str
    key_findings: List[str]
    sources: List[str]

class Editor(BaseModel):
    hook: str
    body: str
    call_to_action: str
    hashtags: List[str]
    full_post: str

class Evaluator(BaseModel):
    hook_critique: str
    grammar_and_style_fixes: List[str]
    enhanced_post: str
    is_corrections_needed: str

class FactChecker(BaseModel):
    is_verified: bool
    false_or_unsupported_claims: List[str]
    corrections: List[str]
    verdict: str