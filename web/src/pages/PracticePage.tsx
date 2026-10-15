import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import Markdown from "react-markdown";
import { useParams } from "react-router-dom";

import { api, isFinished } from "../api/client";
import { AttemptHistory } from "../components/AttemptHistory";
import { CodeEditor } from "../components/CodeEditor";
import { ErrorMessage } from "../components/ErrorMessage";
import { RECOMMENDATION_KEY, RecommendationCard } from "../components/RecommendationCard";
import { SubmissionResult } from "../components/SubmissionResult";
import { loadDraft, saveDraft } from "../drafts";

export const POLL_MS = 1000;

export function PracticePage() {
  const { slug = "" } = useParams();
  const problem = useQuery({ queryKey: ["problem", slug], queryFn: () => api.getProblem(slug) });
  if (problem.isPending) return <p>Loading problem…</p>;
  if (problem.isError) return <ErrorMessage error={problem.error} />;
  return (
    <Workspace
      key={problem.data.version}
      slug={slug}
      title={problem.data.title}
      statement={problem.data.statement}
      starter={problem.data.starter_code}
    />
  );
}

function Workspace(props: { slug: string; title: string; statement: string; starter: string }) {
  const { slug } = props;
  const queryClient = useQueryClient();
  const [source, setSource] = useState(() => loadDraft(slug) ?? props.starter);
  const [selectedId, setSelectedId] = useState<string | null>(null);

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

  return (
    <div className="workspace">
      <section className="statement">
        <h1>{props.title}</h1>
        <Markdown>{props.statement}</Markdown>
      </section>
      <section className="editor">
        <CodeEditor
          value={source}
          onChange={(value) => {
            setSource(value);
            saveDraft(slug, value);
          }}
        />
        <div className="actions">
          <button type="button" onClick={() => submit.mutate()} disabled={pending}>
            {pending ? "Evaluating…" : "Submit"}
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() => {
              setSource(props.starter);
              saveDraft(slug, props.starter);
            }}
          >
            Reset to starter code
          </button>
        </div>
        {submit.isError && <ErrorMessage error={submit.error} />}
        {selected.isError && <ErrorMessage error={selected.error} />}
        {selected.data && <SubmissionResult submission={selected.data} />}
        {finished && <RecommendationCard currentSlug={slug} />}
        <h2>Your attempts</h2>
        {history.isError ? (
          <ErrorMessage error={history.error} />
        ) : (
          <AttemptHistory
            attempts={history.data ?? []}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        )}
      </section>
    </div>
  );
}
