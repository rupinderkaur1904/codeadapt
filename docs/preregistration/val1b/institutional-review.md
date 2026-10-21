# Institutional review: questions and recorded determination

**Status: NOT YET REQUESTED.** Recruitment is blocked until §2 is filled in with the
institution's actual answer. Exemption is not assumed.

## 1. Questions to send to the supervisor and/or ethics office

Please attach `materials/information-sheet.md`, `materials/consent-form.md`,
`materials/recruitment.md`, `materials/licence.md` and `protocol.md`.

1. **Scope.** Does a study fall under the institution's human-participants research
   policy if participants donate artefacts they create (deliberately buggy programs) and
   expert judgements about those artefacts (labels)? It collects no data about the
   participants themselves, such as performance, learning, opinions or demographics.
2. **Review route.** If it is in scope, which review route applies: full, expedited or
   minimal-risk, or exempt with registration? Who must make that determination (supervisor,
   department or ethics committee)?
3. **Recruiting students.** May the organiser invite fellow students, or students at the
   same institution? What conditions apply? Are there restrictions when the organiser is a
   student, or holds a teaching or assessment role?
4. **Degree or course work.** The work is part of [degree project / course / independent
   research; owner to state]. Does that change the route, or require supervisor sign-off?
5. **Publication of donated material.** May participants' code and labels be published in
   a public repository under a public-domain dedication (CC0 1.0) when an individual
   contributor explicitly opts in (private use is the default), given the consent wording? Does the institution have an intellectual-property or research-data policy
   that affects this?
6. **Personal data.** Names, contact details and signed consent forms are held only by the
   organiser, outside the repository, and the code key is deleted after [DATE]. Does this
   meet the institution's requirements and applicable data-protection law? Is a data
   management plan required?
7. **AI-assisted analysis.** Pseudonymised programs and labels are analysed with an AI
   assistant (Claude, Anthropic), which never receives identities. Does this need to be
   disclosed differently, or approved?
8. **Payment.** If participants are compensated, are there rules on the amount or form?
9. **Templates.** Must the institution's own information-sheet or consent templates be used
   instead of these drafts?

## 2. Determination record (to be filled in by the owner)

| Field | Entry |
| --- | --- |
| Date the questions were sent | |
| Sent to (role and office) | |
| Date of answer | |
| Body that answered | |
| Answer, verbatim or attached | |
| Reference number, if any | |
| Conditions imposed | |
| Changes required to the protocol or materials | |
| Recorded by, and date | |

If the answer imposes changes, the protocol and materials are revised and re-approved by
the owner before recruitment.

## 3. Data handling (as proposed; subject to §2)

| Item | Where it is kept | Who sees it | Deleted |
| --- | --- | --- | --- |
| Names, contacts, signed forms | Owner's private storage, outside the repository | Owner only | [retention period per institution] |
| Code key (person to `A1`, `L1`) | Owner's private storage | Owner only | [DATE] after the withdrawal deadline |
| Programs, notes, labels (coded) | Study repository (public or private per consent) | Owner, Claude, readers if public | Not deleted if published |

## 4. Request message (ready for the owner to send; Claude does not send it)

> Subject: Does this small software-evaluation study need ethics review before recruitment?
>
> Dear [SUPERVISOR / ETHICS OFFICE],
>
> I am [OWNER NAME], [ROLE]. As part of [degree project / independent research], I am
> building CodeAdapt, a research prototype that gives automated feedback on small C++
> binary-search exercises. Before any use with learners, I want to test it on programs
> written independently of me.
>
> The study would ask 3–5 volunteers (adults who write C++) to write deliberately buggy
> solutions to four exercises, about 2–3 hours each, and 2 volunteers with teaching or
> code-review experience to describe the error in each program, about 4–6 hours each.
> No data about the participants themselves (performance, learning, opinions,
> demographics) is collected. Programs and labels are stored under codes; names, contact
> details and consent forms stay with me only. Contributors may opt in to publishing their
> code under CC0; otherwise it stays private. Pseudonymised material is analysed with an AI
> assistant that never receives identities.
>
> I have not contacted anyone. Could you tell me whether this requires review, and if so
> which route, and answer the questions in the attached note (§1)? I attach the protocol,
> information sheet, consent form, recruitment criteria and licence note.
>
> Thank you,
> [OWNER NAME]
