#!/usr/bin/env python3
"""Build references/data/graphite_tells_lexicon.json from Graphite's tells_vs_human CSV.

    python3 scripts/build_tell_lexicon.py [--min-ratio 4] [--min-share 0.03] [--top 250]

For each of the nine models it keeps two lists:
  model  terms the model uses at >= min-ratio x the human rate, in >= min-share of its articles
  human  terms humans use at >= min-ratio x that model's rate, in >= min-share of human articles
Frames are kept only when lift >= 1.5 (the frame says more than its words alone).
Each list is ranked by log2(ratio) x article share.

It also stores, per list, the summed per-1k-position rates on both sides. These are the
expected hits per 1k tokens when every term is counted independently, for human text and for
that model's text. slop_scan's model_fingerprint metric uses them as calibrated reference
points instead of guessed thresholds.

Source: Graphite, "AI Tells" (2026), https://graphite.io/five-percent/research/ai-tells. CC BY 4.0.
"""
import argparse
import csv
import gzip
import io
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "references" / "data" / "graphite_ai_tells_tells_vs_human.csv.gz"
OUT = ROOT / "references" / "data" / "graphite_tells_lexicon.json"
N_ARTICLES = 9984
NAMES = {"gpt41": "GPT-4.1", "gpt5": "GPT-5", "gpt-5-6-sol": "GPT-5.6 Sol", "gpt-6-astra": "GPT-6 Astra",
         "claude-opus-4-20250514": "Claude Opus 4", "claude-opus-4-6": "Claude Opus 4.6",
         "claude-opus-5": "Claude Opus 5", "gemini-2-5-pro": "Gemini 2.5 Pro",
         "gemini-3-1-pro-preview": "Gemini 3.1 Pro"}
CURRENT = ["claude-opus-5", "gpt-6-astra", "gemini-3-1-pro-preview"]


def fnum(x):
    return math.inf if x == "inf" else float(x or 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-ratio", type=float, default=4.0)
    ap.add_argument("--min-share", type=float, default=0.03)
    ap.add_argument("--top", type=int, default=250)
    a = ap.parse_args()
    rows = list(csv.DictReader(io.TextIOWrapper(gzip.open(SRC), encoding="utf-8")))
    common = set()
    for r in rows:
        if r["kind"] == "frame":
            common.update(t for t in r["term"].split() if t != "_")
    out = {"source": "Graphite, \"AI Tells\" (2026), https://graphite.io/five-percent/research/ai-tells (CC BY 4.0)",
           "params": vars(a), "names": NAMES, "current": CURRENT,
           "frame_common_words": sorted(common), "models": {}}
    for m in NAMES:
        entry = {}
        for side in ("model", "human"):
            sel = []
            for r in rows:
                if r["model"] != m or (r["used_more_by"] == "human") != (side == "human"):
                    continue
                arts = int(r["human_articles"] if side == "human" else r["model_articles"])
                ratio = fnum(r["ratio"])
                if ratio < a.min_ratio or arts / N_ARTICLES < a.min_share:
                    continue
                if r["kind"] == "frame" and fnum(r["lift"]) < 1.5:
                    continue
                score = math.log2(min(ratio, 1024)) * arts / N_ARTICLES
                sel.append({"term": r["term"], "kind": r["kind"],
                            "ratio": None if ratio == math.inf else round(ratio, 2),
                            "model_rate": float(r["model_rate_per1k_positions"]),
                            "human_rate": float(r["human_rate_per1k_positions"]),
                            "share": round(arts / N_ARTICLES, 3), "score": round(score, 4)})
            sel.sort(key=lambda x: -x["score"])
            sel = sel[:a.top]
            entry[side] = {"terms": sel,
                           "expected_per_1k": {"model": round(sum(t["model_rate"] for t in sel), 3),
                                               "human": round(sum(t["human_rate"] for t in sel), 3)}}
        out["models"][m] = entry
    OUT.write_text(json.dumps(out, separators=(",", ":")))
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
    for m in CURRENT:
        e = out["models"][m]
        print(f"{NAMES[m]:16} model-list: {len(e['model']['terms'])} terms, expected/1k model {e['model']['expected_per_1k']['model']} "
              f"vs human {e['model']['expected_per_1k']['human']} | human-list expected/1k human {e['human']['expected_per_1k']['human']} "
              f"vs model {e['human']['expected_per_1k']['model']}")
        print("   top:", ", ".join(f"{t['term']}({t['ratio'] or 'inf'}x)" for t in e["model"]["terms"][:14]))
        print("   human-only:", ", ".join(f"{t['term']}({t['ratio'] or 'inf'}x)" for t in e["human"]["terms"][:14]))


if __name__ == "__main__":
    main()
