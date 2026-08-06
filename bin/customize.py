import os
import json
import shutil
import sys

def main():
    print("################################################################################")
    print("# USER CUSTOMIZATION")
    print("################################################################################")

    profile_path = "profile.json"
    if not os.path.exists(profile_path):
        print("Error: profile.json not found. Run sysprofile.py first.")
        sys.exit(1)

    with open(profile_path, 'r') as f:
        profile = json.load(f)

    import socket
    hostname = socket.gethostname()
    my_node = next((n for n in profile.get("nodes", []) if n.get("hostname") == hostname), None)

    if not my_node:
        print("Error: Node not found in profile.")
        sys.exit(1)

    planes = my_node.get("planes", [])

    if "control" in planes:
        # 1. Routing Strategy (Saved natively to profile.json for orchestrator to consume)
        print("\nSelect Prompt Routing Strategy for OpenClaw:")
        print("  [1] Lexical + Predictive (Uses local Judge Model to score complexity)")
        print("  [2] Pass-Through (Rigid 1:1 mapping based entirely on YAML profiles)")
        print("  [3] Semantic-Predictive (Hybrid Vector + LLM Judge Routing)")
        while True:
            r_choice = input("Enter choice [1]: ").strip()
            if not r_choice or r_choice == '1':
                routing_strategy = "lexical_predictive"
                break
            elif r_choice == '2':
                routing_strategy = "pass_through"
                break
            elif r_choice == '3':
                routing_strategy = "semantic_predictive"
                break
            else:
                print("Invalid choice.")

        profile["routing_strategy"] = routing_strategy

        if routing_strategy == "semantic_predictive":
            print("\nSelect Semantic Granularity:")
            print("  [1] Hierarchical Semantic Routing (Only Team Leads added to vector space)")
            print("  [2] Flat Semantic Routing (All team members and leads added to vector space)")
            while True:
                g_choice = input("Enter choice [1]: ").strip()
                if not g_choice or g_choice == '1':
                    semantic_granularity = "hierarchical"
                    break
                elif g_choice == '2':
                    semantic_granularity = "flat"
                    break
                else:
                    print("Invalid choice.")
            profile["semantic_granularity"] = semantic_granularity
            print(f"  -> Semantic Granularity saved: {semantic_granularity}")

        with open(profile_path, 'w') as f:
            json.dump(profile, f, indent=2)
        print(f"  -> Routing Strategy saved: {routing_strategy}")

        # 2. Workspace Provisioning (Saved to global cache to bypass prompting)
        # We calculate the absolute path based on the user's current working directory
        # so they clearly see where the workspace will be placed relative to the system root.
        default_ws_abs = os.path.abspath(os.path.join(os.getcwd(), "..", "workspace"))

        print(f"\nEnter path for your persistent MetaClaw workspace directory [{default_ws_abs}]: ")
        ws_choice = input("> ").strip()
        if not ws_choice:
            ws_choice = default_ws_abs

        # Resolve absolute path (in case they typed something relative or used ~)
        abs_ws_path = os.path.abspath(os.path.expanduser(ws_choice))

        if os.path.exists(abs_ws_path):
            print(f"  -> External workspace already exists at {abs_ws_path}. Preserving user data.")
        else:
            print(f"  -> Workspace directory does not exist at {abs_ws_path}. Please provision it manually.")

        # 3. Config Drop-Zone Provisioning
        default_cfg_abs = os.path.abspath(os.path.join(os.getcwd(), "..", "config"))
        print(f"\nEnter path for your persistent MetaClaw configuration directory [{default_cfg_abs}]: ")
        cfg_choice = input("> ").strip()
        if not cfg_choice:
            cfg_choice = default_cfg_abs

        abs_cfg_path = os.path.abspath(os.path.expanduser(cfg_choice))

        if os.path.exists(abs_cfg_path):
            print(f"  -> External config already exists at {abs_cfg_path}. Preserving user data.")
        else:
            print(f"  -> Creating empty config directory structure: {abs_cfg_path}")
            for sub in ['docs', 'bin', 'lib', 'data', 'data/grafana/provisioning/custom']:
                os.makedirs(os.path.join(abs_cfg_path, sub), exist_ok=True)

        # Save to root .env.json so env_instantiate picks it up automatically globally
        root_env_json = ".env.json"
        env_data = {}
        if os.path.exists(root_env_json):
            with open(root_env_json, 'r') as f:
                try:
                    env_data = json.load(f)
                except json.JSONDecodeError:
                    pass

        env_data["METACLAW_WORKSPACE"] = abs_ws_path
        env_data["METACLAW_CONFIG"] = abs_cfg_path
        with open(root_env_json, 'w') as f:
            json.dump(env_data, f, indent=2)

        print(f"  -> Paths saved to global MetaClaw configuration.")
    else:
        print("Node does not operate the Control plane. Skipping Gateway customizations.")

if __name__ == "__main__":
    main()
