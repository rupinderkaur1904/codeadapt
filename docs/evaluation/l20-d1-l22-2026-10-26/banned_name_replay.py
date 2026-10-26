"""Which stored evaluation programs name a banned call of their problem (D1 replay)."""
import sys
from collections import Counter
from pathlib import Path
from codeadapt.adaptation.technique import banned_names_found
from codeadapt.content import load_catalogue

root = Path(sys.argv[1])
specs = {p.spec.slug: p.spec for p in load_catalogue(root / "content" / "demo")}
total, hits, per = 0, [], Counter()
for base in ("eval/heldout", "eval/calibration", "eval/mutation"):
    for f in sorted((root / base).rglob("*.cpp")):
        slug = next((part for part in f.relative_to(root / base).parts if part in specs), None)
        if slug is None:
            continue
        total += 1
        per[(base, slug in {s for s, p in specs.items() if p.banned_names})] += 1
        found = banned_names_found(f.read_text(), specs[slug].banned_names)
        if found:
            hits.append((str(f.relative_to(root)), found))
print(f"programs scanned: {total}; by set and whether the problem bans names: {dict(per)}")
print(f"programs with a banned name found: {len(hits)}")
for h in hits:
    print("  ", *h)
