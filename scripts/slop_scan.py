#!/usr/bin/env python3
"""slop_scan: measure linguistic fingerprints of LLM-generated prose.

Every metric is a standalone measurement tool registered in METRICS. Run them
all as a report, pick individual ones, compare against a human baseline, or
import this file and call metric functions directly.

    python3 slop_scan.py draft.md                    # full report
    python3 slop_scan.py draft.md -m participial_clauses -m nominalizations
    python3 slop_scan.py draft.md --baseline mine.md # deltas vs a human sample
    python3 slop_scan.py draft.md --genre chat       # genre-aware thresholds
    python3 slop_scan.py draft.md --json             # machine-readable
    python3 slop_scan.py --list                      # describe every metric
    cat draft.md | python3 slop_scan.py -            # stdin

    # as a library
    from slop_scan import Doc, run_metric
    run_metric("sentence_length", Doc(text))

Standard library only. Optional: --spacy (if spaCy + en_core_web_sm are
installed) swaps parser-based versions in for the heuristic noun_stacks,
dependency_proxy, dropped_that and inanimate_agents.

All values are heuristics meant to direct a careful read, not to grade text.
See ../references/patterns.md for what each metric means and how to fix it.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import statistics
import sys
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable

# --------------------------------------------------------------------------
# Lexicons
# --------------------------------------------------------------------------

FUNCTION_WORDS = set("""
a an the and or but nor so yet for of in on at to from by with without within into onto upon
over under about above below across after before between through during against among around
as if than then because although though while whereas unless until since when where whether
which who whom whose what that this these those there here it its it's i me my mine we us our
ours you your yours he him his she her hers they them their theirs one ones is are was were be
been being am do does did doing done have has had having will would shall should can could may
might must not no nor only also just very too more most less least much many some any all each
every both either neither few several such own same other another again further once out up
down off away back even still already ever never always often sometimes how why
toward towards via per amid amidst despite unlike near
""".split())

PERSON_NOUNS = set("""
user users developer developers engineer engineers team teams people person author authors
reviewer reviewers customer customers student students teacher teachers reader readers writer
writers maintainer maintainers admin admins operator operators client clients human humans
man woman men women child children kid kids friend friends manager managers founder founders
researcher researchers scientist scientists doctor doctors patient patients
""".split())

# Tiered vocabulary drawn from Reinhart et al. 2025 (Table 1), Kobak et al. 2025,
# Liang et al. 2024, Paech et al. 2025, and Wikipedia:Signs of AI writing.
# Patterns are regex stems; matched case-insensitively at word boundaries.
FLAGGED_VOCAB: dict[str, list[str]] = {
    "grandeur": [
        r"tapestr(y|ies)", r"intricate(ly)?", r"intricac(y|ies)", r"interplay", r"multifaceted",
        r"nuanced", r"landscape", r"realm", r"symphony", r"cacophony", r"labyrinth(ine)?",
        r"mosaic", r"kaleidoscope", r"beacon", r"testament", r"crucible", r"tableau",
        r"ever-evolving", r"ever-changing", r"bustling", r"vibrant",
    ],
    "significance_verbs": [
        r"delv(e|es|ed|ing)", r"underscor(e|es|ed|ing)", r"showcas(e|es|ed|ing)",
        r"foster(s|ed|ing)?", r"bolster(s|ed|ing)?", r"harness(es|ed|ing)?",
        r"leverag(e|es|ed|ing)", r"navigat(e|es|ed|ing)", r"unlock(s|ed|ing)?",
        r"unleash(es|ed|ing)?", r"elevat(e|es|ed|ing)", r"empower(s|ed|ing)?",
        r"streamlin(e|es|ed|ing)", r"embark(s|ed|ing)?", r"grappl(e|es|ed|ing)",
        r"unravel(s|ed|led|ing|ling)?", r"ignit(e|es|ed|ing)", r"resonat(e|es|ed|ing)",
        r"illuminat(e|es|ed|ing)", r"spearhead(s|ed|ing)?", r"revolutioniz(e|es|ed|ing)",
        r"reimagin(e|es|ed|ing)", r"elucidat(e|es|ed|ing)",
    ],
    "evaluation": [
        r"crucial(ly)?", r"pivotal", r"paramount", r"comprehensive(ly)?", r"robust(ly|ness)?",
        r"seamless(ly)?", r"commendable", r"meticulous(ly)?", r"noteworthy", r"invaluable",
        r"transformative", r"groundbreaking", r"cutting-edge", r"game-?changer", r"profound(ly)?",
        r"unparalleled", r"indispensable", r"holistic", r"dynamic", r"innovative",
        r"remarkabl(e|y)", r"notabl(e|y)", r"versatile", r"captivating", r"enduring",
    ],
    "fiction": [
        r"palpable", r"camaraderie", r"unspoken", r"fleeting", r"solace", r"amidst",
        r"pang", r"waft(s|ed|ing)?", r"unease", r"newfound", r"steel(ed|ing)? (himself|herself|themselves)",
        r"elara", r"kael", r"lyra", r"seraphina", r"thrumm?(ed|ing)", r"shimmer(ed|ing)?",
        r"whisper(ed|s)? of", r"a mix(ture)? of",
    ],
    "evaluative_2026": [   # Graphite 2026: top evaluative adjectives/adverbs per current model (×human)
        r"dependable", r"meaningful", r"deliberate(ly)?", r"incredibly", r"immense(ly)?",
        r"enormously", r"remarkably", r"tangible", r"actionable",
    ],
    "connective_filler": [
        r"additionally", r"moreover", r"furthermore", r"consequently", r"notably",
        r"ultimately", r"essentially", r"arguably", r"overall",
    ],
}

STOCK_PHRASES: dict[str, list[str]] = {
    "assistant_framing": [
        r"^(certainly|absolutely|of course|sure|great question)[!,.]", r"great question",
        r"i hope (this|that) helps", r"let me know if", r"feel free to", r"happy to help",
        r"you'?re (absolutely|completely) right", r"here'?s (a|the) (breakdown|summary|quick)",
        r"i'?d be happy to", r"don'?t hesitate to", r"as an ai",
    ],
    "openers": [
        r"in today'?s (fast-paced|digital|modern|ever)", r"in the (ever-evolving|ever-changing|realm|world) of",
        r"when it comes to", r"in an era (of|where)", r"imagine a world", r"have you ever wondered",
        r"i hope this (email|message) finds you", r"i wanted to reach out",
    ],
    "editorializing": [
        r"it'?s (important|worth|crucial|essential) (to note|noting|to remember|mentioning)",
        r"it is (important|worth|crucial|essential) (to note|noting|to remember|mentioning)",
        r"it should be noted", r"needless to say", r"it goes without saying",
        r"plays? an? (crucial|pivotal|vital|key|significant|important) role",
        r"stands? as an? (testament|reminder)", r"a testament to", r"serves? as a (reminder|testament)",
        r"sheds? light on", r"paves? the way", r"at the end of the day", r"the (power|importance) of",
        r"rich (cultural )?(heritage|history|tapestry)", r"(deeply|truly) (rooted|matters)",
        r"(unlock\w*|unleash\w*|harness\w*) (the|its|their|our|new) (full )?(potential|power|levels?)",
        r"bridges? the gap", r"(navigate|navigating) (the|this) (complex|ever)", r"embrac\w+ (this|the) (evolving|new)",
    ],
    "transitions_2026": [  # Graphite 2026 transition tells (×human: 8.6–117)
        r"another dimension", r"together,? these", r"what comes next", r"looking ahead,? the",
        r"furthermore,? the", r"ultimately,? this", r"additionally,? the", r"this comprehensive guide",
    ],
    "closers": [
        r"^in (summary|conclusion|essence|short)\b", r"^to (summarize|sum up|conclude)\b",
        r"^overall,", r"^ultimately,", r"^all in all", r"^in the end,",
        r"by (following|understanding|leveraging) (these|this)",
        r"the (right )?(choice|answer|decision|approach|solution) (ultimately )?(depends|comes down) (on|to)",
        r"presents? both (opportunities|challenges|benefits)",
        r"the future (of \w+ )?(looks|is) (bright|promising)", r"as we (move|look) (forward|ahead)",
        r"will (only )?continue to (grow|evolve|shape|play)", r"remains? to be seen",
    ],
}

VAGUE_REFS = [
    r"others", r"researchers", r"experts", r"critics", r"observers", r"scholars", r"many people",
    r"some people", r"many (believe|argue|say|feel)", r"some (argue|say|believe|suggest)",
    r"studies (show|suggest|have shown)", r"research (shows|suggests|has shown)",
    r"it is (said|believed|widely)", r"various", r"numerous", r"a (wide )?(variety|range|array|plethora|myriad) of",
]

ADDITIVE_CONNECTIVES = ["additionally", "moreover", "furthermore", "in addition", "also", "besides",
                        "likewise", "similarly", "notably", "importantly"]
LOGICAL_CONNECTIVES = ["because", "but", "so", "although", "though", "if", "when", "since", "unless",
                       "yet", "whereas", "however", "instead", "otherwise", "still"]

HEDGES = [r"might", r"perhaps", r"probably", r"possibly", r"maybe", r"i think", r"i guess",
          r"i suspect", r"i doubt", r"seems?", r"appears? to", r"likely", r"unlikely", r"sort of",
          r"kind of", r"roughly", r"i'm not sure", r"not sure", r"as far as i know"]
GENERIC_HEDGES = [r"can potentially", r"could potentially", r"may potentially", r"may help (to )?",
                  r"can help (to )?", r"it is possible that", r"to some extent", r"in some cases",
                  r"may or may not", r"can be (a )?(useful|helpful|beneficial)", r"tends? to be",
                  r"(may|can) provide", r"not necessarily", r"need not"]
BOOSTERS = [r"clearly", r"obviously", r"definitely", r"certainly", r"of course", r"really",
            r"frankly", r"honestly", r"in fact", r"actually", r"surely", r"undoubtedly"]

ANIMATE_VERBS = """
swallow swallows swallowed bite bites bit want wants wanted know knows knew care cares cared
decide decides decided refuse refuses refused complain complains complained insist insists insisted
ask asks asked tell tells told hate hates hated love loves loved eat eats ate chew chews chewed
hide hides hid pretend pretends pretended fight fights fought sneak sneaks snuck grab grabs grabbed
steal steals stole lie lies lied hope hopes hoped believe believes believed think thinks thought
forget forgets forgot remember remembers remembered agree agrees agreed argue argues argued
lean leans leaned whisper whispers whispered scream screams screamed beg begs begged
quietly silently happily cheerfully
""".split()
ANIMATE_VERB_SET = {w for w in ANIMATE_VERBS if not w.endswith("ly")}

DENOMINAL_VERBS = [
    r"surfac(ed|es|ing)", r"gat(ed|ing)", r"bucket(ed|ing)", r"land(ed|ing) (the|a|this|that|it|my|our|your)",
    r"scop(ed|ing) (to|down|out)", r"plumb(ed|ing)( through)?", r"thread(ed|ing) (through|it|the)",
    r"wired? up", r"paper(ed|ing)? over", r"footnot(ed|ing)", r"calendar(ed|ing)", r"action(ed|ing)",
    r"task(ed|ing) with", r"messag(ed|ing) (me|you|him|her|them|the)", r"dial(ed|led|ing)? in",
    r"bak(ed|ing) in", r"sunset(ted|ting)", r"greenlit", r"timebox(ed|ing)", r"upstream(ed|ing)",
    r"dogfood(ed|ing)", r"bikeshed(ded|ding)", r"socializ(ed|ing) (the|this|it)", r"gut-check(ed|ing)?",
    r"sanity-check(ed|ing)", r"de-?risk(ed|ing|s)?", r"productioniz(ed|ing|e)", r"operationaliz(ed|ing|e)",
    r"architect(ed|ing)", r"ideat(ed|ing|e)", r"impact(ed|ing|s) (the|our|your|their|it)",
    r"spik(ed|ing) (on|out)", r"ticket(ed|ing)", r"fence(d)? off", r"pin(ned|ning) (to|the|it)",
    r"stub(bed|bing) (out|the)", r"shim(med|ming)", r"guardrail(ed|ing)", r"flag(ged|ging) (it|the|this) off",
]

COMPLEMENT_VERBS = """
ensure ensures ensured confirm confirms confirmed verify verifies verified assume assumes assumed
mean means meant show shows showed note notes noted notice notices noticed realize realizes realized
think thinks thought believe believes believed feel feels felt say says said know knows knew found
find finds suggest suggests suggested indicate indicates indicated guarantee guarantees guaranteed
check checks checked expect expects expected claim claims claimed hope hopes hoped
""".split()
FINITE_CUES = set("""
is are was were has have had will would can could should does did doesn't don't isn't aren't wasn't
weren't won't can't couldn't shouldn't handles works fails returns runs uses needs matches passes
breaks exists contains calls sees gets makes takes keeps holds covers applies happens stays
""".split())

ING_NOT_VERBS = set("""
thing things nothing something anything everything morning mornings evening evenings during ceiling
king kings ring rings string strings spring springs wing wings sibling siblings building buildings
meeting meetings feeling feelings setting settings heading headings wedding wording beginning
ending endings understanding painting paintings offering offerings including according regarding
concerning pending following given notwithstanding lightning pudding earring darling
housing parking funding pricing training spending lending zoning marketing planning engineering computing
programming testing logging caching networking accounting advertising shipping clothing bedding warning
warnings earnings savings booking hearing hearings funding filing filings listing listings rating ratings
ceiling siding roofing seating lighting heating cooling plumbing flooring catering banking mining farming
""".split())

NOMINALIZATION_EXCLUDE = set("""
nation nations station stations ration mention mentions moment moments comment comments
city cities pity entity entities quality qualities quantity quantities sentence sentences
science sciences experience experiences evidence audience audiences silence distance distances
balance instance instances fence fences sense dance chance chances ambience element elements
department departments government governments document documents argument arguments payment
payments segment segments fragment fragments apartment environment environments question questions
function functions option options section sections version versions session sessions
position positions condition conditions caution motion lotion potion portion portions
business witness witnesses
""".split())

OBJECT_STARTERS = set("the a an us them it this that these those which its their our your his her me him".split())
NOUN_STACK_BLOCK_SUFFIX = ("ly", "ed", "ing", "ous", "ful", "ive", "able", "ible", "ical", "less", "est", "ish")
COMMON_NON_NOUNS = set("""
new old good bad big small large great high low long short first last next real same different
open closed main full empty fast slow easy hard simple clear true false right wrong own other
best better worse sure free whole entire public private early late recent current final local
global single double many few several each every any some such like just only very really
get gets got make makes made take takes took use uses run runs see sees go goes went come comes
set sets put puts let lets keep keeps write writes say says said tell tells told give gives gave
higher lower bigger smaller faster slower
""".split())

# Per-article means from Graphite "AI Tells" (2026), 9,984 matched web-article topics, CC BY 4.0.
# Source: references/data/graphite_ai_tells_features.csv. Shown next to measured values in reports.
GRAPHITE_REF = {
    "word_len_mean": {"human": 4.90, "opus5": 5.20, "astra": 5.63, "gemini31": 5.35},
    "word_len_skew": {"human": 0.83, "opus5": 0.67, "astra": 0.49, "gemini31": 0.60},
    "mtld": {"human": 85.6, "opus5": 150.3, "astra": 153.6, "gemini31": 127.1},
    "sent_len_mean": {"human": 26.6, "opus5": 18.3, "astra": 16.2, "gemini31": 19.4},
    "sent_len_std": {"human": 17.0, "opus5": 8.4, "astra": 5.8, "gemini31": 6.8},
    "sent_len_skew": {"human": 1.10, "opus5": 0.45, "astra": 0.39, "gemini31": 0.24},
    "sent_len_max": {"human": 73.6, "opus5": 40.2, "astra": 32.0, "gemini31": 34.3},
    "emdash_per1k": {"human": 3.14, "opus5": 2.93, "astra": 0.37, "gemini31": 0.01},
    "semicolon_per1k": {"human": 1.39, "opus5": 0.59, "astra": 0.59, "gemini31": 0.33},
    "exclaim_per1k": {"human": 2.81, "opus5": 0.02, "astra": 0.02, "gemini31": 0.02},
    "question_per1k": {"human": 2.75, "opus5": 0.78, "astra": 0.96, "gemini31": 0.55},
    "paren_per1k": {"human": 7.68, "opus5": 0.94, "astra": 0.05, "gemini31": 0.04},
    "year_ref_per1k": {"human": 5.87, "opus5": 1.26, "astra": 1.37, "gemini31": 1.00},
    "bookend_echo_rate": {"human": 0.12, "opus5": 0.20, "astra": 0.32, "gemini31": 0.25},
    "concessive_per1k": {"human": 0.04, "opus5": 0.14, "astra": 0.48, "gemini31": 0.43},
}
# Checks whose difference from human text has the SAME sign for every model tested: all nine models in
# Graphite's features (GPT-4.1 -> GPT-6, Opus 4 -> 5, Gemini 2.5 -> 3.1), or all five corpora in
# evals/graphite_validation.json. They track the instruction-tuned register itself rather than a
# fashionable word, so they are the least likely to decay. See references/research.md.
DURABLE = ["word_length", "participial_clauses", "importance_flags", "tradeoff_dodges", "triads",
           "model_fingerprint", "request_fit", "lexical_diversity"]
# Held in BOTH Graphite web articles (9 models) and ELEPHANT advice replies (9 models, 7 vendors incl. open
# models). lexical_diversity holds for frontier closed models only (Qwen/Llama/Mistral ~ human).
# Dropped after ELEPHANT: sentence_shape/longest sentence (no gap in advice text), contrast_frames (Qwen,
# GPT-5 below human), bookend_echo and denominal_verbs (not testable / not tested there).

# metric field -> GRAPHITE_REF key, for report annotations
REF_FIELDS = {
    "word_length": {"mean_letters": "word_len_mean", "skew": "word_len_skew"},
    "lexical_diversity": {"mtld": "mtld"},
    "sentence_length": {"mean": "sent_len_mean", "sd": "sent_len_std", "skew": "sent_len_skew", "max": "sent_len_max"},
    "sentence_shape": {"skew": "sent_len_skew", "max": "sent_len_max"},
    "punctuation": {"em_dash_per_1k": "emdash_per1k", "semicolon_per_1k": "semicolon_per1k",
                    "exclaim_per_1k": "exclaim_per1k", "question_per_1k": "question_per1k", "paren_per_1k": "paren_per1k"},
    "specificity": {"years_per_1k": "year_ref_per1k"},
    "concessive_frames": {"per_1k": "concessive_per1k"},
}


def skewness(xs: list[float]) -> float | None:
    if len(xs) < 3:
        return None
    m = statistics.mean(xs)
    sd = statistics.pstdev(xs)
    if not sd:
        return 0.0
    return round(sum((x - m) ** 3 for x in xs) / len(xs) / sd ** 3, 2)


# --------------------------------------------------------------------------
# Document model
# --------------------------------------------------------------------------

ABBREV = r"(?:e\.g|i\.e|etc|vs|cf|al|Dr|Mr|Mrs|Ms|Prof|St|Jr|Sr|Inc|Ltd|Fig|No|approx)"
WORD_RE = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)*(?:-[A-Za-z]+)*")


@dataclass
class Doc:
    raw: str
    text: str = ""                      # prose with code removed
    paragraphs: list[str] = field(default_factory=list)
    sentences: list[str] = field(default_factory=list)
    words: list[str] = field(default_factory=list)   # lowercase tokens
    lines: list[str] = field(default_factory=list)   # raw markdown lines (for formatting)
    _nlp_doc: object = None

    def __post_init__(self):
        raw = self.raw.replace("\r\n", "\n")
        self.lines = raw.split("\n")
        t = re.sub(r"```.*?```", "\n", raw, flags=re.S)          # fenced code
        t = re.sub(r"`[^`\n]+`", "CODE", t)                       # inline code -> placeholder
        t = re.sub(r"https?://\S+", "URL", t)
        t = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", t)          # md links
        t = t.replace("’", "'").replace("‘", "'")
        paras = []
        for block in re.split(r"\n\s*\n", t):
            block_lines = []
            for ln in block.split("\n"):
                s = ln.strip()
                if not s or re.match(r"^#{1,6}\s", s) or re.match(r"^\|", s) or re.match(r"^[-*_]{3,}$", s):
                    continue
                s = re.sub(r"^([-*+]|\d+[.)])\s+", "", s)           # list markers
                s = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", s)  # emphasis
                block_lines.append(s)
            if block_lines:
                paras.append(" ".join(block_lines))
        self.paragraphs = paras
        self.text = "\n\n".join(paras)
        self.sentences = [s for p in paras for s in split_sentences(p)]
        self.words = [w.lower() for w in WORD_RE.findall(self.text)]

    @property
    def n_words(self) -> int:
        return max(len(self.words), 1)

    def per_1k(self, n: float) -> float:
        return round(1000.0 * n / self.n_words, 2)


def split_sentences(p: str) -> list[str]:
    p = re.sub(rf"\b({ABBREV})\.", r"\1<DOT>", p)
    parts = re.split(r"(?<=[.!?])[\"')\]]*\s+(?=[\"'(\[]?[A-Z0-9])", p)
    out = [s.replace("<DOT>", ".").strip() for s in parts]
    return [s for s in out if len(WORD_RE.findall(s)) > 0]


def words_of(s: str) -> list[str]:
    return [w.lower() for w in WORD_RE.findall(s)]


def find_all(patterns: list[str], text: str, flags=re.I | re.M) -> list[str]:
    """All matches of all patterns, dropping matches that overlap an earlier (longer) one."""
    spans = []
    for pat in patterns:
        for m in re.finditer(rf"\b{pat}\b" if not pat.startswith("^") else pat, text, flags):
            spans.append((m.start(), m.end(), m.group(0)))
    spans.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    out, last_end = [], -1
    for a, b, g in spans:
        if a >= last_end:
            out.append(g)
            last_end = b
    return out


def context(text: str, start: int, end: int, pad: int = 40) -> str:
    a, b = max(0, start - pad), min(len(text), end + pad)
    return ("…" if a else "") + text[a:b].replace("\n", " ") + ("…" if b < len(text) else "")


def mtld(words: list[str], threshold: float = 0.72) -> float | None:
    """Measure of Textual Lexical Diversity (McCarthy & Jarvis 2010), mean of forward and backward passes."""
    if len(words) < 50:
        return None

    def one_pass(ws):
        factors, types, count = 0.0, set(), 0
        for x in ws:
            count += 1
            types.add(x)
            if len(types) / count <= threshold:
                factors += 1
                types, count = set(), 0
        if count:
            factors += (1 - len(types) / count) / (1 - threshold)
        return len(ws) / factors if factors else float(len(ws))
    return round((one_pass(words) + one_pass(words[::-1])) / 2, 1)


def cv(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = statistics.mean(xs)
    return round(statistics.pstdev(xs) / m, 3) if m else 0.0


# --------------------------------------------------------------------------
# Metric registry
# --------------------------------------------------------------------------

@dataclass
class Metric:
    name: str
    layer: str
    profile: str          # "A" bloated, "B" compressed, "both"
    description: str
    fn: Callable[[Doc], dict]
    key: str              # which output field thresholds apply to
    warn_above: float | None = None
    warn_below: float | None = None


METRICS: dict[str, Metric] = {}


def metric(name, layer, profile, description, key, warn_above=None, warn_below=None):
    def deco(fn):
        METRICS[name] = Metric(name, layer, profile, description, fn, key, warn_above, warn_below)
        return fn
    return deco


# ---- Rhythm ---------------------------------------------------------------

@metric("sentence_length", "rhythm", "both",
        "Sentence length mean/sd and coefficient of variation (burstiness). Low CV = metronomic LLM rhythm.",
        key="cv", warn_below=0.40)
def m_sentence_length(d: Doc) -> dict:
    lens = [len(words_of(s)) for s in d.sentences]
    if not lens:
        return {"cv": 0.0, "n_sentences": 0}
    band = sum(1 for x in lens if 12 <= x <= 25) / len(lens)
    return {"cv": cv(lens), "skew": skewness(lens), "hits": [f"{n}w: {s[:60]}" for n, s in zip(lens, d.sentences)], "mean": round(statistics.mean(lens), 1),
            "sd": round(statistics.pstdev(lens), 1), "min": min(lens), "max": max(lens),
            "share_12_25_words": round(band, 2), "n_sentences": len(lens)}


@metric("paragraph_rhythm", "structure", "A",
        "Paragraph length variation (sentences per paragraph). Low CV = uniform blocks.",
        key="cv", warn_below=0.30)
def m_paragraph_rhythm(d: Doc) -> dict:
    counts = [len(split_sentences(p)) for p in d.paragraphs]
    if len(counts) < 3:
        return {"cv": None, "n_paragraphs": len(counts), "note": "too few paragraphs"}
    return {"cv": cv(counts), "mean_sentences": round(statistics.mean(counts), 1), "n_paragraphs": len(counts)}


@metric("sentence_openers", "grammar", "A",
        "Repetition of sentence-initial words; share of The/This/It openers (canonical-order proxy).",
        key="top_opener_share", warn_above=0.30)
def m_sentence_openers(d: Doc) -> dict:
    firsts = [words_of(s)[0] for s in d.sentences if words_of(s)]
    if not firsts:
        return {"top_opener_share": 0.0}
    c = Counter(firsts)
    top, n = c.most_common(1)[0]
    consec = sum(1 for a, b in zip(firsts, firsts[1:]) if a == b)
    tti = sum(c[w] for w in ("the", "this", "it", "these", "that")) / len(firsts)
    return {"top_opener_share": round(n / len(firsts), 2), "top_opener": top,
            "the_this_it_share": round(tti, 2), "consecutive_same_opener": consec,
            "top5": c.most_common(5)}


# ---- Lexicon ----------------------------------------------------------------

@metric("flagged_vocab", "lexicon", "A",
        "Density of words over-represented in LLM output (Reinhart, Kobak, Liang, Paech, Wikipedia).",
        key="per_1k", warn_above=3.0)
def m_flagged_vocab(d: Doc) -> dict:
    by_tier, hits = {}, Counter()
    for tier, pats in FLAGGED_VOCAB.items():
        h = find_all(pats, d.text)
        by_tier[tier] = len(h)
        hits.update(x.lower() for x in h)
    total = sum(by_tier.values())
    return {"per_1k": d.per_1k(total), "count": total, "by_tier": by_tier, "hits": hits.most_common(15)}


@metric("stock_phrases", "content", "A",
        "Assistant framing, stock openers/closers, editorializing and puffery phrases.",
        key="count", warn_above=0)
def m_stock_phrases(d: Doc) -> dict:
    by_cat, hits = {}, []
    sent_text = "\n".join(d.sentences)
    for cat, pats in STOCK_PHRASES.items():
        h = find_all(pats, sent_text)
        by_cat[cat] = len(h)
        hits += [f"{cat}: {x}" for x in h]
    return {"count": sum(by_cat.values()), "by_category": by_cat, "hits": hits[:20]}


@metric("lexical_diversity", "lexicon", "A",
        "MTLD, MATTR-50, TTR, hapax share. Current models score HIGHER than humans (Graphite: MTLD 127-154 vs 85.6, "
        "d≈+1.0-1.4): they vary wording instead of repeating the key noun. Older LLMs were lower. Noisy under ~300 words.",
        key="mtld", warn_below=None)
def m_lexical_diversity(d: Doc, window: int = 50) -> dict:
    w = d.words
    if len(w) < window:
        return {"mtld": mtld(w), "mattr": None, "ttr": round(len(set(w)) / max(len(w), 1), 3), "note": "text shorter than window"}
    counts = Counter(w[:window])
    ttrs = [len(counts) / window]
    for i in range(window, len(w)):
        counts[w[i]] += 1
        old = w[i - window]
        counts[old] -= 1
        if counts[old] == 0:
            del counts[old]
        ttrs.append(len(counts) / window)
    c = Counter(w)
    hapax = sum(1 for v in c.values() if v == 1)
    return {"mtld": mtld(w), "mattr": round(statistics.mean(ttrs), 3), "ttr": round(len(c) / len(w), 3),
            "hapax_share_of_types": round(hapax / len(c), 3)}


@metric("repeated_ngrams", "lexicon", "both",
        "Content-bearing 3/4-grams used 2+ times (formulaic phrasing; Shaib et al., Paech et al.).",
        key="per_1k", warn_above=4.0)
def m_repeated_ngrams(d: Doc) -> dict:
    out, total = {}, 0
    for n in (3, 4):
        grams = Counter()
        for s in d.sentences:
            ws = words_of(s)
            for i in range(len(ws) - n + 1):
                g = ws[i:i + n]
                if sum(1 for x in g if x not in FUNCTION_WORDS) >= 2 and "code" not in g:
                    grams[" ".join(g)] += 1
        rep = [(g, c) for g, c in grams.most_common() if c >= 2]
        out[f"{n}gram"] = rep[:10]
        total += sum(c - 1 for _, c in rep)
    return {"per_1k": d.per_1k(total), "repeats": total, **out}


@metric("vague_references", "content", "A",
        "Vague group/attribution references: others, experts, studies show, a variety of...",
        key="per_1k", warn_above=3.0)
def m_vague(d: Doc) -> dict:
    h = find_all(VAGUE_REFS, d.text)
    return {"per_1k": d.per_1k(len(h)), "count": len(h), "hits": Counter(x.lower() for x in h).most_common(10)}


@metric("specificity", "content", "A",
        "Numbers, mid-sentence capitalized names, and dates per 1k words. Low = abstract prose.",
        key="per_1k", warn_below=8.0)
def m_specificity(d: Doc) -> dict:
    nums = len(re.findall(r"\b\d[\d,.:%]*\b", d.text)) + len(re.findall(
        r"\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|fifty|hundred|"
        r"thousand|million|billion|percent|half|dozen)\b", d.text, re.I))
    names = 0
    for s in d.sentences:
        toks = s.split()
        for t in toks[1:]:
            t = t.strip("\"'()[],.;:!?")
            if t[:1].isupper() and not t.isupper() and t not in ("I", "CODE", "URL"):
                names += 1
    months = len(re.findall(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d", d.text))
    years = len(re.findall(r"\b(1[89]\d\d|20\d\d)s?\b", d.text))
    pct = len(re.findall(r"\d\s?%|\bpercent\b", d.text))
    total = nums + names + months
    return {"per_1k": d.per_1k(total), "numbers": nums, "proper_names": names, "dates": months,
            "years_per_1k": d.per_1k(years), "percents": pct}


# ---- Grammar: Profile A --------------------------------------------------

@metric("participial_clauses", "grammar", "A",
        "Present participial clauses (', making...', 'Leaning on..., she'). 2-5x human rate in tuned LLMs.",
        key="per_100_sentences", warn_above=12.0)
def m_participial(d: Doc) -> dict:
    hits = []
    for s in d.sentences:
        for m in re.finditer(r"(,|—|–|\bwhile( also)?|\bthereby)\s+(also\s+|further\s+|thus\s+)?([a-z]+ing)\b", s):
            w = m.group(4)
            if len(w) >= 5 and w not in ING_NOT_VERBS:
                hits.append(context(s, m.start(), m.end(), 30))
        m = re.match(r"^\s*([A-Z][a-z]+ing)\b([^,]{0,60}),", s)
        # a participial opener is short before its comma ("Leaning on his agility, Bryan ..."); a long
        # comma-free run means the -ing word is a gerund subject ("Parking also eats land that could ...")
        if m and m.group(1).lower() not in ING_NOT_VERBS and len(m.group(2).split()) <= 6:
            hits.append(context(s, 0, m.end(), 0))
    return {"per_100_sentences": round(100.0 * len(hits) / max(len(d.sentences), 1), 1),
            "count": len(hits), "hits": hits[:12]}


@metric("nominalizations", "grammar", "A",
        "Nouns derived from verbs/adjectives (-tion, -ment, -ness, -ity, -ance, -ence...). 1.5-2x human rate.",
        key="per_1k", warn_above=35.0)
def m_nominalizations(d: Doc) -> dict:
    pat = re.compile(r"^[a-z]{3,}(tion|sion|ment|ness|ity|ance|ence|ancy|ency|ization|isation)s?$")
    hits = [w for w in d.words if pat.match(w) and w not in NOMINALIZATION_EXCLUDE and len(w) >= 7]
    return {"per_1k": d.per_1k(len(hits)), "count": len(hits), "top": Counter(hits).most_common(12)}


@metric("that_subjects", "grammar", "A",
        "'That'-clauses as subject and extraposed frames ('It is important to note that...'). 2.6x human rate.",
        key="count", warn_above=1)
def m_that_subjects(d: Doc) -> dict:
    hits = []
    for s in d.sentences:
        if re.match(r"^That\s+(the|this|these|those|a|an|we|they|it|he|she|you|i|our|their|such|no)\b", s, re.I):
            hits.append(s[:90])
        for m in re.finditer(r"\bit(?: is|'s| was| remains| becomes)\s+(?:\w+\s+){0,2}"
                             r"(important|worth|clear|evident|essential|crucial|notable|interesting|"
                             r"apparent|obvious|vital|imperative|noteworthy|undeniable)\b[^.]{0,30}?\bthat\b", s, re.I):
            hits.append(context(s, m.start(), m.end(), 10))
    return {"count": len(hits), "per_100_sentences": round(100.0 * len(hits) / max(len(d.sentences), 1), 1),
            "hits": hits[:10]}


@metric("triads", "structure", "A",
        "Three-item lists ('X, Y, and Z'). The rule of three; share of sentences containing one.",
        key="share_of_sentences", warn_above=0.15)
def m_triads(d: Doc) -> dict:
    item = r"[\w'-]+(?:\s+[\w'-]+){0,3}"
    pat = re.compile(rf"\b{item},\s+{item},?\s+(?:and|or)\s+{item}")
    hits, sents = [], 0
    for s in d.sentences:
        ms = [m.group(0) for m in pat.finditer(s) if m.group(0).count(",") <= 2]
        if ms:
            sents += 1
            hits += ms
    return {"share_of_sentences": round(sents / max(len(d.sentences), 1), 2), "count": len(hits), "hits": hits[:10]}


@metric("coordination", "grammar", "A",
        "Phrasal coordination density: 'and'/'or' per 1k words and lists of 2+ commas.",
        key="and_per_1k", warn_above=45.0)
def m_coordination(d: Doc) -> dict:
    c = Counter(d.words)
    lists = sum(len(re.findall(r",[^,.;]{1,40},[^,.;]{1,40},?\s+(and|or)\b", s)) for s in d.sentences)
    return {"and_per_1k": d.per_1k(c["and"]), "or_per_1k": d.per_1k(c["or"]), "comma_lists": lists}


@metric("contrast_frames", "structure", "A",
        "Negative parallelism: 'not X, but Y', 'it's not X, it's Y', 'isn't just X', 'not only...but'.",
        key="count", warn_above=1)
def m_contrast(d: Doc) -> dict:
    pats = [
        r"\bnot (just|only|merely|simply|so much)\b[^.?!]{0,80}?\b(but|it'?s|it is|they'?re|—|–)",
        r"\b(it|this|that|which)(?:'s| is| was)(?: not|n't)(?: just| only| merely| simply| really)?\b[^.?!;]{1,60}?[,;—–]\s*(it|this|that)(?:'s| is| was)\b",
        r"\b(isn'?t|aren'?t|wasn'?t) (just|only|merely|simply|about)\b",
        r"\bless about\b[^.]{1,50}\bmore about\b",
        r"\bless (like )?an? \w+(?: \w+)? and more (like )?an?\b",
        r"\brather than (merely|simply|just|relying|focusing)\b",
        r"\b(is|are|was) not (simply|merely)\b", r"\binstead,? (it|this|they) (is|are)\b",
        r"\bthe (question|point|issue|problem|goal) (isn'?t|is not)\b",
        r"^Not\b[^.?!]{1,60}[.?!]\s",
    ]
    hits = []
    for s in d.sentences:
        for p in pats:
            m = re.search(p, s, re.I)
            if m:
                hits.append(context(s, m.start(), m.end(), 15))
                break
    for a, b in zip(d.sentences, d.sentences[1:]):           # "It's not X. It's Y."
        if re.match(r"^(it|this|that)(?:'s| is)(?: not|n't)\b", a, re.I) and re.match(r"^(it|this|that)(?:'s| is)\b", b, re.I) \
                and not any(re.search(p, a, re.I) for p in pats):
            hits.append(a[:50] + " / " + b[:40])
    return {"count": len(hits), "per_1k": d.per_1k(len(hits)), "hits": hits[:10]}


@metric("connectives", "grammar", "A",
        "Additive (Additionally/Moreover) vs logical (because/but/so/if) connectives; sentence-initial repeats.",
        key="additive_ratio", warn_above=0.35)
def m_connectives(d: Doc) -> dict:
    low = d.text.lower()
    add = {c: len(re.findall(rf"(^|[.!?]\s+|\n){re.escape(c)}\b", low)) for c in ADDITIVE_CONNECTIVES if c != "also"}
    add["also (initial)"] = len(re.findall(r"(^|[.!?]\s+)also,", low))
    logi = {c: len(re.findall(rf"\b{re.escape(c)}\b", low)) for c in LOGICAL_CONNECTIVES}
    a, l = sum(add.values()), sum(logi.values())
    initial = Counter(words_of(s)[0] for s in d.sentences if words_of(s) and words_of(s)[0] in
                      set(ADDITIVE_CONNECTIVES + LOGICAL_CONNECTIVES + ["overall", "ultimately", "consequently", "thus", "therefore"]))
    return {"additive_ratio": round(a / max(a + l, 1), 2), "additive": a, "logical_per_1k": d.per_1k(l),
            "additive_detail": {k: v for k, v in add.items() if v}, "sentence_initial": initial.most_common(5)}


@metric("stance", "grammar", "A",
        "Epistemic hedges, boosters, and generic hedges ('can potentially'). AI text: few real stance markers.",
        key="generic_hedges", warn_above=1)
def m_stance(d: Doc) -> dict:
    h, g, b = find_all(HEDGES, d.text), find_all(GENERIC_HEDGES, d.text), find_all(BOOSTERS, d.text)
    return {"hedges_per_1k": d.per_1k(len(h)), "boosters_per_1k": d.per_1k(len(b)),
            "generic_hedges": len(g), "generic_hits": g[:8]}


# ---- Grammar: Profile B (Clark, Martin & Mahowald 2026) ---------------------

@metric("inanimate_agents", "grammar", "B",
        "Inanimate/code subjects with animate verbs ('is_file() swallows that', 'this bites'). Heuristic.",
        key="count", warn_above=1)
def m_inanimate(d: Doc) -> dict:
    hits = []
    dets = {"the", "a", "an", "its", "this", "that", "our", "your", "their", "my", "every", "each"}
    pron = {"it", "this", "that", "which", "code"}
    skip = {"also", "just", "quietly", "silently", "happily", "still", "never", "always", "now", "simply"}
    for s in (c for sent in d.sentences for c in re.split(r"[:;,—–()\"]", sent)):
        toks = re.findall(r"[A-Za-z'-]+", s)
        low = [t.lower() for t in toks]
        for i, v in enumerate(low):
            if v not in ANIMATE_VERB_SET or i == 0:
                continue
            j = i - 1
            while j >= 0 and low[j] in skip | {"doesn't", "didn't", "does", "did", "not", "won't", "can't"}:
                j -= 1
            if j < 0:
                continue
            noun = low[j]
            if noun in pron and (j == 0 or low[j - 1] not in ("to", "of", "about", "that")):
                hits.append(" ".join(toks[j:i + 1]))
                continue
            if noun in FUNCTION_WORDS or noun in PERSON_NOUNS or toks[j][:1].isupper() and j > 0:
                continue
            k = j - 1
            while k >= 0 and j - k <= 3 and low[k] not in dets:
                if low[k] in FUNCTION_WORDS:
                    k = -1
                    break
                k -= 1
            if k >= 0 and low[k] in dets:
                hits.append(" ".join(toks[k:i + 1]))
    return {"count": len(hits), "per_1k": d.per_1k(len(hits)), "hits": hits[:10]}


@metric("denominal_verbs", "grammar", "B",
        "Nouns used as verbs / jargon conversions ('surfaced the error', 'gated behind', 'landed the fix').",
        key="per_1k", warn_above=2.0)
def m_denominal(d: Doc) -> dict:
    h = find_all(DENOMINAL_VERBS, d.text)
    return {"per_1k": d.per_1k(len(h)), "count": len(h), "hits": Counter(x.lower() for x in h).most_common(10)}


@metric("noun_stacks", "grammar", "B",
        "Runs of 3+ noun-like words ('retry budget exhaustion handling'). Heuristic; --spacy for parser.",
        key="per_1k", warn_above=8.0)
def m_noun_stacks(d: Doc) -> dict:
    hits = []
    for s in d.sentences:
        for chunk in re.split(r"[^\w\s'-]", s):
            toks = chunk.split()
            run = []

            def close(run, nxt):
                # a final -s word followed by an object determiner is probably a verb ("wrapper swallows the")
                if run and nxt in OBJECT_STARTERS and re.search(r"[^s]s$", run[-1].lower()):
                    run = run[:-1]
                if len(run) >= 3:
                    hits.append(" ".join(run))

            for i, tok in enumerate(toks):
                w = tok.lower()
                # gerunds count as nouns only at the end of an existing noun run ("exhaustion handling")
                gerund_head = w.endswith("ing") and len(run) >= 2
                nounish = (w.isalpha() or "-" in w) and w not in FUNCTION_WORDS and w not in COMMON_NON_NOUNS \
                    and (gerund_head or not w.endswith(NOUN_STACK_BLOCK_SUFFIX)) and not tok[:1].isupper() and len(w) > 2
                if nounish:
                    run.append(tok)
                else:
                    close(run, w)
                    run = []
            close(run, "")
    return {"per_1k": d.per_1k(len(hits)), "count": len(hits), "hits": hits[:12], "method": "heuristic"}


@metric("hyphen_compounds", "lexicon", "B",
        "Hyphenated multiword coinages ('reader-patience budget', 'load-bearing'). Proxy for unattested bigrams.",
        key="per_1k", warn_above=12.0)
def m_hyphen(d: Doc) -> dict:
    h = re.findall(r"\b[a-z]+(?:-[a-z]+)+\b", d.text)
    return {"per_1k": d.per_1k(len(h)), "count": len(h), "hits": Counter(h).most_common(12)}


@metric("unattested_bigrams", "lexicon", "B",
        "Content-word bigrams absent from the --baseline corpus (needs a large human baseline to be meaningful).",
        key="rate", warn_above=None)
def m_unattested(d: Doc, baseline: Doc | None = None) -> dict:
    if baseline is None:
        return {"rate": None, "note": "requires --baseline (ideally 50k+ words of human text in the genre)"}

    def bigrams(doc):
        out = []
        for s in doc.sentences:
            ws = words_of(s)
            out += [(a, b) for a, b in zip(ws, ws[1:]) if a not in FUNCTION_WORDS and b not in FUNCTION_WORDS]
        return out
    ref = set(bigrams(baseline))
    mine = bigrams(d)
    novel = [f"{a} {b}" for a, b in mine if (a, b) not in ref]
    return {"rate": round(len(novel) / max(len(mine), 1), 3), "content_bigrams": len(mine),
            "baseline_bigram_types": len(ref), "examples": Counter(novel).most_common(12)}


@metric("dropped_that", "grammar", "B",
        "Omitted optional 'that' after complement verbs and in object relatives ('the files we changed').",
        key="drop_ratio", warn_above=0.75)
def m_dropped_that(d: Doc) -> dict:
    cverbs = "|".join(COMPLEMENT_VERBS)
    dropped, kept, rel_drop, rel_kept, hits = 0, 0, 0, 0, []
    for s in d.sentences:
        low = s.lower()
        for m in re.finditer(rf"\b({cverbs})\s+(that\s+)?((?:[a-z'-]+\s+){{1,4}}?)([a-z']+)\b", low):
            if m.group(4) in FINITE_CUES:
                if m.group(2):
                    kept += 1
                else:
                    first = m.group(3).split()[0] if m.group(3).split() else ""
                    if first not in ("to", "that", "how", "what", "why", "if", "whether", "when", "where"):
                        dropped += 1
                        hits.append("complement: " + context(s, m.start(), m.end(), 10))
        for m in re.finditer(r"\b(the|a|an|this|these|those|any|every|some|all)\s+(?:[a-z-]+\s+){0,2}?([a-z-]+)\s+"
                             r"(that\s+|which\s+)?(i|you|we|they|he|she|people|users)\s+([a-z']+)\b", low):
            if m.group(2) in FUNCTION_WORDS or m.group(5) in ("and", "or", "are", "is", "were", "was"):
                continue
            if m.group(3):
                rel_kept += 1
            else:
                rel_drop += 1
                hits.append("relative: " + context(s, m.start(), m.end(), 10))
    tot_d, tot_k = dropped + rel_drop, kept + rel_kept
    return {"drop_ratio": round(tot_d / max(tot_d + tot_k, 1), 2) if tot_d + tot_k >= 3 else None,
            "complement_dropped": dropped, "complement_kept": kept,
            "relative_dropped": rel_drop, "relative_kept": rel_kept, "hits": hits[:10], "method": "heuristic"}


@metric("dependency_proxy", "grammar", "B",
        "Longest punctuation-free span per sentence (proxy for long dependencies). --spacy: true dep distance.",
        key="share_long_spans", warn_above=0.20)
def m_dep_proxy(d: Doc) -> dict:
    spans = []
    for s in d.sentences:
        segs = [len(words_of(x)) for x in re.split(r"[,;:—–()]", s)]
        spans.append(max(segs) if segs else 0)
    if not spans:
        return {"share_long_spans": 0.0}
    return {"share_long_spans": round(sum(1 for x in spans if x >= 22) / len(spans), 2),
            "mean_longest_span": round(statistics.mean(spans), 1), "method": "heuristic"}


@metric("symbol_prose", "punctuation", "B",
        "Arrows, 'w/', '&', slashes and '+' standing in for verbs and connectives in prose.",
        key="per_1k", warn_above=3.0)
def m_symbol(d: Doc) -> dict:
    pats = {"arrows": r"(→|->|=>|⇒|←)", "w/": r"\bw/o?\b", "ampersand": r" & ",
            "slash_pairs": r"\b[a-z]+/[a-z]+\b", "plus": r" \+ "}
    out = {k: len(re.findall(p, d.text)) for k, p in pats.items()}
    total = sum(out.values())
    return {"per_1k": d.per_1k(total), **out}


# ---- Rhetorical moves (Wikipedia AI Cleanup; blader/humanizer) -------------

@metric("copula_avoidance", "grammar", "A",
        "'serves as', 'stands as', 'boasts', 'represents' where plain 'is/has' would do.",
        key="per_1k", warn_above=2.0)
def m_copula(d: Doc) -> dict:
    pats = [r"serv(e|es|ed|ing) as (a|an|the)", r"stand(s|ing)? as (a|an|the)", r"function(s|ed)? as (a|an|the)",
            r"act(s|ed)? as (a|an|the) (key|crucial|vital|central|powerful)", r"boast(s|ed|ing)?",
            r"represent(s|ed)? (a|an) (significant|major|key|pivotal|important|new)",
            r"(offers|provides|features) (a|an) (wide|rich|diverse|range|variety|robust|seamless|comprehensive)"]
    h = find_all(pats, d.text)
    return {"per_1k": d.per_1k(len(h)), "count": len(h), "hits": h[:10]}


@metric("staged_reveals", "structure", "A",
        "Run-ups and drama: 'Here's the thing:', 'The result? X.', 'The kicker:', short punchy paragraph closers.",
        key="count", warn_above=1)
def m_staged(d: Doc) -> dict:
    hits = []
    pats = [r"\bhere'?s (the thing|the kicker|the catch|the twist|where it gets|what (matters|happened|you need))\b",
            r"\b(the|my) (result|answer|kicker|catch|twist|punchline|takeaway|bottom line|upshot)( here)?\s*[?:]",
            r"\b(but|and) (here'?s|that'?s) (the|where)\b", r"^(spoiler|plot twist|enter)\b",
            r"\blet that sink in\b", r"\b(and|but) honestly\?", r"\bthe best part\?"]
    for s in d.sentences:
        for p in pats:
            m = re.search(p, s, re.I)
            if m:
                hits.append(context(s, m.start(), m.end(), 15))
                break
    closers = 0
    for p in d.paragraphs:
        ss = split_sentences(p)
        if len(ss) >= 3:
            last = words_of(ss[-1])
            prev = statistics.mean(len(words_of(x)) for x in ss[:-1])
            if len(last) <= 6 and prev >= 10 and re.match(r"^(that|this|it|and|which|the|so)\b", ss[-1], re.I):
                closers += 1
                hits.append("closer: " + ss[-1])
    return {"count": len(hits), "punchy_closers": closers, "hits": hits[:10]}


NUMBER_WORDS = "one two three four five six seven eight nine ten eleven twelve several both zero".split()
VERB_CUES = re.compile(r"\b(is|are|was|were|be|been|being|am|has|have|had|do|does|did|will|would|can|could|"
                       r"should|shall|may|might|must|need|needs|needed|'s|'re|'ve|'ll|'d|n't|"
                       r"came|went|got|made|took|saw|ran|said|found|gave|knew|left|felt|kept|held|brought|began|"
                       r"broke|built|chose|fell|grew|led|lost|meant|met|paid|sent|showed|spent|stood|told|thought|"
                       r"won|wrote|let|works|runs|fails|passes|returns|covers|scans|protects|holds|uses|takes|"
                       r"makes|gets|keeps|needs|means|shows|looks|seems|stays|set|use|add|check|run|look|make|try|keep|see|suspect|avoid|call|pick|start|stop)\b|\b[a-z]{3,}ed\b", re.I)


@metric("count_fragments", "structure", "B",
        "Verbless count-led or headline fragments: 'Two findings, one significant.' 'One deliverable, ready to use.'",
        key="count", warn_above=0)
def m_count_fragments(d: Doc) -> dict:
    """Block language / headlinese in running prose: a numeral + noun phrase with no finite verb in its
    main clause, or a very short sentence with no finite verb at all."""
    hits = []
    nums = "|".join(NUMBER_WORDS) + r"|a few|\d+"
    for s in d.sentences:
        ws = words_of(s)
        if not ws or len(ws) > 14:
            continue
        head = re.split(r"[,:;—–]", s)[0]
        if re.match(rf"^\s*(?:{nums})\s+[\w'-]+(?:\s+[\w'-]+)?\s*[,:;—–.]", s, re.I) and not VERB_CUES.search(head):
            hits.append(s[:80])
        elif (len(ws) <= 8 and "," in s and s.rstrip().endswith(".") and not VERB_CUES.search(s)
              and not re.match(r"^\s*(yes|no|ok|okay|sure|thanks|so|well|now|then|also|still)\b", s, re.I)):
            hits.append(s[:80])           # "Fixed, two caveats." / "Clean diff, small blast radius."
    return {"count": len(hits), "per_100_sentences": round(100.0 * len(hits) / max(len(d.sentences), 1), 1),
            "hits": hits[:10]}


AUX_STRAND = re.compile(r"\b(is|are|was|were|am|do|does|did|can|could|will|would|should|shall|may|might|must|has|have|had)"
                        r"(n't| not)?\s*[.!]$|\b(isn't|aren't|wasn't|weren't|don't|doesn't|didn't|can't|won't|"
                        r"wouldn't|shouldn't|hasn't|haven't|hadn't)\s*[.!]$|\b(do so|does too|did too)\s*[.!]$", re.I)
BARE_DEICTIC_END = re.compile(r"\b(this|that|these|those)\s*[.!]$", re.I)   # 'it' is usually a concrete referent
WH_WORDS = re.compile(r"\b(what|which|who|whom|how|where|whatever|wherever|when|why)\b", re.I)
GNOMIC_END = re.compile(r"\b(nothing|nobody|no one|none|everything|everyone|anything)\s*[.!]$|"
                        r"\bnever (works|helps|matters|lasts|scales|ends well)\s*[.!]$|"
                        r"\b(itself|themselves)\s*[.!]$|"                                   # "None of this fixes itself."
                        r"\b(less|more) than (people|you|most people|anyone|we|they) (think|expect|realize|assume)\b|"
                        r"^(none|all|most|much|some) of (this|that|it)\b", re.I)
DEICTIC = re.compile(r"\b(this|that|it|these|those|which)\b(?!\s+(?!is\b|was\b|are\b|isn't\b|matters\b|means\b|works\b)[a-z]{3,})", re.I)
VERDICT_VERBS = re.compile(r"\b(matters?|counts?|works|helps|holds|wins|fails|breaks|helps|protects|changes|solves|"
                           r"saves|costs|pays|bites|hurts|stings|adds up|follows)\b", re.I)


def _stem(w: str) -> str:
    for suf in ("ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w


@metric("echo_fragments", "rhythm", "both",
        "Short sentences that add a verdict but no new content: stranded auxiliaries ('Most POSTs aren't.'), "
        "gnomic negations ('...protects nothing.'), and deictic verdicts ('Check your script for this.', "
        "'That matters.'). Fake burstiness: rhythm without information.",
        key="count", warn_above=1)   # human web text: 0.15/1k, 10% of articles have one
def m_echo(d: Doc) -> dict:
    hits, short, content_short = [], 0, 0
    sents = d.sentences
    for i, s in enumerate(sents):
        ws = words_of(s)
        if not ws or len(ws) > 9 or s.rstrip().endswith((":", "?")) or re.match(r'^\s*["“]', s):
            continue
        short += 1
        prev = set()
        for p in sents[max(0, i - 2):i]:
            prev |= {_stem(w) for w in words_of(p) if w not in FUNCTION_WORDS}
        content = [w for w in ws if w not in FUNCTION_WORDS and w not in ("code", "url")]
        nums = re.findall(r"\d+", s)                      # numbers are new content
        new = [w for w in content if _stem(w) not in prev] + nums
        novelty = len(new) / (len(content) + len(nums)) if (content or nums) else 0.0
        reason = None
        m_aux = AUX_STRAND.search(s)
        if m_aux and i > 0 and not WH_WORDS.search(s[:m_aux.start()]):
            reason = "stranded auxiliary (ellipsis)"
        elif re.search(r"\beither\s*[.!]$", s) and len(ws) <= 5 and i > 0:
            reason = "stranded auxiliary (ellipsis)"
        elif GNOMIC_END.search(s):
            reason = "gnomic negation/universal"
        elif BARE_DEICTIC_END.search(s) and i > 0 and len(ws) <= 7:
            reason = "bare deictic end"
        elif DEICTIC.search(s) and novelty <= 0.5 and i > 0:
            reason = "deictic verdict"
        elif i > 0 and content and novelty == 0 and VERDICT_VERBS.search(s):
            reason = "restated verdict"
        if reason:
            hits.append(f"{reason}: {s[:70]}  (new content {round(novelty, 2)})")
        else:
            content_short += 1
    return {"count": len(hits), "short_sentences": short,
            "echo_share_of_short": round(len(hits) / short, 2) if short else None, "hits": hits[:12]}


WH_HEAD = re.compile(r"^(?:#{1,6}\s*)?(?:\*\*)?(what|why|how|here'?s what|here is what|what'?s)\b(?!\s+to\b)[^.!?;,]{2,80}$", re.I)
WH_LABEL = re.compile(r"^(?:\*\*)?(what|why|how)\b(?!\s+to\b)(?:\s+\S+){1,5}?\s*(?:\*\*)?:\s+\S", re.I)


@metric("wh_headings", "structure", "both",
        "Headings and stand-alone lines built as wh-clauses ('Why X Matters', 'How X Works', 'What the Survey Found'), "
        "plus wh-label run-ups ('Why the split: ...'). 'How to ...' is excluded (common in human instructions). "
        "Graphite: 7% of human articles vs 14-80% for all 9 models (Opus 4 16% -> Opus 5 63%); ELEPHANT advice: "
        "0.1% human vs 7-30% for Claude, Gemini, DeepSeek, GPT-5.",
        key="count", warn_above=0)
def m_wh_headings(d: Doc) -> dict:
    hits = []
    for ln in d.lines:
        s = ln.strip()
        if not s or s.startswith("|") or len(s.lstrip("#* ").split()) > 12:
            continue
        core = s.strip("*").strip()
        if WH_HEAD.match(s) or WH_HEAD.match(core):
            hits.append("heading: " + core[:80])
    for sent in d.sentences:
        if WH_LABEL.match(sent):
            hits.append("label: " + sent[:80])
    return {"count": len(hits), "per_1k": d.per_1k(len(hits)), "hits": hits[:10]}


@metric("meta_reference", "content", "A",
        "Writing about the document instead of its subject: 'This article explores...', 'In this section, we will...'.",
        key="count", warn_above=0)
def m_meta(d: Doc) -> dict:
    pats = [r"(this|the following|in this) (article|post|guide|section|document|essay|piece|overview|tutorial|response|answer)"
            r"( will| we will| we'll| I will| I'll)? (explore|explores|discuss|discusses|cover|covers|examine|examines|"
            r"delve|delves|walk|walks|outline|outlines|provide|provides|aim|aims|look|looks|break|breaks|take|takes)",
            r"(let'?s|we will|we'll) (dive|delve|take a (closer|deep) look|explore|break (it|this) down|unpack)",
            r"without further ado", r"as (mentioned|discussed|noted|stated) (above|earlier|previously|before)",
            r"(below|here) (is|are) (a|an|some|the) (breakdown|overview|summary|few|list)"]
    h = find_all(pats, d.text)
    return {"count": len(h), "hits": h[:10]}


# ---- Graphite 2026 "AI Tells" metrics ---------------------------------------

@metric("word_length", "lexicon", "A",
        "Mean letters per word. Graphite 2026: AI 5.2–5.7 vs human 4.9 on web articles (also a top Reinhart feature).",
        key="mean_letters", warn_above=5.2)
def m_word_length(d: Doc) -> dict:
    lens = [len(re.sub(r"[^a-z]", "", w)) for w in d.words if w not in ("code", "url")]
    lens = [x for x in lens if x]
    if not lens:
        return {"mean_letters": None}
    long = sum(1 for x in lens if x >= 7) / len(lens)
    return {"mean_letters": round(statistics.mean(lens), 2), "skew": skewness(lens),
            "share_7plus_letters": round(long, 2)}


@metric("tradeoff_dodges", "content", "A",
        "'without sacrificing/losing/compromising/requiring': claims of benefit with no cost (Graphite: 2.6–70×).",
        key="count", warn_above=0)
def m_tradeoff(d: Doc) -> dict:
    h = find_all([r"without (requiring|losing|sacrificing|compromising|giving up|breaking the bank|the (need|hassle))",
                  r"(all )?while (still )?(maintaining|preserving|keeping)",
                  r"the best of both worlds"], d.text)
    return {"count": len(h), "per_1k": d.per_1k(len(h)), "hits": h[:10]}


@metric("importance_flags", "content", "A",
        "Announcing importance instead of showing it: 'matters because', 'this distinction matters', 'absolutely essential' (Graphite: 19–357×).",
        key="count", warn_above=0)
def m_importance(d: Doc) -> dict:
    h = find_all([r"(this|the|that) (distinction|difference|nuance|detail|choice|point) matters",
                  r"matters (because|more than|most|here)", r"(why|where|what) (this|it) (really )?matters",
                  r"absolutely (essential|critical|crucial|vital)", r"cannot be overstated",
                  r"(single|arguably the) most (important|critical|significant)"], d.text)
    return {"count": len(h), "per_1k": d.per_1k(len(h)), "hits": h[:10]}


@metric("intensifiers", "lexicon", "A",
        "Intensifier/precision adverbs: absolutely, incredibly, entirely, highly, precisely, every single (Graphite: Gemini ~13× human).",
        key="per_1k", warn_above=4.0)
def m_intensifiers(d: Doc) -> dict:
    h = find_all([r"absolutely", r"incredibly", r"entirely", r"highly", r"exceptionally", r"remarkably",
                  r"enormously", r"immensely", r"truly", r"precisely", r"exactly", r"specifically",
                  r"every single", r"utterly", r"deeply"], d.text)
    return {"per_1k": d.per_1k(len(h)), "count": len(h), "hits": Counter(x.lower() for x in h).most_common(10)}


@metric("mannered_frames", "lexicon", "both",
        "Mannered substitutions: 'a dial worth turning', 'worth sitting with', 'earns its place' (Graphite mannered-prose; Opus 5 ~2.5× human).",
        key="count", warn_above=1)
def m_mannered(d: Doc) -> dict:
    h = find_all([r"(an?|the) \w+ worth (turning|pulling|sitting with|holding|naming|keeping|watching|revisiting)",
                  r"worth sitting with", r"earns? (its|their) (place|keep)", r"does (a lot of|the) (heavy lifting|work)",
                  r"load-bearing", r"(quietly|silently) (doing|carrying|holding)", r"the quiet \w+ of",
                  r"(lives|sits) (upstream|downstream) of", r"pays? (for itself|rent)"], d.text)
    return {"count": len(h), "hits": h[:10]}


@metric("human_markers", "lexicon", "A",
        "Informality markers that appear almost only in human text (Graphite): reader address, casual qualifiers, "
        "anecdote/time refs, enthusiasm, exclamations, parentheses. Low is normal in formal genres.",
        key="per_1k", warn_below=None)
def m_human(d: Doc) -> dict:
    cats = {
        "reader_address": [r"you can'?t", r"did you know", r"you'?ll (want|need|find)", r"if you'?re like me"],
        "first_person": [r"we all know", r"we'?re going to", r"i'?ve (been|seen|found|tried)", r"in my experience"],
        "casual_qualifiers": [r"pretty (much|good|sure|easy|hard|bad)", r"sort of", r"kind of", r"a bit", r"a lot"],
        "anecdote_time": [r"(he|she|they) said", r"years ago", r"last (year|week|month)", r"the other day", r"back (then|in)"],
        "personal": [r"my (favorite|favourite|mom|dad|wife|husband|kids?|friend)", r"mom", r"dad"],
        "enthusiasm": [r"love to", r"excited to", r"can'?t wait", r"so (cool|fun|good)"],
    }
    out = {k: len(find_all(v, d.text)) for k, v in cats.items()}
    out["exclamations"] = d.text.count("!")
    out["parentheticals"] = d.text.count("(")
    total = sum(out.values())
    return {"per_1k": d.per_1k(total), **out}


@metric("js_divergence", "lexicon", "both",
        "Jensen–Shannon divergence of word distributions vs --baseline (0 = identical, 1 = disjoint). Graphite's model-vs-human measure.",
        key="jsd", warn_above=None)
def m_jsd(d: Doc, baseline: Doc | None = None) -> dict:
    if baseline is None:
        return {"jsd": None, "note": "requires --baseline (human writing in the same genre/topic)"}
    p, q = Counter(d.words), Counter(baseline.words)
    np_, nq = sum(p.values()) or 1, sum(q.values()) or 1
    jsd = 0.0
    contrib = []
    for w in set(p) | set(q):
        a, b = p[w] / np_, q[w] / nq
        m = (a + b) / 2
        c = (a * math.log2(a / m) if a else 0) + (b * math.log2(b / m) if b else 0)
        jsd += c / 2
        contrib.append((w, round(c / 2, 5), "over" if a > b else "under"))
    contrib.sort(key=lambda x: -x[1])
    return {"jsd": round(jsd, 3), "top_contributors": [f"{w} ({k})" for w, _, k in contrib[:12]]}


@metric("sentence_shape", "rhythm", "both",
        "Skew and max of sentence lengths. Humans: a long right tail (skew 1.1, longest ~74 words); current "
        "models: symmetric and capped (skew 0.24-0.45, longest 32-40). Needs 15+ sentences.",
        key="skew", warn_below=0.5)
def m_sentence_shape(d: Doc) -> dict:
    lens = [len(words_of(s)) for s in d.sentences]
    if len(lens) < 15:
        return {"skew": None, "max": max(lens) if lens else None, "note": "fewer than 15 sentences"}
    srt = sorted(lens)
    return {"skew": skewness(lens), "max": srt[-1], "p90": srt[int(0.9 * (len(srt) - 1))],
            "share_over_35_words": round(sum(1 for x in lens if x > 35) / len(lens), 2)}


@metric("bookend_echo", "structure", "A",
        "Ending that mirrors the opening (content-word overlap of first and last paragraph). Graphite: "
        "20-32% of model articles vs 12% of human ones.",
        key="jaccard", warn_above=0.25)
def m_bookend(d: Doc) -> dict:
    if len(d.paragraphs) < 3:
        return {"jaccard": None, "note": "fewer than 3 paragraphs"}
    def cw(p):
        return {w for w in words_of(p) if w not in FUNCTION_WORDS and len(w) > 3}
    a, b = cw(d.paragraphs[0]), cw(d.paragraphs[-1])
    if not a or not b:
        return {"jaccard": 0.0}
    shared = sorted(a & b)
    return {"jaccard": round(len(a & b) / len(a | b), 2), "shared": shared[:12]}


@metric("concessive_frames", "grammar", "A",
        "Sentence-initial concessive setups: 'While X, Y', 'Although X, Y', 'Despite X, Y'. Graphite: 3-11x human.",
        key="count", warn_above=1)
def m_concessive(d: Doc) -> dict:
    hits = [s[:70] for s in d.sentences
            if re.match(r"^(while|although|though|even though|despite|whereas|granted|admittedly|yes)\b[^,]{3,90},", s, re.I)]
    return {"count": len(hits), "per_1k": d.per_1k(len(hits)), "hits": hits[:8]}


# ---- Data-driven model fingerprints (Graphite tells_vs_human) ---------------

LEXICON_PATH = pathlib.Path(__file__).resolve().parent.parent / "references" / "data" / "graphite_tells_lexicon.json"
_LEXICON = None


def tell_lexicon():
    global _LEXICON
    if _LEXICON is None:
        try:
            _LEXICON = json.loads(LEXICON_PATH.read_text())
        except Exception:
            _LEXICON = {}
    return _LEXICON


def _likeness(x: float, toward: float, away: float) -> float | None:
    """Position of rate x on a log scale: 0 at `away`, 1 at `toward` (clipped to [-0.5, 1.5])."""
    if toward <= 0 or away <= 0 or toward == away:
        return None
    v = math.log((x + 0.1) / (away + 0.1)) / math.log((toward + 0.1) / (away + 0.1))
    return round(max(-0.5, min(1.5, v)), 2)


@metric("model_fingerprint", "lexicon", "both",
        "Hits on each model's data-driven tell list (Graphite: >=4x human rate, in >=3% of articles) vs the "
        "expected rate in human and in that model's text. tell_likeness 0 = human rate, 1 = that model's rate. "
        "The human-marker side (we/our/I/said/please, contractions) is genre-dependent and reported separately.",
        key="max_tell_likeness", warn_above=0.5)
def m_fingerprint(d: Doc) -> dict:
    lex = tell_lexicon()
    if not lex:
        return {"max_tell_likeness": None, "note": f"lexicon missing: run scripts/build_tell_lexicon.py ({LEXICON_PATH})"}
    toks = re.findall(r"[a-z]+(?:'[a-z]+)?", d.text.lower().replace("code", " "))
    n = max(len(toks), 1)
    common = set(lex["frame_common_words"])
    masked = [t if t in common else "_" for t in toks]
    grams, mgrams = Counter(), Counter()
    for k in range(1, 8):
        for i in range(len(toks) - k + 1):
            grams[" ".join(toks[i:i + k])] += 1
            mgrams[" ".join(masked[i:i + k])] += 1
    per_model, best = {}, (None, -9)
    for m, e in lex["models"].items():
        def hits(side):
            out = []
            for t in e[side]["terms"]:
                c = (mgrams if t["kind"] == "frame" else grams).get(t["term"], 0)
                if c:
                    out.append((t["term"], c, t["ratio"]))
            return out
        mh, hh = hits("model"), hits("human")
        mrate = 1000.0 * sum(c for _, c, _ in mh) / n
        hrate = 1000.0 * sum(c for _, c, _ in hh) / n
        em, eh = e["model"]["expected_per_1k"], e["human"]["expected_per_1k"]
        like_m = _likeness(mrate, em["model"], em["human"])
        like_h = _likeness(hrate, eh["model"], eh["human"])     # 1 = as few human-markers as the model
        per_model[m] = {"name": lex["names"][m], "tells_per_1k": round(mrate, 1),
                        "expected": f"human {em['human']} / model {em['model']}",
                        "human_markers_per_1k": round(hrate, 1),
                        "expected_human_markers": f"human {eh['human']} / model {eh['model']}",
                        "tell_likeness": like_m, "human_marker_absence": like_h,
                        "top_tells": [f"{t} x{c} ({r or 'inf'}x)" for t, c, r in
                                      sorted(mh, key=lambda x: -x[1] * math.log2(min(x[2] or 1024, 1024)))[:8]]}
        if like_m is not None and like_m > best[1]:
            best = (m, like_m)
    cur = {m: per_model[m] for m in lex.get("current", []) if m in per_model}
    order = sorted(per_model, key=lambda m: -(per_model[m]["tell_likeness"] or -9))
    return {"max_tell_likeness": best[1] if best[0] else None, "closest_model": lex["names"].get(best[0]),
            "ranking": [f"{per_model[m]['name']} {per_model[m]['tell_likeness']}" for m in order],
            "current_models": cur, "tokens": n,
            "note": "web-article norms; under ~300 tokens the rates are noisy"}


# ---- Request-relative checks (Gricean: Relation, Quantity) -----------------

YESNO_Q = re.compile(r"^\s*(is|are|was|were|can|could|should|would|will|do|does|did|has|have|had|am|may|must|isn't|aren't|"
                     r"doesn't|don't|can't|shouldn't)\b", re.I)
DIRECT_START = re.compile(r"^\s*(yes|no|nope|yeah|yep|not|never|always|usually|generally|mostly|probably|likely|"
                          r"unlikely|absolutely|definitely|sure|it depends|depends|only if|only when|in most cases|"
                          r"short answer)\b", re.I)


def _cw(text: str) -> set:
    return {_stem(w) for w in words_of(text) if w not in FUNCTION_WORDS and len(w) > 2 and w not in ("code", "url")}


@metric("request_fit", "content", "both",
        "Reply vs the request (needs --prompt): does the first sentence restate the question, does the last "
        "sentence recap it, how much of the reply is new content, length relative to the ask, and whether a "
        "yes/no question gets a direct first sentence.",
        key="restates_question", warn_above=0)
def m_request_fit(d: Doc, prompt: str | None = None) -> dict:
    if not prompt:
        return {"restates_question": None, "note": "requires --prompt (the question or request this text answers)"}
    q = _cw(prompt)
    S = d.sentences
    if not S or not q:
        return {"restates_question": None}
    first, last = _cw(S[0]), _cw(S[-1])
    first_from_q = len(first & q) / len(first) if first else 0.0
    restates = int(len(first) >= 3 and first_from_q >= 0.6)
    opening = q | _cw(" ".join(S[:2]))
    last_recap = len(last & opening) / len(last) if last else 0.0
    recap = int(len(S) >= 4 and len(last) >= 4 and last_recap >= 0.7)
    body = _cw(d.text)
    novelty = len(body - q) / len(body) if body else 0.0
    qwords = max(len(words_of(prompt)), 1)
    yesno = bool(YESNO_Q.match(prompt.split("?")[0].split(".")[-1].strip() or prompt))
    direct = bool(DIRECT_START.match(S[0])) if yesno else None
    return {"restates_question": restates, "first_sentence_from_question": round(first_from_q, 2),
            "closing_recap": recap, "last_sentence_overlap_with_opening": round(last_recap, 2),
            "novelty": round(novelty, 2), "length_ratio": round(len(d.words) / qwords, 1),
            "yes_no_question": yesno, "direct_first_sentence": direct, "words": len(d.words),
            "length_ref": "HC3 median reply words, human / ChatGPT-3.5: ELI5 98/174, open QA 39/107, "
                          "finance 137/209, medicine 78/186; current Claude ~2x human on the same questions"}


# ---- Person / register ------------------------------------------------------

@metric("pronouns", "lexicon", "A",
        "1st/2nd person pronoun rates (involvement) and 'their' (over-used by LLMs).",
        key="involved_per_1k", warn_below=None)
def m_pronouns(d: Doc) -> dict:
    c = Counter(d.words)
    fs = sum(c[w] for w in ("i", "me", "my", "mine", "i'm", "i've", "i'd", "i'll"))
    fp = sum(c[w] for w in ("we", "us", "our", "ours", "we're", "we've", "we'll", "let's"))
    sp = sum(c[w] for w in ("you", "your", "yours", "you're", "you've", "you'll", "you'd"))
    return {"involved_per_1k": d.per_1k(fs + fp + sp), "first_singular_per_1k": d.per_1k(fs),
            "first_plural_per_1k": d.per_1k(fp), "second_per_1k": d.per_1k(sp), "their_per_1k": d.per_1k(c["their"])}


@metric("contractions", "lexicon", "A",
        "Contraction rate vs expandable full forms ('do not', 'it is'). Near zero = formal/LLM default.",
        key="contraction_share", warn_below=None)
def m_contractions(d: Doc) -> dict:
    con = len(re.findall(r"\b\w+(n't|'re|'ve|'ll|'d|'m)\b|\b(it|that|there|here|what|let|he|she|who)'s\b", d.text, re.I))
    full = len(re.findall(r"\b(do|does|did|is|are|was|were|have|has|had|would|will|could|should) not\b|\bcannot\b|"
                          r"\b(it|that|there|what) is\b|\b(i|you|we|they) (am|are|have|will)\b", d.text, re.I))
    return {"contraction_share": round(con / max(con + full, 1), 2) if con + full >= 3 else None,
            "contractions_per_1k": d.per_1k(con), "expandable_full_forms": full}


@metric("punctuation", "punctuation", "both",
        "Em dashes, semicolons, colons, parentheses, questions per 1k words; punctuation variety (entropy).",
        key="em_dash_per_1k", warn_above=6.0)
def m_punct(d: Doc) -> dict:
    t = d.text
    em = len(re.findall(r"—|(?<!\d)\s?–\s?(?!\d)|\s--\s", t))   # en dash in number ranges (70–75%) is fine
    marks = {",": t.count(","), ".": t.count("."), ";": t.count(";"), ":": t.count(":"),
             "(": t.count("("), "?": t.count("?"), "!": t.count("!"), "—": em, "'\"": len(re.findall(r"[\"“”]", t))}
    tot = sum(marks.values()) or 1
    ent = -sum((v / tot) * math.log2(v / tot) for v in marks.values() if v)
    curly = len(re.findall(r"[“”‘’]", d.raw))
    straight = len(re.findall(r"(?<!\w)\"|\"(?!\w)", d.raw))
    return {"em_dash_per_1k": d.per_1k(em), "semicolon_per_1k": d.per_1k(marks[";"]),
            "colon_per_1k": d.per_1k(marks[":"]), "paren_per_1k": d.per_1k(marks["("]),
            "question_per_1k": d.per_1k(marks["?"]), "exclaim_per_1k": d.per_1k(marks["!"]),
            "entropy_bits": round(ent, 2), "mixed_quote_styles": bool(curly and straight),
            "unicode_ellipsis": d.raw.count("…")}


@metric("formatting", "structure", "A",
        "Markdown density: headings, bullet-line share, bold spans, emoji, title-case headings.",
        key="bold_per_1k", warn_above=6.0)
def m_formatting(d: Doc) -> dict:
    lines = [l for l in d.lines if l.strip()]
    heads = [l for l in lines if re.match(r"^\s*#{1,6}\s", l)]
    bullets = sum(1 for l in lines if re.match(r"^\s*([-*+]|\d+[.)])\s", l))
    bold = len(re.findall(r"\*\*[^*]+\*\*|__[^_]+__", d.raw))
    emoji = len(re.findall(r"[\U0001F300-\U0001FAFF☀-➿⭐✅]", d.raw))
    def title_case(h):
        ws = [w for w in re.sub(r"^#+\s*", "", h).split() if w.isalpha() and len(w) > 3]
        return len(ws) >= 2 and all(w[0].isupper() for w in ws)
    return {"bold_per_1k": d.per_1k(bold), "headings": len(heads), "title_case_headings": sum(map(title_case, heads)),
            "bullet_line_share": round(bullets / max(len(lines), 1), 2), "emoji": emoji}


# --------------------------------------------------------------------------
# Optional spaCy-backed overrides
# --------------------------------------------------------------------------

def load_spacy():
    try:
        import spacy  # type: ignore
        return spacy.load("en_core_web_sm")
    except Exception as e:  # pragma: no cover
        sys.stderr.write(f"[slop_scan] spaCy unavailable ({e}); using heuristics.\n")
        return None


def spacy_overrides(nlp) -> dict[str, Callable[[Doc], dict]]:
    def parsed(d: Doc):
        if d._nlp_doc is None:
            d._nlp_doc = nlp(d.text)
        return d._nlp_doc

    def noun_stacks(d: Doc) -> dict:
        doc, hits = parsed(d), []
        for tok in doc:
            if tok.pos_ in ("NOUN", "PROPN") and tok.dep_ != "compound":
                comp = [c for c in tok.subtree if c.dep_ == "compound" and c.i < tok.i]
                if len(comp) >= 2:
                    hits.append(doc[comp[0].i: tok.i + 1].text)
        return {"per_1k": d.per_1k(len(hits)), "count": len(hits), "hits": hits[:12], "method": "spacy"}

    def dependency(d: Doc) -> dict:
        doc = parsed(d)
        dists, per_sent = [], []
        for sent in doc.sents:
            ds = [abs(t.i - t.head.i) for t in sent if t.head is not t and not t.is_punct]
            if ds:
                dists += ds
                per_sent.append(max(ds))
        if not dists:
            return {"share_long_spans": 0.0, "method": "spacy"}
        return {"share_long_spans": round(sum(1 for x in per_sent if x >= 16) / len(per_sent), 2),   # ~ human mean + 1 sd
                "mean_dependency_distance": round(statistics.mean(dists), 2),
                "mean_max_distance": round(statistics.mean(per_sent), 1), "method": "spacy"}

    def dropped_that(d: Doc) -> dict:
        doc = parsed(d)
        rel_drop = rel_kept = comp_drop = comp_kept = 0
        hits = []
        for t in doc:
            if t.dep_ == "relcl":
                has_rel = any(c.tag_ in ("WDT", "WP", "WP$", "WRB") or c.lower_ == "that" for c in t.children)
                subj = [c for c in t.children if c.dep_ in ("nsubj", "nsubjpass")]
                is_obj_rel = subj and subj[0].i != t.head.i
                if is_obj_rel:
                    if has_rel:
                        rel_kept += 1
                    else:
                        rel_drop += 1
                        hits.append("relative: " + doc[t.head.i: t.i + 1].text)
            if t.dep_ == "ccomp" and t.head.pos_ == "VERB":
                if any(c.dep_ == "mark" and c.lower_ == "that" for c in t.children):
                    comp_kept += 1
                else:
                    comp_drop += 1
        tot_d, tot_k = rel_drop + comp_drop, rel_kept + comp_kept
        return {"drop_ratio": round(tot_d / max(tot_d + tot_k, 1), 2) if tot_d + tot_k >= 3 else None,
                "relative_dropped": rel_drop, "relative_kept": rel_kept,
                "complement_dropped": comp_drop, "complement_kept": comp_kept, "hits": hits[:10], "method": "spacy"}

    def inanimate(d: Doc) -> dict:
        doc, hits = parsed(d), []
        for t in doc:
            if t.dep_ == "nsubj" and t.head.lemma_.lower() in ANIMATE_VERB_SET | {w.rstrip("s") for w in ANIMATE_VERB_SET}:
                if t.pos_ == "PRON" and t.lower_ not in ("it", "this", "that", "which"):
                    continue
                if t.ent_type_ in ("PERSON", "NORP", "ORG") or t.lemma_.lower() in PERSON_NOUNS:
                    continue
                hits.append(doc[min(t.i, t.head.i): max(t.i, t.head.i) + 1].text)
        return {"count": len(hits), "per_1k": d.per_1k(len(hits)), "hits": hits[:10], "method": "spacy"}

    return {"noun_stacks": noun_stacks, "dependency_proxy": dependency,
            "dropped_that": dropped_that, "inanimate_agents": inanimate}


# --------------------------------------------------------------------------
# Thresholds by genre
# --------------------------------------------------------------------------

GENRE_OVERRIDES: dict[str, dict[str, dict]] = {
    "academic": {"word_length": {"warn_above": None}, "noun_stacks": {"warn_above": None},
                 "dependency_proxy": {"warn_above": None}, "dropped_that": {"warn_above": None}, "nominalizations": {"warn_above": 60.0}, "specificity": {"warn_below": 12.0},
                 "coordination": {"warn_above": 45.0}, "sentence_length": {"warn_below": 0.35}},
    "chat": {"sentence_length": {"warn_below": 0.50}, "repeated_ngrams": {"warn_above": 8.0},
             "echo_fragments": {"warn_above": 3},   # ELEPHANT: humans use more ellipsis in conversational advice "pronouns": {"warn_below": 20.0},
             "contractions": {"warn_below": 0.5}, "formatting": {"warn_above": 2.0},
             "punctuation": {"warn_above": 1.0}, "nominalizations": {"warn_above": 25.0}},
    "code": {"word_length": {"warn_above": None}, "inanimate_agents": {"warn_above": 2}, "repeated_ngrams": {"warn_above": 8.0}, "denominal_verbs": {"warn_above": 1.0},
             "noun_stacks": {"warn_above": 10.0}, "specificity": {"warn_below": None}, "symbol_prose": {"warn_above": 2.0}},
    "fiction": {"participial_clauses": {"warn_above": 20.0}, "sentence_length": {"warn_below": 0.50},
                "nominalizations": {"warn_above": 15.0}, "specificity": {"warn_below": None}},
    "docs": {"pronouns": {"warn_below": 10.0}, "formatting": {"warn_above": 10.0},
             "noun_stacks": {"warn_above": None}, "dependency_proxy": {"warn_above": None}},
    "email": {"pronouns": {"warn_below": 20.0}, "contractions": {"warn_below": 0.3}},
    "essay": {"contractions": {"warn_below": 0.2}, "word_length": {"warn_above": 5.1},
              "noun_stacks": {"warn_above": None}, "dependency_proxy": {"warn_above": None}, "dropped_that": {"warn_above": None}},
    "marketing": {"flagged_vocab": {"warn_above": 1.0}},
}


def run_metric(name: str, d: Doc, baseline: Doc | None = None, impl: dict | None = None,
               prompt: str | None = None) -> dict:
    fn = (impl or {}).get(name) or METRICS[name].fn
    if name in ("unattested_bigrams", "js_divergence"):
        return fn(d, baseline)
    if name == "request_fit":
        return fn(d, prompt)
    return fn(d)


def flag(name: str, result: dict, genre: str | None) -> str | None:
    m = METRICS[name]
    above, below = m.warn_above, m.warn_below
    ov = GENRE_OVERRIDES.get(genre or "", {}).get(name, {})
    above = ov.get("warn_above", above)
    below = ov.get("warn_below", below)
    v = result.get(m.key)
    if v is None:
        return None
    if above is not None and v > above:
        return f"{m.key}={v} > {above}"
    if below is not None and v < below:
        return f"{m.key}={v} < {below}"
    return None


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

LAYER_ORDER = ["content", "structure", "grammar", "rhythm", "lexicon", "punctuation"]


def read(path: str) -> str:
    return sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()


def fmt_val(v) -> str:
    if isinstance(v, list):
        if not v:
            return "—"
        return " | ".join(f"{x[0]} ×{x[1]}" if isinstance(x, (list, tuple)) and len(x) == 2 else str(x) for x in v)
    if isinstance(v, dict):
        return ", ".join(f"{k}={x}" for k, x in v.items()) or "—"
    return str(v)


def render(results: dict, flags: dict, base: dict | None, show_hits: int, show_refs: bool = True) -> str:
    out = []
    n_flag = sum(1 for f in flags.values() if f)
    out.append(f"slop_scan: {n_flag} metric(s) flagged out of {len(flags)}\n")
    for layer in LAYER_ORDER:
        names = [n for n in results if METRICS[n].layer == layer]
        if not names:
            continue
        out.append(f"## {layer}")
        for n in names:
            r, m = results[n], METRICS[n]
            mark = "⚠" if flags.get(n) else "·"
            head = r.get(m.key)
            delta = ""
            if base and n in base and isinstance(head, (int, float)) and isinstance(base[n].get(m.key), (int, float)):
                delta = f"  (baseline {base[n][m.key]})"
            out.append(f"{mark} {n} [{m.profile}] {m.key}={head}{delta}" + (f"   <- {flags[n]}" if flags.get(n) else ""))
            for fld, rk in REF_FIELDS.get(n, {}).items():
                if fld in r and r[fld] is not None and show_refs:
                    ref = GRAPHITE_REF[rk]
                    out.append(f"      {fld}={r[fld]}  ref: human {ref['human']} | opus5 {ref['opus5']} | "
                               f"astra {ref['astra']} | gemini3.1 {ref['gemini31']}")
            ref_shown = set(REF_FIELDS.get(n, {})) if show_refs else set()
            for k, v in r.items():
                if k == m.key or k in ref_shown:
                    continue
                if k in ("hits", "top", "examples", "generic_hits", "3gram", "4gram", "top5") and show_hits:
                    vv = v[:show_hits] if isinstance(v, list) else v
                    out.append(f"      {k}: {fmt_val(vv)}")
                elif k not in ("hits", "top", "examples", "generic_hits", "3gram", "4gram", "top5"):
                    out.append(f"      {k}: {fmt_val(v)}")
        out.append("")
    out.append("Profiles: A = bloated/informational, B = over-compressed/jargon. "
               "Flags are prompts to read closely, not verdicts. See references/patterns.md.")
    return "\n".join(out)


# --------------------------------------------------------------------------
# Agent aides: anchored output, own-family tells, regression mode
# --------------------------------------------------------------------------

# metric -> section of references/patterns.md that holds the rewrite move
PATTERN_REF = {
    "stock_phrases": "1.1-1.4", "vague_references": "1.5", "meta_reference": "1.6b", "staged_reveals": "1.6c",
    "tradeoff_dodges": "1.6d", "importance_flags": "1.6e", "bookend_echo": "1.6f", "concessive_frames": "1.6g",
    "specificity": "1.7", "triads": "2.1", "contrast_frames": "2.2", "paragraph_rhythm": "2.3", "formatting": "2.4",
    "participial_clauses": "3.1", "nominalizations": "3.2", "that_subjects": "3.3", "copula_avoidance": "3.3b",
    "coordination": "3.4", "connectives": "3.5", "sentence_openers": "3.6", "stance": "3.7",
    "inanimate_agents": "4.1", "denominal_verbs": "4.2", "noun_stacks": "4.3", "hyphen_compounds": "4.4",
    "unattested_bigrams": "4.4", "dropped_that": "4.5", "dependency_proxy": "4.6", "symbol_prose": "4.7",
    "count_fragments": "4.8", "wh_headings": "2.4b", "sentence_length": "5.1", "sentence_shape": "5.1b", "echo_fragments": "5.1c",
    "repeated_ngrams": "5.2", "flagged_vocab": "6.1", "model_fingerprint": "6.1", "lexical_diversity": "6.2",
    "word_length": "6.2b", "intensifiers": "6.2c", "mannered_frames": "6.2d", "pronouns": "6.3",
    "contractions": "6.3", "human_markers": "7.1b", "punctuation": "7.1", "request_fit": "SKILL.md step 3.1",
}
FAMILIES = {"claude": ["claude-opus-5", "claude-opus-4-6", "claude-opus-4-20250514"],
            "gpt": ["gpt-6-astra", "gpt-5-6-sol", "gpt5", "gpt41"],
            "gemini": ["gemini-3-1-pro-preview", "gemini-2-5-pro"]}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("…", " ").replace("CODE", " ")).strip().lower()


def locate(d: Doc, hit) -> list[int]:
    """Indices of sentences that contain a hit (a snippet, a word, or a (word, count) pair)."""
    if isinstance(hit, (list, tuple)):
        hit = hit[0]
    h = str(hit)
    h = re.sub(r"^[a-z_ ]+: ", "", h)                       # "editorializing: ..." / "complement: ..."
    h = re.sub(r"\s+\(new content [\d.]+\)$", "", h)
    h = re.sub(r"\s+x\d+ \([^)]*\)$", "", h)                  # fingerprint "term x2 (15.4x)"
    h = re.sub(r" ×\d+$", "", h)
    pieces = [p for p in re.split(r"…| / ", h) if len(p.strip()) >= 3]
    if not pieces:
        return []
    key = _norm(max(pieces, key=len))[:60]
    out = []
    if " _ " in f" {key} ":                                    # Graphite frame: "_" is one word
        pat = re.compile(r"\b" + r"\s+".join(r"[a-z']+" if w == "_" else re.escape(w) for w in key.split()) + r"\b")
        return [i for i, s in enumerate(d.sentences) if pat.search(_norm(s))]
    for i, s in enumerate(d.sentences):
        ns = _norm(s)
        if key and key in ns:
            out.append(i)
        elif len(key.split()) <= 3 and re.search(rf"\b{re.escape(key)}\b", ns):
            out.append(i)
    return out


def own_family_tells(d: Doc, family: str, top: int = 12) -> list[dict]:
    """Tells from the latest model of `family` that occur in the text, with sentence anchors."""
    lex = tell_lexicon()
    if not lex or family not in FAMILIES:
        return []
    common = set(lex["frame_common_words"])
    found = {}
    for m in FAMILIES[family]:
        if m not in lex["models"]:
            continue
        for t in lex["models"][m]["model"]["terms"]:
            if t["term"] in found:
                continue
            if t["kind"] == "frame":
                parts = [r"[a-z']+" if p == "_" else re.escape(p) for p in t["term"].split()]
                pat = re.compile(r"\b" + r"\s+".join(parts) + r"\b", re.I)
            else:
                pat = re.compile(r"\b" + re.escape(t["term"]) + r"\b", re.I)
            sents = [i for i, s in enumerate(d.sentences) if pat.search(s.replace("’", "'"))]
            if t["kind"] == "frame":   # the blank must be an uncommon word, as in Graphite's frames
                sents = [i for i in sents if any(w.lower() not in common for w in
                                                 re.findall(r"[A-Za-z']+", pat.search(d.sentences[i]).group(0)))]
            if sents:
                found[t["term"]] = {"term": t["term"], "ratio": t["ratio"], "model": lex["names"][m],
                                    "sentences": sents[:4], "weight": (t["ratio"] or 1024) * len(sents)}
    return sorted(found.values(), key=lambda x: -math.log2(min(x["weight"], 4096)))[:top]


def agent_report(d: Doc, results: dict, flags: dict, self_family: str | None, max_hits: int = 4) -> str:
    """Compact, sentence-anchored report for an agent doing the pass: flagged metrics only, durable first."""
    lines = [f"{len(d.words)} words, {len(d.sentences)} sentences. Sentences are numbered s0..s{len(d.sentences) - 1}."]
    order = sorted([n for n in results if flags.get(n)], key=lambda n: (n not in DURABLE, n))
    used = set()
    for n in order:
        r = results[n]
        tag = "durable" if n in DURABLE else METRICS[n].profile
        lines.append(f"FLAG {n} [{tag}] {flags[n]}  -> fix: patterns.md {PATTERN_REF.get(n, '?')}")
        hits = r.get("hits") or r.get("top") or r.get("top_tells") or []
        if n == "model_fingerprint":
            cm = r.get("current_models") or {}
            best = max(cm.values(), key=lambda v: v["tell_likeness"] or -9) if cm else None
            hits = best["top_tells"] if best else []
        shown = 0
        for h in hits:
            idx = locate(d, h)
            label = h[0] if isinstance(h, (list, tuple)) else str(h)
            if idx:
                for i in idx[:2]:
                    lines.append(f"  s{i}: {d.sentences[i][:160]}")
                    used.add(i)
                lines[-1] += f"   [{label[:50]}]"
            else:
                lines.append(f"  (doc-level) {label[:110]}")
            shown += 1
            if shown >= max_hits:
                break
        if not hits:
            extra = {k: v for k, v in r.items() if isinstance(v, (int, float)) and k != METRICS[n].key}
            if extra:
                lines.append("  " + ", ".join(f"{k}={v}" for k, v in list(extra.items())[:5]))
    if "request_fit" in results and results["request_fit"].get("words") is not None:
        rf = results["request_fit"]
        lines.append(f"REQUEST words={rf['words']} ratio={rf['length_ratio']}x restates={rf['restates_question']} "
                     f"recap={rf['closing_recap']}  ({rf['length_ref']})")
    if self_family:
        tells = own_family_tells(d, self_family)
        lines.append(f"SELF ({self_family}): {len(tells)} of your family's tells in this text"
                     + (" -- rewrite these first; your revision will add more of them" if tells else ""))
        for t in tells:
            lines.append(f"  '{t['term']}' {t['ratio'] or 'inf'}x ({t['model']}) in " +
                         ", ".join(f"s{i}" for i in t["sentences"]))
    if not order:
        lines.append("No metric flagged.")
    return "\n".join(lines)


def regression_report(before: Doc, after: Doc, names: list[str], genre: str | None, impl: dict,
                      prompt: str | None) -> tuple[str, dict]:
    """What got worse between two drafts: new flags, durable metrics moving away from the human reference,
    echo fragments and own-family tells added, and dropped facts (check_invariants)."""
    rb = {n: run_metric(n, before, None, impl, prompt) for n in names}
    ra = {n: run_metric(n, after, None, impl, prompt) for n in names}
    fb = {n: flag(n, rb[n], genre) for n in names}
    fa = {n: flag(n, ra[n], genre) for n in names}
    new = [n for n in names if fa[n] and not fb[n]]
    fixed = [n for n in names if fb[n] and not fa[n]]
    still = [n for n in names if fa[n] and fb[n]]
    lines = [f"REGRESSION CHECK  before {len(before.words)}w -> after {len(after.words)}w",
             f"fixed {len(fixed)}: {', '.join(fixed) or '-'}",
             f"still flagged {len(still)}: {', '.join(still) or '-'}",
             f"NEW flags {len(new)}: {', '.join(new) or '-'}"]
    for n in new:
        hits = ra[n].get("hits") or []
        for h in hits[:2]:
            for i in locate(after, h)[:1]:
                lines.append(f"  {n} s{i}: {after.sentences[i][:150]}")
    # durable distributional metrics: did they move toward or away from human?
    for n, key, ref in (("word_length", "mean_letters", 4.9), ("lexical_diversity", "mtld", 85.6)):
        if n in names and rb[n].get(key) and ra[n].get(key):
            b, a2 = rb[n][key], ra[n][key]
            if a2 <= ref:
                verdict = f"at or below human {ref}: not a model direction"
            else:
                verdict = f"{'toward' if a2 < b else 'AWAY FROM'} human {ref} (models are higher)"
            lines.append(f"  {n}.{key}: {b} -> {a2} ({verdict})")
    inv = {}
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import check_invariants as ci  # noqa: E402
        inv = ci.compare(before.raw, after.raw)
        lines.append(ci.render(inv, brief=True))
    except ImportError:
        pass
    return "\n".join(lines), {"new": new, "fixed": fixed, "still": still, "invariants": inv}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="text/markdown file, or - for stdin")
    ap.add_argument("-m", "--metric", action="append", help="run only this metric (repeatable)")
    ap.add_argument("--profile", choices=["A", "B"], help="run only metrics for one slop profile")
    ap.add_argument("--durable", action="store_true",
                    help="run only checks whose direction held across every model generation tested")
    ap.add_argument("--baseline", help="human-written sample to compare against")
    ap.add_argument("--genre", choices=sorted(GENRE_OVERRIDES), help="genre-aware thresholds")
    ap.add_argument("--prompt", help="the request this text answers (a string, or a path to a file); enables request_fit")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--hits", type=int, default=5, help="example hits to show per metric (0 = none)")
    ap.add_argument("--spacy", action="store_true", help="use spaCy parser for B-profile metrics if installed")
    ap.add_argument("--list", action="store_true", help="list available metrics")
    ap.add_argument("--flagged-only", action="store_true", help="report only flagged metrics")
    ap.add_argument("--no-refs", action="store_true", help="hide Graphite human/model reference values")
    ap.add_argument("--agent", action="store_true",
                    help="compact report for an agent: flagged metrics only, durable first, sentence-anchored, with fix refs")
    ap.add_argument("--self", dest="self_family", choices=sorted(FAMILIES),
                    help="also list your own model family's tells in the text, with sentence anchors")
    ap.add_argument("--before", help="earlier draft: report regressions (new flags, dropped facts) from it to FILE")
    a = ap.parse_args(argv)

    if a.list:
        for n, m in METRICS.items():
            thr = []
            if m.warn_above is not None:
                thr.append(f"warn >{m.warn_above}")
            if m.warn_below is not None:
                thr.append(f"warn <{m.warn_below}")
            print(f"{n:22} [{m.profile}] {m.layer:11} {m.key} {' '.join(thr)}\n    {m.description}")
        return 0
    if not a.file:
        ap.error("file required (or --list)")

    names = a.metric or list(METRICS)
    unknown = [n for n in names if n not in METRICS]
    if unknown:
        ap.error(f"unknown metric(s): {', '.join(unknown)}. Use --list.")
    if a.profile:
        names = [n for n in names if METRICS[n].profile in (a.profile, "both")]
    if a.durable:
        names = [n for n in names if n in DURABLE]

    impl = {}
    if a.spacy:
        nlp = load_spacy()
        if nlp:
            impl = spacy_overrides(nlp)

    d = Doc(read(a.file))
    bd = Doc(read(a.baseline)) if a.baseline else None
    prompt = None
    if a.prompt:
        pp = pathlib.Path(a.prompt)
        prompt = pp.read_text(encoding="utf-8") if pp.is_file() else a.prompt
    if a.before:
        text, data = regression_report(Doc(read(a.before)), d, names, a.genre, impl, prompt)
        if a.self_family:
            tb = {t["term"] for t in own_family_tells(Doc(read(a.before)), a.self_family, top=200)}
            added = [t for t in own_family_tells(d, a.self_family, top=200) if t["term"] not in tb]
            text += f"\nSELF ({a.self_family}) tells ADDED by the revision: {len(added)}"
            text += "".join(f"\n  '{t['term']}' {t['ratio'] or 'inf'}x in " + ", ".join(f"s{i}" for i in t["sentences"])
                            for t in added[:12])
            data["self_added"] = [t["term"] for t in added]
        print(json.dumps(data, indent=2, default=str) if a.json else text)
        return 0
    results = {n: run_metric(n, d, bd, impl, prompt) for n in names}
    if a.agent:
        flags = {n: flag(n, results[n], a.genre) for n in names}
        print(agent_report(d, results, flags, a.self_family))
        return 0
    flags = {n: flag(n, results[n], a.genre) for n in names}
    if a.flagged_only:
        results = {n: r for n, r in results.items() if flags[n]}
    base = {n: run_metric(n, bd, None, impl) for n in names if n not in ("unattested_bigrams", "js_divergence")} if bd else None

    if a.json:
        refs = {n: {f: GRAPHITE_REF[k] for f, k in REF_FIELDS[n].items()} for n in results if n in REF_FIELDS}
        print(json.dumps({"words": len(d.words), "sentences": len(d.sentences), "genre": a.genre,
                          "results": results, "flags": flags, "baseline": base, "graphite_ref": refs},
                         indent=2, default=str))
    else:
        print(f"{len(d.words)} words, {len(d.sentences)} sentences, {len(d.paragraphs)} paragraphs"
              + (f", genre={a.genre}" if a.genre else ""))
        print(render(results, flags, base, a.hits, not a.no_refs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
