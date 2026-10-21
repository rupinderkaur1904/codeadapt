# Practice key (for discussion after the practice items only)

Expected outputs on `[1,1,2,2,2,1]`, `[]`, `[5]`, `[1,2,3]`, `[4,4,4]`, `[1,1,2]`:
`3 0 1 1 3 2`.

The key is written in plain words, not in any study category, so discussing it does not
teach the stage-2 categories.

| Program | Correct? | Primary error | Minimal fix |
| --- | --- | --- | --- |
| practice_1.cpp | no (prints `3 0 0 1 0 2`; it passes the first sample) | The last run is never compared with `best`, because the comparison happens only when a run ends inside the loop. | Replace `return best;` with `return current > best ? current : best;` |
| practice_2.cpp | no (prints `2 0 0 0 2 1`) | A new run starts at length 0 instead of 1, so every run is counted one short. | Replace `current = 0;` (in the `else`) with `current = 1;` |
| practice_3.cpp | yes (prints `3 0 1 1 3 2`) | none | none |

Practice items are excluded from every result (protocol §4, stage 0).
