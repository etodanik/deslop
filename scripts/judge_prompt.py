#!/usr/bin/env python3
"""judge_prompt: fill an LLM-judge rubric with a request and a reply, for the agent (or a subagent) to answer.

    python3 judge_prompt.py --rubric validation --prompt question.txt --response reply.md
    python3 judge_prompt.py --rubric all --prompt "How do I..." --response reply.md

Rubrics come from references/judges/elephant_sycophancy.md (ELEPHANT, CC0): validation, indirectness,
framing. Each prompt asks for a single digit. No API calls: the model running the skill judges, ideally in
a fresh subagent that hasn't seen the draft being written.
"""
import argparse
import pathlib
import re
import sys

RUBRICS = pathlib.Path(__file__).resolve().parent.parent / "references" / "judges" / "elephant_sycophancy.md"


def rubrics() -> dict:
    text = RUBRICS.read_text()
    parts = re.split(r"^## (\w+)\s*$", text, flags=re.M)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def fill(name: str, question: str, response: str) -> str:
    return (f"{rubrics()[name]}\n\nQuestion: {question.strip()}\nAdvice: {response.strip()}\n\n"
            "Judge the advice. Answer with the single digit only.")


def _arg(v: str) -> str:
    p = pathlib.Path(v)
    return p.read_text(encoding="utf-8") if p.is_file() else v


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rubric", default="all", choices=["all", "validation", "indirectness", "framing"])
    ap.add_argument("--prompt", required=True, help="the request (string or file)")
    ap.add_argument("--response", required=True, help="the reply (string or file)")
    a = ap.parse_args(argv)
    names = ["validation", "indirectness", "framing"] if a.rubric == "all" else [a.rubric]
    q, r = _arg(a.prompt), _arg(a.response)
    print("\n\n=====\n\n".join(f"[{n}]\n{fill(n, q, r)}" for n in names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
