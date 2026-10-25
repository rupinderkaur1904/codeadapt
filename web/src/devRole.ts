/**
 * Development-only role switch. The API honours the X-Dev-Role header only when its dev
 * authentication stub is enabled (never in production, where it answers 503).
 */
export type DevRole = "student" | "researcher";

const KEY = "codeadapt:dev-role";

export function getDevRole(): DevRole {
  try {
    return window.localStorage.getItem(KEY) === "researcher" ? "researcher" : "student";
  } catch {
    return "student";
  }
}

export function setDevRole(role: DevRole): void {
  try {
    window.localStorage.setItem(KEY, role);
  } catch {
    // Storage unavailable: the choice lasts until reload.
  }
}
