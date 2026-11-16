#!/usr/bin/env python3
"""Build the bench: scan every before/after pair and write viewer_data.js + viewer_standalone.html.

    python3 evals/build_viewer.py
"""
import csv
import json
import pathlib
import random
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import slop_scan as ss  # noqa: E402

# Real sentence-level fixes from this repo's rewrites (before -> after, with the pattern fixed).
FIXES = [
    ("echo fragment",
     "\"Idempotent\" means doing something twice has the same effect as doing it once. Most POSTs aren't.",
     "\"Idempotent\" means doing something twice has the same effect as doing it once, which isn't true of most POST endpoints."),
    ("maxim",
     "Check your script for this. A new key on each attempt protects nothing.",
     "If your script generates a new key on every attempt, the server treats each retry as a new order."),
    ("own-family tell (85× for Opus 5)",
     "Short TTLs, versioned keys, or deleting the key a second time shortly after the write all close that gap.",
     "Short TTLs, versioned keys, or deleting the key a second time shortly after the write all prevent that race."),
    ("intensifiers, family tells",
     "Short answer: it's safe if the endpoint is truly idempotent, but a timeout is exactly the case where you need to be careful about what \"idempotent\" means in practice.",
     "It's safe only if a retry can't create a second order."),
    ("personified code",
     "The retry wrapper swallows the timeout and the caller never knows the request failed.",
     "When a request times out, the retry wrapper catches the exception and returns `None`, so the caller can't tell that the request failed."),
    ("jargon verbs",
     "Now gated behind `STRICT_RETRY` so we can derisk the rollout.",
     "The new behavior is off by default behind the `STRICT_RETRY` flag, so we can turn it on for a few job types first."),
    ("nominalization, -ing tail",
     "The implementation of remote work policies has led to a significant improvement in employee satisfaction, fostering a sense of autonomy and empowerment.",
     "In most surveys, employees who can work from home report higher satisfaction, mostly because they control their own schedule and skip the commute."),
    ("contrast frame",
     "It's important to note that this shift isn't just about where we work—it's about how we work.",
     ""),
    ("second tells-only pass: lost precision",
     "One example is Google's original **PageRank** algorithm, which treats links as votes of importance.",
     "One example is Google's original **PageRank** algorithm, which treats links as votes."),
    ("fiction slop",
     "The camaraderie among the patrons was palpable, a fleeting tapestry of stories and songs woven amidst the flickering candlelight.",
     "Someone near the fire was losing at dice and taking it badly, and the floor stuck to her boots."),
]


def scan(text, genre):
    d = ss.Doc(text)
    res = {n: ss.run_metric(n, d) for n in ss.METRICS}
    flags = sorted(n for n in ss.METRICS if ss.flag(n, res[n], genre))
    return {"words": len(d.words), "flags": flags, "claude": len(ss.own_family_tells(d, "claude", top=500))}


def detok(t):
    t = re.sub(r" (n't|'s|'re|'ve|'ll|'d|'m)\b", r"\1", t)
    t = re.sub(r" ([.,;:!?%)\]])", r"\1", t)
    return re.sub(r"([(\[$]) ", r"\1", t).strip()


def pair(group, title, genre, prompt, before, after, labels):
    return {"group": group, "title": title, "prompt": prompt, "before": before, "after": after, "labels": labels,
            "sb": scan(before, genre), "sa": scan(after, genre)}


