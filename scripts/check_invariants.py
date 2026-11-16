#!/usr/bin/env python3
"""check_invariants: did a revision keep the facts?

    python3 check_invariants.py before.md after.md          # report; exit 1 if facts were dropped
    python3 check_invariants.py before.md after.md --json

Compares two drafts and lists what the revision dropped or added among the things a style pass
must not change:

  numbers      digits and number words with their units ("600-second", "70-75%", "2 million")
  code         inline `code` spans and fenced code blocks (exact text)
  links        URLs and markdown link targets
  names        capitalized names, ALLCAPS terms, identifiers (snake_case, camelCase, dotted.names)
  quotes       quoted strings
  negations    sentences whose meaning depends on not / never / no / without (content-word match)
  hedges       sentences carrying may / might / could / probably / usually / often ... (content-word match)

Dropped numbers, code or links are errors (exit 1). Dropped names, quotes, negations and hedges are
warnings: a style pass may legitimately remove a generic hedge, but every removal should be a choice.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

NUM_WORDS = r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|fifty|hundred|thousand|million|billion|dozen|half)"
UNIT = r"(?:\s?(?:%|percent|ms|s|sec|seconds?|minutes?|mins?|hours?|days?|weeks?|months?|years?|gb|mb|kb|tb|rows|requests|users|messages|x|times))?"
NEG = re.compile(r"\b(not|never|no|none|nothing|nobody|neither|nor|without|cannot)\b|n't\b", re.I)
HEDGE = re.compile(r"\b(may|might|could|probably|possibly|perhaps|usually|often|typically|generally|likely|unlikely|"
                   r"sometimes|some|most|almost|roughly|about|approximately|around|seems?|appears?)\b", re.I)
STOP = set("""a an the and or but of in on at to from by with for as is are was were be been it its this that these
those you your we our they their he she his her i my me not no never if then than so do does did can will would should
could may might must have has had just also very more most some any all each""".split())


def _sentences(text: str) -> list[str]:
    t = re.sub(r"```.*?```", " ", text, flags=re.S)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n", t) if s.strip()]


def _cw(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z][a-z'-]{2,}", s.lower()) if w not in STOP}


def _clean(text: str) -> str:
    t = re.sub(r"(?m)^#{1,6}\s+", "", text)                          # headings first ("## 2. Fix ...")
    t = re.sub(r"(?m)^\s*(?:[-*+]|\d+[.)])\s+", "", t)              # list markers, incl. "1."
    t = re.sub(r"(\*\*|\*)(?=\S)(.+?)(?<=\S)\1", r"\2", t)         # * / ** emphasis (not _, to keep snake_case)
    t = re.sub(r"(?<![\w])__(?=\S)(.+?)(?<=\S)__(?![\w])", r"\1", t)
    return t


def _fence_lines(text: str) -> list[str]:
    out = []
    for f in re.findall(r"```[^\n]*\n(.*?)```", text, flags=re.S):
        out += [ln.strip() for ln in f.splitlines() if ln.strip()]
    return out


def extract(text: str) -> dict:
    fences = _fence_lines(text)
    text = _clean(text)
    body = re.sub(r"```.*?```", " ", text, flags=re.S)
    code = re.findall(r"`([^`\n]+)`", body)
    plain = re.sub(r"`[^`\n]+`", " ", body)
    links = re.findall(r"https?://[^\s)>\]]+", text) + re.findall(r"\]\(([^)]+)\)", text)
    nums = []
    for m in re.finditer(rf"(?<![\w.:/])(\d[\d,.]*(?:\s?[-–]\s?\d[\d,.]*)?{UNIT}|{NUM_WORDS}{UNIT})(?![\w])", plain, re.I):
        v = m.group(0).lower().replace("–", "-").replace(" ", "").rstrip(".,")
        if re.fullmatch(r"(one|half)", v):          # too common as pronoun/determiner
            continue
        nums.append(v)
    names = set()
    for s in _sentences(plain):
        toks = re.findall(r"[A-Za-z][\w.+#-]*", s)
        for i, t in enumerate(toks):
            t = t.rstrip(".")
            if t.lower() in ("e.g", "i.e", "etc", "vs"):
                continue
            if re.fullmatch(r"[A-Z]{2,}[\w-]*", t) or re.search(r"[a-z][A-Z]|_|\.\w", t) or (i > 0 and t[:1].isupper() and t.lower() not in STOP):
                names.add(t)
    quotes = re.findall(r"[\"“]([^\"”\n]{3,80})[\"”]", plain)
    sents = _sentences(text)
    negs = [s for s in sents if NEG.search(s)]
    hedges = [s for s in sents if HEDGE.search(s)]
    return {"numbers": nums, "code": code + fences, "links": links, "names": sorted(names),
            "quotes": quotes, "negations": negs, "hedges": hedges}


def _sentence_kept(s: str, pool: list[str], thresh: float = 0.5) -> bool:
    """A negated/hedged sentence counts as kept if some sentence in pool with the same marker shares
    at least `thresh` of its content words."""
    c = _cw(s)
    if not c:
        return True
    return any(len(c & _cw(p)) / len(c) >= thresh for p in pool)


def compare(before: str, after: str) -> dict:
    b, a = extract(before), extract(after)
    out = {}
    for k in ("numbers", "code", "links", "names", "quotes"):
        lb, la = b[k], a[k]
        a_norm = {re.sub(r"\s+", " ", x).lower() for x in la}
        b_norm = {re.sub(r"\s+", " ", x).lower() for x in lb}
        dropped = sorted({x for x in lb if re.sub(r"\s+", " ", x).lower() not in a_norm})
        added = sorted({x for x in la if re.sub(r"\s+", " ", x).lower() not in b_norm})
        if k in ("names", "code"):   # kept if the text still appears anywhere (e.g. moved out of backticks)
            a_text = re.sub(r"\s+", " ", after.lower())
            dropped = [x for x in dropped if re.sub(r"\s+", " ", x.lower()) not in a_text]
        if k == "numbers":           # kept if its digits survive ("600 seconds" -> "600-second")
            a_text = after.lower().replace(" ", "")
            a_digits = set(re.findall(r"\d[\d,.]*\d|\d", after))
            dropped = [x for x in dropped if x not in a_text and
                       not (re.findall(r"\d[\d,.]*\d|\d", x) and all(dg in a_digits for dg in re.findall(r"\d[\d,.]*\d|\d", x)))]
        out[k] = {"dropped": dropped, "added": added}
    for k in ("negations", "hedges"):
        out[k] = {"dropped": [s for s in b[k] if not _sentence_kept(s, a[k])],
                  "added": [s for s in a[k] if not _sentence_kept(s, b[k])]}
    out["errors"] = sum(len(out[k]["dropped"]) for k in ("numbers", "code", "links"))
    out["warnings"] = sum(len(out[k]["dropped"]) for k in ("names", "quotes", "negations", "hedges"))
    return out


def render(res: dict, brief: bool = False) -> str:
    lines = [f"INVARIANTS errors={res['errors']} (dropped numbers/code/links), warnings={res['warnings']} "
             f"(dropped names/quotes/negations/hedges)"]
    for k in ("numbers", "code", "links", "names", "quotes", "negations", "hedges"):
        d, ad = res[k]["dropped"], res[k]["added"]
        if not d and not (ad and not brief):
            continue
        if d:
            lines.append(f"  DROPPED {k}: " + " | ".join(x[:90] for x in d[:8]))
        if ad and not brief and k in ("numbers", "code", "links", "names"):
            lines.append(f"  added {k}: " + " | ".join(x[:90] for x in ad[:8]))
        elif ad and k in ("numbers", "names"):
            lines.append(f"  ADDED {k} (check it is not invented): " + " | ".join(x[:60] for x in ad[:6]))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    res = compare(open(a.before, encoding="utf-8").read(), open(a.after, encoding="utf-8").read())
    print(json.dumps(res, indent=2) if a.json else render(res))
    return 1 if res["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
