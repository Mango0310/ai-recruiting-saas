"use client";

const KEY = "ai_recruit_company";

export interface CompanyInfo {
  name: string;
  industry: string;
  size: string;
  business: string;
}

export function getCompanyInfo(): CompanyInfo {
  if (typeof window === "undefined") return { name: "", industry: "", size: "", business: "" };
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : { name: "", industry: "", size: "", business: "" };
  } catch {
    return { name: "", industry: "", size: "", business: "" };
  }
}

export function saveCompanyInfo(info: CompanyInfo) {
  if (typeof window === "undefined") return;
  localStorage.setItem(KEY, JSON.stringify(info));
}

export function hasCompanyInfo(): boolean {
  const c = getCompanyInfo();
  return !!(c.name && c.industry);
}
