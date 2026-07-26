import json
import requests
import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import os
import sys

def load_local_env(repo_root):
    """
    Dynamically loads the API key from local environment configuration files across known paths.
    """
    # 1. Try litellm .env.json
    env_json_path = os.path.join(repo_root, 'services', 'proxies', 'litellm', '.env.json')
    if os.path.exists(env_json_path):
        try:
            with open(env_json_path, 'r') as f:
                data = json.load(f)
                for k, v in data.items():
                    os.environ[k] = str(v)
        except Exception:
            pass

    # 2. Try litellm .env
    litellm_env = os.path.join(repo_root, 'services', 'proxies', 'litellm', '.env')
    if os.path.exists(litellm_env):
        with open(litellm_env, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in os.environ:
                        os.environ[key] = value.strip('"\' ')

    # 3. Try root .env
    root_env = os.path.join(repo_root, '.env')
    if os.path.exists(root_env):
        with open(root_env, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in os.environ:
                        os.environ[key] = value.strip('"\' ')

def fetch_embeddings(urls, headers, texts):
  """Attempts fetching vector arrays, cascading across proxy IP targets if needed."""
  payload = {
    "model": "gemini/gemini-embedding-001",
    "input": texts
  }
  last_err = None
  for url in urls:
    try:
      response = requests.post(url, headers=headers, json=payload, timeout=15)
      response.raise_for_status()
      data = response.json()
      sorted_data = sorted(data["data"], key=lambda x: x["index"])
      return [item["embedding"] for item in sorted_data]
    except Exception as e:
      last_err = e
      continue
  raise last_err

def main():
  # Absolute path resolution to prevent CWD dependency errors
  script_dir = os.path.dirname(os.path.abspath(__file__))
  proxy_dir = os.path.dirname(script_dir)
  repo_root = os.path.dirname(os.path.dirname(os.path.dirname(proxy_dir)))

  load_local_env(repo_root)

  master_key = os.environ.get('ACTIVE_PROXY_KEY')
  if not master_key:
      print("FATAL: ACTIVE_PROXY_KEY not found in environment or .env files.")
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

  # Formulate candidate URLs (Tailscale IP, loopback IPs)
  target_urls = list(dict.fromkeys([
      f"http://{proxy_ip}:4000/v1/embeddings",
      "http://127.0.0.1:4000/v1/embeddings",
      "http://localhost:4000/v1/embeddings"
  ]))

  headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {master_key}"
  }

  router_path = os.path.join(proxy_dir, "router.json")
  print(f"Loading {router_path}...")
  if not os.path.exists(router_path):
      print(f"FATAL: {router_path} not found.")
      sys.exit(1)

  with open(router_path, 'r') as f:
    config = json.load(f)

  routes = config.get("routes", [])
  if not routes:
    print("No routes found in router.json.")
    sys.exit(0)

  all_embeddings = []
  labels = []
  colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

  print(f"Fetching embeddings from proxy endpoints...")
  for i, route in enumerate(routes):
    tier_name = route["name"]
    utterances = route["utterances"]
    print(f"  Vectorizing {len(utterances)} utterances for '{tier_name}'...")

    embeddings = fetch_embeddings(target_urls, headers, utterances)
    all_embeddings.extend(embeddings)
    labels.extend([(tier_name, colors[i % len(colors)])] * len(utterances))

  X = np.array(all_embeddings)
  tier_labels = [label[0] for label in labels]
  tier_colors = [label[1] for label in labels]

  print(f"Reducing dimensionality of {X.shape[0]} vectors ({X.shape[1]} dimensions) to 2D...")
  tsne = TSNE(n_components=2, perplexity=15, random_state=42, init='pca', learning_rate='auto')
  X_2d = tsne.fit_transform(X)

  print("Generating scatter plot...")
  plt.figure(figsize=(12, 8))

  unique_tiers = list(dict.fromkeys(tier_labels))
  unique_colors = list(dict.fromkeys(tier_colors))

  for tier, color in zip(unique_tiers, unique_colors):
    idx = [i for i, label in enumerate(tier_labels) if label == tier]
    plt.scatter(
      X_2d[idx, 0],
      X_2d[idx, 1],
      c=color,
      label=tier,
      alpha=0.7,
      edgecolors='w',
      s=100
    )

  plt.title('Semantic Auto Router Boundaries: 2D t-SNE Projection', fontsize=16)
  plt.xlabel('t-SNE Dimension 1', fontsize=12)
  plt.ylabel('t-SNE Dimension 2', fontsize=12)
  plt.legend(title="Complexity Tiers / Agents", fontsize=10, title_fontsize=12, bbox_to_anchor=(1.05, 1), loc='upper left')
  plt.grid(True, linestyle='--', alpha=0.5)
  plt.tight_layout()

  print("Saving plot to disk...")
  out_path = os.path.join(proxy_dir, 'advanced', 'semantic_clusters.png')
  plt.savefig(out_path, dpi=300, bbox_inches='tight')
  print(f"Plot successfully saved to {out_path}")

if __name__ == "__main__":
  main()
