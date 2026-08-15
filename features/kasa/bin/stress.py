#!/usr/bin/env python3
"""
Hardware Stress Testing Utility for MetaClaw Nodes.

STRESS TESTING BEYOND CPU (Future Roadmap):
1. CPU & Vector Scaling:
   - Scales active worker threads using `stress-ng --cpu N`.
   - Supports specific CPU vector methods like `--cpu-method fft` or `--cpu-method matrixprod`
     for heavy floating-point and AVX stress.

2. System Memory (RAM):
   - Thrashes system memory bandwidth using `stress-ng --vm N --vm-bytes 80%`.

3. Storage I/O (NVMe):
   - Stresses NVMe read/write throughput using `stress-ng --hdd N --hdd-bytes 10G`.

4. GPU & VRAM Acceleration:
   - For NVIDIA GB10 / CUDA nodes (e.g., DGX Spark / Ascent GX10):
     - `gpu-burn` for simultaneous Tensor/CUDA core and VRAM power stress.
     - PyTorch allocation loops:
       `python3 -c "import torch; x = torch.randn(15000, 15000, device='cuda'); while True: y = x @ x"`
   - For AMD Integrated Graphics (e.g., GMKtec EVO-X2 / K8 Plus):
     - OpenCL / Vulkan tools (`clpeak`, `glmark2`, `vkmark`).

5. Network Interconnect:
   - Pushes high-speed QSFP / ConnectX-7 interface power using `iperf3 -c <target> -P 8`
     or `stress-ng --sock N`.
"""

import sys
import time
import json
import argparse
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path

# Insert repository root to import lib.metaclaw
repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from lib.metaclaw import Inst

VM_QUERY_URL = "http://127.0.0.1:8428/api/v1/query"


def get_kasa_watts(device_alias):
    """Polls VictoriaMetrics for the instantaneous kasa_power_watts metric for a given device."""
    params = urllib.parse.urlencode({"query": f'kasa_power_watts{{device="{device_alias}"}}'})
    url = f"{VM_QUERY_URL}?{params}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            results = data.get("data", {}).get("result", [])
            if results:
                return float(results[0]["value"][1])
    except Exception:
        pass
    return None


def run_remote_command(node, command):
    """Executes a command on the target ComputeNode via SSH."""
    host_ip = getattr(node, 'ip', getattr(node, 'hostname', getattr(node, 'name', str(node))))
    res = subprocess.run(["ssh", host_ip, command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return res.stdout.strip()


def get_node_cpu_count(node):
    """Determines the total number of physical/logical CPUs on the node."""
    if hasattr(node, 'cpus') and node.cpus:
        return int(node.cpus)

    try:
        out = run_remote_command(node, "nproc")
        if out and out.strip().isdigit():
            return int(out.strip())
    except Exception:
        pass
    return 1


def start_stress_ng(node, cpus, duration):
    """Starts stress-ng asynchronously on the target node."""
    cmd = f"stress-ng --cpu {cpus} --timeout {duration}s"
    host_ip = getattr(node, 'ip', getattr(node, 'hostname', getattr(node, 'name', str(node))))
    proc = subprocess.Popen(["ssh", host_ip, cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc


def parse_args():
    parser = argparse.ArgumentParser(description="CPU and Hardware Stress Testing Utility with TSDB Power Monitoring.")
    parser.add_argument("--host", type=str, required=True, help="Target compute node name (e.g., spark1, compute, control)")
    parser.add_argument("--duration", type=int, default=30, help="Duration in seconds for each stress level (default: 30)")
    parser.add_argument("--pause", type=int, default=10, help="Pause duration in seconds between stress levels (default: 10)")
    return parser.parse_args()


def main():
    args = parse_args()

    # Resolve node from metaclaw.Inst
    devices = Inst.devices()
    target_node = None

    if isinstance(devices, dict):
        target_node = devices.get(args.host)
    elif isinstance(devices, list):
        for dev in devices:
            if getattr(dev, 'name', None) == args.host or getattr(dev, 'hostname', None) == args.host:
                target_node = dev
                break

    if not target_node:
        print(f"ERROR: Could not resolve compute node '{args.host}' from metaclaw.Inst.devices().")
        sys.exit(1)

    device_alias = getattr(target_node, 'name', args.host)
    max_cpus = get_node_cpu_count(target_node)
    print(f"Target Host: {device_alias} | Resolved Max CPUs: {max_cpus}")

    # Build doubling CPU step sequence (1, 2, 4, 8, ... up to max_cpus)
    cpu_steps = []
    c = 1
    while c < max_cpus:
        cpu_steps.append(c)
        c *= 2
    if not cpu_steps or cpu_steps[-1] != max_cpus:
        cpu_steps.append(max_cpus)

    print(f"Starting CPU stress progression sequence: {cpu_steps}")
    print("=" * 70)

    for step_idx, cpus in enumerate(cpu_steps, 1):
        print(f"\n--- [Step {step_idx}/{len(cpu_steps)}] Testing with {cpus} CPU(s) for {args.duration}s ---")

        # 1. Poll Watts just before stress starts
        w_before = get_kasa_watts(device_alias)
        w_before_str = f"{w_before:.2f} W" if w_before is not None else "N/A"
        print(f"  [T-0s] Power before stress start: {w_before_str}")

        # 2. Start stress-ng asynchronously
        proc = start_stress_ng(target_node, cpus, args.duration)

        # 3. Poll Watts 5 seconds after stress starts
        t_start_wait = min(5, max(1, args.duration // 2))
        time.sleep(t_start_wait)
        w_after_start = get_kasa_watts(device_alias)
        w_after_start_str = f"{w_after_start:.2f} W" if w_after_start is not None else "N/A"
        print(f"  [T+{t_start_wait}s] Power into stress:         {w_after_start_str}")

        # 4. Wait until 5 seconds before stress ends
        remaining_stress = args.duration - (t_start_wait + 5)
        if remaining_stress > 0:
            time.sleep(remaining_stress)

        w_before_end = get_kasa_watts(device_alias)
        w_before_end_str = f"{w_before_end:.2f} W" if w_before_end is not None else "N/A"
        print(f"  [T-5s] Power before stress end:   {w_before_end_str}")

        # Wait for stress process to complete final 5s
        time.sleep(5)
        if hasattr(proc, 'wait'):
            proc.wait()

        # 5. Poll Watts 5 seconds into the pause
        t_pause_wait = min(5, max(1, args.pause // 2))
        time.sleep(t_pause_wait)
        w_pause = get_kasa_watts(device_alias)
        w_pause_str = f"{w_pause:.2f} W" if w_pause is not None else "N/A"
        print(f"  [Pause+{t_pause_wait}s] Power into pause:      {w_pause_str}")

        # Sleep remaining pause duration
        remaining_pause = args.pause - t_pause_wait
        if remaining_pause > 0:
            time.sleep(remaining_pause)

    print("\n" + "=" * 70)
    print("Stress testing sequence completed successfully.")


if __name__ == "__main__":
    main()
