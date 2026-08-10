# 00 — 项目概述

## 产品名称

**AI Recruiting Assistant** — 面向企业HR的AI候选人智能分析系统

## 一句话介绍

通过 LLM 实现简历结构化解析、候选人画像生成、岗位智能匹配和人才资产沉淀，辅助 HR 完成招聘筛选与决策。

## 当前版本

**V1.0 MVP** — 单实例 AI 候选人智能分析系统

## V1 核心能力

| 能力 | 说明 |
|------|------|
| JD 智能解析 | 从岗位描述中提取结构化岗位画像 |
| 简历结构化 | PDF 文字层提取 + LLM 信息抽取 → Candidate Profile |
| 候选人画像 | 技能、经验、项目、优势、风险的结构化卡片 |
| AI 匹配分析 | 基于岗位画像与候选人画像的 Match Report（非评分） |
| 人才库 | 结构化候选人数据沉淀，支持搜索与复用 |

## V1 不做什么

- 不做用户注册/登录系统（单实例）
- 不做多租户（架构预留 tenant_id）
- 不做自动沟通/自动投递
- 不做招聘渠道对接
- 不做面试 scheduling

## 技术栈概览

```
Frontend:   Next.js + React + Tailwind CSS
Backend:    Python FastAPI
Database:   SQLite (开发) → PostgreSQL (生产)
AI Layer:   独立 AI Service，封装 LLM 调用
File:       本地文件存储
Deploy:     无 Docker，直接运行
```

## 项目结构

```
ai-recruiting-saas/
├── README.md
├── docs/                    # 产品文档
│   ├── 00-overview.md
│   ├── 01-product-positioning.md
│   ├── 02-user-persona.md
│   ├── 03-user-flow.md
│   ├── 04-page-prototypes.md
│   ├── 05-data-model.md
│   ├── 06-ai-workflow.md
│   ├── 07-tech-architecture.md
│   ├── 08-roadmap.md
│   └── 09-product-decisions.md
├── demo-data/               # 演示数据集
│   ├── jobs/
│   ├── resumes/
│   └── expected-results.md
├── backend/
├── frontend/
├── ai-service/
└── storage/
```
