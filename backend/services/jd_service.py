import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ai_service.base import get_provider
from ai_service.analyzers.jd_analyzer import analyze_jd
from models.job import Job

def create_job_from_jd(db, title: str, jd_text: str) -> Job:
    job_profile = analyze_jd(jd_text)
    job = Job(title=title, jd_raw=jd_text, job_profile=job_profile)

    # Generate embedding
    try:
        from ai_service.embeddings import generate_job_embedding, mock_embedding
        emb = generate_job_embedding(job_profile, title)
        if emb is None:
            emb = mock_embedding(f"{title} {json.dumps(job_profile, ensure_ascii=False)}")
        job.embedding = emb
    except Exception:
        pass

    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def reanalyze_job(db, job: Job) -> Job:
    if not job.jd_raw:
        raise ValueError("No JD text available for analysis")
    job_profile = analyze_jd(job.jd_raw)
    job.job_profile = job_profile
    db.commit()
    db.refresh(job)
    return job


PROBE_PROMPT = """你是一位资深招聘顾问。你正在帮助一位HR为一个岗位生成精准的招聘需求。

你的任务：根据HR提供的基础信息，提出3-5个关键追问来帮助精准化岗位画像。

**你需要特别关注招聘背景信息：**
- 如果HR提供了"为什么招人"（hiring_reason），你的追问要围绕这个目标来设计
- 如果HR提供了"团队现状"（team_context），追问要考虑现有人力结构和新人的角色定位
- 如果HR提供了"入职3个月目标"，追问要帮助明确达成目标所需的具体能力

追问原则：
1. 每个问题都要直接影响到招聘标准的制定
2. 问题的答案会改变岗位画像的权重、技能要求或评估标准
3. 不要问泛泛的问题（如"还有什么补充吗"），要问具体场景
4. 根据已填信息触类旁通

输出格式：只输出一个JSON数组，每个元素是一个问题字符串。"""

FULL_PROFILE_PROMPT = """你是一位资深招聘顾问。你正在帮一家公司为一个岗位生成结构化招聘画像。

**核心原则：基于已有信息做合理推断，而不是偷懒写"待确认"**

工作方式：
1. 阅读HR填写的所有信息（公司背景、岗位、业务阶段、AI追问回答等）
2. 把这些信息组织成结构化岗位画像
3. **根据公司行业和业务阶段合理推断**：如果你知道公司是"跨境电商SaaS"、业务阶段是"增长期"，你就应该能推断出这个岗位需要什么能力，而不是写"待确认"
4. **只有完全没有任何线索的字段才写"待确认"**。公司名+行业+业务阶段已经给了足够多的线索
5. 评估标准必须具体：不要写"待确认"，要根据公司业务阶段写出具体的A/B/C标准

**输出JSON格式：**

{
  "hiring_brief": {
    "goal": "招聘目标——一句话说清这个岗位存在的业务原因",
    "success_criteria": ["入职3个月的成功标准", "入职6个月的成功标准"],
    "key_challenges": ["这个岗位面临的最大挑战"],
    "team_fit": "与现有团队的协作关系"
  },
  "job_goal": "从输入中提取的岗位核心目标",
  "business_context": "从输入中总结的业务背景",
  "responsibilities": ["从输入中提取的职责"],
  "required_skills": ["从输入中提取的必备能力"],
  "skill_tags": ["从输入中提取的技能标签"],
  "competency_model": {
    "业务方强调的技术能力": ["具体技能"],
    "业务方强调的业务能力": ["具体能力"]
  },
  "evaluation_framework": {
    "A级-直接上岗": "根据业务方要求定义的最高标准",
    "B级-可培养": "根据业务方要求的可接受标准",
    "C级-不推荐": "不满足核心要求的底线"
  },
  "role_category": "tech",
  "weight_distribution": {"维度名": 30},
  "experience_requirements": {"years_min": 0, "industry": [], "preferred": []},
  "interview_focus": ["业务方最关心的验证点"],
  "unconfirmed": ["信息不完整需要业务方补充的项"]
}

**规则：**
- 基于公司行业+业务阶段+岗位名做合理推断，不要盲目写"待确认"
- 一个跨境电商SaaS公司的"AI产品经理"和一个医疗公司的"AI产品经理"能力要求完全不同——利用行业信息
- weight_distribution 基于业务方强调的重点 + 行业常识来定权重
- role_category 根据岗位名称和职责判断：技术研发类→"tech"，设计类→"design"，其他→"generic"
- 只输出JSON"""


