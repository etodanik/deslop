#!/usr/bin/env python3
"""Score the A/B test of the agent aides.

    .venv/bin/python evals/evaluate_ab.py        # uses deep_scan for Biber D1 if available

evals/ab/input/<id>.md   original Claude answer, with <id>.prompt.txt
evals/ab/armA/<id>.md    pass with SKILL.md + plain scanner report
evals/ab/armB/<id>.md    pass with the aides (--agent, --self, --prompt, --before, check_invariants)

Lower is better for every column except d1 (closer to the human web mean, 0, is better) and words.
Writes evals/ab/results.json.
"""
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

AB = ROOT / "evals" / "ab"


def measure(path: pathlib.Path, prompt: str, original: str | None) -> dict:
    text = path.read_text(encoding="utf-8")
    d = ss.Doc(text)
    res = {n: ss.run_metric(n, d, prompt=prompt) for n in ss.METRICS}
    flags = {n: ss.flag(n, res[n], "chat") for n in ss.METRICS}
    own = ss.own_family_tells(d, "claude", top=500)
    out = {"words": len(d.words), "length_ratio": res["request_fit"]["length_ratio"],
           "flags_all": sum(1 for f in flags.values() if f),
           "flags_durable": sum(1 for n in ss.DURABLE if flags.get(n)),
           "claude_tells": len(own), "opus5_likeness": res["model_fingerprint"]["current_models"]["claude-opus-5"]["tell_likeness"],
           "echo_fragments": res["echo_fragments"]["count"], "participial_per_100s": res["participial_clauses"]["per_100_sentences"],
           "triads_share": res["triads"]["share_of_sentences"], "word_length": res["word_length"]["mean_letters"]}
    if original is not None:
        inv = ci.compare(original, text)
        out["facts_dropped"] = inv["errors"]
        out["soft_dropped"] = inv["warnings"]
    if ds is not None:
        try:
            out["d1"] = ds.biber_d1(d)["d1"]
        except Exception:
            pass
    return out


def main():
    ids = sorted(p.stem for p in (AB / "input").glob("*.md"))
    table = {}
    for i in ids:
        prompt = (AB / "input" / f"{i}.prompt.txt").read_text()
        orig = (AB / "input" / f"{i}.md").read_text()
        table[i] = {"input": measure(AB / "input" / f"{i}.md", prompt, None)}
        for arm in ("armA", "armB"):
            p = AB / arm / f"{i}.md"
            if p.exists():
                table[i][arm] = measure(p, prompt, orig)
    (AB / "results.json").write_text(json.dumps(table, indent=1))
    cols = ["words", "length_ratio", "flags_all", "flags_durable", "claude_tells", "opus5_likeness", "echo_fragments",
            "participial_per_100s", "triads_share", "word_length", "facts_dropped", "soft_dropped", "d1"]
    print(f"{'metric':22}{'input':>10}{'armA':>10}{'armB':>10}   (means over {len(ids)} answers)")
    for c in cols:
        row = f"{c:22}"
        for arm in ("input", "armA", "armB"):
            xs = [table[i][arm][c] for i in ids if arm in table[i] and table[i][arm].get(c) is not None]
            row += f"{statistics.mean(xs):>10.2f}" if xs else f"{'-':>10}"
        print(row)
    print("\nper answer: claude_tells / facts_dropped / echo  (A vs B)")
    for i in ids:
        if "armA" in table[i] and "armB" in table[i]:
            A, B = table[i]["armA"], table[i]["armB"]
            print(f"  {i:16} A {A['claude_tells']:>3} / {A['facts_dropped']:>2} / {A['echo_fragments']}   "
                  f"B {B['claude_tells']:>3} / {B['facts_dropped']:>2} / {B['echo_fragments']}")


if __name__ == "__main__":
    main()
