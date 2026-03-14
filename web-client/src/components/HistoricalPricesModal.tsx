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
  // Parse symbol to get base and quote (e.g., "FX:USDSEK" -> "USD", "SEK")
  const symbolParts = symbol.replace("FX:", "");
  const defaultBase = symbolParts.substring(0, 3);
  const defaultQuote = symbolParts.substring(3, 6);

  const [base, setBase] = useState(defaultBase);
  const [quote, setQuote] = useState(defaultQuote);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Set default start date to 30 days ago
  React.useEffect(() => {
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    setStartDate(thirtyDaysAgo.toISOString().split("T")[0]);
  }, []);

  const fetchHistorical = useMutation({
    mutationFn: () =>
      client.post<HistoricalPrice[]>("/me/prices/historical", {
        base,
        quote,
        start_date: startDate,
        end_date: endDate || undefined,
      }).then(r => r.data),
    onError: (e: any) => setError(e?.response?.data?.detail || e.message || "Failed to fetch historical prices"),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    fetchHistorical.mutate();
  };

  const handleClose = () => {
    fetchHistorical.reset();
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-800">Historical Prices</h2>
            <button
              onClick={handleClose}
              className="text-gray-500 hover:text-gray-700 text-2xl"
            >
              &times;
            </button>
          </div>

          <form onSubmit={handleSubmit} className="mb-6">
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Base Currency
                </label>
                <input
                  type="text"
                  value={base}
                  onChange={(e) => setBase(e.target.value.toUpperCase())}
                  className="w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  maxLength={3}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Quote Currency
                </label>
                <input
                  type="text"
                  value={quote}
                  onChange={(e) => setQuote(e.target.value.toUpperCase())}
                  className="w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  maxLength={3}
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
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
                  End Date (optional)
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="flex gap-2">
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition disabled:opacity-50"
                disabled={fetchHistorical.isPending || !base || !quote || !startDate}
              >
                {fetchHistorical.isPending ? "Loading..." : "Fetch Prices"}
              </button>
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition"
              >
                Close
              </button>
            </div>
          </form>

          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded mb-4">
              {error}
            </div>
          )}

          {fetchHistorical.data && fetchHistorical.data.length > 0 && (
            <div>
              <h3 className="font-medium text-gray-700 mb-2">
                {base}/{quote} - {fetchHistorical.data.length} days
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b">
                      <th className="py-2 text-gray-600 font-medium">#</th>
                      <th className="py-2 text-gray-600 font-medium">Date</th>
                      <th className="py-2 text-gray-600 font-medium">Price</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fetchHistorical.data.map((item, index) => (
                      <tr key={item.date} className="border-b last:border-0">
                        <td className="py-2 text-gray-500">{index + 1}</td>
                        <td className="py-2 text-gray-800">{item.date}</td>
                        <td className="py-2 text-gray-800 font-mono">{item.price.toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {fetchHistorical.data && fetchHistorical.data.length === 0 && (
            <p className="text-gray-500 text-center py-4">
              No data found for the selected date range.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