def probe_questions(context: dict) -> list[str]:
    """Generate smart follow-up questions based on hiring context."""
    provider = get_provider()

    # Build context summary
    parts = [f"岗位: {context.get('title', '未提供')}"]
    if context.get("company_name"):
        parts.append(f"公司: {context['company_name']}")
    if context.get("company_industry"):
        parts.append(f"行业: {context['company_industry']}")
    if context.get("company_size"):
        parts.append(f"规模: {context['company_size']}")
    if context.get("requirement_source"):
        src_map = {"ceo": "CEO/创始人", "cpo": "产品负责人", "cto": "技术负责人", "business": "业务部门负责人", "hrbp": "HRBP转述", "other": "其他"}
        parts.append(f"需求来源: {src_map.get(context['requirement_source'], context['requirement_source'])}")
    if context.get("raw_requirements"):
        parts.append(f"业务方原始需求: {context['raw_requirements']}")
        stage_map = {"exploration": "探索期找PMF", "growth": "增长期规模化", "mature": "成熟期优化", "transform": "转型期变革"}
        parts.append(f"业务阶段: {stage_map.get(context['business_stage'], context['business_stage'])}")
    if context.get("target_audience"):
        aud_map = {"internal": "内部用户", "external": "外部客户", "both": "内外都有"}
        parts.append(f"服务对象: {aud_map.get(context['target_audience'], context['target_audience'])}")
    if context.get("product_stage"):
        stage_map = {"0-1": "0到1从零搭建", "iteration": "1到10持续迭代", "mature": "10到100成熟优化"}
        parts.append(f"产品阶段: {stage_map.get(context['product_stage'], context['product_stage'])}")
    if context.get("team_role"):
        role_map = {"independent": "独立负责", "assist": "协助执行", "lead": "带团队"}
        parts.append(f"角色: {role_map.get(context['team_role'], context['team_role'])}")
    if context.get("tech_required"):
        tech_map = {"must": "必须有技术背景", "preferred": "优先技术背景", "no": "不需要技术背景"}
        parts.append(f"技术要求: {tech_map.get(context['tech_required'], context['tech_required'])}")
    if context.get("department"):
        parts.append(f"部门: {context['department']}")
    if context.get("salary"):
        parts.append(f"薪资: {context['salary']}")
    if context.get("notes"):
        parts.append(f"备注: {context['notes']}")

    user_input = "\n".join(parts)

    raw = provider.chat(PROBE_PROMPT, user_input, temperature=0.3)
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return [
            "这个岗位需要对接哪些内部团队或外部合作伙伴？",
            "有没有已经在做类似事情的同事可以参考？",
            "这个岗位上的人半年内最重要的交付成果是什么？",
        ]


def generate_full_profile(db, context: dict) -> Job:
    """Generate a complete job profile with competency model and evaluation framework."""
    provider = get_provider()

    # Build rich input
    parts = [f"岗位名称: {context.get('title', '')}"]
    if context.get("company_name"):
        parts.append(f"公司: {context['company_name']}")
    if context.get("company_industry"):
        parts.append(f"行业: {context['company_industry']}")
    if context.get("company_size"):
        parts.append(f"规模: {context['company_size']}")
    if context.get("requirement_source"):
        parts.append(f"需求来源: {context['requirement_source']}")
    if context.get("raw_requirements"):
        parts.append(f"业务方原始需求: {context['raw_requirements']}")
    if context.get("hiring_reason"):
        parts.append(f"招聘原因: {context['hiring_reason']}")
    if context.get("team_context"):
        parts.append(f"团队情况: {context['team_context']}")
    if context.get("three_month_goal"):
        parts.append(f"入职3个月目标: {context['three_month_goal']}")
    if context.get("department"):
        parts.append(f"所属部门: {context['department']}")
    if context.get("reports_to"):
        parts.append(f"汇报对象: {context['reports_to']}")
    if context.get("salary"):
        parts.append(f"薪资范围: {context['salary']}")
    if context.get("business_stage"):
        parts.append(f"业务阶段: {context['business_stage']}")
    if context.get("target_audience"):
        parts.append(f"服务对象: {context['target_audience']}")
    if context.get("product_stage"):
        parts.append(f"产品阶段: {context['product_stage']}")
    if context.get("team_role"):
        parts.append(f"团队角色: {context['team_role']}")
    if context.get("tech_required"):
        parts.append(f"技术背景: {context['tech_required']}")
    if context.get("notes"):
        parts.append(f"补充说明: {context['notes']}")

    # Add AI Q&A
    qa_pairs = context.get("ai_questions", [])
    if qa_pairs:
        parts.append("\n--- AI追问与回答 ---")
        for qa in qa_pairs:
            q = qa.get("question", "")
            a = qa.get("answer", "")
            if a:
                parts.append(f"问: {q}\n答: {a}")

    # Inject company knowledge
    from ai_service.knowledge_context import get_company_context
    ctx = get_company_context()
    if ctx:
        parts.insert(0, f"## 公司背景知识（请参考以下信息生成贴合公司的岗位画像）\n{ctx}\n")

    user_input = "\n".join(parts)

    raw = provider.chat(FULL_PROFILE_PROMPT, user_input, temperature=0.1)

    # Parse
    import re
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        profile = json.loads(cleaned)
    except json.JSONDecodeError:
        # Retry once
        raw = provider.chat(FULL_PROFILE_PROMPT, f"上次输出格式错误，请严格输出纯JSON。\n\n{user_input}", temperature=0.0)
        cleaned = raw.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        profile = json.loads(cleaned)

    # Build jd_raw from input for reference
    jd_raw = f"岗位: {context.get('title')}\n" + "\n".join(parts)

    job = Job(
        title=context.get("title", "未命名岗位"),
        jd_raw=jd_raw,
        job_profile=profile,
    )

    # Generate embedding for semantic search
    try:
        from ai_service.embeddings import generate_job_embedding, mock_embedding
        emb = generate_job_embedding(profile, job.title)
        if emb is None:
            emb = mock_embedding(f"{job.title} {json.dumps(profile, ensure_ascii=False)}")
        job.embedding = emb
    except Exception:
        pass
    db.add(job)
    db.commit()
    db.refresh(job)
    return job
