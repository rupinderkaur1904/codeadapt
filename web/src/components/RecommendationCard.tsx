import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api } from "../api/client";

export const RECOMMENDATION_KEY = ["recommendation"] as const;

/** Shown when adaptation failed after the latest attempt (D6, owner decision 2026-11-07). */
export const ADAPTATION_FALLBACK =
  "We couldn't prepare your next recommended problem right now. Please try again in a moment.";

/** "Recommended next" from the adaptive policy, plus the verdict on the last follow-up. */
export function RecommendationCard({ currentSlug }: { currentSlug?: string }) {
  const queryClient = useQueryClient();
  const next = useQuery({ queryKey: RECOMMENDATION_KEY, queryFn: api.myRecommendation });
  const retry = useMutation({
    mutationFn: api.retryRecommendation,
    onSuccess: (data) => queryClient.setQueryData(RECOMMENDATION_KEY, data),
  });
  if (!next.data) return null;
  if (next.data.adaptation_unavailable) {
    // Never show a recommendation or verdict made before the latest attempt.
    return (
      <aside className="recommendation" aria-label="Recommended next">
        <p role="status">{ADAPTATION_FALLBACK}</p>
        <button type="button" onClick={() => retry.mutate()} disabled={retry.isPending}>
          {retry.isPending ? "Trying again…" : "Try again"}
        </button>
      </aside>
    );
  }
  const { recommendation: rec, last_followup: followup } = next.data;
  if (!rec && !followup) return null;
  return (
    <aside className="recommendation" aria-label="Recommended next">
      {followup && <p className={`followup followup-${followup.verdict}`}>{followup.message}</p>}
      {rec && (
        <>
          <h2>Recommended next</h2>
          <p>{rec.message}</p>
          {rec.focus.length > 0 && (
            <>
              <p className="muted">Focus:</p>
              <ul>
                {rec.focus.map((f) => (
                  <li key={f}>{f}</li>
                ))}
              </ul>
            </>
          )}
          {rec.problem_slug &&
            (rec.problem_slug === currentSlug ? (
              <p className="muted">This is the problem you are on.</p>
            ) : (
              <Link to={`/practice/${rec.problem_slug}`}>Go to {rec.problem_title}</Link>
            ))}
        </>
      )}
    </aside>
  );
}
