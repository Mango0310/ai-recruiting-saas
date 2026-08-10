from pydantic import BaseModel
from typing import Optional


class JobProfile(BaseModel):
    responsibilities: list[str] = []
    required_skills: list[str] = []
    skill_tags: list[str] = []
    experience_requirements: Optional[dict] = None


class WeightDistribution(BaseModel):
    ai_understanding: int = 25
    product_ability: int = 25
    project_experience: int = 25
    education: int = 25


class JobProfileFull(JobProfile):
    weight_distribution: WeightDistribution = WeightDistribution()
