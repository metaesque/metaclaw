import json
import requests
import numpy as np
import os
import sys

def load_local_env(repo_root):
    """
    Dynamically loads the API key from the local environment files.
    """
    env_json_path = os.path.join(repo_root, 'services', 'proxies', 'litellm', '.env.json')
    if os.path.exists(env_json_path):
        try:
            with open(env_json_path, 'r') as f:
                data = json.load(f)
                for k, v in data.items():
                    os.environ[k] = str(v)
        except Exception:
            pass

    env_path = os.path.join(repo_root, '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in os.environ:
                        os.environ[key] = value.strip('"\' ')

def fetch_embeddings(url, headers, texts):
  """Fetches vector arrays from the local LiteLLM proxy."""
  payload = {
    "model": "gemini/gemini-embedding-001",
    "input": texts
  }
  response = requests.post(url, headers=headers, json=payload)
  response.raise_for_status()
  data = response.json()
  sorted_data = sorted(data["data"], key=lambda x: x["index"])
  return [item["embedding"] for item in sorted_data]

def cosine_similarity(vec_a, vec_b):
  """Calculates the cosine similarity between two vectors."""
  dot_product = np.dot(vec_a, vec_b)
  norm_a = np.linalg.norm(vec_a)
  norm_b = np.linalg.norm(vec_b)
  if norm_a == 0 or norm_b == 0:
    return 0.0
  return dot_product / (norm_a * norm_b)

def main():
  # Absolute path resolution to prevent CWD dependency errors
  script_dir = os.path.dirname(os.path.abspath(__file__))
  proxy_dir = os.path.dirname(script_dir)
  repo_root = os.path.dirname(os.path.dirname(os.path.dirname(proxy_dir)))

  load_local_env(repo_root)

  master_key = os.environ.get('ACTIVE_PROXY_KEY')
  if not master_key:
      print("FATAL: ACTIVE_PROXY_KEY not found in environment.")
      sys.exit(1)

  # Resolve the dynamic proxy IP from the cluster profile
  proxy_ip = "127.0.0.1"
  profile_path = os.path.join(repo_root, "profile.json")
  if os.path.exists(profile_path):
      with open(profile_path, 'r') as f:
          try:
              profile = json.load(f)
              for node in profile.get('nodes', []):
                  if 'proxy' in node.get('providers', {}):
                      proxy_ip = node.get('hardware', {}).get('ip_address', '127.0.0.1')
                      break
          except json.JSONDecodeError:
              pass

  url = f"http://{proxy_ip}:4000/v1/embeddings"
  headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {master_key}"
  }

  router_path = os.path.join(proxy_dir, "router.json")
  print(f"Loading {router_path}...")
  if not os.path.exists(router_path):
      print("FATAL: router.json not found.")
      sys.exit(1)

  with open(router_path, 'r') as f:
    config = json.load(f)

  routes = config.get("routes", [])
  cluster_embeddings = {}

  print(f"Vectorizing utterances from proxy ({proxy_ip})...")
  for route in routes:
    tier_name = route["name"]
    utterances = route["utterances"]
    cluster_embeddings[tier_name] = fetch_embeddings(url, headers, utterances)

  test_prompts = [
    "What is the capital of France?",
    "Convert 500 miles to kilometers.",
    "Write a bash script to parse nginx access logs and output a summary.",
    "Draft a contract termination notice for a commercial lease.",
    "Design an event-driven microservice architecture utilizing Kafka.",
    "Write a custom Python metaclass for a multi-agent framework.",
    "Formulate a mathematical proof for the twin prime conjecture.",
    "Evaluate the epistemological limits of artificial superintelligence.",
    "Give me a recipe for chocolate chip cookies.",
    "Extract the gross revenue from this AAPL 10-K filing.",
    "Calculate the current RSI and MACD for Ethereum."
  ]

  print("Vectorizing test prompts...\n")
  test_embeddings = fetch_embeddings(url, headers, test_prompts)

  headers_print = ["Test Prompt", "Top Match", "Confidence Score"]
  print(f"{headers_print[0]:<72} | {headers_print[1]:<25} | {headers_print[2]}")
  print("-" * 125)

  for i, test_emb in enumerate(test_embeddings):
    scores = {}
    for tier_name, utterances_embs in cluster_embeddings.items():
      max_score = max([cosine_similarity(test_emb, u_emb) for u_emb in utterances_embs])
      scores[tier_name] = max_score

    prompt_trunc = (test_prompts[i][:69] + '...') if len(test_prompts[i]) > 72 else test_prompts[i]

    best_tier = max(scores, key=scores.get)
    best_val = scores[best_tier]

    print(f"{prompt_trunc:<72} | {best_tier:<25} | {best_val:.3f}")

if __name__ == "__main__":
  main()
