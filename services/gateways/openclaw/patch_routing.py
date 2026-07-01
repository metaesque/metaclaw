import json
import os
import sys
import glob
import yaml
import subprocess
import re

# Load local .env to fetch parameterized container paths
env_path = '.env'
internal_home = '/home/node'
if os.path.exists(env_path):
  with open(env_path, 'r') as f:
    for line in f:
      if line.startswith('OPENCLAW_INTERNAL_HOME='):
        internal_home = line.strip().split('=', 1)[1]

CONFIG_PATH = 'config/openclaw.json'
JS_CONFIG_PATH = 'config/openclaw.config.js'

# Ensure the directory exists to prevent FileNotFoundError if OpenClaw hasn't natively flushed its config yet
os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

port = os.environ.get('OPENCLAW_PORT', '18789')
# Retrieve the exact proxy key injected by the orchestrator
proxy_key = os.environ.get('ACTIVE_PROXY_KEY', 'metaclaw_secure_bypass_token')

# Find the workspace dir
workspace_dir = None
if os.path.exists(env_path):
  with open(env_path, 'r') as f:
    for line in f:
      if line.startswith('OPENCLAW_WORKSPACE='):
        workspace_dir = line.strip().split('=', 1)[1]
        break

if not workspace_dir:
  workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'workspace'))
else:
  # Resolve ~ if the user provided it
  workspace_dir = os.path.expanduser(workspace_dir)

# ==============================================================================
# JS CONFIGURATION INJECTION (Non-Destructive Module Loading)
# ==============================================================================

# Fetch chosen routing strategy from profile.json
profile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'profile.json'))
routing_strategy = "lexical_predictive"
if os.path.exists(profile_path):
    with open(profile_path, 'r') as f:
        profile_data = json.load(f)
        routing_strategy = profile_data.get('routing_strategy', 'lexical_predictive')

module_path = os.path.join('modules', 'routing', f'{routing_strategy}.js')
module_code = ""
if os.path.exists(module_path):
    with open(module_path, 'r') as f:
        # Strip the module.exports wrapper from the source template so we can inject just the object
        raw_code = f.read()
        match = re.search(r'module\.exports\s*=\s*\{([\s\S]*)\};', raw_code)
        if match:
            module_code = match.group(1).strip()

START_MARKER = "// --- METACLAW ROUTING START ---"
END_MARKER = "// --- METACLAW ROUTING END ---"
injection_block = f"{START_MARKER}\n{module_code}\n{END_MARKER}"

if os.path.exists(JS_CONFIG_PATH):
    with open(JS_CONFIG_PATH, 'r') as f:
        js_content = f.read()

    if START_MARKER in js_content and END_MARKER in js_content:
        # Safely regex replace only the MetaClaw block, preserving user custom plugins above/below
        js_content = re.sub(f"{START_MARKER}.*?{END_MARKER}", injection_block, js_content, flags=re.DOTALL)
        with open(JS_CONFIG_PATH, 'w') as f:
            f.write(js_content)
        print(f"SUCCESS: Non-destructively updated {routing_strategy} module in openclaw.config.js.")
    else:
        # User has a custom config but no MetaClaw markers. We must wrap their entire file safely to avoid destruction.
        print("WARNING: Existing openclaw.config.js found without MetaClaw markers. Unable to perform safe regex injection.")
        print("         Please manually insert the routing hooks if desired.")
else:
    # Write fresh templated file
    with open(JS_CONFIG_PATH, 'w') as f:
        f.write(f"module.exports = {{\n{injection_block}\n}};\n")
    print(f"SUCCESS: Provisioned fresh openclaw.config.js with {routing_strategy} module.")


# ==============================================================================
# JSON CONFIGURATION INJECTION (Non-Destructive Merge)
# ==============================================================================

data = {}
if os.path.exists(CONFIG_PATH):
  try:
    with open(CONFIG_PATH, 'r') as f:
      data = json.load(f)
  except json.JSONDecodeError:
    pass

