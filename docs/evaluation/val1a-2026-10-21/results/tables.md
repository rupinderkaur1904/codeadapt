## Results by style and pooled

### Style A: half-open (reference style)

| Category | Count |
| --- | ---: |
| compile_error | 0 |
| unreliable | 6 |
| equivalent | 4 |
| suite_gap | 0 |
| incorrect_failing | 34 |
| **total** | 44 |

| Metric (denominator: `incorrect_failing` unless stated) | Value |
| --- | --- |
| Coverage: diagnosed (any) | 14/34 (41%, 95% CI 26–58%) |
| — diagnosed, unqualified | 13/34 (38%, 95% CI 24–55%) |
| — diagnosed, qualified | 1/34 (3%, 95% CI 1–15%) |
| Abstained: ambiguous | 0/34 (0%, 95% CI 0–10%) |
| Abstained: insufficient_evidence | 0/34 (0%, 95% CI 0–10%) |
| Abstained: unmodelled_behaviour | 20/34 (59%, 95% CI 42–74%) |
| Concept agreement (strict labels; denominator: diagnoses) | 9/14 (64%, 95% CI 39–84%) |
| Cross-pattern diagnoses (strict; denominator: diagnoses) | 5/14 (36%, 95% CI 16–61%) |
| — of which unqualified | 5 |
| — cross-skill, unqualified (strict) | 5 |
| Library recall on labelled mutants (strict; denominator: labelled `incorrect_failing`) | 9/9 (100%, 95% CI 70–100%) |
| Concept agreement (lenient labels; denominator: diagnoses) | 9/14 (64%, 95% CI 39–84%) |
| Cross-pattern diagnoses (lenient; denominator: diagnoses) | 5/14 (36%, 95% CI 16–61%) |
| — of which unqualified | 5 |
| — cross-skill, unqualified (lenient) | 5 |
| Library recall on labelled mutants (lenient; denominator: labelled `incorrect_failing`) | 9/9 (100%, 95% CI 70–100%) |
| Suite gap (denominator: non-equivalent reliable mutants) | 0/34 (0%, 95% CI 0–10%) |
| Mutants with a library label (strict; denominator: all mutants) | 9/44 (20%, 95% CI 11–35%) |

### Style B: closed + answer variable

| Category | Count |
| --- | ---: |
| compile_error | 0 |
| unreliable | 9 |
| equivalent | 6 |
| suite_gap | 0 |
| incorrect_failing | 42 |
| **total** | 57 |

| Metric (denominator: `incorrect_failing` unless stated) | Value |
| --- | --- |
| Coverage: diagnosed (any) | 14/42 (33%, 95% CI 21–48%) |
| — diagnosed, unqualified | 14/42 (33%, 95% CI 21–48%) |
| — diagnosed, qualified | 0/42 (0%, 95% CI 0–8%) |
| Abstained: ambiguous | 0/42 (0%, 95% CI 0–8%) |
| Abstained: insufficient_evidence | 0/42 (0%, 95% CI 0–8%) |
| Abstained: unmodelled_behaviour | 28/42 (67%, 95% CI 52–79%) |
| Concept agreement (strict labels; denominator: diagnoses) | 2/14 (14%, 95% CI 4–40%) |
| Cross-pattern diagnoses (strict; denominator: diagnoses) | 12/14 (86%, 95% CI 60–96%) |
| — of which unqualified | 12 |
| — cross-skill, unqualified (strict) | 12 |
| Library recall on labelled mutants (strict; denominator: labelled `incorrect_failing`) | 2/2 (100%, 95% CI 34–100%) |
| Concept agreement (lenient labels; denominator: diagnoses) | 8/14 (57%, 95% CI 33–79%) |
| Cross-pattern diagnoses (lenient; denominator: diagnoses) | 6/14 (43%, 95% CI 21–67%) |
| — of which unqualified | 6 |
| — cross-skill, unqualified (lenient) | 6 |
| Library recall on labelled mutants (lenient; denominator: labelled `incorrect_failing`) | 8/10 (80%, 95% CI 49–94%) |
| Suite gap (denominator: non-equivalent reliable mutants) | 0/42 (0%, 95% CI 0–8%) |
| Mutants with a library label (strict; denominator: all mutants) | 2/57 (4%, 95% CI 1–12%) |

### Style C: recursive

| Category | Count |
| --- | ---: |
| compile_error | 0 |
| unreliable | 20 |
| equivalent | 4 |
| suite_gap | 0 |
| incorrect_failing | 22 |
| **total** | 46 |

| Metric (denominator: `incorrect_failing` unless stated) | Value |
| --- | --- |
| Coverage: diagnosed (any) | 4/22 (18%, 95% CI 7–39%) |
| — diagnosed, unqualified | 3/22 (14%, 95% CI 5–33%) |
| — diagnosed, qualified | 1/22 (5%, 95% CI 1–22%) |
| Abstained: ambiguous | 0/22 (0%, 95% CI 0–15%) |
| Abstained: insufficient_evidence | 0/22 (0%, 95% CI 0–15%) |
| Abstained: unmodelled_behaviour | 18/22 (82%, 95% CI 61–93%) |
| Concept agreement (strict labels; denominator: diagnoses) | 4/4 (100%, 95% CI 51–100%) |
| Cross-pattern diagnoses (strict; denominator: diagnoses) | 0/4 (0%, 95% CI 0–49%) |
| — of which unqualified | 0 |
| — cross-skill, unqualified (strict) | 0 |
| Library recall on labelled mutants (strict; denominator: labelled `incorrect_failing`) | 4/4 (100%, 95% CI 51–100%) |
| Concept agreement (lenient labels; denominator: diagnoses) | 4/4 (100%, 95% CI 51–100%) |
| Cross-pattern diagnoses (lenient; denominator: diagnoses) | 0/4 (0%, 95% CI 0–49%) |
| — of which unqualified | 0 |
| — cross-skill, unqualified (lenient) | 0 |
| Library recall on labelled mutants (lenient; denominator: labelled `incorrect_failing`) | 4/4 (100%, 95% CI 51–100%) |
| Suite gap (denominator: non-equivalent reliable mutants) | 0/22 (0%, 95% CI 0–15%) |
| Mutants with a library label (strict; denominator: all mutants) | 9/46 (20%, 95% CI 11–33%) |

