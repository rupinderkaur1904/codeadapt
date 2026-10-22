"""VAL1-A2: generate single-edit mutants of the originals of the three remaining problems.

The operators are VAL1-A's (../val1a-2026-10-21/generate.py), with the two mechanical
adaptations of PLAN.md §3: `flags.size()` is a size expression and `n` is a variable.

Run from the repository root:  python3 docs/evaluation/val1a2-2026-10-22/generate.py

Writes eval/mutation/<problem>/mutants/*.cpp and manifest.json (deterministic).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROBLEMS = ("count-occurrences", "last-less-than", "first-true")
STYLES = {"A": "half_open", "B": "closed_answer", "C": "recursive"}

TOKEN = re.compile(
    r"(?P<size>static_cast<int>\((?:a|flags)\.size\(\)\))"
    r"|(?P<ident>[A-Za-z_]\w*)"
    r"|(?P<num>\d+)"
    r"|(?P<op><=|>=|==|!=|&&|\|\||[<>+\-*/=!])"
    r"|(?P<other>\S)"
    r"|(?P<ws>\s+)"
)
RELATIONAL = ["<", "<=", ">", ">=", "==", "!="]
VARIABLES = {"lo", "hi", "mid", "ans", "n"}


def tokens(line: str) -> list[tuple[str, str]]:
    return [(m.lastgroup or "", m.group()) for m in TOKEN.finditer(line)]


def mutable(line: str) -> bool:
    s = line.strip()
    if not s or s.startswith(("#", "//")) or s in ("{", "}", "} else {"):
        return False
    # Signature lines (function definitions) are never mutated.
    return not re.match(r"^(static\s+)?int\s+\w+\(const std::vector<int>&", s)


def is_target(toks: list[tuple[str, str]], i: int) -> bool:
    """True when token i is assigned or declared (not a read)."""
    nxt = next((t for t in toks[i + 1 :] if t[0] != "ws"), ("", ""))
    prev = [t for t in toks[:i] if t[0] != "ws"]
    declared = bool(prev) and prev[-1][1] == "int"
    return nxt == ("op", "=") or declared


def join(toks: list[tuple[str, str]]) -> str:
    return "".join(t[1] for t in toks)


def edits(line: str) -> list[tuple[str, str, str]]:
    """(operator, description, mutated line) for every single edit of `line`."""
    toks = tokens(line)
    out: list[tuple[str, str, str]] = []
    for i, (kind, text) in enumerate(toks):
        if kind == "op" and text in RELATIONAL:
            for r in RELATIONAL:
                if r != text:
                    out.append(("ROR", f"{text} -> {r}", join(toks[:i] + [("op", r)] + toks[i + 1 :])))
        if kind == "op" and text in "+-" and len(text) == 1:
            r = "-" if text == "+" else "+"
            out.append(("AOR", f"{text} -> {r}", join(toks[:i] + [("op", r)] + toks[i + 1 :])))
        if kind == "num":
            k = int(text)
            for r in (k + 1, k - 1):
                out.append(("ICR", f"{k} -> {r}", join(toks[:i] + [("num", str(r))] + toks[i + 1 :])))
        if (kind == "ident" and text in VARIABLES and not is_target(toks, i)) or kind == "size":
            for sign in ("+", "-"):
                rep = f"({text} {sign} 1)"
                out.append(("UOI", f"{text} -> {rep}", join(toks[:i] + [("x", rep)] + toks[i + 1 :])))
    # DEL: remove each "+ 1" / "- 1" term.
    for m in re.finditer(r"\s*[+-]\s*1\b", line):
        out.append(("DEL", f"delete '{m.group().strip()}'", line[: m.start()] + line[m.end() :]))
    # NEG: negate an if/while condition.
    m = re.match(r"^(\s*)(if|while) \((.*)\) \{\s*$", line)
    if m:
        out.append(("NEG", f"negate {m.group(2)} condition", f"{m.group(1)}{m.group(2)} (!({m.group(3)})) {{"))
    # SDL: delete an assignment statement that is not a declaration.
    if re.match(r"^\s*\w+ = [^=].*;\s*$", line) and not re.match(r"^\s*(const\s+)?int\s", line):
        out.append(("SDL", "delete statement", None))  # type: ignore[arg-type]
    return out


def generate(problem: str) -> None:
    BASE = ROOT / "eval/mutation" / problem
    mutants_dir = BASE / "mutants"
    mutants_dir.mkdir(parents=True, exist_ok=True)
    for old in mutants_dir.glob("*.cpp"):
        old.unlink()
    manifest = []
    seen: dict[str, str] = {}
    for style, name in STYLES.items():
        original = (BASE / "originals" / f"{name}.cpp").read_text()
        lines = original.split("\n")
        n = 0
        for idx, line in enumerate(lines):
            if not mutable(line):
                continue
            for op, desc, new in edits(line):
                new_lines = lines[:idx] + ([] if new is None else [new]) + lines[idx + 1 :]
                source = "\n".join(new_lines)
                n += 1
                mid = f"{style}_{op}_{n:03d}"
                entry = {
                    "id": mid,
                    "file": f"{mid}.cpp",
                    "style": style,
                    "style_name": name,
                    "operator": op,
                    "edit": desc,
                    "line_no": idx + 1,
                    "original_line": line.strip(),
                    "mutated_line": None if new is None else new.strip(),
                }
                if source == original:
                    entry["excluded"] = "identical to original"
                elif source in seen:
                    entry["excluded"] = f"duplicate of {seen[source]}"
                else:
                    seen[source] = mid
                    (mutants_dir / entry["file"]).write_text(source)
                manifest.append(entry)
    (BASE / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    kept = [e for e in manifest if "excluded" not in e]
    print(f"{problem}: {len(manifest)} generated, {len(kept)} kept, {len(manifest) - len(kept)} excluded")


def main() -> None:
    for problem in PROBLEMS:
        generate(problem)


if __name__ == "__main__":
    main()
