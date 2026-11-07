# Controlled pilot protocol (DRAFT, not approved)

> **Status: DRAFT for owner Gate C and for independent ethics review.**
> - No ethics approval or exemption exists.
> - Nobody has been recruited or contacted.
> - No real-student data has been collected.
> - Enrollment needs, all recorded in writing: Gate B (a verified deployment), Gate C (the
>   owner's go-ahead) and the ethics determination.

## 1. Purpose

The pilot is a **feasibility and usability** study. It asks whether CodeAdapt can be
operated safely and reliably with a small group of real learners, and how they experience
it.

**It is not an effectiveness study.** It cannot establish any of the following, and no
report from it will claim them:

- diagnostic accuracy on real students;
- learning gains;
- the benefit of personalised recommendations.

The diagnostic method, recommendation policy, learner model and content stay **frozen**
for the whole pilot. The Milestone 3 research-freeze manifest is checked before the pilot
starts and again at the end.

## 2. Research questions

- **RQ1 (operational).** Under real use, does the system stay available, process
  submissions within an acceptable time and record evidence without loss?
  - Measured by uptime from `/ready` probes and by the queue wait from submission to
    result, using the `jobs` timestamps.
  - Also measured by failed jobs, adaptation failures and incidents.
- **RQ2 (usability).** How do participants rate the clarity and usefulness of the
  feedback?
  - Measured by a short post-session questionnaire (5-point items and free text).
  - The questionnaire is drafted and approved together with this protocol. It is not
    included here.
- **RQ3 (descriptive).** How often does the frozen method name a specific error, abstain,
  or give no failure on real submissions?
  - Reported as descriptive counts only.
  - **Not** as accuracy: there is no ground truth for these submissions.

## 3. Participants

- **8 to 20 adult volunteers (18+)** who are learning C++ or algorithms at an
  introductory level.
- Exclusions: under 18; anyone in a dependent relationship with the owner where
  participation could feel compulsory (for example the owner's own students in a course
  the owner grades).
- Recruitment uses one neutral message on a channel approved by the review body. **No
  recruitment until Gate C.**
- No payment and no course credit. **[REVIEW]** whether a small token of thanks is
  acceptable.

## 4. Procedure

1. The participant reads the information sheet and gives consent
   (`informed-consent.md`). They receive a pseudonymous account code and a password
   privately, and change the password at first login.
2. **Sessions:** one or two supervised sessions, each up to 60 minutes, online or in
   person.
   - The participant solves problems from the existing problem bank.
   - Feedback appears after each submission.
   - Participants may stop at any time.
3. After the last session the participant fills in the questionnaire, which takes about
   10 minutes.
4. The operator checks the system status before each session and takes a backup
   (production-runbook.md §5).

## 5. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Misleading feedback: the diagnosis or recommendation may be wrong, because the method is not validated on real students | The information sheet says so plainly. The UI makes no mastery claims (BKT is researcher-only). Participants can ignore the feedback. Nothing is graded. |
| Frustration or time pressure | Short sessions, no assessment, free to stop |
| Privacy | Pseudonymous accounts; minimal data (data-governance.md §2); encrypted transport; least-privilege access; deletion on withdrawal |
| Security of submitted code execution | Student code runs only under gVisor on an isolated runner, verified on the host (gvisor-verification.md L3) |
| Service failure during a session | Monitoring, a runbook, and an incident response plan. A failed session is rescheduled, not counted. |

The overall risk is judged **minimal**. **[REVIEW]** That is the review body's
determination, not ours.

## 6. Data and analysis

- What is collected and how long it is kept: `data-governance.md`.
- The analysis is descriptive, covering RQ1 to RQ3. Free-text answers are summarised
  without quotations that could identify anyone.
- Results report small numbers as small, with no p-values used to suggest
  generalisation.
- Synthetic, held-out and pilot data are reported separately and never pooled (ADR-008).

## 7. Stopping rules

The pilot stops, and nothing further is collected until the owner reviews, if any of
these happens:

- a SEV1 incident (incident-response.md), including any suspected data exposure or
  sandbox escape;
- a participant reports harm or distress connected to the study;
- the deployment fails its gVisor host verification, or an upgrade changes any
  research-frozen file without an approved ADR;
- the ethics determination is withdrawn or its conditions are not met.

## 8. Responsibilities and gates

| Gate | Decision | Who |
| --- | --- | --- |
| A | architecture, provider, region, budget, domain | owner |
| B | provisioning and exposure, after host verification passes | owner |
| Ethics | approval or exemption in writing | the review body chosen by the owner |
| C | enrollment may begin | owner, after the above and after the [REVIEW] items in data-governance.md are resolved |
