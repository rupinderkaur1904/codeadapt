import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import type { SubmissionView } from "../api/client";
import { problem, supported } from "../test/fixtures";
import { PracticePage } from "./PracticePage";

// CodeMirror needs layout APIs jsdom lacks; a textarea keeps the contract.
vi.mock("../components/CodeEditor", () => ({
  CodeEditor: ({ value, onChange }: { value: string; onChange: (v: string) => void }) => (
    <textarea aria-label="Solution code" value={value} onChange={(e) => onChange(e.target.value)} />
  ),
}));

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/practice/lower-bound"]}>
        <Routes>
          <Route path="/practice/:slug" element={<PracticePage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("PracticePage", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("submits the editor content and polls until feedback arrives", async () => {
    let polls = 0;
    const posted: unknown[] = [];
    const queued: SubmissionView = { ...supported, status: "queued", feedback: null, tests: [] };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/problems/lower-bound")) return json(problem);
      if (url.includes("/submissions?problem_slug=")) return json([]);
      if (url.endsWith("/submissions") && init?.method === "POST") {
        posted.push(JSON.parse(String(init.body)));
        return json({ id: "s1", status: "queued" }, 202);
      }
      if (url.endsWith("/submissions/s1")) return json(++polls < 2 ? queued : supported);
      throw new Error(`unexpected request ${url}`);
    });

    renderPage();
    const editor = await screen.findByLabelText("Solution code");
    expect(editor).toHaveValue(problem.starter_code);
    await userEvent.clear(editor);
    await userEvent.type(editor, "int f() {{ return 1; }");
    await userEvent.click(screen.getByRole("button", { name: "Submit" }));

    expect(
      await screen.findByText(/Can your search ever return/, {}, { timeout: 4000 }),
    ).toBeInTheDocument();
    expect(posted).toEqual([{ problem_slug: "lower-bound", source: "int f() { return 1; }" }]);
    expect(polls).toBeGreaterThanOrEqual(2);
    // The draft is kept locally.
    expect(window.localStorage.getItem("codeadapt:draft:lower-bound")).toBe(
      "int f() { return 1; }",
    );
  });

  it("shows API errors as problem details", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      json({ type: "x/not-found", title: "Problem not found", status: 404 }, 404),
    );
    renderPage();
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Problem not found"));
  });
});
