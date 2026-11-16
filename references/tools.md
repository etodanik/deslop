# Tools

Everything runs from the `deslop/` folder. `slop_scan.py`, `check_invariants.py`, `judge_prompt.py` and `mine_tells.py` use only the standard library. `deep_scan.py` and `--spacy` need `deslop/.venv` (Python 3.12 with spaCy, torch, transformers and sentence-transformers). Each tool below lists the evidence for using it. Numbers come from `references/research.md` and `evals/`.

## slop_scan.py: the scanner (47 metrics)

```bash
python3 scripts/slop_scan.py draft.md --agent --self claude --genre chat --prompt question.txt   # for agents
python3 scripts/slop_scan.py revised.md --before draft.md --self claude --genre chat            # regressions
python3 scripts/slop_scan.py draft.md                       # full human-readable report, by layer
python3 scripts/slop_scan.py draft.md --durable --flagged-only
python3 scripts/slop_scan.py draft.md -m participial_clauses --hits 20   # one metric as a measurement tool
python3 scripts/slop_scan.py --list                          # every metric, its threshold, what it measures
```

From Python: `from slop_scan import Doc, run_metric, METRICS; run_metric("word_length", Doc(text))`.

| Flag | What it does | Evidence |
|---|---|---|
| `--agent` | Flagged metrics only, durable checks first. Each flag names the `patterns.md` section with the fix and quotes the offending sentences by number (s0, s1, …). About 450 tokens vs about 2,100 for the full report | Token cost. In the A/B it was part of arm B; not shown to improve quality on its own |
| `--self claude\|gpt\|gemini` | Lists your own model family's tells in the text (Graphite tell lists, ≥4× human), with sentence numbers | **A/B: Claude tells per answer 6.2 → 1.5 (fewer in all 6 answers); blind judge rated arm B more human-sounding 3–1**. Without it, a Claude reviser left its own tells in place (6.2 → 6.2). A further tells-only pass once likeness is below about 0.3 hurt: blind judge preferred one pass 5–0 |
| `--before FILE` | Regression mode: fixed / still flagged / newly flagged metrics, word length and MTLD moving toward or away from human, own-family tells the revision added (with `--self`), and a facts check | Caught "close that gap" (85×) and other added tells in this repo's own rewrites |
| `--prompt Q` | Enables `request_fit`: restated question, closing recap, length and length ratio against HC3 human medians | Length vs the ask is the request signal that grew across generations (human 142 words, ChatGPT-3.5 183, Claude 294 on the same questions). In the A/B neither arm shortened toward it, so *you* have to act on it |
| `--durable` | Only the checks that held for every model in both Graphite and ELEPHANT | See `research.md` |
| `--genre` | chat, code, docs, email, essay, academic, fiction, marketing thresholds | |
| `--baseline FILE` | Deltas against a human sample (voice anchor); enables `unattested_bigrams`, `js_divergence` | |
| `--spacy` | Parser-based noun stacks, dependency length, dropped relativizers, inanimate agents. `.venv/bin/python` | Chat, code and agent output only. In article prose, models score *below* humans on these |
| `--no-refs` | Hides Graphite reference values (`ref: human 4.9 \| opus5 5.2 \| …`) | |

**Metrics by layer.** Content: `request_fit`, `stock_phrases`, `meta_reference`, `vague_references`, `specificity`, `tradeoff_dodges`, `importance_flags`. Structure: `triads`, `contrast_frames`, `staged_reveals`, `count_fragments`, `wh_headings`, `bookend_echo`, `paragraph_rhythm`, `formatting`. Grammar A: `participial_clauses`, `nominalizations`, `that_subjects`, `copula_avoidance`, `concessive_frames`, `coordination`, `connectives`, `stance`, `sentence_openers`. Grammar B: `inanimate_agents`, `denominal_verbs`, `noun_stacks`, `dropped_that`, `dependency_proxy`. Rhythm: `sentence_length`, `sentence_shape`, `echo_fragments`. Lexicon: `model_fingerprint`, `word_length`, `lexical_diversity`, `flagged_vocab`, `intensifiers`, `mannered_frames`, `repeated_ngrams`, `hyphen_compounds`, `human_markers`, `pronouns`, `contractions`, `unattested_bigrams`, `js_divergence`. Punctuation: `punctuation`, `symbol_prose`.

