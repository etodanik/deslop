#!/usr/bin/env python3
"""Validate request-fit and durable checks on ELEPHANT OEQ (Cheng et al., ICLR 2026; CC0).

    python3 evals/validate_elephant.py [--n 600]

3,027 open-ended advice prompts, each answered by a crowdsourced human and 12 models. Reports,
per response source, the means of request_fit, the durable style checks and ELEPHANT's own
sycophancy labels (validation, indirectness, framing). Aggregates go to evals/elephant_validation.json.
"""
import argparse
import csv
import json
import pathlib
import random
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import slop_scan as ss  # noqa: E402

SRC = ROOT / "sources" / "raw" / "elephant" / "elephant_full_results" / "OEQ_full_results.csv"
COLS = ["Human", "Claude", "GPT-4o", "GPT-5", "Gemini", "DeepSeek", "Qwen", "Llama-70B", "Llama-8B", "Mistral-24B"]


def score(prompt, text):
    d = ss.Doc(text)
    if len(d.words) < 30:
        return None
    rf = ss.run_metric("request_fit", d, prompt=prompt)
    if rf.get("restates_question") is None:
        return None
    lens = [len(ss.words_of(s)) for s in d.sentences]
    out = {"words": len(d.words), "length_ratio": rf["length_ratio"], "restates_question": rf["restates_question"],
           "closing_recap": rf["closing_recap"], "word_length": ss.run_metric("word_length", d)["mean_letters"],
           "mtld": ss.run_metric("lexical_diversity", d)["mtld"], "longest_sentence": max(lens) if lens else 0,
           "participial_per_100s": ss.run_metric("participial_clauses", d)["per_100_sentences"],
           "bold_per_1k": ss.run_metric("formatting", d)["bold_per_1k"]}
    for m in ("importance_flags", "tradeoff_dodges", "contrast_frames", "echo_fragments"):
        out[m + "_per_1k"] = 1000 * ss.run_metric(m, d)["count"] / len(d.words)
    out["triads_share"] = ss.run_metric("triads", d)["share_of_sentences"]
    fp = ss.run_metric("model_fingerprint", d)
    out["fingerprint_max"] = fp.get("max_tell_likeness")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=600)
    a = ap.parse_args()
    csv.field_size_limit(10 ** 9)
    rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
    random.Random(13).shuffle(rows)
    rows = rows[: a.n]
    acc = {c: [] for c in COLS}
    labels = {c: {"validation": [], "indirectness": [], "framing": []} for c in COLS}
    for r in rows:
        for c in COLS:
            s = score(r["prompt"], r.get(c) or "")
            if s:
                acc[c].append(s)
            for lab in labels[c]:
                v = r.get(f"{lab}_{c}")
                try:
                    labels[c][lab].append(float(v))
                except (TypeError, ValueError):
                    pass
    out = {}
    for c in COLS:
        keys = acc[c][0].keys() if acc[c] else []
        out[c] = {k: round(statistics.mean([x[k] for x in acc[c] if x[k] is not None]), 3) for k in keys}
        out[c].update({f"elephant_{k}": round(statistics.mean(v), 3) for k, v in labels[c].items() if v})
        out[c]["n"] = len(acc[c])
    (ROOT / "evals" / "elephant_validation.json").write_text(json.dumps(out, indent=1))
    keys = list(out["Human"].keys())
    print(f"{a.n} OEQ prompts. Means per response source.\n")
    print(f"{'metric':24}" + "".join(f"{c[:10]:>11}" for c in COLS))
    for k in keys:
        print(f"{k:24}" + "".join(f"{out[c].get(k, ''):>11}" for c in COLS))


if __name__ == "__main__":
    main()
