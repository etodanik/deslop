#!/usr/bin/env python3
"""Check the deslop self-pass on the skill's own docs for regressions.

    python3 evals/selfpass_check.py

Compares evals/selfpass/before/<path> with evals/selfpass/after/<path>. A file PASSES when:
  structure  same heading levels and numbering, same pattern numbers (**3.1 …**), same fenced code blocks,
             same table shapes, frontmatter kept
  data       every quoted example and `metric:` reference kept, no dropped numbers/code/links
  prose      on prose only (quotes, code and tables removed): own-family (claude) tells and echo fragments
             not increased, durable flags not increased
Writes evals/selfpass/report.json.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import slop_scan as ss  # noqa: E402
import check_invariants as ci  # noqa: E402

SP = ROOT / "evals" / "selfpass"


def headings(t):
    return [(len(m.group(1)), re.match(r"[\d.]+[a-z]?", m.group(2)).group(0) if re.match(r"[\d.]+[a-z]?", m.group(2)) else "")
            for m in re.finditer(r"(?m)^(#{1,6})\s+(.*)$", t)]


def pattern_nums(t):
    return sorted(re.findall(r"\*\*(\d+\.\d+[a-z]?)\b", t))


def fences(t):
    return [re.sub(r"\s+", " ", f).strip() for f in re.findall(r"```.*?```", t, flags=re.S)]


def tables(t):
    shapes, cur = [], []
    for ln in t.splitlines():
        if ln.strip().startswith("|"):
            cur.append(ln.count("|"))
        elif cur:
            shapes.append((len(cur), cur[0]))
            cur = []
    if cur:
        shapes.append((len(cur), cur[0]))
    return shapes


def quotes(t):
    return set(re.findall(r'"([^"\n]{2,120})"', t))


def metric_refs(t):
    return sorted(re.findall(r"`metric: ([a-z_]+)", t))


def prose_only(t):
    t = re.sub(r"(?s)^---.*?---", " ", t)
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = "\n".join(ln for ln in t.splitlines() if not ln.strip().startswith("|"))
    t = re.sub(r'"[^"\n]{1,160}"|“[^”\n]{1,160}”', ' "x" ', t)
    t = re.sub(r"\*[^*\n]{1,80}\*", " ", t)          # italic example words
    return t


def prose_metrics(t):
    d = ss.Doc(prose_only(t))
    r = {n: ss.run_metric(n, d) for n in ss.METRICS}
    fl = {n: ss.flag(n, r[n], "docs") for n in ss.METRICS}
    return {"words": len(d.words), "claude_tells": len(ss.own_family_tells(d, "claude", top=500)),
            "opus5_likeness": r["model_fingerprint"]["current_models"]["claude-opus-5"]["tell_likeness"],
            "echo": r["echo_fragments"]["count"], "durable_flags": sum(1 for n in ss.DURABLE if fl.get(n)),
            "all_flags": sum(1 for v in fl.values() if v), "participial": r["participial_clauses"]["per_100_sentences"],
            "word_length": r["word_length"]["mean_letters"], "importance": r["importance_flags"]["count"],
            "tradeoff": r["tradeoff_dodges"]["count"]}


def main():
    report, ok_all = {}, True
    for b in sorted((SP / "before").rglob("*.md")):
        rel = b.relative_to(SP / "before")
        a = SP / "after" / rel
        if not a.exists():
            report[str(rel)] = {"status": "MISSING"}
            ok_all = False
            continue
        B, A = b.read_text(), a.read_text()
        problems = []
        if headings(B) != headings(A):
            problems.append(f"headings changed ({len(headings(B))} -> {len(headings(A))})")
        if pattern_nums(B) != pattern_nums(A):
            problems.append(f"pattern numbers changed: missing {sorted(set(pattern_nums(B)) - set(pattern_nums(A)))}")
        if fences(B) != fences(A):
            problems.append("code blocks changed")
        if tables(B) != tables(A):
            problems.append(f"table shapes changed {tables(B)} -> {tables(A)}")
        if B.startswith("---") and not A.startswith("---"):
            problems.append("frontmatter lost")
        lost_q = sorted(quotes(B) - quotes(A))
        if lost_q and rel.name in ("patterns.md", "register.md"):
            problems.append(f"{len(lost_q)} quoted examples changed: {lost_q[:4]}")
        if metric_refs(B) != metric_refs(A):
            problems.append("metric: references changed")
        from collections import Counter
        numtok = lambda t: Counter(re.findall(r"\d[\d.,]*\d|\d", re.sub(r"```.*?```", " ", t, flags=re.S)))  # noqa: E731
        lost_nums = numtok(B) - numtok(A)
        if lost_nums:
            problems.append(f"numeric tokens changed or removed: {dict(list(lost_nums.items())[:8])}")
        inv = ci.compare(B, A)
        if inv["errors"]:
            problems.append(f"dropped facts: {[(k, inv[k]['dropped'][:4]) for k in ('numbers', 'code', 'links') if inv[k]['dropped']]}")
        pb, pa = prose_metrics(B), prose_metrics(A)
        for k in ("claude_tells", "echo", "durable_flags"):
            if pa[k] > pb[k]:
                problems.append(f"prose regression: {k} {pb[k]} -> {pa[k]}")
        status = "PASS" if not problems else "FAIL"
        ok_all &= status == "PASS"
        report[str(rel)] = {"status": status, "problems": problems, "before": pb, "after": pa,
                            "soft_dropped": {k: inv[k]["dropped"][:6] for k in ("names", "negations", "hedges") if inv[k]["dropped"]},
                            "lost_quotes": lost_q[:10]}
        print(f"\n{status}  {rel}")
        for p in problems:
            print("   -", p)
        print("   prose before:", {k: pb[k] for k in ("words", "claude_tells", "opus5_likeness", "echo", "durable_flags", "all_flags", "participial", "word_length")})
        print("   prose after: ", {k: pa[k] for k in ("words", "claude_tells", "opus5_likeness", "echo", "durable_flags", "all_flags", "participial", "word_length")})
        if report[str(rel)]["soft_dropped"]:
            print("   warnings (dropped names/negations/hedges):", {k: len(v) for k, v in report[str(rel)]["soft_dropped"].items()})
    (SP / "report.json").write_text(json.dumps(report, indent=1))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
