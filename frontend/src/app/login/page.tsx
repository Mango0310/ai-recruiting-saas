"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.push("/");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "登录失败，请重试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-2xl shadow-sm border p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">AI 招聘助手</h1>
          <p className="text-sm text-gray-500 mt-2">登录你的账号</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{error}</div>
          )}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">邮箱</label>
            <input className="w-full border rounded-lg px-3 py-2.5 text-sm" type="email" placeholder="your@email.com"
              value={email} onChange={e => setEmail(e.target.value)} autoFocus />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">密码</label>
            <input className="w-full border rounded-lg px-3 py-2.5 text-sm" type="password" placeholder="输入密码"
              value={password} onChange={e => setPassword(e.target.value)} />
          </div>
          <button type="submit" disabled={loading}
            className="w-full py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition">
            {loading ? "登录中..." : "登录"}
          </button>
        </form>

        <p className="text-center text-xs text-gray-400 mt-6">
          还没有账号？<Link href="/register" className="text-blue-600 hover:underline">注册</Link>
        </p>
      </div>
    </div>
  );
}
