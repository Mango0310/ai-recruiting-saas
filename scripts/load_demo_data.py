"""Load demo data with differentiated candidate profiles and intelligent matching."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ai_service"))

from database import engine, Base, SessionLocal
from models.company import Company

Base.metadata.create_all(bind=engine)

db = SessionLocal()

if db.query(Company).count() == 0:
    db.add(Company(name="演示公司", industry="互联网", size="50-200人"))
    db.commit()

from models.job import Job

if db.query(Job).count() > 0:
    print("Demo data already exists. Skipping.")
    db.close()
    sys.exit(0)

# ── Create jobs via real LLM ──
from services.jd_service import create_job_from_jd

demo_jobs = [
    {
        "title": "AI产品经理",
        "jd_raw": """岗位职责：
1. 负责AI产品的需求分析、市场调研和产品设计，制定产品路线图
2. 协调算法团队、工程团队和设计团队，推动产品从概念到落地
3. 持续跟踪AI行业技术趋势，将新技术转化为产品能力
4. 分析用户反馈和产品数据，持续优化产品体验和核心指标

任职要求：
1. 本科及以上学历，计算机、人工智能或相关专业优先
2. 3年以上互联网产品经理经验，其中至少1年AI相关产品经验
3. 对LLM、Agent、RAG等AI技术有基础理解，能与算法团队有效沟通
4. 具备扎实的产品设计能力和数据分析能力
5. 优秀的跨团队协作和项目管理能力

加分项：
- 有B端SaaS产品经验
- 有从0到1的产品经验""",
    },
    {
        "title": "海外运营经理",
        "jd_raw": """岗位职责：
1. 负责公司AI产品在海外市场的运营策略制定和执行
2. 搭建海外用户增长体系，制定获客、激活、留存策略
3. 分析海外用户行为数据，输出本地化运营方案
4. 管理海外社交媒体矩阵，策划内容营销活动

