"""AI Employee Profile Generator — builds a comprehensive capability portrait
from all available employee data (resume, evaluations, feedback, match report).
"""

import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ai_service.base import get_provider

PROMPT = """你是一位资深HRBP和组织发展专家。你正在为一位员工生成综合能力画像。

任务：综合员工的所有数据（招聘时的候选人画像、AI匹配报告、面试反馈、试用期评估），生成结构化的员工能力画像。

评估维度（每个维度1-10分，10分为该领域顶尖）：
1. technical_expertise: 专业能力 — 岗位所需硬技能的掌握程度
2. business_acumen: 业务理解 — 对公司业务、行业、用户需求的理解深度
3. execution: 执行力 — 完成任务的质量、效率、闭环能力
4. collaboration: 团队协作 — 跨部门沟通、团队配合、知识分享
5. growth_potential: 成长潜力 — 学习速度、主动性、发展空间
6. leadership: 领导力 — 影响力、决策力、带人能力（对非管理者此项可偏低）

输出要求：
1. 只输出JSON
2. scores 每个维度必须有1-10的分数和一句话依据
3. strengths 写3-5个核心优势，每个附具体证据
4. growth_areas 写2-3个待发展领域，附建议
5. career_stage 判断职业阶段：early（成长期）/ growth（快速发展期）/ mature（成熟期）/ plateau（瓶颈期）
6. team_role 团队角色定位：core_contributor / specialist / coordinator / mentor / potential_leader
7. summary 50-80字的综合画像总结

输出JSON格式：
{
  "scores": {
    "technical_expertise": {"score": 7, "evidence": "证据一句话"},
    "business_acumen": {"score": 6, "evidence": "证据一句话"},
    "execution": {"score": 8, "evidence": "证据一句话"},
    "collaboration": {"score": 5, "evidence": "证据一句话"},
    "growth_potential": {"score": 7, "evidence": "证据一句话"},
    "leadership": {"score": 4, "evidence": "证据一句话"}
  },
  "strengths": [
    {"point": "核心优势", "evidence": "具体证据"}
  ],
  "growth_areas": [
    {"point": "待发展领域", "suggestion": "发展建议"}
  ],
  "career_stage": "growth",
  "team_role": "core_contributor",
  "summary": "综合画像总结，50-80字"
}"""


def generate_employee_profile(employee_data: dict) -> dict:
    """Generate a comprehensive AI employee capability profile.

    employee_data should contain:
      - name, position, department
      - candidate_profile: original resume parse result
      - match_report: AI match analysis from hiring
      - interview_feedback: interviewer notes
      - probation_evaluations: list of stage assessments
      - education, skills
    """

    parts = [
        f"员工: {employee_data.get('name', '')}",
        f"岗位: {employee_data.get('position', '')}",
        f"部门: {employee_data.get('department', '')}",
    ]

    # Education & skills from candidate profile
    cp = employee_data.get("candidate_profile") or {}
    if cp:
        parts.append(f"\n教育: {cp.get('highest_degree','')} {cp.get('education','')}")
        skills = cp.get("skills", [])
        if skills:
            parts.append(f"技能标签: {', '.join(skills[:10])}")
        parts.append(f"经验年限: {cp.get('years_of_experience', '未知')}年")
        strengths = cp.get("strengths", [])
        if strengths:
            parts.append(f"简历自述优势: {'; '.join(strengths[:5])}")

    # Match report
    mr = employee_data.get("match_report") or {}
    if mr:
        parts.append(f"\n招聘时AI评级: {mr.get('star_rating','')}/5星")
        parts.append(f"AI结论: {mr.get('overall_conclusion','')}")
        ai_strengths = [s.get("point", "") for s in mr.get("strengths", [])]
        if ai_strengths:
            parts.append(f"AI识别的优势: {'; '.join(ai_strengths)}")
        ai_gaps = [g.get("point", "") for g in mr.get("gaps", [])]
        if ai_gaps:
            parts.append(f"AI识别的短板: {'; '.join(ai_gaps)}")

    # Interview feedback
    fb = employee_data.get("interview_feedback") or {}
    if fb:
        parts.append(f"\n面试评分: {fb.get('actual_rating','')}/5星")
        parts.append(f"面试观察: {fb.get('key_observations','')}")
        parts.append(f"面试官: {fb.get('interviewer','')}")

    # Probation evaluations
    evals = employee_data.get("probation_evaluations") or []
    if evals:
        parts.append(f"\n试用期评估 ({len(evals)}次):")
        for ev in evals:
            scores = ev.get("scores", {})
            if scores:
                parts.append(f"  {ev.get('stage','')}: "
                           f"适应{scores.get('adaption','-')}/"
                           f"产出{scores.get('performance','-')}/"
                           f"协作{scores.get('collaboration','-')}/"
                           f"潜力{scores.get('potential','-')}")
            parts.append(f"  优势: {ev.get('strengths','')[:80]}")
            parts.append(f"  建议: {ev.get('recommendation','')}")

    user_prompt = "\n".join(parts)

    try:
        provider = get_provider()
        raw = provider.chat(PROMPT, user_prompt, temperature=0.2)
        from ai_service.json_repair import parse_json
        result = parse_json(raw)
        return _validate_and_fix(result, employee_data)
    except Exception:
        return _fallback_profile(employee_data)


