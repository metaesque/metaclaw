import json
import os
import subprocess
import socket
import sys

# Ensure we can import metaclaw from the lib directory
sys.path.insert(
  0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
)
import metaclaw

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
        # MANDATE: Resolve symlink to physical path so Docker Compose relative paths evaluate correctly.
        # If PWD is the symlink (services/proxy), then ../../memory/.env resolves incorrectly to services/.env.
        # By resolving the realpath (services/proxies/litellm), ../../memory/.env resolves correctly to services/memory/.env.
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
  # 2. PROVISIONING
  # --------------------------------------------------------------------------
  cluster_nodes = profile.get("nodes", [])
  cluster_tier = max([n.get("tier", 0) for n in cluster_nodes] + [0])

  for svc, prov_data in providers.items():
    if isinstance(prov_data, dict):
      provider = prov_data.get("uid")
      metal = prov_data.get("metal", False)
    else:
      # Support legacy string-based profile configurations
      provider = prov_data
      metal = False

    if svc not in metaclaw.Inst.structure()['services']:
      print(
        f"[Orchestrator] Warning: Unknown service '{svc}' found in profile.\n"
        "Skipping symlink generation."
      )
      continue

    uids = metaclaw.Inst.structure()['services'][svc]['uids']
    sym_path = os.path.join(services_dir, svc)
    target_path = os.path.join(uids, provider)

    # Use lexists to correctly detect broken symlinks targeting unimplemented providers
    if not os.path.lexists(sym_path):
      cwd = os.getcwd()
      os.chdir(services_dir)
      os.symlink(target_path, svc)
      print(f'NOTE: created symlink from {target_path} to {svc}')
      os.chdir(cwd)

    # Establish execution state hooks for Makefiles
    metal_flag_path = os.path.join(sym_path, ".metal")
    if metal:
      with open(metal_flag_path, "w") as f:
        f.write("1\n")
    else:
      if os.path.exists(metal_flag_path):
        os.remove(metal_flag_path)

    # ========================================================================
    # TIER-AWARE ENVIRONMENT SEEDING
    # Automatically populates .env.json with intelligent defaults based on the
    # cluster topology, preventing non-technical users from being prompted.
    # ========================================================================
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
      env_data["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"
      seeded = True

    elif provider == "litellm":
      compute_node = next((n for n in cluster_nodes if "compute" in n.get("planes", [])), None)
      if cluster_tier >= 2 and compute_node:
        compute_ip = compute_node.get("hardware", {}).get("ip_address", "127.0.0.1")
        env_data["COMPLEX_MODEL_ID"] = "ollama/ingu627/llama4-scout-q4:109b"
        env_data["COMPLEX_MODEL_API_BASE"] = f"http://{compute_ip}:11434"
        env_data["COMPLEX_MODEL_API_KEY"] = "sk-local-ollama-key"
      else:
        env_data["COMPLEX_MODEL_ID"] = "gemini/gemini-3.1-pro-preview"
        env_data["COMPLEX_MODEL_API_BASE"] = "https://gateway.ai.google"
        if "COMPLEX_MODEL_API_KEY" in env_data:
            del env_data["COMPLEX_MODEL_API_KEY"]
      seeded = True

    if seeded:
      os.makedirs(real_provider_path, exist_ok=True)
      with open(env_json_path, "w") as f:
        json.dump(env_data, f, indent=2)

  # --------------------------------------------------------------------------
  # 3. DISTRIBUTED DNS GENERATION
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
