import { type FormEvent, useState } from "react";

import { ApiError, api, type AuthUser } from "../api/client";

function message(error: unknown): string {
  if (error instanceof ApiError && error.status === 429) {
    return "Too many failed attempts. Wait a few minutes and try again.";
  }
  if (error instanceof ApiError && error.status === 401) return "Wrong username or password.";
  return "Could not reach the server. Try again.";
}

/** Login form. Accounts are created by the study team; there is no sign-up. */
export function LoginPage({ onLoggedIn }: { onLoggedIn: (user: AuthUser) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      onLoggedIn(await api.login(username, password));
    } catch (e) {
      setError(message(e));
      setPassword("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="login" onSubmit={(e) => void submit(e)}>
      <h1>Log in</h1>
      <label>
        Username
        <input
          autoComplete="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
      </label>
      <label>
        Password
        <input
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </label>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <button type="submit" disabled={busy}>
        {busy ? "Logging in…" : "Log in"}
      </button>
    </form>
  );
}
