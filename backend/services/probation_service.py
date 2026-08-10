"""Probation management: AI-powered milestone evaluations at 30/60/90 days.

Evaluations are stored as JSON on Employee.probation_evaluations.
The AI generates reports using DeepSeek's chat API.
"""

import json
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ai_service.base import get_provider

# Milestones: (days, label)
MILESTONES = [
    (30, "30天"),
    (60, "60天"),
    (90, "90天 / 转正评估"),
]

EVAL_SYSTEM_PROMPT = """你是一位经验丰富的HRBP，正在对试用期员工进行阶段性评估。

任务：根据员工基本信息和主管反馈，生成结构化的试用期评估报告。

评估维度（1-5分）：
- adaption: 适应速度 — 对公司文化、团队、工作流程的融入程度
- performance: 工作产出 — 任务完成质量和效率，是否达到岗位预期
- collaboration: 团队协作 — 与同事/跨部门的沟通配合
- potential: 成长潜力 — 学习能力、主动性、发展空间

要求：
1. 只输出JSON，不要任何额外文字
2. strengths 写2-3个具体优势，要结合员工信息
3. risks 写1-2个需要关注的风险点或待提升方向
4. recommendation 给出下一步建议（继续观察 / 安排1v1沟通 / 准备转正 / 建议延长试用期）
5. 评论要具体，不要写"表现良好"这种空话

输出JSON格式：
{
  "scores": {"adaption": 4, "performance": 3, "collaboration": 4, "potential": 4},
  "strengths": "具体优势描述，2-3句话",
  "risks": "风险点或待提升方向，1-2句话",
  "recommendation": "下一步建议",
  "summary": "50字以内的总结"
}"""


def _get_days_employed(hire_date_val) -> int:
    if isinstance(hire_date_val, str):
        hire_date_val = datetime.strptime(hire_date_val, "%Y-%m-%d").date()
    if hasattr(hire_date_val, "date"):
        hire_date_val = hire_date_val.date()
    return (date.today() - hire_date_val).days


def _get_current_milestone(days_employed: int, probation_months: int = 3) -> Optional[tuple[int, str]]:
    """Return the current milestone (day, label), or None if no milestone reached yet."""
    milestones = []
    if probation_months >= 1:
        milestones.append((30, "30天"))
    if probation_months >= 2:
        milestones.append((60, "60天"))
    milestones.append((probation_months * 30, "转正评估"))

    for day, label in milestones:
        if days_employed >= day - 5 and days_employed <= day + 5:  # 5-day window
            return (day, label)
    return None


def completion_rate(employee: dict) -> float:
    """What % of the employee's profile is filled in?"""
    fields = [
        "phone", "email", "id_number", "education_degree", "education_school",
        "bank_name", "bank_account", "emergency_contact_name", "emergency_contact_phone",
    ]
    filled = sum(1 for f in fields if employee.get(f))
    return round(filled / len(fields) * 100)


def _get_completed_milestones(evaluations: list) -> set:
    return {e.get("stage", "") for e in (evaluations or [])}


def generate_evaluation(employee: dict, manager_notes: str = "") -> dict:
    """Generate an AI-powered probation evaluation for the current milestone.

    Args:
        employee: Employee dict with name, position, department, hire_date, etc.
        manager_notes: Optional notes from the manager (30-200 chars recommended).

    Returns the evaluation dict, or raises ValueError if no milestone is due.
    """
    days = _get_days_employed(employee.get("hire_date"))
    milestone = _get_current_milestone(days, employee.get("probation_months", 3))

    if not milestone:
        raise ValueError(f"No milestone due. Employee has been employed for {days} days.")

    day_num, stage_label = milestone

    # Build context for AI
    parts = [
        f"员工姓名: {employee.get('name', '')}",
        f"岗位: {employee.get('position', '')}",
        f"部门: {employee.get('department', '')}",
        f"入职日期: {employee.get('hire_date', '')}",
        f"入职天数: {days}天",
        f"试用期: {employee.get('probation_months', 3)}个月",
        f"当前评估节点: {stage_label}（入职第{day_num}天）",
        f"学历: {employee.get('education_degree', '未知')} {employee.get('education_school', '')} {employee.get('education_major', '')}",
        f"档案完整度: {completion_rate(employee)}%",
    ]
    if manager_notes:
        parts.append(f"\n主管反馈:\n{manager_notes}")

    user_prompt = "\n".join(parts)

    provider = get_provider()
    raw = provider.chat(EVAL_SYSTEM_PROMPT, user_prompt, temperature=0.3)

    # Parse
    from ai_service.json_repair import parse_json
    try:
        result = parse_json(raw)
    except ValueError:
        # Fallback: build a basic evaluation manually
        result = {
            "scores": {"adaption": 3, "performance": 3, "collaboration": 3, "potential": 3},
            "strengths": f"{employee.get('name','员工')}在{days}天的试用期内展现了基本的工作能力，对团队和工作内容正在逐步适应。",
            "risks": "当前信息不足，建议主管安排定期1v1沟通以深入了解适应情况。",
            "recommendation": "继续观察，收集更多反馈",
            "summary": f"入职{days}天，处于{stage_label}节点，建议保持关注",
        }

    # Validate scores
    scores = result.get("scores", {})
    for dim in ["adaption", "performance", "collaboration", "potential"]:
        s = scores.get(dim, 3)
        if not isinstance(s, (int, float)) or s < 1 or s > 5:
            scores[dim] = 3
    result["scores"] = {k: int(v) for k, v in scores.items()}

    result["stage"] = stage_label
    result["day"] = day_num
    result["evaluated_at"] = date.today().isoformat()
    result["days_employed"] = days
    result["generated_by"] = "ai"

    return result


def add_manager_evaluation(employee_data: dict, manager_notes: str, scores: Optional[dict] = None) -> dict:
    """Add a manual evaluation by a manager (without AI)."""
    days = _get_days_employed(employee_data.get("hire_date"))

    return {
        "stage": f"主管评估（第{days}天）",
        "day": 0,
        "evaluated_at": date.today().isoformat(),
        "days_employed": days,
        "scores": scores or {"adaption": 0, "performance": 0, "collaboration": 0, "potential": 0},
        "strengths": manager_notes,
        "risks": "",
        "recommendation": "",
        "summary": manager_notes[:50] if len(manager_notes) > 50 else manager_notes,
        "generated_by": "manager",
    }
