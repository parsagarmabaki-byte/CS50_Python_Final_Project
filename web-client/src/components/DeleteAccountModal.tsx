import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import client from "../api/client";
import { useAuth } from "../auth/AuthProvider";

interface DeleteAccountModalProps {
  onClose: () => void;
}

export default function DeleteAccountModal({ onClose }: DeleteAccountModalProps) {
  const auth = useAuth();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState<string | null>(null);

  const deleteAccount = useMutation({
    mutationFn: async () => {
      await client.delete("/me/account", {
        data: { password, confirmation },
      });
    },
    onSuccess: () => {
      auth.logout();
      navigate("/login");
    },
    onError: (e: any) => {
      setError(e?.response?.data?.detail || e.message || "Failed to delete account");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (confirmation.toUpperCase() !== "DELETE") {
      setError("You must type 'DELETE' to confirm");
      return;
    }
    deleteAccount.mutate();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div className="p-4 border-b flex justify-between items-center">
          <h2 className="text-xl font-semibold text-red-600">Delete Account</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="p-4">
          <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-4">
            <p className="text-red-800 text-sm">
              <strong>Warning:</strong> This action is irreversible. All your data including:
            </p>
            <ul className="text-red-800 text-sm mt-2 ml-4 list-disc">
              <li>Account information</li>
              <li>Watchlist entries</li>
              <li>Stored price history</li>
            </ul>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Enter your password to verify
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
                placeholder="Your password"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Type <strong>DELETE</strong> to confirm
              </label>
              <input
                type="text"
                value={confirmation}
                onChange={(e) => setConfirmation(e.target.value)}
                className="w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
                placeholder="Type DELETE here"
                required
              />
            </div>

            {error && (
              <div className="text-red-600 bg-red-50 p-2 rounded text-sm">{error}</div>
            )}

            <div className="flex gap-2">
              <button
                type="submit"
                className="flex-1 bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition disabled:opacity-50"
                disabled={deleteAccount.isPending}
              >
                {deleteAccount.isPending ? "Deleting..." : "Delete My Account"}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
