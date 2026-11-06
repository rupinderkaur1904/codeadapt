import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../App";

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function renderApp(path: string) {
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

describe("password change", () => {
  it("checks the current password, then uses the new session's CSRF token", async () => {
    const calls: { url: string; csrf: string | null; body?: string }[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        calls.push({
          url,
          csrf: new Headers(init?.headers).get("X-CSRF-Token"),
          body: init?.body ? String(init.body) : undefined,
        });
        if (url.endsWith("/auth/me"))
          return json({ username: "ana", role: "student", csrf_token: "tok1" });
        if (url.endsWith("/auth/password")) {
          const body = JSON.parse(String(init?.body)) as { current_password: string };
          if (body.current_password !== "old password!")
            return json({ type: "x/wrong-password", title: "Wrong", status: 403 }, 403);
          return json({ username: "ana", role: "student", csrf_token: "tok2" });
        }
        if (url.endsWith("/auth/logout")) return new Response(null, { status: 204 });
        return json([]);
      }),
    );
    const user = userEvent.setup();
    renderApp("/account");

    await user.type(await screen.findByLabelText("Current password"), "guess");
    await user.type(screen.getByLabelText(/^New password/), "a new passphrase");
    await user.type(screen.getByLabelText("Repeat new password"), "different one!!");
    await user.click(screen.getByRole("button", { name: "Change password" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("do not match");
    expect(calls.some((c) => c.url.endsWith("/auth/password"))).toBe(false);

    await user.clear(screen.getByLabelText("Repeat new password"));
    await user.type(screen.getByLabelText("Repeat new password"), "a new passphrase");
    await user.click(screen.getByRole("button", { name: "Change password" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("current password is wrong");

    await user.clear(screen.getByLabelText("Current password"));
    await user.type(screen.getByLabelText("Current password"), "old password!");
    await user.type(screen.getByLabelText(/^New password/), "a new passphrase");
    await user.type(screen.getByLabelText("Repeat new password"), "a new passphrase");
    await user.click(screen.getByRole("button", { name: "Change password" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Password changed");
    const change = calls.filter((c) => c.url.endsWith("/auth/password")).at(-1);
    expect(change?.csrf).toBe("tok1");

    // The next state-changing request uses the rotated session's token.
    await user.click(screen.getByRole("button", { name: "Log out" }));
    expect(calls.find((c) => c.url.endsWith("/auth/logout"))?.csrf).toBe("tok2");
  });

  it("is not offered under the development stub", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) =>
        url.endsWith("/auth/me")
          ? json({ username: "dev-student", role: "student", csrf_token: null })
          : json([]),
      ),
    );
    renderApp("/account");
    expect(await screen.findByText("Password change needs a real login.")).toBeInTheDocument();
  });
});
