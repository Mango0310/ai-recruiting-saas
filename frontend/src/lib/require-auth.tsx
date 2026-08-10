"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export function useRequireAuth() {
  const router = useRouter();
  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("ai_recruit_token");
    if (!token) {
      router.replace("/login");
    }
  }, [router]);
}
