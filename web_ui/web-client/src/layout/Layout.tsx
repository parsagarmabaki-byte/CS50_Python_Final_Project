import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";

export default function Layout({ children }: { children: React.ReactNode }) {
  const auth = useAuth();
  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-white shadow">
        <div className="container mx-auto px-4 py-3 flex justify-between items-center">
          <Link to="/" className="font-bold text-lg text-blue-600">MarketWatch</Link>
          <div className="flex items-center space-x-3">
            {auth.user ? (
              <>
                <span className="text-sm text-gray-600 hidden sm:inline">Hello, {auth.user.username}</span>
                <button 
                  className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 transition" 
                  onClick={() => auth.logout()}
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="px-3 py-1 rounded bg-blue-500 text-white hover:bg-blue-600 transition">Login</Link>
                <Link to="/register" className="px-3 py-1 rounded border border-gray-300 hover:bg-gray-50 transition">Register</Link>
              </>
            )}
          </div>
        </div>
      </nav>
      <main className="container mx-auto px-4 py-6 flex-1">
        {children}
      </main>
    </div>
  );
}