def main():
    pairs = []
    for sid, title, genre in (("essay", "Blog post", "essay"), ("agent", "Agent status", "code"),
                              ("fiction", "Fiction", "fiction")):
        pairs.append(pair("Caricatures", title, genre, "",
                          (ROOT / "examples" / f"{sid}_before.md").read_text(),
                          (ROOT / "examples" / f"{sid}_after.md").read_text(), ["Before", "After"]))
    for s in json.loads((ROOT / "evals" / "scenarios.json").read_text())["scenarios"]:
        pairs.append(pair("Chat replies", s["term"], "chat", s["prompt"],
                          (ROOT / "evals" / "before" / f"{s['id']}.md").read_text(),
                          (ROOT / "evals" / "after" / f"{s['id']}.md").read_text(), ["Before", "After"]))

    # New genres (model default -> one deslop pass)
    gdir = ROOT / "evals" / "genres"
    if (gdir / "items.json").exists():
        for g in json.loads((gdir / "items.json").read_text()):
            bf, af = gdir / "before" / f"{g['id']}.md", gdir / "after" / f"{g['id']}.md"
            if bf.exists() and af.exists():
                grp = "Advice replies" if g["id"].startswith("advice") else "Other genres"
                pairs.append(pair(grp, g["title"], g["genre"], g["prompt"][:600] if grp == "Advice replies" else g["prompt"],
                                  bf.read_text(), af.read_text(), ["Before", "After"]))
    # Held-out answers and A/B inputs, original -> one pass with the aides
    for sub, arm, grp in (("pass2exp", "p1", "Held-out answers"), ("ab", "armB", "More answers")):
        d_ = ROOT / "evals" / sub
        for p in sorted((d_ / "input").glob("*.md")) if (d_ / "input").exists() else []:
            af = d_ / arm / p.name
            if af.exists():
                pairs.append(pair(grp, p.stem.replace("_", " "), "chat", (d_ / "input" / f"{p.stem}.prompt.txt").read_text(),
                                  p.read_text(), af.read_text(), ["Before", "After"]))

    hc3, claude = ROOT / "sources" / "raw" / "hc3_all.jsonl", ROOT / "evals" / "hc3" / "claude_answers.json"
    if hc3.exists() and claude.exists():
        ans = json.loads(claude.read_text())
        qs = {q["id"]: q for q in json.loads((ROOT / "evals" / "hc3" / "sample_questions.json").read_text())}
        index = {}
        for line in open(hc3, encoding="utf-8"):
            r = json.loads(line)
            index[detok(r["question"]).replace("ELI5: ", "", 1)] = r
        for qid, title in (("reddit_eli5-1", "Elevator cable"), ("finance-26", "Finance question")):
            q = qs.get(qid)
            if q and qid in ans and q["question"] in index:
                pairs.append(pair("Compare: human vs model", title, "chat", q["question"], ans[qid],
                                  detok(index[q["question"]]["human_answers"][0]), ["Claude", "Human (HC3)"]))
    el = ROOT / "sources" / "raw" / "elephant" / "elephant_full_results" / "OEQ_full_results.csv"
    if el.exists():
        csv.field_size_limit(10 ** 9)
        rows = [r for r in csv.DictReader(open(el, encoding="utf-8")) if len((r.get("Human") or "").split()) > 80]
        random.Random(2).shuffle(rows)
        for k, r in enumerate(rows[:2]):
            pairs.append(pair("Compare: human vs model", f"Advice {k + 1}", "chat", r["prompt"][:600], r["Claude"], r["Human"],
                              ["Claude", "Human (ELEPHANT)"]))
    ab = ROOT / "evals" / "ab"
    for p in sorted((ab / "input").glob("*.md")) if (ab / "input").exists() else []:
        a_, b_ = ab / "armA" / p.name, ab / "armB" / p.name
        if a_.exists() and b_.exists():
            pairs.append(pair("Compare: plain vs aides", p.stem, "chat", (ab / "input" / f"{p.stem}.prompt.txt").read_text(),
                              a_.read_text(), b_.read_text(), ["Plain report", "With aides"]))

    x = ROOT / "evals" / "pass2exp"
    for p in sorted((x / "p1").glob("*.md")) if (x / "p1").exists() else []:
        p2 = x / "p2" / p.name
        if p2.exists() and p2.read_text() != p.read_text():
            pairs.append(pair("Compare: second pass (rejected)", p.stem, "chat", (x / "input" / f"{p.stem}.prompt.txt").read_text(),
                              p.read_text(), p2.read_text(), ["One pass", "+ tells-only pass"]))

    lex = {"flagged": [p for ps in ss.FLAGGED_VOCAB.values() for p in ps],
           "stock": [p for ps in ss.STOCK_PHRASES.values() for p in ps],
           "denominal": ss.DENOMINAL_VERBS, "animate": sorted(ss.ANIMATE_VERB_SET), "ingNot": sorted(ss.ING_NOT_VERBS)}
    out = ROOT / "evals" / "viewer_data.js"
    out.write_text("window.DESLOP = " + json.dumps({"pairs": pairs, "fixes": FIXES, "lex": lex}) + ";\n")
    html = (ROOT / "evals" / "viewer.html").read_text()
    data = out.read_text().replace("</script", "<\\/script")
    (ROOT / "evals" / "viewer_standalone.html").write_text(
        html.replace('<script src="viewer_data.js"></script>', "<script>\n" + data + "</script>"))
    print(f"wrote {out} and viewer_standalone.html ({len(pairs)} pairs, {len(FIXES)} fixes)")


if __name__ == "__main__":
    main()
