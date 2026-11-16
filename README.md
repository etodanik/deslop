# deslop

deslop is a Claude skill that revises a draft to remove the fingerprints of LLM-generated prose. Its rules come from corpus-linguistics and psycholinguistics research comparing human and model text, and they were checked against three public corpora in which humans and models answered the same prompts.

The pass changes how the text is written, not what it says. It doesn't detect authorship, and it doesn't invent details to make text sound human.

The research behind it is in [`references/research.md`](references/research.md).

## Example

A client email in Claude's default style (228 words, 3 Claude tells) opens like this:

> I wanted to reach out with an important update on your website launch. We're now targeting **March 17** instead of the original March 3 date, a delay of two weeks.
>
> The reason for the delay is that the payment provider's API review is taking longer than we anticipated. Because secure payment processing is a critical part of the site, we can't go live until the review is complete.

After one pass (132 words, 0 Claude tells, no facts dropped):

> Your website launch will slip two weeks, from March 3 to March 17. The payment provider's API review is taking longer than we planned, and we can't go live with payments until it's done.
## Install

Copy this folder into your skills directory:

```bash
cp -r deslop ~/.claude/skills/deslop
```

Then ask Claude to "deslop this", "make this sound less like AI", or "run a slop pass" on a draft.

## The pass

1. Pick the genre and reader (chat, email, docs, code, essay, academic, fiction, marketing).
2. Scan the draft. The scanner lists each problem with the sentence it's in, the reviser's own model-family tells, and the reply's length against the question.
3. Revise from the outside in: content, structure, sentence grammar, sentence length, word choice, punctuation.
4. Re-scan against the original. This lists new flags, tells the revision added, and dropped facts (numbers, code, links, negations, hedges).
5. Stop once the text is in the human range. A second tells-only pass made answers worse in a blind test (5–0).

`SKILL.md` has the full workflow.

## Tools

The core tools need only Python 3:

```bash
python3 scripts/slop_scan.py draft.md --agent --self claude --genre chat --prompt question.txt
python3 scripts/slop_scan.py revised.md --before draft.md --self claude --genre chat
python3 scripts/check_invariants.py draft.md revised.md
python3 scripts/slop_scan.py --list
```

The optional extras need a Python 3.12 venv with spaCy, torch, transformers and sentence-transformers in `.venv`. They are `deep_scan.py` (Biber Dimension 1, semantic redundancy, GPT-2 surprisal), `--spacy` parser metrics, and `judge_prompt.py` (sycophancy rubrics for a judge subagent).

`references/tools.md` lists every flag and metric with the evidence for it.

## Files

| Path | Contents |
|---|---|
| `SKILL.md` | the workflow Claude follows |
| `references/` | pattern catalog, genre targets, tool reference, research notes, judge rubrics, derived data |
| `scripts/` | scanner, facts checker, model-based tools, tell miner |
| `evals/` | validation scripts, A/B tests, before/after samples, the bench viewer |
| `examples/` | hand-written before/after caricatures |
| `sources/` | papers and raw datasets (local only; see `sources/MANIFEST.md`) |

## Evidence

The rules come from Reinhart et al. (2025), Terčon & Dobrovoljc (2025), Clark, Martin & Mahowald (2026), Graphite's "AI Tells" (2026), HC3 (Guo et al. 2023) and ELEPHANT (Cheng et al. 2026). `references/research.md` lists every source with its numbers, including which checks held across every model generation and which ones flipped.

## Licensing

The skill's code and docs are this project's own. `references/data/` includes Graphite measurements under CC BY 4.0, with credit. `evals/` includes short excerpts from HC3 (Guo et al. 2023, CC BY-SA 4.0) and ELEPHANT (Cheng et al. 2026, CC0) for the bench and the judge check. `sources/raw/` and `sources/papers/` hold third-party text for local analysis only. Don't redistribute them.
