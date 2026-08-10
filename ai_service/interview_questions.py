"""AI-powered structured interview question generator.

Unlike the basic interview_suggestions in the match report, this generates
a complete interview script structured by phases, with deep-dive questions
tailored to the candidate's specific profile gaps and strengths.
"""

import json
from ai_service.base import get_provider

SYSTEM_PROMPT = """你是一位资深面试官，擅长根据候选人画像设计高命中率的面试问题。

任务：根据候选人画像（简历）、岗位画像（JD/能力模型）、AI匹配报告，生成一套结构化面试题。

核心原则：
1. **不问他没有的经验**：如果候选人缺少某领域经验，不要问"举例说明你的XX经验"，改为考察可迁移能力或学习意愿
2. **深挖不重复**：每个问题考察不同的能力维度，不要多个问题考察同一个点
3. **STAR追问**：行为面试题要引导候选人用 STAR 方式回答（情境→任务→行动→结果）
4. **基于证据**：每个问题要说明"为什么要问这个"——基于简历中的哪个点或匹配报告中的哪个gap
5. **难度适中**：不要出不可能答上来的题，也不要出太简单的题

输出JSON格式：
{
  "interview_structure": {
    "opening": [
      {"question": "问题文本", "why": "为什么问这个", "duration": "2min"}
    ],
    "technical_deep_dive": [
      {"question": "问题文本", "why": "为什么问这个", "dimension": "考察的能力维度", "duration": "5min"}
    ],
    "behavioral": [
      {"question": "问题文本", "why": "为什么问这个", "dimension": "考察的能力维度", "duration": "5min"}
    ],
    "situational": [
      {"question": "问题文本", "why": "为什么问这个", "scenario": "什么情景", "duration": "5min"}
    ],
    "closing": [
      {"question": "问题文本", "why": "为什么问这个", "duration": "2min"}
    ]
  },
  "interview_focus": ["本次面试重点验证的3个核心问题"],
  "estimated_total_duration": "45min",
  "difficulty_assessment": "中等偏难——候选人在XX方面经验丰富，但在YY方面需要重点考察"
}

每个阶段的问题数量：
- opening: 1-2个
- technical_deep_dive: 2-3个
- behavioral: 2-3个
- situational: 1-2个
- closing: 1个

要求：只输出JSON。"""


def generate_interview_questions(
    candidate_profile: dict,
    job_profile: dict,
    match_report: dict,
) -> dict:
    """Generate a structured interview script.

    Args:
        candidate_profile: From Candidate.profile (resume parse result)
        job_profile: From Job.job_profile (JD analysis result)
        match_report: From AIAnalysis.match_report (strengths, gaps, suggestions)
    """
    # Build rich context
    parts = ["## 候选人画像", json.dumps(candidate_profile, ensure_ascii=False, indent=2)]
    parts.append("\n## 岗位画像")
    parts.append(json.dumps(job_profile, ensure_ascii=False, indent=2))
    parts.append("\n## AI匹配报告")
    parts.append(json.dumps(match_report, ensure_ascii=False, indent=2))

    # Highlight key gaps for the interviewer
    strengths = [s.get("point", "") for s in match_report.get("strengths", [])]
    gaps = [g.get("point", "") for g in match_report.get("gaps", [])]
    parts.append(f"\n## 面试重点提示")
    parts.append(f"已验证的优势: {'; '.join(strengths) if strengths else '暂无'}")
    parts.append(f"需要验证的短板: {'; '.join(gaps) if gaps else '暂无'}")
    parts.append(f"AI匹配星级: {match_report.get('star_rating','?')}/5")

    # Add company knowledge
    from ai_service.knowledge_context import get_company_context
    ctx = get_company_context()
    if ctx:
        parts.insert(0, f"## 公司背景知识\n{ctx}\n")

    user_prompt = "\n".join(parts)

    provider = get_provider()
    raw = provider.chat(SYSTEM_PROMPT, user_prompt, temperature=0.3)

    from ai_service.json_repair import parse_json
    try:
        result = parse_json(raw)
        return _validate(result)
    except Exception:
        return _fallback(candidate_profile, job_profile, match_report)


