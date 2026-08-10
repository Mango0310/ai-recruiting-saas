from pydantic import BaseModel
from typing import Optional


class WorkExperience(BaseModel):
    company: str
    position: str
    start_date: str
    end_date: str
    projects: list[dict] = []


class Education(BaseModel):
    school: str
    degree: str
    major: str
    start_year: int
    end_year: int


class CandidateProfile(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    years_of_experience: int = 0
    highest_degree: str = ""
    current_position: str = ""
    current_company: str = ""
    skills: list[str] = []
    work_experience: list[dict] = []
    education: list[dict] = []
