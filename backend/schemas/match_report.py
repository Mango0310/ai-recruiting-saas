from pydantic import BaseModel
from typing import Optional


class Strength(BaseModel):
    point: str
    evidence: str


class Gap(BaseModel):
    point: str
    evidence: str


class MatchReport(BaseModel):
    overall_conclusion: str = ""
    star_rating: int = 0
    summary: str = ""
    strengths: list[dict] = []
    gaps: list[dict] = []
    interview_suggestions: list[str] = []
    dimension_scores: dict = {}
