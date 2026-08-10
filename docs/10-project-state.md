# 10 — 项目当前状态（新对话直接读这个）

## 项目位置

`D:\honor share\ai-recruiting-saas`

## 运行方式

**一键启动**: 双击 `start_all.bat`（三个窗口：后端8000 + 前端3000 + ngrok隧道）

或手动：

```powershell
# 终端1：后端 (port 8000)
cd "D:\honor share\ai-recruiting-saas\backend"
.\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000

# 终端2：前端 (port 3000)
cd "D:\honor share\ai-recruiting-saas\frontend"
npm run dev

# 终端3：公网隧道（发给别人访问）
"D:\honor share\ai-recruiting-saas\tools\ngrok\ngrok.exe" http 3000
```

打开 `http://localhost:3000` → 自动跳转登录页

**演示账号**: `admin@demo.com` / `demo123`（公司：跨境通科技）

**LLM 配置**: `.env` 在 `backend\.env`，已配 DeepSeek API Key。删 key 走 Mock 模式（离线演示）。

**数据库**: SQLite 在 `data\ai_recruit.db`。加新字段不需要删库——`schema_doctor.py` 启动时自动补列。

---

## 功能全貌

### 页面 (11个)

| 页面 | 文件 | 说明 |
|------|------|------|
| 登录 | `frontend/src/app/login/page.tsx` | 邮箱+密码登录 |
| 注册 | `frontend/src/app/register/page.tsx` | 注册（公司名相同则共享数据） |
| Dashboard | `frontend/src/app/page.tsx` | Hero头部+统计卡片(可点击)+招聘漏斗+岗位列表+候选人卡片+快捷入口 |
| 公司设置 | `frontend/src/app/company/page.tsx` | 公司信息+企业知识库(上传文档/AI自动参考)+Webhook设置 |
| 智能创建 | `frontend/src/app/create-job/page.tsx` | 三步：填背景→AI追问→生成完整画像(Hiring Brief+能力模型+A/B/C标准) |
| 岗位详情 | `frontend/src/app/jobs/[id]/page.tsx` | 三tab：岗位画像/候选人评审台/对比分析表+面试简报 |
| 候选人画像 | `frontend/src/app/candidates/[id]/page.tsx` | Pipeline状态条+Match Report+结构画面试题(AI生成)+HR决策+面试反馈+入职 |
| 人才库 | `frontend/src/app/talent-pool/page.tsx` | 关键词/语义搜索切换+技能筛选+状态筛选+相似候选人 |
| 员工台账 | `frontend/src/app/employees/page.tsx` | 表格(含手机号/银行卡列)+统计卡片+手动添加(30+字段)+试用期预警 |
| 员工详情 | `frontend/src/app/employees/[id]/page.tsx` | 能力画像(雷达图)+试用期追踪(时间线+评估)+全字段可编辑+入职链接管理+招聘质量分析 |
| 员工自助入职 | `frontend/src/app/onboarding/[token]/page.tsx` | 填学历/银行卡/社保公积金/紧急联系人+上传文件+预览 |

### 后端 API

| 文件 | 主要路由 |
|------|---------|
| `routers/auth.py` | POST `/auth/register`, `/auth/login`, GET `/auth/me` (JWT) |
| `routers/jobs.py` | POST `/jobs`, `/jobs/probe`, `/jobs/create-full`, GET/PUT/DELETE |
| `routers/upload.py` | POST `/jobs/{id}/resumes` 上传PDF+自动解析+自动匹配 |
| `routers/candidates.py` | GET 列表, PUT 决策, PUT 状态, GET/POST 匹配报告, POST 面试题, GET 简历 |
| `routers/talent_pool.py` | GET 搜索, POST 语义搜索, GET 相似候选人 |
| `routers/employees.py` | POST 入职, POST 手动添加, GET 列表+统计+详情, PUT 更新, PUT 自助填写, GET probation, POST 试用期评估, GET 反馈闭环, GET 能力画像, POST 重新生成入职链接, GET 文件预览 |
| `routers/dashboard.py` | GET 统计, GET 漏斗数据 |
| `routers/company.py` | GET/PUT 公司信息, POST 知识库上传, DELETE 知识库文件 |

### 数据模型 (8张表)

```
User ──→ Company → Job → Application → Candidate → Resume → AIAnalysis
                     ↓
                  Employee (台账+试用期评估+token管理+画像)
```

