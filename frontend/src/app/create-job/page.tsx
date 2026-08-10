"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getCompanyInfo, hasCompanyInfo } from "@/lib/company";

const API_BASE = "/api";

type Step = "info" | "ai_questions" | "result";

export default function CreateJob() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("info");
  const [loading, setLoading] = useState(false);

  // Step 1: Basic info
  const [title, setTitle] = useState("");
  const [department, setDepartment] = useState("");
  const [reportsTo, setReportsTo] = useState("");
  const [salary, setSalary] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [companyIndustry, setCompanyIndustry] = useState("");
  const [companySize, setCompanySize] = useState("");
  const [businessStage, setBusinessStage] = useState("");
  const [targetAudience, setTargetAudience] = useState("");
  const [productStage, setProductStage] = useState("");
  const [teamRole, setTeamRole] = useState("");
  const [techRequired, setTechRequired] = useState("");
  const [requirementSource, setRequirementSource] = useState("");
  const [rawRequirements, setRawRequirements] = useState("");
  const [hiringReason, setHiringReason] = useState("");
  const [teamContext, setTeamContext] = useState("");
  const [threeMonthGoal, setThreeMonthGoal] = useState("");
  const [jdNote, setJdNote] = useState("");

  // Pre-fill saved company info
  useEffect(() => {
    if (hasCompanyInfo()) {
      const c = getCompanyInfo();
      setCompanyName(c.name);
      setCompanyIndustry(c.industry);
      setCompanySize(c.size);
    }
  }, []);

  // Step 2: AI follow-up questions
  const [aiQuestions, setAiQuestions] = useState<string[]>([]);
  const [aiAnswers, setAiAnswers] = useState<string[]>([]);

  // Step 3: Result
  const [jobProfile, setJobProfile] = useState<any>(null);

  const handleNextToAI = async () => {
    if (!title) return;
    setLoading(true);
    try {
      const context = {
        title,
        department,
        reports_to: reportsTo,
        salary,
        company_name: companyName,
        company_industry: companyIndustry,
        company_size: companySize,
        business_stage: businessStage,
        target_audience: targetAudience,
        product_stage: productStage,
        team_role: teamRole,
        tech_required: techRequired,
        requirement_source: requirementSource,
        raw_requirements: rawRequirements,
        hiring_reason: hiringReason,
        team_context: teamContext,
        three_month_goal: threeMonthGoal,
        notes: jdNote,
      };

      const resp = await fetch(`${API_BASE}/jobs/probe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(context),
      });
      const data = await resp.json();
      setAiQuestions(data.questions || []);
      setAiAnswers(new Array(data.questions?.length || 0).fill(""));
      setStep("ai_questions");
    } catch (e) {
      alert("AI 追问失败: " + (e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateProfile = async () => {
    setLoading(true);
    try {
      const payload = {
        title,
        department,
        reports_to: reportsTo,
        salary,
        company_name: companyName,
        company_industry: companyIndustry,
        company_size: companySize,
        business_stage: businessStage,
        target_audience: targetAudience,
        product_stage: productStage,
        team_role: teamRole,
        tech_required: techRequired,
        requirement_source: requirementSource,
        raw_requirements: rawRequirements,
        hiring_reason: hiringReason,
        team_context: teamContext,
        three_month_goal: threeMonthGoal,
        notes: jdNote,
        ai_questions: aiQuestions.map((q, i) => ({ question: q, answer: aiAnswers[i] || "" })),
      };

      const resp = await fetch(`${API_BASE}/jobs/create-full`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await resp.json();
      setJobProfile(data);
      setStep("result");
    } catch (e) {
      alert("生成失败: " + (e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoToJob = () => {
    if (jobProfile?.id) {
      router.push(`/jobs/${jobProfile.id}`);
    }
  };

  if (step === "info") {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <h1 className="text-xl font-bold">创建招聘需求</h1>
        <p className="text-sm text-gray-500">AI 帮你把业务方的原始需求整理成结构化岗位画像，追问关键细节，生成评估框架。</p>

        <div className="bg-white rounded-xl border p-6 space-y-4">
          <div className="bg-blue-50 rounded-lg p-3 text-xs text-blue-700">
            <strong>使用方式：</strong>把业务方/老板说的原始需求填进来，AI 负责整理、追问遗漏、生成评估标准。AI 不会帮你编需求，只会帮你结构化需求。
          </div>

          {/* Company info */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-medium text-gray-500">公司信息</p>
              {hasCompanyInfo() && (
                <Link href="/company" className="text-xs text-blue-500 hover:underline">修改</Link>
              )}
            </div>
            {!hasCompanyInfo() && (
              <div className="mb-3 p-2 bg-yellow-50 rounded text-xs text-yellow-700">
                建议先到 <Link href="/company" className="underline">公司设置</Link> 填写公司信息，创建岗位时自动填充，不用每次重复填。
              </div>
            )}
            <div className="grid grid-cols-3 gap-3">
              <input className="border rounded-lg px-3 py-2 text-sm" placeholder="公司名称"
                value={companyName} onChange={e => setCompanyName(e.target.value)} />
              <input className="border rounded-lg px-3 py-2 text-sm" placeholder="行业（如：跨境电商、医疗SaaS）"
                value={companyIndustry} onChange={e => setCompanyIndustry(e.target.value)} />
              <select className="border rounded-lg px-3 py-2 text-sm" value={companySize} onChange={e => setCompanySize(e.target.value)}>
                <option value="">公司规模</option>
                <option value="1-20">1-20人</option>
                <option value="20-99">20-99人</option>
                <option value="100-299">100-299人</option>
                <option value="300-1000">300-1000人</option>
                <option value="1000+">1000人以上</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">岗位名称 *</label>
              <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="如：AI产品经理"
                value={title} onChange={e => setTitle(e.target.value)} />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">所属部门</label>
              <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="如：产品部"
                value={department} onChange={e => setDepartment(e.target.value)} />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">需求来源</label>
            <select className="w-full border rounded-lg px-3 py-2 text-sm" value={requirementSource} onChange={e => setRequirementSource(e.target.value)}>
              <option value="">请选择</option>
              <option value="ceo">CEO / 创始人</option>
              <option value="cpo">CPO / 产品负责人</option>
              <option value="cto">CTO / 技术负责人</option>
              <option value="business">业务部门负责人</option>
              <option value="hrbp">HRBP 转述</option>
              <option value="other">其他</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">业务方原始需求（老板/业务负责人是怎么说的）</label>
            <textarea className="w-full border rounded-lg px-3 py-2 text-sm h-24"
              placeholder="把业务方原话填进来，比如：'我们现在的AI产品增长太慢了，需要一个有增长经验的PM来把产品从1做到10'"
              value={rawRequirements} onChange={e => setRawRequirements(e.target.value)} />
          </div>

          {/* Hiring Brief fields */}
          <div className="border-t pt-4">
            <p className="text-xs font-medium text-gray-500 mb-3">招聘背景（帮助 AI 生成 Hiring Brief）</p>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">为什么招聘？（替换离职/新增岗位/业务扩张）</label>
                <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="如：原PM转岗，需要新人接手增长方向"
                  value={hiringReason} onChange={e => setHiringReason(e.target.value)} />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">当前团队情况</label>
                <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="如：产品团队5人，2个PM各负责不同方向，此人需独立负责增长"
                  value={teamContext} onChange={e => setTeamContext(e.target.value)} />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">入职3个月希望达成什么？</label>
                <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="如：完成增长方向的需求调研，输出产品路线图，推动至少一个增长实验上线"
                  value={threeMonthGoal} onChange={e => setThreeMonthGoal(e.target.value)} />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">汇报对象</label>
              <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="如：产品总监"
                value={reportsTo} onChange={e => setReportsTo(e.target.value)} />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">薪资范围</label>
              <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="如：25k-40k"
                value={salary} onChange={e => setSalary(e.target.value)} />
            </div>
          </div>

          <div className="border-t pt-4">
            <p className="text-xs font-medium text-gray-500 mb-3">业务背景（帮助 AI 精准画像）</p>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-400 mb-1">当前业务阶段</label>
                <select className="w-full border rounded-lg px-3 py-2 text-sm" value={businessStage} onChange={e => setBusinessStage(e.target.value)}>
                  <option value="">请选择</option>
                  <option value="exploration">探索期（找PMF）</option>
                  <option value="growth">增长期（规模化）</option>
                  <option value="mature">成熟期（优化效率）</option>
                  <option value="transform">转型期（业务变革）</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">服务对象</label>
                <select className="w-full border rounded-lg px-3 py-2 text-sm" value={targetAudience} onChange={e => setTargetAudience(e.target.value)}>
                  <option value="">请选择</option>
                  <option value="internal">内部用户</option>
                  <option value="external">外部客户</option>
                  <option value="both">两者都有</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">产品阶段</label>
                <select className="w-full border rounded-lg px-3 py-2 text-sm" value={productStage} onChange={e => setProductStage(e.target.value)}>
                  <option value="">请选择</option>
                  <option value="0-1">0 → 1 从零搭建</option>
                  <option value="iteration">1 → 10 持续迭代</option>
                  <option value="mature">10 → 100 成熟优化</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">团队角色</label>
                <select className="w-full border rounded-lg px-3 py-2 text-sm" value={teamRole} onChange={e => setTeamRole(e.target.value)}>
                  <option value="">请选择</option>
                  <option value="independent">独立负责</option>
                  <option value="assist">协助执行</option>
                  <option value="lead">带团队</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">是否需要技术背景</label>
                <select className="w-full border rounded-lg px-3 py-2 text-sm" value={techRequired} onChange={e => setTechRequired(e.target.value)}>
                  <option value="">请选择</option>
                  <option value="must">必须有</option>
                  <option value="preferred">优先考虑</option>
                  <option value="no">不需要</option>
                </select>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">补充说明</label>
            <textarea className="w-full border rounded-lg px-3 py-2 text-sm h-20" placeholder="其他你想让AI了解的信息..."
              value={jdNote} onChange={e => setJdNote(e.target.value)} />
          </div>

          <div className="flex gap-2 justify-end pt-2">
            <button onClick={() => router.back()} className="px-4 py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-lg">取消</button>
            <button onClick={handleNextToAI} disabled={loading || !title}
              className="px-6 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
              {loading ? "AI 分析中..." : "下一步：AI 追问"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Step 2: AI follow-up questions
  if (step === "ai_questions") {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <h1 className="text-xl font-bold">AI 追问</h1>
        <p className="text-sm text-gray-500">AI 根据你填写的背景，追问一些关键细节来生成更精准的岗位画像。</p>

        <div className="bg-white rounded-xl border p-6 space-y-4">
          {aiQuestions.map((q, i) => (
            <div key={i}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{i + 1}. {q}</label>
              <textarea className="w-full border rounded-lg px-3 py-2 text-sm h-16"
                placeholder="输入你的回答..."
                value={aiAnswers[i] || ""}
                onChange={e => {
                  const next = [...aiAnswers];
                  next[i] = e.target.value;
                  setAiAnswers(next);
                }} />
            </div>
          ))}

          <div className="flex gap-2 justify-between pt-2">
            <button onClick={() => setStep("info")} className="px-4 py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-lg">← 返回修改</button>
            <button onClick={handleGenerateProfile} disabled={loading}
              className="px-6 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
              {loading ? "AI 生成中..." : "生成岗位画像"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Step 3: Result
  if (step === "result" && jobProfile) {
    const jp = jobProfile.job_profile || {};
    const competencies = jp.competency_model || {};
    const evalFramework = jp.evaluation_framework || {};

    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">{jobProfile.title} — 岗位画像</h1>
            <p className="text-sm text-gray-500">AI 已根据你的业务场景生成完整招聘评估框架</p>
          </div>
          <button onClick={handleGoToJob} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">进入岗位</button>
        </div>

        {/* Hiring Brief */}
        {jp.hiring_brief && (
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-200 p-6 space-y-3">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">📋</span>
              <h2 className="text-lg font-bold text-gray-800">Hiring Brief — 招聘任务说明书</h2>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-gray-400 mb-1">招聘目标</p>
                <p className="text-sm font-medium text-gray-800">{jp.hiring_brief.goal}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 mb-1">团队定位</p>
                <p className="text-sm text-gray-700">{jp.hiring_brief.team_fit}</p>
              </div>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-1">成功标准</p>
              {(jp.hiring_brief.success_criteria || []).map((c: string, i: number) => (
                <p key={i} className="text-sm text-gray-700 ml-2">· {c}</p>
              ))}
            </div>
            {(jp.hiring_brief.key_challenges || []).length > 0 && (
              <div>
                <p className="text-xs text-gray-400 mb-1">关键挑战</p>
                {(jp.hiring_brief.key_challenges || []).map((c: string, i: number) => (
                  <p key={i} className="text-sm text-orange-700 ml-2">· {c}</p>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Job Goal */}
        <div className="bg-white rounded-xl border p-6">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">岗位目标</h3>
          <p className="text-sm text-gray-800">{jp.job_goal || "—"}</p>
        </div>

        {/* Core Responsibilities */}
        <div className="bg-white rounded-xl border p-6">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">核心职责</h3>
          <div className="space-y-3">
            {(jp.responsibilities || []).map((r: string, i: number) => (
              <div key={i} className="flex gap-3">
                <span className="text-blue-500 font-bold">{i + 1}.</span>
                <p className="text-sm text-gray-700">{r}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Competency Model */}
        <div className="bg-white rounded-xl border p-6">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">能力模型</h3>
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(competencies).map(([cat, skills]: [string, any]) => (
              <div key={cat} className="bg-gray-50 rounded-lg p-4">
                <p className="text-xs font-semibold text-gray-500 uppercase mb-2">{cat}</p>
                {(skills || []).map((s: string, i: number) => (
                  <p key={i} className="text-sm text-gray-700 ml-2">· {s}</p>
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* Evaluation Framework */}
        <div className="bg-white rounded-xl border p-6">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">面试评价标准</h3>
          <div className="space-y-3">
            {Object.entries(evalFramework).map(([level, desc]: [string, any]) => (
              <div key={level} className={`p-4 rounded-lg ${level === "A级" ? "bg-green-50 border border-green-200" : level === "B级" ? "bg-blue-50 border border-blue-200" : "bg-gray-50 border border-gray-200"}`}>
                <span className="text-xs font-bold uppercase mr-2">{level}</span>
                <span className="text-sm text-gray-700">{desc}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Weight Framework */}
        <div className="bg-white rounded-xl border p-6">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">评估权重</h3>
          <div className="space-y-2">
            {Object.entries(jp.weight_distribution || {}).map(([k, v]: [string, any]) => (
              <div key={k}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">{k}</span>
                  <span className="font-medium">{v}%</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full">
                  <div className="h-full bg-blue-600 rounded-full" style={{ width: `${v}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Required skills & tags */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white rounded-xl border p-6">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">必备能力</h3>
            <div className="flex flex-wrap gap-1.5">
              {(jp.required_skills || []).map((s: string, i: number) => (
                <span key={i} className="px-2 py-1 bg-blue-50 text-blue-700 rounded-full text-xs">{s}</span>
              ))}
            </div>
          </div>
          <div className="bg-white rounded-xl border p-6">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">技能标签</h3>
            <div className="flex flex-wrap gap-1.5">
              {(jp.skill_tags || []).map((s: string, i: number) => (
                <span key={i} className="px-2 py-1 bg-gray-50 text-gray-700 rounded-full text-xs border">{s}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
