import subprocess
import json
import time
import sys
import re

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

        # Parse the JSON safely
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
            # Based on OpenClaw CLI output logs, the target UUID is the requestId.
            req_id = item.get("requestId")

            if req_id and uuid_pattern.match(req_id):
                uuids.append(req_id)
            else:
                # Fallback: if the schema key differs slightly, scan the values
                # of this specific pending object for a valid UUID.
                for v in item.values():
                    if isinstance(v, str) and uuid_pattern.match(v):
                        uuids.append(v)

        return list(set(uuids))

    except Exception as e:
        print(f"[Auto-Approve] JSON parsing error: {e}", flush=True)
        return []

def main():
    print("[Auto-Approve] Starting background watch loop for 30 seconds...", flush=True)

    # Loop for 30 seconds (15 iterations * 2s sleep)
    # This provides ample time for the browser to open, load the React app,
    # generate the crypto keys, establish the WebSocket, and submit the pending request.
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
                    print(f"[Auto-Approve] Successfully executed approval for: {req_id}", flush=True)
                    # We let the loop finish its current iteration to catch any
                    # secondary requests that might have fired concurrently,
                    # but the overall approval is successful.
                else:
                    print(f"[Auto-Approve] Approval command failed. Output: {result.stdout}", flush=True)

        time.sleep(2)

    print("\n[Auto-Approve] Watch loop finished.", flush=True)

if __name__ == "__main__":
    main()
