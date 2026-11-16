# Register targets by genre

The research's central finding is that LLMs don't shift register with genre the way people do (Reinhart et al.; Sardinha 2024). So the target is always **what skilled humans do in this genre**, and the pass should push toward that genre's pole, not toward one "human" style.

Biber's Dimension 1 is the main axis:

- **Involved** pole: 1st/2nd person, private verbs (*think, feel, guess*), contractions, present tense, hedges and emphatics, *because*-clauses, demonstratives, questions, *that*-deletion in short clauses, discourse particles.
- **Informational** pole: nouns, nominalizations, prepositions, attributive adjectives, long words, high type/token ratio.

The scanner thresholds are rough. Use `--baseline` with a real sample of the target genre when you can.

---

## Chat reply / Slack / DM
- **Pole:** strongly involved.
- **Do:** answer in the first line. Use contractions, "I"/"you", short paragraphs, and fragments where natural. Ask a question back if you need one. Stop when you're done.
- **Avoid:** headers, bullet lists for under 4 items, bold, recap endings, "Great question", "Hope this helps".
- **Profile-B risk** (high): private jargon that accumulates over the thread, verbed nouns, personified code. Spell things out for a reader who joins cold.
- **Rough targets:** sentence-length CV ≥ 0.5; contractions present; 1st/2nd person ≥ 20 per 1k words; em dashes ≈ 0.

## Coding-agent output, PR descriptions, status updates, commit bodies
- **Pole:** mixed. Informational content, but addressed to a person.
- **Do:** say what changed, why, and what's uncertain, as full sentences with real agents ("I changed X because Y"). Use the established terms of the codebase. Keep a technical term fixed once you've introduced it. Use bullets for separable changes.
- **Avoid (Profile B):** "X swallows/bites/wants/knows", "surfaced/gated/landed/bucketed" for readers outside the team, 3+ noun stacks, arrows instead of verbs, dropped "that" in long clauses, coined metaphors ("load-bearing", "blast radius").
- **Avoid (Profile A):** "This PR comprehensively enhances...", recap paragraphs, "robust", "seamless".
- **Commit subject lines** are a legit telegraphic genre: imperative mood, ≤ 72 characters.

## README / technical docs / tutorials
- **Pole:** informational, second person.
- **Do:** use imperative steps, "you", concrete commands and outputs, and one fixed name per concept. Explain *why* briefly where it helps people avoid mistakes.
- **Avoid:** "seamlessly", "powerful", "robust", "leverage", marketing openers, "In this guide, we will delve into...", emoji headings, a "Conclusion" section.

## Expository essay / blog / op-ed
- **Pole:** mid. A blog leans involved, an essay leans informational, and an op-ed commits to a stance.
- **Do:** lead with the claim. Use specific examples, varied paragraph lengths, and a clear authorial stance with real hedges only where the author is uncertain. Use idioms and plain verbs.
- **Avoid:** five-paragraph symmetry, "In today's world", triads, contrast frames, fake balance, recap conclusions, participial tails, "a testament to".
- **Note:** Sardinha found AI essays *less* persuasive and *less* involved than human ones, so make the case with evidence, not ornament.

## Academic writing (abstracts, papers)
- **Pole:** informational. Nominalizations and passives are normal here, and so is low involvement.
- **Do:** keep the density, but make it specific: name the method, data, n, effect size and limitation. Use explicit references, measured claims, and stance markers the field uses ("we argue", "this suggests").
- **Avoid:** Kobak/Liang excess vocabulary (*delve, intricate, pivotal, underscore, meticulous, commendable, showcase, notable, comprehensive*), "plays a crucial role", "sheds light on", "paves the way", participial tails that editorialize ("..., highlighting the importance of"). Sardinha found AI academic text *more* persuasive than human academic text, so tone down the advocacy.
- **Rough targets:** nominalizations high is OK. Watch participial tails (< 1 per 100 words) and flagged vocabulary (≈ 0).

## Fiction
- **Pole:** narrative. Past tense, 3rd person, dialogue, concrete sensory detail.
- **Do:** use specific nouns, plain dialogue tags ("said"), subtext, unexpected but *apt* word choice, varied sentence length, and sentence fragments.
- **Avoid:** Reinhart/Paech fiction slop (*palpable, camaraderie, unspoken, fleeting, solace, amidst, pang, waft, a testament to, barely above a whisper, a mix of X and Y, eyes sparkling with mischief, the air thick with*), stock names (*Elara, Kael, Lyra, Seraphina*), one participial tail per sentence, characters who name their emotions, endings that resolve with a moral.
- **Note:** the survey found AI fiction and reviews sometimes *more* emotional but in a generic way. Use specific feeling shown through action.

## Email (professional)
- **Pole:** involved-leaning but polite.
- **Do:** put the ask or the news in the first two sentences, then the context, then the next step. Use "I"/"you" and contractions as the relationship allows.
- **Avoid:** "I hope this email finds you well", "I wanted to reach out", "Please don't hesitate to", "Thank you for your understanding", triads of thanks.

## Marketing / product copy
- **Pole:** persuasive and involved.
- **Do:** make one concrete benefit per sentence with a number or a scenario, and use the customer's own words.
- **Avoid:** *unlock, elevate, empower, seamless, cutting-edge, revolutionize, game-changer, next-level, in today's fast-paced*. These are both the most-flagged and the least persuasive.
