# CodeAdapt group presentation: speaking script

The slides are part of the website: open `/presentation` on the running app (for example
`http://localhost:5173/presentation`). It needs no login. Keys: → or Space next, ← back,
F full screen, G all slides. The slide number is in the address (`/presentation#9`), so a
link can open on any slide.

**Running time:** 21 minutes, plus questions. Each presenter has **5 minutes**, then the
team shares the last minute.

| Part | Presenter | Slides | Time |
| --- | --- | --- | --- |
| Problem, users, solution, journey, student screens | Rupinder | 1–6 | 5 min |
| Live demo, results, architecture | Ashmeen | 7–9 | 5 min |
| Integration, diagnosis, use cases, class diagram | Gourav | 10–16 | 5 min |
| Sequence diagrams, researcher screens, status, evaluation | Jasroop | 17–24 | 5 min |
| Contributions and questions | everyone | 25–26 | 1 min + Q&A |

Each spoken part is about 600–650 words, which is 5 minutes at a calm pace. Ashmeen's part
has fewer words because the demo needs time for pasting code and waiting for results. The
time next to each slide heading is a target, so you can tell during rehearsal whether you are
running long. Time each other in rehearsal: if you finish a part in under 4½ minutes, you
are going too fast.

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
5. Fill in the contribution slide (slide 25) with real links. See "Contribution slide" below.

---

## Part 1 · Rupinder (slides 1–6, 5 minutes)

### Slide 1 · Title (40 seconds)

> Good morning. We're Rupinder, Ashmeen, Gourav and Jasroop, and our project is CodeAdapt.
>
> In one sentence: it's a C++ practice platform that tries to work out *why* a solution
> fails, and only names a mistake when the tests can actually tell that mistake apart from the
> others.
>
> Each of us has about five minutes. I'll explain the problem and who it's for. Ashmeen will
> run the real system live. Gourav will show how the parts fit together and the design, and
> Jasroop will finish with how the system behaves inside, what works, and what doesn't yet.

*[→]*

### Slide 2 · The problem (1 minute 10 seconds)

> Most of us have seen a judge say "Wrong answer on test 7", and nothing more.
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

### Slide 3 · Users and why (1 minute)

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

### Slide 4 · Proposed solution (1 minute)

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

### Slide 5 · User journey (45 seconds)

> This is the journey we built. You log in with an account the administrator created, pick a
> problem from twenty-five, write C++ in the editor and submit. You get the failing cases in
> plain words, a hint only if one known mistake fits, and a recommended next problem.
>
> Researchers get a second path *[point to the right column]*: submissions with metrics, the
> full evidence trace of any one of them, and a learner model, always labelled "estimated
> under assumed parameters".

*[→]*

### Slide 6 · The student's screens (40 seconds)

> These are screenshots of the real pages, taken from the running system with our test
> accounts. *[point left]* This is the practice page after a submission: the statement, the
> code, and underneath, the feedback. It says the code "behaves as if" it has a mistake, gives
> one hint, and lists the cases that show it. *[point right]* And this is the problem list,
> grouped by family, with the recommendation at the top.
>
> That's the plan on paper. Ashmeen will now show you that it actually runs.

*[→]*

**Where your code is (Rupinder):** `web/src/pages/LandingPage.tsx`,
`web/src/pages/ProblemListPage.tsx`, `web/src/App.tsx` (routes), `docs/architecture.md` §1.

**Likely questions**

- *Why not use an existing judge?* Judges stop at a verdict. We needed per-test outputs from
  known-wrong programs to compare against, and an evidence trail behind every message.
- *Why C++ only?* One toolchain (GCC 14.2, pinned) keeps runs reproducible. The design does not
  depend on the language, but every problem would need new error models.
- *Who are your users in practice?* Nobody yet. It has not been used with real students, and we
  say so on slide 23.

---

## Part 2 · Ashmeen (slides 7–9, 5 minutes)

This part has fewer words than the others because about two minutes go on pasting code,
waiting for results and switching accounts. Keep talking while a result loads: say what you
expect to see.

### Slide 7 · Live demo (3 minutes 40 seconds)

> Thanks, Rupinder. This part is live, on the real system. These are four test programs we
> wrote ourselves, not student submissions, and each one should get a different answer.

