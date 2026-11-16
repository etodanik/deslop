# Pattern catalog

Each entry gives the pattern, why it matters, the scanner metric that measures it (`metric: name`), and the rewrite move. There are two slop profiles. Diagnose which one you're facing before rewriting:

- **Profile A, bloated/informational** (Reinhart; Terčon & Dobrovoljc; Kobak). Typical of essays, articles, marketing, summaries and "explain X" answers.
- **Profile B, over-compressed/jargon** (Clark, Martin & Mahowald). Typical of coding-agent output, status updates, PR descriptions, commit messages and long chat threads.

A single text can show both. Fixing A by cutting words can push it into B. Fixing B by spelling things out can push it into A. Aim for plain, finite clauses with real agents.

---

## 1. Content and discourse (read for these; the scanner only partly sees them)

**1.1 Preamble and restated question.** Example: "Great question! Understanding X is crucial in today's..." / "In the ever-evolving landscape of..."
*Move:* delete it and start with the answer. `metric: stock_phrases`

**1.2 Recap ending.** Examples: "In summary,", "Overall,", "Ultimately,", "In conclusion,", a final paragraph that restates the body, or a section-ending moral ("This highlights the importance of...").
*Move:* delete it. Keep a conclusion only if the genre needs one, and then make it add something: a decision, a next step, an implication not yet stated. `metric: stock_phrases`

**1.3 Assistant framing and sycophancy.** Examples: "Certainly!", "I hope this helps", "Let me know if you'd like...", "You're absolutely right", "Here's a breakdown:".
*Move:* delete. `metric: stock_phrases`

**1.4 Empty significance claims (puffery).** Examples: "plays a crucial role", "stands as a testament to", "a rich tapestry of", "pivotal", "game-changer", "unlock the full potential".
*Move:* replace with the actual fact that shows significance (a number, consequence or example) or delete it. Ask what the sentence claims. If it claims nothing, cut it. `metric: flagged_vocab`, `stock_phrases`

**1.5 Vague attribution.** Examples: "Experts say", "Many believe", "researchers have found", "some critics argue", "others".
*Move:* name the source if the text has it. If not, state the claim directly or mark `[source?]`. `metric: vague_references`

**1.6 Reflexive balance.** Example: "While X has benefits, it also has drawbacks. Ultimately, the right choice depends on your needs."
*Move:* commit to a position the content supports, or say concretely what it depends on.

**1.6b Writing about the document.** Examples: "In this guide, we'll explore...", "This section covers...", "Let's dive in", "Below is a breakdown", "As mentioned above".
*Move:* delete it and say the thing. `metric: meta_reference`

**1.6c Staged reveals and punchy closers.** Examples: "Here's the thing:", "The result? X.", "The kicker:", and a short final sentence that sums up the paragraph ("That's the real win." "And that changes everything.").
*Move:* state the point plainly where it belongs, usually first. Delete a closer that restates the paragraph. `metric: staged_reveals`

**1.6d Tradeoff dodging.** Examples: "scale without sacrificing quality", "without requiring any setup", "while still maintaining", "the best of both worlds". These claim a benefit with no cost (Graphite: 2.6–70× human).
*Move:* name the cost, or cut the clause. Real systems trade things off, and saying what you gave up is more credible. `metric: tradeoff_dodges`

**1.6e Announcing importance.** Examples: "This distinction matters because...", "Here's why it matters", "absolutely essential", "cannot be overstated", "the single most important" (Graphite: up to 357×; "distinction matters" never occurs in the human corpus).
*Move:* delete the announcement and state the consequence. "This distinction matters because X fails" becomes "X fails when...". `metric: importance_flags`

**1.6f Bookend echo.** The last paragraph restates the first (Graphite: 20–32% of model articles vs 12% of human ones).
*Move:* end on the last new thing: a next step, a consequence, a caveat. `metric: bookend_echo`

**1.6g Concessive setups.** Examples: "While X has benefits, Y." "Although X, it's important to Y." "Despite X, Y." Graphite's concessive frames run 3–11× human (Astra 0.48 per 1k vs human 0.04). *Although* in mid-sentence is normal. The tell is the sentence-*initial* concession used as a run-up.
*Move:* state the main claim first, and add the concession after it if it matters. `metric: concessive_frames`

