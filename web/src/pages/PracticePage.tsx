import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type CSSProperties, useEffect, useRef, useState } from "react";
import Markdown from "react-markdown";
import { useParams, useSearchParams } from "react-router-dom";

import { api, isFinished, type ProblemDetail } from "../api/client";
import { AttemptHistory } from "../components/AttemptHistory";
import { CodeEditor } from "../components/CodeEditor";
import { ErrorMessage } from "../components/ErrorMessage";
import { RECOMMENDATION_KEY, RecommendationCard } from "../components/RecommendationCard";
import { ResizeHandle, useSplit } from "../components/ResizeHandle";
import { SubmissionResult } from "../components/SubmissionResult";
import { clearDraftsExcept, loadDraft, saveDraft } from "../drafts";

export const POLL_MS = 1000;

/** `username` scopes the locally saved draft, so one account never opens another's code. */
export function PracticePage({ username }: { username: string }) {
  const { slug = "" } = useParams();
  const problem = useQuery({ queryKey: ["problem", slug], queryFn: () => api.getProblem(slug) });
  if (problem.isPending) {
    return (
      <p className="page-state muted" role="status">
        Loading problem…
      </p>
    );
  }
  if (problem.isError) {
    return (
      <div className="page-state">
        <ErrorMessage error={problem.error} />
      </div>
    );
  }
  return (
    <Workspace
      key={`${username}\n${problem.data.version}`}
      username={username}
      slug={slug}
      problem={problem.data}
    />
  );
}

function ProblemPanel({ problem }: { problem: ProblemDetail }) {
  const samples = problem.sample_tests;
  return (
    <section className="panel problem-panel" aria-labelledby="problem-title">
      <header className="panel-header problem-header">
        <p className="eyebrow">Problem</p>
        <h1 id="problem-title">{problem.title}</h1>
      </header>
      <div className="panel-body problem-body">
        <div className="statement-text">
          <Markdown>{problem.statement}</Markdown>
        </div>
        {samples.length > 0 && (
          <section className="samples" aria-labelledby="samples-title">
            <h2 id="samples-title">Sample tests</h2>
            <p className="muted samples-note">
              These visible cases run with every submission. Your results show your output for each
              of them.
            </p>
            <ol className="sample-list">
              {samples.map((s, i) => (
                <li key={i} className="sample-case">
                  <p className="sample-title">
                    <span className="sample-number">Sample {i + 1}</span>
                    {s.description}
                  </p>
                  <dl className="io-grid">
                    <dt>Input</dt>
                    <dd>
                      <code>{s.input}</code>
                    </dd>
                    <dt>Expected</dt>
                    <dd>
                      <code>{s.expected_output}</code>
                    </dd>
                  </dl>
                </li>
              ))}
            </ol>
          </section>
        )}
      </div>
    </section>
  );
}

