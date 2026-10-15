/** Per-browser draft storage. Best effort only: storage can be unavailable or cleared. */
const key = (slug: string) => `codeadapt:draft:${slug}`;

export function loadDraft(slug: string): string | null {
  try {
    return window.localStorage.getItem(key(slug));
  } catch {
    return null;
  }
}

export function saveDraft(slug: string, source: string): void {
  try {
    window.localStorage.setItem(key(slug), source);
  } catch {
    // Ignore: drafts are a convenience, never the record of a submission.
  }
}
