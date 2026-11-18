#!/usr/bin/env python3
"""Find brief screen changes in a replay video and save a frame of each.

Reads every frame (full frame rate, downscaled to grey 320x180), flags frame-to-frame
changes, and groups them into segments. A big change that reverts within --max-hold
seconds is a "flash" (a tab or dialog shown for a moment): the kind of thing interval
sampling misses. Every segment gets a full-size PNG from its middle, so you can read it.

Usage: python -I flashes.py [--threshold 1.5] [--max-hold 5] [--out DIR] video.mp4 [...]
Needs ffmpeg/ffprobe on PATH and numpy (pip install numpy).
"""
import argparse, os, subprocess, sys
import numpy as np

W, H = 320, 180

def frames(path):
    rate = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                           "stream=r_frame_rate", "-of", "csv=p=0", path],
                          capture_output=True, text=True, check=True).stdout.strip().split("\n")[0].strip(",")
    num, den = (rate.split("/") + ["1"])[:2]
    fps = float(num) / float(den)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W}:{H},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return fps, np.frombuffer(raw, dtype=np.uint8).reshape(-1, H, W).astype(np.int16)

def grab(path, t, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1", out], check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--threshold", type=float, default=1.5, help="mean grey diff that counts as a screen change")
    ap.add_argument("--max-hold", type=float, default=5.0, help="seconds a change may last and still count as a flash")
    ap.add_argument("--out", default="flash-frames")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    total = 0
    for v in a.videos:
        fps, f = frames(v)
        base = os.path.splitext(os.path.basename(v))[0]
        d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
        jumps = [i + 1 for i in np.where(d > a.threshold)[0]]  # frame index where the new screen starts
        print(f"{base}: {len(f)} frames at {fps:g} fps, {len(f)/fps:.1f} s, {len(jumps)} big changes")
        i = 0
        while i < len(jumps):
            start = jumps[i]
            # a flash: some later frame within max-hold looks like the frame before the jump again
            before = f[start - 1]
            end = None
            for k in range(start + 1, min(len(f), start + int(a.max_hold * fps) + 1)):
                if np.abs(f[k] - before).mean() < a.threshold:
                    end = k
                    break
            if end is not None:
                mid = (start + end) / 2 / fps
                png = os.path.join(a.out, f"{base}-flash-{start/fps:06.2f}.png")
                grab(v, mid, png)
                print(f"  FLASH {start/fps:6.2f}s -> {end/fps:6.2f}s ({(end-start)/fps:.2f} s)  frame: {png}")
                total += 1
                while i < len(jumps) and jumps[i] <= end:
                    i += 1
            else:
                png = os.path.join(a.out, f"{base}-change-{start/fps:06.2f}.png")
                grab(v, start / fps + 0.2, png)
                print(f"  change {start/fps:6.2f}s (screen stays)  frame: {png}")
                i += 1
    print(f"{total} flash(es). Open every frame listed and write what it shows, word for word.")

if __name__ == "__main__":
    sys.exit(main())