def _validate(result: dict) -> dict:
    """Ensure all required sections exist."""
    required = ["opening", "technical_deep_dive", "behavioral", "situational", "closing"]
    structure = result.get("interview_structure", {})
    for key in required:
        if key not in structure:
            structure[key] = [{"question": "请自我介绍并简述职业经历", "why": "开场暖场", "duration": "3min"}]

    result["interview_structure"] = structure
    result["estimated_total_duration"] = result.get("estimated_total_duration", "45min")
    result["interview_focus"] = result.get("interview_focus", [])
    result["difficulty_assessment"] = result.get("difficulty_assessment", "")
    return result


def _fallback(candidate_profile: dict, job_profile: dict, match_report: dict) -> dict:
    """Generate a basic interview script without AI (rule-based fallback)."""
    name = candidate_profile.get("name", "候选人")
    skills = candidate_profile.get("skills", [])
    strengths = [s.get("point", "") for s in match_report.get("strengths", [])]
    gaps = [g.get("point", "") for g in match_report.get("gaps", [])]
    star = match_report.get("star_rating", 3)

    technical = []
    if skills:
        top_skills = skills[:3]
        technical.append({
            "question": f"你在简历中提到{', '.join(top_skills)}，请选一项讲一个你用它解决过的最复杂的问题",
            "why": "验证核心技术能力的深度",
            "dimension": "技术深度",
            "duration": "5min",
        })
    technical.append({
        "question": "在你做过的项目里，哪个让你最有成就感？具体讲讲你的角色和贡献",
        "why": "了解候选人的项目参与深度和自我认知",
        "dimension": "项目经验",
        "duration": "5min",
    })

    behavioral = []
    if gaps:
        behavioral.append({
            "question": f"从你的简历看，对{gaps[0]}的经验较少。你通常会怎么快速补齐一个不熟悉的领域？举个例子",
            "why": "考察学习能力和成长心态",
            "dimension": "学习能力",
            "duration": "4min",
        })

    # Cross-team collaboration is always relevant
    behavioral.append({
        "question": "请讲一个你和同事意见严重分歧的例子——你是怎么处理的？最后结果如何？",
        "why": "考察冲突处理和沟通能力",
        "dimension": "协作能力",
        "duration": "5min",
    })
    behavioral.append({
        "question": "你有没有在资源或时间严重不足的情况下完成一项任务的经历？你是怎么做的？",
        "why": "考察执行力和抗压能力",
        "dimension": "执行力",
        "duration": "4min",
    })

    situational = [{
        "question": "假设你是这个岗位的新人，入职后发现团队的工作方式和你的习惯差异很大，你会怎么处理？",
        "why": "考察适应能力和文化契合度",
        "scenario": "入职适应",
        "duration": "4min",
    }]

    # Motivation + fit
    situational.append({
        "question": "如果这个岗位有两个方向可以深入发展——一个是继续深耕你的现有技能，另一个是拓展全新的领域，你会怎么选？为什么？",
        "why": "了解职业发展偏好和风险偏好",
        "scenario": "职业规划",
        "duration": "4min",
    })

    return {
        "interview_structure": {
            "opening": [{"question": "请简单做个自我介绍，以及你为什么对这个岗位感兴趣？", "why": "暖场并了解求职动机", "duration": "3min"}],
            "technical_deep_dive": technical,
            "behavioral": behavioral,
            "situational": situational,
            "closing": [{"question": "你有什么想问我们的吗？", "why": "了解候选人的关注点和思考深度", "duration": "2min"}],
        },
        "interview_focus": gaps[:2] if gaps else ["验证技术能力深度", "评估团队协作和沟通能力"],
        "estimated_total_duration": "40min",
        "difficulty_assessment": f"匹配度{star}星——{'需要重点验证短板领域' if star < 4 else '以确认匹配度为主，辅以文化契合度考察'}",
    }
