import json
import httpx
from ai_service.base import LLMProvider


class DeepSeekProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": 4096,
        }
        resp = httpx.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


class MockProvider(LLMProvider):
    """Mock provider for development without API key. Returns realistic demo data."""

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        combined = system_prompt + user_prompt

        if "提出3-5个关键追问" in combined:
            return json.dumps(self._probe_questions(user_prompt), ensure_ascii=False)
        elif "岗位名称:" in user_prompt and ("所属部门" in user_prompt or "公司:" in user_prompt):
            return json.dumps(self._full_profile(user_prompt), ensure_ascii=False)
        elif "Match Report" in combined or "匹配分析报告" in combined or "人才评估" in system_prompt:
            return json.dumps(self._match_report(), ensure_ascii=False)
        elif "简历" in combined:
            # Detect role from system prompt keywords
            if "tech_stack_depth" in system_prompt or "技术岗位特化" in system_prompt:
                return json.dumps(self._candidate_profile_tech(), ensure_ascii=False)
            elif "portfolio_url" in system_prompt or "设计岗位特化" in system_prompt:
                return json.dumps(self._candidate_profile_design(), ensure_ascii=False)
            else:
                return json.dumps(self._candidate_profile(), ensure_ascii=False)
        elif "JD" in combined or "岗位描述" in combined or "extract from JD" in system_prompt.lower():
            return json.dumps(self._job_profile(), ensure_ascii=False)
        else:
            return json.dumps(self._match_report(), ensure_ascii=False)

    @staticmethod
    def _job_profile():
        return {
            "role_category": "tech",
            "responsibilities": [
                "负责AI产品的需求分析和产品设计",
                "协调算法和工程团队完成产品落地",
                "制定产品路线图并跟踪执行",
                "分析用户反馈和数据，持续优化产品体验",
            ],
            "required_skills": ["AI/ML基础理解", "产品需求分析", "跨团队协作", "数据分析能力", "项目管理"],
            "skill_tags": ["AI应用", "产品设计", "LLM", "Agent", "项目管理", "数据分析", "用户研究"],
            "experience_requirements": {"years_min": 3, "industry": ["互联网", "企业服务"], "preferred": ["AI产品经验", "B端SaaS经验"]},
            "weight_distribution": {"ai_understanding": 40, "product_ability": 30, "project_experience": 20, "education": 10},
        }

    @staticmethod
    def _candidate_profile():
        return {
            "name": "张三",
            "email": "zhangsan@example.com",
            "phone": "13800138000",
            "years_of_experience": 5,
            "highest_degree": "硕士",
            "current_position": "高级产品经理",
            "current_company": "XX科技有限公司",
            "skills": ["AI Agent", "Python", "产品设计", "项目管理", "LLM应用", "用户研究", "数据分析", "敏捷开发"],
            "strengths": ["有AI产品从0到1经验", "产品设计能力扎实", "跨团队协作能力强"],
            "risks": ["商业化经验不足", "缺少国际化产品经验"],
            "work_experience": [
                {
                    "company": "XX科技有限公司",
                    "position": "高级产品经理",
                    "start_date": "2023-01",
                    "end_date": "至今",
                    "projects": [{"name": "企业AI助手平台", "description": "从0到1搭建AI助手产品，服务500+企业客户", "highlights": ["设计Agent工作流编排功能", "产品上线后月活增长300%"]}],
                },
                {
                    "company": "YY网络科技",
                    "position": "产品经理",
                    "start_date": "2021-06",
                    "end_date": "2022-12",
                    "projects": [{"name": "SaaS后台管理系统", "description": "负责权限管理和数据分析模块", "highlights": ["重构权限体系", "搭建数据看板，提升效率40%"]}],
                },
            ],
            "education": [
                {"school": "北京大学", "degree": "硕士", "major": "计算机科学与技术", "start_year": 2019, "end_year": 2021},
                {"school": "武汉大学", "degree": "本科", "major": "信息管理与信息系统", "start_year": 2015, "end_year": 2019},
            ],
        }

    @staticmethod
    def _probe_questions(user_prompt: str):
        """Generate smart follow-up questions based on context."""
        questions = [
            "这个岗位第一个季度最重要的交付成果是什么？",
            "团队成员背景是怎样的？需要这个人和什么角色紧密配合？",
        ]
        if "产品" in user_prompt:
            questions.insert(0, "这个产品目前核心用户是谁？日活大概多少？")
        if "增长" in user_prompt or "运营" in user_prompt:
            questions.insert(0, "当前增长的主要瓶颈在哪？获客、激活还是留存？")
        if "技术" in user_prompt:
            questions.insert(0, "需要这个人有技术背景到什么程度？要能看懂代码还是能写代码？")
        if len(questions) > 5:
            questions = questions[:5]
        return questions

    @staticmethod
    def _full_profile(user_prompt: str):
        """Generate a complete job profile with competency model and evaluation framework."""
        company = "演示公司"
        title = "产品经理"
        industry = "互联网"
        for line in user_prompt.split("\n"):
            if "公司:" in line:
                company = line.split(":", 1)[1].strip()
            elif "行业:" in line:
                industry = line.split(":", 1)[1].strip()
            elif "岗位名称:" in line:
                title = line.split(":", 1)[1].strip()

        # Extract hiring reason from prompt if present
        hiring_reason = ""
        team_context = ""
        three_month = ""
        for line in user_prompt.split("\n"):
            if "招聘原因:" in line:
                hiring_reason = line.split(":", 1)[1].strip()
            elif "团队情况:" in line:
                team_context = line.split(":", 1)[1].strip()
            elif "3个月目标" in line or "入职3个月" in line:
                three_month = line.split(":", 1)[1].strip()

        return {
            "hiring_brief": {
                "goal": hiring_reason or f"为{company}组建{title}能力，推动核心业务目标达成",
                "success_criteria": [
                    three_month or f"入职3个月内完成{industry}业务需求调研，输出产品路线图",
                    f"入职6个月内推动至少一个产品模块从规划到上线",
                ],
                "key_challenges": [f"快速理解{industry}行业特点和用户需求", "在现有团队结构中建立有效的协作模式"],
                "team_fit": team_context or f"该岗位将独立负责{title}方向，与现有团队紧密配合",
            },
            "job_goal": f"负责{company}{title}的全流程工作，推动产品从当前阶段向下一阶段演进",
            "business_context": f"{company}是一家{industry}领域的公司，当前需要{title}来推进核心业务目标",
            "responsibilities": [
                f"负责需求分析与产品规划",
                f"协调内外部资源推动产品落地",
                f"跟踪产品数据，持续优化核心指标",
                f"与业务方密切沟通，将业务需求转化为产品方案",
            ],
            "required_skills": ["需求分析能力", "产品设计能力", "跨团队协作", "数据分析", "行业理解"],
            "skill_tags": ["产品设计", "需求管理", "数据分析", "用户研究", "项目管理", "行业知识"],
            "competency_model": {
                "业务能力": ["行业理解", "需求优先级判断", "商业化思维"],
                "产品能力": ["产品设计", "用户研究", "数据分析"],
                "软技能": ["跨部门沟通", "向上管理", "项目推动"],
            },
            "evaluation_framework": {
                "A级-直接上岗": f"3年以上{industry}产品经验，独立负责过类似项目，有从0到1经验",
                "B级-可培养": "具备产品基本功，行业经验可补，有较强的学习能力和成长潜力",
                "C级-不推荐": "缺乏产品核心能力或行业理解，建议关注其他方向",
            },
            "weight_distribution": {"产品能力": 35, "行业理解": 25, "项目经验": 25, "沟通协作": 15},
            "experience_requirements": {"years_min": 2, "industry": [industry], "preferred": ["有从0到1经验", f"{industry}背景"]},
            "interview_focus": [
                "产品设计方法论和实际案例",
                "如何处理需求冲突和资源不足的情况",
                "对行业的理解深度和趋势判断",
            ],
            "unconfirmed": [],
        }

    @staticmethod
    def _candidate_profile_tech():
        """Mock candidate profile for tech roles (backend/frontend/mobile/DevOps etc)."""
        return {
            "name": "李四",
            "email": "lisi@example.com",
            "phone": "13900139000",
            "years_of_experience": 6,
            "highest_degree": "本科",
            "current_position": "高级后端工程师",
            "current_company": "YY技术有限公司",
            "skills": ["Go", "Python", "Kubernetes", "PostgreSQL", "Redis", "gRPC", "微服务", "系统设计", "CI/CD"],
            "strengths": ["分布式系统设计经验丰富", "高并发场景实战", "开源项目贡献者"],
            "risks": ["缺少AI/ML相关经验", "团队管理经验不足"],
            "tech_stack_depth": {
                "primary_languages": ["Go", "Python"],
                "scale_context": "日均处理10亿+请求的微服务架构，200+服务实例"
            },
            "github_username": "lisitech",
            "open_source_contributions": ["Kubernetes sig-contributor", "自研开源RPC框架2000+ stars"],
            "system_design_experience": ["设计过支持千万QPS的广告投放系统"],
            "architecture_experience": ["主导公司从单体到微服务的架构升级"],
            "code_quality_indicators": ["团队CI/CD覆盖率95%", "主导代码review规范建设"],
            "work_experience": [
                {
                    "company": "YY技术有限公司",
                    "position": "高级后端工程师",
                    "start_date": "2021-03",
                    "end_date": "至今",
                    "projects": [
                        {"name": "实时计算平台", "description": "基于Flink的实时数据处理平台，日处理数据量100TB+", "highlights": ["设计多级容错机制", "P99延迟从500ms降到50ms"]}
                    ],
                },
                {
                    "company": "ZZ互联网公司",
                    "position": "后端工程师",
                    "start_date": "2019-06",
                    "end_date": "2021-02",
                    "projects": [
                        {"name": "支付系统", "description": "对接微信、支付宝支付网关", "highlights": ["优化支付回调延迟", "设计幂等防重机制"]}
                    ],
                },
            ],
            "education": [
                {"school": "华中科技大学", "degree": "本科", "major": "软件工程", "start_year": 2015, "end_year": 2019},
            ],
        }

    @staticmethod
    def _candidate_profile_design():
        """Mock candidate profile for design roles (UI/UX/visual/brand etc)."""
        return {
            "name": "王五",
            "email": "wangwu@example.com",
            "phone": "13700137000",
            "years_of_experience": 4,
            "highest_degree": "本科",
            "current_position": "资深UI设计师",
            "current_company": "AA设计工作室",
            "skills": ["Figma", "Sketch", "After Effects", "Design System", "用户研究", "原型设计", "交互设计"],
            "strengths": ["设计系统搭建经验", "B2B SaaS产品设计经验", "用户研究方法扎实"],
            "risks": ["缺少品牌设计项目经验", "国际化产品设计经验不足"],
            "portfolio_url": "https://dribbble.com/wangwu",
            "design_tools": [
                {"tool": "Figma", "proficiency": "expert"},
                {"tool": "Sketch", "proficiency": "advanced"},
                {"tool": "After Effects", "proficiency": "intermediate"},
            ],
            "design_methodology": ["Design Thinking", "原子设计", "用户旅程地图"],
            "project_types": ["B2B", "B2C"],
            "design_system_experience": "从0到1搭建包含200+组件的企业级设计系统，服务3条产品线",
            "work_experience": [
                {
                    "company": "AA设计工作室",
                    "position": "资深UI设计师",
                    "start_date": "2022-01",
                    "end_date": "至今",
                    "projects": [
                        {"name": "企业级SaaS设计系统", "description": "搭建统一的设计规范和组件库", "highlights": ["200+组件覆盖", "3条产品线统一设计语言"]}
                    ],
                },
                {
                    "company": "BB互联网",
                    "position": "UI设计师",
                    "start_date": "2020-07",
                    "end_date": "2021-12",
                    "projects": [
                        {"name": "电商App改版", "description": "主导首页和商品详情页的视觉改版", "highlights": ["改版后转化率提升15%"]}
                    ],
                },
            ],
            "education": [
                {"school": "中国美术学院", "degree": "本科", "major": "视觉传达设计", "start_year": 2016, "end_year": 2020},
            ],
        }

    @staticmethod
    def _match_report():
        return {
            "overall_conclusion": "推荐进入初面",
            "star_rating": 4,
            "summary": "候选人具备扎实的AI产品经验和产品设计能力，与岗位高度匹配。主要风险在于缺少B端SaaS经验。",
            "strengths": [
                {"point": "有AI项目实战经验", "evidence": "从0到1搭建企业AI助手平台，与岗位AI产品方向高度匹配"},
                {"point": "产品设计能力扎实", "evidence": "SaaS后台 + AI产品双重经验"},
                {"point": "有流程优化相关经验", "evidence": "Agent工作流编排是核心项目，体现了抽象和设计能力"},
            ],
            "gaps": [
                {"point": "缺少B端SaaS经验", "evidence": "简历中没有体现面向企业客户的SaaS产品经验"},
                {"point": "商业化经验不足", "evidence": "项目描述偏产品功能，缺少商业化指标的体现"},
            ],
            "interview_suggestions": [
                "了解他对AI产品商业化的看法",
                "考察跨团队协作的具体案例",
                "询问离职原因和职业发展规划",
                "让他现场分析一款AI产品的设计逻辑",
            ],
            "dimension_scores": {"ai_understanding": "high", "product_ability": "mid_high", "project_experience": "high", "education": "mid_high"},
        }
