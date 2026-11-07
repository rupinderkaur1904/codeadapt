import { type FormEvent, useState } from "react";

import { ApiError, api, setCsrfToken } from "../api/client";

function message(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 403 && error.type.endsWith("/wrong-password")) {
      return "Your current password is wrong.";
    }
    if (error.status === 422) return "The new password must have at least 12 characters.";
    if (error.status === 429) return "Too many failed attempts. Wait a few minutes and try again.";
    if (error.status === 401) return "Your session ended. Log in again.";
  }
  return "Could not change the password. Try again.";
}

/** Self-service password change (ADR-041). Every other session of the account ends. */
export function AccountPage({ username }: { username: string }) {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [repeat, setRepeat] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setDone(false);
    if (next !== repeat) {
      setError("The two new passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      const user = await api.changePassword(current, next);
      setCsrfToken(user.csrf_token ?? null);
      setDone(true);
      setCurrent("");
      setNext("");
      setRepeat("");
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="login" onSubmit={(e) => void submit(e)}>
      <h1>Change password</h1>
      <p>
        Signed in as <strong>{username}</strong>. Changing your password signs you out everywhere
        else.
      </p>
      <label>
        Current password
        <input
          type="password"
          autoComplete="current-password"
          value={current}
          onChange={(e) => setCurrent(e.target.value)}
          required
        />
      </label>
      <label>
        New password (at least 12 characters)
        <input
          type="password"
          autoComplete="new-password"
          minLength={12}
          value={next}
          onChange={(e) => setNext(e.target.value)}
          required
        />
      </label>
      <label>
        Repeat new password
        <input
          type="password"
          autoComplete="new-password"
          value={repeat}
          onChange={(e) => setRepeat(e.target.value)}
          required
        />
      </label>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {done && <p role="status">Password changed. Other sessions have been signed out.</p>}
      <button type="submit" disabled={busy}>
        {busy ? "Saving…" : "Change password"}
      </button>
    </form>
  );
}
