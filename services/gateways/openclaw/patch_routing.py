import json
import os
import sys
import glob
import yaml
import subprocess

# Load local .env to fetch parameterized container paths
env_path = '.env'
internal_home = '/home/node'
if os.path.exists(env_path):
  with open(env_path, 'r') as f:
    for line in f:
      if line.startswith('OPENCLAW_INTERNAL_HOME='):
        internal_home = line.strip().split('=', 1)[1]

CONFIG_PATH = 'config/openclaw.json'

# Ensure the directory exists to prevent FileNotFoundError if OpenClaw hasn't natively flushed its config yet
os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

port = os.environ.get('OPENCLAW_PORT', '18789')
# Retrieve the exact proxy key injected by the orchestrator
proxy_key = os.environ.get('ACTIVE_PROXY_KEY', 'metaclaw_secure_bypass_token')

data = {}
if os.path.exists(CONFIG_PATH):
  try:
    with open(CONFIG_PATH, 'r') as f:
      data = json.load(f)
  except json.JSONDecodeError:
    pass

# 1. Patch the Operating Mode and UI Auth
if 'gateway' not in data:
  data['gateway'] = {}

data['gateway']['mode'] = 'local'

if 'controlUi' not in data['gateway']:
  data['gateway']['controlUi'] = {}
data['gateway']['controlUi']['allowInsecureAuth'] = True

# 1b. Inject Tailscale IPs into Allowed Origins to satisfy CORS
allowed_origins = data['gateway']['controlUi'].get('allowedOrigins', [])

# Always allow local interfaces
if f"http://127.0.0.1:{port}" not in allowed_origins:
    allowed_origins.append(f"http://127.0.0.1:{port}")
if f"http://localhost:{port}" not in allowed_origins:
    allowed_origins.append(f"http://localhost:{port}")

# Dynamically fetch Tailscale IP and MagicDNS if available on the host
try:
    ts_status = subprocess.run(['tailscale', 'status', '--json'], capture_output=True, text=True, check=True)
    ts_data = json.loads(ts_status.stdout)

    # Allow explicit Tailscale IPs
    for ip in ts_data.get('Self', {}).get('TailscaleIPs', []):
        ts_origin = f"http://{ip}:{port}"
        if ts_origin not in allowed_origins:
            allowed_origins.append(ts_origin)

    # Allow MagicDNS for Tailscale Serve (HTTPS)
    dns_name = ts_data.get('Self', {}).get('DNSName', '')
    if dns_name:
        dns_name = dns_name.rstrip('.')
        https_origin = f"https://{dns_name}"
        if https_origin not in allowed_origins:
            allowed_origins.append(https_origin)
except Exception:
    pass # Tailscale not installed or not accessible to the script

data['gateway']['controlUi']['allowedOrigins'] = allowed_origins

# 1c. Forcefully Synchronize the Authentication Token
if 'auth' not in data['gateway']:
  data['gateway']['auth'] = {}
data['gateway']['auth']['token'] = proxy_key

# 2. Hijack the Default OpenAI Provider
if 'models' not in data:
  data['models'] = {}

if 'providers' not in data['models']:
  data['models']['providers'] = {}

if 'openai' not in data['models']['providers']:
  data['models']['providers']['openai'] = {}

data['models']['providers']['openai']['baseUrl'] = "http://active-proxy:4000/v1"
data['models']['providers']['openai']['apiKey'] = proxy_key

# 3. Default Agent Model Override
if 'agents' not in data:
  data['agents'] = {}

if 'defaults' not in data['agents']:
  data['agents']['defaults'] = {}

data['agents']['defaults']['model'] = "openai/complex-model"

# 4. Auto-Discover Custom YAML Agents
agents_list = [{"id": "main", "default": True}]

# patch_routing.py is executed on the host from services/gateways/openclaw/
# We traverse upwards to locate the workspace directory and dynamically scan for agent YAMLs.
workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'workspace'))
search_path = os.path.join(workspace_dir, 'agents', '**', '*.yaml')
yaml_files = glob.glob(search_path, recursive=True)

# Filter out template files
yaml_files = [f for f in yaml_files if not f.endswith('.template')]

for yf in yaml_files:
  try:
    with open(yf, 'r', encoding='utf-8') as f:
      agent_data = yaml.safe_load(f)
      agent_id = agent_data.get('name')
      if agent_id:
        # STRICT ZOD COMPLIANCE: Do not inject undocumented keys like "identity".
        # OpenClaw natively scans the mounted workspace for metadata matching this ID.
        agents_list.append({
          "id": agent_id
        })
  except Exception as e:
    print(f"Warning: Could not parse {yf}: {e}")

data['agents']['list'] = agents_list

# Save openclaw.json
with open(CONFIG_PATH, 'w') as f:
  json.dump(data, f, indent=2)

print("SUCCESS: Patched baseline network routing and loopback binding.")
print("SUCCESS: Allowed insecure HTTP auth and injected Tailscale IPs to facilitate mesh access.")
print("SUCCESS: Synchronized the Gateway Auth Token with the MetaClaw ACTIVE_PROXY_KEY.")
print("SUCCESS: Hijacked the default OpenAI provider to transparently route via active-proxy.")
print("SUCCESS: Enforced 'complex-model' fallback to prevent nonexistent model requests.")
print(f"SUCCESS: Auto-discovered and registered {len(agents_list) - 1} custom agents from workspace.")