### Styles B + C pooled

| Category | Count |
| --- | ---: |
| compile_error | 0 |
| unreliable | 29 |
| equivalent | 10 |
| suite_gap | 0 |
| incorrect_failing | 64 |
| **total** | 103 |

| Metric (denominator: `incorrect_failing` unless stated) | Value |
| --- | --- |
| Coverage: diagnosed (any) | 18/64 (28%, 95% CI 19–40%) |
| — diagnosed, unqualified | 17/64 (27%, 95% CI 17–38%) |
| — diagnosed, qualified | 1/64 (2%, 95% CI 0–8%) |
| Abstained: ambiguous | 0/64 (0%, 95% CI 0–6%) |
| Abstained: insufficient_evidence | 0/64 (0%, 95% CI 0–6%) |
| Abstained: unmodelled_behaviour | 46/64 (72%, 95% CI 60–81%) |
| Concept agreement (strict labels; denominator: diagnoses) | 6/18 (33%, 95% CI 16–56%) |
| Cross-pattern diagnoses (strict; denominator: diagnoses) | 12/18 (67%, 95% CI 44–84%) |
| — of which unqualified | 12 |
| — cross-skill, unqualified (strict) | 12 |
| Library recall on labelled mutants (strict; denominator: labelled `incorrect_failing`) | 6/6 (100%, 95% CI 61–100%) |
| Concept agreement (lenient labels; denominator: diagnoses) | 12/18 (67%, 95% CI 44–84%) |
| Cross-pattern diagnoses (lenient; denominator: diagnoses) | 6/18 (33%, 95% CI 16–56%) |
| — of which unqualified | 6 |
| — cross-skill, unqualified (lenient) | 6 |
| Library recall on labelled mutants (lenient; denominator: labelled `incorrect_failing`) | 12/14 (86%, 95% CI 60–96%) |
| Suite gap (denominator: non-equivalent reliable mutants) | 0/64 (0%, 95% CI 0–6%) |
| Mutants with a library label (strict; denominator: all mutants) | 11/103 (11%, 95% CI 6–18%) |

### All styles pooled

| Category | Count |
| --- | ---: |
| compile_error | 0 |
| unreliable | 35 |
| equivalent | 14 |
| suite_gap | 0 |
| incorrect_failing | 98 |
| **total** | 147 |

| Metric (denominator: `incorrect_failing` unless stated) | Value |
| --- | --- |
| Coverage: diagnosed (any) | 32/98 (33%, 95% CI 24–42%) |
| — diagnosed, unqualified | 30/98 (31%, 95% CI 22–40%) |
| — diagnosed, qualified | 2/98 (2%, 95% CI 1–7%) |
| Abstained: ambiguous | 0/98 (0%, 95% CI 0–4%) |
| Abstained: insufficient_evidence | 0/98 (0%, 95% CI 0–4%) |
| Abstained: unmodelled_behaviour | 66/98 (67%, 95% CI 58–76%) |
| Concept agreement (strict labels; denominator: diagnoses) | 15/32 (47%, 95% CI 31–64%) |
| Cross-pattern diagnoses (strict; denominator: diagnoses) | 17/32 (53%, 95% CI 36–69%) |
| — of which unqualified | 17 |
| — cross-skill, unqualified (strict) | 17 |
| Library recall on labelled mutants (strict; denominator: labelled `incorrect_failing`) | 15/15 (100%, 95% CI 80–100%) |
| Concept agreement (lenient labels; denominator: diagnoses) | 21/32 (66%, 95% CI 48–80%) |
| Cross-pattern diagnoses (lenient; denominator: diagnoses) | 11/32 (34%, 95% CI 20–52%) |
| — of which unqualified | 11 |
| — cross-skill, unqualified (lenient) | 11 |
| Library recall on labelled mutants (lenient; denominator: labelled `incorrect_failing`) | 21/23 (91%, 95% CI 73–98%) |
| Suite gap (denominator: non-equivalent reliable mutants) | 0/98 (0%, 95% CI 0–4%) |
| Mutants with a library label (strict; denominator: all mutants) | 20/147 (14%, 95% CI 9–20%) |

## Every diagnosis

