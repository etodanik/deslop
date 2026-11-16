#!/usr/bin/env python3
"""deep_scan: model-based measurements (needs deslop/.venv: spaCy, torch, transformers, sentence-transformers).

    .venv/bin/python scripts/deep_scan.py draft.md                 # all three
    .venv/bin/python scripts/deep_scan.py draft.md --only surprisal redundancy
    .venv/bin/python scripts/deep_scan.py draft.md --json
    .venv/bin/python scripts/deep_scan.py --calibrate-biber        # rebuild Biber norms from Graphite human articles

surprisal   GPT-2 (124M) per-token surprisal in bits. Reports mean, the spread of sentence-mean surprisal
            (uniform information density: human text varies more), the share of highly predictable tokens,
            and the most predictable sentences (candidates for cutting: they say what the reader expected).
redundancy  MiniLM sentence embeddings. Sentences that restate an earlier one (cosine >= 0.80), how much
            the last paragraph restates the opening (tie-back), and mean similarity within paragraphs
            (one point diluted across sentences).
biber_d1    Biber's (1988) Dimension 1, involved vs informational production, from spaCy features:
            sum of z-scores of the involved features minus the informational ones, normalized against
            human web articles (references/data/biber_d1_norms.json). Positive = involved/conversational,
            negative = informational/dense. LLM text sits at the informational end regardless of genre.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import os
import pathlib
import random
import re
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import slop_scan as ss  # noqa: E402

NORMS = ROOT / "references" / "data" / "biber_d1_norms.json"
_CACHE = {}


# ------------------------------------------------------------------ surprisal

def _lm():
    if "lm" not in _CACHE:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        tok = AutoTokenizer.from_pretrained("gpt2")
        model = AutoModelForCausalLM.from_pretrained("gpt2").eval()
        _CACHE["lm"] = (torch, tok, model)
    return _CACHE["lm"]


def surprisal(d: ss.Doc, max_tokens: int = 2048) -> dict:
    torch, tok, model = _lm()
    text = d.text
    enc = tok(text, return_offsets_mapping=True)
    ids, offs = enc["input_ids"][:max_tokens], enc["offset_mapping"][:max_tokens]
    if len(ids) < 20:
        return {"mean_bits": None, "note": "too short"}
    bits = [None] * len(ids)
    win, stride = 1024, 512
    with torch.no_grad():
        for start in range(0, len(ids), stride):
            chunk = ids[max(0, start - (win - stride)): start + stride]
            ctx = start - max(0, start - (win - stride))
            x = torch.tensor([chunk])
            logp = torch.log_softmax(model(x).logits[0], -1)
            for j in range(max(ctx, 1), len(chunk)):
                gi = max(0, start - (win - stride)) + j
                if gi < len(ids) and bits[gi] is None:
                    bits[gi] = -logp[j - 1, chunk[j]].item() / math.log(2)
            if start + stride >= len(ids):
                break
    vals = [b for b in bits if b is not None]
    # sentence means: map tokens to sentences by character offset
    spans, pos = [], 0
    for s in d.sentences:
        i = text.find(s[:30], pos)
        if i < 0:
            continue
        spans.append((i, i + len(s), s))
        pos = i + len(s)
    sent_bits = []
    for a, b, s in spans:
        bs = [bits[k] for k, (o1, o2) in enumerate(offs) if bits[k] is not None and o1 >= a and o2 <= b]
        if len(bs) >= 6:
            sent_bits.append((statistics.mean(bs), s))
    sm = [x for x, _ in sent_bits]
    srt = sorted(sent_bits)
    return {"mean_bits": round(statistics.mean(vals), 2), "token_sd_bits": round(statistics.pstdev(vals), 2),
            "sentence_mean_sd": round(statistics.pstdev(sm), 2) if len(sm) > 2 else None,
            "share_under_1_bit": round(sum(1 for v in vals if v < 1) / len(vals), 3), "tokens": len(vals),
            "most_predictable": [f"{x:.2f} bits: {s[:110]}" for x, s in srt[:3]],
            "least_predictable": [f"{x:.2f} bits: {s[:110]}" for x, s in srt[-2:]]}


# ------------------------------------------------------------------ redundancy

def _emb():
    if "emb" not in _CACHE:
        from sentence_transformers import SentenceTransformer
        _CACHE["emb"] = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _CACHE["emb"]


def redundancy(d: ss.Doc, thresh: float = 0.80) -> dict:
    sents = [s for s in d.sentences if len(ss.words_of(s)) >= 4]
    if len(sents) < 4:
        return {"restatements": None, "note": "too few sentences"}
    import numpy as np
    m = _emb()
    E = m.encode(sents, normalize_embeddings=True)
    S = E @ E.T
    pairs, maxprev = [], []
    for i in range(1, len(sents)):
        j = int(np.argmax(S[i, :i]))
        maxprev.append(float(S[i, j]))
        if S[i, j] >= thresh:
            pairs.append((round(float(S[i, j]), 2), j, i))
    out = {"restatements": len(pairs), "restatement_share": round(len(pairs) / (len(sents) - 1), 3),
           "mean_max_prev_sim": round(statistics.mean(maxprev), 3),
           "pairs": [f"{c}: [{sents[j][:60]}] ~ [{sents[i][:60]}]" for c, j, i in sorted(pairs, reverse=True)[:5]]}
    paras = [p for p in d.paragraphs if len(ss.words_of(p)) >= 8]
    if len(paras) >= 3:
        P = m.encode(paras, normalize_embeddings=True)
        out["tieback_last_vs_first"] = round(float(P[-1] @ P[0]), 3)
        out["tieback_last_vs_best_prior"] = round(float(max(P[-1] @ P[k] for k in range(len(paras) - 1))), 3)
    within = []
    for p in d.paragraphs:
        ps = [s for s in ss.split_sentences(p) if len(ss.words_of(s)) >= 4]
        if len(ps) >= 3:
            Q = m.encode(ps, normalize_embeddings=True)
            within += [float(Q[a] @ Q[b]) for a in range(len(ps)) for b in range(a + 1, len(ps))]
    out["mean_within_paragraph_sim"] = round(statistics.mean(within), 3) if within else None
    return out


# ------------------------------------------------------------------ Biber D1

PRIVATE = set("""accept anticipate ascertain assume believe calculate check conclude conjecture consider decide deduce
deem demonstrate determine discover doubt dream ensure establish estimate expect fancy fear feel find foresee forget
gather guess hear hold hope imagine imply indicate infer insure judge know learn mean note notice observe perceive
presume presuppose pretend prove realize reason recall reckon recognize reflect remember reveal see sense show signify
suppose suspect think understand""".split())
EMPHATIC = re.compile(r"\b(for sure|a lot|such an?|really|so|just|totally|definitely|actually|indeed|surely)\b", re.I)
HEDGE = re.compile(r"\b(at about|something like|more or less|almost|maybe|sort of|kind of|perhaps|possibly)\b", re.I)
AMPLIFIER = re.compile(r"\b(absolutely|altogether|completely|enormously|entirely|extremely|fully|greatly|highly|"
                       r"intensely|perfectly|strongly|thoroughly|totally|utterly|very)\b", re.I)
INDEF = re.compile(r"\b(anybody|anyone|anything|everybody|everyone|everything|nobody|none|nothing|nowhere|somebody|"
                   r"someone|something)\b", re.I)
WH = {"what", "where", "when", "how", "whether", "why", "whoever", "whomever", "whichever", "wherever", "whenever",
      "whatever", "who", "which"}
POS_FEATURES = ["private_verbs", "that_deletion", "contractions", "present_tense", "second_person", "do_proverb",
                "analytic_negation", "demonstrative_pronouns", "emphatics", "first_person", "pronoun_it",
                "be_main_verb", "causative_sub", "discourse_particles", "indefinite_pronouns", "hedges",
                "amplifiers", "sentence_relatives", "wh_questions", "possibility_modals", "clausal_coordination",
                "wh_clauses", "final_prepositions"]
NEG_FEATURES = ["nouns", "word_length", "prepositions", "type_token_ratio", "attributive_adjectives"]


def _nlp():
    if "nlp" not in _CACHE:
        import spacy
        _CACHE["nlp"] = spacy.load("en_core_web_sm")
    return _CACHE["nlp"]


def biber_features(text: str) -> dict:
    doc = _nlp()(text[:20000])
    toks = [t for t in doc if not t.is_space and not t.is_punct]
    n = max(len(toks), 1)
    per = lambda c: 1000.0 * c / n  # noqa: E731
    low = text.lower()
    f = {}
    f["private_verbs"] = per(sum(1 for t in toks if t.pos_ == "VERB" and t.lemma_.lower() in PRIVATE))
    f["that_deletion"] = per(sum(1 for t in doc if t.dep_ == "ccomp" and t.head.lemma_.lower() in PRIVATE
                                 and not any(c.dep_ == "mark" and c.lower_ == "that" for c in t.children)))
    f["contractions"] = per(len(re.findall(r"\b\w+(n't|'re|'ve|'ll|'d|'m)\b|\b(it|that|there|what|he|she)'s\b", low)))
    f["present_tense"] = per(sum(1 for t in toks if t.tag_ in ("VBP", "VBZ")))
    f["second_person"] = per(sum(1 for t in toks if t.lower_ in ("you", "your", "yours", "yourself", "yourselves")))
    f["do_proverb"] = per(sum(1 for t in toks if t.lemma_ == "do" and t.dep_ not in ("aux", "auxpass")
                              and not any(c.dep_ in ("dobj", "xcomp", "ccomp") for c in t.children)))
    f["analytic_negation"] = per(sum(1 for t in toks if t.lower_ in ("not", "n't")))
    f["demonstrative_pronouns"] = per(sum(1 for t in toks if t.lower_ in ("this", "that", "these", "those")
                                          and t.dep_ in ("nsubj", "dobj", "pobj", "nsubjpass")))
    f["emphatics"] = per(len(EMPHATIC.findall(low)))
    f["first_person"] = per(sum(1 for t in toks if t.lower_ in ("i", "me", "my", "mine", "myself", "we", "us", "our",
                                                                "ours", "ourselves")))
    f["pronoun_it"] = per(sum(1 for t in toks if t.lower_ == "it"))
    f["be_main_verb"] = per(sum(1 for t in toks if t.lemma_ == "be" and t.dep_ in ("ROOT", "ccomp", "conj", "advcl", "relcl")))
    f["causative_sub"] = per(sum(1 for t in toks if t.lower_ == "because"))
    f["discourse_particles"] = per(sum(1 for s in doc.sents for t in list(s)[:1] if t.lower_ in ("well", "now", "anyway", "anyhow", "anyways")))
    f["indefinite_pronouns"] = per(len(INDEF.findall(low)))
    f["hedges"] = per(len(HEDGE.findall(low)))
    f["amplifiers"] = per(len(AMPLIFIER.findall(low)))
    f["sentence_relatives"] = per(len(re.findall(r", which\b", low)))
    f["wh_questions"] = per(sum(1 for s in doc.sents if s.text.strip().endswith("?") and s[0].lower_ in WH | {"how"}))
    f["possibility_modals"] = per(sum(1 for t in toks if t.lower_ in ("can", "could", "may", "might")))
    f["clausal_coordination"] = per(sum(1 for t in toks if t.dep_ == "cc" and t.lower_ == "and" and t.head.pos_ in ("VERB", "AUX")
                                        and any(c.dep_ == "conj" and c.pos_ in ("VERB", "AUX") and any(g.dep_.startswith("nsubj") for g in c.children) for c in t.head.children)))
    f["wh_clauses"] = per(sum(1 for t in doc if t.dep_ == "ccomp" and any(c.lower_ in WH for c in t.children if c.i < t.i)))
    f["final_prepositions"] = per(sum(1 for s in doc.sents for t in [x for x in s if not x.is_punct][-1:] if t.pos_ == "ADP"))
    f["nouns"] = per(sum(1 for t in toks if t.pos_ in ("NOUN", "PROPN")))
    f["word_length"] = statistics.mean(len(t.text) for t in toks) if toks else 0.0
    f["prepositions"] = per(sum(1 for t in toks if t.pos_ == "ADP"))
    w400 = [t.lower_ for t in toks[:400]]
    f["type_token_ratio"] = len(set(w400)) / max(len(w400), 1)
    f["attributive_adjectives"] = per(sum(1 for t in toks if t.pos_ == "ADJ" and t.dep_ == "amod"))
    return f


def biber_d1(d: ss.Doc) -> dict:
    if not NORMS.exists():
        return {"d1": None, "note": "run --calibrate-biber first"}
    norms = json.loads(NORMS.read_text())
    f = biber_features(d.text)
    z = {k: (f[k] - norms[k]["mean"]) / (norms[k]["sd"] or 1) for k in POS_FEATURES + NEG_FEATURES}
    z = {k: max(-5, min(5, v)) for k, v in z.items()}
    score = sum(z[k] for k in POS_FEATURES) - sum(z[k] for k in NEG_FEATURES)
    contrib = {k: (z[k] if k in POS_FEATURES else -z[k]) for k in z}   # + pushes involved, - pushes informational
    top = sorted(contrib.items(), key=lambda kv: kv[1])
    return {"d1": round(score, 2), "norm": "z vs human web articles (Graphite); 0 = human average",
            "pulling_informational": [f"{k} {v:+.1f}" for k, v in top[:4]],
            "pulling_involved": [f"{k} {v:+.1f}" for k, v in top[-3:]]}


def calibrate_biber(n: int = 200):
    path = ROOT / "sources" / "raw" / "graphite_ai_tells_articles.jsonl.gz"
    rows = gzip.open(path, "rt").readlines()
    random.Random(21).shuffle(rows)
    feats = []
    for line in rows[: n * 2]:
        t = json.loads(line)["human"]
        if len(t.split()) >= 300:
            feats.append(biber_features(t))
        if len(feats) >= n:
            break
    norms = {k: {"mean": statistics.mean(x[k] for x in feats), "sd": statistics.pstdev(x[k] for x in feats)}
             for k in POS_FEATURES + NEG_FEATURES}
    norms["_meta"] = {"source": "Graphite human web articles (pre-2022)", "n": len(feats)}
    NORMS.write_text(json.dumps(norms, indent=1))
    print(f"wrote {NORMS} from {len(feats)} human articles")


TOOLS = {"surprisal": surprisal, "redundancy": redundancy, "biber_d1": biber_d1}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?")
    ap.add_argument("--only", nargs="+", choices=sorted(TOOLS))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--calibrate-biber", action="store_true")
    a = ap.parse_args(argv)
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    if a.calibrate_biber:
        calibrate_biber()
        return 0
    if not a.file:
        ap.error("file required")
    d = ss.Doc(ss.read(a.file))
    res = {k: TOOLS[k](d) for k in (a.only or TOOLS)}
    if a.json:
        print(json.dumps(res, indent=2))
        return 0
    for k, r in res.items():
        print(f"## {k}")
        for kk, v in r.items():
            if isinstance(v, list):
                for x in v:
                    print(f"   {kk}: {x}")
            else:
                print(f"   {kk}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
