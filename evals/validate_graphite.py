#!/usr/bin/env python3
"""Measure slop_scan metrics on Graphite's matched human/model articles.

    python3 evals/validate_graphite.py /path/to/ai_tells_articles.jsonl.gz [--topics 2000] [--show 15]

For each corpus it reports, per metric: the mean rate per 1k words and the share of articles
with at least one hit. It also prints sample human-text hits to the terminal so you can inspect
false positives. Only aggregate numbers are written (evals/graphite_validation.json). No article
text is stored: the articles are third-party copyrighted pages and are not redistributed.
"""
import argparse
import gzip
import json
import pathlib
import random
import re
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import slop_scan as ss  # noqa: E402

CORPORA = ["human", "claude-opus-5", "gpt-6-astra", "gemini-3-1-pro-preview", "gpt41", "claude-opus-4-20250514"]
METRICS = ["echo_fragments", "count_fragments", "staged_reveals", "contrast_frames",
           "concessive_frames", "tradeoff_dodges", "importance_flags", "mannered_frames", "inanimate_agents",
           "denominal_verbs", "meta_reference", "copula_avoidance", "that_subjects", "participial_clauses",
           "triads", "intensifiers", "stock_phrases"]


def hit_count(name, r):
    for k in ("count", "hits"):
        if isinstance(r.get(k), int):
            return r[k]
    if name == "participial_clauses":
        return r["count"]
    if name == "triads":
        return r["count"]
    if name == "intensifiers":
        return r["count"]
    return len(r.get("hits") or [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--topics", type=int, default=2000)
    ap.add_argument("--show", type=int, default=15)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    rows = []
    with gzip.open(a.path, "rt", encoding="utf-8") as f:
        for line in f:
            rows.append(line)
    random.Random(a.seed).shuffle(rows)
    rows = rows[: a.topics]

    agg = {c: {m: {"hits": 0, "docs_with": 0} for m in METRICS} for c in CORPORA}
    words = defaultdict(int)
    ndocs = defaultdict(int)
    samples = defaultdict(list)
    for line in rows:
        o = json.loads(line)
        for c in CORPORA:
            text = o.get(c) or ""
            if len(text.split()) < 150:
                continue
            d = ss.Doc(text)
            ndocs[c] += 1
            words[c] += len(d.words)
            for m in METRICS:
                r = ss.run_metric(m, d)
                h = hit_count(m, r)
                agg[c][m]["hits"] += h
                agg[c][m]["docs_with"] += 1 if h else 0
                if c == "human" and h and len(samples[m]) < a.show:
                    hs = r.get("hits") or []
                    if hs:
                        samples[m].append(str(hs[0])[:110])
    out = {"topics": len(rows), "corpora": {}}
    for c in CORPORA:
        out["corpora"][c] = {"docs": ndocs[c], "words": words[c], "metrics": {
            m: {"per_1k": round(1000 * v["hits"] / max(words[c], 1), 3),
                "doc_share": round(v["docs_with"] / max(ndocs[c], 1), 3)} for m, v in agg[c].items()}}
    (ROOT / "evals" / "graphite_validation.json").write_text(json.dumps(out, indent=1))

    hdr = f"{'metric':20}" + "".join(f"{c.split('-')[0][:6] + ('5' if c == 'claude-opus-5' else '4' if c.startswith('claude-opus-4') else ''):>15}" for c in CORPORA)
    print(f"{len(rows)} topics. per 1k words (share of docs with ≥1 hit)\n" + hdr)
    for m in METRICS:
        line = f"{m:20}"
        for c in CORPORA:
            v = out["corpora"][c]["metrics"][m]
            line += f"{v['per_1k']:>8.2f} ({v['doc_share']:.2f})"
        hum = out["corpora"]["human"]["metrics"][m]["per_1k"]
        cur = [out["corpora"][c]["metrics"][m]["per_1k"] for c in CORPORA[1:4]]
        ratio = (sum(cur) / 3) / hum if hum else float("inf")
        print(line + f"   current/human={ratio:.1f}x")
    print("\nSample HUMAN hits (false-positive check):")
    for m in METRICS:
        if samples[m]:
            print(f"\n[{m}]")
            for s in samples[m][: a.show]:
                print("   ", s)


if __name__ == "__main__":
    main()
