from typing import List
from pydantic import BaseModel


class MissingInfoAnalysis(BaseModel):
    is_sufficient: bool
    missing_fields: List[str]
    clarification_questions: List[str]
    missing_critical_count: int