import sys
import litellm
from litellm.integrations.custom_logger import CustomLogger
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

# print("[PATCH] Injecting LiteLLMRouterEncoder.encode_queries monkey patch...")
# LiteLLMRouterEncoder.encode_queries = chunked_encode_queries

class ToolCallInterceptor(CustomLogger):
  """
  LiteLLM Post-Call Interceptor.
  Designed to intercept raw LLM completion responses and transform stringified
  JSON tool outputs into standard OpenAI tool_calls objects before returning to OpenClaw.
  """
  async def async_post_call_success_hook(self, data, user_api_key_dict, response):
    try:
      print(f"[INTERCEPTOR] async_post_call_success_hook fired for model: {data.get('model', 'unknown')}", flush=True)
      try:
          if hasattr(response, 'choices') and len(response.choices) > 0:
              content = response.choices[0].message.content
              print(f"\n[INTERCEPTOR] RAW PAYLOAD START:\n{content}\n[INTERCEPTOR] RAW PAYLOAD END\n", flush=True)
      except Exception as inner_e:
          print(f"[INTERCEPTOR] Could not extract raw payload for logging: {inner_e}", flush=True)
      return response
    except Exception as e:
      print(f"[INTERCEPTOR] Error during execution: {e}", flush=True)
      return response

print("[PATCH] ToolCallInterceptor loaded into environment. Registering callback...")
litellm.callbacks = [ToolCallInterceptor()]

if __name__ == "__main__":
  run_server()