**1.7 Abstraction where an example belongs.** The survey found fewer proper nouns, dates, numbers and personal references in AI text.
*Move:* pull specifics from the source to the front. If there are none, flag `[example needed]`. Never invent one. `metric: specificity`

---

## 2. Structure and formatting

**2.1 Rule of three.** Lists of exactly three adjectives, nouns or clauses, over and over ("fast, reliable, and scalable").
*Move:* use the number of items the content has. Two is fine and so is one. Turn some lists into a sentence that ranks or relates the items. `metric: triads`

**2.2 Contrast frames (negative parallelism).** Examples: "It's not X, it's Y." "This isn't just about X—it's about Y." "Not only X, but also Y." "X isn't a bug; it's a feature." Paech et al. flag this as a recurring n-gram fingerprint.
*Move:* state Y directly. Keep a contrast only if someone actually holds belief X. `metric: contrast_frames`

**2.3 Uniform paragraphs and sections.** Every paragraph runs 3–5 sentences, every section is the same length, every section ends on a takeaway.
*Move:* let content set the length. A one-sentence paragraph is allowed. `metric: paragraph_rhythm`

**2.4 Over-formatting.** Headers on a short answer, bullets for continuous reasoning, **bold** sprinkled on phrases, title-case headings, emoji bullets, "Key Takeaways" boxes.
*Move:* use prose for reasoning and bullets for parallel, separable items. Bold at most one or two things a reader must not miss. Use sentence-case headings. `metric: formatting`

---

## 3. Sentence grammar, Profile A (bloated)

**3.1 Present participial tails.** 2–5× the human rate, the strongest single grammatical signal. Examples: "The update improves load times, **making** the app feel faster." "She smiled, **leaning** against the doorframe." Also ", highlighting...", ", underscoring...", ", ensuring...", ", reflecting...", ", paving the way for...".
*Move:* (a) delete the tail if it only editorializes ("..., highlighting its importance"); (b) make it a finite clause with a real link: "so the app feels faster", "because..."; (c) split it into its own sentence. In fiction, keep some, but not one per sentence. `metric: participial_clauses`

**3.2 Nominalizations.** 1.5–2× the human rate. Example: "The implementation of caching resulted in a significant reduction in latency."
*Move:* make the noun a verb and give it an agent: "Caching cut latency by 40%." Keep a nominalization when it names a real concept in a technical genre ("authentication", "inflation"). `metric: nominalizations`

**3.3 "That"-clause subjects and extraposed frames.** 2.6×. Examples: "That this approach works is evident." "It is important to note that..." "It is worth mentioning that..."
*Move:* state the content clause as the main clause: "This approach works." Drop "It is important to note that" entirely. `metric: that_subjects`

**3.3b Copula avoidance.** Examples: "serves as a hub", "stands as a reminder", "boasts a robust API", "represents a significant step", "features a wide range of". LLMs avoid plain *is/has*.
*Move:* "is a hub", "has an API". Then ask whether the sentence says anything. `metric: copula_avoidance`

**3.4 Phrasal coordination stacks.** 1.9×. Every sentence carries a "X, Y, and Z" noun-phrase list. Example: "...reduce deforestation, habitat destruction, and pollution, while also promoting sustainable consumption patterns."
*Move:* keep the one or two items that matter, or split them into clauses that say how they relate. `metric: triads`, `metric: coordination`

**3.5 Additive connective stacking.** Examples: "Additionally," "Moreover," "Furthermore," "Also," as paragraph starters. Human text uses more *but, because, so, if, when, although*.
*Move:* use the real logical relation. If the relation is just "and", drop the connective and let order do the work. `metric: connectives`

**3.6 Canonical order every time.** Every sentence opens Subject–Verb–Object, often with "The/This/It".
*Move:* vary some sentences: front a time or condition ("When the cache misses, ..."), put a question, or in informal genres use a fragment. `metric: sentence_openers`

