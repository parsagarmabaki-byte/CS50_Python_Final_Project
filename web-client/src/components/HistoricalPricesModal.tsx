import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import client from "../api/client";

interface HistoricalPricesModalProps {
  symbol: string;
  onClose: () => void;
}

interface HistoricalPrice {
  date: string;
  price: number;
}

export default function HistoricalPricesModal({ symbol, onClose }: HistoricalPricesModalProps) {
  // Parse symbol FX:USDSEK -> base=USD, quote=SEK
  const parts = symbol.replace("FX:", "").match(/([A-Z]{3})([A-Z]{3})/);
  const base = parts?.[1] || "";
  const quote = parts?.[2] || "";

  const [startDate, setStartDate] = useState(() => {
    // Default to 7 days ago
    const date = new Date();
    date.setDate(date.getDate() - 7);
    return date.toISOString().split("T")[0];
  });
  const [endDate, setEndDate] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [prices, setPrices] = useState<HistoricalPrice[] | null>(null);

  const fetchHistorical = useMutation({
    mutationFn: async () => {
      const payload: { base: string; quote: string; start_date: string; end_date?: string } = {
        base,
        quote,
        start_date: startDate,
      };
      if (endDate) {
        payload.end_date = endDate;
      }
      const resp = await client.post("/me/prices/historical", payload);
      return resp.data as HistoricalPrice[];
    },
    onSuccess: (data) => {
      setPrices(data);
      setError(null);
    },
    onError: (e: any) => {
      setError(e?.response?.data?.detail || e.message || "Failed to fetch historical prices");
      setPrices(null);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchHistorical.mutate();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 border-b flex justify-between items-center sticky top-0 bg-white rounded-t-lg">
          <h2 className="text-xl font-semibold text-gray-800">
            Historical Prices: {symbol}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="p-4">
          <form onSubmit={handleSubmit} className="space-y-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Date (optional, defaults to latest)
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            {error && (
              <div className="text-red-600 bg-red-50 p-2 rounded text-sm">{error}</div>
            )}
            <div className="flex gap-2">
              <button
                type="submit"
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition disabled:opacity-50"
                disabled={fetchHistorical.isPending}
              >
                {fetchHistorical.isPending ? "Fetching..." : "Fetch Prices"}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition"
              >
                Close
              </button>
            </div>
          </form>

          {prices && prices.length > 0 && (
            <div className="border rounded-md overflow-hidden">
              <table className="w-full text-left">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="py-2 px-3 text-sm font-medium text-gray-600">Date</th>
                    <th className="py-2 px-3 text-sm font-medium text-gray-600">Price ({quote})</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {prices.map((p, index) => (
                    <tr key={p.date} className={index % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                      <td className="py-2 px-3 text-gray-800">{p.date}</td>
                      <td className="py-2 px-3 text-gray-700 font-mono">{p.price.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {prices && prices.length === 0 && (
            <p className="text-gray-500 text-center py-4">No price data found for this date range.</p>
          )}
        </div>
      </div>
    </div>
  );
}
