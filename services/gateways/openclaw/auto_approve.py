import subprocess
import re
import time
import sys

def get_pending_uuids():
    """
    Executes 'openclaw devices list --json' inside the gateway container.
    Uses regex to extract standard UUID strings to strictly avoid
    guessing the exact OpenClaw 2026.6.8 JSON schema topology.
    """
    try:
        res = subprocess.run(
            ["docker", "exec", "openclaw-gateway", "openclaw", "devices", "list", "--json"],
            capture_output=True,
            text=True
        )

        if res.returncode != 0:
            return []

        # Standard UUID regex pattern (e.g., d7cf1e37-846f-490b-b7ee-65b601968a77)
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

        # The JSON output places the pairing request UUID inside the 'pending' array structure.
        # We extract all UUIDs. Assuming a fresh boot, any UUID generated during connection is a pairing request.
        uuids = re.findall(uuid_pattern, res.stdout.lower())

        return list(set(uuids))
    except Exception:
        return []

def main():
    # Flush=True ensures the output hits the Make terminal immediately without Python buffering
    print("[Auto-Approve] Starting background watch loop for 30 seconds...", flush=True)

    # Loop for 30 seconds (15 iterations * 2s sleep)
    # This provides ample time for the browser to open, load the React app,
    # generate the crypto keys, establish the WebSocket, and submit the pending request.
    for _ in range(15):
        uuids = get_pending_uuids()

        for req_id in uuids:
            # We found a UUID. Attempt to approve it.
            print(f"\n[Auto-Approve] Caught pending device request ({req_id}). Approving...", flush=True)
            result = subprocess.run(
                ["docker", "exec", "openclaw-gateway", "openclaw", "devices", "approve", req_id],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"[Auto-Approve] Successfully paired device. You may proceed in the browser.", flush=True)
                sys.exit(0)
            else:
                # If approval fails (e.g., the UUID was a paired device string rather than a request),
                # we silently ignore and continue the loop.
                pass

        time.sleep(2)

    print("\n[Auto-Approve] Watch loop finished. No pending requests approved (Device likely already paired).", flush=True)

if __name__ == "__main__":
    main()
