import os
import argparse
import requests
import json
import sys

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

def main():
    load_local_env()

    parser = argparse.ArgumentParser(description="OpenClaw Gateway Routing Tester")
    parser.add_argument("-t", "--type", choices=['simple', 'medium', 'complex', 'frontier'],
                        default='simple', help="The type of prompt to simulate.")
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

    # Define test prompts
    prompts = {
        "simple": "What is 2+2?",
        "medium": "Summarize the history of the Roman Empire in three sentences.",
        "complex": "Write a Python script that uses recursion to solve the Tower of Hanoi.",
        "frontier": "If I have three apples and you take away two, how many apples do I have left? Explain the logic."
    }

    # We send ALL requests targeting the default agent ('openclaw') to let the
    # lexical_predictive.js hook intercept and score the complexity automatically.
    payload = {
        "model": "openclaw",
        "messages": [{"role": "user", "content": prompts[args.type]}],
        "temperature": 0.1
    }

    print(f"--- Sending {args.type.upper()} request to OpenClaw Gateway ---")
    print(f"Endpoint: {url}")
    print(f"Prompt:   '{prompts[args.type]}'\n")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=300)
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
