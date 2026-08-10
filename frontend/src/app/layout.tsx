import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "./shell";

export const metadata: Metadata = {
  title: "AI Recruiting Assistant",
  description: "AI-powered candidate intelligence system",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="bg-gray-50 text-gray-900 min-h-screen">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
