import sys
import json
import uuid
import litellm
from litellm.integrations.custom_logger import CustomLogger
from litellm.router_strategy.auto_router.litellm_encoder import LiteLLMRouterEncoder
from litellm.proxy.proxy_cli import run_server
from litellm.types.utils import ModelResponse, ChatCompletionMessageToolCall, Function

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
  async def async_post_call_success_hook(self, data: dict, user_api_key_dict, response):
    try:
      print(f"[INTERCEPTOR] async_post_call_success_hook fired for model: {data.get('model', 'unknown')}", flush=True)

      # Defensively extract raw response data regardless of its type (dict vs ModelResponse)
      resp_data = None
      if hasattr(response, 'model_dump'):
          resp_data = response.model_dump()
      elif hasattr(response, 'dict'):
          resp_data = response.dict()
      elif isinstance(response, dict):
          resp_data = response
      else:
          resp_data = {"raw_str": str(response)}

      print(f"\n[INTERCEPTOR] RAW PAYLOAD START:\n{json.dumps(resp_data, indent=2)}\n[INTERCEPTOR] RAW PAYLOAD END\n", flush=True)

      # Try to mutate if it is a ModelResponse object natively supporting choices
      if hasattr(response, 'choices') and len(response.choices) > 0:
          choice = response.choices[0]
          if hasattr(choice, 'message'):
              message = choice.message
              content = getattr(message, 'content', None)

              if content and isinstance(content, str):
                  clean_content = content.strip()
                  if clean_content.startswith('```json'):
                      clean_content = clean_content[7:]
                  elif clean_content.startswith('```'):
                      clean_content = clean_content[3:]
                  if clean_content.endswith('```'):
                      clean_content = clean_content[:-3]
                  clean_content = clean_content.strip()

                  # Loosened heuristic: Look for tool call signatures anywhere in the cleaned content
                  if '{' in clean_content and '"name"' in clean_content and '"parameters"' in clean_content:
                      # Extract everything from the first '{' to the last '}'
                      try:
                          start_idx = clean_content.find('{')
                          end_idx = clean_content.rfind('}') + 1
                          json_str = clean_content[start_idx:end_idx]

                          tool_data = json.loads(json_str)
                          tool_call = ChatCompletionMessageToolCall(
                              id=f"call_{uuid.uuid4().hex[:16]}",
                              type="function",
                              function=Function(
                                  name=tool_data.get("name"),
                                  arguments=json.dumps(tool_data.get("parameters", {}))
                              )
                          )
                          message.content = None
                          message.tool_calls = [tool_call]
                          choice.finish_reason = "tool_calls"
                          print(f"[INTERCEPTOR] Successfully transformed content into tool_call: {tool_data.get('name')}", flush=True)
                      except Exception as inner_e:
                          print(f"[INTERCEPTOR] Failed JSON decoding during heuristic mutation: {inner_e}", flush=True)

      return response
    except Exception as e:
      print(f"[INTERCEPTOR] Error during execution: {e}", flush=True)
      return response

print("[PATCH] ToolCallInterceptor loaded into environment. Registering callback...")
litellm.callbacks = [ToolCallInterceptor()]

if __name__ == "__main__":
  run_server()
