# CodeAdapt group presentation: speaking script

The slides are part of the website: open `/presentation` on the running app (for example
`http://localhost:5173/presentation`). It needs no login. Keys: → or Space next, ← back,
F full screen, G all slides. The slide number is in the address (`/presentation#7`), so a
link can open on any slide.

**Running time:** about 21 minutes, plus questions.

| Part | Presenter | Slides | Time |
| --- | --- | --- | --- |
| Problem, users, solution, journey | Rupinder | 1–5 | 4½ min |
| Live demo and integration | Ashmeen | 6–10 | 6 min |
| Use case and class diagrams | Gourav | 11–16 | 4½ min |
| Sequence diagrams, status, evidence | Jasroop | 17–23 | 5 min |
| Contributions and questions | everyone | 24–25 | 1 min + Q&A |

Speak to the room, not the screen. The lines below are a guide: say them in your own words.
Words in *[brackets]* are actions, not speech.

---

## Before the session (whole team, 30 minutes earlier)

1. Start the full stack (API, worker, database, web) on the machine you will present from, or
   open the hosted site. Open `/presentation` in one tab and `/problems` in another, both
   logged out, to check the links work for someone who is not signed in.
2. **Warm up the sandbox.** Log in as the demo student and submit any program to Lower
   bound once. The first submission measures every error model's fingerprints, which took
   about 3 minutes in rehearsal. After that, a submission takes seconds.
3. Keep the four demo programs ready: they are on slide 7 with a Copy button, and in
   `eval/heldout/lower-bound/`.
4. Each member opens, in a browser tab, the files they will be asked about (see the
   "Where your code is" list at the end of each part).
5. Fill in the contribution slide (slide 24) with real links. See "Contribution slide" below.

---

## Part 1 · Rupinder (slides 1–5)

### Slide 1 · Title

> Good morning. We're Rupinder, Ashmeen, Gourav and Jasroop, and our project is CodeAdapt.
>
> One sentence on what it is: a C++ practice platform that tries to work out *why* a
> solution fails, and only names a mistake when the tests can actually tell that mistake
> apart from the others.
>
> I'll explain the problem and who it's for. Ashmeen will run the real system live. Gourav
> and Jasroop will take you through the design, and Jasroop will finish with what works, what
> doesn't yet, and what's next.

*[→]*

### Slide 2 · The problem

> Most of us have seen this screen. "Wrong answer on test 7." That's it.
>
> If you're a beginner and your binary search is off by one, that verdict doesn't tell you
> what's wrong. So you do what everyone does: change a plus one to a minus one, resubmit, and
> repeat until it goes green. You pass, but you haven't learned which idea was wrong.
>
> The obvious fix is to have the tool guess the cause. But that has its own trap. Two
> different mistakes can produce exactly the same wrong output. If the tool picks one and
> says "you don't understand boundaries", it's confidently wrong, and the student can't tell.
>
> So the student really needs three answers: which case breaks my code, said in words; is it
> one known mistake, or can't you tell; and what should I practise next.

*[→]*

### Slide 3 · Users and why

> We designed for three users.
>
> Students in a first data-structures course, writing C++. They practise, submit, and read
> feedback.
>
> Researchers or instructors, who want to see how errors actually show up, with every
> diagnosis traceable back to the test results behind it.
>
> And an administrator, who creates accounts and checks problem content before it goes live.
>
> We picked binary search on purpose. It's about ten lines of code, but there are many ways
> to get it subtly wrong. Our lower-bound problem alone has eight modelled mistakes and
> seventeen tests, chosen so those mistakes produce different outputs. The bank has since
> grown to twenty-five problems in five families.

*[→]*

### Slide 4 · Proposed solution

