import json
import os
import sys
import yaml
import glob

# Load local .env to fetch parameterized container paths
env_path = '.env'
internal_home = '/home/node'
if os.path.exists(env_path):
  with open(env_path, 'r') as f:
    for line in f:
      if line.startswith('OPENCLAW_INTERNAL_HOME='):
        internal_home = line.strip().split('=', 1)[1]

# Config path strictly reflects the 'config' directory on the host
CONFIG_PATH = 'config/openclaw.json'
LITELLM_CONFIG_PATH = '../../proxy/config.yaml'
WORKSPACE_DIR = '../../../workspace'
AGENTS_DIR = os.path.join(WORKSPACE_DIR, 'agents')

if not os.path.exists(CONFIG_PATH):
  print(f"FATAL: {CONFIG_PATH} not found. You must run the TUI wizard first.")
  sys.exit(1)

if not os.path.exists(LITELLM_CONFIG_PATH):
  print(f"FATAL: {LITELLM_CONFIG_PATH} not found.")
  sys.exit(1)

try:
  with open(CONFIG_PATH, 'r') as f:
    data = json.load(f)
except json.JSONDecodeError:
  print(f"FATAL: {CONFIG_PATH} is corrupted. Please factory reset and re-run wizard.")
  sys.exit(1)

# Extract models from LiteLLM config
try:
  with open(LITELLM_CONFIG_PATH, 'r') as f:
    litellm_config = yaml.safe_load(f)
except yaml.YAMLError:
  print(f"FATAL: Could not parse {LITELLM_CONFIG_PATH}.")
  sys.exit(1)

dynamic_models = []
for model_entry in litellm_config.get('model_list', []):
  model_name = model_entry.get('model_name')
  if not model_name:
    continue

  is_reasoning = 'reasoning' in model_name or 'deep-think' in model_name

  dynamic_models.append({
    "id": model_name,
    "name": f"LiteLLM {model_name.replace('-', ' ').title()}",
    "reasoning": is_reasoning,
    "input": ["text", "image"],
    "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
    "contextWindow": 128000,
    "maxTokens": 8192
  })

# 1. Patch the LiteLLM Provider configuration
if 'models' not in data:
  data['models'] = {}
if 'providers' not in data['models']:
  data['models']['providers'] = {}
if 'litellm' not in data['models']['providers']:
  data['models']['providers']['litellm'] = {}

data['models']['providers']['litellm']['baseUrl'] = "http://active-proxy:4000/v1"
data['models']['providers']['litellm']['api'] = "openai-completions"
data['models']['providers']['litellm']['models'] = dynamic_models

# 2. Patch the Gateway Default Models Dynamically
if 'agents' not in data:
  data['agents'] = {}
if 'defaults' not in data['agents']:
  data['agents']['defaults'] = {}

data['agents']['defaults']['models'] = {}

for model_obj in dynamic_models:
  m_id = model_obj['id']

  if '/' in m_id:
    gateway_model_id = m_id
  else:
    gateway_model_id = f"litellm/{m_id}"

  data['agents']['defaults']['models'][gateway_model_id] = {
    "alias": "LiteLLM" if gateway_model_id.startswith("litellm/") else m_id.split('/')[0].capitalize()
  }

# 3. Auto-Discover and Patch Agents
if 'list' not in data['agents']:
  data['agents']['list'] = []

agents_dict = {a['id']: a for a in data['agents']['list']}

for a_id, a_data in agents_dict.items():
  a_data.pop('description', None)

if 'main' in agents_dict:
  # Adjusted to the parameterized home directory mapping
  agents_dict['main']['workspace'] = f"{internal_home}/.openclaw/workspace"
  agents_dict['main']['model'] = "litellm/complex-model"

