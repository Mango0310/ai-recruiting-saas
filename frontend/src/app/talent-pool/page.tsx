"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { searchTalentPool, semanticSearch } from "@/lib/api";

const decisionLabel: Record<string, string> = {
  pending: "待处理", suitable: "合适", maybe: "待定", not_suitable: "不合适",
};
const decisionColor: Record<string, string> = {
  pending: "bg-gray-50 text-gray-600",
  suitable: "bg-green-50 text-green-700",
  maybe: "bg-yellow-50 text-yellow-700",
  not_suitable: "bg-red-50 text-red-700",
};

function TalentPoolInner() {
  const searchParams = useSearchParams();
  const initialStatus = searchParams.get("status") || "";
  const initialType = searchParams.get("type") || "";

  const [candidates, setCandidates] = useState<any[]>([]);
  const [q, setQ] = useState("");
  const [skill, setSkill] = useState("");
  const [status, setStatus] = useState(initialStatus);
  const [talentType, setTalentType] = useState(initialType);
  const [loading, setLoading] = useState(false);
  const [searchMode, setSearchMode] = useState<"keyword" | "semantic">("keyword");
  const [semanticResults, setSemanticResults] = useState<any[]>([]);

  const search = async () => {
    setLoading(true);
    try {
      if (searchMode === "semantic" && q.trim()) {
        const data = await semanticSearch(q.trim());
        setSemanticResults(data.results || []);
        setCandidates([]);
      } else {
        const data = await searchTalentPool(q || undefined, skill || undefined, status || undefined, talentType || undefined);
        setCandidates(data);
        setSemanticResults([]);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { search(); }, [status, talentType]);
  useEffect(() => {
    const onFocus = () => search();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [status, talentType]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">
          {talentType === "hired" ? "入职员工库" : "人才库"}
        </h1>
        {/* Type tabs */}
        <div className="flex bg-gray-100 rounded-lg p-0.5">
          {[
            { key: "", label: "全部候选人" },
            { key: "hired", label: "入职员工" },
          ].map(t => (
            <Link
              key={t.key}
              href={`/talent-pool${t.key ? `?type=${t.key}` : ""}`}
              onClick={() => setTalentType(t.key)}
              className={`px-3 py-1.5 text-xs rounded-md transition ${
                talentType === t.key ? "bg-white text-gray-900 shadow-sm font-medium" : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {t.label}
            </Link>
          ))}
        </div>
      </div>

      <div className="flex gap-2 flex-wrap">
        <div className="flex-1 min-w-[200px] flex gap-0">
          <input
            className="flex-1 border rounded-l-lg px-3 py-2 text-sm"
            placeholder={searchMode === "semantic" ? "描述你想找的候选人，如：有微服务架构经验的Go后端..." : "搜索姓名、技能、公司..."}
            value={q} onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && search()}
          />
          <select
            className="border-y border-r rounded-r-lg px-2 py-2 text-xs bg-gray-50 text-gray-500"
            value={searchMode}
            onChange={(e) => { setSearchMode(e.target.value as "keyword" | "semantic"); setSemanticResults([]); }}
          >
            <option value="keyword">关键词</option>
            <option value="semantic">语义</option>
          </select>
        </div>
        <input
          className="w-32 border rounded-lg px-3 py-2 text-sm"
          placeholder="技能标签"
          value={skill} onChange={(e) => setSkill(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
        />
        {talentType !== "hired" && (
          <select value={status} onChange={(e) => setStatus(e.target.value)} className="border rounded-lg px-3 py-2 text-sm text-gray-600">
            <option value="">全部状态</option>
            <option value="pending">待处理</option>
            <option value="suitable">合适</option>
            <option value="maybe">待定</option>
            <option value="not_suitable">不合适</option>
          </select>
        )}
        <button onClick={search} disabled={loading} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
          搜索
        </button>
      </div>

      {loading && <p className="text-gray-400 text-center py-10">搜索中...</p>}

      {/* Semantic results */}
      {semanticResults.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-gray-400">语义搜索结果（{semanticResults.length} 个），按相关度排序</p>
          {semanticResults.map((c: any) => (
            <Link key={c.id} href={`/candidates/${c.id}`}
              className="block bg-white rounded-lg border p-4 hover:border-blue-300 hover:shadow-sm transition">
              <div className="flex justify-between items-center flex-wrap gap-2">
                <div>
                  <span className="font-medium">{c.name}</span>
                  <span className="text-sm text-gray-500 ml-3">{c.current_position} @ {c.current_company}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 font-medium">
                    相关度 {(c.score * 100).toFixed(0)}%
                  </span>
                  <span className="text-xs text-gray-400">{c.years_of_experience || 0}年经验</span>
                </div>
              </div>
              <div className="flex flex-wrap gap-1 mt-2">
                {(c.skills || []).slice(0, 8).map((s: string, i: number) => (
                  <span key={i} className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">{s}</span>
                ))}
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Keyword results */}
      {semanticResults.length === 0 && (
        <div className="space-y-2">
          {!loading && candidates.length === 0 && (
            <p className="text-gray-400 py-10 text-center">
              {talentType === "hired" ? "暂无入职员工" : "暂无候选人"}
            </p>
          )}
          {candidates.map((c: any) => (
            <Link key={c.id} href={`/candidates/${c.id}`}
              className="block bg-white rounded-lg border p-4 hover:border-blue-300 transition">
              <div className="flex justify-between items-center flex-wrap gap-2">
                <div>
                  <span className="font-medium">{c.name}</span>
                  <span className="text-sm text-gray-500 ml-3">{c.current_position} @ {c.current_company}</span>
                </div>
                <div className="flex items-center gap-3">
                  {c.star_rating && (
                    <span className="text-yellow-500 text-sm tracking-wide">
                      {"★".repeat(c.star_rating)}<span className="text-gray-300">{"★".repeat(5 - c.star_rating)}</span>
                    </span>
                  )}
                  {talentType === "hired" ? (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-700">已入职</span>
                  ) : (
                    <span className={`text-xs px-2 py-0.5 rounded-full ${decisionColor[c.hr_decision] || decisionColor.pending}`}>
                      {decisionLabel[c.hr_decision] || "待处理"}
                    </span>
                  )}
                  <span className="text-xs text-gray-400">{c.latest_job}</span>
                </div>
              </div>
              <div className="flex flex-wrap gap-1 mt-2">
                {(c.skills || []).slice(0, 8).map((s: string, i: number) => (
                  <span key={i} className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">{s}</span>
                ))}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export default function TalentPoolPage() {
  return (
    <Suspense fallback={<div className="py-20 text-center text-gray-500">加载中...</div>}>
      <TalentPoolInner />
    </Suspense>
  );
}
