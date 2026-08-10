# 06 — AI Workflow 设计

## 架构概览

```
                     AI Service
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   JD Analyzer     Resume Parser    Candidate Matcher
        │                │                │
        └────────────────┼────────────────┘
                         │
                      LLM API
```

AI Service 是独立的 Python 模块，不耦合 FastAPI。每个 Analyzer/Parser/Matcher 是独立的函数，输入明确、输出 Schema 化。

---

## Workflow 1：JD Analyzer（岗位分析）

### 输入

```
岗位名称: "AI产品经理"
JD 原文:   "[HR 粘贴的 JD 文本]"
```

### 处理步骤

```
Step 1: JD 文本预处理
  - 去除多余空行
  - 识别文本结构（职责段、要求段、加分项段）

Step 2: LLM 结构化抽取
  - Prompt 输入: JD原文 + 输出Schema
  - LLM 输出: Job Profile JSON

Step 3: Schema 校验
  - 必填字段完整性检查
  - 字段类型校验
  - 不通过 → 重试一次 / 标记需人工补充
```

### 输出 Schema

```json
{
  "responsibilities": ["string"],
  "required_skills": ["string"],
  "skill_tags": ["string"],
  "experience_requirements": {
    "years_min": "number",
    "industry": ["string"],
    "preferred": ["string"]
  },
  "weight_distribution": {
    "ai_understanding": "number",
    "product_ability": "number",
    "project_experience": "number",
    "education": "number"
  }
}
```

### Prompt 设计原则

1. **Role Setting**：设定为"资深招聘顾问"，非通用 AI
2. **Output Constraint**：只返回 JSON，不返回解释性文字
3. **Few-shot Example**：在 System Prompt 中提供一个完整的输入/输出示例
4. **权重推理**：要求根据 JD 中关键词密度和职位级别推断权重分布，不能随机分配

### 示例 System Prompt 结构

```
你是一位资深招聘顾问，擅长从岗位描述中提取关键信息。

任务：分析以下JD，输出结构化的岗位画像JSON。

要求：
1. 只输出JSON，不要任何额外文字
2. skill_tags 控制在5-8个标签
3. weight_distribution 四项加起来必须等于100
4. years_min 如果没有明确写，默认填0

输出格式：
{JSON Schema}
```

---

## Workflow 2：Resume Parser（简历解析）

### 输入

```
PDF 文件路径 (英文/中文简历)
```

### 处理步骤

```
Step 1: PDF 文本提取
  工具: PyMuPDF (fitz)
  提取: 全部文字层内容

Step 2: 文本清洗
  - 去除页眉页脚
  - 合并被PDF断开的段落
  - 识别章节边界（工作经历、教育背景、技能等）

Step 3: LLM 信息抽取
  - Prompt 输入: 清洗后的简历文本 + Candidate Profile Schema
  - LLM 输出: Candidate Profile JSON

Step 4: Schema 校验
  - 检查必填字段（name, skills, work_experience）
  - 检查日期格式一致性
  - 不通过 → 重试一次 / 标记需人工补充

Step 5: 技能标准化（可选，V2）
  - 技能别名统一（"Python开发" → "Python"）
  - 技能分类（编程语言、框架、领域知识）
```

### 输出 Schema

```json
{
  "name": "string",
  "email": "string|null",
  "phone": "string|null",
  "years_of_experience": "number",
  "highest_degree": "string",
  "current_position": "string",
  "current_company": "string",
  "skills": ["string"],
  "work_experience": [
    {
      "company": "string",
      "position": "string",
      "start_date": "string",
      "end_date": "string",
      "projects": [
        {
          "name": "string",
          "description": "string",
          "highlights": ["string"]
        }
      ]
    }
  ],
  "education": [
    {
      "school": "string",
      "degree": "string",
      "major": "string",
      "start_year": "number",
      "end_year": "number"
    }
  ]
}
```

### 解析失败的降级策略

| 失败原因 | 策略 |
|---------|------|
| PDF 无法提取文字（扫描件） | 标记为"不支持"，提示用户重新上传文字版 PDF |
| LLM 返回格式错误 | 重试 1 次；仍失败则标记为"解析失败"，保留原始文本供人工查看 |
| 必填字段缺失（如 name 为空） | 标记为"部分解析"，缺失字段留空 |
| PDF 超大（>20MB） | 拒绝上传，提示压缩后重试 |

---

## Workflow 3：Candidate Matcher（候选人匹配）

### 输入

```
Job Profile JSON       (来自 JD Analyzer 的输出或 HR 编辑后的版本)
Candidate Profile JSON  (来自 Resume Parser 的输出)
```

### 处理步骤

```
Step 1: 数据对齐
  - 将 Job Profile 的维度权重映射到 Candidate Profile 的分析维度

Step 2: LLM 匹配分析
  - Prompt 输入: Job Profile + Candidate Profile
  - LLM 输出: Match Report JSON

Step 3: 人工确认
  - HR 查看报告后可修改结论
  - 修改记录不覆盖 AI 原始分析
```

### 输出 Schema

```json
{
  "overall_conclusion": "string",
  "star_rating": "number",
  "summary": "string",
  "strengths": [
    {
      "point": "string",
      "evidence": "string"
    }
  ],
  "gaps": [
    {
      "point": "string",
      "evidence": "string"
    }
  ],
  "interview_suggestions": ["string"],
  "dimension_scores": {
    "string": "string"
  }
}
```

### Prompt 设计原则

1. **对比式分析**：明确要求"逐一对比岗位要求与候选人经历"
2. **证据驱动**：每个优势/不足必须引用简历或 JD 中的具体内容
3. **面试建议可操作**：输出具体问题，而非"考察技术能力"这种泛泛建议
4. **无分数的星级**：星级是感性综合判断（1-5），不是数学计算结果

### 关键约束

- **不做淘汰判断**：不输出"不合适"、"淘汰"等否定性结论。HR 做淘汰决策，AI 只提供分析
- **不做歧视性分析**：不输出关于年龄、性别、地域、婚育等人口学信息的分析。即使简历中包含这些信息，AI 也忽略

---

## LLM 调用通用规范

### 调用配置

```
Model:      DeepSeek-V3 (默认) / Qwen-Max (备选)
Temperature: 0.1 (抽取任务需要低随机性)
Max Tokens: 4096
```

### 重试策略

```
1st call → 失败/格式错误
         → 2nd call (降低温度至 0.0)
         → 仍失败 → 标记需人工处理
```

### 成本估算

```
JD Analyzer:   ~2K tokens in, ~500 tokens out → ~0.005 元/次
Resume Parser: ~3K tokens in, ~800 tokens out → ~0.008 元/次
Matcher:       ~4K tokens in, ~1K tokens out  → ~0.012 元/次

一份简历完整流程: ~0.025 元
100份简历: ~2.5 元
```

---

## AI Service 代码结构（规划）

```python
# ai_service/
# ├── __init__.py
# ├── base.py            # LLMProvider 抽象基类
# ├── providers/
# │   ├── deepseek.py    # DeepSeek provider
# │   └── qwen.py        # Qwen provider
# ├── analyzers/
# │   ├── jd_analyzer.py
# │   ├── resume_parser.py
# │   └── matcher.py
# └── schemas/
#     ├── job_profile.py
#     ├── candidate_profile.py
#     └── match_report.py
```
