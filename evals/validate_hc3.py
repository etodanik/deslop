#!/usr/bin/env python3
"""Validate request-relative checks on HC3 (Guo et al. 2023): same questions, human vs ChatGPT answers.

    python3 evals/validate_hc3.py [sources/raw/hc3_all.jsonl] [--claude evals/hc3/claude_answers.json]

Reports per source (reddit_eli5, open_qa, finance, medicine, wiki_csai) the rate of restated questions,
closing recaps, direct first sentences for yes/no questions, novelty and length ratio, plus a few durable
style metrics. With --claude, it also scores current-model answers to the 40 questions in
evals/hc3/sample_questions.json against the human and ChatGPT answers to the same questions.
Aggregates go to evals/hc3_validation.json. HC3 is CC BY-SA 4.0.
"""
import argparse
import json
import pathlib
import re
import statistics
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import slop_scan as ss  # noqa: E402

STYLE = ["word_length", "participial_clauses", "importance_flags", "contrast_frames", "echo_fragments"]


def detok(t: str) -> str:
    t = re.sub(r" (n't|'s|'re|'ve|'ll|'d|'m)\b", r"\1", t)
    t = re.sub(r" ([.,;:!?%)\]])", r"\1", t)
    t = re.sub(r"([(\[$]) ", r"\1", t)
    t = re.sub(r'" ([^"]*?) "', r'"\1"', t)
    return t.strip()


def score(question, answer):
    d = ss.Doc(answer)
    if len(d.words) < 30:
        return None
    rf = ss.run_metric("request_fit", d, prompt=question)
    if rf.get("restates_question") is None:
        return None
    out = {k: rf[k] for k in ("restates_question", "closing_recap", "novelty", "length_ratio",
                              "first_sentence_from_question")}
    if rf["yes_no_question"]:
        out["direct_first_sentence"] = int(rf["direct_first_sentence"])
    out["words"] = len(d.words)
    out["word_length"] = ss.run_metric("word_length", d)["mean_letters"]
    for m in ("participial_clauses", "importance_flags", "contrast_frames", "echo_fragments"):
        r = ss.run_metric(m, d)
        out[m + "_per_1k"] = 1000 * r["count"] / len(d.words)
    return out


def summarize(vals):
    keys = sorted({k for v in vals for k in v})
    res = {}
    for k in keys:
        xs = [v[k] for v in vals if k in v and v[k] is not None]
        if xs:
            res[k] = {"mean": round(statistics.mean(xs), 3),
                      "median": round(statistics.median(xs), 3), "n": len(xs)}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=str(ROOT / "sources" / "raw" / "hc3_all.jsonl"))
    ap.add_argument("--claude", default=str(ROOT / "evals" / "hc3" / "claude_answers.json"))
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(a.path, encoding="utf-8")]
    acc = defaultdict(lambda: {"human": [], "chatgpt": []})
    for r in rows:
        q = detok(r["question"]).replace("ELI5: ", "", 1)
        for side, key in (("human", "human_answers"), ("chatgpt", "chatgpt_answers")):
            if r[key]:
                s = score(q, detok(r[key][0]))
                if s:
                    acc[r["source"]][side].append(s)
    out = {"by_source": {src: {side: summarize(v) for side, v in d.items()} for src, d in acc.items()}}

    cpath = pathlib.Path(a.claude)
    if cpath.exists():
        claude = json.loads(cpath.read_text())
        qs = json.loads((ROOT / "evals" / "hc3" / "sample_questions.json").read_text())
        index = {detok(r["question"]).replace("ELI5: ", "", 1): r for r in rows}
        trio = {"human": [], "chatgpt": [], "claude": []}
        for q in qs:
            r = index.get(q["question"])
            ans = claude.get(q["id"])
            if not r or not ans:
                continue
            for side, text in (("human", detok(r["human_answers"][0])), ("chatgpt", detok(r["chatgpt_answers"][0])),
                               ("claude", ans)):
                s = score(q["question"], text)
                if s:
                    trio[side].append(s)
        out["sample_40"] = {side: summarize(v) for side, v in trio.items()}
    (ROOT / "evals" / "hc3_validation.json").write_text(json.dumps(out, indent=1))

    cols = ["restates_question", "closing_recap", "direct_first_sentence", "novelty", "length_ratio", "words",
            "word_length", "participial_clauses_per_1k", "importance_flags_per_1k", "contrast_frames_per_1k",
            "echo_fragments_per_1k"]
    for src, d in out["by_source"].items():
        print(f"\n== {src}  (n human {len(acc[src]['human'])}, chatgpt {len(acc[src]['chatgpt'])})")
        for c in cols:
            h, g = d["human"].get(c), d["chatgpt"].get(c)
            if h and g:
                print(f"  {c:28} human {h['mean']:>8}   chatgpt {g['mean']:>8}   (medians {h['median']} / {g['median']})")
    if "sample_40" in out:
        print("\n== 40-question sample: human / ChatGPT-3.5 (2023) / current Claude (Sonnet)")
        for c in cols:
            vs = [out["sample_40"][s].get(c, {}).get("mean") for s in ("human", "chatgpt", "claude")]
            print(f"  {c:28} " + "   ".join(f"{v!s:>8}" for v in vs))


if __name__ == "__main__":
    main()
