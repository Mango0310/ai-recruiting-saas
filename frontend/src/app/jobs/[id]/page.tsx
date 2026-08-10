"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getJob, updateJob, deleteJob, getCandidates, reanalyzeJob, getCompareCandidates, getBriefing } from "@/lib/api";

export default function JobDetail() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [job, setJob] = useState<any>(null);
  const [candidates, setCandidates] = useState<any[]>([]);
  const [tab, setTab] = useState<"profile" | "candidates" | "compare">("profile");
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editJd, setEditJd] = useState("");
  const [editProfile, setEditProfile] = useState("");
  const [decisionFilter, setDecisionFilter] = useState<string>("all");
  const [compareData, setCompareData] = useState<any>(null);
  const [briefingData, setBriefingData] = useState<any>(null);
  const [showBriefing, setShowBriefing] = useState(false);

  const fetchJob = () => getJob(Number(id)).then((j) => { setJob(j); setEditTitle(j.title); setEditJd(j.jd_raw || ""); setEditProfile(JSON.stringify(j.job_profile, null, 2)); }).catch(console.error);
  const fetchCandidates = () => getCandidates(Number(id)).then(setCandidates).catch(console.error);
  const fetchCompare = () => getCompareCandidates(Number(id)).then(setCompareData).catch(console.error);
  const fetchBriefing = () => getBriefing(Number(id)).then((d) => { setBriefingData(d); setShowBriefing(true); }).catch(console.error);

  useEffect(() => { fetchJob(); fetchCandidates(); }, [id]);
  useEffect(() => { if (tab === "compare") fetchCompare(); }, [tab]);

  const handleSave = async () => {
    try {
      const profile = JSON.parse(editProfile);
      await updateJob(Number(id), { title: editTitle, jd_raw: editJd, job_profile: profile });
      setEditing(false);
      fetchJob();
    } catch {
      alert("JSON 格式错误");
    }
  };

  const handleDelete = async () => {
    if (!confirm("确定删除这个岗位？所有关联的候选人申请也将一并删除。")) return;
    try {
      await deleteJob(Number(id));
      router.push("/");
    } catch {
      alert("删除失败，请重试");
    }
  };

  const handleReanalyze = async () => {
    await reanalyzeJob(Number(id));
    fetchJob();
  };

  if (!job) return <div className="py-20 text-center text-gray-500">加载中...</div>;

  const profile = job.job_profile || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-gray-400 hover:text-gray-600">&larr; 返回</Link>
          <h1 className="text-xl font-bold">{job.title}</h1>
        </div>
        <div className="flex gap-2">
          {!editing && <button onClick={() => setEditing(true)} className="px-3 py-1.5 text-sm border rounded-lg hover:bg-gray-50">编辑</button>}
          <button onClick={handleDelete} className="px-3 py-1.5 text-sm border border-red-200 text-red-600 rounded-lg hover:bg-red-50">删除</button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b">
        <button onClick={() => setTab("profile")} className={`pb-2 text-sm font-medium ${tab === "profile" ? "text-blue-600 border-b-2 border-blue-600" : "text-gray-500"}`}>岗位画像</button>
        <button onClick={() => setTab("candidates")} className={`pb-2 text-sm font-medium ${tab === "candidates" ? "text-blue-600 border-b-2 border-blue-600" : "text-gray-500"}`}>
          候选人 ({candidates.length})
        </button>
        <button onClick={() => setTab("compare")} className={`pb-2 text-sm font-medium ${tab === "compare" ? "text-blue-600 border-b-2 border-blue-600" : "text-gray-500"}`}>
          对比分析
        </button>
      </div>

      {/* Profile Tab */}
      {tab === "profile" && !editing && (
        <div className="space-y-4">
          <div className="bg-white rounded-lg border p-6 space-y-4">
            <div>
              <h3 className="font-semibold mb-2">岗位职责</h3>
              <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                {(profile.responsibilities || []).map((r: string, i: number) => <li key={i}>{r}</li>)}
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-2">必备能力</h3>
              <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                {(profile.required_skills || []).map((s: string, i: number) => <li key={i}>{s}</li>)}
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-2">技能标签</h3>
              <div className="flex flex-wrap gap-2">
                {(profile.skill_tags || []).map((t: string, i: number) => (
                  <span key={i} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">{t}</span>
                ))}
              </div>
            </div>
            {/* Hiring Brief */}
            {profile.hiring_brief && (
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200 p-5 space-y-2">
                <h3 className="font-semibold text-gray-700 mb-1">Hiring Brief — 招聘任务说明书</h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-xs text-gray-400">招聘目标</p>
                    <p className="text-gray-800 font-medium">{profile.hiring_brief.goal}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400">团队定位</p>
                    <p className="text-gray-700">{profile.hiring_brief.team_fit}</p>
                  </div>
                </div>
                {(profile.hiring_brief.success_criteria || []).length > 0 && (
                  <div>
                    <p className="text-xs text-gray-400">成功标准</p>
                    {(profile.hiring_brief.success_criteria as string[]).map((c: string, i: number) => (
                      <p key={i} className="text-sm text-gray-700 ml-2">· {c}</p>
                    ))}
                  </div>
                )}
                {(profile.hiring_brief.key_challenges || []).length > 0 && (
                  <div>
                    <p className="text-xs text-gray-400">关键挑战</p>
                    {(profile.hiring_brief.key_challenges as string[]).map((c: string, i: number) => (
                      <p key={i} className="text-sm text-orange-700 ml-2">· {c}</p>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Job Goal */}
            {profile.job_goal && (
              <div className="bg-blue-50 rounded-lg p-4">
                <h3 className="font-semibold text-blue-800 mb-1">岗位目标</h3>
                <p className="text-sm text-blue-700">{profile.job_goal}</p>
              </div>
            )}

            {/* Competency Model */}
            {profile.competency_model && Object.keys(profile.competency_model).length > 0 && (
              <div>
                <h3 className="font-semibold mb-2">能力模型</h3>
                <div className="grid grid-cols-3 gap-3">
                  {Object.entries(profile.competency_model as Record<string, string[]>).map(([cat, skills]) => (
                    <div key={cat} className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs font-semibold text-gray-500 mb-1">{cat}</p>
                      {(skills as string[]).map((s: string, i: number) => (
                        <p key={i} className="text-xs text-gray-600">· {s}</p>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Evaluation Framework */}
            {profile.evaluation_framework && Object.keys(profile.evaluation_framework).length > 0 && (
              <div>
                <h3 className="font-semibold mb-2">面试评价标准</h3>
                <div className="space-y-2">
                  {Object.entries(profile.evaluation_framework as Record<string, string>).map(([level, desc]) => {
                    const isA = level.includes("A");
                    const isB = level.includes("B");
                    return (
                      <div key={level} className={`p-3 rounded-lg text-sm ${isA ? "bg-green-50 border border-green-200" : isB ? "bg-blue-50 border border-blue-200" : "bg-gray-50 border border-gray-200"}`}>
                        <span className="font-bold text-xs mr-2">{level}</span>
                        <span className="text-gray-700">{desc as string}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Unconfirmed items */}
            {profile.unconfirmed && (profile.unconfirmed as any[]).length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <p className="text-xs font-semibold text-yellow-700 mb-1">待业务方确认</p>
                {(profile.unconfirmed as string[]).map((item: string, i: number) => (
                  <p key={i} className="text-xs text-yellow-600">· {item}</p>
                ))}
              </div>
            )}

            {profile.experience_requirements && (
              <div>
                <h3 className="font-semibold mb-2">经验要求</h3>
                <p className="text-sm text-gray-700">最低年限: {profile.experience_requirements.years_min || 0}年</p>
                <p className="text-sm text-gray-700">行业: {(profile.experience_requirements.industry || []).join("、") || "不限"}</p>
                <p className="text-sm text-gray-700">优先: {(profile.experience_requirements.preferred || []).join("、") || "无"}</p>
              </div>
            )}
            <div className="flex gap-2 pt-2">
              <button onClick={handleReanalyze} className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">AI 重新分析</button>
            </div>
          </div>
        </div>
      )}

      {tab === "profile" && editing && (
        <div className="bg-white rounded-lg border p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">岗位名称</label>
            <input className="w-full border rounded-lg px-3 py-2 text-sm" value={editTitle} onChange={(e) => setEditTitle(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">JD 原文</label>
            <textarea className="w-full border rounded-lg px-3 py-2 text-sm h-32" value={editJd} onChange={(e) => setEditJd(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Job Profile (JSON)</label>
            <textarea className="w-full border rounded-lg px-3 py-2 text-sm font-mono h-60" value={editProfile} onChange={(e) => setEditProfile(e.target.value)} />
          </div>
          <div className="flex gap-2">
            <button onClick={handleSave} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">保存</button>
            <button onClick={() => setEditing(false)} className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50">取消</button>
          </div>
        </div>
      )}

      {/* Candidates Tab */}
      {tab === "candidates" && (
        <div className="space-y-4">
          <div className="flex gap-2 items-center justify-between">
            <div className="flex gap-2">
              <Link href={`/jobs/${id}/upload`} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">+ 上传简历</Link>
              {candidates.length > 0 && (
                <button onClick={fetchBriefing} className="px-4 py-2 text-sm border border-purple-200 text-purple-600 rounded-lg hover:bg-purple-50">
                  面试简报
                </button>
              )}
            </div>
            <select
              value={decisionFilter}
              onChange={(e) => setDecisionFilter(e.target.value)}
              className="text-sm border rounded-lg px-3 py-2 text-gray-600"
            >
              <option value="all">全部 ({candidates.length})</option>
              <option value="pending">待处理 ({candidates.filter((c: any) => c.hr_decision === "pending").length})</option>
              <option value="suitable">合适 ({candidates.filter((c: any) => c.hr_decision === "suitable").length})</option>
              <option value="maybe">待定 ({candidates.filter((c: any) => c.hr_decision === "maybe").length})</option>
              <option value="not_suitable">不合适 ({candidates.filter((c: any) => c.hr_decision === "not_suitable").length})</option>
            </select>
          </div>
          {candidates.filter((c: any) => decisionFilter === "all" || c.hr_decision === decisionFilter).length === 0 && (
            <p className="text-gray-400 py-10 text-center">暂无匹配的候选人</p>
          )}
          <div className="space-y-3">
            {candidates.filter((c: any) => decisionFilter === "all" || c.hr_decision === decisionFilter).map((c: any) => (
              <Link key={c.application_id} href={`/candidates/${c.candidate_id}`}
                className="block bg-white rounded-lg border p-5 hover:border-blue-300 hover:shadow-sm transition group">
                <div className="flex items-start justify-between gap-4">
                  {/* Left: avatar + name + position */}
                  <div className="flex items-start gap-4 min-w-0">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-white font-bold text-sm flex-shrink-0 mt-1">
                      {c.candidate_name[0]}
                    </div>
                    <div className="min-w-0">
                      <p className="font-semibold group-hover:text-blue-600 transition">{c.candidate_name}</p>
                      <p className="text-xs text-gray-400">{c.current_position} · {c.years_of_experience || "?"}年</p>
                      {/* AI judgment — the key evidence */}
                      {c.has_report && c.strengths && c.strengths.length > 0 && (
                        <div className="mt-2 space-y-0.5">
                          {c.strengths.map((s: string, i: number) => (
                            <p key={i} className="text-xs text-green-700 flex items-center gap-1">
                              <span className="text-green-400 text-[10px]">+</span> {s}
                            </p>
                          ))}
                          {c.gaps && c.gaps.map((g: string, i: number) => (
                            <p key={i} className="text-xs text-orange-600 flex items-center gap-1">
                              <span className="text-orange-400 text-[10px]">!</span> {g}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  {/* Right: eval badge + stars + decision */}
                  <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                    {c.has_report ? (
                      <>
                        {c.eval_level && (
                          <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                            c.eval_level.includes("A") ? "bg-green-100 text-green-800"
                            : c.eval_level.includes("B") ? "bg-blue-100 text-blue-800"
                            : "bg-gray-100 text-gray-600"
                          }`}>{c.eval_level}</span>
                        )}
                        <p className="text-yellow-500 text-base leading-none tracking-wide">
                          {"★".repeat(c.star_rating || 0)}
                          <span className="text-gray-300">{"★".repeat(5 - (c.star_rating || 0))}</span>
                        </p>
                      </>
                    ) : (
                      <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">待分析</span>
                    )}
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      c.hr_decision === "suitable" ? "bg-green-50 text-green-700"
                      : c.hr_decision === "maybe" ? "bg-yellow-50 text-yellow-700"
                      : c.hr_decision === "not_suitable" ? "bg-red-50 text-red-700"
                      : "bg-gray-50 text-gray-500"
                    }`}>
                      {c.hr_decision === "suitable" ? "合适" : c.hr_decision === "maybe" ? "待定" : c.hr_decision === "not_suitable" ? "不合适" : "待处理"}
                    </span>
                    <svg className="w-4 h-4 text-gray-300 group-hover:text-blue-400 transition mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                  </div>
                </div>
                {/* Skills bar */}
                <div className="flex flex-wrap gap-1 mt-3 ml-14">
                  {(c.skills || []).slice(0, 5).map((s: string, i: number) => (
                    <span key={i} className="px-2 py-0.5 bg-gray-50 text-gray-500 rounded-full text-xs border border-gray-100">{s}</span>
                  ))}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Compare Tab */}
      {tab === "compare" && (
        <div className="space-y-4">
          {!compareData ? (
            <p className="text-gray-400 py-10 text-center">加载中...</p>
          ) : compareData.candidates.length === 0 ? (
            <p className="text-gray-400 py-10 text-center">暂无候选人</p>
          ) : (
            <>
              <p className="text-sm text-gray-500">横向对比 {compareData.candidates.length} 位候选人的匹配维度，辅助招聘决策</p>

              {/* Radar-style table */}
              <div className="overflow-x-auto bg-white rounded-xl border">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50">
                      <th className="text-left px-4 py-3 font-medium text-gray-500 w-32">候选人</th>
                      {compareData.dimensions.map((dim: string) => (
                        <th key={dim} className="text-center px-3 py-3 font-medium text-gray-500">{dim}</th>
                      ))}
                      <th className="text-center px-3 py-3 font-medium text-gray-500">综合</th>
                      <th className="text-center px-3 py-3 font-medium text-gray-500">决策</th>
                      <th className="w-10"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {compareData.candidates.map((c: any) => (
                      <tr key={c.candidate_id} className="border-b hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div>
                            <p className="font-medium">{c.name}</p>
                            <p className="text-xs text-gray-400">{c.years_of_experience}年</p>
                          </div>
                        </td>
                        {compareData.dimensions.map((dim: string) => {
                          const score = c.dimension_scores[dim] || "mid_low";
                          const colors: Record<string, string> = {
                            high: "bg-green-500", mid_high: "bg-blue-400", mid: "bg-yellow-400",
                            mid_low: "bg-orange-400", low: "bg-red-400", no_match: "bg-gray-300",
                          };
                          const labels: Record<string, string> = {
                            high: "强", mid_high: "较强", mid: "中", mid_low: "较弱", low: "弱", no_match: "无",
                          };
                          return (
                            <td key={dim} className="text-center px-3 py-3">
                              <span className={`inline-block px-2 py-0.5 rounded-full text-xs text-white ${colors[score] || "bg-gray-300"}`}>
                                {labels[score] || score}
                              </span>
                            </td>
                          );
                        })}
                        <td className="text-center px-3 py-3">
                          <span className="text-yellow-500 font-bold">{"★".repeat(c.star_rating || 0)}</span>
                          <span className="text-gray-300">{"★".repeat(5 - (c.star_rating || 0))}</span>
                        </td>
                        <td className="text-center px-3 py-3">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${
                            c.hr_decision === "suitable" ? "bg-green-50 text-green-700"
                            : c.hr_decision === "maybe" ? "bg-yellow-50 text-yellow-700"
                            : c.hr_decision === "not_suitable" ? "bg-red-50 text-red-700"
                            : "bg-gray-50 text-gray-500"
                          }`}>
                            {c.hr_decision === "suitable" ? "合适" : c.hr_decision === "maybe" ? "待定" : c.hr_decision === "not_suitable" ? "不合适" : "待处理"}
                          </span>
                        </td>
                        <td className="px-2 py-3">
                          <Link href={`/candidates/${c.candidate_id}`} className="text-blue-500 text-xs hover:underline">详情</Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Key difference summary */}
              <div className="grid grid-cols-2 gap-4">
                {compareData.candidates.sort((a: any, b: any) => (b.star_rating || 0) - (a.star_rating || 0)).slice(0, 4).map((c: any) => (
                  <div key={c.candidate_id} className="bg-white rounded-lg border p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-sm">{c.name}</span>
                      <span className="text-yellow-500 text-sm">{c.star_rating ? "★".repeat(c.star_rating) : ""}</span>
                    </div>
                    <div className="space-y-1 text-xs">
                      {(c.strengths || []).slice(0, 2).map((s: string, i: number) => (
                        <p key={i} className="text-green-700">+ {s}</p>
                      ))}
                      {(c.gaps || []).slice(0, 2).map((g: string, i: number) => (
                        <p key={i} className="text-orange-700">- {g}</p>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Briefing Modal */}
      {showBriefing && briefingData && (
        <div className="fixed inset-0 bg-black/40 flex items-start justify-center z-50 overflow-y-auto py-10">
          <div className="bg-white rounded-xl p-6 w-full max-w-2xl space-y-4 mx-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold">面试简报 — {briefingData.job_title}</h2>
              <button onClick={() => setShowBriefing(false)} className="text-gray-400 hover:text-gray-600 text-lg">&times;</button>
            </div>

            <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg p-4 text-white">
              <p className="text-sm opacity-80">共收到 {briefingData.total_candidates} 位候选人</p>
              <p className="text-xl font-bold">{briefingData.top_picks.length} 位推荐进入面试</p>
            </div>

            <div className="space-y-3 max-h-[60vh] overflow-y-auto">
              {briefingData.all_candidates.map((c: any, i: number) => (
                <div key={i} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${c.star_rating >= 4 ? "bg-green-500" : c.star_rating >= 3 ? "bg-yellow-500" : "bg-gray-400"}`} />
                      <span className="font-semibold text-sm">{c.name}</span>
                      <span className="text-xs text-gray-400">{c.hr_decision === "suitable" ? "合适" : c.hr_decision === "maybe" ? "待定" : c.hr_decision === "not_suitable" ? "不合适" : "待处理"}</span>
                    </div>
                    <span className="text-yellow-500 text-sm">{"★".repeat(c.star_rating || 0)}</span>
                  </div>
                  <p className="text-xs text-gray-600 mb-1"><span className="text-green-600">优势:</span> {c.key_strength}</p>
                  <p className="text-xs text-gray-600 mb-2"><span className="text-orange-600">关注:</span> {c.key_gap}</p>
                  {c.interview_questions && c.interview_questions.length > 0 && (
                    <div className="bg-purple-50 rounded p-2 text-xs">
                      <p className="font-medium text-purple-700 mb-1">面试要点：</p>
                      {c.interview_questions.map((q: string, qi: number) => (
                        <p key={qi} className="text-purple-800 ml-2">· {q}</p>
                      ))}
                    </div>
                  )}
                  <Link href={`/candidates/${c.candidate_id}`} className="text-blue-500 text-xs mt-2 inline-block hover:underline">查看完整报告</Link>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
