import os
import argparse
import requests
import json
import sys
import glob
import yaml

def load_local_env():
    """
    Dynamically finds and loads the ACTIVE_PROXY_KEY from the repository config.
    OpenClaw uses this same key for its Gateway authentication token by default.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)

    env_json_path = os.path.join(repo_root, 'services', 'proxies', 'litellm', '.env.json')
    if os.path.exists(env_json_path):
        try:
            with open(env_json_path, 'r') as f:
                data = json.load(f)
                for k, v in data.items():
                    os.environ[k] = str(v)
        except Exception:
            pass

    gateway_env_path = os.path.join(repo_root, 'services', 'gateways', 'openclaw', '.env')
    if os.path.exists(gateway_env_path):
        with open(gateway_env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in os.environ:
                        os.environ[key] = value.strip('"\' ')

def get_agent_test_prompt(agent_arg, prompt_type):
    """
    Extracts custom test prompts from the agent's YAML definition based on the
    requested complexity type, falling back to generalized defaults if missing.
    """
    # Fallback default prompts
    prompts = {
        "simple": "What is 2+2?",
        "medium": "Summarize the history of the Roman Empire in three sentences.",
        "complex": "Write a Python script that uses recursion to solve the Tower of Hanoi.",
        "frontier": "If I have three apples and you take away two, how many apples do I have left? Explain the logic."
    }

    agent_name = agent_arg
    if agent_name == 'openclaw':
        agent_name = 'orchestrator'
    elif '/' in agent_name:
        agent_name = agent_name.split('/', 1)[1]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    workspace_dir = os.environ.get('OPENCLAW_WORKSPACE')

    if not workspace_dir:
        workspace_dir = os.path.abspath(os.path.join(repo_root, '..', 'workspace'))
    else:
        workspace_dir = os.path.expanduser(workspace_dir)

    search_path = os.path.join(workspace_dir, 'agents', '**', '*.yaml')
    yaml_files = glob.glob(search_path, recursive=True)

    for yf in yaml_files:
        name = os.path.splitext(os.path.basename(yf))[0]
        rel_path = os.path.relpath(yf, os.path.join(workspace_dir, 'agents'))
        parts = rel_path.replace('\\', '/').split('/')
        if len(parts) > 1:
            team_id = "_".join(parts[:-1])
            test_id = f"{team_id}_{name}"
        else:
            test_id = name

        if test_id == agent_name or name == agent_name:
            try:
                with open(yf, 'r', encoding='utf-8') as f:
                    agent_data = yaml.safe_load(f)
                    tests = agent_data.get('tests', [])
                    for t in tests:
                        t_model = t.get('model', '').replace('-model', '')
                        if t_model == prompt_type:
                            return t.get('prompt')
            except Exception:
                pass

    return prompts.get(prompt_type)

def main():
    load_local_env()

    parser = argparse.ArgumentParser(description="OpenClaw Gateway Routing Tester")
    parser.add_argument("-t", "--type", choices=['simple', 'medium', 'complex', 'frontier'],
                        default='simple', help="The type of prompt to simulate.")
    parser.add_argument("-a", "--agent", default="openclaw", help="The specific agent ID to target (defaults to the global 'openclaw' default agent).")
    args = parser.parse_args()

    # OpenClaw shares the proxy key as its gateway token by default
    master_key = os.getenv("OPENCLAW_GATEWAY_TOKEN", os.getenv("ACTIVE_PROXY_KEY"))
    port = os.getenv("OPENCLAW_PORT", "18789")

    if not master_key:
        print(f"FATAL: Gateway Token / Proxy Key not found in environment.")
        sys.exit(1)

    url = f"http://localhost:{port}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {master_key}",
        "Content-Type": "application/json"
    }

    prompt_text = get_agent_test_prompt(args.agent, args.type)

    # We send requests targeting the specified agent to let the
    # lexical_predictive.js hook intercept and score the complexity automatically.
    payload = {
        "model": args.agent,
        "messages": [{"role": "user", "content": prompt_text}],
        "temperature": 0.1
    }

    print(f"--- Sending {args.type.upper()} request to OpenClaw Gateway ---")
    print(f"Endpoint: {url}")
    print(f"Agent:    '{args.agent}'")
    print(f"Prompt:   '{prompt_text}'\n")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=900)
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            # OpenClaw passes through the final resolved model in the response
            actual_model = result.get('model', 'unknown')
            print(f"SUCCESS (Resolved to: {actual_model})")
            print("-" * 40)
            print(content)
            print("-" * 40)
        else:
            print(f"FAILURE: Received HTTP {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"ERROR: Connection failed. Is the OpenClaw gateway running on port {port}?")
        print(f"Details: {e}")

if __name__ == "__main__":
    main()
