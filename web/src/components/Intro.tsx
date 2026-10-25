import { useEffect, useRef, useState } from "react";

const SEEN_KEY = "codeadapt.introSeen";
const EXIT_MS = 600;
const NAME = "CodeAdapt";

/** True when the intro has already been shown in this browser tab. */
export function introSeen(): boolean {
  try {
    return window.sessionStorage.getItem(SEEN_KEY) === "1";
  } catch {
    return false;
  }
}

function markSeen() {
  try {
    window.sessionStorage.setItem(SEEN_KEY, "1");
  } catch {
    // Storage can be blocked; the intro then simply shows again next time.
  }
}

/**
 * Full-screen opening: the name grows in at the centre like a sprout from the soil line.
 * Click anywhere, or press Enter or Space, to continue to the landing page. Shown once per
 * tab session; with reduced motion the name appears without animation.
 */
export function Intro({ onDone }: { onDone: () => void }) {
  const button = useRef<HTMLButtonElement>(null);
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    button.current?.focus();
  }, []);

  useEffect(() => {
    if (!leaving) return;
    const reduced = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    const timer = window.setTimeout(onDone, reduced ? 0 : EXIT_MS);
    return () => window.clearTimeout(timer);
  }, [leaving, onDone]);

  function enter() {
    if (leaving) return;
    markSeen();
    setLeaving(true);
  }

  return (
    <button
      ref={button}
      type="button"
      className={leaving ? "intro intro-leaving" : "intro"}
      onClick={enter}
      aria-label="Enter CodeAdapt"
    >
      <span className="intro-stage" aria-hidden="true">
        <span className="intro-sky">
          <svg className="intro-sprout" viewBox="0 0 80 60">
            <path className="intro-stem" d="M40 60 V26" />
            <path
              className="intro-leaf intro-leaf-l"
              d="M40 34 C34 18 16 14 6 18 C12 30 28 36 40 34Z"
            />
            <path
              className="intro-leaf intro-leaf-r"
              d="M40 30 C46 12 66 6 78 10 C72 26 54 32 40 30Z"
            />
          </svg>
          <span className="intro-name">
            {[...NAME].map((ch, i) => (
              <span
                key={i}
                className="intro-letter"
                style={{ animationDelay: `${0.35 + i * 0.06}s` }}
              >
                {ch}
              </span>
            ))}
          </span>
        </span>
        <span className="intro-ground">
          <svg className="intro-roots" viewBox="0 0 400 70" preserveAspectRatio="none">
            <path d="M200 2 C190 24 150 34 110 46" />
            <path d="M200 2 C206 30 230 44 280 58" />
            <path d="M200 2 C198 26 196 44 192 68" />
          </svg>
          <span className="intro-tagline">Fix the root, not just the symptom.</span>
          <span className="intro-hint">Click anywhere or press Enter</span>
        </span>
      </span>
    </button>
  );
}