> Our idea is to treat every submission as evidence.
>
> *[point along the row]* A submission is run in a sandbox, once per test. That gives us
> observations. Those observations are matched against known mistakes to get a diagnosis.
> The diagnosis picks a follow-up problem that exercises the same skill. The next attempt is
> new evidence, and we check whether it met the goal we set.
>
> Three rules hold all of this together. We store what we observed before we infer anything,
> and we never edit it. When the evidence doesn't separate the possible mistakes, we abstain:
> the student sees the failing cases and no guess. And we describe the program, never the
> person: the feedback says your code "behaves as if" it has a mistake.

*[→]*

### Slide 5 · User journey

> This is the journey we built, and Ashmeen will walk it live in a minute.
>
> The landing page explains what the tool does and doesn't claim. You log in with an account
> the administrator created. You pick a problem from twenty-five, grouped by family. You write
> C++ in the editor and submit. You get the result: the failing cases in plain words, and a
> hint only if one known mistake fits. Then a recommended next problem, and the system checks
> the follow-up on your next attempt.
>
> Researchers get a second path *[point to the lower row]*: a list of submissions with
> metrics, a full evidence trace for any one of them, and a learner model, which is always
> labelled "estimated under assumed parameters". I'll hand over to Ashmeen.

*[→]*

**Where your code is (Rupinder):** `web/src/pages/LandingPage.tsx`,
`web/src/pages/ProblemListPage.tsx`, `web/src/App.tsx` (routes), `docs/architecture.md` §1.

**Likely questions**

- *Why not use an existing judge?* Judges stop at a verdict. We needed per-test outputs from
  known-wrong programs to compare against, and an evidence trail behind every message.
- *Why C++ only?* One toolchain (GCC 14.2, pinned) keeps runs reproducible. The design does not
  depend on the language, but every problem would need new error models.
- *Who are your users in practice?* Nobody yet. It has not been used with real students, and we
  say so on slide 22.

---

## Part 2 · Ashmeen (slides 6–10)

### Slide 6 · Divider

> Thanks, Rupinder. This part is live: real sandbox, real database, and four prepared
> programs. Nothing is recorded.

*[→]*

### Slide 7 · Demo kit, then the live app

> These are our four test programs. We wrote them ourselves to exercise the system; they are
> not student submissions. Each should get a different answer.

*[Click "Open the live app". Log in as the demo student. Open Lower bound.]*

> This is the practice page: the statement on the left, the editor on the right.

**Program 1: `correct_iterative.cpp`.** *[Copy from slide 7, paste, Submit.]*

> It's a correct solution in an unusual style. *[wait for the result]* All seventeen tests
> pass. Notice the wording: it says tests can show mistakes but can't prove a solution
> correct. We don't overclaim even on a pass.

**Program 2: `recursive_early_equal.cpp`.** *[Paste, Submit.]*

> This one returns as soon as it finds an equal element. For lower bound that's wrong when the
> target repeats. *[result]* Here the system names a mistake, because exactly one known
> mistake fits every failing test. You see the failing cases, a hint, and a recommended next
> problem.

**Program 3: `double_bug.cpp`.** *[Paste, Submit.]*

> This has two mistakes at once. *[result]* No single known mistake explains it, so the
> system shows the failing cases and does not guess. That is the abstention we talked about.

**Program 4: `size_t_stuck_left.cpp`.** *[Paste, Submit.]*

> This loop never makes progress. *[result]* It hits the time limit. We report that as a
> symptom, "did not finish", and name no mistake, because many different bugs cause a timeout.