| Mutant | Edit | Diagnosed model | Qualified | Groups | Strict label | Lenient label | Agrees (strict) |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| A_UOI_004 | `int hi = static_cast<int>(a.size());` → `int hi = (static_cast<int>(a.size()) - 1);` | hi_init_last_index | yes | 1 | hi_init_last_index | hi_init_last_index | yes |
| A_UOI_006 | `while (lo < hi) {` → `while ((lo - 1) < hi) {` | closed_loop_hi_mid | no | 9 | none | none | **no** |
| A_ROR_007 | `while (lo < hi) {` → `while (lo <= hi) {` | closed_loop_hi_mid | no | 9 | closed_loop_hi_mid | closed_loop_hi_mid | yes |
| A_UOI_012 | `while (lo < hi) {` → `while (lo < (hi + 1)) {` | closed_loop_hi_mid | no | 9 | closed_loop_hi_mid | closed_loop_hi_mid | yes |
| A_ROR_027 | `if (a[mid] < target) {` → `if (a[mid] <= target) {` | upper_bound_confusion | no | 6 | upper_bound_confusion | upper_bound_confusion | yes |
| A_UOI_034 | `lo = mid + 1;` → `lo = (mid - 1) + 1;` | no_progress_update | no | 6 | no_progress_update | no_progress_update | yes |
| A_AOR_035 | `lo = mid + 1;` → `lo = mid - 1;` | no_progress_update | no | 6 | none | none | **no** |
| A_ICR_037 | `lo = mid + 1;` → `lo = mid + 0;` | no_progress_update | no | 6 | no_progress_update | no_progress_update | yes |
| A_DEL_038 | `lo = mid + 1;` → `lo = mid;` | no_progress_update | no | 6 | no_progress_update | no_progress_update | yes |
| A_SDL_039 | `lo = mid + 1;` → `None` | no_progress_update | no | 6 | none | none | **no** |
| A_UOI_040 | `hi = mid;` → `hi = (mid + 1);` | closed_loop_hi_mid | no | 9 | none | none | **no** |
| A_UOI_041 | `hi = mid;` → `hi = (mid - 1);` | hi_skips_candidate | no | 3 | hi_skips_candidate | hi_skips_candidate | yes |
| A_SDL_042 | `hi = mid;` → `None` | closed_loop_hi_mid | no | 9 | none | none | **no** |
| A_UOI_044 | `return lo;` → `return (lo - 1);` | returns_wrong_pointer | no | 11 | returns_wrong_pointer | returns_wrong_pointer | yes |
| B_UOI_012 | `while (lo <= hi) {` → `while ((lo - 1) <= hi) {` | closed_loop_hi_mid | no | 9 | none | none | **no** |
| B_UOI_018 | `while (lo <= hi) {` → `while (lo <= (hi + 1)) {` | closed_loop_hi_mid | no | 9 | none | none | **no** |
| B_ROR_035 | `if (a[mid] >= target) {` → `if (a[mid] > target) {` | upper_bound_confusion | no | 6 | upper_bound_confusion | upper_bound_confusion | yes |
| B_UOI_042 | `hi = mid - 1;` → `hi = (mid + 1) - 1;` | closed_loop_hi_mid | no | 9 | none | closed_loop_hi_mid | **no** |
| B_AOR_044 | `hi = mid - 1;` → `hi = mid + 1;` | closed_loop_hi_mid | no | 9 | none | none | **no** |
| B_ICR_046 | `hi = mid - 1;` → `hi = mid - 0;` | closed_loop_hi_mid | no | 9 | none | closed_loop_hi_mid | **no** |
| B_DEL_047 | `hi = mid - 1;` → `hi = mid;` | closed_loop_hi_mid | no | 9 | none | closed_loop_hi_mid | **no** |
| B_SDL_048 | `hi = mid - 1;` → `None` | closed_loop_hi_mid | no | 9 | none | none | **no** |
| B_UOI_050 | `lo = mid + 1;` → `lo = (mid - 1) + 1;` | no_progress_update | no | 6 | none | no_progress_update | **no** |
| B_AOR_051 | `lo = mid + 1;` → `lo = mid - 1;` | no_progress_update | no | 6 | none | none | **no** |
| B_ICR_053 | `lo = mid + 1;` → `lo = mid + 0;` | no_progress_update | no | 6 | none | no_progress_update | **no** |
| B_DEL_054 | `lo = mid + 1;` → `lo = mid;` | no_progress_update | no | 6 | none | no_progress_update | **no** |
| B_SDL_055 | `lo = mid + 1;` → `None` | no_progress_update | no | 6 | none | none | **no** |
| B_UOI_057 | `return ans;` → `return (ans - 1);` | returns_wrong_pointer | no | 11 | returns_wrong_pointer | returns_wrong_pointer | yes |
| C_UOI_012 | `return lo;` → `return (lo - 1);` | returns_wrong_pointer | no | 11 | returns_wrong_pointer | returns_wrong_pointer | yes |
| C_ROR_025 | `if (a[mid] < target) {` → `if (a[mid] <= target) {` | upper_bound_confusion | no | 6 | upper_bound_confusion | upper_bound_confusion | yes |
| C_UOI_042 | `return search(a, target, lo, mid);` → `return search(a, target, lo, (mid - 1));` | hi_skips_candidate | no | 3 | hi_skips_candidate | hi_skips_candidate | yes |
| C_UOI_046 | `return search(a, target, 0, static_cast<int>(a.size()));` → `return search(a, target, 0, (static_cast<int>(a.size()) - 1));` | hi_init_last_index | yes | 1 | hi_init_last_index | hi_init_last_index | yes |

## Labelled mutants that were not diagnosed with their label

| Mutant | Edit | Strict label | Category | Outcome | Model / candidates |
| --- | --- | --- | --- | --- | --- |
| C_ROR_005 | `if (lo >= hi) {` → `if (lo > hi) {` | closed_loop_hi_mid | unreliable | unreliable_evidence | — |
| C_UOI_008 | `if (lo >= hi) {` → `if (lo >= (hi + 1)) {` | closed_loop_hi_mid | unreliable | unreliable_evidence | — |
| C_UOI_032 | `return search(a, target, mid + 1, hi);` → `return search(a, target, (mid - 1) + 1, hi);` | no_progress_update | unreliable | unreliable_evidence | — |
| C_ICR_035 | `return search(a, target, mid + 1, hi);` → `return search(a, target, mid + 0, hi);` | no_progress_update | unreliable | unreliable_evidence | — |
| C_DEL_038 | `return search(a, target, mid + 1, hi);` → `return search(a, target, mid, hi);` | no_progress_update | unreliable | unreliable_evidence | — |

## Collisions