def setdefault_path(d, path_keys):
    """
    Safely traverses a dictionary, creating nested dictionaries if they do not exist,
    and returns the innermost dictionary. This prevents destructive overwrites of user configs.
    """
    current = d
    for key in path_keys:
        current = current.setdefault(key, {})
    return current

# 1. Patch the Operating Mode and UI Auth
gw = setdefault_path(data, ['gateway'])
gw['mode'] = 'local'

cui = setdefault_path(data, ['gateway', 'controlUi'])
cui['allowInsecureAuth'] = True

# 1b. Inject Tailscale IPs into Allowed Origins safely (Preserve user origins)
allowed_origins = set(cui.get('allowedOrigins', []))

# Always allow local interfaces
allowed_origins.add(f"http://127.0.0.1:{port}")
allowed_origins.add(f"http://localhost:{port}")

# Dynamically fetch Tailscale IP and MagicDNS if available on the host
try:
    ts_status = subprocess.run(['tailscale', 'status', '--json'], capture_output=True, text=True, check=True)
    ts_data = json.loads(ts_status.stdout)

    # Allow explicit Tailscale IPs
    for ip in ts_data.get('Self', {}).get('TailscaleIPs', []):
        allowed_origins.add(f"http://{ip}:{port}")

    # Allow MagicDNS for Tailscale Serve (HTTPS)
    dns_name = ts_data.get('Self', {}).get('DNSName', '')
    if dns_name:
        dns_name = dns_name.rstrip('.')
        allowed_origins.add(f"https://{dns_name}")
except Exception:
    pass # Tailscale not installed or not accessible to the script

cui['allowedOrigins'] = list(allowed_origins)

# 1c. Forcefully Synchronize the Authentication Token
auth = setdefault_path(data, ['gateway', 'auth'])
auth['token'] = proxy_key

# 2. Hijack the Default OpenAI Provider (Preserve other provider settings)
openai_prov = setdefault_path(data, ['models', 'providers', 'openai'])
openai_prov['baseUrl'] = "http://active-proxy:4000/v1"
openai_prov['apiKey'] = proxy_key

# 3. Default Agent Model Override
defaults = setdefault_path(data, ['agents', 'defaults'])
defaults['model'] = "openai/complex-model"

# 4. Auto-Discover Custom YAML Agents & Non-Destructively Merge
agents = setdefault_path(data, ['agents'])
existing_list = agents.get('list', [])

# Create a dictionary mapping by agent ID to preserve existing GUI-created configurations
agents_dict = {agent.get('id'): agent for agent in existing_list if isinstance(agent, dict) and 'id' in agent}

if 'main' not in agents_dict:
    agents_dict['main'] = {"id": "main", "default": True}

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
        if agent_id not in agents_dict:
            agents_dict[agent_id] = {"id": agent_id}
        # If it already exists, we leave it untouched, preserving GUI tweaks.
  except Exception as e:
    print(f"Warning: Could not parse {yf}: {e}")

# Write the merged dictionary back to the list
agents['list'] = list(agents_dict.values())

# Save openclaw.json
with open(CONFIG_PATH, 'w') as f:
  json.dump(data, f, indent=2)

print("SUCCESS: Patched baseline network routing and loopback binding.")
print("SUCCESS: Allowed insecure HTTP auth and safely merged Tailscale IPs to facilitate mesh access.")
print("SUCCESS: Synchronized the Gateway Auth Token with the MetaClaw ACTIVE_PROXY_KEY.")
print("SUCCESS: Hijacked the default OpenAI provider to transparently route via active-proxy.")
print("SUCCESS: Enforced 'complex-model' fallback to prevent nonexistent model requests.")
print(f"SUCCESS: Auto-discovered and safely merged {len(agents_dict) - 1} custom agents from external workspace.")