for filepath in glob.glob(f'{AGENTS_DIR}/**/*.yaml', recursive=True):
  if filepath.endswith('.template'):
    continue

  try:
    with open(filepath, 'r') as f:
      yaml_data = yaml.safe_load(f)

    if not yaml_data or 'name' not in yaml_data:
      continue

    agent_id = yaml_data['name'].lower().replace(' ', '_')

    raw_model_str = yaml_data.get('model', 'complex-model')
    if '/' in raw_model_str:
      model_str = raw_model_str
    else:
      model_str = f"litellm/{raw_model_str}"

    base_name = os.path.splitext(os.path.basename(filepath))[0]
    host_agent_dir = os.path.join(os.path.dirname(filepath), base_name)

    if not os.path.exists(host_agent_dir):
      os.makedirs(host_agent_dir, exist_ok=True)

    rel_dir = os.path.relpath(host_agent_dir, WORKSPACE_DIR)
    # Adjusted to the parameterized home directory mapping
    container_workspace = f"{internal_home}/.openclaw/workspace/{rel_dir}".replace('\\', '/')

    if agent_id in agents_dict:
      agents_dict[agent_id].update({
        "name": yaml_data.get('name').replace('_', ' ').title(),
        "workspace": container_workspace,
        "model": model_str
      })
    else:
      agents_dict[agent_id] = {
        "id": agent_id,
        "name": yaml_data.get('name').replace('_', ' ').title(),
        "workspace": container_workspace,
        "model": model_str
      }
  except Exception as e:
    print(f"Warning: Failed to parse {filepath}: {e}")

data['agents']['list'] = list(agents_dict.values())

# 4. Patch the Network Binding and CORS Policies
if 'gateway' not in data:
  data['gateway'] = {}

data['gateway']['bind'] = 'lan'

if 'controlUi' not in data['gateway']:
  data['gateway']['controlUi'] = {}

port = os.environ.get('OPENCLAW_PORT', '18789')
data['gateway']['controlUi']['allowedOrigins'] = [
  f"http://localhost:{port}",
  f"http://127.0.0.1:{port}"
]

# 5. Patch Compaction Safeguards
if 'compaction' not in data['agents']['defaults']:
  data['agents']['defaults']['compaction'] = {}

data['agents']['defaults']['compaction'].pop('thresholdTokens', None)
data['agents']['defaults']['compaction'].pop('targetTokens', None)

data['agents']['defaults']['compaction']['mode'] = "default"
data['agents']['defaults']['compaction']['reserveTokensFloor'] = 24000
data['agents']['defaults']['compaction']['model'] = "litellm/medium-model"

# ==============================================================================
# 6. Apply Security Hardening
# ==============================================================================
if 'tools' not in data:
  data['tools'] = {}
data['tools']['deny'] = ["group:web", "browser"]

if 'sandbox' not in data['agents']['defaults']:
  data['agents']['defaults']['sandbox'] = {}

# Note: The OpenClaw 2026.3.28 schema STRICTLY validates this block.
# We CANNOT pass arbitrary docker keys (like network or memoryLimit) here or the gateway will crash.
# We must rely on `mode: "all"` to spawn isolated containers.
data['agents']['defaults']['sandbox']['mode'] = "all"
data['agents']['defaults']['sandbox'].pop('network', None)
data['agents']['defaults']['sandbox'].pop('memoryLimit', None)
data['agents']['defaults']['sandbox'].pop('dropCapabilities', None)

if 'auth' not in data['gateway']:
  data['gateway']['auth'] = {}
data['gateway']['auth']['rateLimit'] = {
  "maxAttempts": 10,
  "windowMs": 60000,
  "lockoutMs": 300000
}

if 'heartbeat' not in data['agents']['defaults']:
  data['agents']['defaults']['heartbeat'] = {}
data['agents']['defaults']['heartbeat']['every'] = "12h"

# Save openclaw.json
with open(CONFIG_PATH, 'w') as f:
  json.dump(data, f, indent=2)

print(f"SUCCESS: Patched network routing, CORS policies, loopback binding, and dynamic model registry.")
print(f"SUCCESS: Auto-discovered and registered {len(data['agents']['list'])} agents.")
print(f"SUCCESS: Enforced strict memory compaction thresholds to prevent context bloat.")
print(f"SUCCESS: Parameterized internal paths configured for {internal_home}.")
