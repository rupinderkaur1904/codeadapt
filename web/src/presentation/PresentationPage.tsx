import { useCallback, useEffect, useLayoutEffect, useState } from "react";
import { Link } from "react-router-dom";

import { SLIDES } from "./slides";
import "./presentation.css";

// The group presentation, served by the app itself at /presentation. It needs no login.
// Keys: → / Space / PageDown next, ← / PageUp back, Home / End, F full screen, G overview.
// The slide number is kept in the URL hash (#5), so a link opens on that slide.

const STAGE_W = 1280;
const STAGE_H = 720;

function fromHash(): number {
  const n = Number.parseInt(window.location.hash.replace("#", ""), 10);
  return Number.isFinite(n) && n >= 1 && n <= SLIDES.length ? n - 1 : 0;
}

export function PresentationPage() {
  const [index, setIndex] = useState(fromHash);
  const [grid, setGrid] = useState(false);
  const [scale, setScale] = useState(1);

  const go = useCallback((i: number) => {
    const next = Math.max(0, Math.min(SLIDES.length - 1, i));
    setIndex(next);
    window.history.replaceState(null, "", `#${next + 1}`);
  }, []);

  useEffect(() => {
    document.title = "CodeAdapt · presentation";
    const onHash = () => setIndex(fromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement | null;
      if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA")) return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (["ArrowRight", "PageDown", " "].includes(e.key)) {
        e.preventDefault();
        go(index + 1);
      } else if (["ArrowLeft", "PageUp"].includes(e.key)) {
        e.preventDefault();
        go(index - 1);
      } else if (e.key === "Home") go(0);
      else if (e.key === "End") go(SLIDES.length - 1);
      else if (e.key === "f" || e.key === "F") {
        if (document.fullscreenElement) void document.exitFullscreen();
        else void document.documentElement.requestFullscreen?.();
      } else if (e.key === "g" || e.key === "G") setGrid((g) => !g);
      else if (e.key === "Escape") setGrid(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go, index]);

  useLayoutEffect(() => {
    // Sized from the window, not the frame: the frame's own size can be read before the
    // deck's stylesheet has loaded. The margins match .deck-frame in presentation.css.
    const fit = () => {
      const width = window.innerWidth - 24;
      const height = window.innerHeight - 68;
      setScale(Math.max(0.1, Math.min(width / STAGE_W, height / STAGE_H)));
    };
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, [grid]);

  const slide = SLIDES[index] ?? SLIDES[0];
  if (!slide) return null;

  if (grid) {
    return (
      <div className="deck deck-grid">
        <header className="deck-bar">
          <span className="deck-brand">CodeAdapt · all slides</span>
          <button type="button" onClick={() => setGrid(false)}>
            Back to slide {index + 1}
          </button>
        </header>
        <ol className="deck-thumbs">
          {SLIDES.map((s, i) => (
            <li key={s.id}>
              <button
                type="button"
                className={i === index ? "on" : undefined}
                onClick={() => {
                  go(i);
                  setGrid(false);
                }}
              >
                <span className="deck-thumb-no">{i + 1}</span>
                <span className="deck-thumb-part">{s.part}</span>
                <span className="deck-thumb-who">{s.speaker}</span>
              </button>
            </li>
          ))}
        </ol>
      </div>
    );
  }

  return (
    <div className="deck">
      <div className="deck-frame">
        <div
          className={`deck-stage ${slide.tone === "soil" ? "on-soil" : "on-paper"}`}
          style={{
            width: STAGE_W,
            height: STAGE_H,
            transform: `translate(-50%, -50%) scale(${scale})`,
          }}
          onClick={(e) => {
            const target = e.target as HTMLElement;
            if (target.closest("a, button, pre, table, svg")) return;
            go(index + 1);
          }}
        >
          <div className="deck-slide" key={slide.id}>
            {slide.body}
          </div>
          <footer className="deck-foot">
            <span className="deck-foot-brand">CodeAdapt</span>
            <span className="deck-foot-part">{slide.part}</span>
            <span className="deck-foot-who">
              {slide.speaker === "All" ? "Team" : slide.speaker}
            </span>
            <span className="deck-foot-no">
              {index + 1} / {SLIDES.length}
            </span>
          </footer>
        </div>
      </div>
      <nav className="deck-controls" aria-label="Slide controls">
        <button
          type="button"
          onClick={() => go(index - 1)}
          disabled={index === 0}
          aria-label="Previous slide"
        >
          ←
        </button>
        <button
          type="button"
          onClick={() => go(index + 1)}
          disabled={index === SLIDES.length - 1}
          aria-label="Next slide"
        >
          →
        </button>
        <button type="button" onClick={() => setGrid(true)}>
          All slides
        </button>
        <Link to="/">Leave</Link>
        <progress value={index + 1} max={SLIDES.length} aria-label="Progress" />
      </nav>
    </div>
  );
}