**Model fingerprint.** For each of nine models, there's a data-driven list of 250 terms and frames it uses at ≥4× the human rate in ≥3% of its articles, from Graphite's `tells_vs_human` data. Each list gives its expected rate in human and in model text, so `tell_likeness` is calibrated: 0 = human rate, 1 = that model's rate. It was built from web articles, and it also tells human from model text on ELEPHANT's advice replies (human 0.26 vs 0.59–0.82), including models it never saw (DeepSeek, Qwen, Llama, Mistral).

## check_invariants.py: did the revision keep the facts?

```bash
python3 scripts/check_invariants.py draft.md revised.md     # exit 1 if numbers, code or links were dropped
```

Dropped numbers, code spans and links are errors. Dropped names, quotes, negations and hedges are warnings: a pass may remove a generic hedge, but on purpose. Also flags *added* numbers and names, to catch invented facts. `--before` includes it.

Evidence: on this repo's first eight rewrites it found real losses (`--insecure`, the `PUT /orders/123` example, "200 requests in two seconds", "400 seconds", `medium: Memory`) once list numbering and reformatted code stopped producing false alarms. In the A/B neither arm dropped a fact, so its benefit there was zero. Keep it as a cheap safety net.

## deep_scan.py: model-based measurements (`.venv`)

```bash
.venv/bin/python scripts/deep_scan.py draft.md                       # all three
.venv/bin/python scripts/deep_scan.py draft.md --only biber_d1 redundancy
```

| Tool | Output | Evidence (Cohen's d vs human; n = 40 per corpus) | Use |
|---|---|---|---|
| `biber_d1` | Biber's Dimension 1, involved (+) vs informational (−), z-scored against human web articles; lists the features pulling each way | Lower than human for 7 of 8 model/corpus pairs (ELEPHANT d −0.7 to −1.1) | **Durable register check** |
| `redundancy` | MiniLM embeddings: restated sentences (cos ≥ 0.80), mean similarity to the closest earlier sentence, tie-back of the last paragraph to the first, within-paragraph similarity | Higher than human for every model in advice replies (d +0.55 to +2.56); not in web articles (human boilerplate) | Chat and advice: find restatement and one point diluted across sentences |
| `surprisal` | GPT-2 bits per token; spread of sentence-mean surprisal; the highest- and lowest-probability sentences | Mean surprisal flips sign by model (Claude/GPT higher than human, Gemini/Llama lower). Don't use the level | **Diagnostic only**: the highest-probability sentences are cut candidates (in the test essay they were "It's important to note…" and "In conclusion…") |

`--calibrate-biber` rebuilds `references/data/biber_d1_norms.json` from Graphite human articles.

## judge_prompt.py: sycophancy judging (advice and chat)

```bash
python3 scripts/judge_prompt.py --rubric validation --prompt question.txt --response reply.md
```

This fills ELEPHANT's CC0 judge rubrics (`references/judges/elephant_sycophancy.md`). Hand the output to a fresh subagent that hasn't seen your draft, and it answers with one digit. Checked against ELEPHANT's GPT-4o labels on 40 blind items: **validation agreement 90% (κ 0.80) and indirectness 95% (κ 0.90): use these. Framing 74% (κ 0.02, chance level): don't use it.** Models score far above humans on both rubrics that held up (validation 0.50–0.81 vs 0.21; indirectness 0.53–0.98 vs 0.21).

## mine_tells.py and build_tell_lexicon.py: refresh the fingerprints

```bash
python3 scripts/mine_tells.py --ai outputs/ --human human_samples/ --top 40
python3 scripts/build_tell_lexicon.py            # rebuild graphite_tells_lexicon.json from the CSV
```

Tells churn between releases: 55–72% change per version in Graphite's data. Mine the model you're editing when you have its outputs plus human text on the same topics.

## Validation harnesses (`evals/`)

`validate_graphite.py`, `validate_hc3.py`, `validate_elephant.py`, `validate_deep.py`, `evaluate_ab.py`, `build_viewer.py` (bench). Sources and refresh commands: `sources/MANIFEST.md`.
