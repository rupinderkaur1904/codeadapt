import { type FormEvent, useState } from "react";

import { ApiError, api, type AuthUser } from "../api/client";

function message(error: unknown): string {
  if (!(error instanceof ApiError)) return "Could not reach the server. Try again.";
  if (error.status === 429) return "Too many attempts. Wait a few minutes and try again.";
  if (error.type.endsWith("/bad-invite-code")) {
    return "That invite code is not valid. Check it with your instructor.";
  }
  if (error.type.endsWith("/username-taken")) return "That username is taken. Choose another.";
  if (error.type.endsWith("/signup-disabled")) return "Sign-up is not open right now.";
  if (error.status === 422 && error.detail) return `${error.detail}.`;
  return "Could not create the account. Try again.";
}

/** Self-service sign-up (ADR-044, ADR-045), with an invite code field only when the
 * deployment asks for one. The new account is a student account; the server decides its
 * role and data class, not this form. */
export function SignupPage({
  minPasswordLength,
  needsInviteCode,
  onSignedUp,
  onCancel,
}: {
  minPasswordLength: number;
  needsInviteCode: boolean;
  onSignedUp: (user: AuthUser) => void;
  onCancel: () => void;
}) {
  const [inviteCode, setInviteCode] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [repeat, setRepeat] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (password.length < minPasswordLength) {
      setError(`Use a password of at least ${minPasswordLength} characters.`);
      return;
    }
    if (password !== repeat) {
      setError("The two passwords differ.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      onSignedUp(await api.signup(username, password, needsInviteCode ? inviteCode : undefined));
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="login" onSubmit={(e) => void submit(e)}>
      <h1>Create an account</h1>
      {needsInviteCode && (
        <>
          <p className="muted">You need the invite code your instructor gave your class.</p>
          <label>
            Invite code
            <input
              autoComplete="off"
              spellCheck={false}
              value={inviteCode}
              onChange={(e) => setInviteCode(e.target.value)}
              required
            />
          </label>
        </>
      )}
      <label>
        Username
        <input
          autoComplete="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          minLength={3}
          maxLength={32}
          required
        />
      </label>
      <label>
        Password
        <input
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </label>
      <label>
        Repeat password
        <input
          type="password"
          autoComplete="new-password"
          value={repeat}
          onChange={(e) => setRepeat(e.target.value)}
          required
        />
      </label>
      <p className="muted">At least {minPasswordLength} characters.</p>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <button type="submit" disabled={busy}>
        {busy ? "Creating account…" : "Create account"}
      </button>
      <button type="button" className="link" onClick={onCancel}>
        I already have an account
      </button>
    </form>
  );
}