Pipeline 七阶段 + 分叉: `简历入库→AI解析→匹配分析→HR筛选→面试中→面试完成→入职员工库 / 储备人才库`

### AI 层

| 文件 | 说明 |
|------|------|
| `ai_service/base.py` | LLMProvider 抽象基类，get_provider() 自动选 DeepSeek/Qwen/Mock |
| `ai_service/providers/deepseek.py` | DeepSeekProvider + MockProvider(离线可用) |
| `ai_service/analyzers/jd_analyzer.py` | JD→Job Profile（自动推断role_category） |
| `ai_service/analyzers/resume_parser.py` | 角色感知简历解析（tech/design/generic三套prompt） |
| `ai_service/analyzers/matcher.py` | 匹配分析报告 |
| `ai_service/interview_questions.py` | 结构化面试题生成（开场/深挖/行为/情景/收尾） |
| `ai_service/embeddings.py` | 向量嵌入（DeepSeek API / 关键词重叠模拟） |
| `ai_service/json_repair.py` | LLM输出JSON自动修复 |
| `ai_service/knowledge_context.py` | 企业知识库注入AI prompt |
| `ai_service/integrations/github.py` | GitHub公开API（repos/stars/languages） |
| `services/probation_service.py` | 试用期30/60/90天AI评估 |
| `services/feedback_loop.py` | 招聘反馈闭环（AI预测vs实际表现） |
| `services/employee_profile.py` | AI员工能力画像（六维雷达图） |
| `services/notify_service.py` | Webhook通知（飞书卡片/企微Markdown/自定义JSON） |
| `services/schema_doctor.py` | 启动时自动补列，无需删库重建 |
| `services/multi_tenant.py` | 多租户数据隔离工具 |

---

## 关键设计决策

1. **不做评分数字** —展示优势/不足/面试建议，不显示"匹配度86%"
2. **面试不问他没的经验** — 缺某领域经验问可迁移能力
3. **AI追问引擎** — HR输入模糊需求→AI追问→生成精准画像
4. **Hiring Brief** — 招聘不只是JD，还有"为什么招"+"入职后干什么"+"成功标准"
5. **面试反馈闭环** — AI预测 vs 实际面试评分对比
6. **HR和员工分开填入职信息** — HR填工作信息，员工通过链接自助填个人敏感信息
7. **录用后分叉** — 合适→入职员工库，待定/不合适→储备人才库
8. **角色感知解析** — 技术岗/设计岗/通用岗三套prompt
9. **语义搜索** — 自然语言搜索候选人
10. **Webhook通知** — 飞书实时推送
11. **多用户+公司隔离** — 同公司HR数据共享，跨公司隔离，JWT认证

---

## 已知问题

1. **ngrok免费版偶尔断** — 断了双击 `start_all.bat` 重新拉隧道
2. **ngrok浏览器拦截页** — 首次打开要点"Visit Site"，axios已加跳过header但偶尔失效
3. **LLM JSON偶尔解析失败** — 已增强（json_repair.py），但极端情况仍有风险
4. **没有CI/CD** — 部署到云服务器需手动操作

---

## 后续可选方向

- 正式部署到云服务器（阿里云/Railway）
- Docker Compose 一键部署
- AI面试问题嵌入到更多场景
- 邮件通知
- 招聘需求诊断（AI先判断"真需要招吗"）

## 技术栈

```
前端: Next.js 16 + React + Tailwind CSS + TypeScript
后端: FastAPI + SQLAlchemy + Pydantic + PyMuPDF
认证: JWT (HS256, 7天) + pbkdf2密码哈希
AI: DeepSeek API（可切换Qwen），MockProvider离线可用
数据库: SQLite(开发) / PostgreSQL + pgvector(生产) 双模式
部署: ngrok隧道(临时) / Docker(计划中)
C盘占用: 零（全部在 D:\honor share\）
```

## 演示账号

```
邮箱: admin@demo.com
密码: demo123
公司: 跨境通科技
```

## ngrok 公网地址

当前: `https://demystify-underpaid-recopy.ngrok-free.dev`

注意: ngrok 免费版URL固定不变，关了重开会保留。首次访问有拦截页，点"Visit Site"即可。如果打不开，双击 `start_all.bat` 重启。
