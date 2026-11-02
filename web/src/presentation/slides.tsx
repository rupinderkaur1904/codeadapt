// Slide content. Each slide names who presents it; the speaking script that goes with these
// slides is docs/presentation/script.md. Numbers quoted here come from
// docs/release-2026-10-26.md and docs/evaluation/summary.md; keep them in step.

import { useState, type ReactNode } from "react";

import {
  CLASSES,
  SD_ADAPT,
  SD_EVALUATE,
  SD_LOGIN,
  SD_RESEARCH,
  SD_SUBMIT,
  UC_ADMIN,
  UC_RESEARCHER,
  UC_STUDENT,
  UC_WORKER,
} from "./diagrams";
import { DEMO_PROGRAMS } from "./demoKit";
import { ClassDiagram, SequenceDiagram, UseCaseDiagram } from "./uml";

export type Speaker = "Rupinder" | "Ashmeen" | "Gourav" | "Jasroop" | "All";

export type Slide = {
  id: string;
  speaker: Speaker;
  part: string;
  tone?: "soil" | "paper";
  body: ReactNode;
};

export const TEAM: { name: Exclude<Speaker, "All">; part: string }[] = [
  { name: "Rupinder", part: "Problem, users, solution and journey" },
  { name: "Ashmeen", part: "Live demo and system integration" },
  { name: "Gourav", part: "Use case and class diagrams" },
  { name: "Jasroop", part: "Sequence diagrams, status and next steps" },
];

// Fill each `evidence` line with real links before presenting: commits, issues, tests,
// documents or journal entries the member can open and explain. The brief says each member
// will be asked to find their own code, so list only work that member did.
const CONTRIBUTIONS: { name: string; did: string[]; evidence: string }[] = [
  {
    name: "Rupinder",
    did: ["Problem framing and user research", "Landing page and user journey"],
    evidence: "",
  },
  {
    name: "Ashmeen",
    did: ["Backend pipeline and sandbox", "Integration, demo set-up"],
    evidence: "",
  },
  { name: "Gourav", did: ["Use case and class diagrams", "Data model review"], evidence: "" },
  { name: "Jasroop", did: ["Sequence diagrams", "Testing, limitations and roadmap"], evidence: "" },
];

const REPO = "https://github.com/rupinderkaur1904/codeadapt";

function Head({
  kicker,
  title,
  children,
}: {
  kicker: string;
  title: ReactNode;
  children?: ReactNode;
}) {
  return (
    <header className="s-head">
      <p className="s-kicker">{kicker}</p>
      <h2>{title}</h2>
      {children && <p className="s-sub">{children}</p>}
    </header>
  );
}

function Diagram({
  kicker,
  title,
  note,
  children,
}: {
  kicker: string;
  title: string;
  note: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="s-diagram">
      <header className="s-head compact">
        <p className="s-kicker">{kicker}</p>
        <h2>{title}</h2>
      </header>
      <div className="s-figure">{children}</div>
      <p className="s-note">{note}</p>
    </div>
  );
}

function Divider({ n, title, who, line }: { n: string; title: string; who: string; line: string }) {
  return (
    <div className="s-divider">
      <p className="s-part-no">{n}</p>
      <h2>{title}</h2>
      <p className="s-divider-line">{line}</p>
      <p className="s-divider-who">{who}</p>
      <svg className="s-divider-roots" viewBox="0 -70 600 290" aria-hidden="true">
        <path className="stem" d="M300 0 V-44" />
        <path className="leaf" d="M300 -32 C293 -52 270 -59 256 -54 C263 -39 283 -30 300 -32Z" />
        <path className="leaf" d="M300 -37 C307 -59 332 -68 348 -63 C341 -45 318 -35 300 -37Z" />
        <path d="M0 0 H600" className="ground" />
        <path d="M300 0 C300 60 220 90 120 120 S20 190 0 210" />
        <path d="M300 0 C310 70 360 110 430 150 S560 200 600 205" />
        <path d="M300 0 C296 80 300 140 290 220" />
        <path className="thin" d="M120 120 C110 150 80 170 60 200" />
        <path className="thin" d="M430 150 C450 170 470 190 476 220" />
      </svg>
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      type="button"
      className="s-copy"
      onClick={() => {
        void navigator.clipboard?.writeText(text).then(() => {
          setDone(true);
          window.setTimeout(() => setDone(false), 1500);
        });
      }}
    >
      {done ? "Copied" : "Copy code"}
    </button>
  );
}

