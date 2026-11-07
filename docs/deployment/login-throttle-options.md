# Login throttle: current behaviour and alternatives (M3.5, audit F10)

Status: **analysis only. Nothing has changed.** Changing the policy has a material effect
on users, so it waits for a recorded owner decision.

## Current behaviour (ADR-029, ADR-041)

`auth.recent_failures` counts failed logins and failed password changes in the last 15
minutes. A failure counts if it is for **this username** (ignoring case) **or** from
**this client address**. At 5 or more, login answers 429 for the rest of the window,
even when the password is correct.

## Risks for a classroom pilot

1. **Targeted lockout.** Anyone who knows or guesses a student's username can keep that
   student locked out with 5 wrong attempts every 15 minutes.
2. **Shared address.** A class on one campus network usually reaches the site through a
   single NAT address. Five typos across the whole room then lock out **every** student
   in it for 15 minutes. This is the more likely problem in practice.
3. **The proxy setting.** If uvicorn does not trust the proxy's forwarded address, every
   client appears as the proxy and risk 2 applies to everyone. The M3.4 artifacts set
   `--forwarded-allow-ips` to the proxy's fixed address, and the CI smoke test exercises
   that path.

## Alternatives

| Option | Change | Guessing resistance | Lockout risk | Effort |
| --- | --- | --- | --- | --- |
| **T0. Keep as is** | none | strong: 5 guesses per user per 15 min | high (risks 1 and 2) | none |
| **T1. Raise the per-client limit** | per-username limit stays 5; per-client limit becomes, say, 50 per 15 min | per account unchanged; one address can still try at most 50 across all accounts | risk 2 mostly gone; risk 1 unchanged | small |
| **T2. Progressive delay instead of a hard lock, per username** | after N failures, each new attempt for that username must wait 2^k seconds (capped, e.g. 5 min); a correct password after the wait succeeds | still slow for guessing: about 12 guesses per hour at the cap | a student can still log in after a short wait, so risk 1 becomes delay rather than denial | medium |
| **T3. Count per (username, client) pair, plus a per-client cap** | a failure counts only against its own pair; the per-client cap stops one address spraying many accounts | weaker against distributed guessing (5 per address per account) | risk 1 only from the student's own address; risk 2 gone | medium |
| **T4. Operator unlock** | `codeadapt-admin unlock <user>` writes an audit event that resets that user's window | unchanged | a lockout can be cleared within minutes by the operator during a session | small, but needs the operator on hand |

Pilot passwords are created by the operator and long (the minimum length is enforced), so
online guessing is slow under every option.

## Recommendation

**T1 + T4** before the pilot:

- T1 removes the shared-address lockout, which is the likeliest failure in a classroom.
- T4 gives the operator a way out of a targeted lockout during a session.

Consider T2 if targeted lockouts actually happen. Each option needs tests that pin the new
behaviour and an ADR. **Owner decision required.**
