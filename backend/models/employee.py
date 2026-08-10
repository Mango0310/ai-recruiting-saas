from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, JSON
from database import Base


class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidate.id"))
    job_id = Column(Integer, ForeignKey("job.id"))
    application_id = Column(Integer, ForeignKey("application.id"))

    # Basic info
    name = Column(String(100), nullable=False)
    email = Column(String(200))
    phone = Column(String(50))
    id_number = Column(String(20))

    # Job info
    department = Column(String(100))
    position = Column(String(200))
    reports_to = Column(String(100))
    salary = Column(String(50))

    # Employment dates
    hire_date = Column(Date, default=datetime.utcnow)
    probation_months = Column(Integer, default=3)
    probation_end_date = Column(Date)
    contract_type = Column(String(20), default="fulltime")
    contract_end_date = Column(Date)

    # Social insurance & housing fund
    social_insurance = Column(String(20))
    social_insurance_account = Column(String(50))
    housing_fund = Column(String(20))
    housing_fund_account = Column(String(50))

    # Bank info
    bank_name = Column(String(100))
    bank_account = Column(String(50))

    # Education (filled by employee self-service)
    education_degree = Column(String(50))
    education_school = Column(String(100))
    education_major = Column(String(100))
    education_graduation_year = Column(Integer)

    # Document uploads (paths to uploaded files)
    diploma_file = Column(String(500))
    id_card_file = Column(String(500))

    # Emergency contact
    emergency_contact_name = Column(String(50))
    emergency_contact_phone = Column(String(50))
    emergency_contact_relation = Column(String(20))

    # Self-service onboarding
    onboard_token = Column(String(64), unique=True)
    onboard_token_created_at = Column(DateTime)
    onboard_token_expires_at = Column(DateTime)
    onboard_completed = Column(String(1), default="N")

    # Probation evaluations — list of stage assessments
    # [{stage: "30天", evaluated_at: "2026-09-07", status: "on_track",
    #   scores: {adaption: 4, performance: 3, collaboration: 4},
    #   strengths: "适应能力强...", risks: "需要加强...",
    #   recommendation: "建议继续观察", generated_by: "ai"}]
    probation_evaluations = Column(JSON, default=list)

    # Status & metadata
    status = Column(String(20), default="probation")  # probation / regular / resigned
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def days_until_probation_end(self):
        if self.probation_end_date and self.status == "probation":
            delta = self.probation_end_date - datetime.utcnow().date()
            return delta.days
        return None

    @property
    def probation_alert(self):
        days = self.days_until_probation_end
        if days is None:
            return None
        if days <= 0:
            return "overdue"
        if days <= 7:
            return "urgent"
        if days <= 14:
            return "upcoming"
        return None

    @property
    def contract_alert(self):
        """预警合同到期"""
        if self.contract_end_date:
            days = (self.contract_end_date - datetime.utcnow().date()).days
            if days <= 30:
                return "urgent"
            if days <= 60:
                return "upcoming"
        return None

    @property
    def onboard_token_status(self) -> str:
        """Token status: 'valid' / 'expired' / 'used' / 'none'"""
        if not self.onboard_token:
            return "none"
        if self.onboard_completed == "Y":
            return "used"
        if self.onboard_token_expires_at:
            if datetime.utcnow() > self.onboard_token_expires_at:
                return "expired"
        return "valid"
