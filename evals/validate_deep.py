#!/usr/bin/env python3
"""Validate deep_scan tools (surprisal, redundancy, Biber D1) on Graphite and ELEPHANT.

    .venv/bin/python evals/validate_deep.py [--n 40]

Aggregates (means and Cohen's d vs human) go to evals/deep_validation.json.
"""
import argparse, csv, gzip, json, pathlib, random, statistics, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import slop_scan as ss  # noqa: E402
import deep_scan as ds  # noqa: E402

KEYS = [("surprisal", "mean_bits"), ("surprisal", "sentence_mean_sd"), ("surprisal", "share_under_1_bit"),
        ("redundancy", "restatement_share"), ("redundancy", "mean_max_prev_sim"),
        ("redundancy", "mean_within_paragraph_sim"), ("redundancy", "tieback_last_vs_first"), ("biber_d1", "d1")]


def measure(text):
    d = ss.Doc(text[:7000])
    r = {k: ds.TOOLS[k](d) for k in ("surprisal", "redundancy", "biber_d1")}
    return {f"{t}.{k}": r[t].get(k) for t, k in KEYS}


def cohen(h, m):
    sp = ((statistics.pstdev(h) ** 2 + statistics.pstdev(m) ** 2) / 2) ** 0.5 or 1
    return (statistics.mean(m) - statistics.mean(h)) / sp


def report(name, acc):
    cols = list(acc)
    print(f"\n== {name}  (means; Cohen's d vs human in [])")
    out = {}
    for t, k in KEYS:
        key = f"{t}.{k}"
        h = [x[key] for x in acc["human"] if x[key] is not None]
        line = f"  {key:36} human {statistics.mean(h) if h else float('nan'):7.3f}"
        out[key] = {"human": statistics.mean(h) if h else None}
        for c in cols[1:]:
            m = [x[key] for x in acc[c] if x[key] is not None]
            if len(m) > 3 and len(h) > 3:
                line += f" | {c[:12]} {statistics.mean(m):7.3f} [{cohen(h, m):+.2f}]"
                out[key][c] = {"mean": statistics.mean(m), "d": cohen(h, m)}
        print(line)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    a = ap.parse_args()
    res = {}
    rows = gzip.open(ROOT / "sources/raw/graphite_ai_tells_articles.jsonl.gz", "rt").readlines()
    random.Random(4).shuffle(rows)
    G = ["human", "claude-opus-5", "gpt-6-astra", "gemini-3-1-pro-preview"]
    acc = {c: [] for c in G}
    for line in rows[: a.n]:
        o = json.loads(line)
        for c in G:
            if len((o.get(c) or "").split()) >= 200:
                acc[c].append(measure(o[c]))
    res["graphite"] = report("Graphite web articles", acc)
    csv.field_size_limit(10 ** 9)
    er = list(csv.DictReader(open(ROOT / "sources/raw/elephant/elephant_full_results/OEQ_full_results.csv", encoding="utf-8")))
    random.Random(4).shuffle(er)
    E = ["Human", "Claude", "GPT-5", "Gemini", "Llama-70B"]
    acc = {c: [] for c in E}
    acc["human"] = acc.pop("Human")
    acc = {"human": acc["human"], **{c: acc[c] for c in E[1:]}}
    for r in er[: a.n]:
        for c in E:
            t = r.get(c) or ""
            if len(t.split()) >= 60:
                acc["human" if c == "Human" else c].append(measure(t))
    res["elephant"] = report("ELEPHANT advice replies", acc)
    (ROOT / "evals" / "deep_validation.json").write_text(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
