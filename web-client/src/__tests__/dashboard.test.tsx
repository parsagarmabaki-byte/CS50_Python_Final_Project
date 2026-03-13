import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import Dashboard from "../pages/Dashboard";
import client from "../api/client";

// Mock axios client
vi.mock("../api/client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

function renderDashboard() {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

describe("Dashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    queryClient.clear();
  });

  it("renders loading state initially", () => {
    vi.mocked(client.get).mockImplementation(() => new Promise(() => {}));
    
    renderDashboard();
    
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders watchlist and prices when data is available", async () => {
    vi.mocked(client.get).mockResolvedValue({
      data: [
        { symbol: "FX:USDSEK", price: 10.5, date: "2026-03-13", source: "Frankfurter" },
      ],
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("FX:USDSEK")).toBeInTheDocument();
    });
  });

  it("renders empty state when watchlist is empty", async () => {
    vi.mocked(client.get).mockResolvedValue({ data: [] });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("No symbols in watchlist. Add one above.")).toBeInTheDocument();
    });
  });

  it("calls API to add symbol when Add button is clicked", async () => {
    vi.mocked(client.get).mockResolvedValue({ data: [] });
    vi.mocked(client.post).mockResolvedValue({ data: {} });

    renderDashboard();

    // Wait for loading to finish
    await waitFor(() => {
      expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
    });

    // Fill in inputs
    const baseInput = screen.getByPlaceholderText("Base (e.g., USD)");
    const quoteInput = screen.getByPlaceholderText("Quote (e.g., SEK)");
    
    fireEvent.change(baseInput, { target: { value: "EUR" } });
    fireEvent.change(quoteInput, { target: { value: "GBP" } });
    
    // Click Add button
    fireEvent.click(screen.getByText("Add"));

    await waitFor(() => {
      expect(client.post).toHaveBeenCalledWith("/me/watchlist", { base: "EUR", quote: "GBP" });
    });
  });

  it("calls API to remove symbol when Remove is clicked", async () => {
    vi.mocked(client.get).mockResolvedValue({
      data: [{ symbol: "FX:USDSEK" }],
    });
    vi.mocked(client.delete).mockResolvedValue({ data: {} });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("Remove")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Remove"));

    await waitFor(() => {
      expect(client.delete).toHaveBeenCalledWith("/me/watchlist/FX:USDSEK");
    });
  });

  it("calls API to update prices when Update Prices is clicked", async () => {
    vi.mocked(client.get).mockResolvedValue({ data: [] });
    vi.mocked(client.post).mockResolvedValue({ data: {} });

    renderDashboard();

    await waitFor(() => {
      expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Update Prices"));

    await waitFor(() => {
      expect(client.post).toHaveBeenCalledWith("/me/prices/update");
    });
  });

  it("displays error message when adding symbol fails", async () => {
    vi.mocked(client.get).mockResolvedValue({ data: [] });
    vi.mocked(client.post).mockRejectedValue({ 
      response: { data: { detail: "Invalid currency codes" } } 
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
    });

    const baseInput = screen.getByPlaceholderText("Base (e.g., USD)");
    const quoteInput = screen.getByPlaceholderText("Quote (e.g., SEK)");
    
    fireEvent.change(baseInput, { target: { value: "INVALID" } });
    fireEvent.change(quoteInput, { target: { value: "BAD" } });
    
    fireEvent.click(screen.getByText("Add"));

    await waitFor(() => {
      expect(screen.getByText("Invalid currency codes")).toBeInTheDocument();
    });
  });
});
