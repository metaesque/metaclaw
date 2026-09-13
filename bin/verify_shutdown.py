#!/usr/bin/env python3
import subprocess
import sys
import os

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "down"
    issues = []

    # 1. Check Docker Containers
    try:
        res = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True, check=True)
        containers = [c.strip() for c in res.stdout.split('\n') if c.strip()]

        # Containers preserved during a standard 'halt'
        obs_containers = {
            "victorialogs-logger", "victoriametrics-tsdb", "telegraf-collector",
            "fluentbit-forwarder", "grafana-visualizer", "grafana-init-visualizer",
            "tailscale-network", "signoz-tracer"
        }

        if mode == "halt":
            for c in containers:
                if c not in obs_containers and not c.startswith("portainer") and "network" not in c:
                    issues.append(f"Unexpected running container: {c}")
        else:
            for c in containers:
                # Factory-reset-soft wipes everything. Only third-party untracked tools should remain.
                if not c.startswith("portainer"):
                    issues.append(f"Leftover container: {c}")
    except FileNotFoundError:
        pass # Docker not installed/running

    # 2. Check Bare-Metal Processes
    try:
        res = subprocess.run(["ps", "-A", "-o", "comm"], capture_output=True, text=True)
        processes = res.stdout.split('\n')
        if "ollama" in processes:
            issues.append("Leftover bare-metal process: ollama")
        if "agentbrowser" in processes:
            issues.append("Leftover bare-metal process: agentbrowser")
    except Exception:
        pass

    if issues:
        print(f"--- SHUTDOWN ANOMALIES DETECTED ({mode.upper()}) ---")
        for issue in issues:
            print(f" [!] {issue}")
        sys.exit(1)
    else:
        print(f"SUCCESS: Shutdown verified ({mode.upper()}). No anomalous processes detected.")

if __name__ == "__main__":
    main()
