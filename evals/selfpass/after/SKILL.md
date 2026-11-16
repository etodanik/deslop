---
name: deslop
description: Run a revision pass that takes the fingerprints of LLM-generated prose ("slop") from a draft, using findings from corpus linguistics and psycholinguistics on how AI text differs from human text. Use when the user asks to de-slopify, de-AI, humanize, "make this sound less like ChatGPT", tighten a draft that reads as machine-written, or run a slop pass on text (their own draft, or something you just wrote). Not for detecting authorship or judging whether someone used AI.
---

# De-slop pass

Instruction-tuned LLMs write in one register no matter what they are asked for: noun-heavy, dense, impersonal, evenly paced, positive and neutral, with a small set of favored words and sentence shapes. Humans vary their writing with genre, audience and mood. That missing variation is what readers pick up on. Banned words are a small part of it.

This pass moves the text toward what a skilled human would write **in this genre for this reader**. It does not swap synonyms. A synonym swap just gives you a new kind of slop.

Evidence for every rule below is in `references/research.md`. The full pattern catalog with rewrite moves is in `references/patterns.md`. Per-genre targets are in `references/register.md`. Every tool and flag, with the evidence for each, is in `references/tools.md`.

## When the user asks for a pass

### 1. Fix the target before touching the text

Settle these first. Ask only if you can't infer them.

- **Genre and medium**: Slack message, README, essay, fiction, academic abstract, cover letter, docs. Read the matching section of `references/register.md`. Register drives everything else. Some "slop" features are correct in some genres: nominalizations belong in an abstract, and "palpable" can be fine in a novel.
- **Voice anchor**: if the user has supplied their own writing, or the surrounding document has human-written parts, run the scanner on that and treat its profile as the target. Text written to match a real human sample ends up much closer to human style than text generated from a topic alone.
- **Intensity**: `light` (lexicon, clichés, formatting), `standard` (default: adds sentence grammar and rhythm), `deep` (also restructures paragraphs and cuts padding content). Default to `standard`.
- **Invariants**: facts, numbers, names, claims, code, quotes and links stay exactly as they are. Never invent anecdotes, opinions, data or first-person experience to make text "sound human". If a passage needs a concrete example the source lacks, mark it `[example needed]`. Don't fabricate one.

### 2. Scan

```bash
python3 scripts/slop_scan.py draft.md --agent --self claude --genre chat --prompt question.txt
```

`--agent` prints only the flagged metrics, durable checks first. It quotes the offending sentences by number and names the `references/patterns.md` section with the fix. `--self` names your own model family (`claude`, `gpt` or `gemini`) and lists the tells of that family found in the text. In an A/B test, revisers with `--self` cut their own family's tells from 6.2 to 1.5 per answer, and a blind judge rated the result more human-sounding (3–1). Without it the tells stayed (6.2 → 6.2). `--prompt` adds `request_fit`: whether the reply restates or recaps the question, and its length against human answers to similar questions. Omit `--prompt` when there's no request.

Then **read the text yourself** for what the scanner can't see: empty claims, summary paragraphs, fake balance, unearned profundity. For advice or emotional replies, check sycophancy with `scripts/judge_prompt.py --rubric validation` (and `indirectness`) in a fresh subagent. Both rubrics agree with ELEPHANT's labels at κ ≥ 0.80.

Optional, with `deslop/.venv`: `.venv/bin/python scripts/deep_scan.py draft.md` gives Biber Dimension 1 (a durable register score), semantic redundancy (restatement, in chat and advice) and the least surprising sentences (cut candidates). Every flag, metric, reference value and the evidence for each tool is in `references/tools.md`. Treat the numbers as prompts to look closer, not as a grade.

### 3. Revise, outermost layer first

Work top-down. Fixing the paragraph structure often clears up the sentence-level problems too.

1. **Content** (deep only). Cut preambles ("Great question", "In today's fast-paced world"), recap paragraphs ("In summary..."), throat-clearing, restated questions, and closing offers ("Let me know if..."). Replace abstract claims with the specific fact, number, name or example the text already contains, or flag one as missing. Cut "balanced" caveats nobody needs.
2. **Structure**. Break up uniform paragraphs. Don't make every list three items long. Don't bullet what should be prose, and don't bold every other phrase. Use headings only where the genre uses them. Don't end every section with a takeaway line.
3. **Sentence grammar.** This is the strongest evidence-backed layer:
   - Turn **present participial tails** (", highlighting...", ", ensuring...", ", leaving...") into finite clauses or separate sentences, or delete them. They run at 2–5× the human rate.
   - Turn **nominalizations** back into verbs with real agents: "the implementation of caching led to a reduction in latency" becomes "caching cut latency". They run at 1.5–2× the human rate.
   - Rewrite **"that"-clauses as subject** and **"It is X that..."** frames.
   - Break up **phrasal coordination stacks** ("X, Y, and Z" noun lists in every sentence).
   - Write **clausal links** a human would use: *because*, *but*, *so*, *if*, *when*, *although*. Avoid stacking *Additionally / Moreover / Furthermore*. LLM text uses fewer causal and contrastive conjunctions, and uses the ones it has more repetitively.
   - Vary **word order**: front an adverbial now and then, ask a question, write a fragment where the genre allows it. Don't put every sentence in canonical subject-verb-object order.
4. **Rhythm**. Human prose has more length variation than LLM prose. The main difference is a long right tail: occasional long, well-built sentences (skew 1.1 vs 0.2–0.45). Get variation by letting some sentences run long, not by inserting short ones. **A short sentence has to carry its own new content**: an event, a fact, a number, a name ("The deploy failed at 3am."). Never write a short sentence that only echoes or judges the previous one:
   - stranded-auxiliary ellipsis: "Most POSTs aren't." "A rising one isn't."
   - gnomic maxims: "A new key protects nothing." "None of this fixes itself." "Tools matter less than people think."
   - bare-deictic verdicts: "Check your script for this." "That matters."

   These imitate variation without adding information, and in this repo's evals the pass itself wrote every one of them. Fold the content into the neighboring sentence instead ("…which isn't true of most POST endpoints"). `metric: echo_fragments`