任职要求：
1. 本科及以上学历，市场营销、国际贸易或相关专业
2. 3年以上海外运营经验，熟悉东南亚或欧美市场
3. 英语流利（CET-6或同等水平），可作为工作语言
4. 有SaaS产品或AI产品运营经验优先
5. 具备数据分析能力，熟练使用Google Analytics等工具""",
    },
]

for jd in demo_jobs:
    job = create_job_from_jd(db, jd["title"], jd["jd_raw"])
    print(f"Created job: {job.title} (id={job.id})")

# ── Differentiated candidate profiles ──
candidates_data = [
    {
        "name": "张三",
        "email": "zhangsan@example.com",
        "phone": "13800001111",
        "years_of_experience": 5,
        "highest_degree": "硕士",
        "current_position": "高级产品经理",
        "current_company": "XX科技",
        "skills": ["AI Agent", "Python", "产品设计", "LLM应用", "项目管理", "用户研究", "数据分析"],
        "strengths": ["有AI产品从0到1经验", "产品设计能力扎实", "跨团队协作能力强"],
        "risks": ["商业化经验不足", "传统行业背景偏弱"],
        "work_experience": [
            {
                "company": "XX科技有限公司",
                "position": "高级产品经理",
                "start_date": "2023-01",
                "end_date": "至今",
                "projects": [
                    {
                        "name": "企业AI助手平台",
                        "description": "从0到1搭建AI助手产品，服务500+企业客户",
                        "highlights": ["设计Agent工作流编排功能", "产品上线后月活增长300%", "帮助企业客户效率提升40%"],
                    }
                ],
            },
            {
                "company": "YY网络科技",
                "position": "产品经理",
                "start_date": "2020-06",
                "end_date": "2022-12",
                "projects": [
                    {
                        "name": "SaaS后台管理系统",
                        "description": "负责权限管理和数据分析模块",
                        "highlights": ["重构权限体系，支持细粒度RBAC", "搭建数据看板"],
                    }
                ],
            },
        ],
        "education": [
            {"school": "北京大学", "degree": "硕士", "major": "计算机科学与技术", "start_year": 2018, "end_year": 2020},
            {"school": "武汉大学", "degree": "本科", "major": "信息管理", "start_year": 2014, "end_year": 2018},
        ],
    },
    {
        "name": "李四",
        "email": "lisi@example.com",
        "phone": "13800002222",
        "years_of_experience": 3,
        "highest_degree": "本科",
        "current_position": "产品经理",
        "current_company": "某在线教育公司",
        "skills": ["产品设计", "用户研究", "数据分析", "Axure", "SQL", "需求文档"],
        "strengths": ["产品基本功扎实", "用户研究经验丰富"],
        "risks": ["无AI相关经验", "技术理解力较弱", "缺少B端产品经验"],
        "work_experience": [
            {
                "company": "某在线教育公司",
                "position": "产品经理",
                "start_date": "2023-03",
                "end_date": "至今",
                "projects": [
                    {
                        "name": "在线课堂功能优化",
                        "description": "优化直播互动功能，提升用户留存",
                        "highlights": ["用户留存率提升15%", "完成20+需求迭代"],
                    }
                ],
            },
            {
                "company": "某电商公司",
                "position": "产品助理",
                "start_date": "2021-07",
                "end_date": "2023-02",
                "projects": [
                    {
                        "name": "商品详情页改版",
                        "description": "参与商品详情页的交互优化",
                        "highlights": ["转化率提升8%"],
                    }
                ],
            },
        ],
        "education": [
            {"school": "华中科技大学", "degree": "本科", "major": "市场营销", "start_year": 2017, "end_year": 2021},
        ],
    },
    {
        "name": "王五",
        "email": "wangwu@example.com",
        "phone": "13800003333",
        "years_of_experience": 4,
        "highest_degree": "硕士",
        "current_position": "海外运营总监",
        "current_company": "出海SaaS公司",
        "skills": ["海外运营", "用户增长", "Google Analytics", "社交媒体营销", "英语流利", "数据分析", "内容策略"],
        "strengths": ["丰富的海外市场经验", "SaaS产品运营背景", "数据驱动决策能力强"],
        "risks": ["国内招聘市场经验不足", "团队管理经验有限"],
        "work_experience": [
            {
                "company": "某出海SaaS公司",
                "position": "海外运营总监",
                "start_date": "2024-01",
                "end_date": "至今",
                "projects": [
                    {
                        "name": "东南亚市场拓展",
                        "description": "主导产品在东南亚市场的冷启动，6个月内获取10万用户",
                        "highlights": ["搭建本地化运营团队", "设计A/B测试框架提升转化30%", "管理印尼、越南双市场"],
                    }
                ],
            },
            {
                "company": "某跨境电商平台",
                "position": "海外运营经理",
                "start_date": "2021-03",
                "end_date": "2023-12",
                "projects": [
                    {
                        "name": "欧美市场用户增长",
                        "description": "通过社交媒体和内容营销实现用户增长",
                        "highlights": ["TikTok账号3个月涨粉50万", "搭建KOL合作网络"],
                    }
                ],
            },
        ],
        "education": [
            {"school": "复旦大学", "degree": "硕士", "major": "国际商务", "start_year": 2019, "end_year": 2021},
            {"school": "广东外语外贸大学", "degree": "本科", "major": "商务英语", "start_year": 2015, "end_year": 2019},
        ],
    },
    {
        "name": "赵六",
        "email": "zhaoliu@example.com",
        "phone": "13800004444",
        "years_of_experience": 1,
        "highest_degree": "本科",
        "current_position": "产品助理",
        "current_company": "某初创企业",
        "skills": ["Figma", "需求文档", "基础SQL", "竞品分析"],
        "strengths": ["学习能力强", "执行力好"],
        "risks": ["经验不足", "独立负责能力待验证", "无AI或运营相关经验"],
        "work_experience": [
            {
                "company": "某AI初创企业",
                "position": "产品实习生",
                "start_date": "2025-07",
                "end_date": "2025-12",
                "projects": [
                    {
                        "name": "产品需求管理",
                        "description": "协助产品经理整理需求和用户反馈",
                        "highlights": ["整理200+用户反馈", "输出竞品分析报告5份"],
                    }
                ],
            },
        ],
        "education": [
            {"school": "浙江大学", "degree": "本科", "major": "工业设计", "start_year": 2021, "end_year": 2025},
        ],
    },
]

from models.candidate import Candidate
from models.application import Application
from models.resume import Resume
from models.ai_analysis import AIAnalysis
from models.job import Job


def _fuzzy_match(job_tag: str, cand_skills: set) -> bool:
    """Check if job tag fuzzy-matches any candidate skill."""
    jt = job_tag.lower().strip()
    # Direct match
    if jt in cand_skills:
        return True
    # Token-based: split both into 2-char tokens
    for cs in cand_skills:
        cs = cs.lower().strip()
        if jt in cs or cs in jt:
            return True
        # Token overlap (for Chinese)
        jt_tokens = {jt[i:i+2] for i in range(len(jt)-1)}
        cs_tokens = {cs[i:i+2] for i in range(len(cs)-1)}
        if jt_tokens & cs_tokens:
            return True
    return False


def smart_match(job_profile: dict, candidate_profile: dict, job_title: str = "") -> dict:
    """Rule-based matching that produces differentiated results."""
    job_tags = [tag.lower() for tag in job_profile.get("skill_tags", [])]
    job_skills = [s.lower() for s in job_profile.get("required_skills", [])]
    cand_skills = set(s.lower() for s in candidate_profile.get("skills", []))
    cand_exp = candidate_profile.get("years_of_experience", 0)
    required_exp = job_profile.get("experience_requirements", {}).get("years_min", 0)
    preferred = [p.lower() for p in job_profile.get("experience_requirements", {}).get("preferred", [])]

    # Fuzzy overlap
    matched_tags = [jt for jt in job_tags if _fuzzy_match(jt, cand_skills)]
    overlap_ratio = len(matched_tags) / max(len(job_tags), 1)
    skill_overlap = set(matched_tags)

    # Star rating
    if overlap_ratio >= 0.5 and cand_exp >= required_exp:
        star = 5 if overlap_ratio >= 0.7 else 4
    elif overlap_ratio >= 0.3:
        star = 3
    elif overlap_ratio >= 0.1:
        star = 2
    else:
        star = 1

    # Build strengths
    strengths = []
    matched_skills = list(skill_overlap)[:4]
    for skill in matched_skills:
        strengths.append({"point": f"具备{skill}相关能力", "evidence": f"候选人技能标签中包含{skill}"})
    if cand_exp >= required_exp:
        strengths.append({"point": f"工作年限满足要求", "evidence": f"候选人{cand_exp}年经验，要求{required_exp}年"})
    if not strengths:
        strengths = [{"point": "基本条件达标", "evidence": "满足学历等基本门槛"}]

    # Build gaps
    gaps = []
    missing = [jt for jt in job_tags if not _fuzzy_match(jt, cand_skills)]
    for skill in list(missing)[:3]:
        gaps.append({"point": f"缺少{skill}相关经验", "evidence": f"岗位要求中包含{skill}，候选人未体现"})
    if cand_exp < required_exp:
        gaps.append({"point": f"工作年限不足", "evidence": f"候选人{cand_exp}年经验，要求{required_exp}年"})
    for pref in preferred:
        if not any(pref in s for s in cand_skills):
            gaps.append({"point": f"缺少优先条件：{pref}", "evidence": f"岗位优先考虑{pref}，候选人无此背景"})
    if not gaps:
        gaps = [{"point": "无明显短板", "evidence": "候选人背景与岗位要求基本匹配"}]

    # Dimension scores — use JD's actual weight_distribution keys
    dims = {}
    weight_dist = job_profile.get("weight_distribution", {})
    for dim_name in weight_dist.keys():
        # Fuzzy match the dimension name against candidate skills + profile text
        profile_text = json.dumps(candidate_profile, ensure_ascii=False).lower()
        dim_lower = dim_name.lower()
        # Count matches: dim name tokens in skills or profile text
        tokens = [dim_lower[i:i+2] for i in range(len(dim_lower)-1)]
        skill_matches = sum(1 for tk in tokens if any(tk in s.lower() for s in cand_skills))
        text_matches = sum(1 for tk in tokens if tk in profile_text)
        score = skill_matches + text_matches
        if score >= 5: dims[dim_name] = "high"
        elif score >= 3: dims[dim_name] = "mid_high"
        elif score >= 1: dims[dim_name] = "mid"
        else: dims[dim_name] = "mid_low"

    # Conclusion — use evaluation framework if available
    eval_fw = job_profile.get("evaluation_framework", {})
    eval_level = ""
    eval_desc = ""
    if eval_fw:
        a_key = next((k for k in eval_fw.keys() if "A" in k), None)
        b_key = next((k for k in eval_fw.keys() if "B" in k), None)
        c_key = next((k for k in eval_fw.keys() if "C" in k), None)
        if star >= 4:
            eval_level = a_key or "A级"
            eval_desc = eval_fw.get(a_key or "", "")
            conclusion = f"{eval_level}—建议优先面试"
            summary = eval_desc[:120] if eval_desc else "候选人与岗位评估标准高度匹配，建议优先安排面试。"
        elif star >= 3:
            eval_level = b_key or "B级"
            eval_desc = eval_fw.get(b_key or "", "")
            conclusion = f"{eval_level}—可进入面试"
            summary = eval_desc[:120] if eval_desc else "候选人部分达标，建议面试中进一步验证关键能力。"
        else:
            eval_level = c_key or "C级"
            conclusion = f"{eval_level}—暂不推荐"
            summary = "暂不满足岗位核心要求，建议放入人才库关注。"
    elif star >= 4:
        conclusion = "推荐进入初面"
        summary = "候选人与岗位匹配度较高，建议优先安排面试。"
    elif star == 3:
        conclusion = "可考虑进入初面"
        summary = "候选人部分匹配岗位要求，但存在明显短板，建议根据竞争情况决定是否面试。"
    elif star == 2:
        conclusion = "建议暂缓"
        summary = "候选人与岗位要求差距较大，建议放入人才库关注后续发展。"
    else:
        conclusion = "暂不推荐"
        summary = "候选人背景与岗位要求不匹配，建议关注其他岗位机会。"

    # Interview questions — quality over quantity, never ask what they can't answer
    suggestions = []
    role_is_product = "产品" in job_title
    role_is_ops = "运营" in job_title
    gap_labels = [g["point"] for g in gaps]

    # Q1: Competence — the hardest thing they've done (everyone gets this)
    if cand_exp >= 4:
        suggestions.append("请描述你做过的复杂度最高的一个项目——最难的不是成功的地方，而是中间你推翻过自己几次、为什么？")
    else:
        suggestions.append("在你做过的项目里，哪个让你最有成就感？讲一下你具体做了什么、怎么判断做对还是做错了？")

    # Q2: Based on the biggest gap — but ask about transferable ability, not the missing experience
    missing_keywords = " ".join(gap_labels)
    if "AI" in missing_keywords or "LLM" in missing_keywords:
        suggestions.append("你对AI能力的边界怎么判断？举个例子：用户想要一个功能，技术上可以实现但效果不稳定，作为PM你会怎么决策——是上线还是等到效果达标？")
    elif "SaaS" in missing_keywords or "B端" in missing_keywords:
        suggestions.append("如果你面对两个需求：一个是付费大客户提的紧急需求，一个是影响80%免费用户的基础体验问题，资源只够做一个，你怎么判断优先级？")
    elif "运营" in missing_keywords or "增长" in missing_keywords:
        suggestions.append("给你两周时间和一万元预算，让你验证一个增长假设，你会怎么设计实验？具体第一步做什么？")
    elif "技术" in missing_keywords:
        suggestions.append("当研发说'这个需求技术上实现不了'时，你觉得PM应该追问什么问题来确认是真的实现不了还是只是代价高？举个你经历过的例子")
    elif cand_exp <= 2:
        suggestions.append("你有没有在资源或经验不足的情况下完成过一件事？你是怎么弥补短板的？")
    else:
        suggestions.append("在你过去的经历中，有没有一个你做出来的方案被业务方或领导否掉的case？后来怎么样了？")

    # Q3: Role-specific deep dive
    if role_is_product:
        suggestions.append("请分析一个你最近用过的、你觉得产品设计很差的App——具体哪里差、如果你来做会改什么？目的是看你能不能清晰表达产品判断")
    elif role_is_ops:
        if cand_exp >= 3:
            suggestions.append("如果公司明天进入一个你完全不了解的国家市场，给你一周时间做进入策略，你的信息搜集和分析框架是什么样的？")
        else:
            suggestions.append("假设让你负责一个海外社交媒体账号从0开始运营，前三周你会做什么？具体每天的工作节奏是什么样的？")
    else:
        suggestions.append("过去一年里，你主动学过的一个跟你当前工作不完全相关的技能是什么？为什么选它？")

    # Q4: Collaboration / conflict — every role needs this
    suggestions.append("你合作过的同事里，有没有你觉得很难配合的人？你是怎么处理的——是绕过他、说服他、还是让步？结果怎么样？")

    # Strip duplicates by first 8 chars
    seen = set()
    unique = []
    for s in suggestions:
        prefix = s[:12]
        if prefix not in seen:
            seen.add(prefix)
            unique.append(s)
    suggestions = unique[:4]

    # Potential assessment — for junior candidates
    potential_signals = []
    potential_level = "low"
    if cand_exp <= 2:
        profile_text = json.dumps(candidate_profile, ensure_ascii=False).lower()
        strengths_text = " ".join(candidate_profile.get("strengths", [])).lower()
        # Check for growth signals
        if any(w in strengths_text for w in ["学习", "成长", "快速", "独立"]):
            potential_level = "medium"
            potential_signals.append({"signal": "学习意愿强", "evidence": "展现出快速学习和成长的意愿"})
        if cand_exp <= 1 and candidate_profile.get("highest_degree") in ("硕士", "博士"):
            potential_signals.append({"signal": "学术背景扎实", "evidence": f"{candidate_profile.get('highest_degree')}学历，理论基础好"})
        if any(s in profile_text for s in ["实习", "项目", "比赛", "开源"]):
            potential_level = "medium"
            potential_signals.append({"signal": "主动实践", "evidence": "在校期间有相关项目实践经验"})
        if not potential_signals:
            potential_signals = [{"signal": "需进一步考察", "evidence": "简历信息不足以评估潜质，建议面试中关注"}]
    elif cand_exp <= 3:
        potential_level = "medium"
        potential_signals = [{"signal": "有一定成长空间", "evidence": f"{cand_exp}年经验，处于快速成长期"}]
    else:
        potential_level = "high"
        potential_signals = [{"signal": "经验成熟", "evidence": f"{cand_exp}年经验，已证明持续成长能力"}]

    return {
        "overall_conclusion": conclusion,
        "star_rating": star,
        "summary": summary,
        "strengths": strengths,
        "gaps": gaps,
        "interview_suggestions": suggestions,
        "dimension_scores": dims,
        "potential_level": potential_level,
        "potential_signals": potential_signals,
        "eval_level": eval_level,
    }


# Create candidates and applications
for i, cdata in enumerate(candidates_data):
    # Remove non-profile fields for storage
    profile = {k: v for k, v in cdata.items() if k != "strengths" and k != "risks"}
    # Store strengths/risks inside profile
    profile["strengths"] = cdata["strengths"]
    profile["risks"] = cdata["risks"]

    candidate = Candidate(name=cdata["name"], email=cdata["email"], phone=cdata["phone"], profile=profile)

    # Generate embedding for demo candidate
    try:
        from ai_service.embeddings import mock_embedding
        search_text = f"{cdata.get('current_position','')} {cdata.get('current_company','')} {' '.join(cdata.get('skills',[]))}"
        candidate.embedding = mock_embedding(search_text)
    except Exception:
        pass

    db.add(candidate)
    db.flush()

    resume = Resume(file_name=f"{cdata['name']}_简历.pdf", file_path="demo", parse_status="completed", raw_text=json.dumps(profile, ensure_ascii=False))
    db.add(resume)
    db.flush()

    # Assign to jobs: first 2 for AI PM, last 2 for Overseas
    job_id = 1 if i < 2 else 2
    app = Application(job_id=job_id, candidate_id=candidate.id, resume_id=resume.id, status="ai_screened")
    db.add(app)
    db.flush()

    # Generate smart match report
    job = db.query(Job).filter(Job.id == job_id).first()
    report = smart_match(job.job_profile, profile, job.title)

    analysis = AIAnalysis(
        application_id=app.id,
        job_profile_snapshot=job.job_profile,
        candidate_profile_snapshot=profile,
        match_report=report,
        model_version="smart-mock-v1",
    )
    db.add(analysis)
    star = report.get("star_rating", "?")
    print(f"Created: {cdata['name']} → {job.title} → {star}星 → {report['overall_conclusion']}")

db.commit()
db.close()
print(f"\n{'='*50}")
print("Demo data loaded with differentiated matching!")
print(f"{'='*50}")
print("张三 (5年AI PM) → AI产品经理 → 应得4-5星")
print("李四 (3年传统PM) → AI产品经理 → 应得2-3星")
print("王五 (4年海外运营) → 海外运营经理 → 应得4-5星")
print("赵六 (1年实习生) → 海外运营经理 → 应得1-2星")
