"""Recruitment feedback loop: compare AI predictions with actual on-the-job performance.

After an employee completes probation, we compare:
  - AI match report prediction (star_rating, strengths, gaps)
  - Interview feedback (AI accuracy assessment)
  - Probation evaluation scores (real performance data)

This generates a "hiring quality" report and feeds back into the system
so the AI gets smarter about what traits predict success.
"""

import sys
from datetime import date
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ai_service.base import get_provider

FEEDBACK_SYSTEM_PROMPT = """你是一位数据分析师，正在评估招聘决策的质量。

任务：对比AI招聘时的预测和员工入职后的实际表现，生成招聘反馈闭环报告。

分析维度：
1. 预测准确度：AI当初判断的优势和不足，有多少在实际工作中得到了验证？
2. 关键信号：哪些初始特征最能预测这个人是否胜任？
3. 改进建议：AI的匹配模型可以从这个案例中学到什么？

要求：
1. 只输出JSON
2. prediction_accuracy: "accurate"(AI预测基本准确) / "partial"(部分准确部分偏差) / "inaccurate"(AI预测与实际表现差距大)
3. validated_strengths: 哪些AI预测的优势被实际表现验证了
4. missed_risks: AI当时没发现但实际暴露的问题
5. hiring_quality: 综合判断这个招聘决策的质量 — "excellent" / "good" / "acceptable" / "poor"
6. lesson: 从这次招聘中可以学到什么（50字以内）

输出JSON格式：
{
  "prediction_accuracy": "accurate",
  "validated_strengths": ["被验证的优势"],
  "missed_risks": ["AI没预测到但实际发生的问题"],
  "hiring_quality": "good",
  "overall_assessment": "2-3句话的综合评价",
  "lesson": "从这个案例中学到的经验教训"
}"""


def _compute_avg_score(scores: dict) -> float:
    if not scores:
        return 0
    dims = ["adaption", "performance", "collaboration", "potential"]
    vals = [scores.get(d, 0) for d in dims if scores.get(d, 0) > 0]
    return sum(vals) / len(vals) if vals else 0


def generate_feedback_report(
    match_report: Optional[dict],
    interview_feedback: Optional[dict],
    probation_evaluations: list,
    employee_name: str = "",
    position: str = "",
) -> dict:
    """Generate a hiring quality feedback report.

    Args:
        match_report: Original AI match report from application analysis
        interview_feedback: Interview feedback with AI prediction accuracy
        probation_evaluations: List of probation stage evaluations
        employee_name, position: Employee context

    Returns a feedback report dict. On LLM failure, returns a rule-based fallback.
    """
    ai_star = match_report.get("star_rating") if match_report else None
    ai_strengths = [s.get("point", "") for s in match_report.get("strengths", [])] if match_report else []
    ai_gaps = [g.get("point", "") for g in match_report.get("gaps", [])] if match_report else []
    ai_conclusion = match_report.get("overall_conclusion", "") if match_report else ""

    interview_accuracy = interview_feedback.get("ai_predictions_match", "") if interview_feedback else ""
    interview_rating = interview_feedback.get("actual_rating") if interview_feedback else None
    interview_observations = interview_feedback.get("key_observations", "") if interview_feedback else ""

    # Compute average probation score
    avg_eval_scores = []
    for ev in (probation_evaluations or []):
        if ev.get("scores"):
            avg = _compute_avg_score(ev["scores"])
            if avg > 0:
                avg_eval_scores.append(avg)

    overall_avg = sum(avg_eval_scores) / len(avg_eval_scores) if avg_eval_scores else None
    evaluation_count = len(avg_eval_scores)

    # Build context for AI
    parts = [
        f"员工: {employee_name}",
        f"岗位: {position}",
        "",
        "== AI招聘时的预测 ==",
        f"匹配星级: {ai_star}/5" if ai_star else "匹配星级: 无数据",
        f"AI判断的优势: {', '.join(ai_strengths)}" if ai_strengths else "",
        f"AI判断的不足: {', '.join(ai_gaps)}" if ai_gaps else "",
        f"AI结论: {ai_conclusion}",
        "",
        "== 面试反馈 ==",
        f"AI预测准确度: {interview_accuracy} (match=准确, partial=部分准确, no_match=不准确)",
        f"面试评分: {interview_rating}/5" if interview_rating else "",
        f"面试观察: {interview_observations}",
        "",
        "== 试用期表现 ==",
        f"评估次数: {evaluation_count}",
        f"综合评分: {overall_avg:.1f}/5.0" if overall_avg else "综合评分: 暂无",
    ]

    for i, ev in enumerate(probation_evaluations or []):
        if ev.get("scores"):
            parts.append(f"  {ev.get('stage','')}期: 适应{ev['scores'].get('adaption',0)} "
                        f"产出{ev['scores'].get('performance',0)} "
                        f"协作{ev['scores'].get('collaboration',0)} "
                        f"潜力{ev['scores'].get('potential',0)} "
                        f"建议: {ev.get('recommendation','')}")

    user_prompt = "\n".join(parts)

    # Try AI generation
    try:
        provider = get_provider()
        raw = provider.chat(FEEDBACK_SYSTEM_PROMPT, user_prompt, temperature=0.2)
        from ai_service.json_repair import parse_json
        result = parse_json(raw)
        result["computed"] = {
            "ai_star": ai_star,
            "interview_rating": interview_rating,
            "probation_avg": round(overall_avg, 1) if overall_avg else None,
            "evaluation_count": evaluation_count,
        }
        return result
    except Exception:
        pass

    # Rule-based fallback
    accuracy = "partial"
    if overall_avg is not None and ai_star is not None:
        pred_high = ai_star >= 4
        actual_high = overall_avg >= 3.5
        if pred_high == actual_high:
            accuracy = "accurate"
        elif pred_high and not actual_high:
            accuracy = "inaccurate"

    quality = "good"
    if overall_avg is not None:
        if overall_avg >= 4:
            quality = "excellent"
        elif overall_avg >= 3:
            quality = "good"
        elif overall_avg >= 2:
            quality = "acceptable"
        else:
            quality = "poor"

    validated = ai_strengths[:2] if ai_strengths else ["经验匹配"]
    missed = ai_gaps[:1] if ai_gaps else []

    return {
        "prediction_accuracy": accuracy,
        "validated_strengths": validated,
        "missed_risks": missed,
        "hiring_quality": quality,
        "overall_assessment": (
            f"AI预测{ai_star}星，实际表现{overall_avg:.1f}/5.0。"
            f"{'预测基本准确' if accuracy == 'accurate' else '预测与实际有偏差'}。"
            f"招聘质量：{quality}。"
        ) if overall_avg else "试用期数据不足，尚无法生成完整评估。",
        "lesson": ("高匹配候选人更倾向于在实际工作中表现优秀" if quality in ("excellent", "good")
                   else "需要关注面试中难以评估的软技能维度"),
        "computed": {
            "ai_star": ai_star,
            "interview_rating": interview_rating,
            "probation_avg": round(overall_avg, 1) if overall_avg else None,
            "evaluation_count": evaluation_count,
        },
    }
