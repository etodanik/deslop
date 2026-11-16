#!/usr/bin/env python3
"""mine_tells: build your own slop fingerprint, following Graphite's 2026 "AI Tells" method.

Give it a folder of model-written texts and a folder of human-written texts on the
same topics and in the same genre. It reports every unigram, bigram, trigram and
"frame" (an n-gram template where rare words become _) that the model uses at least
--ratio times as often as the humans, appears in enough model documents to matter,
and is ranked by rate ratio.

    python3 mine_tells.py --ai runs/model_x/ --human corpus/human/ --top 40
    python3 mine_tells.py --ai a/ --human h/ --json > tells.json

Why: tells change fast. In Graphite's data 65% of tells were unique to one model
family, and 55–72% changed between consecutive versions of the same family, so a
fixed word list goes stale. Mine the model you're actually editing.

Rates are occurrences per million tokens. A feature with zero human occurrences gets
ratio = inf. Defaults scale Graphite's document-frequency floors (500/250/100/120 of
10,000 docs) to your corpus size, with an absolute minimum of 3 documents.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import sys
from collections import Counter

TOKEN = re.compile(r"[a-z]+(?:'[a-z]+)?|[—–!?;:()]")
DF_FRACTION = {"unigram": 0.05, "bigram": 0.025, "trigram": 0.01, "frame": 0.012}


def load(folder: str) -> list[list[str]]:
    docs = []
    for p in sorted(pathlib.Path(folder).rglob("*")):
        if p.is_file() and p.suffix.lower() in (".md", ".txt", ""):
            t = p.read_text(encoding="utf-8", errors="ignore").lower().replace("’", "'")
            t = re.sub(r"```.*?```", " ", t, flags=re.S)
            t = re.sub(r"\be\.g\.", " eg ", t)
            t = re.sub(r"\bi\.e\.", " ie ", t)
            t = re.sub(r"`[^`\n]+`", " code ", t)
            docs.append(TOKEN.findall(t))
    return docs


def features(doc: list[str], common: set[str]) -> Counter:
    f = Counter()
    for n, kind in ((1, "unigram"), (2, "bigram"), (3, "trigram")):
        for i in range(len(doc) - n + 1):
            f[(kind, " ".join(doc[i:i + n]))] += 1
    masked = [w if w in common else "_" for w in doc]
    for n in range(3, 8):  # frames up to seven tokens, as in Graphite
        for i in range(len(masked) - n + 1):
            g = masked[i:i + n]
            lits = sum(1 for x in g if x != "_")
            if "_" in g and lits >= 2 and g[0] != "_" and g[-1] != "_":
                f[("frame", " ".join(g))] += 1
    return f


def mine(ai_docs, human_docs, ratio=2.0, top=50, min_docs=None, n_common=300):
    vocab = Counter(w for d in ai_docs + human_docs for w in d)
    common = {w for w, _ in vocab.most_common(n_common)}
    ai_tok = sum(len(d) for d in ai_docs) or 1
    hu_tok = sum(len(d) for d in human_docs) or 1
    ai_cnt, hu_cnt, ai_df = Counter(), Counter(), Counter()
    for d in ai_docs:
        f = features(d, common)
        ai_cnt.update(f)
        ai_df.update(f.keys())
    for d in human_docs:
        hu_cnt.update(features(d, common))
    out = {k: [] for k in DF_FRACTION}
    for (kind, g), c in ai_cnt.items():
        floor = min_docs if min_docs is not None else max(3, math.ceil(DF_FRACTION[kind] * len(ai_docs)))
        if ai_df[(kind, g)] < floor:
            continue
        if kind == "unigram" and not g.isalpha():
            pass  # keep punctuation unigrams (em dash, !, parentheses) — they are real tells
        ra = 1e6 * c / ai_tok
        rh = 1e6 * hu_cnt.get((kind, g), 0) / hu_tok
        r = math.inf if rh == 0 else ra / rh
        if r >= ratio:
            out[kind].append({"feature": g, "ratio": r, "ai_per_m": round(ra, 1), "human_per_m": round(rh, 1),
                              "ai_docs": ai_df[(kind, g)]})
    # also report strongly human-only features (the inverse direction), useful as "restore these"
    under = []
    for (kind, g), c in hu_cnt.items():
        if kind not in ("unigram", "bigram"):
            continue
        rh = 1e6 * c / hu_tok
        ra = 1e6 * ai_cnt.get((kind, g), 0) / ai_tok
        if rh >= 200 and (ra == 0 or rh / ra >= ratio):
            under.append({"feature": g, "ratio_human_over_ai": math.inf if ra == 0 else rh / ra,
                          "human_per_m": round(rh, 1), "ai_per_m": round(ra, 1)})
    for k in out:
        out[k].sort(key=lambda x: (-(x["ratio"] if x["ratio"] != math.inf else 1e12), -x["ai_docs"]))
        out[k] = out[k][:top]
    under.sort(key=lambda x: -(x["ratio_human_over_ai"] if x["ratio_human_over_ai"] != math.inf else 1e12))
    return {"ai_docs": len(ai_docs), "human_docs": len(human_docs), "ai_tokens": ai_tok, "human_tokens": hu_tok,
            "tells": out, "human_only": under[:top]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ai", required=True, help="folder of model-written texts")
    ap.add_argument("--human", required=True, help="folder of human-written texts (same genre/topics)")
    ap.add_argument("--ratio", type=float, default=2.0, help="minimum AI/human rate ratio (default 2, as Graphite)")
    ap.add_argument("--min-docs", type=int, help="override the document-frequency floor for every feature type")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    ai, hu = load(a.ai), load(a.human)
    if not ai or not hu:
        ap.error("both folders need at least one .md/.txt file")
    res = mine(ai, hu, a.ratio, a.top, a.min_docs)
    if a.json:
        print(json.dumps(res, indent=2, default=lambda x: "inf" if x == math.inf else x))
        return 0
    print(f"{res['ai_docs']} AI docs ({res['ai_tokens']} tokens) vs {res['human_docs']} human docs ({res['human_tokens']} tokens)")
    if res["ai_docs"] < 30:
        print("note: fewer than 30 AI docs; ratios are unstable. Graphite used 10,000 per model.")
    fmt = lambda r: "inf" if r == math.inf else f"{r:.1f}x"
    for kind, rows in res["tells"].items():
        print(f"\n## {kind}s over-used by the model (≥{a.ratio}x)")
        for r in rows:
            print(f"  {fmt(r['ratio']):>8}  {r['feature']:<40} ai {r['ai_per_m']}/M  human {r['human_per_m']}/M  in {r['ai_docs']} docs")
    print("\n## human-only features the model under-uses (restore where natural)")
    for r in res["human_only"]:
        print(f"  {fmt(r['ratio_human_over_ai']):>8}  {r['feature']:<40} human {r['human_per_m']}/M  ai {r['ai_per_m']}/M")
    return 0


if __name__ == "__main__":
    sys.exit(main())
