"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [form, setForm] = useState({ email: "", password: "", name: "", company_name: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.email || !form.password || !form.name) {
      setError("请填写必填字段"); return;
    }
    if (form.password.length < 4) {
      setError("密码至少4位"); return;
    }
    setError("");
    setLoading(true);
    try {
      await register(form.email, form.password, form.name, form.company_name);
      router.push("/");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "注册失败，请重试");
    } finally {
      setLoading(false);
    }
  };

  const update = (key: string, v: string) => setForm({ ...form, [key]: v });

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-2xl shadow-sm border p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">创建账号</h1>
          <p className="text-sm text-gray-500 mt-2">注册后即可使用 AI 招聘助手</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{error}</div>
          )}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">姓名 *</label>
            <input className="w-full border rounded-lg px-3 py-2.5 text-sm" placeholder="你的名字"
              value={form.name} onChange={e => update("name", e.target.value)} autoFocus />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">邮箱 *</label>
            <input className="w-full border rounded-lg px-3 py-2.5 text-sm" type="email" placeholder="your@email.com"
              value={form.email} onChange={e => update("email", e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">密码 *（至少4位）</label>
            <input className="w-full border rounded-lg px-3 py-2.5 text-sm" type="password" placeholder="设置密码"
              value={form.password} onChange={e => update("password", e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">公司名称</label>
            <input className="w-full border rounded-lg px-3 py-2.5 text-sm" placeholder="你的公司（同公司HR数据共享）"
              value={form.company_name} onChange={e => update("company_name", e.target.value)} />
            <p className="text-xs text-gray-400 mt-1">同公司的HR用同一个公司名注册，即可共享岗位数据</p>
          </div>
          <button type="submit" disabled={loading}
            className="w-full py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition">
            {loading ? "注册中..." : "注册"}
          </button>
        </form>

        <p className="text-center text-xs text-gray-400 mt-6">
          已有账号？<Link href="/login" className="text-blue-600 hover:underline">登录</Link>
        </p>
      </div>
    </div>
  );
}
