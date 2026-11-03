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
import fbCorrect from "./shots/fb-correct_iterative.png";
import fbDouble from "./shots/fb-double_bug.png";
import fbEarly from "./shots/fb-recursive_early_equal.png";
import fbStuck from "./shots/fb-size_t_stuck_left.png";
import shotLearner from "./shots/learner.png";
import shotPractice from "./shots/practice.png";
import shotProblems from "./shots/problems.png";
import shotResearch from "./shots/research.png";
import shotTrace from "./shots/trace.png";
import { ClassDiagram, SequenceDiagram, UseCaseDiagram } from "./uml";

export type Speaker = "Rupinder" | "Ashmeen" | "Gourav" | "Jasroop" | "All";

export type Slide = {
  id: string;
  speaker: Speaker;
  title: string;
  body: ReactNode;
};

export const TEAM: Exclude<Speaker, "All">[] = ["Rupinder", "Ashmeen", "Gourav", "Jasroop"];

// Each member's part: what they present and answer questions on, and the files they open
// if asked to find the code. Kept the same size for everyone.
const CONTRIBUTIONS: { name: string; part: string; files: string }[] = [
  {
    name: "Rupinder",
    part: "Problem, users and user journey; landing page and problem list",
    files: "LandingPage.tsx, ProblemListPage.tsx, App.tsx",
  },
  {
    name: "Ashmeen",
    part: "Live demo, worker pipeline and sandbox, system architecture",
    files: "worker/pipeline.py, execution/docker.py, db/queue.py",
  },
  {
    name: "Gourav",
    part: "Integration, diagnosis method, use case and class diagrams",
    files: "diagnosis/fingerprint_v1.py, db/models.py, diagrams.tsx",
  },
  {
    name: "Jasroop",
    part: "Login, recommendations, sequence diagrams, status and evaluation",
    files: "auth/, adaptation/policy_v1.py, docs/limitations.md",
  },
];

const SHOT_NOTE =
  "Screenshots of the running system, taken on 3 November 2026 with test accounts and our own test programs.";

function Shot({ src, label, maxHeight }: { src: string; label: string; maxHeight: number }) {
  return (
    <figure className="s-shot">
      <img src={src} alt={label} style={{ maxHeight }} />
      <figcaption>{label}</figcaption>
    </figure>
  );
}

const REPO = "https://github.com/rupinderkaur1904/codeadapt";

function Page({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="s-page">
      <h2 className="s-title-bar">{title}</h2>
      <div className="s-content">{children}</div>
    </div>
  );
}

function Figure({ title, note, children }: { title: string; note?: string; children: ReactNode }) {
  return (
    <Page title={title}>
      <div className="s-figure">{children}</div>
      {note && <p className="s-caption">{note}</p>}
    </Page>
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
      {done ? "Copied" : "Copy"}
    </button>
  );
}

