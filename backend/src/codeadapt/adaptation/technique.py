"""Technique-evidence eligibility: banned library names in a submission (D1, ADR-035).

A statement may forbid named library calls ("Do not call `std::upper_bound`"). An attempt
that names one of them still runs and is still diagnosed, but it gives no skill
observations: a pass that relies on the library says nothing about the skills the problem
assesses.

This is a static token match after removing comments and string and character literals. It
shows that a banned name appears in the source as a call or a qualified name. It does not show
which algorithm the program uses, that the call is reached, or anything about complexity. A
macro, a function pointer obtained some other way, or a hand-written linear scan is not
detected. A program's own function, lambda or variable of the banned name is not counted as the
library call; such a program that also calls the library function unqualified is missed.

The result is recomputed from the stored source whenever evidence is read, so a change to this
detector applies to earlier attempts too (docs/limitations.md L23).
"""

from __future__ import annotations

import re
from collections.abc import Iterable

# Researcher-facing; students are not shown this (owner instruction 2026-10-26).
TECHNIQUE_NOTE = (
    "Static token match after removing comments and literals. A found name means the attempt "
    "gives no skill observations; it does not show which algorithm the program uses, that the "
    "call is reached, or anything about its complexity. An attempt with no name found is not "
    "verified to use the intended technique either."
)

_COMMENT_OR_LITERAL = re.compile(
    r"""//[^\n]*|/\*.*?\*/|R"(?P<d>[^()\\\s]{0,16})\(.*?\)(?P=d)"|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'""",
    re.DOTALL,
)


def strip_comments_and_literals(source: str) -> str:
    """Replace comments and string/character literals with a space, keeping the code."""
    return _COMMENT_OR_LITERAL.sub(" ", source)


def _detected(code: str, name: str) -> bool:
    word = re.escape(name.rsplit("::", 1)[-1])
    # A qualified use, called or not: std::name, std::ranges::name, and `using std::name;`.
    # C library functions count too: std::sqrt is sqrt.
    if re.search(rf"\bstd\s*::\s*(ranges\s*::\s*)?{word}\b", code):
        return True
    # An unqualified call, as after `using namespace std;`, or a C library function. Member
    # calls (`s.find(`, `p->find(`) and other namespaces (`mine::find(`) are other functions,
    # except `ranges::name(` after `using namespace std;`.
    call = rf"(?:(?<![\w.:>])|(?<=ranges::)){word}\s*(?:<[^;(){{}}]*>)?\s*\("
    if not re.search(call, code):
        return False
    # A program that defines its own function of that name calls its own function. So does
    # one that declares a variable of that name with an initialiser (a lambda or a
    # std::function: `auto pow = [](long long v) { ... };`).
    own = rf"[\w>&*]\s+{word}\s*\([^;{{}}]*\)\s*(?:const\s*)?\{{"
    variable = rf"[\w>&*]\s+{word}\s*=(?!=)"
    return re.search(own, code) is None and re.search(variable, code) is None


def banned_names_found(source: str, banned: Iterable[str]) -> tuple[str, ...]:
    """The banned names (as the statement writes them) that appear in `source`."""
    code = strip_comments_and_literals(source)
    return tuple(sorted(name for name in set(banned) if _detected(code, name)))
