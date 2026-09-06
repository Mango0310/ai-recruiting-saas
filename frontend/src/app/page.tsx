"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getDashboardStats, createJob, getFunnelData } from "@/lib/api";

const stageLabels: Record<string, string> = {
  new: "新入库", parsed: "已解析", ai_screened: "AI筛选",
  hr_reviewed: "HR筛选", interviewing: "面试中", interviewed: "面试完成",
  hired: "已入职",
};

const stageColors: Record<string, string> = {
  new: "bg-gray-300", parsed: "bg-indigo-400",
  ai_screened: "bg-blue-500", hr_reviewed: "bg-yellow-500",
  interviewing: "bg-purple-500", interviewed: "bg-orange-500",
  hired: "bg-green-500",
};

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [funnel, setFunnel] = useState<any>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [title, setTitle] = useState("");
  const [jdText, setJdText] = useState("");
  const [companyBusiness, setCompanyBusiness] = useState("");
  const [creating, setCreating] = useState(false);

  const fetchStats = () => getDashboardStats().then(setStats).catch(console.error);
  const fetchFunnel = () => getFunnelData().then(setFunnel).catch(console.error);

  useEffect(() => { fetchStats(); fetchFunnel(); }, []);
  useEffect(() => {
    const onFocus = () => { fetchStats(); fetchFunnel(); };
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, []);

  const handleCreate = async () => {
    if (!title) return;
    setCreating(true);
    try {
      const jdInput = jdText || `公司业务: ${companyBusiness || "未提供"}\n岗位名称: ${title}`;
      await createJob(title, jdInput);
      setShowCreate(false);
      setTitle("");
      setJdText("");
      setCompanyBusiness("");
      fetchStats();
    } catch {
      alert("创建失败，请重试");
    } finally {
      setCreating(false);
    }
  };

  if (!stats) {
    return null;
  }

  const today = new Date();
  const greeting = today.getHours() < 12 ? "早上好" : today.getHours() < 18 ? "下午好" : "晚上好";
  const dateStr = `${today.getFullYear()}年${today.getMonth() + 1}月${today.getDate()}日`;

  return (
    <div className="space-y-6 pb-8">
      {/* ── Hero Header ── */}
      <div className="bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 rounded-2xl p-8 text-white">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-blue-100 text-sm">{dateStr}</p>
            <h1 className="text-2xl font-bold mt-1">{greeting}，AI 招聘助手</h1>
            <p className="text-blue-100 text-sm mt-2 max-w-md">
              {stats.job_count > 0
                ? `当前 ${stats.job_count} 个岗位进行中，${stats.candidate_count} 位候选人等待评估`
                : "创建第一个招聘岗位，AI 将帮你完成简历解析和匹配分析"}
            </p>
          </div>
          <div className="hidden sm:flex gap-2">
            <button onClick={() => setShowCreate(true)}
              className="px-4 py-2 bg-white/20 text-white rounded-lg text-sm hover:bg-white/30 border border-white/30 transition">
              快速创建
            </button>
            <Link href="/create-job"
              className="px-4 py-2 bg-white text-blue-700 rounded-lg text-sm font-medium hover:bg-blue-50 transition">
              + 智能创建
            </Link>
          </div>
        </div>

        {/* Quick stats row inside hero */}
        <div className="grid grid-cols-4 gap-4 mt-6">
          {[
            { label: "招聘岗位", value: stats.job_count, action: () => document.getElementById("jobs")?.scrollIntoView({behavior:"smooth"}) },
            { label: "候选人", value: stats.candidate_count, href: "/talent-pool" },
            { label: "待决策", value: stats.pending_count, action: () => document.getElementById("jobs")?.scrollIntoView({behavior:"smooth"}) },
            { label: "面试中", value: stats.interviewing_count || 0, href: "/talent-pool" },
          ].map(s => {
            if ("href" in s && s.href) {
              return <Link key={s.label} href={s.href as string} className="bg-white/15 rounded-xl p-3 backdrop-blur-sm hover:bg-white/25 transition cursor-pointer block">
                <p className="text-2xl font-bold text-white">{s.value}</p>
                <p className="text-blue-100 text-xs mt-0.5">{s.label}</p>
              </Link>;
            }
            return <button key={s.label} onClick={(s as any).action} className="bg-white/15 rounded-xl p-3 backdrop-blur-sm hover:bg-white/25 transition cursor-pointer block text-left w-full">
              <p className="text-2xl font-bold text-white">{s.value}</p>
              <p className="text-blue-100 text-xs mt-0.5">{s.label}</p>
            </button>;
          })}
        </div>

        {/* Pipeline bar */}
        {stats.pipeline_stages && (
          <div className="mt-5 bg-white/10 rounded-xl p-4">
            <p className="text-blue-100 text-xs mb-3">候选人管道</p>
            <div className="flex rounded-full overflow-hidden h-3">
              {Object.entries(stageLabels).map(([key, label]) => {
                const count = stats.pipeline_stages[key] || 0;
                const total = stats.candidate_count || 1;
                const pct = Math.max(count / total * 100, count > 0 ? 3 : 0);
                return count > 0 ? (
                  <div key={key}
                    className={`${stageColors[key]} transition-all`}
                    style={{ width: `${pct}%` }}
                    title={`${label}: ${count}`}
                  />
                ) : null;
              })}
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2">
              {Object.entries(stageLabels).map(([key, label]) => {
                const count = stats.pipeline_stages[key] || 0;
                return (
                  <span key={key} className="text-xs text-blue-100">
                    <span className={`inline-block w-2 h-2 rounded-full mr-1 ${stageColors[key]}`} />
                    {label} {count}
                  </span>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* ── Mobile create buttons ── */}
      <div className="sm:hidden flex gap-2">
        <button onClick={() => setShowCreate(true)}
          className="flex-1 py-2.5 border border-gray-300 text-gray-700 rounded-xl text-sm hover:bg-gray-50">
          快速创建
        </button>
        <Link href="/create-job"
          className="flex-1 py-2.5 bg-blue-600 text-white rounded-xl text-sm text-center font-medium hover:bg-blue-700">
          + 智能创建
        </Link>
      </div>

      {/* ── Alert bar ── */}
      {stats.urgent_alerts > 0 && (
        <Link href="/employees?alert=pending"
          className="flex items-center gap-3 bg-red-50 border border-red-200 rounded-xl px-5 py-3 hover:bg-red-100 transition">
          <span className="w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center text-sm font-bold">!</span>
          <div>
            <p className="text-red-800 text-sm font-medium">转正预警：{stats.urgent_alerts} 位员工需要关注</p>
            <p className="text-red-500 text-xs">试用期即将到期或已逾期，点击查看详情 →</p>
          </div>
        </Link>
      )}

      {/* ── Recruitment Funnel ── */}
      {funnel && funnel.total_candidates > 0 && (
        <div className="bg-white rounded-2xl border p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-semibold text-gray-800">招聘漏斗</h2>
            <div className="flex items-center gap-4 text-xs text-gray-400">
              <span>总计 {funnel.total_candidates} 候选人</span>
              {funnel.avg_time_to_hire_days && <span>· 平均录用周期 {funnel.avg_time_to_hire_days} 天</span>}
            </div>
          </div>

          {/* Funnel bars */}
          <div className="space-y-2">
            {funnel.funnel?.map((stage: any, i: number) => {
              const maxW = funnel.funnel[0]?.count || 1;
              const w = Math.max((stage.count / maxW) * 100, 3);
              const colors = ["bg-blue-600","bg-indigo-500","bg-blue-400","bg-yellow-500","bg-purple-500","bg-orange-500","bg-green-500"];
              return (
                <div key={i} className="flex items-center gap-3">
                  <span className="w-16 text-xs text-gray-500 text-right">{stage.label}</span>
                  <div className="flex-1 flex items-center gap-3">
                    <div className="flex-1 bg-gray-100 rounded-full h-7 overflow-hidden">
                      <div className={`h-full rounded-full ${colors[i]||"bg-gray-400"} flex items-center justify-end pr-3 transition-all duration-700`}
                        style={{ width: `${w}%`, minWidth: stage.count > 0 ? "40px" : "0" }}>
                        {stage.count > 0 && <span className="text-white text-xs font-bold">{stage.count}</span>}
                      </div>
                    </div>
                    <span className="w-12 text-xs text-gray-400 text-right">
                      {stage.conversion != null ? `${stage.conversion}%` : "—"}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Drop-off highlights */}
          {funnel.dropoffs?.length > 0 && (
            <div className="mt-4 grid grid-cols-3 gap-3">
              {funnel.dropoffs.slice(0, 3).map((d: any, i: number) => (
                <div key={i} className="bg-red-50 rounded-lg p-3 text-center">
                  <p className="text-xs text-red-400">{d.from} → {d.to}</p>
                  <p className="text-lg font-bold text-red-600">-{d.lost} 人</p>
                  <p className="text-xs text-red-400">流失率 {d.loss_rate}%</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Two column: Jobs + Candidates ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Jobs */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 id="jobs" className="font-semibold text-gray-800">进行中的岗位</h2>
            <Link href="/create-job" className="text-xs text-blue-600 hover:underline">+ 新建</Link>
          </div>

          {(!stats.recent_jobs || stats.recent_jobs.length === 0) && (
            <div className="bg-white rounded-xl border border-dashed border-gray-300 p-10 text-center">
              <p className="text-gray-400 mb-3">还没有招聘岗位</p>
              <button onClick={() => setShowCreate(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
                创建第一个岗位
              </button>
            </div>
          )}

          <div className="space-y-3">
            {stats.recent_jobs?.map((job: any) => {
              const totalApps = job.candidate_count || 0;
              const screening = (job.screening_count || 0) + (job.new_count || 0);
              const interviewing = job.interviewing_count || 0;
              return (
                <Link key={job.id} href={`/jobs/${job.id}`}
                  className="block bg-white rounded-xl border border-gray-200 p-4 hover:border-blue-300 hover:shadow-sm transition group">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-900 group-hover:text-blue-600 truncate">{job.title}</h3>
                      <div className="flex items-center gap-3 mt-1.5">
                        <span className="text-xs text-gray-400">共 {totalApps} 候选人</span>
                        {job.top_star > 0 && (
                          <span className="text-yellow-500 text-xs">{"★".repeat(job.top_star)} 最高匹配</span>
                        )}
                      </div>
                    </div>
                    <span className="text-xs text-gray-400 ml-3 whitespace-nowrap">{job.created_at?.slice(0, 10)}</span>
                  </div>

                  {/* Mini progress bar */}
                  {totalApps > 0 && (
                    <div className="mt-3 flex gap-1 h-1.5 rounded-full overflow-hidden">
                      {screening > 0 && (
                        <div className="bg-blue-400" style={{ width: `${(screening / totalApps) * 100}%` }} title={`${screening} 筛选中`} />
                      )}
                      {interviewing > 0 && (
                        <div className="bg-purple-400" style={{ width: `${(interviewing / totalApps) * 100}%` }} title={`${interviewing} 面试中`} />
                      )}
                    </div>
                  )}
                </Link>
              );
            })}
          </div>
        </div>

        {/* Recent Candidates */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-gray-800">最近候选人</h2>
            <Link href="/talent-pool" className="text-xs text-blue-600 hover:underline">人才库 →</Link>
          </div>

          {(!stats.recent_candidates || stats.recent_candidates.length === 0) && (
            <div className="bg-white rounded-xl border border-dashed border-gray-300 p-10 text-center">
              <p className="text-gray-400 mb-1">暂无候选人</p>
              <p className="text-gray-400 text-xs">上传简历后将自动出现在这里</p>
            </div>
          )}

          <div className="space-y-3">
            {stats.recent_candidates?.map((c: any) => (
              <Link key={c.id} href={`/candidates/${c.id}`}
                className="block bg-white rounded-xl border border-gray-200 p-4 hover:border-blue-300 hover:shadow-sm transition group">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-700 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                        {c.name?.charAt(0)}
                      </span>
                      <div className="min-w-0">
                        <h3 className="font-medium text-sm text-gray-900 truncate">{c.name}</h3>
                        <p className="text-xs text-gray-500 truncate mt-0.5">
                          {[c.current_position, c.current_company].filter(Boolean).join(" @ ") || "未知职位"}
                        </p>
                      </div>
                    </div>
                    {c.job_title && (
                      <p className="text-xs text-gray-400 mt-1.5 ml-10">投递: {c.job_title}</p>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-1 ml-3 flex-shrink-0">
                    {c.star_rating && (
                      <span className="text-yellow-500 text-xs tracking-wide">
                        {"★".repeat(c.star_rating)}
                        <span className="text-gray-200">{"★".repeat(5 - c.star_rating)}</span>
                      </span>
                    )}
                    <span className="text-xs text-gray-400">{c.created_at?.slice(0, 10)}</span>
                  </div>
                </div>

                {/* Skills chips */}
                {c.skills && c.skills.length > 0 && (
                  <div className="flex flex-wrap gap-1 ml-10 mt-2">
                    {c.skills.slice(0, 4).map((s: string, i: number) => (
                      <span key={i} className="px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded text-xs">{s}</span>
                    ))}
                    {c.skills.length > 4 && (
                      <span className="text-xs text-gray-400 py-0.5">+{c.skills.length - 4}</span>
                    )}
                  </div>
                )}

                {c.conclusion && (
                  <p className="text-xs text-gray-400 mt-1 ml-10 truncate">{c.conclusion}</p>
                )}
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* ── Quick links ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: "员工台账", desc: `${stats.total_employees || 0} 人在职`, href: "/employees", icon: "👥" },
          { label: "人才库", desc: `${stats.talent_pool_count || 0} 位候选人`, href: "/talent-pool", icon: "📋" },
          { label: "公司设置", desc: "Webhook 通知", href: "/company", icon: "⚙" },
          { label: "智能创建", desc: "AI 辅助招聘", href: "/create-job", icon: "✨" },
        ].map(item => (
          <Link key={item.label} href={item.href}
            className="bg-white rounded-xl border border-gray-200 p-4 hover:border-blue-300 hover:shadow-sm transition group">
            <p className="text-lg">{item.icon}</p>
            <p className="font-medium text-sm text-gray-800 mt-1 group-hover:text-blue-600">{item.label}</p>
            <p className="text-xs text-gray-400 mt-0.5">{item.desc}</p>
          </Link>
        ))}
      </div>

      {/* ── Quick create modal ── */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setShowCreate(false)}>
          <div className="bg-white rounded-xl p-6 w-full max-w-lg mx-4 space-y-4" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">快速创建岗位</h3>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600 text-lg">&times;</button>
            </div>
            <p className="text-xs text-gray-400">
              输入岗位名称和 JD，AI 自动分析生成岗位画像。
              如需更精准的画像，推荐使用<Link href="/create-job" className="text-blue-600 underline">智能创建</Link>（含 AI 追问）。
            </p>
            <input
              className="w-full border rounded-lg px-3 py-2 text-sm"
              placeholder="岗位名称，如：高级后端工程师"
              value={title} onChange={e => setTitle(e.target.value)}
              autoFocus
            />
            <textarea
              className="w-full border rounded-lg px-3 py-2 text-sm h-20"
              placeholder="公司业务（可选，帮助 AI 理解招聘场景）&#10;如：一家跨境电商 SaaS 公司，主做东南亚市场"
              value={companyBusiness} onChange={e => setCompanyBusiness(e.target.value)}
            />
            <textarea
              className="w-full border rounded-lg px-3 py-2 text-sm h-40"
              placeholder="粘贴 JD 文本（可选，不填则根据岗位名自动推断）..."
              value={jdText} onChange={e => setJdText(e.target.value)}
            />
            <div className="flex gap-2 justify-end pt-1">
              <button onClick={() => setShowCreate(false)}
                className="px-4 py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-lg">取消</button>
              <button onClick={handleCreate} disabled={creating || !title}
                className="px-5 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition">
                {creating ? "AI 分析中..." : "AI 分析并创建"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
