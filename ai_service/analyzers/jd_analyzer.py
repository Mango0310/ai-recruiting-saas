import json

from ai_service.base import get_provider
from ai_service.json_repair import parse_json

SYSTEM_PROMPT = """你是一位资深招聘顾问，擅长根据公司业务背景和岗位需求，生成精准的结构化岗位画像。

任务：分析输入文本（可能包含公司业务描述和JD），输出结构化的岗位画像JSON。

**关键原则**：
- 如果输入包含公司业务描述，所有的职责、技能标签、维度权重都要结合公司业务来定
- 同一岗位在不同行业要求完全不同。例如"AI产品经理"：
  - 电商公司 → 重点在推荐算法、供应链AI、GMV增长
  - 医疗公司 → 重点在医疗合规、临床AI、数据隐私
  - SaaS公司 → 重点在B端体验、API集成、客户成功
- **不要生成通用的岗位画像，要生成这个公司在这个业务场景下真正需要的画像**

要求：
1. 只输出JSON，不要任何额外文字、不要markdown代码块标记
2. skill_tags 控制在5-8个标签，要结合业务场景
3. weight_distribution 的 key 是维度名称（中文，2-4个字），value 是0-100的整数，加起来等于100
4. **维度名称必须结合公司业务和JD来定**，每个维度反映这个公司在实际业务中真正看重的方面
5. 通常提取3-5个维度即可
6. years_min 如果没有明确写，默认填0
7. industry 根据公司业务和JD推断
8. preferred 填写结合了业务特点的优先条件或加分项
9. role_category 根据岗位名称和职责判断角色类型：技术研发类（后端/前端/移动端/AI/数据/运维/嵌入式/测试等）→"tech"，设计类（UI/UX/视觉/品牌/3D/插画/动效/交互等）→"design"，其他（产品/运营/销售/市场/人事/财务等）→"generic"

输出JSON格式：
{
  "role_category": "tech",
  "responsibilities": ["职责1", "职责2"],
  "required_skills": ["技能1", "技能2"],
  "skill_tags": ["标签1", "标签2"],
  "experience_requirements": {
    "years_min": 3,
    "industry": ["互联网"],
    "preferred": ["AI产品经验"]
  },
  "weight_distribution": {
    "产品思维": 40,
    "AI技术理解": 30,
    "项目经验": 20,
    "学历背景": 10
  }
}"""


def analyze_jd(jd_text: str) -> dict:
    provider = get_provider()

    # Inject company knowledge context
    from ai_service.knowledge_context import get_company_context
    ctx = get_company_context()
    user_prompt = jd_text
    if ctx:
        user_prompt = f"## 公司背景知识（请参考以下信息来生成更贴合公司的岗位画像）\n{ctx}\n\n## 岗位需求\n{jd_text}"

    raw = provider.chat(SYSTEM_PROMPT, user_prompt, temperature=0.1)
    return _parse_response(jd_text, raw)


def _parse_response(jd_text: str, raw: str) -> dict:
    try:
        result = parse_json(raw)
        _validate(result)
        return result
    except (ValueError, json.JSONDecodeError) as e:
        provider = get_provider()
        raw = provider.chat(SYSTEM_PROMPT, f"上一次输出JSON格式错误，请严格只输出JSON。\n\nJD文本：\n{jd_text}", temperature=0.0)
        try:
            result = parse_json(raw)
            _validate(result)
            return result
        except (ValueError, json.JSONDecodeError) as e2:
            raise ValueError(f"Failed to parse JD after retry: {e2}\nRaw: {raw[:500]}")


def _validate(data: dict):
    required_keys = ["responsibilities", "required_skills", "skill_tags", "experience_requirements", "weight_distribution"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")

    wd = data.get("weight_distribution", {})
    total = sum(wd.values())
    if total != 100:
        raise ValueError(f"weight_distribution sum must be 100, got {total}")