function DemoKit() {
  const [open, setOpen] = useState(0);
  const p = DEMO_PROGRAMS[open];
  if (!p) return null;
  return (
    <div className="s-demo">
      <div className="s-demo-list">
        <Head kicker="Part 2 · live demo" title="Four programs, four different answers" />
        <ol>
          {DEMO_PROGRAMS.map((d, i) => (
            <li key={d.file}>
              <button
                type="button"
                className={i === open ? "on" : undefined}
                onClick={() => setOpen(i)}
              >
                <span className="mono">{d.file}</span>
                <span className="s-demo-intent">{d.intent}</span>
                <span className="s-demo-expect mono">{d.expect}</span>
              </button>
            </li>
          ))}
        </ol>
        <p className="s-fine">
          Test data: author-written programs from{" "}
          <span className="mono">eval/heldout/lower-bound/</span>. They are not student submissions.
        </p>
        <a className="s-launch" href="/problems" target="_blank" rel="noreferrer">
          Open the live app → Lower bound
        </a>
      </div>
      <div className="s-demo-code">
        <div className="s-demo-bar">
          <span className="mono">{p.file}</span>
          <CopyButton text={p.source} />
        </div>
        <pre>
          <code>{p.source}</code>
        </pre>
        <p className="s-demo-shows">
          <strong>Watch for:</strong> {p.shows}
        </p>
      </div>
    </div>
  );
}

function Architecture() {
  const box = (
    x: number,
    y: number,
    w: number,
    h: number,
    title: string,
    lines: string[],
    tone = "",
  ) => (
    <g className={`arch-box ${tone}`}>
      <rect x={x} y={y} width={w} height={h} rx="10" />
      <text x={x + 16} y={y + 28} className="arch-title">
        {title}
      </text>
      {lines.map((l, i) => (
        <text key={l} x={x + 16} y={y + 52 + i * 19} className="arch-line">
          {l}
        </text>
      ))}
    </g>
  );
  return (
    <svg viewBox="0 0 1180 470" className="arch" role="img" aria-label="Component diagram">
      <defs>
        <marker
          id="arr"
          viewBox="0 0 10 10"
          refX="9"
          refY="5"
          markerWidth="8"
          markerHeight="8"
          orient="auto-start-reverse"
        >
          <path d="M0 0 L10 5 L0 10 Z" className="arch-head" />
        </marker>
      </defs>
      <rect x="560" y="12" width="608" height="446" rx="14" className="arch-zone" />
      <text x="580" y="40" className="arch-zone-label">
        runner side: the only part that touches Docker
      </text>
      {box(12, 40, 240, 150, "Web app", [
        "React 19 + TypeScript",
        "CodeMirror 6 editor",
        "TanStack Query polling",
        "types from OpenAPI",
      ])}
      {box(300, 40, 230, 170, "API", [
        "FastAPI + Pydantic v2",
        "sessions, CSRF, roles",
        "rate limits",
        "student-safe projection",
        "no Docker access",
      ])}
      {box(
        300,
        290,
        230,
        150,
        "Database",
        [
          "PostgreSQL 16 (SQLite dev)",
          "SQLAlchemy 2 + Alembic",
          "append-only evidence",
          "job queue table",
        ],
        "store",
      )}
      {box(
        600,
        60,
        250,
        190,
        "Runner worker",
        [
          "claim job, lease",
          "compile + run tests",
          "diagnosis v1.3",
          "evidence ledger",
          "policy 1.5, follow-up",
        ],
        "core",
      )}
      {box(900, 60, 250, 170, "Sandbox", [
        "one container per test",
        "gcc 14.2, pinned digest",
        "no network, read-only",
        "CPU, wall, memory, output",
        "gVisor tier (CI only)",
      ])}
      {box(900, 290, 250, 150, "Content bundle", [
        "25 problems, 5 families",
        "tests, error models",
        "skill map per version",
        "sha256 content version",
      ])}
      {box(
        600,
        300,
        250,
        140,
        "learner.bkt",
        ["researcher-only", "bkt-params-assumed-1", "never shown to students"],
        "faint",
      )}
      <line x1="252" y1="130" x2="296" y2="130" markerEnd="url(#arr)" className="arch-edge" />
      <text x="274" y="112" className="arch-edge-label" textAnchor="middle">
        HTTPS
      </text>
      <text x="274" y="150" className="arch-edge-label" textAnchor="middle">
        JSON
      </text>
      <line x1="415" y1="210" x2="415" y2="286" markerEnd="url(#arr)" className="arch-edge" />
      <text x="406" y="252" className="arch-edge-label" textAnchor="end">
        insert submission + job
      </text>
      <path
        d="M600 236 C570 250 560 300 534 330"
        markerEnd="url(#arr)"
        className="arch-edge"
        fill="none"
      />
      <text x="424" y="262" className="arch-edge-label">
        worker claims job
      </text>
      <line x1="850" y1="140" x2="896" y2="140" markerEnd="url(#arr)" className="arch-edge" />
      <line x1="896" y1="180" x2="854" y2="180" markerEnd="url(#arr)" className="arch-edge" />
      <line
        x1="896"
        y1="350"
        x2="854"
        y2="230"
        markerEnd="url(#arr)"
        className="arch-edge dashed"
      />
      <text x="880" y="300" className="arch-edge-label" textAnchor="end">
        loads
      </text>
      <line
        x1="725"
        y1="250"
        x2="725"
        y2="296"
        markerEnd="url(#arr)"
        className="arch-edge dashed"
      />
    </svg>
  );
}

