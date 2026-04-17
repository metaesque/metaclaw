import pexpect
import sys
import time
import os

print("Starting automated onboard process (pexpect)...")

# Read the live master key from the environment file
master_key = "ERROR_KEY_NOT_FOUND"
env_path = '../../proxy/.env'
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('ACTIVE_PROXY_KEY='):
                master_key = line.strip().split('=', 1)[1]

# Spawn the interactive docker exec command using a pseudo-TTY
child = pexpect.spawn('docker exec -it openclaw-gateway openclaw agents add main', encoding='utf-8', timeout=30)
child.logfile = sys.stdout

# Handle Idempotency: "Agent already exists" check
i = child.expect([r"Agent \"main\" already exists\. Update it\?", "Workspace directory:"], timeout=15)
if i == 0:
    child.send("\x1b[D") # Left arrow to select Yes
    child.sendline("")
    child.expect("Workspace directory:", timeout=15)

# 1. Workspace directory
child.sendline("")

# 2. Configure model/auth
child.expect(r"Configure model/auth for this agent now\?", timeout=15)
child.send("\x1b[D") # Left arrow to select Yes
child.sendline("")

# 3. Model/auth provider
child.expect("Model/auth provider", timeout=15)
# Press down arrow 10 times to reach LiteLLM
for _ in range(10):
    child.send("\x1b[B")
    time.sleep(0.1)
child.sendline("")

# 4. Proxy API Key - Sending the REAL key directly to OpenClaw
child.expect("Enter LiteLLM API Key:", timeout=15)
child.sendline(master_key)

# 5. Configure chat channels
child.expect(r"Configure chat channels now\?", timeout=25)
child.send("\x1b[C") # Right arrow to select No
child.sendline("")

# Wait for process exit
child.expect(pexpect.EOF, timeout=15)
print("\nAutomated onboard complete.")
