import subprocess
import json
import time
import sys
import re
import webbrowser
import os
import socket

def is_headless():
    """
    Determines if the current execution environment is a headless server.
    First checks profile.json, then falls back to OS-level heuristics.
    """
    profile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'profile.json'))
    if os.path.exists(profile_path):
        try:
            with open(profile_path, 'r') as f:
                profile = json.load(f)
                hostname = socket.gethostname()
                for node in profile.get('nodes', []):
                    if node.get('hostname') == hostname:
                        return node.get('hardware', {}).get('headless', False)
        except Exception:
            pass

    # Fallback heuristic: Assume headless if Linux with no active display server
    if sys.platform == 'linux':
        if not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'):
            return True
    return False

def get_pending_uuids():
    """
    Executes 'openclaw devices list --json' and extracts all UUIDs specifically
    from the 'pending' array based on the known OpenClaw JSON schema.
    """
    try:
        res = subprocess.run(
            ["docker", "exec", "openclaw-gateway", "openclaw", "devices", "list", "--json"],
            capture_output=True,
            text=True
        )

        if res.returncode != 0:
            return []

        data = json.loads(res.stdout)
        pending_list = data.get("pending", [])
        if not pending_list:
            return []

        uuids = []
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )

        for item in pending_list:
            req_id = item.get("requestId")
            if req_id and uuid_pattern.match(req_id):
                uuids.append(req_id)
            else:
                for v in item.values():
                    if isinstance(v, str) and uuid_pattern.match(v):
                        uuids.append(v)

        return list(set(uuids))

    except Exception as e:
        print(f"[Auto-Approve] JSON parsing error: {e}", flush=True)
        return []

def main():
    if len(sys.argv) < 2:
        print("[Auto-Approve] Error: URL argument missing.")
        sys.exit(1)

    url = sys.argv[1]
    headless = is_headless()

    if headless:
        print("\n================================================================================")
        print(f"PLEASE MANUALLY NAVIGATE TO: {url}")
        print("================================================================================")
        print("\n[INSTRUCTIONS]")
        print("1. A login page will appear in your browser, with instructions to approve a request.")
        print("2. This script will automatically approve that request for you.")
        print("3. Once you see a line below stating 'Successfully executed approval for <uuid>'")
        print("   where <uuid> matches the one showing in your browser, you can click the")
        print("   red [Connect] button to gain access to the OpenClaw dashboard.\n")
        input("Press <Enter> once the URL has been loaded in your browser... ")
    else:
        print(f"\n[Auto-Approve] Launching browser to: {url}")
        webbrowser.open(url)

    print("\n[Auto-Approve] Starting watch loop...", flush=True)

    # Loop for 30 seconds (15 iterations * 2s sleep)
    approved_count = 0
    for _ in range(15):
        pending_ids = get_pending_uuids()

        if pending_ids:
            for req_id in pending_ids:
                print(f"\n[Auto-Approve] Found valid pending device request ({req_id}). Approving...", flush=True)

                result = subprocess.run(
                    ["docker", "exec", "openclaw-gateway", "openclaw", "devices", "approve", req_id],
                    capture_output=True,
                    text=True
                )

                # We MUST check stdout for "Approved" because OpenClaw's CLI
                # occasionally returns an exit code of 0 even when throwing a failure.
                if "Approved" in result.stdout:
                    print(f"[Auto-Approve] Successfully executed approval for {req_id}", flush=True)
                    approved_count += 1
                else:
                    print(f"[Auto-Approve] Approval command failed. Output: {result.stdout}", flush=True)

        if approved_count > 0:
            print("\n[Auto-Approve] Device pairing successful. Exiting watch loop.", flush=True)
            break

        time.sleep(2)

    if approved_count == 0:
        print("\n[Auto-Approve] Watch loop finished. No pending requests found or approved.", flush=True)

if __name__ == "__main__":
    main()
