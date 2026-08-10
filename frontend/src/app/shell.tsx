"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { AuthProvider, useAuth } from "@/lib/auth";

function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, token, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const isPublic = pathname === "/login" || pathname === "/register" || pathname?.startsWith("/onboarding/");

  useEffect(() => {
    if (!loading && !user && !token && !isPublic) {
      router.replace("/login");
    }
  }, [loading, user, token, isPublic, router]);

  // Don't render protected pages until we know the user is authenticated
  if (!isPublic && loading) return null;
  if (!isPublic && !user && !token) return null;

  return <>{children}</>;
}

function NavBar() {
  const { user, logout, loading } = useAuth();
  const pathname = usePathname();

  if (pathname === "/login" || pathname === "/register") return null;
  if (pathname?.startsWith("/onboarding/")) return null;

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center gap-6">
        <Link href="/" className="font-bold text-lg text-blue-600">AI Recruiting</Link>
        <Link href="/" className="text-sm text-gray-600 hover:text-gray-900">首页</Link>
        <Link href="/create-job" className="text-sm text-gray-600 hover:text-gray-900">创建需求</Link>
        <Link href="/talent-pool" className="text-sm text-gray-600 hover:text-gray-900">人才库</Link>
        <Link href="/employees" className="text-sm text-gray-600 hover:text-gray-900">员工台账</Link>
        <div className="flex-1" />
        <Link href="/company" className="text-sm text-gray-400 hover:text-gray-600">公司设置</Link>
        {loading ? null : user ? (
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-400">{user.company_name}</span>
            <span className="text-xs text-gray-500">{user.name}</span>
            <button onClick={logout} className="text-xs text-gray-400 hover:text-red-500">退出</button>
          </div>
        ) : (
          <Link href="/login" className="text-xs text-blue-600 hover:underline">登录</Link>
        )}
      </div>
    </nav>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <NavBar />
      <AuthGuard>
        <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
      </AuthGuard>
    </AuthProvider>
  );
}
