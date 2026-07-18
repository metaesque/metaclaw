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
  workspace_dir = os.path.expanduser(workspace_dir)

# ==============================================================================
# NATIVE WORKSPACE PLUGIN GENERATION (Auto-Discovered by OpenClaw)
# ==============================================================================

if os.path.exists(JS_CONFIG_PATH):
    os.remove(JS_CONFIG_PATH)

profile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'profile.json'))
routing_strategy = "lexical_predictive"
if os.path.exists(profile_path):
    with open(profile_path, 'r') as f:
        profile_data = json.load(f)
        routing_strategy = profile_data.get('routing_strategy', 'lexical_predictive')

plugin_dir = os.path.join(workspace_dir, '.openclaw', 'extensions', 'metaclaw-routing')

module_path = os.path.join('modules', 'routing', f'{routing_strategy}.js')
if os.path.exists(module_path):
    os.makedirs(plugin_dir, exist_ok=True)

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

gw = setdefault_path(data, ['gateway'])
gw['mode'] = 'local'

# ==============================================================================
# METACLAW ADMIN SECURITY GATE
# ==============================================================================
# WHAT THIS DOES: Conditionally enables the /v1/chat/completions endpoint on OpenClaw.
# WHY THIS EXISTS: We utilize this endpoint to test prompt-to-model resolution
# via bin/openclaw_test.py. However, exposing a generic OpenAI-compatible interface
# on the Gateway expands the attack surface, allowing potential headless script
# abuse if the token leaks. To protect non-technical users, this is strictly
# gated behind an administrative .env flag and defaults to disabled.

enable_dev_apis = os.environ.get('METACLAW_ADMIN', 'false').lower() == 'true'

http_cfg = setdefault_path(data, ['gateway', 'http'])
endpoints_cfg = setdefault_path(http_cfg, ['endpoints'])
chat_comp_cfg = setdefault_path(endpoints_cfg, ['chatCompletions'])

if enable_dev_apis:
    chat_comp_cfg['enabled'] = True
    print("WARNING: Developer APIs (chatCompletions) actively enabled via METACLAW_ADMIN.")
else:
    chat_comp_cfg['enabled'] = False
    print("SECURE: Developer APIs (chatCompletions) disabled to minimize attack surface.")

cui = setdefault_path(data, ['gateway', 'controlUi'])
cui['allowInsecureAuth'] = True

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

auth = setdefault_path(data, ['gateway', 'auth'])
auth['token'] = proxy_key

# Fix cross-agent delegation visibility error
if 'tools' in data.get('gateway', {}):
    del data['gateway']['tools']

tools_cfg = setdefault_path(data, ['tools'])
sessions_cfg = setdefault_path(tools_cfg, ['sessions'])
sessions_cfg['visibility'] = 'all'

# Restore legacy config required by OpenClaw 2026.6.8 for agent-to-agent delegaton
agent_to_agent_cfg = setdefault_path(tools_cfg, ['agentToAgent'])
agent_to_agent_cfg['enabled'] = True

# ==============================================================================
# PROXY ROUTING INTEGRATION
# ==============================================================================

openai_prov = setdefault_path(data, ['models', 'providers', 'openai'])
openai_prov['baseUrl'] = "http://active-proxy:4000/v1"
openai_prov['apiKey'] = proxy_key
# Increase the provider timeout to 600s to gracefully accommodate massive LLM cold-starts
openai_prov['timeoutSeconds'] = 600

litellm_prov = setdefault_path(data, ['models', 'providers', 'litellm'])
litellm_prov['baseUrl'] = "http://active-proxy:4000/v1"
litellm_prov['apiKey'] = proxy_key
litellm_prov['timeoutSeconds'] = 600

defaults = setdefault_path(data, ['agents', 'defaults'])
defaults['model'] = "openai/medium-model"

agents = setdefault_path(data, ['agents'])
existing_list = agents.get('list', [])

search_path = os.path.join(workspace_dir, 'agents', '**', '*.yaml')
yaml_files = glob.glob(search_path, recursive=True)
yaml_files = [f for f in yaml_files if not f.endswith('.template')]

yaml_has_default = False
yaml_ids = set()
yaml_entries = []
routing_meta = {}

