import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import type { LearnerNext } from "../api/client";
import { next } from "../test/fixtures";
import { RecommendationCard } from "./RecommendationCard";

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
    const { container } = renderCard({ recommendation: null, last_followup: null });
    await new Promise((r) => setTimeout(r, 20));
    expect(container).toBeEmptyDOMElement();
  });
});
