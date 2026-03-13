import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AuthProvider, useAuth } from "./AuthProvider";
import client from "../api/client";

// Mock axios client
vi.mock("../api/client", () => ({
  default: {
    post: vi.fn(),
  },
}));

function TestComponent() {
  const auth = useAuth();
  return (
    <div>
      <span data-testid="user">{auth.user?.username || "none"}</span>
      <button onClick={() => auth.login("testuser", "testpass")}>Login</button>
      <button onClick={() => auth.logout()}>Logout</button>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("initializes with no user when no token in localStorage", () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    expect(screen.getByTestId("user")).toHaveTextContent("none");
  });

  it("restores user from localStorage on mount", () => {
    localStorage.setItem("fp_user", "restoreduser");
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    expect(screen.getByTestId("user")).toHaveTextContent("restoreduser");
  });

  it("stores token and user in localStorage on login", async () => {
    vi.mocked(client.post).mockResolvedValue({ data: { token: "test-token-123" } });
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    fireEvent.click(screen.getByText("Login"));

    await waitFor(() => {
      expect(client.post).toHaveBeenCalledWith("/login", { username: "testuser", password: "testpass" });
      expect(localStorage.getItem("fp_token")).toBe("test-token-123");
      expect(localStorage.getItem("fp_user")).toBe("testuser");
    });
  });

  it("clears localStorage on logout", () => {
    localStorage.setItem("fp_token", "existing-token");
    localStorage.setItem("fp_user", "existinguser");

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    fireEvent.click(screen.getByText("Logout"));

    expect(localStorage.getItem("fp_token")).toBeNull();
    expect(localStorage.getItem("fp_user")).toBeNull();
    expect(screen.getByTestId("user")).toHaveTextContent("none");
  });

  it("calls register and then auto-login", async () => {
    vi.mocked(client.post).mockResolvedValue({ data: { token: "new-token" } });

    function RegisterTestComponent() {
      const auth = useAuth();
      return (
        <div>
          <button onClick={() => auth.register("newuser", "newpass", "new@test.com")}>Register</button>
        </div>
      );
    }

    render(
      <AuthProvider>
        <RegisterTestComponent />
      </AuthProvider>
    );

    fireEvent.click(screen.getByText("Register"));

    await waitFor(() => {
      expect(client.post).toHaveBeenCalledWith("/register", { 
        username: "newuser", 
        password: "newpass", 
        email: "new@test.com" 
      });
      expect(client.post).toHaveBeenCalledWith("/login", { username: "newuser", password: "newpass" });
    });
  });
});
