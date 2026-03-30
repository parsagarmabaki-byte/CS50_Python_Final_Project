import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";

export default function RegisterPage() {
  const auth = useAuth();
  const nav = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      await auth.register(username, password, email || undefined);
      nav("/");
    } catch (e: any) {
      setErr(e?.response?.data?.detail || e.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-white p-6 rounded-lg shadow-md mt-10">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">Register</h2>
      {err && <div className="text-red-600 mb-3 bg-red-50 p-2 rounded">{err}</div>}
      <form onSubmit={submit}>
        <label className="block mb-4">
          <span className="text-gray-700">Username</span>
          <input 
            value={username} 
            onChange={(e) => setUsername(e.target.value)} 
            className="w-full mt-1 border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </label>
        <label className="block mb-4">
          <span className="text-gray-700">Email (optional)</span>
          <input 
            type="email"
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
            className="w-full mt-1 border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </label>
        <label className="block mb-4">
          <span className="text-gray-700">Password</span>
          <input 
            type="password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
            className="w-full mt-1 border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            minLength={3}
            maxLength={24}
            required
          />
        </label>
        <div className="flex gap-2">
          <button 
            type="submit" 
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition disabled:opacity-50"
            disabled={loading}
          >
            {loading ? "..." : "Register"}
          </button>
          <Link 
            to="/login" 
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition"
          >
            Login
          </Link>
        </div>
      </form>
    </div>
  );
}
