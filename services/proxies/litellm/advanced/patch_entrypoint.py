import sys
import litellm
from litellm.router_strategy.auto_router.litellm_encoder import LiteLLMRouterEncoder
from litellm.proxy.proxy_cli import run_server

def chunked_encode_queries(self, docs, **kwargs):
  batch_size = 90
  all_embeddings = []

  print(f"[PATCH] Intercepting vectorization: Chunking {len(docs)} utterances into batches of {batch_size}.")

  for i in range(0, len(docs), batch_size):
    chunk = docs[i:i + batch_size]
    print(f"[PATCH] Processing batch {i // batch_size + 1} ({len(chunk)} items)...")

    try:
      embeds = self.litellm_router_instance.embedding(
        input=chunk,
        model=self.name,
        **kwargs
      )
      sorted_data = sorted(embeds["data"], key=lambda x: x["index"])
      all_embeddings.extend([item["embedding"] for item in sorted_data])
    except Exception as e:
      raise ValueError(f"[PATCH] Router API batch call failed. Error: {e}") from e

  return all_embeddings

print("[PATCH] Injecting LiteLLMRouterEncoder.encode_queries monkey patch...")
LiteLLMRouterEncoder.encode_queries = chunked_encode_queries

if __name__ == "__main__":
  run_server()
