#!/usr/bin/env python3
"""Self-test for check-groups.py on the made-up pack in this folder."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
chk = os.path.join(here, "..", "scripts", "check-groups.py")
def run(*a):
    p = subprocess.run([sys.executable, "-I", chk, *a], capture_output=True, text=True, cwd=here)
    return p.returncode, p.stdout
cases = [
    ("pass with screen notes", run("ok.json", "pack", "screen-notes.md"), 0, ["PASS"]),
    ("refuse on-screen id without notes", run("ok.json", "pack"), 1, ["'jb-7f3a' is in no pack file"]),
    ("refuse bad groups", run("bad.json", "pack", "screen-notes.md"), 1,
     ["cites the summary", "leans on the summary", "expand without a recording", "verb 'rollback'",
      "who must be", "must not be empty", "cites an id twice", "'jb-0000' is in no pack file"]),
]
fail = 0
for name, (code, out), want, needles in cases:
    ok = code == want and all(n in out for n in needles)
    fail += not ok
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else "\n" + out))
sys.exit(1 if fail else 0)
