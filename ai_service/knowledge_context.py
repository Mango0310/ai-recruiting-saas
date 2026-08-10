"""Load company knowledge from DB and build AI prompt context."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))


def get_company_context() -> str:
    """Read company knowledge from DB and return a prompt-ready context block.
    Returns empty string if no company/knowledge exists.
    """
    try:
        from database import SessionLocal
        from models.company import Company
        db = SessionLocal()
        try:
            company = db.query(Company).first()
            if not company:
                return ""

            parts = []

            if company.name and company.name != "演示公司":
                parts.append(f"公司名称: {company.name}")
            if company.industry:
                parts.append(f"行业: {company.industry}")
            if company.size:
                parts.append(f"规模: {company.size}")

            # Knowledge text (free-text: values, products, etc.)
            kt = (company.knowledge_text or "").strip()
            if kt:
                parts.append(f"\n公司知识:\n{kt}\n")

            # Uploaded documents
            docs = company.knowledge_docs or []
            if docs:
                parts.append("已上传的公司资料:")
                for d in docs:
                    snippet = (d.get("snippet") or "").strip()
                    if snippet:
                        parts.append(f"\n[{d['name']}]:\n{snippet[:1500]}")

            return "\n".join(parts).strip() if len(parts) > 1 else ""
        finally:
            db.close()
    except Exception:
        return ""
