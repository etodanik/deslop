# Data

`graphite_ai_tells_features.csv`: per-article feature means for human web articles and nine models
(GPT-4.1, GPT-5, GPT-5.6 Sol, GPT-6 Astra, Claude Opus 4 / 4.6 / 5, Gemini 2.5 Pro / 3.1 Pro), with
Cohen's d vs human, over 9,984 matched topics. Columns: `feature`, `<corpus>_mean`, `<model>_cohens_d_vs_human`.

Source and license: Graphite, "AI Tells" (2026). https://graphite.io/five-percent/research/ai-tells,
released under CC BY 4.0. Unmodified copy of `ai_tells_features.csv`.

`slop_scan.py` uses these values as reference points (`GRAPHITE_REF`) and threshold anchors.

`graphite_ai_tells_tells_vs_human.csv.gz`: unmodified copy of Graphite's `ai_tells_tells_vs_human.csv.gz`
(67,520 rows: one per term × model, n-grams and frames, model-favored and human-favored, with
per-1k-position rates, article counts, ratio and frame lift). CC BY 4.0, same credit as above.

`graphite_tells_lexicon.json`: derived from the CSV above by `scripts/build_tell_lexicon.py`.
For each of the nine models it holds the top 250 model-favored and top 250 human-favored terms
(ratio ≥ 4, in ≥ 3% of articles, frames with lift ≥ 1.5), plus the summed expected rate per 1k
tokens in human and model text. `slop_scan.py -m model_fingerprint` reads it. Rebuild with
different cut-offs: `python3 scripts/build_tell_lexicon.py --min-ratio 3 --top 400`.

The 187 MB `ai_tells_articles.jsonl.gz` (full article text) is not included. It holds third-party
copyrighted pages and model output, and Graphite's CC BY license does not cover it.
