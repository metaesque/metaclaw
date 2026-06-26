import json
import requests
import numpy as np

URL = "http://localhost:4000/v1/embeddings"
HEADERS = {
  "Content-Type": "application/json",
  "Authorization": "Bearer sk-openclaw-master-key-31415"
}
MODEL_NAME = "gemini/gemini-embedding-001"

def fetch_embeddings(texts):
  """Fetches vector arrays from the local LiteLLM proxy."""
  payload = {
    "model": MODEL_NAME,
    "input": texts
  }
  response = requests.post(URL, headers=HEADERS, json=payload)
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
  print("Loading router.json...")
  with open('../router.json', 'r') as f:
    config = json.load(f)

  routes = config.get("routes", [])
  cluster_embeddings = {}

  print("Vectorizing tier utterances from local proxy...")
  for route in routes:
    tier_name = route["name"]
    utterances = route["utterances"]
    cluster_embeddings[tier_name] = fetch_embeddings(utterances)

  test_prompts = [
    "What is the capital of France?",
    "Convert 500 miles to kilometers.",
    "Write a bash script to parse nginx access logs and output a summary.",
    "Draft a contract termination notice for a commercial lease.",
    "Design an event-driven microservice architecture utilizing Kafka.",
    "Write a custom Python metaclass for a multi-agent framework.",
    "Formulate a mathematical proof for the twin prime conjecture.",
    "Evaluate the epistemological limits of artificial superintelligence.",
    "Give me a recipe for chocolate chip cookies."
  ]

  print("Vectorizing test prompts...\n")
  test_embeddings = fetch_embeddings(test_prompts)

  headers = ["Test Prompt", "Simple", "Medium", "Complex", "Reasoning", "Max Match"]
  print(f"{headers[0]:<72} | {headers[1]:<6} | {headers[2]:<6} | {headers[3]:<7} | {headers[4]:<9} | {headers[5]}")
  print("-" * 130)

  for i, test_emb in enumerate(test_embeddings):
    scores = {}
    for tier_name, utterances_embs in cluster_embeddings.items():
      max_score = max([cosine_similarity(test_emb, u_emb) for u_emb in utterances_embs])
      scores[tier_name] = max_score

    prompt_trunc = (test_prompts[i][:69] + '...') if len(test_prompts[i]) > 72 else test_prompts[i]

    s_score = f"{scores['simple-model']:.3f}"
    m_score = f"{scores['medium-model']:.3f}"
    c_score = f"{scores['complex-model']:.3f}"
    r_score = f"{scores['reasoning-model']:.3f}"

    best_tier = max(scores, key=scores.get)
    best_val = scores[best_tier]

    print(f"{prompt_trunc:<72} | {s_score:<6} | {m_score:<6} | {c_score:<7} | {r_score:<9} | {best_tier} ({best_val:.3f})")

if __name__ == "__main__":
  main()
