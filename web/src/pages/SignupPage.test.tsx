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

function renderApp() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/problems"]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const unauthenticated = () =>
  json({ type: "x/not-authenticated", title: "Login", status: 401 }, 401);

afterEach(() => vi.unstubAllGlobals());

describe("sign-up", () => {
  it("is not offered when the deployment has it off", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) =>
        url.endsWith("/auth/signup")
          ? json({ enabled: false, needs_invite_code: true, min_password_length: 12 })
          : unauthenticated(),
      ),
    );
    renderApp();
    expect(await screen.findByRole("heading", { name: "Log in" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Create an account" })).not.toBeInTheDocument();
  });

  it("creates an account with an invite code and enters the app", async () => {
    let signedUp = false;
    const bodies: unknown[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        if (url.endsWith("/auth/signup") && (init?.method ?? "GET") === "GET") {
          return json({ enabled: true, needs_invite_code: true, min_password_length: 12 });
        }
        if (url.endsWith("/auth/signup")) {
          const body = JSON.parse(String(init?.body)) as { invite_code: string };
          bodies.push(body);
          if (body.invite_code !== "ABCD-EFGH-JKMN") {
            return json({ type: "x/bad-invite-code", title: "Bad", status: 403 }, 403);
          }
          signedUp = true;
          return json({ username: "newbie", role: "student", csrf_token: "tok" }, 201);
        }
        if (!signedUp) return unauthenticated();
        if (url.endsWith("/auth/me"))
          return json({ username: "newbie", role: "student", csrf_token: "tok" });
        return json([]);
      }),
    );
    const user = userEvent.setup();
    renderApp();
    await user.click(await screen.findByRole("button", { name: "Create an account" }));
    expect(screen.getByRole("heading", { name: "Create an account" })).toBeInTheDocument();

    await user.type(screen.getByLabelText("Invite code"), "WRONG");
    await user.type(screen.getByLabelText("Username"), "newbie");
    await user.type(screen.getByLabelText("Password"), "short");
    await user.type(screen.getByLabelText("Repeat password"), "short");
    await user.click(screen.getByRole("button", { name: "Create account" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("at least 12 characters");
    expect(bodies).toHaveLength(0);

    await user.clear(screen.getByLabelText("Password"));
    await user.type(screen.getByLabelText("Password"), "correct horse battery");
    await user.clear(screen.getByLabelText("Repeat password"));
    await user.type(screen.getByLabelText("Repeat password"), "correct horse battery");
    await user.click(screen.getByRole("button", { name: "Create account" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("invite code is not valid");

    await user.clear(screen.getByLabelText("Invite code"));
    await user.type(screen.getByLabelText("Invite code"), "ABCD-EFGH-JKMN");
    await user.click(screen.getByRole("button", { name: "Create account" }));
    expect(await screen.findByText("newbie")).toBeInTheDocument();
    // The form never sends a role or data class: the server decides those.
    expect(bodies.at(-1)).toEqual({
      username: "newbie",
      password: "correct horse battery",
      invite_code: "ABCD-EFGH-JKMN",
    });
  });

  it("asks for no invite code when the deployment runs open sign-up", async () => {
    let signedUp = false;
    const bodies: unknown[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        if (url.endsWith("/auth/signup") && (init?.method ?? "GET") === "GET") {
          return json({ enabled: true, needs_invite_code: false, min_password_length: 12 });
        }
        if (url.endsWith("/auth/signup")) {
          bodies.push(JSON.parse(String(init?.body)));
          signedUp = true;
          return json({ username: "newbie", role: "student", csrf_token: "tok" }, 201);
        }
        if (!signedUp) return unauthenticated();
        if (url.endsWith("/auth/me"))
          return json({ username: "newbie", role: "student", csrf_token: "tok" });
        return json([]);
      }),
    );
    const user = userEvent.setup();
    renderApp();
    await user.click(await screen.findByRole("button", { name: "Create an account" }));
    expect(screen.queryByLabelText("Invite code")).not.toBeInTheDocument();
    await user.type(screen.getByLabelText("Username"), "newbie");
    await user.type(screen.getByLabelText("Password"), "correct horse battery");
    await user.type(screen.getByLabelText("Repeat password"), "correct horse battery");
    await user.click(screen.getByRole("button", { name: "Create account" }));
    expect(await screen.findByText("newbie")).toBeInTheDocument();
    expect(bodies).toEqual([{ username: "newbie", password: "correct horse battery" }]);
  });
});