*[Click "Open CodeAdapt". Log in as the demo student. Open Lower bound.]*

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
> system shows the failing cases and does not guess. That's the abstention Rupinder talked
> about.

**Program 4: `size_t_stuck_left.cpp`.** *[Paste, Submit.]*

> This loop never makes progress. *[result]* It hits the time limit. We report that as a
> symptom, "did not finish", and name no mistake, because many different bugs cause a timeout.

*[Open "My attempts", then switch to the researcher account and open Research → the last
submission's trace.]*

> Now I'm logged in as a researcher. I can open any of those submissions and see the whole
> chain: every test's output, which tests were excluded and why, which mistakes were
> candidates, and the reasoning. This is exactly what the student's message was built from.

*[Back to the presentation tab, →]*

**If the sandbox is slow or down:** say so plainly, show the trace of a submission made during
the warm-up, or go to the next slide, which has screenshots of all four results. Say that they
are screenshots, not live.

### Slide 8 · The four demo results (20 seconds)

> To sum up what you just saw, here are the four results side by side. A pass. One mistake
> named, with a hint. Two mistakes, so no guess. And a loop that never ends, reported as a
> time-out. Four programs, four different answers.

*[→]*

### Slide 9 · System architecture (1 minute)

> Behind that demo are six components. The web app is React and TypeScript with a CodeMirror
> editor. The API is FastAPI. The database is PostgreSQL in deployment, SQLite in development.
>
> The important line is this boundary *[point to the dashed zone]*. The API never runs student
> code. It writes a job to the database and answers straight away. A separate worker claims
> the job and is the only process that talks to Docker. The sandbox runs every test in a fresh
> container with no network and strict limits. The learner model sits on the worker side too,
> but it is for researchers only.
>
> Gourav will now show how these parts talk to each other.

*[→]*

**Where your code is (Ashmeen):** `backend/src/codeadapt/worker/pipeline.py` (the job),
`backend/src/codeadapt/execution/docker.py` (sandbox), `backend/src/codeadapt/api/app.py`
(endpoints), `backend/src/codeadapt/db/queue.py` (job claim), `docs/demo.md`.

**Likely questions**

- *What stops student code escaping?* No network, read-only filesystem, CPU, memory, process
  and output limits, one container per test. For public hosting we require gVisor on a separate
  runner machine; that tier is tested in CI but not deployed yet.
- *Why a database queue instead of Redis?* One fewer service, and jobs are evidence we keep
  anyway. The claim is a conditional UPDATE with a lease and heartbeat.
- *What happens if the worker crashes mid-job?* Its lease runs out and another worker can
  claim the job again.

---

## Part 3 · Gourav (slides 10–16, 5 minutes)

### Slide 10 · Integration between components (50 seconds)

> Thanks, Ashmeen. I'll cover how the parts connect, how the diagnosis works, and then the
> design diagrams.
>
> Each joint has a contract that's checked. The web app's types are generated from the API's
> schema, and CI fails if they drift. Logins use an HttpOnly cookie plus a CSRF token, and
> passwords are Argon2id hashes. The worker claims a job with a lease, so two workers can't
> take the same job. And every problem version is a hash of its files, so old evidence always
> points at the exact version it came from.
>
> At release that was 609 backend tests, 39 sandbox tests, 37 web tests and 3 browser flows.

*[→]*

### Slide 11 · How the diagnosis works (50 seconds)

> The core is simple on purpose. Every known mistake is a real program. We run it on every
> test and store its outputs: we call that its fingerprint. Then we compare the student's
> outputs with each fingerprint.
>
> *[point to the table]* In this simplified picture, the student's column matches model B on
> every test, and no other model, so model B is named. If several models fit, it's
> "ambiguous" and nothing is named. If none fit, it's "unmodelled". A timeout is a symptom.
>
> There's no machine learning here. It's deterministic, so we can replay it over stored
> evidence whenever we change the method.

*[→]*

### Slide 12 · Use case diagram 1: Student (40 seconds)

> Now the four use case diagrams. They were drawn from the code, so the names match the
> repository.
>
> The student is the main actor. They log in, browse problems by family, write C++, submit,
> read feedback, follow the recommendation, and review past attempts. Submitting *includes*
> running the tests, with the runner worker as a secondary actor. Showing a hint *extends*
> reading feedback: it only happens when exactly one known mistake fits.

*[→]*

### Slide 13 · Use case diagram 2: Researcher (30 seconds)

> The researcher browses submissions with filters, views metrics, inspects an evidence trace,
> and views a learner model. Viewing the learner model includes estimating skills under
> assumed parameters, with the BKT model as the secondary actor. Offline evaluation extends
> this to compare method versions 1.1, 1.2 and 1.3 on the same evidence.

*[→]*

### Slide 14 · Use case diagram 3: Administrator (25 seconds)

> The administrator works from the command line, not the website: there is deliberately no
> account-management endpoint. Creating an account records an audit event. Setting a new
> password or disabling an account ends that account's sessions. And validating problem content includes measuring every fingerprint in the
> sandbox.

*[→]*

### Slide 15 · Use case diagram 4: Runner worker (30 seconds)

> The fourth actor is a system: the worker. For every job it compiles the submission, runs
> each test, and may re-run failing tests with a sanitiser build to check the result is
> reliable. Then it diagnoses, updates the skill evidence, checks any follow-up, and
> recommends the next activity. Compiling and running both include the sandbox limits. If a
> result can't be trusted, for example because the sandbox itself failed, the run is marked
> unreliable and never counts as evidence against the student.

*[→]*

### Slide 16 · Class diagram (1 minute 15 seconds)

> This is the detailed class diagram. Read it left to right as one evidence chain.
>
> A User makes Submissions and owns AuthSessions. Each Submission has exactly one Job, and
> produces ExecutionRuns, each with many TestObservations. A run happened in one Environment,
> the image and compiler, so it can be reproduced.
>
> *[move right]* A Diagnosis interprets a Submission by matching it against the FingerprintSet
> for that ProblemVersion. It can lead to one Recommendation, which is checked by one
> FollowupEvaluation on the next attempt.
>
> The two «protocol» classes, DiagnosticMethod and SandboxBackend, are interfaces. The worker
> depends on those, which is why we could add method versions and a gVisor sandbox without
> touching the pipeline. And BktParams is marked «assumed», because that's what its numbers
> are. Jasroop will show how these objects talk to each other.

*[→]*

**Where your code is (Gourav):** `backend/src/codeadapt/diagnosis/fingerprint_v1.py`
(diagnosis), `backend/src/codeadapt/db/models.py` (entities),
`backend/src/codeadapt/diagnosis/models.py` (`DiagnosticMethod`, `Outcome`),
`backend/src/codeadapt/execution/backend.py` (`SandboxBackend`), `backend/src/codeadapt/learner/bkt.py`
(`BktParams`), `backend/migrations/versions/`, `web/src/api/` (generated types), and the
diagram data in `web/src/presentation/diagrams.tsx`.

**Likely questions**

- *Why not an ML classifier?* We have no labelled real data to train or check it on, and we
  need every diagnosis to be explainable from the tests.
- *Why composition between Submission and Job?* A job exists only for its submission and is
  created with it.
- *Why are evidence tables append-only?* So a diagnosis can always be traced back to the exact
  observations it used. Corrections are new rows.
- *What is "data class"?* Every row is marked real, synthetic or dev, and research queries
  filter on it so synthetic data is never mixed with real data.

---

## Part 4 · Jasroop (slides 17–24, 5 minutes)

### Slide 17 · Sequence diagram 1: Login (35 seconds)

> Thanks, Gourav. Five sequence diagrams, starting with logging in. The browser posts the
> username and password. The auth module checks throttling, then verifies the Argon2id hash.
> There are three outcomes *[point to the alt frame]*: too many failures gives a 429; a wrong
> password gives a 401 and an audit entry; a correct one creates a session, stores only a hash
> of the token, and sets an HttpOnly cookie that page scripts can't read.

*[→]*

### Slide 18 · Sequence diagram 2: Submit a solution (30 seconds)

> Submitting. The page sends the source with the CSRF token. The API checks the session,
> role, a 64 KiB size limit and the rate limit, records the submission and a queued job, and
> answers 202 straight away. It never waits for the sandbox. The page then polls, and every
> response goes through a student-safe view, so hidden tests and internal labels can't leak.

*[→]*

### Slide 19 · Sequence diagram 3: Run and diagnose (45 seconds)

> This is the worker's side. It claims the job with a lease and loads the problem version. If
> this version has never been measured here, it first runs every error model to get the
> fingerprints, which is why the very first submission is slow. Then it compiles with no
> network. A compile error is recorded but never used as evidence about a skill. Otherwise
> every test runs in a fresh container, failing tests are re-run with a sanitiser, unreliable
> results are excluded, and the diagnosis returns an outcome with its reasons.

*[→]*

### Slide 20 · Sequence diagram 4: Recommendation (40 seconds)

> Then adaptation. If this attempt follows an open recommendation, it's checked against the
> goal we recorded: met, not met, or not comparable. Then the policy asks the evidence ledger
> for skill observations. The policy has an explicit rule for every outcome *[point to the
> alt]*: a named or ambiguous diagnosis leads to a problem on the same skill; a pass moves on
> in the family; a timeout or unmodelled result gets a retry with a review flag.

*[→]*

### Slide 21 · Sequence diagram 5: Researcher view (30 seconds)

> Last, the researcher. Every research endpoint checks the role first; a student gets a 403.
> For the learner model, the API passes the learner's attempts to the BKT module with a named
> set of assumed parameters, counts only the first reliable attempt per problem version, and
> returns an estimate or "insufficient data".

*[→]*

### Slide 22 · The researcher's screens (30 seconds)

> And this is what that looks like. *[point left]* The research page counts stored outcomes
> and lists every submission with its outcome and the next step chosen. *[point right]* The
> trace shows the full evidence for one of them, and the learner model page labels every
> estimate "estimated under assumed parameters". None of it is shown to students.

*[→]*

### Slide 23 · Current status (1 minute 10 seconds)

> So where does it stand? Complete: the sandbox, the diagnosis method with abstention, the
> evidence ledger, recommendations and follow-up checks, login with roles, both interfaces,
> and 25 problems that pass validation.
>
> Limited: we have not tried it with real students. It names a mistake for only about nine
> percent of our incorrect test programs; the rest get failing cases only. The BKT numbers and
> the skill maps are our own assumptions. It doesn't check complexity, so a linear scan passes.
> And the production sandbox tier is tested in CI but not deployed.
>
> Next, in this order: host it properly with the gVisor runner on its own machine; test it on
> programs we didn't write; make the failing-case feedback the main experience, since that's
> what most students will see; and only then fit the learner model on real data.

*[→]*

### Slide 24 · Evaluation results (1 minute)

> A word on numbers, because it's easy to overclaim. On 26 incorrect programs we wrote and
> held back, the method named 14 and got none wrong. On 323 automatically generated incorrect
> programs, it named 30 and got none of those wrong. It never flagged any of the 6 correct
> programs.
>
> *[point to the notes under the table]* But none of this is accuracy on real students. We
> wrote or generated every program. Zero out of thirty still allows an error rate of several
> percent. And each version got fewer names wrong by naming less often. We chose that trade
> deliberately: a wrong hint does more harm than no hint.

*[→]*

**Where your code is (Jasroop):** `backend/src/codeadapt/auth/` and the login route in `backend/src/codeadapt/api/app.py`,
`backend/src/codeadapt/adaptation/policy_v1.py` (policy),
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

## Slide 25 · Team contributions (everyone, 15 seconds each)

Each member says one or two sentences about the part they are responsible for. Use the
same shape so the four of you sound balanced:

> *Rupinder:* I was responsible for the problem definition and the student journey: the
> landing page and the problem list. That's what I presented in the first part.
>
> *Ashmeen:* I was responsible for the worker pipeline and the sandbox, and I set up and ran
> the live demo.
>
> *Gourav:* I was responsible for how the components connect, the diagnosis method, and the
> use case and class diagrams.
>
> *Jasroop:* I was responsible for login, the recommendation flow, the sequence diagrams, and
> the status and evaluation results.

The "Where to find it" column is there so that, if the examiner asks, each of you can open
your own files straight away. Before the session, open them and make sure you can explain
them, and can make a small change in them.

## Slide 26 · Thank you and questions (Rupinder opens, everyone answers)

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
