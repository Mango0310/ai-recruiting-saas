"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getCandidate, updateDecision, getMatchReport, reanalyzeApplication, saveFeedback, getResumeContent, updateApplicationStatus, onboardEmployee, generateInterviewQuestions } from "@/lib/api";

const scoreBar: Record<string, number> = {
  high: 90, mid_high: 70, mid: 50, mid_low: 30, low: 15, no_match: 5,
};

export default function CandidateProfile() {
  const { id } = useParams<{ id: string }>();
  const [candidate, setCandidate] = useState<any>(null);
  const [report, setReport] = useState<any>(null);
  const [loadingReport, setLoadingReport] = useState(true);
  const [decision, setDecision] = useState("");
  const [notes, setNotes] = useState("");
  const [saved, setSaved] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState({ ai_predictions_match: "", actual_rating: 0, key_observations: "", interviewer: "" });
  const [feedbackSaved, setFeedbackSaved] = useState(false);
  const [onboardLink, setOnboardLink] = useState("");
  const [showResume, setShowResume] = useState(false);
  const [resumeContent, setResumeContent] = useState<any>(null);
  const [showOnboard, setShowOnboard] = useState(false);
  const [interviewQs, setInterviewQs] = useState<any>(null);
  const [qsLoading, setQsLoading] = useState(false);
  const [onboard, setOnboard] = useState({
    hire_date: new Date().toISOString().slice(0, 10), probation_months: 3, salary: "",
    department: "", position: "", reports_to: "",
    id_number: "", contract_type: "fulltime", contract_end_date: "",
    social_insurance: "pending", social_insurance_account: "", housing_fund: "pending", housing_fund_account: "",
    bank_name: "", bank_account: "",
    emergency_contact_name: "", emergency_contact_phone: "", emergency_contact_relation: "",
    notes: "",
  });

  const loadResume = async () => {
    if (!appId) return;
    try {
      const data = await getResumeContent(appId);
      setResumeContent(data);
      setShowResume(true);
    } catch {
      alert("无法加载简历");
    }
  };

  useEffect(() => {
    getCandidate(Number(id)).then((c) => {
      setCandidate(c);
      setDecision(c.applications?.[0]?.hr_decision || "pending");
    });
  }, [id]);

  const appId = candidate?.applications?.[0]?.application_id;

  useEffect(() => {
    if (!appId) return;
    setLoadingReport(true);
    getMatchReport(appId)
      .then(setReport)
      .catch(async () => {
        try { const r = await reanalyzeApplication(appId); setReport(r); } catch { /* none */ }
      })
      .finally(() => setLoadingReport(false));
  }, [appId]);

  const handleDecision = async (d: string) => {
    if (!appId) return;
    setDecision(d);
    setSaved(false);
    await updateDecision(appId, d, notes);
    // Refresh to update pipeline status
    const updated = await getCandidate(Number(id));
    setCandidate(updated);
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const handleSaveNotes = async () => {
    if (!appId) return;
    setSaved(false);
    await updateDecision(appId, decision, notes);
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const handleFeedback = async () => {
    if (!appId) return;
    setFeedbackSaved(false);
    await saveFeedback(appId, feedback);
    // Refresh candidate to get updated pipeline status
    const updated = await getCandidate(Number(id));
    setCandidate(updated);
    setFeedbackSaved(true);
    setShowFeedback(false);
    setTimeout(() => setFeedbackSaved(false), 2500);
  };

  if (!candidate) return <div className="flex justify-center py-20"><div className="animate-pulse text-gray-400">加载中...</div></div>;

  const profile = candidate.profile || {};
  const mr = report?.match_report;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link href="/" className="text-sm text-gray-400 hover:text-gray-600">&larr; 返回</Link>
          <h1 className="text-2xl font-bold mt-1">{candidate.name}</h1>
          <p className="text-gray-500 text-sm">
            {profile.current_position} {profile.current_company ? `@ ${profile.current_company}` : ""} · {profile.years_of_experience}年经验 · {profile.highest_degree}
          </p>
        </div>
        <div className="flex gap-2">
          {appId && (
            <>
              <button onClick={loadResume} className="px-4 py-2 text-sm border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition">
                查看原始简历
              </button>
              <button onClick={() => reanalyzeApplication(appId).then(setReport)} className="px-4 py-2 text-sm border border-blue-200 text-blue-600 rounded-lg hover:bg-blue-50 transition">
                AI 重新分析
              </button>
            </>
          )}
        </div>
      </div>

      {/* Pipeline Status */}
      {appId && (
        <div className="bg-white rounded-xl border p-4">
          <div className="flex items-center gap-1 text-xs flex-wrap">
            {[
              { key: "new", label: "简历入库" },
              { key: "parsed", label: "AI解析" },
              { key: "ai_screened", label: "匹配分析" },
              { key: "hr_reviewed", label: "HR筛选" },
              { key: "interviewing", label: "面试中" },
              { key: "interviewed", label: "面试完成" },
            ].map((stage, i, arr) => {
              const appStatus = candidate.applications?.[0]?.status || "new";
              const done = i <= arr.findIndex(s => s.key === appStatus) || appStatus === "hired" || appStatus === "talent_pool";
              const current = stage.key === appStatus;
              return (
                <div key={stage.key} className="flex items-center gap-1">
                  <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                    done ? (current ? "bg-blue-600 text-white ring-2 ring-blue-200" : "bg-blue-100 text-blue-600") : "bg-gray-100 text-gray-400"
                  }`}>{done ? "✓" : i + 1}</span>
                  <span className={done ? "text-blue-700 font-medium" : "text-gray-400"}>{stage.label}</span>
                  {i < arr.length - 1 && <span className="text-gray-300 mx-0.5">→</span>}
                </div>
              );
            })}
            {/* Branching endpoints */}
            <span className="text-gray-300 mx-1">→</span>
            {[
              { key: "hired", label: "入职员工库", dotClass: "bg-green-600 text-white ring-2 ring-green-200", textClass: "text-green-700 font-medium" },
              { key: "talent_pool", label: "储备人才库", dotClass: "bg-blue-600 text-white ring-2 ring-blue-200", textClass: "text-blue-700 font-medium" },
            ].map(ep => {
              const appStatus = candidate.applications?.[0]?.status || "";
              const isThis = appStatus === ep.key;
              const otherTaken = (appStatus === "hired" || appStatus === "talent_pool") && !isThis;
              const dotCls = isThis ? ep.dotClass : (otherTaken ? "bg-gray-100 text-gray-300" : "bg-gray-100 text-gray-400");
              const textCls = isThis ? ep.textClass : (otherTaken ? "text-gray-300" : "text-gray-400");
              return (
                <div key={ep.key} className="flex items-center gap-1">
                  <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${dotCls}`}>{isThis ? "✓" : "○"}</span>
                  <span className={`text-xs ${textCls}`}>{ep.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
      {loadingReport && (
        <div className="bg-white rounded-xl border p-12 text-center">
          <div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-3" />
          <p className="text-gray-500 text-sm">AI 正在生成匹配分析报告...</p>
        </div>
      )}

      {!loadingReport && mr && (
        <div className="space-y-6">
          {/* Hero */}
          <div className="bg-gradient-to-br from-blue-600 to-blue-800 rounded-xl p-8 text-white">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-blue-200 text-xs font-medium mb-2">AI 匹配分析报告</p>
                <p className="text-2xl font-bold mb-1">{mr.overall_conclusion}</p>
                <p className="text-blue-100 text-sm max-w-lg">{mr.summary}</p>
              </div>
              <div className="text-right">
                {mr.eval_level && (
                  <span className={`inline-block text-sm font-bold px-2 py-0.5 rounded mb-1 ${
                    mr.eval_level === "A级" ? "bg-green-500 text-white"
                    : mr.eval_level === "B级" ? "bg-blue-400 text-white"
                    : "bg-gray-400 text-white"
                  }`}>{mr.eval_level}</span>
                )}
                <div className="text-3xl tracking-wider">
                  {"★".repeat(mr.star_rating || 0)}
                  <span className="text-blue-400">{"★".repeat(5 - (mr.star_rating || 0))}</span>
                </div>
                <p className="text-blue-200 text-xs mt-1">
                  {mr.star_rating === 5 ? "高度匹配" : mr.star_rating === 4 ? "大部分匹配" : mr.star_rating === 3 ? "部分匹配" : mr.star_rating === 2 ? "匹配度较低" : "基本不匹配"}
                </p>
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <button onClick={() => window.print()} className="px-3 py-1.5 text-xs bg-white/20 text-white rounded-lg hover:bg-white/30 border border-white/30 transition">
                打印面试准备单
              </button>
              <span className="text-blue-300 text-[11px] hidden sm:inline">| AI 分析仅供参考，不替代HR最终决策</span>
            </div>
          </div>

          {/* Interview Prep */}
          <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl border border-purple-200 p-6">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">📋</span>
              <h3 className="font-bold text-purple-900">面试准备清单</h3>
              <span className="text-xs text-purple-400 ml-2">发给面试官</span>
              <div className="flex-1" />
              <button
                onClick={async () => { setQsLoading(true); try { const d = await generateInterviewQuestions(appId); setInterviewQs(d); } catch { alert("生成失败"); } finally { setQsLoading(false); }}}
                className="text-xs px-3 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                disabled={qsLoading}
              >
                {qsLoading ? "AI 生成中..." : (interviewQs ? "重新生成" : "AI 生成结构化面试题")}
              </button>
            </div>

            {interviewQs?.interview_questions ? (
              /* Structured interview */
              (() => {
                const iq = interviewQs.interview_questions;
                const structure = iq.interview_structure || {};
                const phases: Array<{key: string; label: string; color: string; items: any[]}> = [
                  { key: "opening", label: "开场", color: "bg-green-500", items: structure.opening || [] },
                  { key: "technical_deep_dive", label: "技术深挖", color: "bg-blue-500", items: structure.technical_deep_dive || [] },
                  { key: "behavioral", label: "行为面试", color: "bg-purple-500", items: structure.behavioral || [] },
                  { key: "situational", label: "情景题", color: "bg-orange-500", items: structure.situational || [] },
                  { key: "closing", label: "收尾", color: "bg-gray-500", items: structure.closing || [] },
                ];
                return (
                  <div className="space-y-4">
                    {iq.interview_focus?.length > 0 && (
                      <div className="bg-purple-100 rounded-lg p-3 text-xs">
                        <span className="font-medium text-purple-700">面试重点：</span>
                        <span className="text-purple-600">{iq.interview_focus.join("  ·  ")}</span>
                        <span className="text-purple-400 ml-3">预计 {iq.estimated_total_duration} · {iq.difficulty_assessment}</span>
                      </div>
                    )}
                    {phases.map(phase => phase.items.length > 0 && (
                      <div key={phase.key}>
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`w-2 h-2 rounded-full ${phase.color}`} />
                          <span className="text-xs font-bold text-gray-500">{phase.label}</span>
                          <span className="text-xs text-gray-400">({phase.items.length}题)</span>
                        </div>
                        {phase.items.map((q: any, qi: number) => (
                          <div key={qi} className="flex gap-3 items-start bg-white/60 rounded-lg p-3 mb-2">
                            <span className="flex-shrink-0 w-7 h-7 rounded-full bg-purple-600 text-white text-xs font-bold flex items-center justify-center">{qi + 1}</span>
                            <div className="flex-1">
                              <p className="text-sm text-gray-800 font-medium">{q.question}</p>
                              <div className="flex gap-3 mt-1.5">
                                {q.why && <span className="text-xs text-purple-500">{q.why}</span>}
                                {q.duration && <span className="text-xs text-gray-400">⏱ {q.duration}</span>}
                                {q.dimension && <span className="text-xs px-1.5 py-0.5 bg-purple-50 text-purple-600 rounded">能力：{q.dimension}</span>}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                );
              })()
            ) : (
              /* Fallback to simple suggestions */
              <div className="space-y-3">
                {(mr.interview_suggestions || []).map((s: string, i: number) => (
                  <div key={i} className="flex gap-3 items-start bg-white/60 rounded-lg p-3">
                    <span className="flex-shrink-0 w-7 h-7 rounded-full bg-purple-600 text-white text-xs font-bold flex items-center justify-center">{i + 1}</span>
                    <p className="text-sm text-gray-800 pt-0.5">{s}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Dimensions */}
          <div className="bg-white rounded-xl border p-6">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">匹配维度分析</h3>
            <div className="grid grid-cols-2 gap-4">
              {(Object.entries(mr.dimension_scores || {}) as [string, string][]).map(([k, v]) => (
                <div key={k}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">{k}</span>
                    <span className="font-medium text-blue-600">{v}</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-600 rounded-full transition-all duration-700" style={{ width: `${scoreBar[v] || 50}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Strengths vs Gaps */}
          <div className="grid grid-cols-2 gap-6">
            <div className="bg-white rounded-xl border p-6">
              <h3 className="text-sm font-semibold text-green-600 uppercase tracking-wider mb-4">匹配优势</h3>
              {(mr.strengths || []).map((s: any, i: number) => (
                <div key={i} className="mb-3 pl-3 border-l-2 border-green-200">
                  <p className="text-sm font-medium text-gray-800">{s.point}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{s.evidence}</p>
                </div>
              ))}
            </div>
            <div className="bg-white rounded-xl border p-6">
              <h3 className="text-sm font-semibold text-orange-600 uppercase tracking-wider mb-4">待关注</h3>
              {(mr.gaps || []).map((g: any, i: number) => (
                <div key={i} className="mb-3 pl-3 border-l-2 border-orange-200">
                  <p className="text-sm font-medium text-gray-800">{g.point}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{g.evidence}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Potential Assessment */}
          {(mr.potential_signals && mr.potential_signals.length > 0) && (
            <div className="bg-white rounded-xl border p-6">
              <div className="flex items-center gap-2 mb-4">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">潜质评估</h3>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  mr.potential_level === "high" ? "bg-green-50 text-green-700"
                  : mr.potential_level === "medium" ? "bg-blue-50 text-blue-700"
                  : "bg-gray-50 text-gray-600"
                }`}>
                  {mr.potential_level === "high" ? "高潜质" : mr.potential_level === "medium" ? "有潜力" : "待观察"}
                </span>
              </div>
              <div className="space-y-3">
                {(mr.potential_signals || []).map((ps: any, i: number) => (
                  <div key={i} className="flex gap-3 items-start">
                    <span className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-100 text-purple-700 text-xs font-bold flex items-center justify-center">{i + 1}</span>
                    <div>
                      <p className="text-sm font-medium text-gray-800">{ps.signal}</p>
                      <p className="text-xs text-gray-400">{ps.evidence}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Candidate Profile Detail */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <div className="px-6 py-3 bg-gray-50 border-b">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">候选人画像</h3>
        </div>
        <div className="p-6 space-y-5">
          <div>
            <h4 className="text-xs font-semibold text-gray-400 mb-2">技能标签</h4>
            <div className="flex flex-wrap gap-1.5">
              {(profile.skills || []).map((s: string, i: number) => (
                <span key={i} className="px-2.5 py-1 bg-gray-50 text-gray-700 rounded-full text-xs border border-gray-100">{s}</span>
              ))}
            </div>
          </div>
          <div>
            <h4 className="text-xs font-semibold text-gray-400 mb-2">工作经历</h4>
            {(profile.work_experience || []).map((exp: any, i: number) => (
              <div key={i} className="mb-3 pl-4 border-l-2 border-gray-100">
                <p className="text-sm font-semibold">{exp.position}</p>
                <p className="text-xs text-gray-400">{exp.company} · {exp.start_date} — {exp.end_date}</p>
                {(exp.projects || []).map((proj: any, j: number) => (
                  <div key={j} className="mt-2 ml-2">
                    <p className="text-sm font-medium text-gray-700">{proj.name}</p>
                    <p className="text-xs text-gray-500">{proj.description}</p>
                    {(proj.highlights || []).map((h: string, k: number) => (
                      <p key={k} className="text-xs text-gray-500 ml-2 mt-0.5">· {h}</p>
                    ))}
                  </div>
                ))}
              </div>
            ))}
          </div>
          <div>
            <h4 className="text-xs font-semibold text-gray-400 mb-2">教育背景</h4>
            {(profile.education || []).map((edu: any, i: number) => (
              <p key={i} className="text-sm text-gray-600">{edu.school} · {edu.degree} · {edu.major} · {edu.start_year}-{edu.end_year}</p>
            ))}
          </div>

          {/* Tech stack depth (tech roles) */}
          {profile.tech_stack_depth && (
            <div>
              <h4 className="text-xs font-semibold text-blue-600 mb-2 uppercase tracking-wider">技术栈深度</h4>
              <div className="grid grid-cols-2 gap-3 text-sm">
                {profile.tech_stack_depth.primary_languages && (
                  <div>
                    <span className="text-gray-400">主力语言: </span>
                    <span className="text-gray-700 font-medium">{(profile.tech_stack_depth.primary_languages as string[]).join(" / ")}</span>
                  </div>
                )}
                {profile.tech_stack_depth.scale_context && (
                  <div className="col-span-2">
                    <span className="text-gray-400">规模场景: </span>
                    <span className="text-gray-700">{profile.tech_stack_depth.scale_context}</span>
                  </div>
                )}
              </div>
              {(profile.open_source_contributions && profile.open_source_contributions.length > 0) && (
                <div className="mt-2">
                  <span className="text-xs text-gray-400">开源贡献: </span>
                  <span className="text-sm text-gray-700">{(profile.open_source_contributions as string[]).join(" / ")}</span>
                </div>
              )}
              {(profile.code_quality_indicators && profile.code_quality_indicators.length > 0) && (
                <div className="mt-1">
                  <span className="text-xs text-gray-400">工程化实践: </span>
                  <span className="text-sm text-gray-700">{(profile.code_quality_indicators as string[]).join(" / ")}</span>
                </div>
              )}
            </div>
          )}

          {/* GitHub signals (tech roles) */}
          {profile.github_profile && (
            <div>
              <h4 className="text-xs font-semibold text-gray-400 mb-2">
                GitHub 信号
                <a href={profile.github_profile.profile_url} target="_blank" rel="noopener noreferrer"
                   className="ml-2 text-blue-500 hover:underline font-normal">
                  @{profile.github_profile.username} &rarr;
                </a>
              </h4>
              <div className="grid grid-cols-3 gap-2 text-sm">
                <div className="bg-gray-50 rounded-lg p-2 text-center">
                  <p className="text-lg font-bold text-gray-700">{profile.github_profile.public_repos}</p>
                  <p className="text-xs text-gray-400">公开仓库</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-2 text-center">
                  <p className="text-lg font-bold text-yellow-600">{profile.github_profile.total_stars}</p>
                  <p className="text-xs text-gray-400">Stars</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-2 text-center">
                  <p className="text-lg font-bold text-gray-700">{profile.github_profile.followers}</p>
                  <p className="text-xs text-gray-400">Followers</p>
                </div>
              </div>
              {(profile.github_profile.top_languages && profile.github_profile.top_languages.length > 0) && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {(profile.github_profile.top_languages as string[]).map((lang: string) => (
                    <span key={lang} className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs">{lang}</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Portfolio (design roles) */}
          {profile.portfolio_url && (
            <div>
              <h4 className="text-xs font-semibold text-gray-400 mb-2">作品集链接</h4>
              <a href={profile.portfolio_url} target="_blank" rel="noopener noreferrer"
                 className="text-blue-600 text-sm hover:underline break-all flex items-center gap-1">
                {profile.portfolio_url}
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
              </a>
            </div>
          )}

          {/* Design tools (design roles) */}
          {profile.design_tools && profile.design_tools.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-400 mb-2">设计工具</h4>
              <div className="flex flex-wrap gap-2">
                {(profile.design_tools as Array<{tool: string; proficiency: string}>).map((dt, i) => {
                  const profColors: Record<string, string> = {
                    expert: "bg-pink-100 text-pink-700 border-pink-200",
                    advanced: "bg-purple-50 text-purple-700 border-purple-200",
                    intermediate: "bg-blue-50 text-blue-700 border-blue-200",
                    beginner: "bg-gray-50 text-gray-600 border-gray-200",
                  };
                  return (
                    <span key={i} className={`px-2.5 py-1 rounded-full text-xs border ${profColors[dt.proficiency] || "bg-gray-50 text-gray-600 border-gray-200"}`}>
                      {dt.tool} · {dt.proficiency}
                    </span>
                  );
                })}
              </div>
            </div>
          )}

          {/* Design methodology (design roles) */}
          {profile.design_methodology && profile.design_methodology.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-400 mb-2">设计方法论</h4>
              <div className="flex flex-wrap gap-1.5">
                {(profile.design_methodology as string[]).map((m: string, i: number) => (
                  <span key={i} className="px-2.5 py-1 bg-orange-50 text-orange-700 rounded-full text-xs border border-orange-100">{m}</span>
                ))}
              </div>
            </div>
          )}

          {/* Design system experience (design roles) */}
          {profile.design_system_experience && (
            <div>
              <h4 className="text-xs font-semibold text-gray-400 mb-1">设计系统经验</h4>
              <p className="text-sm text-gray-700">{profile.design_system_experience}</p>
            </div>
          )}

          {/* Project types (design roles) */}
          {profile.project_types && profile.project_types.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {(profile.project_types as string[]).map((pt: string, i: number) => (
                <span key={i} className="px-2 py-0.5 bg-gray-50 text-gray-500 rounded text-xs border border-gray-100">{pt}</span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Resume Modal */}
      {showResume && resumeContent && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setShowResume(false)}>
          <div className="bg-white rounded-xl w-full max-w-2xl max-h-[80vh] overflow-y-auto mx-4" onClick={e => e.stopPropagation()}>
            <div className="px-6 py-4 border-b flex items-center justify-between sticky top-0 bg-white">
              <h3 className="font-semibold">{resumeContent.file_name}</h3>
              <button onClick={() => setShowResume(false)} className="text-gray-400 hover:text-gray-600 text-lg">&times;</button>
            </div>
            <div className="p-6">
              {resumeContent.parse_status === "completed" ? (
                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">{resumeContent.raw_text}</pre>
              ) : (
                <p className="text-gray-500 text-sm">简历解析状态: {resumeContent.parse_status}，无法预览原始内容</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* HR Decision */}
      {appId && (
        <div className="bg-white rounded-xl border p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">HR 决策</h3>
            {saved && (
              <span className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded-full flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                已保存
              </span>
            )}
          </div>
          <div className="flex gap-2 mb-3">
            {[
              { value: "suitable", label: "合适", color: "green" },
              { value: "maybe", label: "待定", color: "yellow" },
              { value: "not_suitable", label: "不合适", color: "red" },
            ].map((d) => (
              <button
                key={d.value}
                onClick={() => handleDecision(d.value)}
                className={`px-4 py-2 text-sm rounded-lg border transition ${
                  decision === d.value
                    ? d.color === "green" ? "bg-green-600 text-white border-green-600 shadow-sm"
                    : d.color === "yellow" ? "bg-yellow-600 text-white border-yellow-600 shadow-sm"
                    : "bg-red-600 text-white border-red-600 shadow-sm"
                    : "hover:bg-gray-50 border-gray-200"
                }`}
              >
                {d.label}
              </button>
            ))}
          </div>
          <div className="flex gap-2 items-start">
            <textarea
              className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400 transition"
              rows={2}
              placeholder="添加备注..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
            <button onClick={handleSaveNotes} className="px-4 py-2 text-sm bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition flex-shrink-0">
              保存备注
            </button>
          </div>

          {/* Interview Feedback — only available after HR decides to interview */}
          {decision === "suitable" && (
          <div className="border-t pt-4 mt-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">面试反馈</h3>
              <button onClick={() => setShowFeedback(!showFeedback)} className="text-xs text-blue-500 hover:underline">
                {showFeedback ? "收起" : (candidate.applications?.[0]?.interview_feedback ? "查看反馈" : "记录反馈")}
              </button>
            </div>

            {/* Feedback saved — show comparison + recommendation */}
            {candidate.applications?.[0]?.interview_feedback && !showFeedback && (() => {
              const fb = candidate.applications[0].interview_feedback;
              const aiStar = fb.ai_predicted_rating || 0;
              const actualStar = fb.actual_rating || 0;
              const diff = actualStar - aiStar;
              return (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-gray-400 mb-1">AI 预测</p>
                      <p className="text-lg font-bold text-yellow-500">{"★".repeat(aiStar)}</p>
                      <p className="text-gray-500 mt-0.5">{fb.interviewer ? `${fb.interviewer} 面试` : ""}</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-gray-400 mb-1">实际面试</p>
                      <p className="text-lg font-bold text-green-600">{"★".repeat(actualStar)}</p>
                      <p className="text-gray-500 mt-0.5">AI预测: {fb.ai_predictions_match === "match" ? "准确" : fb.ai_predictions_match === "partial" ? "部分准确" : "不准确"}</p>
                    </div>
                  </div>
                  {fb.key_observations && (
                    <div className="bg-purple-50 rounded-lg p-3 text-xs">
                      <p className="font-medium text-purple-700 mb-1">面试关键观察</p>
                      <p className="text-purple-800">{fb.key_observations}</p>
                    </div>
                  )}

                  {/* Decision recommendation */}
                  <div className={`rounded-lg p-4 ${actualStar >= 4 ? "bg-green-50 border border-green-200" : actualStar >= 3 ? "bg-yellow-50 border border-yellow-200" : "bg-gray-50 border border-gray-200"}`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-bold">
                          {actualStar >= 4 ? "建议推进" : actualStar >= 3 ? "建议二面或备选" : "建议放入人才库"}
                        </p>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {diff >= 1 ? `实际表现高出AI预测${diff}星，建议重视` :
                           diff <= -2 ? `实际表现低于AI预测${-diff}星，建议重新评估或拒信` :
                           diff < 0 ? `实际表现略低于AI预测，可考虑二面进一步验证` :
                           "实际表现与AI预测基本一致"}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        {actualStar >= 3 && (
                          <button onClick={() => handleDecision("suitable")}
                            className={`px-3 py-1.5 text-xs rounded-lg ${decision === "suitable" ? "bg-green-600 text-white" : "border border-green-300 text-green-700 hover:bg-green-50"}`}>
                            合适
                          </button>
                        )}
                        {actualStar >= 2 && (
                          <button onClick={() => handleDecision("maybe")}
                            className="px-3 py-1.5 text-xs rounded-lg border border-yellow-300 text-yellow-700 hover:bg-yellow-50">
                            待定
                          </button>
                        )}
                        <button onClick={() => handleDecision("not_suitable")}
                          className="px-3 py-1.5 text-xs rounded-lg border border-red-300 text-red-700 hover:bg-red-50">
                          不合适
                        </button>
                      </div>
                    </div>
                    {saved && (
                      <p className="text-xs text-green-600 mt-2">✓ 决策已保存</p>
                    )}
                  </div>
                </div>
              );
            })()}

            {showFeedback && (
              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">面试官</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="面试官姓名"
                    value={feedback.interviewer} onChange={e => setFeedback({...feedback, interviewer: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">AI 预测准确度</label>
                  <select className="w-full border rounded-lg px-3 py-2 text-sm" value={feedback.ai_predictions_match}
                    onChange={e => setFeedback({...feedback, ai_predictions_match: e.target.value})}>
                    <option value="">请选择</option>
                    <option value="match">准确 — 面试表现与AI分析一致</option>
                    <option value="partial">部分准确 — 有些点对，有些偏差</option>
                    <option value="no_match">不准确 — 实际与AI分析出入很大</option>
                  </select>
                </div>
                <div className="flex items-start gap-3">
                  <div className="flex-1">
                    <label className="block text-xs text-gray-500 mb-1">实际面试评分</label>
                    <div className="flex gap-1 text-xl">
                      {[1,2,3,4,5].map(n => (
                        <button key={n} onClick={() => setFeedback({...feedback, actual_rating: n})}
                          className={feedback.actual_rating >= n ? "text-yellow-500" : "text-gray-300"}>★</button>
                      ))}
                    </div>
                  </div>
                  {report && (
                    <div className="text-right text-xs text-gray-400 pt-5">
                      AI 预测: {"★".repeat(report.match_report?.star_rating || 0)}
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">关键观察</label>
                  <textarea className="w-full border rounded-lg px-3 py-2 text-sm" rows={2}
                    placeholder="面完后核心判断：哪里比预期好？哪里让人不放心？"
                    value={feedback.key_observations} onChange={e => setFeedback({...feedback, key_observations: e.target.value})} />
                </div>
                <button onClick={handleFeedback} className="w-full py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 transition">
                  {feedbackSaved ? "✓ 已保存" : "保存面试反馈"}
                </button>
              </div>
            )}
          </div>
          )}

          {/* Pipeline complete — final action */}
          {candidate.applications?.[0]?.status !== "hired" && candidate.applications?.[0]?.status !== "talent_pool" && decision !== "pending" && (
            <div className="border-t pt-3 mt-3">
              <p className="text-xs text-gray-400 mb-2">
                当前阶段: {candidate.applications?.[0]?.status === "interviewed" ? "面试已完成" : candidate.applications?.[0]?.status === "interviewing" ? "面试中" : "HR已筛选"}
                — 确认最终结果？
              </p>
              <button
                onClick={() => {
                  if (decision === "suitable") {
                    // Pre-fill from candidate & job data
                    setOnboard({
                      ...onboard,
                      position: profile.current_position || "",
                      department: candidate.applications?.[0]?.job?.department || "",
                      salary: "",
                      hire_date: new Date().toISOString().slice(0, 10),
                      probation_months: 3,
                      housing_fund: "pending",
                      social_insurance: "pending",
                      bank_name: "",
                      bank_account: "",
                      id_number: "",
                      emergency_contact_name: "",
                      emergency_contact_phone: "",
                      notes: "",
                    });
                    setShowOnboard(true);
                  } else {
                    if (!confirm("确认放入储备人才库？")) return;
                    updateApplicationStatus(appId, "talent_pool").then(async () => {
                      const updated = await getCandidate(Number(id));
                      setCandidate(updated);
                    });
                  }
                }}
                className={`w-full py-2 text-sm rounded-lg transition ${
                  decision === "suitable" ? "bg-green-600 text-white hover:bg-green-700"
                  : decision === "maybe" ? "bg-blue-600 text-white hover:bg-blue-700"
                  : "bg-gray-600 text-white hover:bg-gray-700"
                }`}
              >
                {decision === "suitable" ? "✓ 确认录用 — 录入入职员工库" : decision === "maybe" ? "→ 放入储备人才库备用" : "→ 归档到储备人才库"}
              </button>
            </div>
          )}

          {/* Completed — shows where the candidate ended up */}
          {(candidate.applications?.[0]?.status === "hired" || candidate.applications?.[0]?.status === "talent_pool") && (
            <div className="border-t pt-3 mt-3">
              <div className={`rounded-lg p-3 text-center ${candidate.applications[0].status === "hired" ? "bg-green-50 border border-green-200" : "bg-blue-50 border border-blue-200"}`}>
                <p className={`text-sm font-semibold ${candidate.applications[0].status === "hired" ? "text-green-800" : "text-blue-800"}`}>
                  {candidate.applications[0].status === "hired" ? "✓ 已录入入职员工库" : "已归档到储备人才库"}
                </p>
                <p className={`text-xs mt-1 ${candidate.applications[0].status === "hired" ? "text-green-600" : "text-blue-600"}`}>
                  {candidate.applications[0].status === "hired" ? "可在导航栏「员工台账」中查看" : "可在「人才库」中搜索复用"}
                </p>
                {candidate.applications[0].status === "hired" && onboardLink && (
                  <div className="mt-3 p-3 bg-white rounded-lg border border-green-300 text-left">
                    <p className="text-xs font-medium text-gray-700 mb-1">员工自助入职链接（发给员工填写个人信息）</p>
                    <div className="flex gap-2">
                      <input className="flex-1 text-xs border rounded px-2 py-1 bg-gray-50" value={onboardLink} readOnly />
                      <button onClick={() => { navigator.clipboard.writeText(onboardLink); alert("已复制链接"); }}
                        className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 whitespace-nowrap">
                        复制链接
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Onboarding Form Modal */}
      {showOnboard && (
        <div className="fixed inset-0 bg-black/40 flex items-start justify-center z-50 overflow-y-auto py-10" onClick={() => setShowOnboard(false)}>
          <div className="bg-white rounded-xl p-6 w-full max-w-2xl mx-4 space-y-4" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold">入职登记表 — {candidate.name}</h2>
              <button onClick={() => setShowOnboard(false)} className="text-gray-400 hover:text-gray-600 text-lg">&times;</button>
            </div>

            <div className="bg-blue-50 rounded-lg p-3 text-xs text-blue-700 mb-2">
              HR只需填写岗位信息和入职日期。个人信息（身份证、银行卡、紧急联系人、社保公积金账号）将通过链接由员工自助填写。
            </div>

            <div className="border-t pt-3">
              <p className="text-xs font-medium text-gray-500 mb-2">岗位信息（HR填写）</p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">岗位</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="从招聘需求继承"
                    value={onboard.position} onChange={e => setOnboard({...onboard, position: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">部门</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="从招聘需求继承"
                    value={onboard.department} onChange={e => setOnboard({...onboard, department: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">汇报对象</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="直属上级"
                    value={onboard.reports_to} onChange={e => setOnboard({...onboard, reports_to: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">薪资</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="如：25K×14薪"
                    value={onboard.salary} onChange={e => setOnboard({...onboard, salary: e.target.value})} />
                </div>
              </div>
            </div>

            <div className="border-t pt-3">
              <p className="text-xs font-medium text-gray-500 mb-2">入职信息</p>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">入职日期</label>
                  <input type="date" className="w-full border rounded-lg px-3 py-2 text-sm"
                    value={onboard.hire_date} onChange={e => setOnboard({...onboard, hire_date: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">试用期(月)</label>
                  <select className="w-full border rounded-lg px-3 py-2 text-sm" value={onboard.probation_months}
                    onChange={e => setOnboard({...onboard, probation_months: parseInt(e.target.value)})}>
                    <option value={1}>1个月</option><option value={2}>2个月</option>
                    <option value={3}>3个月</option><option value={6}>6个月</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">合同类型</label>
                  <select className="w-full border rounded-lg px-3 py-2 text-sm" value={onboard.contract_type}
                    onChange={e => setOnboard({...onboard, contract_type: e.target.value})}>
                    <option value="fulltime">全职</option><option value="parttime">兼职</option><option value="intern">实习</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 mt-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">合同到期日</label>
                  <input type="date" className="w-full border rounded-lg px-3 py-2 text-sm"
                    value={onboard.contract_end_date} onChange={e => setOnboard({...onboard, contract_end_date: e.target.value})} />
                </div>
              </div>
            </div>

            <div className="border-t pt-3">
              <p className="text-xs font-medium text-gray-500 mb-2">社保公积金状态（HR确认）</p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">社保</label>
                  <select className="w-full border rounded-lg px-3 py-2 text-sm" value={onboard.social_insurance}
                    onChange={e => setOnboard({...onboard, social_insurance: e.target.value})}>
                    <option value="pending">待办理</option><option value="active">已缴纳</option><option value="exempt">不适用</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">公积金</label>
                  <select className="w-full border rounded-lg px-3 py-2 text-sm" value={onboard.housing_fund}
                    onChange={e => setOnboard({...onboard, housing_fund: e.target.value})}>
                    <option value="pending">待办理</option><option value="active">已缴纳</option><option value="exempt">不适用</option>
                  </select>
                </div>
              </div>
              <p className="text-xs text-gray-400 mt-2">个人账号信息（身份证、银行卡、紧急联系人、社保公积金账号）将生成链接由员工自助填写</p>
            </div>

            <div>
              <label className="block text-xs text-gray-500 mb-1">备注</label>
              <textarea className="w-full border rounded-lg px-3 py-2 text-sm" rows={2} placeholder="HR内部备注"
                value={onboard.notes} onChange={e => setOnboard({...onboard, notes: e.target.value})} />
            </div>

            <div className="flex gap-2 justify-end pt-2">
              <button onClick={() => setShowOnboard(false)} className="px-4 py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-lg">取消</button>
              <button onClick={async () => {
                const result = await onboardEmployee({ application_id: appId, ...onboard });
                setOnboardLink(result.onboard_link);
                setShowOnboard(false);
                const updated = await getCandidate(Number(id));
                setCandidate(updated);
              }} className="px-6 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700">
                确认入职
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
