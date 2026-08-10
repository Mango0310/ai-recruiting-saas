# 07 — 技术架构

## V1 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                        Next.js                              │
│                   (Frontend - Port 3000)                     │
│              React + Tailwind CSS + TypeScript              │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP REST API
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       FastAPI                                │
│                   (Backend - Port 8000)                      │
│                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ Job API  │ │Candidate │ │ Upload   │ │ Talent Pool   │  │
│  │          │ │ API      │ │ API      │ │ API           │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                 AI Service (sync call)                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────┬───────────────────────────┬───────────────────┘
              │                           │
              ▼                           ▼
┌─────────────────────┐     ┌─────────────────────────────┐
│      SQLite         │     │      File Storage            │
│  (ai_recruit.db)    │     │   ./storage/resumes/         │
│                     │     │   ./storage/exports/         │
│  在 D 盘项目目录内   │     │   在 D 盘项目目录内           │
└─────────────────────┘     └─────────────────────────────┘
              │
              │ (Phase 2 迁移)
              ▼
┌─────────────────────┐
│    PostgreSQL       │
│  (Windows 原生安装)  │
│  data 目录在 D 盘    │
└─────────────────────┘
```

## 技术选型详细说明

### Frontend

| 技术 | 版本 | 理由 |
|------|------|------|
| Next.js | 14+ | App Router，SSR 可选，部署灵活 |
| React | 18+ | 生态成熟 |
| Tailwind CSS | 3+ | 快速出页面，不需要单独写 CSS |
| TypeScript | 5+ | 类型安全 |

### Backend

| 技术 | 理由 |
|------|------|
| FastAPI | Python 异步框架，性能好，自动生成 OpenAPI 文档 |
| SQLAlchemy | ORM，SQLite → PostgreSQL 切换只需改连接串 |
| Pydantic | 数据校验，与 FastAPI 深度集成 |
| PyMuPDF | PDF 文字层提取，轻量且中文支持好 |
| Uvicorn | ASGI server |

### Database

| 阶段 | 方案 | 位置 |
|------|------|------|
| V1 | SQLite | `D:\honor share\ai-recruiting-saas\data\ai_recruit.db` |
| V2+ | PostgreSQL | Windows 原生安装，data 目录配到 D 盘 |

### AI Layer

| 组件 | 说明 |
|------|------|
| LLM Provider 抽象 | 接口化，支持 DeepSeek / Qwen / OpenAI 切换 |
| 默认模型 | DeepSeek-V3（中文好、便宜） |
| 调用方式 | FastAPI 同步调用（V1 数据量小，无需异步队列） |

### File Storage

| 类型 | 路径 |
|------|------|
| 原始简历 | `./storage/resumes/{job_id}/{timestamp}_{filename}` |
| 导出文件 | `./storage/exports/` |

---

## V1 不引入的技术

| 技术 | 不引入原因 |
|------|-----------|
| Docker | 已确认，C 盘空间不足，Docker 数据已有 30GB |
| Redis | V1 无异步任务队列需求 |
| Celery | V1 简历解析量小，FastAPI BackgroundTasks 足够 |
| n8n | V1 无自动化编排需求，核心业务逻辑在 Backend |
| pgvector | V2 人才语义搜索才需要 |
| S3/OSS | V1 本地文件存储，单机部署 |
| 用户认证 | V1 单实例，无需登录系统 |

---

## API 路由设计

```python
# jobs
POST   /api/jobs                    # 创建岗位（含 JD 分析）
GET    /api/jobs                    # 岗位列表
GET    /api/jobs/{id}               # 岗位详情
PUT    /api/jobs/{id}               # 更新岗位画像
DELETE /api/jobs/{id}               # 删除岗位

# resumes & candidates
POST   /api/jobs/{id}/resumes       # 上传简历（触发解析+匹配）
GET    /api/jobs/{id}/candidates    # 候选人列表
GET    /api/candidates/{id}         # 候选人画像

# match analysis
GET    /api/applications/{id}/report  # 匹配报告
POST   /api/applications/{id}/reanalyze  # 重新分析

# talent pool
GET    /api/talent-pool             # 人才库搜索
GET    /api/talent-pool/{id}        # 人才详情

# dashboard
GET    /api/dashboard/stats         # 首页统计
```

## 项目目录结构

```
ai-recruiting-saas/
├── README.md
├── docs/                      # 产品文档
├── demo-data/                 # 演示数据
│   ├── jobs/
│   ├── resumes/
│   └── expected-results.md
├── backend/
│   ├── requirements.txt
│   ├── main.py                # FastAPI 入口
│   ├── config.py              # 配置管理
│   ├── database.py            # SQLAlchemy setup
│   ├── models/                # DB models
│   │   ├── job.py
│   │   ├── candidate.py
│   │   ├── resume.py
│   │   ├── application.py
│   │   └── ai_analysis.py
│   ├── schemas/               # Pydantic schemas
│   │   ├── job.py
│   │   ├── candidate.py
│   │   └── match_report.py
│   ├── routers/               # API routes
│   │   ├── jobs.py
│   │   ├── candidates.py
│   │   ├── upload.py
│   │   └── talent_pool.py
│   └── services/              # Business logic
│       ├── jd_service.py
│       ├── resume_service.py
│       └── match_service.py
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── src/
│   │   ├── app/               # Next.js App Router
│   │   ├── components/        # React components
│   │   └── lib/               # API client, utils
├── ai-service/
│   ├── base.py
│   ├── providers/
│   │   ├── deepseek.py
│   │   └── qwen.py
│   ├── analyzers/
│   │   ├── jd_analyzer.py
│   │   ├── resume_parser.py
│   │   └── matcher.py
│   └── schemas/
│       ├── job_profile.py
│       ├── candidate_profile.py
│       └── match_report.py
├── data/                      # SQLite 数据库文件
├── storage/                   # 简历文件存储
│   ├── resumes/
│   └── exports/
└── scripts/                   # 工具脚本
    ├── init_db.py
    └── load_demo_data.py
```

## 为什么不用 n8n 做核心？

n8n 是优秀的自动化编排工具，但在这个系统中：

1. **核心业务逻辑不适合 workflow 表达**：AI 解析、匹配分析的逻辑是线性的，直接用 Python 函数表达更清晰
2. **增加运维复杂度**：多一个中间层意味着多一个故障点
3. **性能开销**：F形式调用不如直连快

n8n 的未来定位（Phase 3）：

- HR 自定义通知流程（"候选人进入面试 → 飞书通知"）
- 批量定时任务（"每周汇总新建候选人"）
- 系统集成（对接外部 HR 系统）

这些场景才是 workflow 引擎的价值所在。

---

## Phase 2 升级路径

```
V1 当前                    V2 目标
─────────────────────────────────────────────
SQLite         →           PostgreSQL (Windows 安装)
同步 AI 调用   →           FastAPI BackgroundTasks
本地文件存储   →           对象存储 (S3/OSS)
单实例         →           多租户 (tenant_id 隔离)
关键词搜索     →           pgvector 语义搜索
```
