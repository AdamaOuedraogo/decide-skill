#!/usr/bin/env python3
"""Transcribe call audio locally with faster-whisper, whole, with times.

Usage: python -I transcribe.py [--model medium] [--language en] audio.m4a [...]
Converts each file to 16 kHz mono WAV with ffmpeg, transcribes it on CPU, writes
<name>.json (segments with words) next to the input and prints "[start - end] text".
Needs ffmpeg on PATH and faster-whisper (pip install faster-whisper). The model downloads
on first use.
"""
import argparse, json, os, subprocess, sys, tempfile, wave
import numpy as np
from faster_whisper import WhisperModel

def load(path):
    with tempfile.TemporaryDirectory() as d:
        wav = os.path.join(d, "a.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", "16000", wav], check=True)
        with wave.open(wav, "rb") as wf:
            return np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--model", default="medium")
    ap.add_argument("--language", default="en")
    a = ap.parse_args()
    model = WhisperModel(a.model, device="cpu", compute_type="int8")
    for f in a.files:
        segs, _ = model.transcribe(load(f), word_timestamps=True, beam_size=5, language=a.language,
                                   condition_on_previous_text=False)
        res = [{"start": s.start, "end": s.end, "text": s.text,
                "words": [{"w": w.word, "s": w.start, "e": w.end, "p": w.probability} for w in (s.words or [])]}
               for s in segs]
        out = os.path.splitext(f)[0] + ".json"
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1)
        print(f"== {f} -> {out}")
        for s in res:
            print(f"[{s['start']:7.2f} - {s['end']:7.2f}] {s['text']}")

if __name__ == "__main__":
    sys.exit(main())
