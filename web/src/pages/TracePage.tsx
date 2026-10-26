import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client";
import { ErrorMessage } from "../components/ErrorMessage";

type Row = Record<string, unknown>;

function text(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

function Fields({ row, keys }: { row: Row; keys: string[] }) {
  return (
    <dl className="fields">
      {keys.map((k) => (
        <div key={k}>
          <dt>{k}</dt>
          <dd>{text(row[k])}</dd>
        </div>
      ))}
    </dl>
  );
}

function Raw({ label, value }: { label: string; value: unknown }) {
  return (
    <details>
      <summary>{label}</summary>
      <pre className="compiler-output">{JSON.stringify(value, null, 2)}</pre>
    </details>
  );
}

/** Researcher-only: the full evidence chain behind one submission. */
export function TracePage() {
  const { id = "" } = useParams();
  const trace = useQuery({ queryKey: ["research", "trace", id], queryFn: () => api.trace(id) });
  if (trace.isPending) return <p>Loading trace…</p>;
  if (trace.isError) return <ErrorMessage error={trace.error} />;
  const t = trace.data;
  const diagnosis = t.diagnosis as Row | null;
  const rationale = (diagnosis?.rationale ?? {}) as Row;
  const runs = new Map(t.execution_runs.map((r) => [r.id, String(r.profile)]));
  const validation = t.content_validation as Row | null;
  const recRationale = (t.recommendation?.rationale ?? {}) as Row;
  return (
    <section>
      <p>
        <Link to="/research">← All submissions</Link>
      </p>
      <h1>Submission trace</h1>
      <Fields row={t.submission} keys={["id", "user_id", "data_class", "origin", "created_at"]} />
      <h2>Diagnosis</h2>
      {diagnosis ? (
        <>
          <Fields
            row={diagnosis}
            keys={[
              "method",
              "method_version",
              "outcome",
              "selected_model",
              "candidates",
              "support",
            ]}
          />
          <Fields
            row={rationale}
            keys={[
              "rule",
              "evidence_strength",
              "excluded",
              "supporting_tests",
              "timed_out_tests",
              "consistent_model",
              "uninformative",
              "informative_tests_excluded",
              "contradicting_tests",
              "caveat",
              "note",
            ]}
          />
          <Raw label="Full rationale" value={rationale} />
        </>
      ) : (
        <p className="muted">No diagnosis yet.</p>
      )}
      {t.technique_check && (
        <>
          <h3>Banned library names</h3>
          <dl className="fields">
            <div>
              <dt>banned</dt>
              <dd>{t.technique_check.banned_names.join(", ")}</dd>
            </div>
            <div>
              <dt>found</dt>
              <dd>
                {t.technique_check.found.length ? t.technique_check.found.join(", ") : "none"}
              </dd>
            </div>
            <div>
              <dt>skill evidence</dt>
              <dd>{t.technique_check.skill_evidence}</dd>
            </div>
          </dl>
          <p className="muted">{t.technique_check.note}</p>
        </>
      )}
      <h2>Adaptation</h2>
      {t.recommendation ? (
        <>
          <Fields
            row={t.recommendation}
            keys={["rule", "action", "problem_slug", "target_skills", "criterion", "review_flag"]}
          />
          <Fields row={recRationale} keys={["qualified_hypothesis", "known_limitation"]} />
          {recRationale.qualified_hypothesis === true && (
            <p className="muted">
              Qualified hypothesis: the evidence is weak (one behaviour group) or the model has a
              documented limitation, so the specific error is not presented as established.
            </p>
          )}
        </>
      ) : (
        <p className="muted">No recommendation was made after this submission.</p>
      )}
      {t.followup_evaluation && (
        <>
          <h3>Follow-up evaluation (this submission as the follow-up)</h3>
          <Fields
            row={t.followup_evaluation}
            keys={["verdict", "reason", "passed", "failed", "excluded", "probes"]}
          />
        </>
      )}
      <h2>Observations</h2>
      <table className="tests">
        <thead>
          <tr>
            <th>Build</th>
            <th>Test</th>
            <th>Run</th>
            <th>Signature</th>
            <th>Excluded because</th>
            <th>Wall ms</th>
          </tr>
        </thead>
        <tbody>
          {t.observations.map((o) => (
            <tr key={String(o.id)}>
              <td>{runs.get(o.run_id) ?? "?"}</td>
              <td>{text(o.test_key)}</td>
              <td>{text(o.repeat_index)}</td>
              <td>
                {text(o.signature_kind)}
                {o.signature_detail ? `: ${text(o.signature_detail)}` : ""}
              </td>
              <td>{text(o.excluded_reason)}</td>
              <td>{text(o.wall_ms)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h2>Provenance</h2>
      {validation && <Fields row={validation} keys={["problem_version", "errors", "warnings"]} />}
      <Raw label="Environment" value={t.environment} />
      <Raw label="Execution runs" value={t.execution_runs} />
      <Raw label="Job" value={t.job} />
    </section>
  );
}
