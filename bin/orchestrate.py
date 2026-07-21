import json
import os
import subprocess
import socket
import sys

# SUPER CRITICAL: REMOTE SSH PRESERVATION MANDATE
# This script MUST NEVER deploy Docker Tailscale on a node that relies on a bare-metal
# Tailscale daemon for remote SSH access.

# Ensure we can import metaclaw from the lib directory
sys.path.insert(
  0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
)
import metaclaw

def get_tier_weight(t):
    """Safely translates string tiers (e.g., '3E') into integer weights for logic evaluation."""
    if isinstance(t, int): return t
    t = str(t).upper()
    if t.startswith('3'): return 3
    if t == '4': return 4
    return int(t) if t.isdigit() else 0

def main():
  """
  The MetaClaw State Enforcer.
  Reads profile.json, tears down deprecated services, establishes new symlinks,
  generates the .env.cluster cross-node routing configuration, and tracks
  bare-metal (.metal) state dependencies.
  """
  profile_path = "profile.json"
  if not os.path.exists(profile_path):
    print(
      "[Orchestrator] No profile.json found. "
      "Please run 'python bin/sysprofile.py' first."
    )
    return

  with open(profile_path, "r") as f:
    profile = json.load(f)

  hostname = socket.gethostname()
  my_node = next(
    (n for n in profile.get("nodes", []) if n["hostname"] == hostname), None
  )

  if not my_node:
    print(f"[Orchestrator] FATAL: Node '{hostname}' not found in profile.json.")
    return

  providers = my_node.get("providers", {})
  services_dir = "services"

  if not os.path.exists(services_dir):
    os.makedirs(services_dir)

  # --------------------------------------------------------------------------
  # 1. TEARDOWN & RECONCILIATION
  # --------------------------------------------------------------------------
  existing_symlinks = [
    d for d in os.listdir(services_dir)
    if os.path.islink(os.path.join(services_dir, d))
  ]

  for sym in existing_symlinks:
    sym_path = os.path.join(services_dir, sym)
    needs_teardown = False

    if sym not in providers:
      needs_teardown = True
    else:
      # Check if transition requires teardown (e.g., target changed or metal state flipped)
      prov_data = providers[sym]
      if isinstance(prov_data, dict):
        provider = prov_data.get("uid")
        metal = prov_data.get("metal", False)
      else:
        provider = prov_data
        metal = False

      uids = metaclaw.Inst.structure()['services'][sym]['uids']
      target_path = os.path.join(uids, provider)
      current_target = os.readlink(sym_path)
      was_metal = os.path.exists(os.path.join(sym_path, ".metal"))

      if current_target != target_path or was_metal != metal:
        needs_teardown = True

    if needs_teardown:
      print(f"[Orchestrator] Teardown triggered for service: {sym}")
      env = dict(os.environ, OPENCLAW_SKIP_ENV="1")
      try:
        real_sym_path = os.path.realpath(sym_path)
        subprocess.run(
          ["make", "--no-print-directory", "-C", real_sym_path, "down"],
          env=env, check=False
        )
      except Exception as e:
        print(f"[Orchestrator] Warning: Teardown script failed for {sym}: {e}")

      if sym not in providers or current_target != target_path:
        os.remove(sym_path)
        print(f"[Orchestrator] Removed symlink: {sym}")

  # --------------------------------------------------------------------------
  # 2. GLOBAL MODEL RESOLUTION
  # --------------------------------------------------------------------------
  # Evaluate the cluster topography globally so we can inject target model strings
  # into multiple provider configurations (Proxy vs Runner) symmetrically.

  cluster_nodes = profile.get("nodes", [])
  cluster_tier_value = max([get_tier_weight(n.get("tier", 0)) for n in cluster_nodes] + [0])
  compute_node = next((n for n in cluster_nodes if "compute" in n.get("planes", [])), None)

  target_simple = "ollama/gemma4:e4b"
  if cluster_tier_value >= 2 and compute_node:
      target_medium = "ollama/qwen3:32b"
      target_complex = "ollama/ingu627/llama4-scout-q4:109b"
  else:
      target_medium = "gemini/gemini-2.5-flash"
      target_complex = "gemini/gemini-3.1-pro-preview"

  # --------------------------------------------------------------------------
  # 3. PROVISIONING
  # --------------------------------------------------------------------------
  for svc, prov_data in providers.items():
    if isinstance(prov_data, dict):
      provider = prov_data.get("uid")
      metal = prov_data.get("metal", False)
    else:
      provider = prov_data
      metal = False

    if svc not in metaclaw.Inst.structure()['services']:
      continue

    uids = metaclaw.Inst.structure()['services'][svc]['uids']
    sym_path = os.path.join(services_dir, svc)
    target_path = os.path.join(uids, provider)

    if not os.path.lexists(sym_path):
      cwd = os.getcwd()
      os.chdir(services_dir)
      os.symlink(target_path, svc)
      print(f'NOTE: created symlink from {target_path} to {svc}')
      os.chdir(cwd)

    metal_flag_path = os.path.join(sym_path, ".metal")
    # CRITICAL LIFELINE PRESERVATION:
    # Overrides matrix settings if the node is headless OR tailscale is already running natively
    if svc == "network":
        metal = my_node.get("hardware", {}).get("headless", False) or my_node.get("hardware", {}).get("tailscale_active", False)

    if metal:
      with open(metal_flag_path, "w") as f:
        f.write("1\n")
    else:
      if os.path.exists(metal_flag_path):
        os.remove(metal_flag_path)

    real_provider_path = os.path.join(services_dir, uids, provider)
    env_json_path = os.path.join(real_provider_path, ".env.json")
    env_data = {}
    if os.path.exists(env_json_path):
      try:
        with open(env_json_path, "r") as f:
          env_data = json.load(f)
      except json.JSONDecodeError:
        pass

    seeded = False
    if provider == "ollama":
      if len(cluster_nodes) > 1:
        env_data["OLLAMA_HOST"] = "0.0.0.0"
      else:
        env_data["OLLAMA_HOST"] = "127.0.0.1"

      # Purge the legacy overrides to prevent discovery collisions
      if "HSA_OVERRIDE_GFX_VERSION" in env_data:
          del env_data["HSA_OVERRIDE_GFX_VERSION"]
      if "HIP_VISIBLE_DEVICES" in env_data:
          del env_data["HIP_VISIBLE_DEVICES"]

      gpu_detected = my_node.get("hardware", {}).get("gpu_detected", "")
      is_linux = my_node.get("hardware", {}).get("os", "") == "Linux"

      # Hardcode Vulkan compute backend exclusively for AMD APUs (RDNA 3.5 specific)
      # We explicitly scope this to the exact hardware running on *this* node.
      if is_linux and "AMD" in gpu_detected and "APU" in gpu_detected:
          env_data["OLLAMA_VULKAN"] = "1"
          env_data["OLLAMA_IGPU_ENABLE"] = "1"
          env_data["ROCR_VISIBLE_DEVICES"] = "none"
          env_data["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"
      else:
          for key in ["OLLAMA_VULKAN", "OLLAMA_IGPU_ENABLE", "ROCR_VISIBLE_DEVICES", "HSA_OVERRIDE_GFX_VERSION"]:
              if key in env_data:
                  del env_data[key]

      # INVARIANT: Judge Model on Control Plane
      # We explicitly deploy the simple/judge model on the Control node for low-latency routing,
      # while heavy models are assigned to the Compute node. Do NOT remove this logic.
      models_to_pull = []
      if "control" in my_node.get("planes", []):
          models_to_pull.append(target_simple)

      if "compute" in my_node.get("planes", []):
          models_to_pull.extend([target_medium, target_complex])

      env_data["OLLAMA_TARGET_MODELS"] = " ".join(list(dict.fromkeys(models_to_pull)))
      seeded = True

    elif provider == "litellm":
      for legacy_key in ["TIER_0_APIKEY", "TIER_1_APIKEY", "GEMINI_API_KEY_SIMPLE", "GEMINI_API_KEY_MEDIUM", "GEMINI_API_KEY_COMPLEX", "GEMINI_API_KEY_REASONING", "GEMINI_API_KEY_EMBEDDING"]:
          if legacy_key in env_data:
              del env_data[legacy_key]

      if cluster_tier_value >= 2 and compute_node:
        compute_ip = compute_node.get("hardware", {}).get("ip_address", "127.0.0.1")

        env_data["SIMPLE_MODEL_ID"] = target_simple
        env_data["SIMPLE_MODEL_API_BASE"] = "http://host.docker.internal:11434"
        env_data["SIMPLE_MODEL_API_KEY"] = "sk-local-ollama-key"

        env_data["MEDIUM_MODEL_ID"] = target_medium
        env_data["MEDIUM_MODEL_API_BASE"] = f"http://{compute_ip}:11434"
        env_data["MEDIUM_MODEL_API_KEY"] = "sk-local-ollama-key"

        env_data["COMPLEX_MODEL_ID"] = target_complex
        env_data["COMPLEX_MODEL_API_BASE"] = f"http://{compute_ip}:11434"
        env_data["COMPLEX_MODEL_API_KEY"] = "sk-local-ollama-key"

        env_data["FRONTIER_MODEL_ID"] = "gemini/gemini-3.1-pro-preview"
        env_data["FRONTIER_MODEL_API_BASE"] = ""
        env_data["FRONTIER_MODEL_API_KEY"] = "${GEMINI_API_KEY}"
      else:
        env_data["SIMPLE_MODEL_ID"] = "gemini/gemini-2.5-flash-lite"
        env_data["SIMPLE_MODEL_API_BASE"] = ""
        env_data["SIMPLE_MODEL_API_KEY"] = "${GEMINI_API_KEY}"

        env_data["MEDIUM_MODEL_ID"] = target_medium
        env_data["MEDIUM_MODEL_API_BASE"] = ""
        env_data["MEDIUM_MODEL_API_KEY"] = "${GEMINI_API_KEY}"

        env_data["COMPLEX_MODEL_ID"] = target_complex
        env_data["COMPLEX_MODEL_API_BASE"] = ""
        env_data["COMPLEX_MODEL_API_KEY"] = "${GEMINI_API_KEY}"

        env_data["FRONTIER_MODEL_ID"] = "gemini/gemini-3.1-pro-preview"
        env_data["FRONTIER_MODEL_API_BASE"] = ""
        env_data["FRONTIER_MODEL_API_KEY"] = "${GEMINI_API_KEY}"

      seeded = True

    if seeded:
      os.makedirs(real_provider_path, exist_ok=True)
      with open(env_json_path, "w") as f:
        json.dump(env_data, f, indent=2)

  # --------------------------------------------------------------------------
  # 4. DISTRIBUTED DNS GENERATION
  # --------------------------------------------------------------------------
  env_lines = [
    "# =====================================================================\n",
    "# AUTOMATICALLY GENERATED BY ORCHESTRATE.PY - DO NOT EDIT\n",
    "# =====================================================================\n"
  ]

  for node in profile.get("nodes", []):
    node_host = node.get("hardware", {}).get("ip_address", "127.0.0.1")
    for svc, _ in node.get("providers", {}).items():
      var_name = f"ACTIVE_{svc.upper()}_HOST"
      env_lines.append(f"{var_name}={node_host}\n")

  with open(".env.cluster", "w") as f:
    f.writelines(env_lines)

  print(
    f"[Orchestrator] Successfully mapped {len(providers)} local services.\n"
    "Distributed DNS (.env.cluster) generated."
  )

if __name__ == "__main__":
  main()
