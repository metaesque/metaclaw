import json
import requests
import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

URL = "http://localhost:4000/v1/embeddings"
HEADERS = {
  "Content-Type": "application/json",
  "Authorization": "Bearer sk-openclaw-master-key-31415"
}
MODEL_NAME = "gemini/gemini-embedding-001"

def fetch_embeddings(texts):
  """Fetches vector arrays from the LiteLLM proxy."""
  payload = {
    "model": MODEL_NAME,
    "input": texts
  }
  response = requests.post(URL, headers=HEADERS, json=payload)
  response.raise_for_status()
  data = response.json()
  sorted_data = sorted(data["data"], key=lambda x: x["index"])
  return [item["embedding"] for item in sorted_data]

def main():
  print("Loading router.json...")
  with open('../router.json', 'r') as f:
    config = json.load(f)

  routes = config.get("routes", [])
  if not routes:
    print("No routes found in router.json.")
    return

  all_embeddings = []
  labels = []
  colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728']

  print(f"Fetching embeddings from {URL}...")
  for i, route in enumerate(routes):
    tier_name = route["name"]
    utterances = route["utterances"]
    print(f"  Vectorizing {len(utterances)} utterances for '{tier_name}'...")

    embeddings = fetch_embeddings(utterances)
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
  plt.legend(title="Complexity Tiers", fontsize=10, title_fontsize=12)
  plt.grid(True, linestyle='--', alpha=0.5)
  plt.tight_layout()

  print("Rendering plot...")
  plt.show()

if __name__ == "__main__":
  main()
