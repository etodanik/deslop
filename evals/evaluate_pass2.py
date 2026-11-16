#!/usr/bin/env python3
"""Score the tells-only second pass: evals/pass2exp/{input,p1,p2}/<id>.md.

    .venv/bin/python evals/evaluate_pass2.py      # (Biber D1 included when deep_scan imports)

For input, P1 (one tested pass) and P2 (P1 + a pass limited to own-family tells):
own-family tells for claude/gpt/gemini, Opus 5 likeness, durable flags, all flags, echo fragments,
participial tails, word length, words, facts dropped vs the input. For P2 it also reports how much of P1
it changed and whether changes stayed inside sentences that --self listed. Writes evals/pass2exp/results.json.
"""
import difflib
import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import slop_scan as ss  # noqa: E402
import check_invariants as ci  # noqa: E402

try:
    import deep_scan as ds  # noqa: E402
except Exception:  # pragma: no cover
    ds = None

X = ROOT / "evals" / "pass2exp"


def measure(text: str, prompt: str, original: str | None) -> dict:
    d = ss.Doc(text)
    res = {n: ss.run_metric(n, d, prompt=prompt) for n in ss.METRICS}
    fl = {n: ss.flag(n, res[n], "chat") for n in ss.METRICS}
    out = {"words": len(d.words), "length_ratio": res["request_fit"]["length_ratio"],
           "all_flags": sum(1 for v in fl.values() if v), "durable_flags": sum(1 for n in ss.DURABLE if fl.get(n)),
           "echo": res["echo_fragments"]["count"], "participial": res["participial_clauses"]["per_100_sentences"],
           "word_length": res["word_length"]["mean_letters"],
           "opus5_likeness": res["model_fingerprint"]["current_models"]["claude-opus-5"]["tell_likeness"]}
    for fam in ("claude", "gpt", "gemini"):
        out[f"{fam}_tells"] = len(ss.own_family_tells(d, fam, top=500))
    if original is not None:
        inv = ci.compare(original, text)
        out["facts_dropped"], out["soft_dropped"] = inv["errors"], inv["warnings"]
    if ds is not None:
        try:
            out["d1"] = ds.biber_d1(d)["d1"]
        except Exception:
            pass
    return out


def scope(p1: str, p2: str) -> dict:
    """How much P2 changed, and whether changed P1 sentences were ones --self listed."""
    d1, d2 = ss.Doc(p1), ss.Doc(p2)
    listed = {i for t in ss.own_family_tells(d1, "claude", top=500) for i in t["sentences"]}
    sm = difflib.SequenceMatcher(a=d1.sentences, b=d2.sentences, autojunk=False)
    changed = set()
    for tag, a1, a2, _b1, _b2 in sm.get_opcodes():
        if tag != "equal":
            changed |= set(range(a1, a2))
    return {"sentences": len(d1.sentences), "changed": len(changed), "changed_listed": len(changed & listed),
            "changed_unlisted": len(changed - listed), "listed": len(listed)}


def main():
    ids = sorted(p.stem for p in (X / "input").glob("*.md"))
    table = {}
    for i in ids:
        prompt = (X / "input" / f"{i}.prompt.txt").read_text()
        orig = (X / "input" / f"{i}.md").read_text()
        table[i] = {"input": measure(orig, prompt, None)}
        for arm in ("p1", "p2"):
            p = X / arm / f"{i}.md"
            if p.exists():
                table[i][arm] = measure(p.read_text(), prompt, orig)
        if (X / "p1" / f"{i}.md").exists() and (X / "p2" / f"{i}.md").exists():
            table[i]["scope"] = scope((X / "p1" / f"{i}.md").read_text(), (X / "p2" / f"{i}.md").read_text())
            inv12 = ci.compare((X / "p1" / f"{i}.md").read_text(), (X / "p2" / f"{i}.md").read_text())
            table[i]["p2_vs_p1_facts_dropped"] = inv12["errors"]
    (X / "results.json").write_text(json.dumps(table, indent=1))
    cols = ["words", "claude_tells", "gpt_tells", "gemini_tells", "opus5_likeness", "durable_flags", "all_flags",
            "echo", "participial", "word_length", "facts_dropped", "soft_dropped", "d1"]
    print(f"{'metric':16}{'input':>9}{'P1':>9}{'P2':>9}   (means over {len(ids)})")
    for c in cols:
        row = f"{c:16}"
        for arm in ("input", "p1", "p2"):
            xs = [table[i][arm][c] for i in ids if arm in table[i] and table[i][arm].get(c) is not None]
            row += f"{statistics.mean(xs):>9.2f}" if xs else f"{'-':>9}"
        print(row)
    print("\nper answer: claude tells input/P1/P2 | P2 scope: changed sentences (listed/unlisted) of total")
    for i in ids:
        t = table[i]
        if "p2" in t:
            s = t["scope"]
            print(f"  {i:16} {t['input']['claude_tells']:>3} {t['p1']['claude_tells']:>3} {t['p2']['claude_tells']:>3} | "
                  f"{s['changed']} ({s['changed_listed']}/{s['changed_unlisted']}) of {s['sentences']}, listed {s['listed']}; "
                  f"P2 dropped facts vs P1: {t['p2_vs_p1_facts_dropped']}")


if __name__ == "__main__":
    main()
