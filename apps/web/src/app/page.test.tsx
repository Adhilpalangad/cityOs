import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import Home from "./page";

vi.mock("@/lib/api", () => ({ getApiHealth: vi.fn().mockResolvedValue({ status: "healthy", service: "api-gateway" }) }));

it("shows the CityOS landing page and platform status", async () => {
  render(await Home());
  expect(screen.getByText("CityOS")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Run the city on one platform" })).toBeInTheDocument();
  expect(screen.getByText("API Gateway")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute("href", "/login");
  expect(screen.getByRole("link", { name: "Create an account" })).toHaveAttribute("href", "/register");
});
