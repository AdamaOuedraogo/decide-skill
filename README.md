# decide

An agent skill for deciding what to do after a release comes back. You give it the signals a team collected (event rows, funnels, errors, CI runs, support mail, call audio, screen replays, a generated summary). It groups the findings, picks one verb per group (expand, revise, simplify, revert, investigate, stop) with cited signal ids, settles bugs on its own, and brings only product-direction calls to the owner as numbered options with a recommendation.

Its core rule: a metric counts only when the action it measures is logged on every path people use, so a generated summary is always checked against the raw rows, every replay frame and every call.

## What it needs

- **Harness:** an agent that loads `SKILL.md` skills (for example Claude Code, from `~/.claude/skills`) and can run shell commands, read files and view images.
- **Model:** one that can read images, because the agent reads saved video frames and quotes them word for word.
- **Python 3:** `check-groups.py` and the tests use only the standard library.
- **ffmpeg and ffprobe:** for frame reading, transcription and contact sheets.
- **numpy:** for `flashes.py` and `transcribe.py`.
- **faster-whisper:** for `transcribe.py` (runs on CPU).

## Install

```
git clone https://github.com/AdamaOuedraogo/decide-skill ~/.agents/skills/decide && ln -s ~/.agents/skills/decide ~/.claude/skills/decide
pip install numpy faster-whisper   # plus ffmpeg from your package manager, e.g. sudo apt install ffmpeg
```

## What is inside

- `SKILL.md`: the skill: kept rule, principles, steps.
- `scripts/flashes.py`: reads every frame of a replay and names each brief screen change (a tab shown for a second), with a saved frame.
- `scripts/transcribe.py`: transcribes call audio locally and whole, with times.
- `scripts/check-groups.py`: refuses a groups file with a bad verb, a missing `who`, a summary cited as evidence, an expand with no recording cited, or a cited id found in no pack file and no screen note.
- `tests/`: a made-up pack and the checker's self-test.

```
python -I scripts/flashes.py --out frames replay.mp4
python -I scripts/transcribe.py call.m4a
python3 -I scripts/check-groups.py groups.json PACK_DIR screen-notes.md
```

## Tests

```
python3 -I tests/run-tests.py
```

It runs `check-groups.py` on the made-up pack in `tests/pack`: one groups file that must pass, the same file without screen notes that must be refused, and one file that must be refused for seven reasons.

## Limits

Tested on one course pack only; frame-by-frame replay reading is slow; the first transcription downloads a 1.5 GB speech model.

## License

MIT, see `LICENSE`.