function Matrix() {
  // A simplified picture of the decision, not real measurements: ✓ = same output as the
  // reference, ✗ = different output.
  const tests = [
    "empty",
    "below_all",
    "above_all",
    "duplicates_mid",
    "duplicates_all",
    "single_equal",
  ];
  const cols: { name: string; marks: string; kind?: string }[] = [
    { name: "this submission", marks: "✓✓✓✗✗✓", kind: "student" },
    { name: "model A", marks: "✓✓✗✓✓✓" },
    { name: "model B", marks: "✓✓✓✗✗✓", kind: "match" },
    { name: "model C", marks: "✗✓✓✗✓✓" },
  ];
  return (
    <table className="s-matrix">
      <thead>
        <tr>
          <th>test</th>
          {cols.map((c) => (
            <th key={c.name} className={c.kind}>
              {c.name}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {tests.map((t, r) => (
          <tr key={t}>
            <td className="mono">{t}</td>
            {cols.map((c) => (
              <td key={c.name} className={`${c.kind ?? ""} ${c.marks[r] === "✗" ? "x" : "ok"}`}>
                {c.marks[r]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export const SLIDES: Slide[] = [
  {
    id: "title",
    speaker: "Rupinder",
    part: "Opening",
    tone: "soil",
    body: (
      <div className="s-title">
        <p className="s-kicker on-soil">Project presentation</p>
        <h1>CodeAdapt</h1>
        <p className="s-title-line">
          A C++ practice platform that looks at <em>why</em> a solution fails, and names a mistake
          only when the tests can tell it apart from the others.
        </p>
        <ul className="s-team">
          {TEAM.map((m) => (
            <li key={m.name}>
              <strong>{m.name}</strong>
              <span>{m.part}</span>
            </li>
          ))}
        </ul>
      </div>
    ),
  },
  {
    id: "problem",
    speaker: "Rupinder",
    part: "1 · The problem",
    body: (
      <div className="s-split">
        <div>
          <Head kicker="1 · The problem" title="“Wrong answer on test 7.” Now what?" />
          <p className="s-body">
            Most online judges stop at a verdict. A beginner whose binary search is off by one sees
            a red cross and a test number, then changes things until it turns green. Nothing tells
            them which idea was wrong.
          </p>
          <p className="s-body">
            Guessing the cause is the other trap. A tool that says “you don’t understand boundaries”
            when two different mistakes give the same output is confidently wrong, and the student
            has no way to tell.
          </p>
        </div>
        <div className="s-verdicts">
          <div className="s-verdict judge">
            <p className="s-verdict-label">a typical judge</p>
            <p className="s-verdict-main">✗ Wrong Answer</p>
            <p className="mono">test 7 / 17 · 3 ms</p>
          </div>
          <div className="s-verdict ours">
            <p className="s-verdict-label">what the student needs</p>
            <ol>
              <li>Which case breaks my code, in words?</li>
              <li>Is it one known mistake, or can’t you tell?</li>
              <li>What should I practise next?</li>
            </ol>
          </div>
        </div>
      </div>
    ),
  },
  {
    id: "users",
    speaker: "Rupinder",
    part: "1 · Users and why",
    body: (
      <div>
        <Head
          kicker="1 · Who it is for, and why this problem"
          title="Three users, one narrow topic on purpose"
        />
        <div className="s-cols three users">
          <section>
            <h3>Students</h3>
            <p>
              Learning algorithms in C++ in a first data-structures course. They practise, submit,
              and read feedback.
            </p>
          </section>
          <section>
            <h3>Researchers / instructors</h3>
            <p>
              Want to see how errors actually show up: every diagnosis traced back to the test
              results behind it.
            </p>
          </section>
          <section>
            <h3>Administrator</h3>
            <p>
              Creates accounts and roles, backs up the data and checks that problem content is valid
              before use.
            </p>
          </section>
        </div>
        <div className="s-why">
          <p className="s-why-label">Why binary search first</p>
          <p>
            About ten lines of code, and many ways to be off by one. The{" "}
            <span className="mono">lower-bound</span> problem alone has{" "}
            <strong>8 modelled mistakes</strong> and <strong>17 tests</strong> chosen so that the
            mistakes produce different outputs. The bank now has{" "}
            <strong>25 problems in 5 families</strong>.
          </p>
        </div>
      </div>
    ),
  },
  {
    id: "solution",
    speaker: "Rupinder",
    part: "2 · Proposed solution",
    body: (
      <div>
        <Head kicker="2 · Proposed solution" title="Treat every submission as evidence">
          The system keeps three things apart: what was observed, what it infers, and what happened
          next.
        </Head>
        <ol className="s-loop">
          {[
            ["Submission", "source + problem version"],
            ["Execution evidence", "one sandboxed run per test"],
            ["Diagnosis", "matched against known mistakes"],
            ["Targeted practice", "a problem that probes the same skill"],
            ["New evidence", "the next attempt"],
            ["Adaptation", "was the criterion met?"],
          ].map(([t, d], i) => (
            <li key={t}>
              <span className="s-loop-no">{i + 1}</span>
              <strong>{t}</strong>
              <span>{d}</span>
            </li>
          ))}
        </ol>
        <div className="s-cols three rules">
          <section>
            <h3>Observe before inferring</h3>
            <p>Observations are stored once and never edited. Diagnoses point back to them.</p>
          </section>
          <section>
            <h3>Abstain when unsure</h3>
            <p>If no single known mistake fits, the student sees the failing cases and no guess.</p>
          </section>
          <section>
            <h3>“Behaves as if”</h3>
            <p>Feedback describes the program’s behaviour, never the student’s mind.</p>
          </section>
        </div>
      </div>
    ),
  },
  {
    id: "journey",
    speaker: "Rupinder",
    part: "2 · User journey",
    body: (
      <div>
        <Head
          kicker="2 · The main journey we implemented"
          title="From a blank editor to the next problem"
        />
        <ol className="s-journey">
          {[
            ["/", "Landing page", "what the tool does and does not claim"],
            ["login", "Log in", "operator-created account, session cookie"],
            ["/problems", "Pick a problem", "25 problems grouped by family"],
            ["/practice/lower-bound", "Write and submit", "statement, samples, C++ editor"],
            ["feedback", "Read the result", "failing cases, a hint only if supported"],
            ["recommended next", "Practise again", "follow-up checked on the next attempt"],
          ].map(([route, t, d], i) => (
            <li key={t}>
              <span className="s-step">{String(i + 1).padStart(2, "0")}</span>
              <span className="mono s-route">{route}</span>
              <strong>{t}</strong>
              <span>{d}</span>
            </li>
          ))}
        </ol>
        <p className="s-why-label s-journey-label">Researcher path</p>
        <ol className="s-journey researcher">
          {[
            ["/research", "Submissions and metrics", "filter by problem, outcome, data class"],
            [
              "/research/submissions/:id",
              "Evidence trace",
              "every observation, candidate and reason",
            ],
            [
              "/research/learners/:username",
              "Learner model",
              "labelled “estimated under assumed parameters”",
            ],
          ].map(([route, t, d], i) => (
            <li key={t}>
              <span className="s-step">{String.fromCharCode(65 + i)}</span>
              <span className="mono s-route">{route}</span>
              <strong>{t}</strong>
              <span>{d}</span>
            </li>
          ))}
        </ol>
      </div>
    ),
  },
  {
    id: "part-demo",
    speaker: "Ashmeen",
    part: "3 · Live demo",
    tone: "soil",
    body: (
      <Divider
        n="Part 2"
        title="Live: one complete run"
        who="Ashmeen"
        line="Real sandbox, real database, prepared programs. No recorded screens."
      />
    ),
  },
  { id: "demo", speaker: "Ashmeen", part: "3 · Demo kit", body: <DemoKit /> },
  {
    id: "architecture",
    speaker: "Ashmeen",
    part: "4 · Integration",
    body: (
      <Diagram
        kicker="4 · How the parts connect"
        title="Six components, one trust boundary"
        note="The API never runs student code. It writes a job; a separate worker claims it and is the only process that talks to Docker."
      >
        <Architecture />
      </Diagram>
    ),
  },
  {
    id: "contracts",
    speaker: "Ashmeen",
    part: "4 · Integration",
    body: (
      <div>
        <Head kicker="4 · Where the parts meet" title="Each seam has a checked contract" />
        <table className="s-table">
          <thead>
            <tr>
              <th>Seam</th>
              <th>What crosses it</th>
              <th>How it is held in place</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Web ↔ API</td>
              <td>JSON under /api/v1, problem+json errors</td>
              <td>TypeScript types generated from the OpenAPI schema; CI fails on drift</td>
            </tr>
            <tr>
              <td>Authentication</td>
              <td>Opaque token in an HttpOnly cookie, CSRF header</td>
              <td>Argon2id hashes; only a SHA-256 of the token is stored; login throttling</td>
            </tr>
            <tr>
              <td>API ↔ Database</td>
              <td>Submissions, jobs, evidence rows</td>
              <td>SQLAlchemy 2, Alembic migrations, tested on PostgreSQL 16 in CI</td>
            </tr>
            <tr>
              <td>Database ↔ Worker</td>
              <td>Job claim with a lease</td>
              <td>Conditional UPDATE, heartbeat renewal, completion fenced to the claim</td>
            </tr>
            <tr>
              <td>Worker ↔ Sandbox</td>
              <td>Source, test input → status, output, time</td>
              <td>Fresh container per test, no network, limits, end-of-output marker</td>
            </tr>
            <tr>
              <td>Worker ↔ Content</td>
              <td>Tests, error models, skill map</td>
              <td>Content version = hash of the files; old versions stay registered</td>
            </tr>
          </tbody>
        </table>
        <p className="s-fine">
          Backend: 609 unit tests + 39 sandbox tests · web: 37 component tests + 3 Playwright
          end-to-end flows (release report, 26 Oct).
        </p>
      </div>
    ),
  },
  {
    id: "matrix",
    speaker: "Ashmeen",
    part: "4 · The model",
    body: (
      <div className="s-split">
        <div>
          <Head
            kicker="4 · How a diagnosis is decided"
            title="Match behaviour, don’t guess intent"
          />
          <p className="s-body">
            Each known mistake is a real program. We run it on every test and store its outputs: its{" "}
            <strong>fingerprint</strong>. A submission’s outputs are compared with each fingerprint.
          </p>
          <ul className="s-rules">
            <li>
              <span className="mono">hypothesis_supported</span> exactly one model fits
            </li>
            <li>
              <span className="mono">ambiguous</span> several fit; none is named
            </li>
            <li>
              <span className="mono">unmodelled_behaviour</span> none fits
            </li>
            <li>
              <span className="mono">non_termination_observed</span> a time limit; a symptom, never
              a name
            </li>
          </ul>
          <p className="s-fine">
            No machine learning: the method is deterministic and can be replayed on stored evidence.
          </p>
        </div>
        <figure className="s-matrix-fig">
          <Matrix />
          <figcaption>
            Simplified illustration. Model B is the only fingerprint that matches every test.
          </figcaption>
        </figure>
      </div>
    ),
  },
  {
    id: "part-design",
    speaker: "Gourav",
    part: "7 · Design",
    tone: "soil",
    body: (
      <Divider
        n="Part 3"
        title="Design: who does what, and what it is made of"
        who="Gourav"
        line="Four use case diagrams and the class diagram, drawn from the code."
      />
    ),
  },
  {
    id: "uc1",
    speaker: "Gourav",
    part: "7 · Use case 1 of 4",
    body: (
      <Diagram
        kicker="Use case diagram 1 of 4"
        title="Student: practise and get feedback"
        note="Submitting always runs the diagnostic tests; a hint is an extension that appears only when one known mistake fits."
      >
        <UseCaseDiagram spec={UC_STUDENT} />
      </Diagram>
    ),
  },
  {
    id: "uc2",
    speaker: "Gourav",
    part: "7 · Use case 2 of 4",
    body: (
      <Diagram
        kicker="Use case diagram 2 of 4"
        title="Researcher: inspect the evidence"
        note="Researchers can also practise. The learner model is researcher-only and every estimate carries its assumption label."
      >
        <UseCaseDiagram spec={UC_RESEARCHER} />
      </Diagram>
    ),
  },
  {
    id: "uc3",
    speaker: "Gourav",
    part: "7 · Use case 3 of 4",
    body: (
      <Diagram
        kicker="Use case diagram 3 of 4"
        title="Administrator: accounts and content"
        note="There is no account-management endpoint in the API. These run from the codeadapt-admin and codeadapt-content command lines."
      >
        <UseCaseDiagram spec={UC_ADMIN} />
      </Diagram>
    ),
  },
  {
    id: "uc4",
    speaker: "Gourav",
    part: "7 · Use case 4 of 4",
    body: (
      <Diagram
        kicker="Use case diagram 4 of 4"
        title="Runner worker: evaluate a submission"
        note="The worker is a system actor. Its use cases run in order for every queued job; the sandbox is the secondary actor."
      >
        <UseCaseDiagram spec={UC_WORKER} />
      </Diagram>
    ),
  },
  {
    id: "classes",
    speaker: "Gourav",
    part: "7 · Class diagram",
    body: (
      <Diagram
        kicker="Detailed class diagram"
        title="The evidence chain, class by class"
        note="White headers: persisted entities (db/models.py). Green: logic classes. Amber: protocols the worker depends on, so a method or sandbox can be swapped."
      >
        <ClassDiagram spec={CLASSES} />
      </Diagram>
    ),
  },
  {
    id: "sd1",
    speaker: "Jasroop",
    part: "7 · Sequence 1 of 5",
    body: (
      <Diagram
        kicker="Sequence diagram 1 of 5"
        title="Log in"
        note="Failed logins are throttled and audited. The cookie is HttpOnly, so page scripts never see the session token."
      >
        <SequenceDiagram spec={SD_LOGIN} />
      </Diagram>
    ),
  },
  {
    id: "sd2",
    speaker: "Jasroop",
    part: "7 · Sequence 2 of 5",
    body: (
      <Diagram
        kicker="Sequence diagram 2 of 5"
        title="Submit a solution"
        note="The API answers 202 at once and never waits for the sandbox. The page polls until the worker has finished."
      >
        <SequenceDiagram spec={SD_SUBMIT} />
      </Diagram>
    ),
  },
  {
    id: "sd3",
    speaker: "Jasroop",
    part: "7 · Sequence 3 of 5",
    body: (
      <Diagram
        kicker="Sequence diagram 3 of 5"
        title="Run and diagnose in the sandbox"
        note="Fingerprints are measured by running each error model, once per content version and environment, then cached."
      >
        <SequenceDiagram spec={SD_EVALUATE} />
      </Diagram>
    ),
  },
  {
    id: "sd4",
    speaker: "Jasroop",
    part: "7 · Sequence 4 of 5",
    body: (
      <Diagram
        kicker="Sequence diagram 4 of 5"
        title="Recommend, then check the follow-up"
        note="Every outcome has an explicit rule. Compile errors, infrastructure failures and timeouts never become evidence about a skill."
      >
        <SequenceDiagram spec={SD_ADAPT} />
      </Diagram>
    ),
  },
  {
    id: "sd5",
    speaker: "Jasroop",
    part: "7 · Sequence 5 of 5",
    body: (
      <Diagram
        kicker="Sequence diagram 5 of 5"
        title="Researcher: trace and learner model"
        note="BKT runs with assumed parameters. It is infrastructure for research, not a validated measure of what anyone knows."
      >
        <SequenceDiagram spec={SD_RESEARCH} />
      </Diagram>
    ),
  },
  {
    id: "status",
    speaker: "Jasroop",
    part: "5 · Status",
    body: (
      <div>
        <Head kicker="5 · Where it stands" title="Complete, limited, next" />
        <div className="s-cols three s-status">
          <section className="s-done">
            <h3>Complete</h3>
            <ul>
              <li>Sandboxed compile and run, per-test containers</li>
              <li>Diagnosis v1.3 with abstention</li>
              <li>Skill-evidence ledger, recommendation policy 1.5, follow-up checks</li>
              <li>Login, roles, CSRF, audit log</li>
              <li>Student workspace and researcher console</li>
              <li>25 problems, all passing content validation</li>
            </ul>
          </section>
          <section className="s-limited">
            <h3>Limited or missing</h3>
            <ul>
              <li>Not yet tried with real students</li>
              <li>
                A named mistake for about 9% of incorrect mutants; the rest get failing cases only
              </li>
              <li>BKT parameters are assumptions</li>
              <li>Skill maps are our own, unvalidated</li>
              <li>Complexity is not checked: a linear scan passes</li>
              <li>gVisor isolation tested in CI only; not deployed</li>
            </ul>
          </section>
          <section className="s-next">
            <h3>Next</h3>
            <ul>
              <li>Host it with the gVisor runner on its own VM</li>
              <li>Test on programs we did not write (public corpus or a consented study)</li>
              <li>Make failing-case feedback the main experience</li>
              <li>Only then: fit BKT on real data</li>
            </ul>
          </section>
        </div>
      </div>
    ),
  },
  {
    id: "numbers",
    speaker: "Jasroop",
    part: "5 · Evidence",
    body: (
      <div className="s-split wide-left">
        <div>
          <Head
            kicker="5 · What our numbers say, and what they don’t"
            title="Measured on programs we wrote or generated"
          />
          <table className="s-table nums">
            <thead>
              <tr>
                <th>Set</th>
                <th>Incorrect programs</th>
                <th>Named</th>
                <th>Named wrongly</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Held-out, author-written</td>
                <td>26</td>
                <td>14</td>
                <td>0</td>
              </tr>
              <tr>
                <td>Single-edit mutants (3 problems)</td>
                <td>323</td>
                <td>30</td>
                <td>0</td>
              </tr>
              <tr>
                <td>Correct held-out programs</td>
                <td className="small">6 correct</td>
                <td colSpan={2} className="small">
                  0 false alarms
                </td>
              </tr>
            </tbody>
          </table>
          <p className="s-fine">Method v1.3. Source: docs/evaluation/summary.md.</p>
        </div>
        <div className="s-caveat">
          <p className="s-why-label">Read with care</p>
          <p>
            None of this is accuracy on real students. Every program was written by us or produced
            mechanically.
          </p>
          <p>
            “0 wrong” rests on small numbers: 0 of 30 still allows an error rate of several percent.
          </p>
          <p>Each version removed wrong names by naming less. We chose that trade on purpose.</p>
        </div>
      </div>
    ),
  },
  {
    id: "team",
    speaker: "All",
    part: "6 · Contributions",
    body: (
      <div>
        <Head kicker="6 · Who did what" title="Each of us can open our own work" />
        <div className="s-cols four">
          {CONTRIBUTIONS.map((c) => (
            <section key={c.name}>
              <h3>{c.name}</h3>
              <ul>
                {c.did.map((d) => (
                  <li key={d}>{d}</li>
                ))}
              </ul>
              <p className={c.evidence ? "s-evidence" : "s-evidence todo"}>
                {c.evidence || "Add links: commits, issues, tests or journal entries"}
              </p>
            </section>
          ))}
        </div>
      </div>
    ),
  },
  {
    id: "end",
    speaker: "All",
    part: "Questions",
    tone: "soil",
    body: (
      <div className="s-title end">
        <p className="s-kicker on-soil">Thank you</p>
        <h1>Questions?</h1>
        <p className="s-title-line">Ask any of us to open the code behind a slide.</p>
        <ul className="s-links">
          <li>
            <span>Repository</span>
            <a href={REPO}>{REPO.replace("https://", "")}</a>
          </li>
          <li>
            <span>Try it</span>
            <a href="/problems">/problems</a>
          </li>
          <li>
            <span>Design docs</span>
            <a href={`${REPO}/tree/claude/project-thread-jn9de7/docs`}>
              docs/architecture.md · docs/limitations.md
            </a>
          </li>
        </ul>
      </div>
    ),
  },
];