def _validate_and_fix(result: dict, employee_data: dict) -> dict:
    """Ensure all required fields exist with valid values."""
    dims = ["technical_expertise", "business_acumen", "execution",
            "collaboration", "growth_potential", "leadership"]
    default_scores = {}
    for d in dims:
        val = (result.get("scores", {}).get(d, {}) if isinstance(result.get("scores", {}).get(d), dict)
               else {"score": 5, "evidence": ""})
        if not isinstance(val, dict):
            val = {"score": 5, "evidence": str(val)}
        score = val.get("score", 5)
        if not isinstance(score, (int, float)) or score < 1 or score > 10:
            score = 5
        default_scores[d] = {
            "score": int(score),
            "evidence": val.get("evidence", "") or ""
        }

    result["scores"] = default_scores
    result["strengths"] = result.get("strengths") or []
    result["growth_areas"] = result.get("growth_areas") or []
    result["career_stage"] = result.get("career_stage", "growth")
    result["team_role"] = result.get("team_role", "core_contributor")
    result["summary"] = result.get("summary", employee_data.get("name", "") + "的综合画像")
    result["generated_at"] = __import__("datetime").date.today().isoformat()
    return result


def _fallback_profile(data: dict) -> dict:
    """Rule-based fallback when AI is unavailable."""
    name = data.get("name", "")
    position = data.get("position", "")

    # Heuristic scoring based on available data
    scores = {
        "technical_expertise": {"score": 6, "evidence": "基于技能标签和岗位匹配的基础评估"},
        "business_acumen": {"score": 5, "evidence": "暂无足够业务反馈数据"},
        "execution": {"score": 6, "evidence": "基于试用期任务完成情况"},
        "collaboration": {"score": 5, "evidence": "基于团队反馈默认评分"},
        "growth_potential": {"score": 6, "evidence": "基于学习和适应的初步判断"},
        "leadership": {"score": 4, "evidence": "暂无领导力相关数据"},
    }

    # Adjust from probation evals if available
    evals = data.get("probation_evaluations") or []
    if evals:
        eval_scores = {}
        for ev in evals:
            s = ev.get("scores", {})
            for k, v in s.items():
                if v and isinstance(v, (int, float)):
                    eval_scores[k] = max(eval_scores.get(k, 0), v)

        if eval_scores:
            avg_perf = (eval_scores.get("performance", 3) + eval_scores.get("adaption", 3)) / 2
            scores["execution"] = {"score": min(10, round(avg_perf * 1.7)), "evidence": "基于试用期产出和适应评分"}
            scores["collaboration"] = {"score": min(10, round(eval_scores.get("collaboration", 3) * 1.7)),
                                        "evidence": "基于试用期协作评分"}
            scores["growth_potential"] = {"score": min(10, round(eval_scores.get("potential", 3) * 1.7)),
                                           "evidence": "基于试用期潜力评分"}

    # Adjust from match report
    mr = data.get("match_report") or {}
    ai_star = mr.get("star_rating", 0)
    if ai_star:
        scores["technical_expertise"]["score"] = min(10, ai_star * 2)
        scores["technical_expertise"]["evidence"] = f"AI匹配{ai_star}星，岗位匹配度参考"

    return {
        "scores": scores,
        "strengths": [
            {"point": "具备岗位所需的基本能力", "evidence": "简历和面试反馈支撑"}],
        "growth_areas": [
            {"point": "试用期数据不足", "suggestion": "建议在1-2次试用期评估后再生成完整画像"}],
        "career_stage": "growth",
        "team_role": "core_contributor",
        "summary": f"{name}（{position}）展现了基本胜任力，随着试用期推进将获得更精准的画像。",
        "generated_at": __import__("datetime").date.today().isoformat(),
    }
