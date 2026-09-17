import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import LoginPage from "./page";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

const loginMock = vi.fn();
vi.mock("@/lib/auth-api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/auth-api")>()),
  login: (...args: unknown[]) => loginMock(...args),
}));

const saveTokensMock = vi.fn();
vi.mock("@/lib/auth-client", () => ({ saveTokens: (...args: unknown[]) => saveTokensMock(...args) }));

beforeEach(() => {
  push.mockClear();
  loginMock.mockReset();
  saveTokensMock.mockClear();
});

it("rejects an invalid email before calling the API", async () => {
  render(<LoginPage />);
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "not-an-email" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "irrelevant" } });
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

  expect(await screen.findByText(/valid email/i)).toBeInTheDocument();
  expect(loginMock).not.toHaveBeenCalled();
});

it("saves tokens and redirects to /account on success", async () => {
  loginMock.mockResolvedValue({
    access_token: "a",
    refresh_token: "r",
    token_type: "bearer",
    expires_in: 900,
  });
  render(<LoginPage />);
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "user@example.com" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "correct-password-1" } });
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

  await waitFor(() => expect(saveTokensMock).toHaveBeenCalledWith({
    access_token: "a",
    refresh_token: "r",
    token_type: "bearer",
    expires_in: 900,
  }));
  expect(push).toHaveBeenCalledWith("/account");
});

it("shows the API error message when login fails", async () => {
  const { ApiError } = await import("@/lib/auth-api");
  loginMock.mockRejectedValue(
    new ApiError({ error: { code: "INVALID_CREDENTIALS", message: "Email or password is incorrect.", request_id: "req_1" } })
  );
  render(<LoginPage />);
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "user@example.com" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "wrong-password" } });
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

  expect(await screen.findByText("Email or password is incorrect.")).toBeInTheDocument();
  expect(push).not.toHaveBeenCalled();
});
