import json
import os
import sys
import glob
import yaml
import subprocess
import shutil

# Load local .env to fetch parameterized container paths
env_path = '.env'
if os.path.exists(env_path):
  with open(env_path, 'r') as f:
    pass

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
# NATIVE WORKSPACE PLUGIN GENERATION (Auto-Discovered by OpenClaw)
# ==============================================================================

# Cleanup the old toxic configuration file that caused validation errors
if os.path.exists(JS_CONFIG_PATH):
    os.remove(JS_CONFIG_PATH)

# Fetch chosen routing strategy from profile.json
profile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'profile.json'))
routing_strategy = "lexical_predictive"
if os.path.exists(profile_path):
    with open(profile_path, 'r') as f:
        profile_data = json.load(f)
        routing_strategy = profile_data.get('routing_strategy', 'lexical_predictive')

module_path = os.path.join('modules', 'routing', f'{routing_strategy}.js')
if os.path.exists(module_path):
    plugin_dir = os.path.join(workspace_dir, '.openclaw', 'extensions', 'metaclaw-routing')
    os.makedirs(plugin_dir, exist_ok=True)

    # 1. Write the mandatory plugin manifest
    manifest = {
        "id": "metaclaw-routing",
        "name": "MetaClaw Routing Hook",
        "description": "Lexical and Predictive LLM routing.",
        "configSchema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {}
        }
    }
    with open(os.path.join(plugin_dir, 'openclaw.plugin.json'), 'w') as f:
        json.dump(manifest, f, indent=2)

    # 2. Write the executable TypeScript module (Node/Jiti handles .js syntax natively)
    with open(module_path, 'r') as f_in, open(os.path.join(plugin_dir, 'index.ts'), 'w') as f_out:
        f_out.write(f_in.read())

    print(f"SUCCESS: Provisioned Native Workspace Plugin '{routing_strategy}' in {plugin_dir}.")


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
    current = d
    for key in path_keys:
        current = current.setdefault(key, {})
    return current

# 1. Patch the Operating Mode and UI Auth
gw = setdefault_path(data, ['gateway'])
gw['mode'] = 'local'

cui = setdefault_path(data, ['gateway', 'controlUi'])
cui['allowInsecureAuth'] = True

# 1b. Inject Tailscale IPs into Allowed Origins safely
allowed_origins = set(cui.get('allowedOrigins', []))
allowed_origins.add(f"http://127.0.0.1:{port}")
allowed_origins.add(f"http://localhost:{port}")

try:
    ts_status = subprocess.run(['tailscale', 'status', '--json'], capture_output=True, text=True, check=True)
    ts_data = json.loads(ts_status.stdout)
    for ip in ts_data.get('Self', {}).get('TailscaleIPs', []):
        allowed_origins.add(f"http://{ip}:{port}")
    dns_name = ts_data.get('Self', {}).get('DNSName', '')
    if dns_name:
        dns_name = dns_name.rstrip('.')
        allowed_origins.add(f"https://{dns_name}")
except Exception:
    pass

cui['allowedOrigins'] = list(allowed_origins)

# 1c. Forcefully Synchronize the Authentication Token
auth = setdefault_path(data, ['gateway', 'auth'])
auth['token'] = proxy_key

# 2. Hijack the Default OpenAI Provider
openai_prov = setdefault_path(data, ['models', 'providers', 'openai'])
openai_prov['baseUrl'] = "http://active-proxy:4000/v1"
openai_prov['apiKey'] = proxy_key

# 3. Default Agent Model Override
defaults = setdefault_path(data, ['agents', 'defaults'])
defaults['model'] = "openai/complex-model"

# 4. Auto-Discover Custom YAML Agents & Non-Destructively Merge
agents = setdefault_path(data, ['agents'])
existing_list = agents.get('list', [])

agents_dict = {agent.get('id'): agent for agent in existing_list if isinstance(agent, dict) and 'id' in agent}

search_path = os.path.join(workspace_dir, 'agents', '**', '*.yaml')
yaml_files = glob.glob(search_path, recursive=True)
yaml_files = [f for f in yaml_files if not f.endswith('.template')]

yaml_has_default = False

for yf in yaml_files:
  try:
    with open(yf, 'r', encoding='utf-8') as f:
      agent_data = yaml.safe_load(f)
      agent_id = agent_data.get('name')
      if agent_id:
        if agent_data.get('default') is True:
            yaml_has_default = True
        if agent_id not in agents_dict:
            agents_dict[agent_id] = {"id": agent_id}
  except Exception as e:
    print(f"Warning: Could not parse {yf}: {e}")

existing_has_default = any(agent.get('default') is True for agent in agents_dict.values())

if not yaml_has_default and not existing_has_default:
    if 'orchestrator' in agents_dict:
        agents_dict['orchestrator']['default'] = True
    elif 'main' in agents_dict:
        agents_dict['main']['default'] = True
    elif len(agents_dict) > 0:
        first_agent = list(agents_dict.keys())[0]
        agents_dict[first_agent]['default'] = True
    else:
        agents_dict['main'] = {"id": "main", "default": True}

agents['list'] = list(agents_dict.values())

# 5. Clean up ALL previous toxic JSON injection attempts
if 'plugins' in data:
    if 'load' in data['plugins']:
        if 'paths' in data['plugins']['load']:
            paths = data['plugins']['load']['paths']
            if '/root/.openclaw/openclaw.config.js' in paths:
                paths.remove('/root/.openclaw/openclaw.config.js')
                data['plugins']['load']['paths'] = paths
            if '/home/node/.openclaw/openclaw.config.js' in paths:
                paths.remove('/home/node/.openclaw/openclaw.config.js')
                data['plugins']['load']['paths'] = paths
        if not data['plugins']['load'].get('paths'):
            del data['plugins']['load']
    if 'entries' in data['plugins'] and 'metaclaw-routing' in data['plugins']['entries']:
        del data['plugins']['entries']['metaclaw-routing']
        if not data['plugins']['entries']:
            del data['plugins']['entries']

# 6. Enable the new Native Workspace Plugin explicitly
plugins = setdefault_path(data, ['plugins'])
plugins['enabled'] = True

allow = plugins.get('allow', [])
if "metaclaw-routing" not in allow:
    allow.append("metaclaw-routing")
plugins['allow'] = allow

entries = setdefault_path(plugins, ['entries'])
mc_routing = setdefault_path(entries, ['metaclaw-routing'])
mc_routing['enabled'] = True
hooks = setdefault_path(mc_routing, ['hooks'])
hooks['allowConversationAccess'] = True

# Save openclaw.json
with open(CONFIG_PATH, 'w') as f:
  json.dump(data, f, indent=2)

print("SUCCESS: Patched baseline network routing and loopback binding.")
print("SUCCESS: Registered 'metaclaw-routing' natively via plugins.allow.")
print("SUCCESS: Allowed insecure HTTP auth and safely merged Tailscale IPs to facilitate mesh access.")
print("SUCCESS: Synchronized the Gateway Auth Token with the MetaClaw ACTIVE_PROXY_KEY.")
print("SUCCESS: Hijacked the default OpenAI provider to transparently route via active-proxy.")
print(f"SUCCESS: Auto-discovered and safely merged {len(agents_dict)} custom agents from external workspace.")
