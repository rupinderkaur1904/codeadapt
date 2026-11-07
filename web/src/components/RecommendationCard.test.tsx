import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import type { LearnerNext } from "../api/client";
import { next } from "../test/fixtures";
import {
  ADAPTATION_FALLBACK,
  ADAPTATION_FALLBACK_NO_RETRY,
  RecommendationCard,
} from "./RecommendationCard";

function renderCard(body: LearnerNext, currentSlug?: string) {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(body), { headers: { "Content-Type": "application/json" } }),
  );
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <RecommendationCard currentSlug={currentSlug} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("RecommendationCard", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows the follow-up verdict, the next problem and its focus", async () => {
    renderCard(next);
    expect(await screen.findByText(/passed all 7 tests/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Recommended next" })).toBeInTheDocument();
    expect(screen.getByText(/equal elements land/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Go to Count occurrences" })).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/master/i);
  });

  it("does not link to the problem already open", async () => {
    renderCard(next, "count-occurrences");
    expect(await screen.findByText("This is the problem you are on.")).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it("renders nothing before the first recommendation", async () => {
    const { container } = renderCard({
      recommendation: null,
      last_followup: null,
      adaptation_unavailable: false,
      retry_available: false,
    });
    await new Promise((r) => setTimeout(r, 20));
    expect(container).toBeEmptyDOMElement();
  });

  it("shows only the neutral fallback when adaptation failed (D6)", async () => {
    renderCard({ ...next, adaptation_unavailable: true, retry_available: true });
    expect(await screen.findByText(ADAPTATION_FALLBACK)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
    // Nothing from before the latest attempt: no recommendation, focus, link or verdict.
    expect(screen.queryByRole("heading", { name: "Recommended next" })).not.toBeInTheDocument();
    expect(screen.queryByText(/passed all 7 tests/)).not.toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it("offers no retry when only a new submission can continue (R10)", async () => {
    renderCard({ ...next, adaptation_unavailable: true, retry_available: false });
    expect(await screen.findByText(ADAPTATION_FALLBACK_NO_RETRY)).toBeInTheDocument();
    expect(screen.queryByText(ADAPTATION_FALLBACK)).not.toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Recommended next" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it("retries once per click and then shows the recovered recommendation", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(
        async (_input, init) =>
          new Response(
            JSON.stringify(
              init?.method === "POST"
                ? next
                : { ...next, adaptation_unavailable: true, retry_available: true },
            ),
            { headers: { "Content-Type": "application/json" } },
          ),
      );
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <RecommendationCard />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    fireEvent.click(await screen.findByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("heading", { name: "Recommended next" })).toBeInTheDocument();
    expect(screen.queryByText(ADAPTATION_FALLBACK)).not.toBeInTheDocument();
    const posts = fetchMock.mock.calls.filter(([, init]) => init?.method === "POST");
    expect(posts).toHaveLength(1);
    expect(String(posts[0]?.[0])).toContain("/me/recommendation/retry");
  });
});