| Model | Skill | Mutants diagnosed | Distinct strict labels | Styles |
| --- | --- | ---: | --- | --- |
| closed_loop_hi_mid | loop_termination | 12 | closed_loop_hi_mid ×2, none ×10 | AB |
| exact_match_sentinel | problem_specification | 0 | — | — |
| hi_init_last_index | search_space_boundaries | 2 | hi_init_last_index ×2 | AC |
| hi_skips_candidate | search_space_boundaries | 2 | hi_skips_candidate ×2 | AC |
| no_progress_update | loop_termination | 10 | no_progress_update ×3, none ×7 | AB |
| returns_wrong_pointer | problem_specification | 3 | returns_wrong_pointer ×3 | ABC |
| stops_at_first_match | equality_handling | 0 | — | — |
| upper_bound_confusion | equality_handling | 3 | upper_bound_confusion ×3 | ABC |

Among 98 `incorrect_failing` mutants there are 43 distinct full signature vectors; 26 are shared by 2 or more mutants (81 mutants).

- A_UOI_034, A_AOR_035, A_ICR_037, A_DEL_038, A_SDL_039, B_UOI_050, B_AOR_051, B_ICR_053, B_DEL_054, B_SDL_055
- A_UOI_040, A_SDL_042, B_UOI_042, B_AOR_044, B_ICR_046, B_DEL_047, B_SDL_048
- A_ROR_009, A_ROR_010, A_NEG_014, C_ROR_003, C_ROR_007, C_NEG_010
- A_UOI_005, A_UOI_013, C_UOI_001, C_UOI_009
- A_ROR_029, A_NEG_032, C_ROR_027, C_NEG_030
- A_UOI_033, A_ICR_036, C_UOI_031, C_ICR_034
- A_UOI_006, A_ROR_007, A_UOI_012
- A_ROR_027, B_ROR_035, C_ROR_025
- A_ROR_031, B_ROR_036, C_ROR_029
- A_UOI_043, B_UOI_056, C_UOI_011
- A_UOI_044, B_UOI_057, C_UOI_012
- B_UOI_011, B_ROR_013, B_UOI_019
- A_ICR_001, C_ICR_043
- A_UOI_004, C_UOI_046
- A_ROR_008, C_ROR_004
- A_UOI_018, A_UOI_022
- A_AOR_020, C_AOR_018
- A_ROR_028, C_ROR_026
- A_ROR_030, C_ROR_028
- A_UOI_041, C_UOI_042
- B_UOI_004, B_ICR_006
- B_UOI_012, B_UOI_018
- B_ROR_014, B_NEG_020
- B_ROR_033, B_NEG_038
- B_UOI_043, B_ICR_045
- B_UOI_049, B_ICR_052

## Abstentions on incorrect_failing mutants

