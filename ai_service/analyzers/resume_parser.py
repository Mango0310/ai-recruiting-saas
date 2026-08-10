import json

from ai_service.base import get_provider
from ai_service.json_repair import parse_json

# Role-specific extensions merged into the base output schema
ROLE_EXTENSIONS = {
    "tech": {
        "tech_stack_depth": {
            "primary_languages": ["Python", "Go"],
            "scale_context": "使用规模场景描述（单体/微服务/高并发/大数据量等）"
        },
        "github_username": "从简历中提取的GitHub用户名或null",
        "open_source_contributions": ["开源贡献描述"],
        "system_design_experience": ["系统设计经验描述"],
        "architecture_experience": ["架构层面经验描述"],
        "code_quality_indicators": ["代码review/CI-CD/测试覆盖率等工程化信号"],
    },
    "design": {
        "portfolio_url": "作品集链接(Behance/Dribbble/个人网站)或null",
        "design_tools": [
            {"tool": "Figma", "proficiency": "expert"}
        ],
        "design_methodology": ["设计方法论关键词"],
        "project_types": ["B2B", "B2C", "品牌", "插画"],
        "design_system_experience": "设计系统/组件库经验描述或null",
    },
}


def _build_system_prompt(role_category: str) -> str:
    extension = ROLE_EXTENSIONS.get(role_category, {})

    base_schema = {
        "name": "姓名",
        "email": "邮箱或null",
        "phone": "电话或null",
        "years_of_experience": 5,
        "highest_degree": "硕士",
        "current_position": "当前职位",
        "current_company": "当前公司",
        "skills": ["技能1", "技能2"],
        "strengths": ["优势1", "优势2"],
        "risks": ["风险1", "风险2"],
        "work_experience": [
            {
                "company": "公司名",
                "position": "职位",
                "start_date": "2023-01",
                "end_date": "至今",
                "projects": [
                    {
                        "name": "项目名称",
                        "description": "项目简介",
                        "highlights": ["量化成果1", "量化成果2"]
                    }
                ]
            }
        ],
        "education": [
            {
                "school": "学校",
                "degree": "学位",
                "major": "专业",
                "start_year": 2019,
                "end_year": 2021
            }
        ],
    }

    output_schema = {**base_schema, **extension}

    role_labels = {"tech": "技术岗", "design": "设计岗", "generic": "通用岗"}
    role_label = role_labels.get(role_category, "通用岗")

    role_specific = ""
    if role_category == "tech":
        role_specific = """
**技术岗位特化解析要求：**
- tech_stack_depth: 分析技术栈深度。不只要列出技能名，还要根据简历中的项目规模推断使用场景（单体应用/微服务/高并发/大数据处理等）。primary_languages 提取候选人最核心的1-3门语言
- github_username: 如果简历中明确写了GitHub用户名或链接，必须提取
- open_source_contributions: 从简历中提取所有开源贡献相关描述（包括项目名和贡献内容）
- system_design_experience: 提取涉及系统设计、技术选型的经验描述
- architecture_experience: 提取架构层面的决策经验（如单体拆微服务、数据库选型等）
- code_quality_indicators: 提取代码review、CI/CD、自动化测试、代码规范等工程化实践信号
"""
    elif role_category == "design":
        role_specific = """
**设计岗位特化解析要求：**
- portfolio_url: 从简历中提取作品集链接（Behance、Dribbble、个人网站、站酷等），这是最重要的信号
- design_tools: 列出设计工具及熟练度，proficiency 用 expert/advanced/intermediate/beginner 四级
- design_methodology: 提取简历中体现的设计方法论（Design Thinking、原子设计、双钻模型、用户旅程地图等）
- project_types: 分类项目类型（B2B后台/B2C移动端/品牌设计/插画/3D/动效等）
- design_system_experience: 提取设计系统或组件库的搭建/维护经验
"""

    return f"""你是一位专业的简历解析专家，擅长从简历文本中提取结构化信息。

任务：分析以下简历文本，输出结构化的候选人画像JSON。
当前岗位类型: {role_label}

要求：
1. 只输出JSON，不要任何额外文字、不要markdown代码块标记
2. 如果某个字段在简历中找不到信息，填写合理的空值（null、空字符串、空数组、0）
3. work_experience按时间倒序排列（最近的在前）
4. skills标签控制在5-15个，提取具体技能名称
5. 日期格式统一为"YYYY-MM"或"YYYY"
6. projects中的highlights提取具体量化成果
{role_specific}
输出JSON格式：
{json.dumps(output_schema, ensure_ascii=False, indent=2)}"""


def parse_resume(resume_text: str, role_category: str = "generic") -> dict:
    provider = get_provider()
    system_prompt = _build_system_prompt(role_category)
    raw = provider.chat(system_prompt, resume_text, temperature=0.1)
    return _parse_response(resume_text, raw, role_category)


def _parse_response(resume_text: str, raw: str, role_category: str = "generic") -> dict:
    system_prompt = _build_system_prompt(role_category)
    try:
        result = parse_json(raw)
        _validate(result)
        return result
    except (ValueError, json.JSONDecodeError) as e:
        provider = get_provider()
        raw = provider.chat(system_prompt, f"上一次输出JSON格式错误，请严格只输出JSON。\n\n简历文本：\n{resume_text}", temperature=0.0)
        try:
            result = parse_json(raw)
            _validate(result)
            return result
        except (ValueError, json.JSONDecodeError) as e2:
            raise ValueError(f"Failed to parse resume after retry: {e2}\nRaw: {raw[:500]}")


def _validate(data: dict):
    required_keys = ["name", "skills", "work_experience", "education"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")