5. **Lexicon**. Prefer the short word ("use" for "utilize"). Current models average 5.2–5.6 letters per word against 4.9 for humans. Call each thing by one name throughout. Cut intensifiers such as "incredibly" and "absolutely". Replace flagged words (see the list in `references/patterns.md`) with the **plainest accurate word**, or delete them. Write "look at" for "delve into", "use" for "leverage" and "shows" for "a testament to". Restore the involved-register words LLMs under-use where they fit: *I/we/you*, sensory and mental verbs (*see, hear, think, feel, guess*), modals of possibility (*might, could, would*), stance markers (*probably, I think, frankly*), contractions in informal genres.
6. **Punctuation and formatting**. Fix uniform comma-and-period punctuation. Use the parenthesis, semicolon, colon or question mark where it is the natural choice. Keep em dashes rare (one per several paragraphs at most). Use straight or curly quotes consistently. Don't put emoji in headings.

### 4. Guard against overcorrection

A de-slopped text that is uniformly casual, uniformly short, or littered with forced "I" and contractions is just slop in another register. Check that:

- Formal genres stay formal: remove the *generic* density there, not *all* density.
- Edits are uneven across the text. Humans aren't consistent, so don't apply every rule to every sentence.
- Long reference answers keep their navigation. In the A/B, the blind judge preferred the version that kept scannable lists and labeled sections for long answers (4–2), even though the other version sounded more human. Dissolve lists in short chat replies, not in an overview someone will scan.
- Length matches the ask. Current Claude answers run about 2× a human's for the same question, and in the A/B neither reviser shortened them. If `request_fit` shows the reply far above the human median for its kind of question, cut whole points, not just words.
- Turning bullets into prose hasn't produced "X, Y, and Z" lists in every sentence. That was the most common regression in the evals (`evals/`). Keep a bullet list when the items really are separate, or rank and relate the items instead of listing them.
- You haven't stripped every question mark and parenthesis. Humans use more of both than current models do (Graphite: parentheses 7.7 vs ≤0.9 per 1k). In this repo's evals, the pass removed all questions from all eight replies.
- You haven't fixed repetition by cycling synonyms. Current models already vary wording *more* than humans (MTLD 127–154 vs 85.6). Call one thing by one name.
- Rhythm hasn't gone flat, and it hasn't been faked. Cutting words tends to leave uniform 12–18-word sentences, and the obvious fix (adding punchy short ones) yields echo fragments. Re-check `sentence_shape` and `echo_fragments`: the target is `echo_fragments = 0` and some long sentences, not a high CV.
- You haven't added new pet words, like "honestly", "here's the thing" or "look,", which are already second-generation slop.
- Meaning is preserved. `--before` runs the facts check; read its warnings too, since a dropped negation can flip a claim.

### 5. Re-scan, check facts, report

```bash
python3 scripts/slop_scan.py revised.md --before draft.md --self claude --genre chat
```

This lists what you fixed, what's still flagged, what's **newly** flagged, which tells of your family the revision *added*, and a facts check: dropped numbers, code and links are errors, and dropped names, negations and hedges are warnings (`scripts/check_invariants.py draft.md revised.md` runs the facts check alone). Fix the new problems and run it again, at most twice. Watch for substitution: when the A/B revisers removed their own tells, participial tails rose (3.6 → 5.4 per 100 sentences), so check `--durable` after fixing `--self` hits.

Report briefly:

- what changed by layer (e.g. "cut 2 recap paragraphs; 9 participial tails → finite clauses; 6 own-family tells removed"),
- anything flagged but left alone on purpose (genre-appropriate),
- any `[example needed]` markers the author should fill in, and any fact the check flagged that you removed on purpose.

Return the revised text in full unless the user asked for a diff or suggestions only.

## When you are the author

If you are drafting something the user will ship under their name, apply step 3 while drafting: write the specific claim first, use verbs over nouns, vary length, and don't recap. It's cheaper than cleaning up afterward.

## Principles

- **Prefer checks that age well.** `--durable` runs only checks whose direction held for every model in both Graphite (web articles, 9 models) and ELEPHANT (advice replies, 9 models from 7 vendors): word length, participial tails, importance flags, tradeoff dodges, triads, the model fingerprint and length relative to the request (`--prompt`). Lexical diversity holds for frontier closed models only. Word lists, punctuation, formatting and sentence-shape tells depend on the model or the genre. Genre devices (questions, recaps, enumeration, ellipsis in conversation) aren't slop by frequency, so judge them against the request.
- **Trust the validated metrics most.** The full evidence, by corpus and by model, is in `references/research.md`. Some tells belong to one model family: intensifiers to Gemini, echo fragments to Claude, tradeoff dodges to GPT. Classic phrases like "it's important to note" now mostly catch older models and human SEO prose.

- **Register over vocabulary.** Word lists change between models and over time ("delve" has already dropped as models were retuned). The grammatical and rhetorical profile is more stable, and it's what experts notice.
- **Variation is the target.** No single feature value is "human". Human text is spread across a range, while LLM text is confined to a narrow band. Aim for the range the genre allows.
- **Specificity beats style.** The fastest way to make text read as human is to make it say something particular, so name the thing. Cut any sentence that could appear in a thousand other documents.
- **Don't fabricate humanity.** Adding fake experience, fake opinions or fake typos is deception, not editing.
