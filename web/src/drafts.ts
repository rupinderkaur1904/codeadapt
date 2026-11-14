/**
 * Per-browser draft storage, scoped to the logged-in account. Best effort only: storage can
 * be unavailable or cleared, and a draft is never the record of a submission.
 *
 * Drafts used to be keyed by problem alone (`codeadapt:draft:<slug>`), so a second account
 * in the same browser opened the first account's code. Keys now carry the username, legacy
 * keys are never read, logging out removes every draft in this browser, and logging in
 * removes drafts that belong to any other account.
 */
const PREFIX = "codeadapt:draft:";
const SCOPED = `${PREFIX}u:`;

const key = (username: string, slug: string) =>
  `${SCOPED}${encodeURIComponent(username)}:${encodeURIComponent(slug)}`;

function storage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function loadDraft(username: string, slug: string): string | null {
  try {
    return storage()?.getItem(key(username, slug)) ?? null;
  } catch {
    return null;
  }
}

export function saveDraft(username: string, slug: string, source: string): void {
  try {
    storage()?.setItem(key(username, slug), source);
  } catch {
    // Ignore: drafts are a convenience, never the record of a submission.
  }
}

function removeWhere(match: (k: string) => boolean): void {
  const store = storage();
  if (store === null) return;
  try {
    const doomed: string[] = [];
    for (let i = 0; i < store.length; i++) {
      const k = store.key(i);
      if (k !== null && match(k)) doomed.push(k);
    }
    for (const k of doomed) store.removeItem(k);
  } catch {
    // Ignore: nothing more can be done without storage.
  }
}

/** Remove every draft in this browser, for any account. Called on logout. */
export function clearAllDrafts(): void {
  removeWhere((k) => k.startsWith(PREFIX));
}

/**
 * Keep only this account's drafts: removes other accounts' drafts (left behind when a
 * session ended without a logout) and unscoped drafts from before this change.
 */
export function clearDraftsExcept(username: string): void {
  const own = `${SCOPED}${encodeURIComponent(username)}:`;
  removeWhere((k) => k.startsWith(PREFIX) && !k.startsWith(own));
}
