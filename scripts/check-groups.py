#!/usr/bin/env python3
"""Refuse a groups file that breaks a decide rule.

Usage: python3 -I check-groups.py groups.json PACK_DIR [screen-notes.md ...]

groups.json: a list of groups, or an object with "groups": [...]. Each group:
  {"name", "signals": [ids], "verb", "who", "confidence"?, "note"}
Checks:
  - verb is one of expand, revise, simplify, revert, investigate, stop
  - who is "agent" or "owner"; name and note are not empty
  - signals is not empty; no id is cited twice in one group
  - every cited id appears in a text file of PACK_DIR, is a file name (without extension) in it,
    or appears in a screen-notes file you wrote
  - no group cites a summary file, and no note leans on "the summary" alone
  - expand cites at least one recording id (replay, call, video, clip): the metric's path was looked at
Exit 0 = pass, 1 = refused (each problem printed).
"""
import json, os, re, sys

VERBS = {"expand", "revise", "simplify", "revert", "investigate", "stop"}
# ids that name a recording (screen replay or call); an expand must cite one
RECORDING = re.compile(r"(replay|call|recording|video|audio|clip)", re.I)
TEXT_EXT = {".csv", ".json", ".md", ".eml", ".html", ".txt", ".log", ".yaml", ".yml"}

def corpus(pack, notes):
    names, text = set(), []
    for root, _, files in os.walk(pack):
        for fn in files:
            stem, ext = os.path.splitext(fn)
            names.add(stem)
            if ext.lower() in TEXT_EXT:
                with open(os.path.join(root, fn), encoding="utf-8", errors="replace") as fh:
                    text.append(fh.read())
    summaries = {os.path.splitext(fn)[0] for _, _, fs in os.walk(pack) for fn in fs if "summary" in fn.lower()}
    note_text = []
    for n in notes:
        with open(n, encoding="utf-8", errors="replace") as fh:
            note_text.append(fh.read())
    return names, "\n".join(text), "\n".join(note_text), summaries

def main(argv):
    if len(argv) < 3:
        print(__doc__); return 2
    data = json.load(open(argv[1], encoding="utf-8"))
    groups = data["groups"] if isinstance(data, dict) else data
    names, text, notes, summaries = corpus(argv[2], argv[3:])
    problems = []
    for gi, g in enumerate(groups, 1):
        tag = f"group {gi} ({g.get('name', '?')})"
        if g.get("verb") not in VERBS:
            problems.append(f"{tag}: verb {g.get('verb')!r} is not one of {sorted(VERBS)}")
        if g.get("who") not in ("agent", "owner"):
            problems.append(f"{tag}: who must be 'agent' or 'owner'")
        if not str(g.get("name", "")).strip() or not str(g.get("note", "")).strip():
            problems.append(f"{tag}: name and note must not be empty")
        sig = g.get("signals") or []
        if not sig:
            problems.append(f"{tag}: cites no signals")
        if len(sig) != len(set(sig)):
            problems.append(f"{tag}: cites an id twice")
        for s in dict.fromkeys(sig):
            if s in summaries:
                problems.append(f"{tag}: cites the summary {s!r}; cite the raw signals it rests on")
                continue
            found = s in names or re.search(r"(?<![\w-])" + re.escape(s) + r"(?![\w-])", text + "\n" + notes)
            if not found:
                problems.append(f"{tag}: {s!r} is in no pack file and no screen note: cite what you saw")
        note = str(g.get("note", ""))
        if re.search(r"\bsummary\b", note, re.I) and not re.search(r"\d", note):
            problems.append(f"{tag}: note leans on the summary with no number of its own")
        if g.get("verb") == "expand" and not any(RECORDING.search(s) for s in sig):
            problems.append(f"{tag}: expand without a recording cited; check the metric's path first")
    if problems:
        print("REFUSED"); print("\n".join(problems)); return 1
    print(f"PASS: {len(groups)} groups"); return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