for yf in yaml_files:
  try:
    with open(yf, 'r', encoding='utf-8') as f:
      agent_data = yaml.safe_load(f)

      rel_path = os.path.relpath(yf, os.path.join(workspace_dir, 'agents'))
      parts = rel_path.replace('\\', '/').split('/')
      name = os.path.splitext(parts[-1])[0]

      if len(parts) > 1:
          team_path = "/".join(parts[:-1])
          team_id = "_".join(parts[:-1])
          agent_id = f"{team_id}_{name}"
          agent_workspace_path = f"~/.openclaw/workspace/agents/{team_path}/{name}"
          abs_agent_workspace = os.path.join(workspace_dir, 'agents', team_path, name)
      else:
          agent_id = name
          agent_workspace_path = f"~/.openclaw/workspace/agents/{name}"
          abs_agent_workspace = os.path.join(workspace_dir, 'agents', name)

      yaml_ids.add(agent_id)
      os.makedirs(abs_agent_workspace, exist_ok=True)

      entry = {
          "id": agent_id,
          "workspace": agent_workspace_path
      }

      if agent_data.get('default') is True:
          entry['default'] = True
          yaml_has_default = True

      if agent_data.get('model'):
          entry['model'] = agent_data.get('model')

      yaml_constraints = agent_data.get('constraints', {})
      if yaml_constraints:
          entry['params'] = {}
          if 'max_tokens' in yaml_constraints:
              entry['params']['maxTokens'] = yaml_constraints['max_tokens']
          if 'temperature' in yaml_constraints:
              entry['params']['temperature'] = yaml_constraints['temperature']

      yaml_tools = agent_data.get('tools', [])
      if yaml_tools:
          allowed_tools = []
          for t in yaml_tools:
              if isinstance(t, str):
                  allowed_tools.append(t)
              elif isinstance(t, dict) and 'name' in t:
                  allowed_tools.append(t['name'])

          if allowed_tools:
              entry['tools'] = {"allow": allowed_tools}

      yaml_entries.append(entry)

      # Extract routing metadata (including is_lead) for the JS plugin
      yaml_routing = agent_data.get('routing')
      if yaml_routing:
          routing_meta[agent_id] = yaml_routing

      handled_keys = {'name', 'description', 'default', 'model', 'tools', 'constraints', 'routing', 'system_prompt'}
      unhandled = set(agent_data.keys()) - handled_keys
      if unhandled:
          with open(yf, 'r', encoding='utf-8') as f_lines:
              lines = f_lines.readlines()
              for k in unhandled:
                  for i, line in enumerate(lines, 1):
                      if line.strip().startswith(k + ':'):
                          print(f"[Warning] {os.path.basename(yf)}:{i} - Unhandled key '{k}' will be ignored by OpenClaw.")
                      break

  except Exception as e:
    print(f"Warning: Could not process {yf}: {e}")

new_list = []
existing_has_default = False
for agent in existing_list:
    if 'id' in agent and agent['id'] in yaml_ids:
        continue
    if agent.get('default') is True:
        existing_has_default = True
    new_list.append(agent)

if not yaml_has_default and not existing_has_default:
    made_default = False
    for entry in yaml_entries:
        if entry['id'] == 'orchestrator':
            entry['default'] = True
            made_default = True
            break
    if not made_default:
        if len(yaml_entries) > 0:
            yaml_entries[0]['default'] = True
        else:
            new_list.append({"id": "main", "default": True})

new_list.extend(yaml_entries)
agents['list'] = new_list

if os.path.exists(plugin_dir):
    routing_meta_path = os.path.join(plugin_dir, 'routing_meta.json')
    with open(routing_meta_path, 'w', encoding='utf-8') as f:
        json.dump(routing_meta, f, indent=2)
    print(f"SUCCESS: Generated routing_meta.json for {len(routing_meta)} agents.")

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

for agent in agents['list']:
    if 'fromFile' in agent:
        del agent['fromFile']

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

with open(CONFIG_PATH, 'w') as f:
  json.dump(data, f, indent=2)

print("SUCCESS: Patched baseline network routing and loopback binding.")
print("SUCCESS: Registered 'metaclaw-routing' natively via plugins.allow.")
print("SUCCESS: Allowed insecure HTTP auth and safely merged Tailscale IPs to facilitate mesh access.")
print("SUCCESS: Synchronized the Gateway Auth Token with the MetaClaw ACTIVE_PROXY_KEY.")
print("SUCCESS: Hijacked the default OpenAI provider to transparently route via active-proxy.")
print("SUCCESS: Configured tools.agentToAgent.enabled to 'true' to permit cross-agent messaging.")
print("SUCCESS: Raised provider timeout ceilings to safely execute massive local LLM cold-starts.")
print("SUCCESS: Injected litellm API configuration for ClawRouter embeddings.")
print(f"SUCCESS: Auto-discovered {len(yaml_ids)} custom YAML agents and mapped properties to JSON.")
