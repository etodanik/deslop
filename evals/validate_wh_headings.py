#!/usr/bin/env python3
"""Validate slop_scan's wh_headings metric on Graphite and ELEPHANT.  python3 evals/validate_wh_headings.py [--n 1500]"""
import argparse, csv, gzip, json, pathlib, random, statistics, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import slop_scan as ss  # noqa: E402

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=1500); a = ap.parse_args()
    res, ex = {}, {}
    def run(key, texts):
        rs = [ss.run_metric("wh_headings", ss.Doc(t)) for t in texts]
        res[key] = {"share_with_any": round(sum(r["count"] > 0 for r in rs) / len(rs), 3),
                    "per_1k": round(statistics.mean(r["per_1k"] for r in rs), 3), "n": len(rs)}
        ex[key] = [h for r in rs for h in r["hits"][:1]][:6]
    rows = gzip.open(ROOT / "sources/raw/graphite_ai_tells_articles.jsonl.gz", "rt").readlines()
    random.Random(12).shuffle(rows); rows = [json.loads(l) for l in rows[: a.n]]
    for c in ("human", "claude-opus-4-20250514", "claude-opus-4-6", "claude-opus-5", "gpt41", "gpt5", "gpt-5-6-sol", "gpt-6-astra", "gemini-2-5-pro", "gemini-3-1-pro-preview"):
        run(f"graphite:{c}", [o[c] for o in rows if o.get(c)])
    csv.field_size_limit(10 ** 9)
    er = list(csv.DictReader(open(ROOT / "sources/raw/elephant/elephant_full_results/OEQ_full_results.csv", encoding="utf-8")))
    random.Random(12).shuffle(er); er = er[: a.n]
    for c in ("Human", "Claude", "GPT-4o", "GPT-5", "Gemini", "DeepSeek", "Qwen", "Llama-70B", "Mistral-24B"):
        run(f"elephant:{c}", [r[c] for r in er if r.get(c)])
    (ROOT / "evals" / "wh_headings_validation.json").write_text(json.dumps(res, indent=1))
    for k, v in res.items():
        print(f"  {k:34} texts with one {v['share_with_any']:.3f}   per 1k {v['per_1k']:.3f}   n={v['n']}")
    for k in ("graphite:human", "elephant:Human"):
        print(f"[{k}] {ex[k]}")

if __name__ == "__main__":
    main()
