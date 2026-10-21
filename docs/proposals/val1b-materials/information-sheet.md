# Information sheet: writing and reviewing buggy binary-search programs (draft)

**Study:** VAL1-B, an independent test of an automated feedback method for programming
exercises.

**Run by:** [OWNER NAME], [ROLE, e.g. student, Department of …], [INSTITUTION].

**Supervisor (if any):** [NAME]. **Contact:** [CONTACT EMAIL].

**Institutional review:** [record of the determination, e.g. "reviewed by … on …,
reference …", or "the … office determined on … that review is not required"]. This line
must be filled in before this sheet is given to anyone.

## What is this about?

CodeAdapt is a research prototype. It looks at C++ solutions to small binary-search
exercises and tries to say which common mistake a wrong solution contains, or says that it
cannot tell. We want to test it on programs written by people who have never seen how it
works, and to see whether experienced people agree with each other about what the mistake
in each program is.

This is a test of the **software**. It is not a test of you. We do not measure your
ability, record grades, or study how you learn.

## What would I do?

**If you are an author:**

- You read four short problem statements. Each one has two example tests.
- For each problem, you write 5 C++ programs that compile but are wrong. Each should
  contain a mistake you think a learner could plausibly make.
- You may also write up to 2 correct programs per problem.
- For each program, you write a one-line private note saying what mistake you intended.
- Please do not use AI code assistants or code generators for these programs, and please
  do not look at the CodeAdapt repository or its documentation before or during the task.
- Expected time: about 2–3 hours, at a time that suits you, within [PERIOD].

**If you are a labeller:**

- You do some practice items first.
- You then look at each program (about 60–100, without knowing who wrote it) and describe
  the mistake in your own words. You also give the smallest change that fixes it, and rate
  your confidence. You may compile and run the programs yourself.
- When you have handed that in, you do a second pass. In it, you match your own
  descriptions to a list of categories we provide, without changing your first answers.
- You must not discuss the programs with the other labeller until you have both handed in
  both passes.
- Expected time: about 4–6 hours in total, within [PERIOD].

## What will happen to what I give?

- **Programs.** Programs are stored under a random code (for example `A3`), never your
  name. With your permission, they are published in a public research repository under the
  licence named on the consent form (proposed: CC0 1.0, which places them in the public
  domain). Published code can be copied by anyone and cannot be recalled after publication.
- **Labels.** Labels (your descriptions, fixes, categories and confidence ratings) are
  stored under a code (`L1`/`L2`) and published with the programs on the same terms.
- **Your name, contact details and consent form** stay with [OWNER NAME] only. They are not
  put in the repository and are not shared with anyone else, including the AI assistant
  used to analyse the results.
- **Analysis.** The analysis is done partly by an AI assistant (Claude, made by Anthropic).
  It sees the programs and labels under their codes only.
- **The key that links codes to people** is deleted on [DATE, after the withdrawal
  deadline].

## Do I have to take part?

No. Taking part is voluntary.

- You can stop at any time without giving a reason.
- You can ask for your programs or labels to be withdrawn until [WITHDRAWAL DEADLINE, before
  publication and before analysis].
- After publication, already-published copies cannot be withdrawn.
- Not taking part, or withdrawing, has no effect on [any course, grade, job or
  relationship with the organiser].

## Payment

[None / amount and form, as decided by the owner.]

## Risks and benefits

- **Risks.** The risks are minimal: the time it takes, and the small possibility that
  someone recognises your coding style in published code.
- **Benefits.** There is no direct benefit to you. The results help show whether automated
  feedback of this kind can be trusted.

## Questions or concerns

Contact [OWNER NAME] at [CONTACT]. If you have a concern you would rather raise with
someone else, contact [SUPERVISOR / ETHICS OFFICE CONTACT].
