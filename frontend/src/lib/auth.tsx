"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import axios from "axios";

axios.defaults.headers.common["ngrok-skip-browser-warning"] = "1";

interface User {
  id: number; email: string; name: string; company_id: number; company_name: string;
}
interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string, company_name: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState>({
  user: null, token: null, loading: true,
  login: async () => {}, register: async () => {}, logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => {
    if (typeof window !== "undefined") return localStorage.getItem("ai_recruit_token");
    return null;
  });
  const [loading, setLoading] = useState(!!token);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    axios.get("/api/auth/me", { headers: { Authorization: `Bearer ${token}` } })
      .then(r => setUser(r.data))
      .catch(() => { localStorage.removeItem("ai_recruit_token"); setToken(null); })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = async (email: string, password: string) => {
    const { data } = await axios.post("/api/auth/login", { email, password });
    localStorage.setItem("ai_recruit_token", data.token);
    setToken(data.token);
    setUser(data.user);
  };

  const register = async (email: string, password: string, name: string, company_name: string) => {
    const { data } = await axios.post("/api/auth/register", { email, password, name, company_name });
    localStorage.setItem("ai_recruit_token", data.token);
    setToken(data.token);
    setUser(data.user);
  };

  const logout = () => {
    localStorage.removeItem("ai_recruit_token");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() { return useContext(AuthContext); }