*[Open "My attempts", then switch to the researcher account and open Research → the last
submission's trace.]*

> As a researcher I can open any of those submissions and see the whole chain: every test's
> output, which tests were excluded and why, which mistakes were candidates, and the reasoning.
> This is what the student's message was built from.

*[Back to the presentation tab, →]*

**If the sandbox is slow or down:** say so plainly, show the trace of a submission made during
the warm-up, and carry on. Do not show screenshots as if they were live.

### Slide 8 · How the parts connect

> Behind that demo are six components. The web app is React and TypeScript with a CodeMirror
> editor. The API is FastAPI. The database is PostgreSQL in deployment, SQLite in development.
>
> The important line is this boundary *[point to the dashed zone]*. The API never runs student
> code. It writes a job to the database and answers straight away. A separate worker claims
> the job and is the only process that talks to Docker. The sandbox runs every test in a fresh
> container with no network and strict limits. The learner model sits on the worker side too,
> but it is for researchers only.

*[→]*

### Slide 9 · Where the parts meet

> Each joint has a contract that's checked. The web app's types are generated from the API's
> OpenAPI schema, and CI fails if they drift. Logins use an HttpOnly cookie plus a CSRF token;
> passwords are Argon2id hashes and we only store a hash of the session token. The worker
> claims a job with a conditional update and a lease, so two workers can't take the same job.
> And every problem's content version is a hash of its files, so old evidence always points at
> the exact version it was produced on.
>
> At release, that was 609 backend unit tests, 39 sandbox tests, 37 web component tests and 3
> end-to-end browser flows.

*[→]*

### Slide 10 · How a diagnosis is decided

> The core is simple on purpose. Every known mistake is a real program. We run it on every
> test and store its outputs: we call that its fingerprint. Then we compare the student's
> outputs with each fingerprint.
>
> *[point to the table]* This is a simplified picture. The student's column matches model B on
> every test, and no other model, so model B is named. If several models fit, the answer is
> "ambiguous" and nothing is named. If none fit, it's "unmodelled". A timeout is a symptom.
>
> There's no machine learning here. It's deterministic, and we can replay it over stored
> evidence when we change the method. Gourav will now show the design.

*[→]*

**Where your code is (Ashmeen):** `backend/src/codeadapt/worker/pipeline.py` (the job),
`backend/src/codeadapt/execution/docker.py` (sandbox), `backend/src/codeadapt/diagnosis/fingerprint_v1.py`
(diagnosis), `backend/src/codeadapt/api/app.py` (endpoints), `backend/src/codeadapt/db/queue.py`
(job claim), `docs/demo.md`.

**Likely questions**

- *What stops student code escaping?* No network, read-only filesystem, CPU, memory, process
  and output limits, one container per test. For public hosting we require gVisor on a separate
  runner machine; that tier is tested in CI but not deployed yet.
- *Why a database queue instead of Redis?* One fewer service, and jobs are evidence we keep
  anyway. The claim is a conditional UPDATE with a lease and heartbeat.
- *Why not an ML classifier?* We have no labelled real data to train or check it on, and we
  need every diagnosis to be explainable from the tests.

---

## Part 3 · Gourav (slides 11–16)

### Slide 11 · Divider

> Thanks, Ashmeen. I'll show who uses the system and what it's made of: four use case
> diagrams and the class diagram. All of them were drawn from the code, so the names you see
> are the names in the repository.

*[→]*

### Slide 12 · Use case 1: Student

> The student is the main actor. They log in, browse problems by family, open one, write C++,
> submit, read feedback, follow the recommendation, and review past attempts.
>
> Two relationships matter. Submitting *includes* running the diagnostic tests: you can't
> submit without that happening, and the runner worker is the secondary actor there. Showing a
> hint *extends* reading feedback: it only happens when exactly one known mistake fits.

*[→]*

### Slide 13 · Use case 2: Researcher

> The researcher browses submissions, with optional filters by problem, outcome and data
> class. They can view metrics, inspect an evidence trace, which always includes the
> observations, candidates and reasoning, see active learners, and view a learner model.
>
> Viewing the learner model includes estimating skills under assumed parameters; the BKT model
> is the secondary actor. Offline evaluation can be extended to compare method versions 1.1,
> 1.2 and 1.3 on the same evidence.

*[→]*

### Slide 14 · Use case 3: Administrator

> The administrator works from the command line, not the website. There is deliberately no
> account-management endpoint in the API. Creating an account records an audit event. Setting
> a new password or disabling an account ends that account's sessions. And validating problem
> content includes measuring every error model's fingerprint in the Docker sandbox.

*[→]*

### Slide 15 · Use case 4: Runner worker

> The fourth actor is a system: the worker. For every queued job it claims the job, compiles
> the submission with the problem's harness, runs each test, and may re-run failing tests with
> a sanitiser build to check the result is reliable. Then it diagnoses, updates the skill
> evidence, evaluates a follow-up if there was one, and recommends the next activity. Compiling
> and running both include the sandbox limits.

*[→]*

### Slide 16 · Class diagram

> This is the detailed class diagram. Read it left to right as one evidence chain.
>
> A User makes Submissions and owns AuthSessions. Each Submission has exactly one Job in the
> queue, and produces ExecutionRuns, each with many TestObservations. A run happened in one
> Environment: the image digest and compiler, so it's reproducible.
>
> *[move right]* A Submission is interpreted by Diagnoses. A Diagnosis is matched against a
> FingerprintSet for that ProblemVersion, and can lead to one Recommendation, which can be
> evaluated by one FollowupEvaluation on the next attempt.
>
> The amber classes are protocols: DiagnosticMethod and SandboxBackend. The worker depends on
> those, not on a concrete class, which is why we could add method versions and a gVisor
> sandbox without touching the pipeline. Green classes are logic: FingerprintConsistency,
> PolicyV1, and BktParams, which is labelled "assumed" because that's what its numbers are.
> Jasroop will show how these objects talk to each other.

*[→]*

**Where your code is (Gourav):** `backend/src/codeadapt/db/models.py` (entities),
`backend/src/codeadapt/diagnosis/models.py` (`DiagnosticMethod`, `Outcome`),
`backend/src/codeadapt/execution/backend.py` (`SandboxBackend`), `backend/src/codeadapt/learner/bkt.py`
(`BktParams`), `backend/migrations/versions/`, and the diagram data in
`web/src/presentation/diagrams.tsx`.

**Likely questions**

- *Why composition between Submission and Job?* A job exists only for its submission and is
  created with it.
- *Why are evidence tables append-only?* So a diagnosis can always be traced back to the exact
  observations it used. Corrections are new rows.
- *What is "data class"?* Every row is marked real, synthetic or dev, and research queries
  filter on it so synthetic data is never mixed with real data.

---

## Part 4 · Jasroop (slides 17–23)

### Slide 17 · Sequence 1: Log in

> Five sequence diagrams, starting with logging in. The browser posts the username and
> password. The auth module first checks throttling, then loads the user and verifies the
> Argon2id hash. There are three outcomes *[point to the alt frame]*: too many failures gives a
> 429; a wrong password gives a 401 and an audit entry; a correct one creates a session,
> stores only a hash of the token, and sets an HttpOnly cookie, so page scripts can never read
> it.

*[→]*

### Slide 18 · Sequence 2: Submit a solution

> Submitting. The page sends the source with the CSRF token. The API checks the session,
> role, size limit of 64 KiB and the rate limit, records the submission and a queued job, and
> answers 202 immediately. It never waits for the sandbox. The page then polls until the job
> is completed, and every response goes through a student-safe projection, so hidden tests
> and internal labels can't leak.

*[→]*

### Slide 19 · Sequence 3: Run and diagnose

> This is the worker's side. It claims the job with a lease and loads the problem version. If
> this version has never been measured in this environment, it first runs every error model to
> get the fingerprints, which is why the first submission is slow. Then it compiles with no
> network. If compiling fails, that's recorded and it is never used as evidence about a skill.
> Otherwise every test runs in a fresh container, failing tests are re-run with a sanitiser,
> unreliable results are excluded, and the diagnosis engine returns an outcome with its reasons.

*[→]*

### Slide 20 · Sequence 4: Recommend and follow up

> Then adaptation. If this attempt follows an open recommendation, it's evaluated against the
> criterion we recorded: met, not met, or not comparable. Then the policy asks the evidence
> ledger for skill observations. A qualified diagnosis adds no negative evidence. The policy has
> an explicit rule for every outcome *[point to the alt]*: a supported or ambiguous diagnosis
> leads to a problem that probes the same skill; a pass moves on in the family; a timeout or
> unmodelled result gets a retry with a review flag.

*[→]*

### Slide 21 · Sequence 5: Researcher

> Last, the researcher. Every research endpoint checks the role first; a student gets a 403.
> The trace returns the full evidence chain. For the learner model, the API passes the
> learner's attempts to the BKT module with a named set of assumed parameters. It counts only
> the first reliable attempt per problem version, and returns either an estimate or
> "insufficient data". Every estimate is labelled, and none of it is shown to students or used
> for recommendations.

*[→]*

### Slide 22 · Complete, limited, next

> Where it stands. Complete: the sandbox, the diagnosis method with abstention, the evidence
> ledger, recommendations and follow-up checks, login with roles, both interfaces, and 25
> problems that pass validation.
>
> Limited: we have not tried it with real students. It names a mistake for only about nine
> percent of our incorrect test programs; the rest get failing cases only. The BKT numbers are
> assumptions. The skill maps are our own judgement. It doesn't check complexity, so a linear
> scan passes. And the production sandbox tier is tested in CI but not deployed.
>
> Next, in this order: host it properly with the gVisor runner on its own machine; test it on
> programs we didn't write; make the failing-case feedback the main experience, since that's
> what most students will see; and only then fit the learner model on real data.

*[→]*

### Slide 23 · What the numbers say

> A word on numbers, because it's easy to overclaim. On 26 incorrect programs we wrote and
> held back, the method named 14 and got none wrong. On 323 automatically generated incorrect
> programs, it named 30 and got none of those wrong. It never flagged any of the 6 correct
> programs.
>
> *[point to the box]* But none of this is accuracy on real students. We wrote or generated
> every program. Zero out of thirty still allows an error rate of several percent. And each
> version got fewer names wrong by naming less often. We chose that trade deliberately: a
> wrong hint does more harm than no hint.

*[→]*

**Where your code is (Jasroop):** `backend/src/codeadapt/adaptation/policy_v1.py` (policy),
`backend/src/codeadapt/adaptation/ledger.py` (evidence), `backend/src/codeadapt/adaptation/followup.py`,
`backend/src/codeadapt/worker/adapt.py`, `docs/limitations.md`, `docs/evaluation/summary.md`,
`docs/release-2026-10-26.md`.

**Likely questions**

- *Does CodeAdapt improve learning?* We don't know. No learning effect has been measured, and
  we make no claim.
- *Is the BKT model accurate?* Its parameters are assumptions, not fitted. Estimates change a lot
  across plausible values, which is why it's researcher-only.
- *Why is coverage so low?* Strict matching: two bugs at once, or one bug plus a timeout, match no
  single model. We prefer abstaining to naming the wrong mistake.

---

## Slide 24 · Contributions (everyone, ~15 seconds each)

Each member says one sentence about what they did and points at their own evidence.

> *Rupinder:* I worked on ... — you can see it in ...
> *Ashmeen:* ...
> *Gourav:* ...
> *Jasroop:* ...

**Contribution slide.** Edit `CONTRIBUTIONS` at the top of `web/src/presentation/slides.tsx`:
replace each `did` list with what that person actually did and put real links in `evidence`
(commits, issues, pull requests, tests or weekly journal entries). The brief says the examiner
may ask any of us to find our code or make a small change, so list only work that person did
and can explain. The placeholders on the slide are highlighted until they are filled.

## Slide 25 · Questions (Rupinder opens, everyone answers)

> That's CodeAdapt. Thank you. We're happy to take questions, and to open the code behind
> any slide.

Answer questions about your own part. If a question is about someone else's part, pass it to
them by name.

---

## Things we never say

- That CodeAdapt is accurate on students, improves learning, or measures mastery.
- That the learner model's numbers are fitted or validated.
- That the held-out or mutant results are independent tests: we wrote or generated them.
- That the system is deployed or hardened for public use.
