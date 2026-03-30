import React, { createContext, useContext, useState, useEffect } from "react";
import client from "../api/client";

type User = { username: string } | null;

type AuthContextType = {
  user: User;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, email?: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User>(() => {
    const username = localStorage.getItem("fp_user");
    return username ? { username } : null;
  });

  useEffect(() => {
    // Could verify token with backend on mount if needed
  }, []);

  const login = async (username: string, password: string) => {
    const resp = await client.post("/login", { username, password });
    const token = resp.data.token;
    localStorage.setItem("fp_token", token);
    localStorage.setItem("fp_user", username);
    setUser({ username });
  };

  const register = async (username: string, password: string, email?: string) => {
    await client.post("/register", { username, password, email });
    // Auto-login after register
    await login(username, password);
  };

  const logout = () => {
    localStorage.removeItem("fp_token");
    localStorage.removeItem("fp_user");
    setUser(null);
  };

  return <AuthContext.Provider value={{ user, login, register, logout }}>{children}</AuthContext.Provider>;
};