**3.7 Uniform hedging and missing stance.** AI text has fewer epistemic and stance markers. Its hedges are generic ("can potentially", "may help to") rather than real doubts.
*Move:* remove the generic hedges ("can potentially help" becomes "helps", or "might help" if that's actually uncertain). Add a stance marker where the author really is uncertain or committed: "probably", "I doubt", "clearly", "in my experience" — and only where the author holds that stance. `metric: stance`

---

## 4. Sentence grammar, Profile B (over-compressed)

**4.1 Inanimate subject + animate verb.** Code, abstractions or documents do the acting. Examples: "`is_file()` **swallows** that." "This is where the asymmetry **bites**." "The test **wants** a fixture." "The config **doesn't know about** X." "The diff **tells** a story."
*Move:* name the real agent or the literal mechanism: "`is_file()` catches the exception and returns False." "This asymmetry causes failures when..." Keep standard technical idiom that readers parse instantly ("the function returns", "the server accepts", "the test expects"). Cut the cute ones. `metric: inanimate_agents`

**4.2 Denominal verbs and nonce conversions.** Examples: "Surfaced the error", "gated behind a flag", "bucketed by user", "landed the fix", "footnote it", "calendar it", "scoped to", "papered over".
*Move:* use the literal verb phrase where the conversion isn't standard for this audience: "showed the error to the user", "put behind a feature flag", "merged the fix". Audience matters. "Ship" and "merge" are fine for engineers. `metric: denominal_verbs`

**4.3 Stacked noun compounds.** Three or more nouns in a row. Examples: "retry budget exhaustion handling", "user session token refresh logic", "reader-patience budget".
*Move:* unpack with prepositions or a clause: "how we handle running out of retries". Keep established compounds the audience already knows ("database connection pool"). `metric: noun_stacks`

**4.4 Coined collocations (unattested bigrams).** Word pairs that never occur in human text. Examples: "quietly load-bearing", "vibes-level confidence", "blast radius of the rename". In long sessions they harden into private jargon, used as if the reader shares it.
*Move:* replace each coinage with the ordinary phrase. If the same coinage recurs, define it once or drop it. `metric: unattested_bigrams` (needs a baseline corpus), `metric: hyphen_compounds`

**4.5 Dropped relativizers and complementizers.** Example: "the activities they care about", "ensures the parser handles", "confirmed the patch fixes". RL-for-brevity makes deleting "that" categorical, while humans decide case by case.
*Move:* restore "that/which" when the relative or complement clause is long, has a full-NP subject, or allows a garden-path misreading. Leave it out in short, casual clauses ("the thing I said"). `metric: dropped_that`

**4.6 Long dependencies.** A subject separated from its verb by a long modifier, or heavy material before the main verb.
*Move:* put subject and verb close together and move heavy modifiers to the end or into their own sentence. `metric: dependency_proxy` (heuristic; `--spacy` gives real dependency distance)

**4.7 Telegraphic fragments and symbol prose.** Example: "Fixed. Root cause: race in init → retry loop. Now gated." Arrows, slashes and "w/" stand in for verbs.
*Move:* use full sentences, unless the user's own register is telegraphic (commit subject lines are a legitimate exception). `metric: symbol_prose`

**4.8 Count-led verbless fragments ("block language" in running prose).** Examples: "Two findings, one significant." "Three scripts, and a package that imports them." "One deliverable, ready to use." "Clean diff, small surface." The finite verb is missing, the count comes first, and an evaluative tag is attached by comma. It's the grammar of headlines, labels and slide titles (Quirk et al. 1985: *block language*), moved into prose. Common in agent wrap-ups and status replies, where the model previews and counts what follows.
*Move:* make it a sentence with a subject and a verb, and lead with the content instead of the count: "I found two problems. The race in `init` matters; the typo doesn't." Drop the count when the reader can see the list. Keep the label style for actual labels (headings, table cells, commit subjects). `metric: count_fragments`

---

## 5. Rhythm

**5.1 Low sentence-length variance.** Human text is "bursty", with short and long sentences mixed. LLM text has a narrow band, often 15–25 words throughout.
*Move:* combine some sentences and cut others short. Put the short sentence where the emphasis is. Target CV (sd/mean) of roughly ≥0.45 for expository prose and higher for fiction or conversation. `metric: sentence_length`

**5.1b Capped, symmetric length distribution.** Variance isn't the only gap. Human web prose has a long right tail: sentence-length skew 1.1 and a longest sentence of about 74 words. Current models have skew 0.24–0.45 and top out at 32–40 words (Graphite; skew d ≈ −0.7 to −1.0, a bigger effect than SD). Their *mean* sentence is also shorter (16–19 words vs 26.6).
*Move:* allow an occasional long, well-built sentence among mostly medium ones, instead of mixing short and medium evenly. `metric: sentence_shape` (needs 15+ sentences), `metric: sentence_length`

**5.1c Echo fragments (fake burstiness).** These are short sentences whose meaning has to be rebuilt from the previous sentence, and which add only polarity or a verdict:
- *Post-auxiliary (VP) ellipsis* as a standalone sentence: "Most POSTs aren't." "A rising one isn't." "It does." VP ellipsis is a normal conversational feature (Biber: an involved-register marker, typical of replies in dialogue). Detached into its own sentence in expository prose, it becomes a rhetorical beat: a polarity flip that restates the previous sentence.
- *Gnomic statements*: generic present tense, a universal or negative quantifier, and an evaluative verb, used to close a step of reasoning as a maxim: "A new key on each attempt protects nothing." "None of this fixes itself." "Tools matter less than people think." This is the "sayings that sound deep" pattern (blader/humanizer #3). "none of this" is a 23× Opus-5 tell in Graphite's data.
- *Bare discourse deixis*: a sentence that ends on, or rests on, "this"/"that" pointing at a whole proposition: "Check your script for this." "That matters." "This is exactly when that matters" stacks deixis on the Graphite tells "matters" (15×) and "is exactly" (11×).

In information-structure terms (Halliday; Chafe), these sentences add no new information. They re-predicate given material with a verdict. Human short sentences in prose usually introduce something new: an event, a number, a referent. LLMs produce these fragments when tuned toward "punchy" cadence. A de-slop pass produces them too when it tries to raise sentence-length variance, which is the cause of every instance in this repo's evals (0 of 39 short sentences in the unedited replies, 6 introduced by the rewrite).
*Move:* fold the content into the neighboring sentence ("…which isn't true of most POST endpoints"), or replace the verdict with the consequence ("…the server treats each retry as a new order"). `metric: echo_fragments`

**5.2 Repeated sentence templates.** The same POS shape recurs, like "[Adj] [noun] [verb]s [noun], [verb]ing [noun]." (Shaib et al.).
*Move:* break repeated shapes, especially in consecutive sentences. `metric: repeated_ngrams`, `metric: sentence_openers`

---

## 6. Lexicon

**6.1 Flagged vocabulary.** The tiers in the scanner come from Reinhart (GPT-4o/Llama tables), Kobak (PubMed excess words), Liang (peer reviews), Paech (antislop), and Wikipedia AI Cleanup. A sample:

- *Relation/grandeur:* tapestry, intricate, interplay, multifaceted, nuanced, landscape, realm, symphony, cacophony, labyrinth, mosaic, kaleidoscope
- *Significance verbs:* delve, underscore, highlight, showcase, foster, bolster, harness, leverage, navigate, unlock, unleash, elevate, empower, streamline, embark
- *Evaluation:* crucial, pivotal, vital, paramount, comprehensive, robust, seamless, commendable, meticulous, notable, noteworthy, invaluable, transformative, groundbreaking, cutting-edge
- *Fiction slop:* palpable, camaraderie, unspoken, fleeting, solace, amidst, pang, waft, unease, a testament to, shivers down spine, eyes sparkling, barely above a whisper, "Elara"
- *Filler:* "it's important to note", "it's worth noting", "in today's fast-paced world", "at the end of the day", "plays a crucial role"

*Move:* use the plainest accurate word, or delete it. Don't swap one fancy word for another ("delve" becomes "explore", which is still slop; "look at" is better). A word is not banned. One "robust" in a statistics paper is correct. The problem is density and genre mismatch. `metric: flagged_vocab`

**6.2 Elegant variation (current models) vs. repetition (older models).** Graphite's data reverses the older finding. Human MTLD is 85.6, and Opus 5 / Astra / Gemini 3.1 score 150 / 154 / 127 (d ≈ +1.0 to +1.4). Humans also repeat content words *more* (d −0.73 for Claude and Gemini). Current models cycle synonyms ("the tool… the platform… the solution… the system") where a person would just say "the tool" again. Repeated multi-word *templates* are still a tell (Shaib; Paech).
*Move:* when a text calls one thing by several names, pick one and repeat it. Vary repeated *phrases and sentence shapes*, not the names of things. `metric: lexical_diversity` (compare MTLD against the human 85.6 reference or a `--baseline`), `metric: repeated_ngrams`

**6.2b Long words.** AI web prose averages 5.2–5.7 letters per word, humans 4.9 (Graphite). This tracks nominalization and Latinate vocabulary.
*Move:* use the short word where it means the same thing ("use" for "utilize", "help" for "facilitate", "about" for "approximately"). Skip this in academic and code genres, where long terms are required. `metric: word_length`

**6.2c Intensifiers.** Examples: "absolutely", "incredibly", "entirely", "highly", "precisely", "every single", "enormously" (Gemini ≈13× human).
*Move:* delete them. If the claim needs strengthening, add a fact. `metric: intensifiers`

**6.2d Mannered substitutions.** A figurative or "writerly" phrase where a plain one exists: "a dial worth turning" (for "a parameter worth varying"), "earns its place", "doing the heavy lifting", "load-bearing", "sits upstream of". Graphite's LLM judge scores Opus 5 and Gemini 3.1 at about 2.5× human.
*Move:* use the literal phrase. Keep a metaphor only if it explains something the literal phrase can't. `metric: mannered_frames` (regex proxy; the real measure needs a judge)

**6.3 Missing involved-register words.** AI text under-uses *I, my, you, it, this*, *say*, sensory verbs (*look, hear, read*), feeling words, *might/would/could*, particles (*up, out, off*), idioms, and in casual genres contractions and the occasional mild profanity.
*Move:* where the genre is involved (chat, blog, email, personal essay), use them naturally. Don't force them into formal genres. `metric: pronouns`, `metric: contractions`, `metric: stance`

---

## 7. Punctuation

**7.1 Em dashes.** This tell depends on the model and is moving. GPT-3.5 used fewer dashes than humans. 2024–25 chat models overused them. In Graphite's 2026 data, GPT-6 Astra uses about ⅛ of the human rate, Gemini 3.1 almost none, and Opus 5 about the human rate. Several vendors seem to have overcorrected.
*Move:* if dashes are dense (more than about 3 per 1k words), replace most with a comma, colon, parentheses or a new sentence. Don't remove every dash, though. Zero dashes is not a human signature. `metric: punctuation`

**7.1b Missing exclamations, questions and parentheticals.** Humans use exclamation marks more than 100× as often as current models, and far more parenthetical asides (Graphite). They also use more question marks (Desaire; Simon). A de-slop pass that converts rhetorical-question headings into statements removes question marks too. That happened in this repo's own evals.
Graphite reference rates per 1k words (human / Opus 5 / Astra / Gemini 3.1): parentheses 7.7 / 0.9 / 0.05 / 0.04; questions 2.8 / 0.8 / 1.0 / 0.6; semicolons 1.4 / 0.6 / 0.6 / 0.3; exclamations 2.8 / ≈0.02 for all three models.
*Move:* in involved genres (chat, blog, email), keep a real question or a parenthetical aside where it fits. Don't add exclamation marks for effect. Genre matters here. Sonnet's chat replies in `evals/` used 11–30 parentheses per 1k words, *above* the human web rate, so don't strip them. `metric: human_markers`, `metric: punctuation`

**7.2 Narrow punctuation range.** Only commas and periods.
*Move:* use a question, a parenthetical, a semicolon or a colon where it fits naturally. `metric: punctuation`

**7.3 Curly-vs-straight quote mixing, unicode ellipsis, arrows in prose.** *Move:* normalize to the document's convention. `metric: punctuation`, `metric: symbol_prose`
