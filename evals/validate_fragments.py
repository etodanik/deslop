#!/usr/bin/env python3
"""Validate the spaCy count_fragments check (verbless sentences) on Graphite and ELEPHANT.

    .venv/bin/python evals/validate_fragments.py [--n 120]

Reports fragments per 100 sentences and the share of texts with >= 1, per source, plus sample human
hits for false-positive inspection. Aggregates go to evals/fragments_validation.json.
"""
import argparse, csv, gzip, json, pathlib, random, statistics, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import slop_scan as ss  # noqa: E402

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=120); a = ap.parse_args()
    impl = ss.spacy_overrides(ss.load_spacy()); frag = impl["count_fragments"]
    res, samples = {}, {}
    def run(corpus, label, texts):
        rates, anyhit, hits = [], 0, []
        for t in texts:
            r = frag(ss.Doc(t[:6000]))
            rates.append(r["per_100_sentences"]); anyhit += r["count"] > 0; hits += r["hits"][:2]
        res[f"{corpus}:{label}"] = {"per_100_sentences": round(statistics.mean(rates), 2), "share_with_any": round(anyhit / len(texts), 3), "n": len(texts)}
        samples[f"{corpus}:{label}"] = hits[:14]
    rows = gzip.open(ROOT / "sources/raw/graphite_ai_tells_articles.jsonl.gz", "rt").readlines()
    random.Random(8).shuffle(rows); rows = [json.loads(l) for l in rows[: a.n]]
    for c in ("human", "claude-opus-5", "gpt-6-astra", "gemini-3-1-pro-preview"):
        run("graphite", c, [o[c] for o in rows if len((o.get(c) or "").split()) >= 200])
    csv.field_size_limit(10 ** 9)
    er = list(csv.DictReader(open(ROOT / "sources/raw/elephant/elephant_full_results/OEQ_full_results.csv", encoding="utf-8")))
    random.Random(8).shuffle(er); er = er[: a.n]
    for c in ("Human", "Claude", "GPT-5", "Gemini", "Llama-70B"):
        run("elephant", c, [r[c] for r in er if len((r.get(c) or "").split()) >= 60])
    (ROOT / "evals" / "fragments_validation.json").write_text(json.dumps(res, indent=1))
    for k, v in res.items():
        print(f"  {k:36} {v['per_100_sentences']:>6} per 100 sentences   {v['share_with_any']:.2f} of texts have one   (n={v['n']})")
    for k in ("graphite:human", "elephant:Human", "graphite:claude-opus-5", "elephant:Claude"):
        print(f"\n[{k}] sample hits:"); [print("   ", h) for h in samples[k][:10]]

if __name__ == "__main__":
    main()
