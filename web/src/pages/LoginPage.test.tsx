import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../App";
import type { ProblemSummary } from "../api/client";

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const problems: ProblemSummary[] = [
  {
    slug: "lower-bound",
    title: "Lower bound",
    family: "binary-search",
    no_failure_observed: false,
  },
];

function renderApp(path = "/problems") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  window.sessionStorage.clear();
});

describe("login", () => {
  it("shows the login form without a session, then the app after logging in", async () => {
    let loggedIn = false;
    const calls: { url: string; method: string; csrf: string | null }[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        const method = init?.method ?? "GET";
        calls.push({ url, method, csrf: new Headers(init?.headers).get("X-CSRF-Token") });
        if (url.endsWith("/auth/login")) {
          if (JSON.parse(String(init?.body)).password !== "right password") {
            return json({ type: "x/login-failed", title: "Wrong", status: 401 }, 401);
          }
          loggedIn = true;
          return json({ username: "ana", role: "student", csrf_token: "tok" });
        }
        if (!loggedIn)
          return json({ type: "x/not-authenticated", title: "Login", status: 401 }, 401);
        if (url.endsWith("/auth/me"))
          return json({ username: "ana", role: "student", csrf_token: "tok" });
        if (url.endsWith("/auth/logout")) {
          loggedIn = false;
          return new Response(null, { status: 204 });
        }
        return json(problems);
      }),
    );
    const user = userEvent.setup();
    renderApp();

    await user.type(await screen.findByLabelText("Username"), "ana");
    await user.type(screen.getByLabelText("Password"), "wrong");
    await user.click(screen.getByRole("button", { name: "Log in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Wrong username or password.");

    await user.type(screen.getByLabelText("Password"), "right password");
    await user.click(screen.getByRole("button", { name: "Log in" }));
    expect(await screen.findByText("ana")).toBeInTheDocument();
    expect(screen.queryByText(/Development role/)).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Research" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Log out" }));
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "Log in" })).toBeInTheDocument(),
    );
    const logout = calls.find((c) => c.url.endsWith("/auth/logout"));
    expect(logout).toMatchObject({ method: "POST", csrf: "tok" });
    expect(calls.filter((c) => c.method === "GET").every((c) => c.csrf === null)).toBe(true);
  });

  it("keeps the development role switch under the dev stub", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) =>
        url.endsWith("/auth/me")
          ? json({ username: "dev-student", role: "student", csrf_token: null })
          : json(problems),
      ),
    );
    renderApp();
    expect(await screen.findByText(/Development role/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Log out" })).not.toBeInTheDocument();
  });

  it("shows the landing page at / without a session, and asks for a login elsewhere", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => json({ type: "x/not-authenticated", title: "Login", status: 401 }, 401)),
    );
    const user = userEvent.setup();
    renderApp("/");
    expect(await screen.findByRole("heading", { name: /Fix the root/ })).toBeInTheDocument();
    // The illustration is labelled as such and shows no learner estimates.
    expect(screen.getByText(/It does not show anyone's progress/)).toBeInTheDocument();
    expect(screen.queryByText(/weak|strong|mastery/i)).not.toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: "Log in to start" }));
    expect(await screen.findByRole("heading", { name: "Log in" })).toBeInTheDocument();
  });

  it("opens the site with the intro, which Enter dismisses once per session", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => json({ type: "x/not-authenticated", title: "Login", status: 401 }, 401)),
    );
    const user = userEvent.setup();
    const first = renderApp("/");
    const intro = screen.getByRole("button", { name: "Enter CodeAdapt" });
    expect(intro).toHaveFocus();
    await user.keyboard("{Enter}");
    await waitFor(() =>
      expect(screen.queryByRole("button", { name: "Enter CodeAdapt" })).not.toBeInTheDocument(),
    );
    first.unmount();

    renderApp("/");
    expect(await screen.findByRole("heading", { name: /Fix the root/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Enter CodeAdapt" })).not.toBeInTheDocument();
  });

  it("skips the intro on deep links", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => json({ type: "x/not-authenticated", title: "Login", status: 401 }, 401)),
    );
    renderApp("/problems");
    expect(await screen.findByRole("heading", { name: "Log in" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Enter CodeAdapt" })).not.toBeInTheDocument();
  });
});
