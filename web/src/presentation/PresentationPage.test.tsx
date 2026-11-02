import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";

import { App } from "../App";
import { PresentationPage } from "./PresentationPage";
import { SLIDES } from "./slides";

beforeAll(() => {
  // jsdom has no ResizeObserver.
  globalThis.ResizeObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;
});

afterEach(() => {
  vi.unstubAllGlobals();
  window.location.hash = "";
});

function renderDeck() {
  return render(
    <MemoryRouter>
      <PresentationPage />
    </MemoryRouter>,
  );
}

describe("presentation", () => {
  it("is served at /presentation without asking the API who is logged in", async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/presentation"]}>
          <App />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect(await screen.findByRole("heading", { name: "CodeAdapt" })).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("moves between slides with the keyboard and keeps the number in the hash", () => {
    renderDeck();
    expect(screen.getByText(`1 / ${SLIDES.length}`)).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "ArrowRight" });
    expect(screen.getByText(`2 / ${SLIDES.length}`)).toBeInTheDocument();
    expect(window.location.hash).toBe("#2");
    fireEvent.keyDown(window, { key: "End" });
    expect(screen.getByText(`${SLIDES.length} / ${SLIDES.length}`)).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "ArrowRight" });
    expect(screen.getByText(`${SLIDES.length} / ${SLIDES.length}`)).toBeInTheDocument();
  });

  it("renders every slide, including all ten diagrams", () => {
    renderDeck();
    let diagrams = 0;
    for (let i = 0; i < SLIDES.length; i += 1) {
      act(() => {
        fireEvent.keyDown(window, { key: i === 0 ? "Home" : "ArrowRight" });
      });
      diagrams += document.querySelectorAll("svg.uml").length;
    }
    expect(diagrams).toBe(10);
  });

  it("names a presenter for every slide", () => {
    const speakers = new Set(SLIDES.map((s) => s.speaker));
    for (const name of ["Rupinder", "Ashmeen", "Gourav", "Jasroop"]) {
      expect(speakers.has(name as never)).toBe(true);
    }
  });
});
