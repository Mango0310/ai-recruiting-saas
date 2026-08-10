# 08 — 开发路线图

## Phase 0：Research & Preparation（当前阶段）

**目标**：确认方向，准备数据

| 任务 | 说明 | 状态 |
|------|------|------|
| 竞品调研 | 了解现有 AI 招聘工具的产品形态 | 待做 |
| 用户访谈假设 | 基于 HR 和 Hiring Manager 的痛点假设，设计验证问题 | 待做 |
| 演示数据准备 | 收集 5-8 份脱敏简历 + 2-3 个岗位 JD | 待做 |
| 技术原型验证 | PDF 提取 + LLM 解析效果快速验证 | 待做 |

**交付物**：
- 竞品分析文档（可并入 PRD）
- `demo-data/` 数据集
- 技术原型（一个 Jupyter Notebook 或 Python 脚本）

---

## Phase 1：MVP — AI Candidate Intelligence System

**目标**：可演示的核心闭环

**时间预估**：1-2 个月（个人开发）

### 里程碑 M1：基础骨架（Week 1-2）

```
✅ FastAPI 项目初始化 + SQLite 建表
✅ Next.js 项目初始化 + Tailwind 配置
✅ 前后端联通（Dashboard 页面展示假数据）
```

### 里程碑 M2：岗位管理（Week 2-3）

```
✅ 创建岗位页面（粘贴 JD）
✅ JD Analyzer（AI 生成 Job Profile）
✅ 岗位画像展示 + 编辑
✅ 岗位列表
```

### 里程碑 M3：简历处理（Week 3-5）★ 核心

```
✅ 简历上传页面（拖拽 + 批量）
✅ PDF 文本提取（PyMuPDF）
✅ Resume Parser（LLM 结构化）
✅ Candidate Profile 页面
✅ 候选人列表
```

### 里程碑 M4：AI 匹配（Week 5-6）

```
✅ Candidate Matcher（LLM 匹配分析）
✅ AI Match Report 页面
✅ 匹配报告可打印/导出
```

### 里程碑 M5：人才库（Week 6-7）

```
✅ 候选人入库
✅ 人才库搜索页（关键词 + 标签筛选）
✅ 人才详情页（只读模式）
```

### 里程碑 M6：打磨（Week 7-8）

```
✅ 错误处理完善
✅ 解析失败降级流程
✅ UI 细节调整
✅ 演示数据加载脚本
✅ README 撰写
```

### Phase 1 交付物

- 可本地运行的完整应用
- 5 个核心页面（Dashboard / Job Detail / Upload / Candidate Profile / Match Report）
- 5-8 份演示简历 + 2-3 个岗位的完整演示流程
- GitHub 仓库 + README
- 完整的产品文档（docs/）

---

## Phase 2：AI Enhancement & Recruiting Flow

**目标**：从"分析系统"扩展到"招聘流程管理"

| 功能 | 说明 |
|------|------|
| 用户系统 | 简单的登录/注册，支持多人使用 |
| 招聘流程管理 | Candidate Pipeline（new → screen → interview → offer） |
| 面试记录 | 面试评价、评分，关联候选人 |
| 面试助手 | 基于候选人画像 + 岗位要求，AI 生成面试问题 |
| 人才语义搜索 | pgvector 向量化候选人技能和项目，支持自然语言搜索 |
| 批量操作 | 批量标记状态、批量导出 |
| 数据库升级 | SQLite → PostgreSQL |
| 异步任务 | FastAPI BackgroundTasks 处理批量解析 |

---

## Phase 3：SaaS 化

**目标**：接近可商业化的多租户产品

| 功能 | 说明 |
|------|------|
| 多租户 | tenant_id 隔离，企业注册 → 独立空间 |
| 权限系统 | Admin / HR / Hiring Manager 角色权限 |
| 企业集成 | 飞书/企微通知，Slack 集成 |
| 自动化 Workflow | n8n 接入，HR 自定义流程 |
| 招聘渠道连接 | 邮箱解析（收到简历邮件 → 自动入库） |
| 数据分析 | 招聘漏斗、渠道效率、人才库构成分析 |
| 对象存储 | 迁移文件存储到 S3/OSS |

---

## 技术债务清单（跨 Phase）

| 项 | Phase 1 处理方式 | 后续改进 |
|-----|-----|-----|
| 数据库 | SQLite 单文件 | Phase 2 → PostgreSQL |
| AI 调用 | 同步阻塞调用 | Phase 2 → 异步任务队列 |
| 文件存储 | 本地目录 | Phase 3 → 对象存储 |
| 错误处理 | try-catch + 日志 | Phase 2 → 统一错误处理中间件 |
| 测试 | 手动测试 | Phase 2 → pytest + Playwright |
| 监控 | print/logging | Phase 3 → Sentry / 日志平台 |
| 部署 | 本地运行 | Phase 3 → Docker Compose + 云服务器 |
