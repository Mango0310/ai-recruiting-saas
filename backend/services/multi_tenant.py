"""Multi-tenant data isolation helpers.

All helpers require a User — callers must pass the result of require_user().
"""

from typing import Optional
from models.job import Job
from models.user import User


def get_company_job_ids(db, user: User) -> set:
    """Returns set of job IDs for user's company."""
    return {j.id for j in db.query(Job).filter(Job.company_id == user.company_id).all()}


def filtered_job_query(db, user: User):
    """Return base query for Job, filtered by user's company."""
    return db.query(Job).filter(Job.company_id == user.company_id)
