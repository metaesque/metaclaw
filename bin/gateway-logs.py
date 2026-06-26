import subprocess
import json
import sys
from datetime import datetime, timezone

def main():
    # Use UTC date to match OpenClaw's internal logging timezone convention
    date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    log_file = f"/tmp/openclaw/openclaw-{date_str}.log"

    cmd = ["docker", "exec", "openclaw-gateway", "tail", "-n", "15", log_file]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"FATAL: Failed to fetch logs from OpenClaw gateway.\nCommand: {' '.join(cmd)}\nError: {e.stderr}")
        sys.exit(1)

    print(f"\n--- Cleaned Gateway Logs ({log_file}) ---\n")
    for line in result.stdout.strip().split('\n'):
        if not line.strip():
            continue

        try:
            data = json.loads(line)
            meta = data.get('_meta', {})

            timestamp = data.get('time', 'UNKNOWN_TIME')
            level = meta.get('logLevelName', 'INFO')
            # Fallback to parentNames if the subsystem name is a serialized JSON string
            raw_name = meta.get('name', 'unknown')
            if raw_name.startswith('{'):
                subsystem = json.loads(raw_name).get('subsystem', 'gateway')
            else:
                subsystem = raw_name

            # OpenClaw JSONL stores the actual console arguments under integer keys '0', '1', etc.
            # We want to parse these in order.
            message_parts = []
            for key in sorted(data.keys(), key=lambda x: int(x) if x.isdigit() else float('inf')):
                if key.isdigit():
                    val = data[key]
                    if isinstance(val, dict):
                        # Condense nested JSON objects (like handshake errors) onto one line
                        message_parts.append(json.dumps(val))
                    else:
                        message_parts.append(str(val))

            payload = " | ".join(message_parts)

            print(f"[{timestamp}] [{level}] [{subsystem}] {payload}")

        except json.JSONDecodeError:
            # Fallback for non-JSON lines (e.g., raw stack traces)
            print(f"RAW: {line}")

if __name__ == "__main__":
    main()