function DemoKit() {
  const [open, setOpen] = useState(0);
  const p = DEMO_PROGRAMS[open];
  if (!p) return null;
  return (
    <div className="s-demo">
      <div>
        <p className="s-text">
          We submit four prepared lower-bound programs in the running system and compare the
          feedback.
        </p>
        <table className="s-table s-demo-table">
          <thead>
            <tr>
              <th>Program</th>
              <th>Expected outcome</th>
            </tr>
          </thead>
          <tbody>
            {DEMO_PROGRAMS.map((d, i) => (
              <tr key={d.file} className={i === open ? "on" : undefined} onClick={() => setOpen(i)}>
                <td>
                  {i + 1}. {d.intent}
                  <br />
                  <span className="s-small">{d.file}</span>
                </td>
                <td className="s-mono">{d.expect}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="s-small">
          Test programs are taken from eval/heldout/lower-bound. We wrote them; they are not student
          submissions.
        </p>
        <a className="s-button" href="/problems" target="_blank" rel="noreferrer">
          Open CodeAdapt
        </a>
      </div>
      <div className="s-code">
        <div className="s-code-bar">
          <span>{p.file}</span>
          <CopyButton text={p.source} />
        </div>
        <pre>
          <code>{p.source}</code>
        </pre>
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
        Runner side (only part with Docker access)
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
    title: "Title",
    body: (
      <div className="s-cover">
        <h1>CodeAdapt</h1>
        <p className="s-cover-sub">An adaptive C++ practice platform with diagnostic feedback</p>
        <div className="s-cover-rule" />
        <p className="s-cover-team">Rupinder · Ashmeen · Gourav · Jasroop</p>
        <p className="s-small">Project presentation, November 2026</p>
      </div>
    ),
  },
  {
    id: "problem",
    speaker: "Rupinder",
    title: "Problem statement",
    body: (
      <Page title="Problem statement">
        <div className="s-two">
          <ul className="s-list">
            <li>Most online judges only report pass or fail for each test.</li>
            <li>
              A beginner sees <em>Wrong Answer on test 7</em> but not which idea in the code is
              wrong.
            </li>
            <li>Students then change the code by trial and error until it passes.</li>
            <li>
              Tools that guess the cause can be wrong, because different mistakes can give the same
              output.
            </li>
          </ul>
          <div className="s-box">
            <p className="s-box-title">What a student needs to know</p>
            <ol className="s-list">
              <li>Which input breaks the code</li>
              <li>Whether it matches one known mistake</li>
              <li>What to practise next</li>
            </ol>
          </div>
        </div>
      </Page>
    ),
  },
  {
    id: "users",
    speaker: "Rupinder",
    title: "Target users and motivation",
    body: (
      <Page title="Target users and motivation">
        <div className="s-two">
          <div>
            <h3>Intended users</h3>
            <ul className="s-list">
              <li>
                <strong>Students</strong> learning algorithms in C++ (first data-structures course)
              </li>
              <li>
                <strong>Researchers and instructors</strong> who want to see how errors appear in
                submissions
              </li>
              <li>
                <strong>Administrator</strong> who manages accounts and problem content
              </li>
            </ul>
          </div>
          <div>
            <h3>Why we chose this problem</h3>
            <ul className="s-list">
              <li>Binary search is short but easy to get wrong by one position.</li>
              <li>
                The lower-bound problem has 8 known mistakes and 17 tests designed to tell them
                apart.
              </li>
              <li>The problem bank now has 25 problems in 5 topic families.</li>
            </ul>
          </div>
        </div>
      </Page>
    ),
  },
  {
    id: "solution",
    speaker: "Rupinder",
    title: "Proposed solution",
    body: (
      <Page title="Proposed solution">
        <ol className="s-flow">
          {[
            "Submit code",
            "Run tests in a sandbox",
            "Compare with known mistakes",
            "Give feedback",
            "Recommend next problem",
            "Check next attempt",
          ].map((t) => (
            <li key={t}>{t}</li>
          ))}
        </ol>
        <h3>Design decisions</h3>
        <ul className="s-list">
          <li>Test results are stored first and never changed; every diagnosis refers to them.</li>
          <li>
            A mistake is named only if exactly one known mistake matches. Otherwise the student just
            sees the failing cases.
          </li>
          <li>Feedback describes the program (&ldquo;behaves as if&rdquo;), not the student.</li>
        </ul>
      </Page>
    ),
  },
  {
    id: "journey",
    speaker: "Rupinder",
    title: "Main user journey",
    body: (
      <Page title="Main user journey">
        <div className="s-two">
          <div>
            <h3>Student</h3>
            <ol className="s-list">
              <li>Open the landing page and log in</li>
              <li>Choose a problem from the problem list</li>
              <li>Write C++ code in the editor and submit</li>
              <li>Read the result: failing cases, and a hint if one mistake matches</li>
              <li>Follow the recommended next problem</li>
              <li>Review earlier attempts under My attempts</li>
            </ol>
          </div>
          <div>
            <h3>Researcher</h3>
            <ol className="s-list">
              <li>Browse submissions and outcome counts</li>
              <li>Open the evidence trace of one submission</li>
              <li>
                View a learner&apos;s skill estimates, labelled &ldquo;estimated under assumed
                parameters&rdquo;
              </li>
            </ol>
          </div>
        </div>
      </Page>
    ),
  },
  {
    id: "student-screens",
    speaker: "Rupinder",
    title: "The student's screens",
    body: (
      <Page title="The student's screens">
        <div className="s-shots s-shots-2">
          <Shot src={shotPractice} label="Practice page after a submission" maxHeight={480} />
          <Shot src={shotProblems} label="Problem list, grouped by family" maxHeight={480} />
        </div>
        <p className="s-caption">{SHOT_NOTE}</p>
      </Page>
    ),
  },
  {
    id: "demo",
    speaker: "Ashmeen",
    title: "Live demo",
    body: (
      <Page title="Live demo">
        <DemoKit />
      </Page>
    ),
  },
  {
    id: "results",
    speaker: "Ashmeen",
    title: "The four demo results",
    body: (
      <Page title="The four demo results">
        <div className="s-shots s-shots-4">
          <Shot src={fbCorrect} label="1. Correct: all 17 tests pass" maxHeight={185} />
          <Shot
            src={fbEarly}
            label="2. One known mistake fits: named, with a hint"
            maxHeight={185}
          />
          <Shot src={fbDouble} label="3. Two mistakes: failing cases, no guess" maxHeight={185} />
          <Shot src={fbStuck} label="4. Loop never ends: reported as a time-out" maxHeight={185} />
        </div>
        <p className="s-caption">{SHOT_NOTE}</p>
      </Page>
    ),
  },
  {
    id: "architecture",
    speaker: "Ashmeen",
    title: "System architecture",
    body: (
      <Figure
        title="System architecture"
        note="The API never runs student code. It stores a job, and a separate worker runs it in the sandbox."
      >
        <Architecture />
      </Figure>
    ),
  },
  {
    id: "contracts",
    speaker: "Gourav",
    title: "Integration between components",
    body: (
      <Page title="Integration between components">
        <table className="s-table">
          <thead>
            <tr>
              <th>Between</th>
              <th>What is exchanged</th>
              <th>How</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Web app and API</td>
              <td>JSON requests under /api/v1</td>
              <td>TypeScript types generated from the OpenAPI schema</td>
            </tr>
            <tr>
              <td>Authentication</td>
              <td>Session cookie and CSRF token</td>
              <td>Argon2id password hashes, login throttling, audit log</td>
            </tr>
            <tr>
              <td>API and database</td>
              <td>Submissions, jobs, results</td>
              <td>SQLAlchemy and Alembic migrations, PostgreSQL 16</td>
            </tr>
            <tr>
              <td>Database and worker</td>
              <td>Queued jobs</td>
              <td>The worker claims a job with a lease so no two workers take it</td>
            </tr>
            <tr>
              <td>Worker and sandbox</td>
              <td>Code and test input, output and timing</td>
              <td>New Docker container per test, no network, resource limits</td>
            </tr>
          </tbody>
        </table>
        <p className="s-small">
          Tests at the last release: 609 backend unit tests, 39 sandbox tests, 37 web component
          tests, 3 browser end-to-end tests.
        </p>
      </Page>
    ),
  },
  {
    id: "matrix",
    speaker: "Gourav",
    title: "How the diagnosis works",
    body: (
      <Page title="How the diagnosis works">
        <div className="s-two">
          <div>
            <ul className="s-list">
              <li>Each known mistake is written as a real program.</li>
              <li>We run it on every test and save its outputs. We call this its fingerprint.</li>
              <li>The student&apos;s outputs are compared with every fingerprint.</li>
            </ul>
            <table className="s-table s-outcomes">
              <tbody>
                <tr>
                  <td>One fingerprint matches</td>
                  <td>the mistake is named, with a hint</td>
                </tr>
                <tr>
                  <td>Several match</td>
                  <td>ambiguous, nothing is named</td>
                </tr>
                <tr>
                  <td>None match</td>
                  <td>unmodelled, failing cases only</td>
                </tr>
                <tr>
                  <td>Time limit reached</td>
                  <td>reported as &ldquo;did not finish&rdquo;</td>
                </tr>
              </tbody>
            </table>
          </div>
          <figure className="s-matrix-fig">
            <Matrix />
            <figcaption className="s-small">
              Simplified example: only model B matches the submission on every test.
            </figcaption>
          </figure>
        </div>
      </Page>
    ),
  },
  {
    id: "uc1",
    speaker: "Gourav",
    title: "Use case diagram 1: Student",
    body: (
      <Figure title="Use case diagram 1: Student">
        <UseCaseDiagram spec={UC_STUDENT} />
      </Figure>
    ),
  },
  {
    id: "uc2",
    speaker: "Gourav",
    title: "Use case diagram 2: Researcher",
    body: (
      <Figure title="Use case diagram 2: Researcher">
        <UseCaseDiagram spec={UC_RESEARCHER} />
      </Figure>
    ),
  },
  {
    id: "uc3",
    speaker: "Gourav",
    title: "Use case diagram 3: Administrator",
    body: (
      <Figure title="Use case diagram 3: Administrator">
        <UseCaseDiagram spec={UC_ADMIN} />
      </Figure>
    ),
  },
  {
    id: "uc4",
    speaker: "Gourav",
    title: "Use case diagram 4: Runner worker",
    body: (
      <Figure title="Use case diagram 4: Runner worker">
        <UseCaseDiagram spec={UC_WORKER} />
      </Figure>
    ),
  },
  {
    id: "classes",
    speaker: "Gourav",
    title: "Class diagram",
    body: (
      <Figure title="Class diagram">
        <ClassDiagram spec={CLASSES} />
      </Figure>
    ),
  },
  {
    id: "sd1",
    speaker: "Jasroop",
    title: "Sequence diagram 1: Login",
    body: (
      <Figure title="Sequence diagram 1: Login">
        <SequenceDiagram spec={SD_LOGIN} />
      </Figure>
    ),
  },
  {
    id: "sd2",
    speaker: "Jasroop",
    title: "Sequence diagram 2: Submit a solution",
    body: (
      <Figure title="Sequence diagram 2: Submit a solution">
        <SequenceDiagram spec={SD_SUBMIT} />
      </Figure>
    ),
  },
  {
    id: "sd3",
    speaker: "Jasroop",
    title: "Sequence diagram 3: Run and diagnose",
    body: (
      <Figure title="Sequence diagram 3: Run and diagnose">
        <SequenceDiagram spec={SD_EVALUATE} />
      </Figure>
    ),
  },
  {
    id: "sd4",
    speaker: "Jasroop",
    title: "Sequence diagram 4: Recommendation",
    body: (
      <Figure title="Sequence diagram 4: Recommendation">
        <SequenceDiagram spec={SD_ADAPT} />
      </Figure>
    ),
  },
  {
    id: "sd5",
    speaker: "Jasroop",
    title: "Sequence diagram 5: Researcher view",
    body: (
      <Figure title="Sequence diagram 5: Researcher view">
        <SequenceDiagram spec={SD_RESEARCH} />
      </Figure>
    ),
  },
  {
    id: "research-screens",
    speaker: "Jasroop",
    title: "The researcher's screens",
    body: (
      <Page title="The researcher's screens">
        <div className="s-shots s-shots-2">
          <Shot src={shotResearch} label="Submissions and outcome counts" maxHeight={480} />
          <div className="s-shots">
            <Shot src={shotTrace} label="Evidence trace of one submission" maxHeight={170} />
            <Shot
              src={shotLearner}
              label="Learner model, under assumed parameters"
              maxHeight={170}
            />
          </div>
        </div>
        <p className="s-caption">{SHOT_NOTE}</p>
      </Page>
    ),
  },
  {
    id: "status",
    speaker: "Jasroop",
    title: "Current status",
    body: (
      <Page title="Current status">
        <div className="s-three">
          <div>
            <h3>Completed</h3>
            <ul className="s-list">
              <li>Sandboxed compile and run</li>
              <li>Diagnosis with abstention</li>
              <li>Recommendations and follow-up checks</li>
              <li>Login and roles</li>
              <li>Student and researcher interfaces</li>
              <li>25 validated problems</li>
            </ul>
          </div>
          <div>
            <h3>Limitations</h3>
            <ul className="s-list">
              <li>Not yet used by real students</li>
              <li>Names a mistake for about 9% of our incorrect test programs</li>
              <li>Learner model uses assumed parameters</li>
              <li>Time complexity is not checked</li>
              <li>Not deployed yet</li>
            </ul>
          </div>
          <div>
            <h3>Next steps</h3>
            <ul className="s-list">
              <li>Deploy with a separate, isolated runner</li>
              <li>Test on programs written by other people</li>
              <li>Improve the feedback for failing cases</li>
              <li>Fit the learner model on real data</li>
            </ul>
          </div>
        </div>
      </Page>
    ),
  },
  {
    id: "numbers",
    speaker: "Jasroop",
    title: "Evaluation results",
    body: (
      <Page title="Evaluation results">
        <table className="s-table">
          <thead>
            <tr>
              <th>Test set</th>
              <th>Incorrect programs</th>
              <th>Mistake named</th>
              <th>Named wrongly</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Held-out programs written by us</td>
              <td>26</td>
              <td>14</td>
              <td>0</td>
            </tr>
            <tr>
              <td>Generated single-edit programs (3 problems)</td>
              <td>323</td>
              <td>30</td>
              <td>0</td>
            </tr>
          </tbody>
        </table>
        <p className="s-text">All 6 correct held-out programs passed with no false alarm.</p>
        <ul className="s-list s-note-list">
          <li>
            These programs were written or generated by us, so this is not accuracy on real
            students.
          </li>
          <li>
            The samples are small: 0 wrong out of 30 still allows a real error rate of a few
            percent.
          </li>
        </ul>
      </Page>
    ),
  },
  {
    id: "team",
    speaker: "All",
    title: "Team contributions",
    body: (
      <Page title="Team contributions">
        <table className="s-table">
          <thead>
            <tr>
              <th>Member</th>
              <th>Part they are responsible for</th>
              <th>Where to find it</th>
            </tr>
          </thead>
          <tbody>
            {CONTRIBUTIONS.map((c) => (
              <tr key={c.name}>
                <td>{c.name}</td>
                <td>{c.part}</td>
                <td className="s-mono">{c.files}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Page>
    ),
  },
  {
    id: "end",
    speaker: "All",
    title: "Thank you",
    body: (
      <div className="s-cover">
        <h1>Thank you</h1>
        <p className="s-cover-sub">Questions?</p>
        <div className="s-cover-rule" />
        <p className="s-text">Repository: {REPO.replace("https://", "")}</p>
        <p className="s-text">Documentation: docs/architecture.md, docs/limitations.md</p>
      </div>
    ),
  },
];