| Mutant | Edit | Outcome | Candidates / nearest | Strict label |
| --- | --- | --- | --- | --- |
| A_ICR_001 | `int lo = 0;` → `int lo = 1;` | unmodelled_behaviour | stops_at_first_match(7), upper_bound_confusion(8), hi_init_last_index(10) | none |
| A_UOI_005 | `while (lo < hi) {` → `while ((lo + 1) < hi) {` | unmodelled_behaviour | hi_init_last_index(4), hi_skips_candidate(4), stops_at_first_match(8) | none |
| A_ROR_008 | `while (lo < hi) {` → `while (lo > hi) {` | unmodelled_behaviour | hi_skips_candidate(8), hi_init_last_index(9), no_progress_update(10) | none |
| A_ROR_009 | `while (lo < hi) {` → `while (lo >= hi) {` | unmodelled_behaviour | hi_skips_candidate(8), hi_init_last_index(9), no_progress_update(10) | none |
| A_ROR_010 | `while (lo < hi) {` → `while (lo == hi) {` | unmodelled_behaviour | hi_skips_candidate(8), hi_init_last_index(9), no_progress_update(10) | none |
| A_UOI_013 | `while (lo < hi) {` → `while (lo < (hi - 1)) {` | unmodelled_behaviour | hi_init_last_index(4), hi_skips_candidate(4), stops_at_first_match(8) | none |
| A_NEG_014 | `while (lo < hi) {` → `while (!(lo < hi)) {` | unmodelled_behaviour | hi_skips_candidate(8), hi_init_last_index(9), no_progress_update(10) | none |
| A_UOI_015 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = (lo + 1) + (hi - lo) / 2;` | unmodelled_behaviour | closed_loop_hi_mid(1), no_progress_update(7), stops_at_first_match(9) | none |
| A_UOI_016 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = (lo - 1) + (hi - lo) / 2;` | unmodelled_behaviour | no_progress_update(3), hi_init_last_index(6), stops_at_first_match(8) | none |
| A_UOI_018 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + ((hi + 1) - lo) / 2;` | unmodelled_behaviour | closed_loop_hi_mid(4), stops_at_first_match(8), hi_init_last_index(9) | none |
| A_AOR_020 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + (hi + lo) / 2;` | unmodelled_behaviour | hi_init_last_index(4), no_progress_update(6), hi_skips_candidate(7) | none |
| A_UOI_022 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + (hi - (lo - 1)) / 2;` | unmodelled_behaviour | closed_loop_hi_mid(4), stops_at_first_match(8), hi_init_last_index(9) | none |
| A_ROR_028 | `if (a[mid] < target) {` → `if (a[mid] > target) {` | unmodelled_behaviour | hi_init_last_index(11), hi_skips_candidate(11), no_progress_update(12) | none |
| A_ROR_029 | `if (a[mid] < target) {` → `if (a[mid] >= target) {` | unmodelled_behaviour | upper_bound_confusion(12), hi_init_last_index(15), closed_loop_hi_mid(16) | none |
| A_ROR_030 | `if (a[mid] < target) {` → `if (a[mid] == target) {` | unmodelled_behaviour | upper_bound_confusion(8), hi_init_last_index(14), hi_skips_candidate(14) | none |
| A_ROR_031 | `if (a[mid] < target) {` → `if (a[mid] != target) {` | unmodelled_behaviour | hi_skips_candidate(8), hi_init_last_index(9), stops_at_first_match(10) | none |
| A_NEG_032 | `if (a[mid] < target) {` → `if (!(a[mid] < target)) {` | unmodelled_behaviour | upper_bound_confusion(12), hi_init_last_index(15), closed_loop_hi_mid(16) | none |
| A_UOI_033 | `lo = mid + 1;` → `lo = (mid + 1) + 1;` | unmodelled_behaviour | hi_skips_candidate(7), hi_init_last_index(8), stops_at_first_match(9) | none |
| A_ICR_036 | `lo = mid + 1;` → `lo = mid + 2;` | unmodelled_behaviour | hi_skips_candidate(7), hi_init_last_index(8), stops_at_first_match(9) | none |
| A_UOI_043 | `return lo;` → `return (lo + 1);` | unmodelled_behaviour | upper_bound_confusion(13), exact_match_sentinel(16), stops_at_first_match(16) | none |
| B_ICR_001 | `int lo = 0;` → `int lo = 1;` | unmodelled_behaviour | stops_at_first_match(6), upper_bound_confusion(7), hi_init_last_index(9) | none |
| B_UOI_004 | `int hi = static_cast<int>(a.size()) - 1;` → `int hi = (static_cast<int>(a.size()) - 1) - 1;` | unmodelled_behaviour | hi_init_last_index(6), hi_skips_candidate(7), stops_at_first_match(7) | none |
| B_ICR_006 | `int hi = static_cast<int>(a.size()) - 1;` → `int hi = static_cast<int>(a.size()) - 2;` | unmodelled_behaviour | hi_init_last_index(6), hi_skips_candidate(7), stops_at_first_match(7) | none |
| B_UOI_009 | `int ans = static_cast<int>(a.size());` → `int ans = (static_cast<int>(a.size()) + 1);` | unmodelled_behaviour | hi_init_last_index(4), stops_at_first_match(8), hi_skips_candidate(9) | none |
| B_UOI_010 | `int ans = static_cast<int>(a.size());` → `int ans = (static_cast<int>(a.size()) - 1);` | unmodelled_behaviour | hi_init_last_index(1), stops_at_first_match(8), hi_skips_candidate(9) | none |
| B_UOI_011 | `while (lo <= hi) {` → `while ((lo + 1) <= hi) {` | unmodelled_behaviour | upper_bound_confusion(8), hi_skips_candidate(10), stops_at_first_match(10) | none |
| B_ROR_013 | `while (lo <= hi) {` → `while (lo < hi) {` | unmodelled_behaviour | upper_bound_confusion(8), hi_skips_candidate(10), stops_at_first_match(10) | none |
| B_ROR_014 | `while (lo <= hi) {` → `while (lo > hi) {` | unmodelled_behaviour | upper_bound_confusion(8), closed_loop_hi_mid(13), hi_skips_candidate(13) | none |
| B_ROR_015 | `while (lo <= hi) {` → `while (lo >= hi) {` | unmodelled_behaviour | upper_bound_confusion(9), closed_loop_hi_mid(12), hi_skips_candidate(13) | none |
| B_ROR_016 | `while (lo <= hi) {` → `while (lo == hi) {` | unmodelled_behaviour | upper_bound_confusion(9), hi_skips_candidate(12), stops_at_first_match(12) | none |
| B_ROR_017 | `while (lo <= hi) {` → `while (lo != hi) {` | unmodelled_behaviour | closed_loop_hi_mid(8), upper_bound_confusion(10), hi_skips_candidate(13) | none |
| B_UOI_019 | `while (lo <= hi) {` → `while (lo <= (hi - 1)) {` | unmodelled_behaviour | upper_bound_confusion(8), hi_skips_candidate(10), stops_at_first_match(10) | none |
| B_NEG_020 | `while (lo <= hi) {` → `while (!(lo <= hi)) {` | unmodelled_behaviour | upper_bound_confusion(8), closed_loop_hi_mid(13), hi_skips_candidate(13) | none |
| B_UOI_021 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = (lo + 1) + (hi - lo) / 2;` | unmodelled_behaviour | closed_loop_hi_mid(4), stops_at_first_match(8), hi_init_last_index(9) | none |
| B_UOI_031 | `if (a[mid] >= target) {` → `if (a[(mid + 1)] >= target) {` | unmodelled_behaviour | hi_skips_candidate(2), returns_wrong_pointer(6), hi_init_last_index(7) | none |
| B_ROR_033 | `if (a[mid] >= target) {` → `if (a[mid] < target) {` | unmodelled_behaviour | upper_bound_confusion(12), hi_init_last_index(15), hi_skips_candidate(15) | none |
| B_ROR_034 | `if (a[mid] >= target) {` → `if (a[mid] <= target) {` | unmodelled_behaviour | hi_skips_candidate(10), hi_init_last_index(11), no_progress_update(12) | none |
| B_ROR_036 | `if (a[mid] >= target) {` → `if (a[mid] == target) {` | unmodelled_behaviour | hi_skips_candidate(8), hi_init_last_index(9), stops_at_first_match(10) | none |
| B_ROR_037 | `if (a[mid] >= target) {` → `if (a[mid] != target) {` | unmodelled_behaviour | upper_bound_confusion(9), hi_init_last_index(14), hi_skips_candidate(14) | none |
| B_NEG_038 | `if (a[mid] >= target) {` → `if (!(a[mid] >= target)) {` | unmodelled_behaviour | upper_bound_confusion(12), hi_init_last_index(15), hi_skips_candidate(15) | none |
| B_UOI_039 | `ans = mid;` → `ans = (mid + 1);` | unmodelled_behaviour | upper_bound_confusion(9), stops_at_first_match(12), closed_loop_hi_mid(13) | none |
| B_UOI_040 | `ans = mid;` → `ans = (mid - 1);` | unmodelled_behaviour | returns_wrong_pointer(4), hi_skips_candidate(8), closed_loop_hi_mid(13) | none |
| B_SDL_041 | `ans = mid;` → `None` | unmodelled_behaviour | upper_bound_confusion(8), closed_loop_hi_mid(13), hi_skips_candidate(13) | none |
| B_UOI_043 | `hi = mid - 1;` → `hi = (mid - 1) - 1;` | unmodelled_behaviour | stops_at_first_match(7), hi_init_last_index(8), hi_skips_candidate(8) | none |
| B_ICR_045 | `hi = mid - 1;` → `hi = mid - 2;` | unmodelled_behaviour | stops_at_first_match(7), hi_init_last_index(8), hi_skips_candidate(8) | none |
| B_UOI_049 | `lo = mid + 1;` → `lo = (mid + 1) + 1;` | unmodelled_behaviour | hi_skips_candidate(7), hi_init_last_index(10), no_progress_update(10) | none |
| B_ICR_052 | `lo = mid + 1;` → `lo = mid + 2;` | unmodelled_behaviour | hi_skips_candidate(7), hi_init_last_index(10), no_progress_update(10) | none |
| B_UOI_056 | `return ans;` → `return (ans + 1);` | unmodelled_behaviour | upper_bound_confusion(13), exact_match_sentinel(16), stops_at_first_match(16) | none |
| C_UOI_001 | `if (lo >= hi) {` → `if ((lo + 1) >= hi) {` | unmodelled_behaviour | hi_init_last_index(4), hi_skips_candidate(4), stops_at_first_match(8) | none |
| C_ROR_003 | `if (lo >= hi) {` → `if (lo < hi) {` | unmodelled_behaviour | hi_skips_candidate(8), hi_init_last_index(9), no_progress_update(10) | none |
| C_ROR_004 | `if (lo >= hi) {` → `if (lo <= hi) {` | unmodelled_behaviour | hi_skips_candidate(8), hi_init_last_index(9), no_progress_update(10) | none |
| C_ROR_007 | `if (lo >= hi) {` → `if (lo != hi) {` | unmodelled_behaviour | hi_skips_candidate(8), hi_init_last_index(9), no_progress_update(10) | none |
| C_UOI_009 | `if (lo >= hi) {` → `if (lo >= (hi - 1)) {` | unmodelled_behaviour | hi_init_last_index(4), hi_skips_candidate(4), stops_at_first_match(8) | none |
| C_NEG_010 | `if (lo >= hi) {` → `if (!(lo >= hi)) {` | unmodelled_behaviour | hi_skips_candidate(8), hi_init_last_index(9), no_progress_update(10) | none |
| C_UOI_011 | `return lo;` → `return (lo + 1);` | unmodelled_behaviour | upper_bound_confusion(13), exact_match_sentinel(16), stops_at_first_match(16) | none |
| C_AOR_018 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + (hi + lo) / 2;` | unmodelled_behaviour | hi_init_last_index(2), hi_skips_candidate(5), stops_at_first_match(5) | none |
| C_ROR_026 | `if (a[mid] < target) {` → `if (a[mid] > target) {` | unmodelled_behaviour | hi_init_last_index(11), hi_skips_candidate(11), no_progress_update(12) | none |
| C_ROR_027 | `if (a[mid] < target) {` → `if (a[mid] >= target) {` | unmodelled_behaviour | upper_bound_confusion(12), hi_init_last_index(15), closed_loop_hi_mid(16) | none |
| C_ROR_028 | `if (a[mid] < target) {` → `if (a[mid] == target) {` | unmodelled_behaviour | upper_bound_confusion(8), hi_init_last_index(14), hi_skips_candidate(14) | none |
| C_ROR_029 | `if (a[mid] < target) {` → `if (a[mid] != target) {` | unmodelled_behaviour | hi_skips_candidate(8), hi_init_last_index(9), stops_at_first_match(10) | none |
| C_NEG_030 | `if (a[mid] < target) {` → `if (!(a[mid] < target)) {` | unmodelled_behaviour | upper_bound_confusion(12), hi_init_last_index(15), closed_loop_hi_mid(16) | none |
| C_UOI_031 | `return search(a, target, mid + 1, hi);` → `return search(a, target, (mid + 1) + 1, hi);` | unmodelled_behaviour | hi_skips_candidate(7), hi_init_last_index(8), stops_at_first_match(9) | none |
| C_ICR_034 | `return search(a, target, mid + 1, hi);` → `return search(a, target, mid + 2, hi);` | unmodelled_behaviour | hi_skips_candidate(7), hi_init_last_index(8), stops_at_first_match(9) | none |
| C_UOI_037 | `return search(a, target, mid + 1, hi);` → `return search(a, target, mid + 1, (hi - 1));` | unmodelled_behaviour | hi_init_last_index(4), hi_skips_candidate(7), stops_at_first_match(8) | none |
| C_UOI_039 | `return search(a, target, lo, mid);` → `return search(a, target, (lo + 1), mid);` | unmodelled_behaviour | upper_bound_confusion(6), stops_at_first_match(7), hi_init_last_index(11) | none |
| C_ICR_043 | `return search(a, target, 0, static_cast<int>(a.size()));` → `return search(a, target, 1, static_cast<int>(a.size()));` | unmodelled_behaviour | stops_at_first_match(7), upper_bound_confusion(8), hi_init_last_index(10) | none |

## Other categories

| Mutant | Edit | Category | Outcome | Native | Excluded tests |
| --- | --- | --- | --- | --- | --- |
| A_ICR_002 | `int lo = 0;` → `int lo = -1;` | unreliable | unreliable_evidence | non_equivalent | below_all: sanitizer: heap-buffer-overflow; duplicates_all: sanitizer: heap-buffer-overflow; empty: sanitizer: null-pointer (+4) |
| A_UOI_003 | `int hi = static_cast<int>(a.size());` → `int hi = (static_cast<int>(a.size()) + 1);` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: heap-buffer-overflow; empty: sanitizer: null-pointer; large_above_all: sanitizer: heap-buffer-overflow (+2) |
| A_ROR_011 | `while (lo < hi) {` → `while (lo != hi) {` | equivalent | no_failure_observed | equivalent |  |
| A_AOR_017 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo - (hi - lo) / 2;` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: heap-buffer-overflow; absent_after_duplicates: sanitizer: heap-buffer-overflow; below_all: sanitizer: heap-buffer-overflow (+8) |
| A_UOI_019 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + ((hi - 1) - lo) / 2;` | equivalent | no_failure_observed | equivalent |  |
| A_UOI_021 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + (hi - (lo + 1)) / 2;` | equivalent | no_failure_observed | equivalent |  |
| A_ICR_023 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + (hi - lo) / 3;` | equivalent | no_failure_observed | equivalent |  |
| A_ICR_024 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + (hi - lo) / 1;` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: heap-buffer-overflow; absent_after_duplicates: sanitizer: heap-buffer-overflow; below_all: sanitizer: heap-buffer-overflow (+13) |
| A_UOI_025 | `if (a[mid] < target) {` → `if (a[(mid + 1)] < target) {` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: heap-buffer-overflow; large_above_all: sanitizer: heap-buffer-overflow; pair_equal_target: sanitizer: heap-buffer-overflow (+3) |
| A_UOI_026 | `if (a[mid] < target) {` → `if (a[(mid - 1)] < target) {` | unreliable | unreliable_evidence | non_equivalent | below_all: sanitizer: heap-buffer-overflow; duplicates_all: sanitizer: heap-buffer-overflow; equal_first: sanitizer: heap-buffer-overflow (+4) |
| B_ICR_002 | `int lo = 0;` → `int lo = -1;` | unreliable | unreliable_evidence | non_equivalent | below_all: sanitizer: heap-buffer-overflow; duplicates_all: sanitizer: heap-buffer-overflow; empty: sanitizer: null-pointer (+5) |
| B_UOI_003 | `int hi = static_cast<int>(a.size()) - 1;` → `int hi = (static_cast<int>(a.size()) + 1) - 1;` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: heap-buffer-overflow; empty: sanitizer: null-pointer; large_above_all: sanitizer: heap-buffer-overflow (+1) |
| B_AOR_005 | `int hi = static_cast<int>(a.size()) - 1;` → `int hi = static_cast<int>(a.size()) + 1;` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: heap-buffer-overflow; empty: sanitizer: null-pointer; large_above_all: sanitizer: heap-buffer-overflow (+2) |
| B_ICR_007 | `int hi = static_cast<int>(a.size()) - 1;` → `int hi = static_cast<int>(a.size()) - 0;` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: heap-buffer-overflow; empty: sanitizer: null-pointer; large_above_all: sanitizer: heap-buffer-overflow (+1) |
| B_DEL_008 | `int hi = static_cast<int>(a.size()) - 1;` → `int hi = static_cast<int>(a.size());` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: heap-buffer-overflow; empty: sanitizer: null-pointer; large_above_all: sanitizer: heap-buffer-overflow (+1) |
| B_UOI_022 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = (lo - 1) + (hi - lo) / 2;` | unreliable | unreliable_evidence | non_equivalent | duplicates_all: sanitizer: heap-buffer-overflow; duplicates_middle: sanitizer: heap-buffer-overflow; pair_equal_target: sanitizer: heap-buffer-overflow (+3) |
| B_AOR_023 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo - (hi - lo) / 2;` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: heap-buffer-overflow; absent_after_duplicates: sanitizer: heap-buffer-overflow; below_all: sanitizer: heap-buffer-overflow (+6) |
| B_UOI_024 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + ((hi + 1) - lo) / 2;` | equivalent | no_failure_observed | equivalent |  |
| B_UOI_025 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + ((hi - 1) - lo) / 2;` | equivalent | no_failure_observed | equivalent |  |
| B_AOR_026 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + (hi + lo) / 2;` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: heap-buffer-overflow; absent_after_duplicates: sanitizer: heap-buffer-overflow; equal_last: sanitizer: heap-buffer-overflow (+3) |
| B_UOI_027 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + (hi - (lo + 1)) / 2;` | equivalent | no_failure_observed | equivalent |  |
| B_UOI_028 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + (hi - (lo - 1)) / 2;` | equivalent | no_failure_observed | equivalent |  |
| B_ICR_029 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + (hi - lo) / 3;` | equivalent | no_failure_observed | equivalent |  |
| B_ICR_030 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + (hi - lo) / 1;` | equivalent | no_failure_observed | equivalent |  |
| B_UOI_032 | `if (a[mid] >= target) {` → `if (a[(mid - 1)] >= target) {` | unreliable | unreliable_evidence | non_equivalent | below_all: sanitizer: heap-buffer-overflow; duplicates_all: sanitizer: heap-buffer-overflow; duplicates_middle: sanitizer: heap-buffer-overflow (+6) |
| C_UOI_002 | `if (lo >= hi) {` → `if ((lo - 1) >= hi) {` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: heap-buffer-overflow; absent_after_duplicates: sanitizer: stack-overflow; below_all: sanitizer: stack-overflow (+14) |
| C_ROR_005 | `if (lo >= hi) {` → `if (lo > hi) {` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: heap-buffer-overflow; absent_after_duplicates: sanitizer: stack-overflow; below_all: sanitizer: stack-overflow (+14) |
| C_ROR_006 | `if (lo >= hi) {` → `if (lo == hi) {` | equivalent | no_failure_observed | equivalent |  |
| C_UOI_008 | `if (lo >= hi) {` → `if (lo >= (hi + 1)) {` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: heap-buffer-overflow; absent_after_duplicates: sanitizer: stack-overflow; below_all: sanitizer: stack-overflow (+14) |
| C_UOI_013 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = (lo + 1) + (hi - lo) / 2;` | unreliable | unreliable_evidence | non_equivalent | below_all: sanitizer: stack-overflow; duplicates_all: sanitizer: stack-overflow; duplicates_middle: sanitizer: stack-overflow (+10) |
| C_UOI_014 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = (lo - 1) + (hi - lo) / 2;` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: stack-overflow; duplicates_middle: sanitizer: stack-overflow; equal_last: sanitizer: stack-overflow (+6) |
| C_AOR_015 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo - (hi - lo) / 2;` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: heap-buffer-overflow; absent_after_duplicates: sanitizer: heap-buffer-overflow; below_all: sanitizer: heap-buffer-overflow (+8) |
| C_UOI_016 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + ((hi + 1) - lo) / 2;` | unreliable | unreliable_evidence | non_equivalent | below_all: sanitizer: stack-overflow; duplicates_all: sanitizer: stack-overflow; duplicates_middle: sanitizer: stack-overflow (+8) |
| C_UOI_017 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + ((hi - 1) - lo) / 2;` | equivalent | no_failure_observed | equivalent |  |
| C_UOI_019 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + (hi - (lo + 1)) / 2;` | equivalent | no_failure_observed | equivalent |  |
| C_UOI_020 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + (hi - (lo - 1)) / 2;` | unreliable | unreliable_evidence | non_equivalent | below_all: sanitizer: stack-overflow; duplicates_all: sanitizer: stack-overflow; duplicates_middle: sanitizer: stack-overflow (+8) |
| C_ICR_021 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + (hi - lo) / 3;` | equivalent | no_failure_observed | equivalent |  |
| C_ICR_022 | `const int mid = lo + (hi - lo) / 2;` → `const int mid = lo + (hi - lo) / 1;` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: heap-buffer-overflow; absent_after_duplicates: sanitizer: heap-buffer-overflow; below_all: sanitizer: heap-buffer-overflow (+13) |
| C_UOI_023 | `if (a[mid] < target) {` → `if (a[(mid + 1)] < target) {` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: heap-buffer-overflow; large_above_all: sanitizer: heap-buffer-overflow; pair_equal_target: sanitizer: heap-buffer-overflow (+3) |
| C_UOI_024 | `if (a[mid] < target) {` → `if (a[(mid - 1)] < target) {` | unreliable | unreliable_evidence | non_equivalent | below_all: sanitizer: heap-buffer-overflow; duplicates_all: sanitizer: heap-buffer-overflow; equal_first: sanitizer: heap-buffer-overflow (+4) |
| C_UOI_032 | `return search(a, target, mid + 1, hi);` → `return search(a, target, (mid - 1) + 1, hi);` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: stack-overflow; absent_after_duplicates: sanitizer: stack-overflow; duplicates_middle: sanitizer: stack-overflow (+7) |
| C_AOR_033 | `return search(a, target, mid + 1, hi);` → `return search(a, target, mid - 1, hi);` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: stack-overflow; absent_after_duplicates: sanitizer: stack-overflow; duplicates_middle: sanitizer: stack-overflow (+7) |
| C_ICR_035 | `return search(a, target, mid + 1, hi);` → `return search(a, target, mid + 0, hi);` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: stack-overflow; absent_after_duplicates: sanitizer: stack-overflow; duplicates_middle: sanitizer: stack-overflow (+7) |
| C_UOI_036 | `return search(a, target, mid + 1, hi);` → `return search(a, target, mid + 1, (hi + 1));` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: heap-buffer-overflow; equal_last: sanitizer: heap-buffer-overflow; large_above_all: sanitizer: heap-buffer-overflow (+1) |
| C_DEL_038 | `return search(a, target, mid + 1, hi);` → `return search(a, target, mid, hi);` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: stack-overflow; absent_after_duplicates: sanitizer: stack-overflow; duplicates_middle: sanitizer: stack-overflow (+7) |
| C_UOI_040 | `return search(a, target, lo, mid);` → `return search(a, target, (lo - 1), mid);` | unreliable | unreliable_evidence | non_equivalent | below_all: sanitizer: heap-buffer-overflow; duplicates_all: sanitizer: heap-buffer-overflow; duplicates_middle: sanitizer: heap-buffer-overflow (+4) |
| C_UOI_041 | `return search(a, target, lo, mid);` → `return search(a, target, lo, (mid + 1));` | unreliable | unreliable_evidence | non_equivalent | absent_after_duplicates: sanitizer: stack-overflow; below_all: sanitizer: stack-overflow; duplicates_all: sanitizer: stack-overflow (+10) |
| C_ICR_044 | `return search(a, target, 0, static_cast<int>(a.size()));` → `return search(a, target, -1, static_cast<int>(a.size()));` | unreliable | unreliable_evidence | non_equivalent | below_all: sanitizer: heap-buffer-overflow; duplicates_all: sanitizer: heap-buffer-overflow; empty: sanitizer: null-pointer (+4) |
| C_UOI_045 | `return search(a, target, 0, static_cast<int>(a.size()));` → `return search(a, target, 0, (static_cast<int>(a.size()) + 1));` | unreliable | unreliable_evidence | non_equivalent | above_all: sanitizer: heap-buffer-overflow; empty: sanitizer: null-pointer; large_above_all: sanitizer: heap-buffer-overflow (+2) |

