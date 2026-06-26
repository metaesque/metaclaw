import argparse
import json
import random
import yaml
import sys
import os

def main():
  parser = argparse.ArgumentParser(description="Compile YAML utterances into LiteLLM router.json")
  parser.add_argument('-o', '--output', type=str, default='router.json', help='Output JSON file')
  parser.add_argument('-k', '--kind', type=str, choices=['tiers', 'interests'], default='tiers', help='Type of utterances to compile (tiers or interests)')
  parser.add_argument('-u', '--per_route', type=int, default=1000, help='Maximum utterances per route')
  parser.add_argument('-r', '--random', action='store_true', help='Randomly sample utterances if exceeding per_route limit')
  parser.add_argument('-t', '--threshold', type=float, default=0.70, help='Score threshold for semantic routing')

  args = parser.parse_args()
  input_file = f"utterances-{args.kind}.yaml"

  if not os.path.exists(input_file):
    print(f"Error: Input file '{input_file}' not found.")
    sys.exit(1)

  with open(input_file, 'r', encoding='utf-8') as f:
    try:
      utterances_dict = yaml.safe_load(f)
    except yaml.YAMLError as e:
      print(f"Error parsing YAML: {e}")
      sys.exit(1)

  routes = []
  for model_name, utterances in utterances_dict.items():
    if not isinstance(utterances, list):
      print(f"Warning: Utterances for '{model_name}' must be a list. Skipping.")
      continue

    if len(utterances) > args.per_route:
      if args.random:
        selected = random.sample(utterances, args.per_route)
      else:
        selected = utterances[:args.per_route]
    else:
      selected = utterances

    routes.append({
      "name": model_name,
      "score_threshold": args.threshold,
      "utterances": selected
    })

  router_config = {
    "encoder_type": "litellm",
    "encoder_name": "gemini/gemini-embedding-001",
    "routes": routes
  }

  new_content = json.dumps(router_config, indent=2) + "\n"

  # Prevent timestamp cascades in Make by only writing if content has changed
  if os.path.exists(args.output):
    with open(args.output, 'r', encoding='utf-8') as f:
      old_content = f.read()
    if old_content == new_content:
      print(f"No changes detected. {args.output} is up to date.")
      sys.exit(0)

  with open(args.output, 'w', encoding='utf-8') as f:
    f.write(new_content)

  print(f"Successfully generated {args.output} from {input_file} containing {len(routes)} routes.")

if __name__ == "__main__":
  main()
