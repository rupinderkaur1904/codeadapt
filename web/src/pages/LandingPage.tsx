import { Link } from "react-router-dom";

// The example is the lower-bound error model hi_init_last_index. The failing case and the
// hint are quoted from content/demo/lower-bound/problem.toml, so the card shows what a
// student would actually be told; it is a static picture, not a live diagnosis.
const EXAMPLE_LINES = [
  { code: "int lo = 0;" },
  { code: "int hi = a.size() - 1;", flagged: true },
  { code: "while (lo < hi) {" },
  { code: "    int mid = lo + (hi - lo) / 2;" },
  { code: "    if (a[mid] < target) lo = mid + 1;" },
  { code: "    else hi = mid;" },
  { code: "}" },
  { code: "return lo;" },
];

// The four skills the demo binary-search problems probe (the [skills] tables in content/demo).
// Each label sits where no root line crosses it: dx/dy offset it from the node.
const TRACED = {
  label: "search-space bounds",
  x: 360,
  y: 118,
  dx: -24,
  dy: 5,
  anchor: "end" as const,
};
const SKILLS = [
  TRACED,
  { label: "equality handling", x: 180, y: 232, dx: 0, dy: 34, anchor: "middle" as const },
  { label: "loop termination", x: 520, y: 262, dx: 24, dy: 5, anchor: "start" as const },
  { label: "problem specification", x: 800, y: 214, dx: 0, dy: 34, anchor: "middle" as const },
];

export function LandingPage({ loggedIn }: { loggedIn: boolean }) {
  return (
    <div className="landing">
      <section className="hero">
        <div className="hero-copy">
          <h1>
            Fix the root,
            <br />
            not just the symptom.
          </h1>
          <p className="lede">
            A failing test is the symptom. CodeAdapt shows you the case that breaks your code and,
            when the evidence points to one known mistake, a hint about what lies underneath.
          </p>
          <div className="hero-actions">
            <Link to="/problems" className="button">
              {loggedIn ? "Start digging" : "Log in to start"}
            </Link>
            <a href="#how" className="button secondary">
              How it works
            </a>
          </div>
        </div>
        <figure className="surface-card" aria-label="Example feedback">
          <figcaption>
            <span className="eyebrow">Example · Lower bound</span>
            <span className="tag tag-symptom">symptom</span>
          </figcaption>
          <pre className="surface-code">
            <code>
              {EXAMPLE_LINES.map((line) => (
                <span key={line.code} className={line.flagged ? "line flagged" : "line"}>
                  {line.code}
                  {"\n"}
                </span>
              ))}
            </code>
          </pre>
          <p className="surface-case">
            <span aria-hidden="true">↓</span> Failing case: the target is larger than every element.
          </p>
          <p className="surface-hint">
            Hint: Can your search ever return <code>a.size()</code>? Check the initial bounds of the
            search space.
          </p>
        </figure>
      </section>

      <section className="soil" id="how" aria-label="How it works">
        <svg className="soil-edge" viewBox="0 0 1200 60" preserveAspectRatio="none" aria-hidden>
          <path d="M0 60V34C90 12 170 8 260 26S420 50 520 24 700 2 800 22 980 46 1080 22 1170 14 1200 20V60Z" />
        </svg>
        <div className="soil-inner">
          <div className="soil-panel">
            <p className="eyebrow">How it reads a failure</p>
            <ol>
              <li>
                <strong>Runs your code</strong> on tests designed to separate common mistakes.
              </li>
              <li>
                <strong>Shows the case that fails</strong>, in plain words.
              </li>
              <li>
                <strong>Gives a hint only when the tests point to one known mistake.</strong>{" "}
                Otherwise it shows the failing cases without guessing.
              </li>
            </ol>
          </div>
          <figure className="roots">
            <RootsIllustration />
            <figcaption>
              Illustration: the four skills the binary-search problems exercise. The dashed line
              follows the example above. It does not show anyone&apos;s progress.
            </figcaption>
          </figure>
        </div>
        <p className="soil-footnote">
          Research prototype · 25 C++ problems in five families (binary search, arrays, two
          pointers, sliding window, prefix sums) · not yet evaluated with real students.
        </p>
      </section>
    </div>
  );
}

function RootsIllustration() {
  const sprout = { x: 620, y: 18 };
  const traced = TRACED;
  return (
    <svg
      viewBox="0 -64 1000 390"
      role="img"
      aria-label="Roots growing from a sprout to four skills"
    >
      <g className="root-lines">
        <path d={`M${sprout.x} ${sprout.y} C600 70 470 90 ${traced.x} ${traced.y}`} />
        <path d={`M${traced.x} ${traced.y} C350 170 240 190 180 232`} />
        <path d={`M${sprout.x} ${sprout.y} C600 120 540 190 520 262`} />
        <path d={`M${sprout.x} ${sprout.y} C680 90 760 140 800 214`} />
        <path className="hair" d="M180 232 C150 220 110 214 70 216" />
        <path className="hair" d="M520 262 C512 284 500 300 494 318" />
        <path className="hair" d="M800 214 C850 190 900 180 960 182" />
      </g>
      <path
        className="trace"
        d={`M${sprout.x + 6} ${sprout.y} C640 80 470 120 ${traced.x + 14} ${traced.y - 4}`}
      />
      <g className="sprout" transform={`translate(${sprout.x} ${sprout.y})`}>
        <path className="stem" d="M0 0 V-40" />
        <path className="leaf" d="M0 -30 C-6 -48 -26 -54 -38 -50 C-32 -36 -14 -28 0 -30Z" />
        <path className="leaf" d="M0 -34 C6 -54 28 -62 42 -58 C36 -42 16 -32 0 -34Z" />
      </g>
      {SKILLS.map((s) => (
        <g key={s.label} className={s === TRACED ? "node traced" : "node"}>
          <circle cx={s.x} cy={s.y} r="14" className="halo" />
          <circle cx={s.x} cy={s.y} r="6" />
          <text x={s.x + s.dx} y={s.y + s.dy} textAnchor={s.anchor}>
            {s.label}
          </text>
        </g>
      ))}
    </svg>
  );
}