function Workspace(props: { username: string; slug: string; problem: ProblemDetail }) {
  const { username, slug, problem } = props;
  const starter = problem.starter_code;
  const queryClient = useQueryClient();
  const [source, setSource] = useState(() => {
    clearDraftsExcept(username);
    return loadDraft(username, slug) ?? starter;
  });
  // "My attempts" links here with ?attempt=<id> to open that attempt's result.
  const [params] = useSearchParams();
  const [selectedId, setSelectedId] = useState<string | null>(() => params.get("attempt"));
  const [split, setSplit] = useSplit();
  const layout = useRef<HTMLDivElement>(null);
  const results = useRef<HTMLElement>(null);

  const history = useQuery({
    queryKey: ["submissions", slug],
    queryFn: () => api.listSubmissions(slug),
  });

  const selected = useQuery({
    queryKey: ["submission", selectedId],
    queryFn: () => api.getSubmission(selectedId ?? ""),
    enabled: selectedId !== null,
    refetchInterval: (query) =>
      query.state.data && isFinished(query.state.data) ? false : POLL_MS,
  });

  const submit = useMutation({
    mutationFn: () => api.submit(slug, source),
    onSuccess: async (accepted) => {
      setSelectedId(accepted.id);
      results.current?.scrollIntoView?.({ block: "nearest", behavior: "smooth" });
      await queryClient.invalidateQueries({ queryKey: ["submissions", slug] });
    },
  });

  const finished = selected.data !== undefined && isFinished(selected.data);
  useEffect(() => {
    // When the selected attempt finishes, refresh the history so its summary updates.
    // The worker records the next recommendation before it marks the attempt finished.
    if (!finished) return;
    void queryClient.invalidateQueries({ queryKey: ["submissions", slug] });
    void queryClient.invalidateQueries({ queryKey: RECOMMENDATION_KEY });
  }, [finished, queryClient, slug]);

  const pending = submit.isPending || (selected.data !== undefined && !finished);
  const atStarter = source === starter;
  const attemptCount = history.data?.length;

  const runSubmit = () => {
    if (!pending) submit.mutate();
  };

  return (
    <div
      className="workspace"
      ref={layout}
      style={{ "--problem-width": `${(split * 100).toFixed(1)}%` } as CSSProperties}
    >
      <ProblemPanel problem={problem} />
      <ResizeHandle container={layout} ratio={split} onChange={setSplit} />
      <div className="work-column">
        <section className="panel editor-panel" aria-label="Code editor">
          <div className="editor-toolbar">
            <span className="lang-badge" title="Solutions are compiled as C++">
              C++
            </span>
            <div className="toolbar-actions">
              <button
                type="button"
                className="ghost"
                disabled={atStarter}
                onClick={() => {
                  setSource(starter);
                  saveDraft(username, slug, starter);
                }}
              >
                Reset to starter code
              </button>
              <button
                type="button"
                className="primary"
                onClick={runSubmit}
                disabled={pending}
                title="Submit (Ctrl+Enter)"
              >
                {pending ? "Evaluating…" : "Submit"}
              </button>
            </div>
          </div>
          <div
            className="editor-surface"
            onKeyDownCapture={(e) => {
              if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                e.stopPropagation();
                runSubmit();
              }
            }}
          >
            <CodeEditor
              value={source}
              onChange={(value) => {
                setSource(value);
                saveDraft(username, slug, value);
              }}
            />
          </div>
          <p className="editor-footer muted">
            <span>Submit runs every test, including hidden ones, and records an attempt.</span>
            <span className="shortcut">
              <kbd>Ctrl</kbd> + <kbd>Enter</kbd>
            </span>
          </p>
        </section>

        <section className="panel results-panel" aria-labelledby="results-title" ref={results}>
          <header className="panel-header results-header">
            <h2 id="results-title">Submission result</h2>
          </header>
          <div className="panel-body">
            {submit.isError && <ErrorMessage error={submit.error} />}
            {selected.isError && <ErrorMessage error={selected.error} />}
            {selected.data ? (
              <SubmissionResult submission={selected.data} />
            ) : (
              !submit.isPending &&
              !selected.isFetching && (
                <p className="empty-state">
                  No submission selected. Submit your solution to see test results and feedback
                  here.
                </p>
              )
            )}
            {submit.isPending && !selected.data && (
              <p className="run-status run-status-pending" role="status">
                <span className="status-dot" aria-hidden="true" />
                Sending your code…
              </p>
            )}
            {finished && <RecommendationCard currentSlug={slug} />}
          </div>
        </section>

        <section className="panel attempts-panel" aria-labelledby="attempts-title">
          <header className="panel-header">
            <h2 id="attempts-title">
              Your attempts
              {attemptCount !== undefined && attemptCount > 0 && (
                <span className="count-pill">{attemptCount}</span>
              )}
            </h2>
          </header>
          <div className="panel-body">
            {history.isError ? (
              <ErrorMessage error={history.error} />
            ) : history.isPending ? (
              <p className="muted">Loading attempts…</p>
            ) : (
              <AttemptHistory
                attempts={history.data}
                selectedId={selectedId}
                onSelect={setSelectedId}
              />
            )}
            <details className="how-feedback">
              <summary>How feedback works</summary>
              <p>
                Your code runs on tests designed to separate common mistakes. When tests fail, you
                see which cases failed. A hint about the likely mistake appears only when the
                failing cases match one known mistake; otherwise you get the cases to compare,
                without a guess.
              </p>
            </details>
          </div>
        </section>
      </div>
    </div>
  );
}
