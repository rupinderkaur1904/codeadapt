import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { api, type LearnerModelView } from "../api/client";
import { ErrorMessage } from "../components/ErrorMessage";

type SkillEstimate = LearnerModelView["estimate"]["skills"][number];
type RetiredSkill = LearnerModelView["retired_skills"][string];

function SkillCard({
  skill,
  label,
  retired,
}: {
  skill: SkillEstimate;
  label: string;
  retired?: RetiredSkill;
}) {
  return (
    <section aria-label={skill.skill}>
      <h2>
        {skill.skill}
        {retired && <span className="badge">deprecated</span>}
      </h2>
      {retired && (
        <p className="muted">
          Retired on {retired.retired} ({retired.decision}); replaced by{" "}
          {retired.replaced_by.join(", ")}. These observations keep the key's historical meaning:{" "}
          <em>{retired.definition}</em> They were recorded on older content versions and are not
          converted to the new keys.
        </p>
      )}
      <p>
        {skill.state === "estimated" && skill.p_known !== null && skill.p_known !== undefined ? (
          <>
            P(known) = <strong>{skill.p_known.toFixed(3)}</strong> ({label})
          </>
        ) : (
          <>Insufficient data: no estimate is shown.</>
        )}{" "}
        {skill.counted} counted observation(s) from {skill.distinct_problems} problem(s).
      </p>
      <table className="tests">
        <thead>
          <tr>
            <th>Submission</th>
            <th>Problem</th>
            <th>Version</th>
            <th>Value</th>
            <th>Counted</th>
            <th>P(known) after</th>
          </tr>
        </thead>
        <tbody>
          {skill.observations.map((t) => (
            <tr key={t.observation.submission_id}>
              <td>
                <Link to={`/research/submissions/${t.observation.submission_id}`}>
                  {new Date(t.observation.created_at).toLocaleString()}
                </Link>
              </td>
              <td>{t.observation.problem_slug}</td>
              <td>{t.observation.problem_version ?? "—"}</td>
              <td title={t.observation.basis}>{t.observation.value}</td>
              <td>{t.counted ? "yes" : `no (${t.reason ?? ""})`}</td>
              <td>
                {t.p_known_after !== null && t.p_known_after !== undefined
                  ? t.p_known_after.toFixed(3)
                  : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

/** Researcher-only: LM1 knowledge-tracing estimates for one learner (ADR-025). */
export function LearnerModelPage() {
  const { username = "" } = useParams();
  const model = useQuery({
    queryKey: ["research", "learner-model", username],
    queryFn: () => api.learnerModel(username),
  });
  if (model.isError) return <ErrorMessage error={model.error} />;
  if (!model.data) return <p>Loading…</p>;
  const { estimate } = model.data;
  return (
    <section>
      <p>
        <Link to="/research">Back to research</Link>
      </p>
      <h1>Learner model: {model.data.username}</h1>
      <p className="muted">
        {estimate.model} {estimate.model_version}, parameter set {estimate.parameter_set}. Values
        are <strong>{estimate.label}</strong>; they are not fitted, calibrated or validated, are not
        shown to the learner and do not affect recommendations. Data class {model.data.data_class};{" "}
        {model.data.attempts} diagnosed attempt(s). No estimate is shown below{" "}
        {estimate.min_observations} counted observations from {estimate.min_problems} problems; that
        threshold is for display only and says nothing about accuracy.
      </p>
      <details>
        <summary>Model assumptions</summary>
        <ul>
          {estimate.assumptions.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      </details>
      {estimate.skills.length === 0 && <p className="muted">No skill observations yet.</p>}
      {estimate.skills.map((s) => (
        <SkillCard
          key={s.skill}
          skill={s}
          label={estimate.label}
          retired={model.data.retired_skills[s.skill]}
        />
      ))}
    </section>
  );
}
