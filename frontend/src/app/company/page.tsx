"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCompanyInfo, saveCompanyInfo, type CompanyInfo } from "@/lib/company";
import { getCompany, updateCompany, uploadKnowledge, deleteKnowledge } from "@/lib/api";
import axios from "axios";

const API = "/api";

export default function CompanySettings() {
  const router = useRouter();
  const [info, setInfo] = useState<CompanyInfo>({ name: "", industry: "", size: "", business: "" });
  const [saved, setSaved] = useState(false);
  const [knowledgeText, setKnowledgeText] = useState("");
  const [knowledgeDocs, setKnowledgeDocs] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [webhookTesting, setWebhookTesting] = useState(false);
  const [webhookResult, setWebhookResult] = useState("");

  useEffect(() => {
    setInfo(getCompanyInfo());
    getCompany().then(c => {
      setKnowledgeDocs(c.knowledge_docs || []);
      setKnowledgeText(c.knowledge_text || "");
    }).catch(() => {});
  }, []);

  const handleSave = async () => {
    saveCompanyInfo(info);
    try {
      await updateCompany({ name: info.name, industry: info.industry, size: info.size, knowledge_text: knowledgeText });
    } catch {}
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setUploading(true);
    try {
      const doc = await uploadKnowledge(f);
      setKnowledgeDocs(prev => [...prev, doc]);
    } catch { alert("上传失败，仅支持 PDF/TXT/MD，不超过10MB"); }
    finally { setUploading(false); }
  };

  const handleDelete = async (docId: string) => {
    if (!confirm("确认删除这份资料？")) return;
    try {
      await deleteKnowledge(docId);
      setKnowledgeDocs(prev => prev.filter(d => d.id !== docId));
    } catch { alert("删除失败"); }
  };

  const handleTestWebhook = async () => {
    setWebhookTesting(true);
    setWebhookResult("");
    try {
      const { data } = await axios.post(`${API}/notify/test`);
      setWebhookResult(data.ok ? "通知发送成功！请检查飞书/企微" : data.message || "发送失败");
    } catch { setWebhookResult("测试失败，检查后端是否运行"); }
    finally { setWebhookTesting(false); }
  };

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <h1 className="text-xl font-bold">公司设置</h1>
      <p className="text-sm text-gray-500">设置一次公司信息，创建岗位和AI分析时自动参考。</p>

      {/* Basic Info */}
      <div className="bg-white rounded-xl border p-6 space-y-4">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">公司名称</label>
          <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="XX科技有限公司"
            value={info.name} onChange={e => setInfo({...info, name: e.target.value})} />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">行业</label>
          <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="跨境电商SaaS / 游戏 / 医疗AI..."
            value={info.industry} onChange={e => setInfo({...info, industry: e.target.value})} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">公司规模</label>
            <select className="w-full border rounded-lg px-3 py-2 text-sm" value={info.size} onChange={e => setInfo({...info, size: e.target.value})}>
              <option value="">请选择</option>
              <option value="1-20人">1-20人</option><option value="20-99人">20-99人</option>
              <option value="100-299人">100-299人</option><option value="300-1000人">300-1000人</option><option value="1000+">1000人以上</option>
            </select>
          </div>
        </div>
        <div className="flex gap-2 justify-between pt-2">
          <button onClick={() => router.back()} className="px-4 py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-lg">返回</button>
          <button onClick={handleSave} className="px-6 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            {saved ? "✓ 已保存" : "保存设置"}
          </button>
        </div>
      </div>

      {/* Knowledge Base */}
      <div className="bg-white rounded-xl border p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-800">企业知识库</h3>
          <span className="text-xs text-gray-400">AI 在生成岗位画像和面试题时自动参考</span>
        </div>

        {/* Knowledge Text */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">公司介绍 / 产品 / 价值观</label>
          <textarea className="w-full border rounded-lg px-3 py-2 text-sm h-28" placeholder={"描述公司做什么、服务谁、核心产品是什么、公司文化和价值观...\n\n例如：\n我们是一家跨境电商SaaS公司，主做东南亚市场，核心产品是智能选品和广告投放工具。公司文化强调数据驱动和快速迭代。技术栈以Go+React为主，团队扁平化。"}
            value={knowledgeText} onChange={e => setKnowledgeText(e.target.value)} />
          <p className="text-xs text-gray-400 mt-1">AI 将在生成岗位画像、匹配分析、面试题时参考这些信息</p>
        </div>

        {/* Upload */}
        <div className="border-t pt-4">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-medium text-gray-500">上传资料（PDF / TXT / MD，单文件不超过10MB）</p>
            <label className={`px-3 py-1.5 text-xs rounded-lg cursor-pointer transition ${uploading ? "bg-gray-100 text-gray-400" : "bg-blue-600 text-white hover:bg-blue-700"}`}>
              {uploading ? "上传中..." : "+ 上传文件"}
              <input type="file" accept=".pdf,.txt,.md" className="hidden" onChange={handleUpload} disabled={uploading} />
            </label>
          </div>

          {knowledgeDocs.length === 0 && <p className="text-xs text-gray-400 text-center py-4">暂无资料。上传产品文档、公司介绍等，AI 将自动参考。</p>}

          {knowledgeDocs.map(doc => (
            <div key={doc.id} className="flex items-center justify-between bg-gray-50 rounded-lg p-3 mb-2">
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-xs">📄</span>
                <div className="min-w-0">
                  <p className="text-xs font-medium text-gray-700 truncate">{doc.name}</p>
                  <p className="text-xs text-gray-400">{new Date(doc.uploaded_at).toLocaleDateString("zh-CN")} · {doc.size ? `${(doc.size/1024).toFixed(0)}KB` : ""}</p>
                </div>
              </div>
              <button onClick={() => handleDelete(doc.id)} className="text-xs text-red-400 hover:text-red-600 ml-3">删除</button>
            </div>
          ))}
        </div>

        <button onClick={handleSave} className="w-full py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          {saved ? "✓ 已保存" : "保存知识库"}
        </button>
      </div>

      {/* Webhook */}
      <div className="bg-white rounded-xl border p-6 space-y-4">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">通知设置 (Webhook)</h3>
        <p className="text-xs text-gray-500">配置飞书/企微 Webhook 后，系统自动发送新候选人、入职、转正预警等通知</p>
        <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-600 font-mono break-all">
          在 backend\.env 中设置 WEBHOOK_URL 和 WEBHOOK_TYPE<br />WEBHOOK_TYPE: feishu / wecom / custom
        </div>
        <div className="flex items-center gap-3">
          <button onClick={handleTestWebhook} disabled={webhookTesting} className="px-4 py-2 text-sm border border-blue-200 text-blue-600 rounded-lg hover:bg-blue-50 disabled:opacity-50">
            {webhookTesting ? "发送中..." : "发送测试通知"}
          </button>
          {webhookResult && <span className={`text-xs ${webhookResult.includes("成功") ? "text-green-600" : "text-gray-500"}`}>{webhookResult}</span>}
        </div>
      </div>
    </div>
  );
}
