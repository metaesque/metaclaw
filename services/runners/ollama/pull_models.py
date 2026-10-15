#!/usr/bin/env python3
"""
Validates and pulls assigned local Ollama models via the local Ollama HTTP API.
Renders a live progress bar with percentage, GB transferred, MB/s speed,
dynamic ETA, and total elapsed time per model.
"""
import json
import os
import re
import sys
import time
import urllib.request
from dotenv import dotenv_values


def pull_one_model(port, model_name):
    t0 = time.time()
    print(f"  -> Pulling {model_name}...", flush=True)

    url = f"http://127.0.0.1:{port}/api/pull"
    payload = json.dumps({"name": model_name, "stream": True}).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=3600) as resp:
            last_print = 0.0
            printed_bar = False
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    continue

                total = evt.get("total", 0)
                comp = evt.get("completed", 0)
                now = time.time()

                if total > 0 and (now - last_print >= 0.25 or comp == total):
                    last_print = now
                    printed_bar = True
                    pct = (comp / total) * 100.0
                    elapsed = max(0.001, now - t0)
                    speed_mbs = (comp / (1024 * 1024)) / elapsed
                    rem_sec = ((total - comp) / (comp / elapsed)) if comp > 0 else 0
                    bar_width = 24
                    filled = int(bar_width * comp // total)
                    bar = "#" * filled + "-" * (bar_width - filled)
                    sys.stdout.write(
                        f"\r     [{bar}] {pct:5.1f}% "
                        f"({comp / (1024**3):.2f}/{total / (1024**3):.2f} GB) | "
                        f"{speed_mbs:5.1f} MB/s | ETA: {int(rem_sec)}s   "
                    )
                    sys.stdout.flush()

            total_elapsed = time.time() - t0
            if printed_bar:
                sys.stdout.write("\n")
            print(f"     Done: {model_name} verified/pulled in {total_elapsed:.1f}s.", flush=True)
    except Exception as e:
        print(f"\nWARNING: Failed to pull {model_name}: {e}", flush=True)


def prewarm_model(port, model_name, keep_alive):
    t0 = time.time()
    print(f"  -> Pre-warming {model_name} into memory...", flush=True)
    url = f"http://127.0.0.1:{port}/api/generate"
    payload = json.dumps(
        {"model": model_name, "prompt": "", "keep_alive": keep_alive}
    ).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            resp.read()
        elapsed = time.time() - t0
        print(f"     Done: {model_name} pre-warmed in {elapsed:.1f}s.", flush=True)
    except Exception as e:
        print(f"WARNING: Failed to pre-warm {model_name}: {e}", flush=True)


def main():
    framework_root = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    )
    service_dir = os.path.dirname(os.path.abspath(__file__))

    cfg = {}
    env_paths = [
        os.path.join(framework_root, ".env"),
        os.path.join(service_dir, ".env"),
        os.path.join(framework_root, "services", "gateway", ".env"),
    ]
    for path in env_paths:
        if os.path.exists(path):
            cfg.update(dotenv_values(path))

    port = cfg.get("OLLAMA_PORT") or os.environ.get("OLLAMA_PORT") or "11434"
    keep_alive = (
        cfg.get("OLLAMA_KEEP_ALIVE") or os.environ.get("OLLAMA_KEEP_ALIVE") or "60m"
    )

    target_models = (
        cfg.get("OLLAMA_TARGET_MODELS")
        or os.environ.get("OLLAMA_TARGET_MODELS")
        or ""
    )
    judge_model = (
        cfg.get("OPENCLAW_JUDGE_MODEL")
        or os.environ.get("OPENCLAW_JUDGE_MODEL")
        or ""
    )

    raw_str = f"{target
