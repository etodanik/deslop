# Source archive

These are the raw sources behind the skill's rules, thresholds and lexicons. They are kept so the numbers can be re-derived and refreshed when new models or new studies appear.

**Licensing.** The files under `raw/` and `papers/` hold third-party text. Keep them for local analysis. Don't publish or redistribute them as part of the skill (if this becomes a git repo, add `sources/raw/` and `sources/papers/` to `.gitignore`, or use Git LFS in a private repo). Only the derived aggregates in `references/data/` and `evals/*.json` are meant to ship.

## Papers (`papers/`)

| File | Source | Used for |
|---|---|---|
| `terkon_dobrovoljc_2025_survey.pdf` (+ `.txt` extraction) | Terčon & Dobrovoljc, "Linguistic Characteristics of AI-Generated Text: A Survey" (44 studies) | lexical, grammatical and stylistic findings in `references/research.md` |
| `reinhart_2025_arxiv_2410.16107v2.pdf` (+ `.txt`) | Reinhart et al., "Do LLMs write like humans? Variation in grammatical and rhetorical styles", arXiv:2410.16107 (PNAS) | Biber-feature rates (participials 2–5×, nominalizations 1.5–2×), vocabulary tables |

Web sources, not archived (URLs in `references/research.md`): Clark, Martin & Mahowald, arXiv:2610.29162; Kobak et al. 2025; Paech et al. arXiv:2510.15061; Graphite "AI Tells" report; Wikipedia "Signs of AI writing"; blader/humanizer; tropes.fyi gist (ossa-ma, CC BY 4.0).

## Datasets (`raw/`)

| File | Source / license | Size | Used for |
|---|---|---|---|
| `graphite_ai_tells_articles.jsonl.gz` | Graphite "AI Tells" (2026), Drive release. Text is third-party; **not** CC-licensed | 187 MB, 9,984 topics × (human + 9 models) | `evals/validate_graphite.py` (metric validation), spaCy calibration |
| `elephant/` (repo, `datasets.zip`, `elephant_full_results.zip`) | ELEPHANT, Cheng et al. ICLR 2026, [myracheng/elephant](https://github.com/myracheng/elephant) + [OSF](https://osf.io/r3dmj/), CC0 | 237 MB; OEQ = 3,027 advice prompts × human + 12 models with sycophancy labels | `evals/validate_elephant.py` |
| `hc3_all.jsonl` | HC3, Guo et al. 2023, arXiv:2301.07597, [Hello-SimpleAI/HC3](https://huggingface.co/datasets/Hello-SimpleAI/HC3), CC BY-SA 4.0 | 74 MB, 24,322 questions with human + ChatGPT-3.5 answers | `evals/validate_hc3.py` (request-fit validation) |

Derived and shipped (`references/data/`, CC BY 4.0 from Graphite): `graphite_ai_tells_features.csv`, `graphite_ai_tells_tells_vs_human.csv.gz`, `graphite_tells_lexicon.json`.

Generated in this repo: `evals/before/*.md` (Sonnet default replies to the SimpleEnglish prompts), `evals/hc3/claude_answers.json` (Sonnet default replies to 40 HC3 questions), `evals/after/*.md` (deslop-pass rewrites), `evals/ab/` (A/B test of the aides: inputs, both arms, blind judgments, results), `evals/judge/` (sycophancy-judge agreement items and labels), and `references/data/biber_d1_norms.json` (Biber D1 norms from 200 Graphite human articles).

Models used by `deep_scan.py` (downloaded into the Hugging Face cache on first use): `gpt2` (124M) and `sentence-transformers/all-MiniLM-L6-v2`. The venv itself is about 1.2 GB.

## Refreshing

```bash
# re-derive the per-model tell lexicon (e.g. after Graphite publishes new models)
python3 scripts/build_tell_lexicon.py
# re-validate metrics against matched human/model articles
python3 evals/validate_graphite.py sources/raw/graphite_ai_tells_articles.jsonl.gz --topics 2000
# re-validate request-relative checks; add new-model answers to evals/hc3/ to compare generations
python3 evals/validate_hc3.py
python3 evals/validate_elephant.py
.venv/bin/python evals/validate_deep.py
.venv/bin/python evals/evaluate_ab.py
# mine a fresh fingerprint for any model you have outputs from
python3 scripts/mine_tells.py --ai outputs/ --human human_samples/
# parser-based metrics (spaCy lives in deslop/.venv, Python 3.12)
.venv/bin/python scripts/slop_scan.py draft.md --spacy
# rebuild and republish the bench viewer
python3 evals/build_viewer.py
```

To add a new model generation: collect its answers to `evals/hc3/sample_questions.json` and to a sample of Graphite topics, rerun the validators, and check which `DURABLE` checks still hold the same direction.
