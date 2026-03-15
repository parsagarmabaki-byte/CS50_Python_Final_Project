import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import client from "../api/client";
import HistoricalPricesModal from "../components/HistoricalPricesModal";
import DeleteAccountModal from "../components/DeleteAccountModal";

type WatchEntry = { symbol: string };
type Price = { symbol: string; price: number; date: string; source: string };

function fetchWatchlist() {
  return client.get<WatchEntry[]>("/me/watchlist").then(r => r.data);
}

function fetchPrices() {
  return client.get<Price[]>("/me/prices").then(r => r.data);
}

export default function Dashboard() {
  const qc = useQueryClient();
  const [base, setBase] = useState("");
  const [quote, setQuote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const watchQ = useQuery({ queryKey: ["watchlist"], queryFn: fetchWatchlist });
  const pricesQ = useQuery({ queryKey: ["prices"], queryFn: fetchPrices });

  const addSym = useMutation({
    mutationFn: (payload: { base: string; quote: string }) => 
      client.post("/me/watchlist", payload).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["watchlist"] });
      qc.invalidateQueries({ queryKey: ["prices"] });
      setBase("");
      setQuote("");
    },
    onError: (e: any) => setError(e?.response?.data?.detail || e.message),
  });

  const updatePrices = useMutation({
    mutationFn: () => client.post("/me/prices/update").then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["prices"] }),
  });

  const exportCsv = async () => {
    const resp = await client.get("/me/prices/export", { responseType: "blob" });
    const url = window.URL.createObjectURL(resp.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = "prices.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  };

  const removeSymbol = async (symbol: string) => {
    await client.delete(`/me/watchlist/${encodeURIComponent(symbol)}`);
    qc.invalidateQueries({ queryKey: ["watchlist"] });
    qc.invalidateQueries({ queryKey: ["prices"] });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-semibold text-gray-800">Dashboard</h1>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => updatePrices.mutate()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition disabled:opacity-50"
            disabled={updatePrices.isPending}
          >
            {updatePrices.isPending ? "Updating..." : "Update Prices"}
          </button>
          <button
            onClick={exportCsv}
            className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition"
          >
            Export CSV
          </button>
          <button
            onClick={() => setShowDeleteModal(true)}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition"
          >
            Delete Account
          </button>
        </div>
      </div>

      <section className="bg-white p-4 rounded-lg shadow">
        <h2 className="font-medium mb-3 text-gray-700">Add Symbol</h2>
        {error && <div className="text-red-600 mb-2 bg-red-50 p-2 rounded">{error}</div>}
        <div className="flex flex-col sm:flex-row gap-2">
          <input 
            placeholder="Base (e.g., USD)" 
            value={base} 
            onChange={(e) => setBase(e.target.value.toUpperCase())} 
            className="border rounded-md px-3 py-2 w-full sm:w-auto focus:outline-none focus:ring-2 focus:ring-blue-500"
            maxLength={3}
          />
          <input 
            placeholder="Quote (e.g., SEK)" 
            value={quote} 
            onChange={(e) => setQuote(e.target.value.toUpperCase())} 
            className="border rounded-md px-3 py-2 w-full sm:w-auto focus:outline-none focus:ring-2 focus:ring-blue-500"
            maxLength={3}
          />
          <button 
            onClick={() => addSym.mutate({ base, quote })} 
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition disabled:opacity-50"
            disabled={addSym.isPending || !base || !quote}
          >
            {addSym.isPending ? "Adding..." : "Add"}
          </button>
        </div>
      </section>

      <section className="bg-white p-4 rounded-lg shadow">
        <h2 className="font-medium mb-3 text-gray-700">Watchlist</h2>
        {watchQ.isLoading ? (
          <div className="text-gray-500">Loading...</div>
        ) : watchQ.data && watchQ.data.length > 0 ? (
          <ul className="divide-y">
            {watchQ.data.map(w => (
              <li key={w.symbol} className="py-2 flex justify-between items-center gap-2">
                <span className="font-mono text-gray-800 flex-1">{w.symbol}</span>
                <div className="flex gap-1">
                  <button
                    className="text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-2 py-1 rounded transition text-sm"
                    onClick={() => setSelectedSymbol(w.symbol)}
                    title="View historical prices"
                  >
                    📈 History
                  </button>
                  <button
                    className="text-red-600 hover:text-red-800 hover:bg-red-50 px-2 py-1 rounded transition text-sm"
                    onClick={() => removeSymbol(w.symbol)}
                    title="Remove from watchlist"
                  >
                    Remove
                  </button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500">No symbols in watchlist. Add one above.</p>
        )}
      </section>

      <section className="bg-white p-4 rounded-lg shadow">
        <h2 className="font-medium mb-3 text-gray-700">Latest Prices</h2>
        {pricesQ.isLoading ? (
          <div className="text-gray-500">Loading...</div>
        ) : pricesQ.data && pricesQ.data.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b">
                  <th className="py-2 text-gray-600 font-medium">Symbol</th>
                  <th className="py-2 text-gray-600 font-medium">Price</th>
                  <th className="py-2 text-gray-600 font-medium">Date</th>
                  <th className="py-2 text-gray-600 font-medium">Source</th>
                </tr>
              </thead>
              <tbody>
                {pricesQ.data.map(p => (
                  <tr key={p.symbol} className="border-b last:border-0">
                    <td className="py-2 font-mono text-gray-800">{p.symbol}</td>
                    <td className="py-2 text-gray-700">{p.price.toFixed(4)}</td>
                    <td className="py-2 text-gray-600">{p.date}</td>
                    <td className="py-2 text-gray-600">{p.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500">No price data available. Add symbols and update prices.</p>
        )}
      </section>

      {selectedSymbol && (
        <HistoricalPricesModal
          symbol={selectedSymbol}
          onClose={() => setSelectedSymbol(null)}
        />
      )}

      {showDeleteModal && (
        <DeleteAccountModal
          onClose={() => setShowDeleteModal(false)}
        />
      )}
    </div>
  );
}
