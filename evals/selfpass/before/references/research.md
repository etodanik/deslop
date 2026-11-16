# Evidence base

What the research says about how LLM text differs from human text, and how much to trust each finding. Each finding notes its **strength**:

- **strong**: replicated across several studies or very large effects
- **moderate**: one large study, or several smaller ones that agree
- **weak / contested**: studies disagree or the finding depends on the model

Caveat for everything here: most studies use English and GPT-3.5/4/4o or Llama 3. Fingerprints differ by model family (Reinhart et al.; Paech et al.), and word-level tells drift as vendors retune. Grammatical and rhetorical findings have been more stable than lexical ones.

---

## Primary sources

### Reinhart et al. (2025). "Do LLMs write like humans? Variation in grammatical and rhetorical styles." arXiv:2410.16107 (PNAS)

Design: parallel corpora (HAP-E, n≈8.3k texts; CAP from COCA, n≈9.6k). Each LLM got 500 words of human text and was asked to continue it *in the same style, tone, and diction*. The comparison used Biber's 66 lexico-grammatical features. Models: GPT-4o, GPT-4o Mini, and Llama 3 8B/70B in base and Instruct versions.

Findings:

- **Present participial clauses**: GPT-4o uses them at **5.3×** the human rate (Cohen's d = 1.38); instruction-tuned models overall at 2–5×. Example: *"Bryan, leaning on his agility, dances around the ring, evading Show's heavy blows."* — strong
- **Nominalizations**: 1.5–2×; GPT-4o 2.1× (d = 1.23). Example: *"...reduce deforestation, habitat destruction, and pollution, while also promoting sustainable consumption patterns."* — strong
- **"That"-clauses as subject**: 2.6× (d = 0.77). — moderate
- **Phrasal coordination**: 1.9× (d = 0.81). — moderate
- **Agentless passive**: GPT-4o uses it at about **half** the human rate. LLM prose is not "passive-heavy". — moderate
- **Model-specific features**: GPT-4o avoids clausal coordination and overuses downtoners (*barely, nearly*). Llama 3 does the reverse on both. — moderate, model-dependent
- **Vocabulary**: GPT-4o/4o-mini overuse *camaraderie, tapestry, palpable, intricate* at >100× the human rate, and *underscore, unspoken, amidst, solace, fleeting, unravel, grapple, ignite, vibrant, cacophony* at 80–130×. "Tapestry" appeared in 23% of GPT-4o outputs and "amidst" in 27%. Llama Instruct overuses *unease, palpable, pang, reminder, prioritize, grapple, waft, camaraderie, policymaker*. LLMs use obscenities more than 100× *less* often than humans. — strong for these models
- **Instruction tuning causes it.** Llama base models match human feature rates closely. Instruct versions diverge sharply and pick up GPT-4o-like traits. Larger models don't match human style better than smaller ones. — strong
- **Genre misalignment.** Even when told to match the sample's style, tuned models drift back to an "informationally dense, noun-heavy" style. Words that are normal in fiction show up in news, academic writing and scripts, where experts read them as "overwritten, sentimental, or simply uneven". GPT-4o's favorites mostly signal complex relations (*tapestry, intricate, amidst*) and go with positive terms (*vibrant, solace*), producing "grandiose, if hollow, summative sentences". — strong
- **Detectability.** Biber features alone distinguish human text from a given LLM with 93–98% accuracy. Misclassification happens mostly between sizes of the same model, rarely between human and LLM.

Practical implication: the biggest, most stable levers are **participial clauses, nominalizations, subject that-clauses, phrasal coordination and genre-inappropriate vocabulary**. Asking for a style in the prompt doesn't fix them, so an explicit revision pass is needed.

### Terčon & Dobrovoljc (2025). "Linguistic Characteristics of AI-Generated Text: A Survey." (44 studies)

**Lexicon**
- **Lower lexical diversity** and smaller vocabulary. Nearly every study agrees (André 2023; Guo 2023; Liu 2023; Muñoz-Ortiz 2024; Herbold 2023...). Two dissent. Function-word diversity is especially low. — strong (but GPT-4 beat humans on diversity in Herbold, so it depends on the model)
- **More repetition** of words, expressions and emoticons (Simon 2023; Yanagita 2024; Arcenal 2024). — strong
- **More frequent higher-order n-grams (n ≥ 3)** and **repeated part-of-speech sequences** (André 2023; Merrill 2024; Shaib 2024). — strong
- **Fewer idioms** (Simon 2023). — moderate
- **Vague group references overused**: *others, researchers*. Rare-but-stock expressions too: *stand out feature, incredibly polite, knowledgeable*. — moderate
- **Under-used in AI text**: the verb *say*; feeling words (*feels like, hate*); **sensing verbs** (*read, look, hear*); the conjunctions *however, but, although, because, if, that, or, when, as*; the pronouns *I, my, this, they, it, us*; the modals *will, would, might, could*; the particles *up, out, off*. Rude or aggressive expressions are absent. — moderate (Desaire 2023; Kim & Desaire 2024; Fujiwara 2024; Wan 2024)
- **Over-used**: modal *can*, *and*, the prepositions *by, with, for*, the pronoun *their*. — moderate
- **Punctuation**: less varied, dominated by commas and periods. Fewer question marks, dashes, parentheses, semicolons and colons; more periods and single quotes (Simon 2023; Desaire 2023). — moderate, **model-dependent**. This is GPT-3.5-era data. Later chat models are widely observed to overuse em dashes (see practitioner sources).
- **Longer words**: contested. LLMs **don't shorten words in predictable contexts** the way humans do (Cai et al. 2023), which is a psycholinguistic efficiency effect they lack.

**Grammar**
- **More nouns, determiners, adpositions and coordinating conjunctions; fewer adverbs and adjectives** (Chong 2023; Guo 2023; Liao 2023). — strong. This is the core "formal, impersonal" signature.
- **More nominalization** (Herbold 2023; Reinhart 2024). — strong
- **Fewer proper nouns** (Chong 2023; Desaire 2023; Petukhova 2024). **Fewer first-person pronouns** (Mitrović 2023). — moderate
- **Greater syntactic complexity** by dependency distance or tree depth (4 of 5 studies). — moderate
- **Less sentence-length variation** (Zindela 2023; Desaire 2023). Mean length is contested. — moderate
- **Canonical SVO order** in English and Spanish, with much less constituent-order variation than humans (Simon 2023). — moderate
- **Fewer, more repetitive discourse markers**. **Fewer modal and epistemic stance markers** (Herbold 2023; Simon 2023). — moderate
- **Fewer comparatives and superlatives**. Lower readability scores. — weak
- **More phrasal coordination, present participial clauses and subject that-clauses** (Reinhart 2024). **Heavy reliance on cohesive devices and formulaic constructions** (Wu 2025). — moderate–strong

**Discourse and style**
- **More formal, analytic and impersonal; less narrative and involved.** Focused on information rather than involvement (Sardinha 2024; Goulart 2024; Markowitz 2023). — strong. In Biber's terms, LLM text sits at the *informational* end of Dimension 1 whatever the genre.
- **More abstract** content (Casal & Kessler 2023; Liao 2023). Depends on genre (Sardinha 2024). — moderate
- **More neutral sentiment**; fewer negative emotions like fear and anger. — strong for neutrality, contested for emotional intensity (hotel reviews ran *more* emotional).
- **Fewer personal references, URLs, @-mentions and dates** (Chong 2023; Goulart 2024). — moderate
- What human judges used to spot AI text: ease of reading, whether the tone felt personal, and phrases that seemed *too* well constructed (Casal & Kessler 2023).
- **Genre-specific** (Sardinha 2024): AI academic text lacks narrative and explicit references and is *more* persuasive. AI essays are info-dense, less involved and *less* persuasive. AI conversation is less involved, less narrative and more abstract.

**Prompting**
- When the LLM **rephrases existing human text** instead of generating from a title, detectors perform much worse (Kim & Desaire 2024; Mindner 2023). Anchoring on a human sample pulls style toward human norms. → This is the reason the skill uses a voice anchor.

### Clark, Martin & Mahowald (2026). "Why is AI-generated language so hard to understand?" arXiv:2610.29162

The other two sources ask how AI text is *recognized*. This one asks why it is *hard to read*. It measures features that psycholinguistics links to **comprehension difficulty**, over 14 models (Claude Sonnet 5 / Opus 5 / Opus 5.5 / Fable 5, GPT-5.6 Luna/Terra/Sol, Kimi K2.5, GLM 5, Olmo 3 Base/Instruct/Think, Llama 3.1 Base/Instruct). Three settings: multi-turn **chat** (vs. OpenSubtitles), multi-turn **coding agent** sessions (vs. StackExchange), and **essays** (vs. top-scored PERSUADE 2.0 student essays). The key control is a **round-trip translation** (EN→JA→EN, NLLB-200). It yields a paraphrase with the same meaning, so if a feature drops after the round trip, the model *chose* it over an available simpler wording.

Features, with the processing literature behind each:

| Feature | Example | Why it's hard (cited work) |
|---|---|---|
| **Unattested bigrams / high n-gram perplexity**: word pairs that never occur in human reference text | "eating its own **reader-patience budget**" | Low-predictability words cost reading time (Levy 2008; Smith & Levy 2013) |
| **Long dependencies** | heads far from dependents | Memory cost of integration (Gibson 1998/2000; Grodner & Gibson 2005; Futrell et al. 2015) |
| **Object relative clauses, esp. reduced** (no *that/which*) | "activities **they care about**" | ORCs are harder than subject relatives, and dropping the relativizer removes a parsing cue (Staub 2010; Mak et al. 2006; Reali & Christiansen 2007) |
| **Stacked noun compounds** (3+ nouns) | "Squad Helps Dog Bite Victim" | Bracketing ambiguity (Lauer 1995; Staub et al. 2007; Cohen & Staub 2014) |
| **Denominal verbs** (noun used as verb) | "Prevented Git dry runs from installing hooks or **staging** changes"; "**calendar** it" | Novel conversions need extra interpretation (Clark & Clark 1979; Thierry et al. 2008) |
| **Inanimate subject + animate verb** (personification) | "`is_file()` **swallows** that and returns False"; "where this asymmetry **bites**"; "A song doesn't **ask** you to..." | Selectional-restriction violations cost processing (Trueswell et al. 1994; Kim & Osterhout 2005; Kuperberg 2007) |

Findings:

- All nine frontier and near-frontier models use **more inanimate-subject + animate-verb constructions and more low-frequency n-grams** than human text. Most also use **longer dependencies, more stacked nouns and more reduced ORCs** in conversation. — strong (new, single study, but large and well controlled)
- The round trip *lowers* unattested bigrams, trigram perplexity, denominal verbs, inanimate subjects and reduced ORCs for nearly all frontier models in all three settings. These are **choices**, not side effects of content. Models **under-use ORCs *with* the relativizer**: they drop optional function words. — strong
- Dependency length and stacked nouns show up mainly in chat and **coding**, less in essays. Effects are smallest in single-prompt essays. The authors suggest that long **multi-turn sessions build up a compressed private jargon**. — moderate
- Base models (Llama, Olmo Base/Instruct) are closest to humans. Olmo effects grow from Base to Instruct to **Think**. **Reasoning/RL post-training increases difficulty.** — moderate
- Proof of concept (Qwen2.5-1.5B, GRPO): adding a **length penalty** to verifiable-reward RL drives a near-categorical (>98%) preference for the shorter variant of optional alternations (dropping "that", etc.). This transfers to untrained constructions. Humans choose such variants by context, and RL turns the choice into a fixed rule. → **The compression comes from rewards for brevity and density.**
- Opus 5.5 scores lower than Opus 5 on 19 of 21 difficulty measures. Training can reduce these features.

**This is a second slop profile.** The Reinhart/Terčon profile is *bloated*: participial tails, nominalizations, puffery, recap paragraphs. The Clark profile is *over-compressed*: dropped relativizers and complementizers, noun stacks, nouns verbed into jargon, code and abstractions personified as agents, coined collocations, and long-range dependencies. It is most common in agentic and coding transcripts, status updates, commit messages and long chat threads. A de-slop pass must handle both, and fixing one must not create the other. Note the tension with Biber's Dimension 1: *that*-deletion is a normal **involved-register** feature in casual human speech. So don't restore every "that". Restore it where the clause is long, the subject is a full noun phrase, or the sentence could be misparsed.

### Druck, Paredes & Smith (Graphite, Sept 2026). "AI Tells." graphite.io/research/ai-tells

This is the largest matched comparison here and the most current. It used 10,000 pre-ChatGPT Common Crawl web articles. Each was summarized, and nine models (GPT-4.1, GPT-5, GPT-5.6 Sol, GPT-6 Astra, Claude Opus 4/4.6/5, Gemini 2.5 Pro/3.1 Pro) wrote an article on the same topic at a matched word count: 9,984 topics × 10 texts. A *tell* is a unigram, bigram, trigram or frame (a template of up to 7 tokens with blanks, built on the 300 most common words) used at **≥2× the human rate** in enough documents (500/250/100/120 of 10k for uni/bi/tri/frame). Stylistic features are ranked by Cohen's d. Divergence is measured with Jensen–Shannon over word distributions.

Measurable findings:

| Feature | Finding | Scanner metric |
|---|---|---|
| **Word length** | AI 5.2–5.7 letters/word vs human **4.9** | `word_length` (warn > 5.2) |
| **Sentence-length SD** | lower in AI | `sentence_length` |
| **Exclamation marks** | humans use them **>100×** more than each current model | `human_markers.exclamations` |
| **Parentheticals** | humans use far more | `human_markers.parentheticals`, `punctuation.paren_per_1k` |
| **Em dashes** | **now model-dependent and partly inverted**: GPT-6 Astra ≈ ⅛ of the human rate, Gemini 3.1 Pro nearly zero, Opus 5 ≈ human. Authors suspect GPT and Gemini overcorrected. | `punctuation.em_dash_per_1k` |
| **Lexical diversity (MTLD)** | **higher** in AI than human. This reverses the older finding. | `lexical_diversity.mtld` (no flag) |
| **Contractions, 2nd person** | humans use far more. Gemini contractions nearly gone. | `contractions`, `pronouns` |
| **Definition by contrast** | "not simply" 157×, "rather than relying" 187×, "rather than merely" 160×, "the _ is not simply" 576×, "less like a _ and more like" 105×, "is not just a _ it is" 153×. Corrective framing in Astra ≈12× human and still rising. Claude "less X, more Y" ≈82×. | `contrast_frames` |
| **Avoiding tradeoffs** | "without requiring" 70×, "without losing" 5–22×, "without sacrificing" 4–8×, "without compromising" 2.6–5× | `tradeoff_dodges` |
| **Flagging importance** | "matters because" 132–357×, "distinction matters" ∞ (absent in human text), "matters more than" 93×, "absolutely essential" 32× | `importance_flags` |
| **Transitions** | "another dimension" 117×, "together these" 95×, "ultimately this" 78×, "furthermore the" 43×, "looking ahead the" 33×, "what comes next" 28× | `stock_phrases.transitions_2026` |
| **Evaluative words** | "dependable" 59×, "practical" 26×, "deliberate" 26×, "profound" 25×, "immense" 22×, "incredibly" 18×, "meaningful" 13× | `flagged_vocab.evaluative_2026` |
| **Intensifiers** | Gemini ≈13× human ("absolutely", "entirely", "highly", "incredibly"). Opus 5 "every single" 112×, "enormously" 45× vs Astra | `intensifiers` |
| **Hedges** | Astra "may provide" 36×, "can provide" 23×, "not necessarily" 18× vs Opus 5. "may" 3× GPT-4.1 | `stance.generic_hedges` |
| **Mannered prose** | LLM-judged 0–100. Opus 5 and Gemini 3.1 Pro ≈2.5× human, Astra ≈1.2×. Opus 5 +19% over Opus 4. Example: "a dial worth turning" for "a parameter worth varying". | `mannered_frames` (regex proxy only) |
| **Human-only tells** | "we all know", "you can't", "did you know", "pretty", "sort of", "he said", "years ago", "my favorite", "mom", "last year", "love to", "excited to" | `human_markers` |
| **Word-distribution divergence** | every model is closer to another model than to humans. Only Claude's divergence from human is falling over versions. | `js_divergence` (with `--baseline`) |

**Released feature data** (`references/data/graphite_ai_tells_features.csv`, CC BY 4.0) gives per-article means and Cohen's d for 90 features. The strongest effects for the current models (Opus 5 / Astra / Gemini 3.1 vs human), which `slop_scan.py` shows as reference values:

| Feature | Human | Opus 5 | Astra | Gemini 3.1 | d range |
|---|---|---|---|---|---|
| mean word length (letters) | 4.90 | 5.20 | 5.63 | 5.35 | +0.66 to +1.56 |
| word-length skew | 0.83 | 0.67 | 0.49 | 0.60 | −0.57 to −1.23 |
| MTLD | 85.6 | 150.3 | 153.6 | 127.1 | +1.04 to +1.41 |
| sentence-length skew | 1.10 | 0.45 | 0.39 | 0.24 | −0.72 to −0.99 |
| longest sentence (words) | 73.6 | 40.2 | 32.0 | 34.3 | −0.41 to −0.51 |
| sentence-length SD | 17.0 | 8.4 | 5.8 | 6.8 | −0.29 to −0.38 |
| content-word over-use | 0.078 | 0.043 | 0.071 | 0.042 | −0.14 to −0.76 |
| concessive frames /1k | 0.04 | 0.14 | 0.48 | 0.43 | +0.25 to +0.68 |
| last paragraph mirrors first | 0.12 | 0.20 | 0.32 | 0.25 | +0.23 to +0.49 |
| hallmark words (delve, tapestry…) /1k | 0.44 | 0.44 | 0.31 | 2.05 | −0.12 to +0.83 |

Rate features with small d but large ratios: parentheses 7.7 vs 0.04–0.9 per 1k; exclamations 2.8 vs ≈0.02; year references 5.9 vs 1.0–1.4; percentages 0.40 vs 0.05–0.22. Their d values are small because these features are rare and lumpy across articles.

**Released tell data** (`references/data/graphite_ai_tells_tells_vs_human.csv.gz`, 67,520 term × model rows, CC BY 4.0) is distilled into per-model lists in `graphite_tells_lexicon.json`: the top 250 terms at ≥4× the human rate in ≥3% of articles. The lists separate cleanly by expected hit rate. For Opus 5: model text 43.2 per 1k tokens vs human text 5.3. Astra: 81.3 vs 9.2. Gemini 3.1: 64.3 vs 8.8. Top current tells:
- **Opus 5:** "rather than" 20×, "genuinely" 68×, "genuine" 30×, "matters" 15×, "practical" 15×, "quietly" 33×, "a genuine" 82×, "is straightforward" 136×
- **Astra:** "not simply" 157×, "practical" 26×, "broader" 31×, "a practical" 64×, "useful" 17×, "rather than treating" (absent in human text)
- **Gemini 3.1:** "highly" 16×, "incredibly" 18×, "massive" 19×, "furthermore" 25×, "whether you are" 35×, "navigating" 26×, "crucial" 9×
- **Human-favored vs all three:** contractions (it's, don't, that's, you're: 50 to 2,000× and up), I/we/our/my, "said", "a lot", "really", "please"

Validation in this repo: on the eight unedited Claude Sonnet replies in `evals/before/`, `model_fingerprint` names Claude Opus 5 as the closest model in 6 of 8 (the others: Opus 4.6 and GPT-5). The hand-written caricatures land on older models (bloated essay → GPT-4.1, fiction → Gemini 2.5 Pro). The fingerprint also caught the reviser's own tells. A Claude rewrite introduced "close that gap" (85× for Opus 5).

What this changes:
- **The classic word list is nearly dead for GPT and Claude.** Hallmark vocabulary shows d ≈ 0 for Opus 5 and is below the human rate for Astra. Only Gemini still over-uses it ("crucial" d = +1.0). The strong current signals are distributional: word length, MTLD, sentence-length shape.
- **High diversity is now the tell, not low.** Models avoid repeating content words. See patterns.md §6.2.
- **Web-article genre.** In this repo's chat evals, Sonnet used *more* parentheses than the human web baseline. Treat these as references for prose articles, not universal norms.

Findings that shape how the skill works:

- **Tells drift fast.** 12,877 unique tells; 65% are unique to one model family; 55–72% differ between the two latest versions of a family. Well-known tells fell 21–50% in strength across versions, and marketing words dropped 73% in Astra vs GPT-4.1. But new tells replaced them: corrective framing rose, "may" tripled, and Claude's concrete-number phrases ("twenty minutes", "a dozen") rose. → Fixed word lists go stale, so measure the model you're editing (`mine_tells.py`). Also note that **suppressing one tell creates another**. That is the same overcorrection risk this skill warns about.
- **Absence is not humanness.** A text with zero em dashes, no hype words and high MTLD can still be fully machine-styled. Opus-5-era "specificity" can be decorative too.
- Caveats from the authors: web-article genre only (may not transfer to chat), a single prompt, a pre-2022 human baseline, an LLM judge for mannered prose, and the advice not to use individual tells for authorship decisions.

### Validation of this repo's metrics on Graphite's matched articles

`evals/validate_graphite.py` runs the scanner on 1,000 random topics from Graphite's article file. Each topic has the human article plus the versions from Opus 5, Astra, Gemini 3.1, GPT-4.1 and Opus 4. Only aggregates are kept (`evals/graphite_validation.json`); the article text is third-party and is not stored. Values are hits per 1k words, with the share of articles that have at least one hit in parentheses:

| Metric | Human | Opus 5 | Astra | Gemini 3.1 | Verdict |
|---|---|---|---|---|---|
| importance_flags | 0.01 (1%) | 0.27 (23%) | 0.31 (24%) | 0.11 (7%) | **strong, all families** |
| mannered_frames | 0.00 | 0.08 (8%) | 0.02 | 0.01 | strong but rare; mostly Claude |
| tradeoff_dodges | 0.04 (3%) | 0.11 (9%) | 0.36 (25%) | 0.17 (10%) | strong, esp. GPT |
| intensifiers | 0.61 (33%) | 1.56 | 0.38 | 5.55 (90%) | **Gemini-specific** (9×) |
| contrast_frames | 0.21 (13%) | 0.50 | 0.91 (50%) | 0.51 | strong (2.4–4.3×) |
| participial_clauses | 2.69 | 5.42 | 6.56 | 7.30 | strong, all (2.0–2.7×), confirms Reinhart |
| triads | 6.96 | 12.55 | 14.11 | 8.15 | moderate (1.2–2×) |
| echo_fragments | 0.15 (10%) | 0.39 (26%) | 0.08 | 0.05 | **Claude-specific** (2.6×); GPT/Gemini *below* human |
| inanimate_agents | 0.34 | 0.66 | 0.46 | 0.58 | moderate (1.4–1.9×) |
| denominal_verbs | 0.07 | 0.16 | 0.13 | 0.12 | moderate (~2×) |
| count_fragments | 0.57 (20%) | 0.71 | 0.47 | 0.27 | **weak in web prose**; human hits are page scraps (addresses, "2,499 likes") |
| concessive_frames | 0.37 | 0.09 | 0.20 | 1.09 | **mismatch**: our regex isn't Graphite's frame; only Gemini is over |
| that_subjects | 0.10 | 0.04 | 0.00 | 0.11 | **not a current tell** (human SEO text says "it's important to note") |
| meta_reference, stock_phrases | 0.08 / 0.47 | 0.06 / 0.22 | 0.00 / 0.46 | 0.12 / 1.59 | not current tells except Gemini; older models (GPT-4.1) higher |

Lessons:
- **Much "classic slop" was human SEO prose first.** Pre-2022 web text already contains "it's important to note", "when it comes to", "let's take a closer look", "serves as a". Current GPT and Claude have moved *past* those phrases, and GPT-4.1 and Opus 4 still use them. Those metrics now mostly catch older models and SEO-style human writing.
- **Several tells are family-specific.** Intensifiers point to Gemini. Echo fragments and mannered frames point to Claude. Tradeoff dodges and contrast frames lean GPT. A pass run by a Claude model should watch Claude's own list (see `model_fingerprint`).
- **Human text trips every detector sometimes.** Echo fragments appear in 10% of human articles ("It's that easy.", "Yes, you absolutely could."). A single hit is weak evidence, so the flag now needs two or more.
- Genre caveat: these are web articles. Chat, code and fiction will differ.

### Which checks age well: sign stability across model generations

A check *ages well* if every model generation differs from humans in the same direction. Graphite's features cover nine models from three vendors (GPT-4.1 → GPT-6 Astra, Opus 4 → 5, Gemini 2.5 → 3.1). This repo's validation adds five corpora.

**Same sign for every model** (smallest |d| among the nine in parentheses): MTLD/TTR higher (0.72 / 0.44); mean word length higher (0.52); word-length skew lower, i.e. fewer short words (0.50); syllables per word higher (0.47); longest sentence shorter (0.38); sentence-length SD lower (0.29) and skew lower (0.25); ending mirrors the opening (0.23); concessive frames more (0.22–0.30); hedge stacking higher (0.22); exclamations fewer (0.27). From this repo's regexes (all five corpora ≥1.2× human): participial tails (2.0–3.5×), importance flags (9–31×), contrast frames (2.4–8×), tradeoff dodges (2.5–15×), triads (1.2–2.1×), denominal verbs (~1.6×).

**Flips between models or versions** (don't age well): em dashes; Graphite's antithesis frame; hallmark words (delve, tapestry, foster); hopeful-future closers; list use; sycophantic phrases; and from this repo, echo fragments (Opus 5 only), intensifiers (Gemini only), stock phrases and "it is important that" (current models are *below* human SEO prose).

Why the split: durable features are properties of the instruction-tuned *register*. Instruction tuning makes models informationally dense and clause-compressed (Reinhart: base models match humans, tuned models diverge), so those features persist across vendors and versions. Decaying features are individual *tokens and conventions* that vendors can see and suppress directly. Once a tell is publicized it gets trained out, often overcorrected (Astra's em dashes fell to ⅛ of the human rate), and a new token replaces it.

**Frequency isn't appropriateness.** Several popular tells (self-answered questions, enumeration, signposting, recaps) are *more* common in human web text than in current model text (self-answered questions: human 0.47 vs ≤0.15 per 1k). They are genre devices, fine in an FAQ and wrong in a chat reply. Checks like these must be relative to the context (the genre baseline, or the request itself: is the answer first, and is the length proportional to the ask?) and not to pooled human text. Grice's maxims are the right frame: Quantity (dilution, recap, belaboring), Relation (preamble, reasoning leak, unrequested work), Manner (invented labels, forced figures), Quality (vague attribution, inflated stakes). Each is a judgment relative to what was asked, so frequency counts can't capture it.

`slop_scan.py --durable` runs only the sign-stable checks.

### Request-relative checks on HC3 (prompt + human reply + model reply)

HC3 (Guo et al. 2023; `sources/raw/hc3_all.jsonl`, CC BY-SA) has 24,322 real questions (Reddit ELI5, open QA, finance, medicine, CS) with human answers and ChatGPT-3.5 answers to the same question. `evals/validate_hc3.py` scores the `request_fit` checks on all of them, and on a 40-question sample also answered by current Claude (Sonnet, default style):

| Check | Human | ChatGPT-3.5 (2023) | Claude (current), 40-q sample | Durable? |
|---|---|---|---|---|
| first sentence restates the question | 0.02–0.04 | 0.12–0.17 (3–7×) | 0.025 | **no**: trained out |
| closing recap repeats question/opening | ≤0.005 | 0.02–0.05 (3–10×) | 0 | **no**: trained out |
| reply length (words), same questions | 142 | 183 | 294 | **yes, and growing**: about 2× human now |
| direct first sentence (yes/no questions) | 0.14 | 0.26 | 0.5 | inverted: humans open with context |
| participial tails /1k | 2.0–2.4 | 1.1–2.6 | 2.7 | started after GPT-3.5 |
| echo fragments /1k | 0.52 (Reddit casual) | 0.0 | 0.74 | Claude-specific; humans use them in casual answers |

What this shows about Grice. The Relation violations that had a recognizable form (restating the question, recapping it) were trained out between generations. The Quantity violation, saying more than the ask needs, grew. Length relative to the question is the request-relative signal that has aged worst, so it's the one to check. `request_fit` reports words and the length ratio with HC3's human medians (ELI5 98 words, open QA 39, finance 137, medicine 78).

### ELEPHANT: advice replies from humans and 12 models (Cheng et al., ICLR 2026; CC0)

ELEPHANT's open-ended questions (OEQ) are 3,027 personal-advice prompts answered by a crowdsourced human and by Claude, GPT-4o, GPT-5, Gemini, DeepSeek, Qwen, Llama-8B/17B/70B and Mistral-7B/24B, each labeled for validation, indirectness and framing sycophancy (`sources/raw/elephant/`; `evals/validate_elephant.py`; aggregates in `evals/elephant_validation.json`). On 500 prompts:

| Check | Human | Models (range) | Verdict |
|---|---|---|---|
| reply words / length ratio | 101 / 1.2× | 157–585 / 2.0–7.4× | **durable, all 9** |
| mean word length | 4.25 | 4.74–5.40 | **durable, all 9** |
| participial tails /100 sentences | 3.1 | 3.5–8.2 | **durable, all 9** |
| importance flags, tradeoff dodges /1k | 0, 0 | 0.01–0.19 | **durable, all 9** |
| triads (share of sentences) | 0.044 | 0.065–0.162 | **durable, all 9** |
| model_fingerprint (Graphite-built) | 0.26 | 0.59–0.82 | **generalizes** to a new genre and to models not in Graphite |
| MTLD | 86.8 | 81–181 | frontier closed models only (Claude 159, GPT-5 181, DeepSeek 156; Qwen/Llama/Mistral ≈ human) |
| longest sentence | 29 | 27–44 | no gap here (the Graphite gap is genre-specific) |
| contrast frames /1k | 0.25 | 0.13–0.85 | not universal |
| echo fragments /1k | **1.28** | 0.08–0.36 | humans higher in conversational advice |
| restates the situation/question | 0.079 | 0.034–0.103 | not a model tell in advice |
| bold /1k | 0.17 | 0.02 (GPT-5) – 40.6 | strong except GPT-5 |
| ELEPHANT validation / indirectness / framing | 0.21 / 0.21 / 0.61 | 0.50–0.81 / 0.53–0.98 / 0.77–0.96 | sycophancy: not measured by this scanner |

The `DURABLE` set in `slop_scan.py` is now the checks that held in both Graphite and ELEPHANT: word length, participial tails, importance flags, tradeoff dodges, triads, model fingerprint and request-fit length, plus lexical diversity for frontier models. Echo fragments only flag in chat at ≥4.

### spaCy calibration of the Profile-B metrics on Graphite articles

On 150 topics with `--spacy`, every model has *shorter* dependencies than human web articles (mean dependency distance d −0.4 to −0.7; longest dependency per sentence d −0.2 to −1.1), *fewer* noun stacks (d −0.3 to −0.4) and *fewer* dropped relativizers (d −0.3 to −0.6). This is the opposite of Clark et al.'s chat and coding results, but it agrees with their observation that the effects shrink in essays. Human web text is also noisy here (navigation lists inflate noun stacks). Conclusion: the Profile-B structure metrics are genre-scoped to chat, code and agent output, and their flags are switched off for `--genre essay/academic/docs`. Inanimate agents are the exception, above human in every corpus (Opus 5 highest, d +0.42), as Clark found.

### Model-based tools (deep_scan) on Graphite and ELEPHANT

`evals/validate_deep.py`, 40 items per corpus, Cohen's d vs human (`evals/deep_validation.json`):

| Measure | Graphite (Opus 5 / Astra / Gemini 3.1) | ELEPHANT (Claude / GPT-5 / Gemini / Llama-70B) | Verdict |
|---|---|---|---|
| Biber D1 (involved − informational) | −0.03 / −0.81 / −0.85 | −1.08 / −1.08 / −1.07 / −0.71 | **durable**: models less involved in 7 of 8 |
| GPT-2 mean surprisal (bits) | +1.03 / +1.04 / −0.03 | +0.47 / +1.28 / −1.57 / −3.54 | flips by model; the "low perplexity" tell no longer holds |
| sentence-surprisal spread | −0.41 / −0.29 / −0.66 | −0.06 / +0.95 / +0.24 / −0.45 | not durable |
| mean similarity to nearest earlier sentence | −1.10 / −0.09 / −0.04 | +0.55 / +0.97 / +1.72 / +2.56 | genre-dependent: models more redundant in advice; human web pages repeat boilerplate |
| last paragraph vs first (tie-back) | (no paragraphs in scraped human text) | +0.16 / +0.01 / +1.61 / +0.88 | model-specific (Gemini, Llama) |

### Sycophancy judge agreement

ELEPHANT's three judge rubrics (CC0) were given to a fresh Claude judge, blind, on 40 OEQ replies (20 human, 20 GPT-4o). Against ELEPHANT's GPT-4o-judged labels: validation 90% agreement (κ 0.80); indirectness 95% (κ 0.90); framing 74% (κ 0.02). Use the first two and drop framing. Both reliable rubrics reproduce the human/model gap (validation 0.2 vs 0.8; indirectness 0.05 vs 1.0). `evals/judge/agreement.json`.

### A/B test of the agent aides

Six current-Claude HC3 answers (ELI5, open QA, finance, medicine, CS) were revised by two Sonnet subagents. Arm A had SKILL.md and the plain report. Arm B had the anchored `--agent` report, `--self claude`, `--prompt`, then `--before` regression and `check_invariants`, with up to two fix rounds. Results (`evals/ab/`):

| Measure (mean of 6) | Input | Arm A | Arm B |
|---|---|---|---|
| Claude-family tells | 6.2 | 6.2 | **1.5** (lower in all 6) |
| Opus 5 tell likeness | 0.34 | 0.47 | **−0.13** |
| durable flags | 1.5 | 1.5 | 1.2 |
| participial tails /100 sentences | 3.6 | 3.6 | **5.4** (substitution) |
| words | 312 | 294 | 290 |
| facts dropped (errors) | – | 0 | 0 |

Blind pairwise judge (fresh Sonnet, randomized order): more human-sounding B 3 – A 1 (2 ties); more information A 1 – B 0 (5 ties); would rather send A 4 – B 2. The judge preferred A's lists and labeled sections in long reference answers.

Verdict per aide:
- `--self`: **canonized**. Large, consistent effect on the reviser's own dialect, and judged more human.
- `--before` + `check_invariants`: kept as a safety net. Neither arm dropped a fact here. On the earlier rewrites it caught five real losses.
- `--agent`: kept as the default agent view for its token cost (about 450 vs 2,100 tokens). No quality effect shown on its own.
- `request_fit` length: neither arm shortened toward the human length even with the number in front of it. Kept as a measurement, and SKILL.md now tells the reviser to cut whole points when far over.
- New guidance from the losses: keep navigation (lists, labeled sections) in long reference answers, and recheck durable flags after removing own-family tells.

### Not directly measured: count-led verbless fragments

The "Two findings, one significant." pattern isn't a feature in any of the studies above, so treat its status as **inferred, not measured**. Three lines of evidence converge on it:

- **Grammar.** It's *block language* or headlinese (Quirk et al. 1985, *A Comprehensive Grammar of the English Language*, §11.41ff): verbless noun-phrase "sentences" with ellipsis of the copula. These are normal in headlines, labels, notes and slides, and marked in running prose. In Biber's terms it's extreme informational packaging: nouns and numerals, no verbs.
- **Compression pressure** (Clark, Martin & Mahowald 2026). RL with brevity or length rewards drives models to categorically drop optional words. A copula and subject ("There are two findings, and one of them is significant") are exactly the kind of material that gets dropped. Their effects are largest in multi-turn agentic and coding contexts, which is where this pattern clusters.
- **Rhetoric** (Wikipedia AI Cleanup; blader/humanizer #2, "dramatic fragments"). The numeral works as an advance organizer and the comma-tag gives an instant verdict. It reads as confident and scannable, which is the kind of feature preference raters may reward in summaries.

Why models over-use it is a plausible account, not established: post-training rewards answers that are short, scannable and lead with a verdict, and agent-summary data is full of status-report and slide genres. Together these make headlinese a cheap way to sound organized. A model's own account of why it writes something is not reliable evidence. Measure the pattern (`count_fragments`) rather than trusting introspection.

---

## Supporting work

- **Kobak et al. (2025), *Science Advances*. "Delving into LLM-assisted writing in biomedical publications through excess vocabulary."** Compared 15M PubMed abstracts against pre-LLM counterfactual frequencies. They estimate ≥13.5% of 2024 abstracts were LLM-processed. The excess words are overwhelmingly **style words** (verbs and adjectives such as *delves, showcasing, underscores, intricate, notable, pivotal, crucial, potential, comprehensive, meticulously*), not content nouns. Follow-ups report "delve" declined after it became a known tell, while words like "significant" kept rising. **Lexical tells drift.**
- **Liang et al. (2024), ICML. "Monitoring AI-modified content at scale."** AI-conference peer reviews showed sharp rises in *commendable, meticulous, intricate, innovative, notable, versatile*.
- **Paech, Roush, Goldfeder & Shwartz-Ziv (2025). "Antislop: A comprehensive framework for identifying and eliminating repetitive patterns in language models."** arXiv:2510.15061 (ICLR 2026). Builds per-model "slop fingerprints" of over-represented words and n-grams in creative writing against human baselines. Fingerprints cluster within model families. Some patterns are extreme (gemma-3: the name "Elara" is about 85,000× over-represented; some trigrams exceed 1,000×). Documents "it's not just X, it's Y" contrast frames. Suppressing banned strings at sampling time works without hurting benchmarks. **The same favored names, trigrams and contrast frames recur.**
- **Shaib et al. (2024). "Detection and measurement of syntactic templates in generated text."** LLMs reuse part-of-speech templates far more than humans, and most templates can be traced to the pre-training data. **Sentence shapes repeat even when the words change.**
- **Holtzman et al. (2020). "The curious case of neural text degeneration."** Human text is *not* the highest-probability text. Its per-token probability varies widely and includes many low-probability choices, while likelihood-maximizing text is bland and repetitive. → This is the information-theoretic basis for "burstiness".
- **Uniform Information Density (Jaeger & Levy 2007; Meister et al. 2020).** Humans spread information *roughly* evenly but locally, with variance. LLM text has lower surprisal variance and sentence-level "burstiness" than human text, which is the basis of perplexity/burstiness detectors (GPTZero; DetectGPT, Mitchell et al. 2023).
- **Markey, Brown, Laudenbach & Kohler (2024), *Written Communication*. "Dense and disconnected: Analyzing the sedimented style of ChatGPT-generated text at scale."** ChatGPT text is informationally dense and weakly connected, a "sedimented" style that persists across tasks.
- **Jiang & Hyland (2024), *Applied Linguistics*.** ChatGPT essays use more noun-based lexical bundles and fewer **stance and engagement bundles** than student essays (*I think, it is possible that, as we can see*).
- **Biber (1988), *Variation across Speech and Writing*.** Dimension 1, involved vs. informational production. The involved pole has private verbs (*think, feel*), *that*-deletion, contractions, present-tense verbs, 1st/2nd person pronouns, demonstratives, emphatics, hedges, discourse particles, causative subordination (*because*). The informational pole has nouns, long words, prepositions, attributive adjectives and high type/token ratio. LLM text sits at the informational pole regardless of genre.
- **Pennebaker / LIWC line of work.** Function words (pronouns, articles, conjunctions) carry most of the stylistic and psychological signal in authorship. Human authenticity correlates with more first-person singular, more exclusive words (*but, except, without*) and more cognitive-process words. This matches the survey's under-used function-word list.

## Practitioner sources (unreviewed, but heavily curated)

- **Wikipedia: "Signs of AI writing"** (WikiProject AI Cleanup). Field guide from editors cleaning up LLM text. Patterns: promotional or puffery language ("rich cultural heritage", "stands as a testament"), editorializing ("it's important to note"), section-ending summaries ("In summary..."), negative parallelism ("not only... but"; "it's not X, it's Y"), the rule of three, vague attributions ("experts say", "some critics argue"), "superficial analysis" participial tails ("..., highlighting its importance"), title-case headings, excessive bold, em dash overuse, curly quotes, emoji bullets, leftover chatbot phrasing ("I hope this helps", "Certainly!"), knowledge-cutoff disclaimers. Its own warning: these are *potential* signs, look for combinations, and detectors have high error rates.
- **Sycophancy and assistant framing** (well documented in RLHF literature, e.g. Sharma et al. 2023, "Towards understanding sycophancy in language models"). Openers that praise the question, mirrored agreement, closing offers of more help.

## Synthesis: the slop profile

| Dimension | LLM default | Human range (varies by genre) |
|---|---|---|
| Register | informational, impersonal, abstract | moves between involved and informational with context |
| Clause packaging | participial tails, nominalizations, subject that-clauses, phrasal lists | finite clauses, verbs with agents, clausal links |
| Connectives | *and*, *additionally*, *moreover*, repeated | *but, because, so, if, when, although*, varied |
| Stance | neutral, hedged in a uniform way, few epistemic markers | committed, opinionated, specific doubts |
| Person | few *I/we/you*, vague groups (*others, researchers, many*) | named people, first and second person |
| Rhythm | low sentence-length variance, SVO order | bursty, inverted orders, fragments, questions |
| Lexicon | small vocabulary, favored "complex relation" and positive words | larger vocabulary, plain words, idioms, occasional profanity in informal genres |
| Repetition | recurrent n-grams and POS templates, recurring contrast frames and triads | avoids repetition without noticing |
| Punctuation | commas and periods (older models) or em-dash heavy (newer) | full range, varied by person |
| Discourse | intro restating the question, recap ending, "balanced" caveat | starts in the middle, stops when done |
