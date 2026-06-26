import os
import argparse
import requests
import json
import sys

def load_local_env():
    """
    Manually parses the .env file in the current working directory.
    This ensures scripts can find keys even if they haven't been 'exported'
    to the shell environment.
    """
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def main():
    load_local_env()

    parser = argparse.ArgumentParser(description="LiteLLM Proxy Routing Tester")
    parser.add_argument("-t", "--type", choices=['simple', 'medium', 'complex', 'reasoning'],
                        default='simple', help="The type of prompt to simulate.")
    args = parser.parse_args()

    # Configuration extraction
    master_key = os.getenv("ACTIVE_PROXY_KEY")
    port = os.getenv("LITELLM_PORT", "4000")

    if not master_key:
        print(f"FATAL: ACTIVE_PROXY_KEY not found in environment or .env file.")
        print(f"Current Directory: {os.getcwd()}")
        sys.exit(1)

    url = f"http://localhost:{port}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {master_key}",
        "Content-Type": "application/json"
    }

    # Define test prompts that trigger specific routes in utterances-tiers.yaml
    prompts = {
        "simple": "What is 2+2?",
        "medium": "Summarize the history of the Roman Empire in three sentences.",
        "complex": "Write a Python script that uses recursion to solve the Tower of Hanoi.",
        "reasoning": "If I have three apples and you take away two, how many apples do I have left? Explain the logic."
    }

    model_map = {
        "simple": "simple-model",
        "medium": "medium-model",
        "complex": "complex-model",
        "reasoning": "reasoning-model"
    }

    payload = {
        "model": model_map[args.type],
        "messages": [{"role": "user", "content": prompts[args.type]}],
        "temperature": 0.1
    }

    print(f"--- Sending {args.type.upper()} request to LiteLLM Proxy ---")
    print(f"Endpoint: {url}")
    print(f"Prompt:   '{prompts[args.type]}'\n")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            actual_model = result.get('model', 'unknown')
            print(f"SUCCESS (Routed to: {actual_model})")
            print("-" * 40)
            print(content)
            print("-" * 40)
        else:
            print(f"FAILURE: Received HTTP {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"ERROR: Connection failed. Is the proxy running on port {port}?")
        print(f"Details: {e}")

if __name__ == "__main__":
    main()
