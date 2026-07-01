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
        while True:
            r_choice = input("Enter choice [1]: ").strip()
            if not r_choice or r_choice == '1':
                routing_strategy = "lexical_predictive"
                break
            elif r_choice == '2':
                routing_strategy = "pass_through"
                break
            else:
                print("Invalid choice.")

        profile["routing_strategy"] = routing_strategy
        with open(profile_path, 'w') as f:
            json.dump(profile, f, indent=2)
        print(f"  -> Routing Strategy saved: {routing_strategy}")

        # 2. Workspace Provisioning (Saved to service-level cache to bypass prompting)
        default_ws = "../workspace"
        print(f"\nEnter path for your persistent OpenClaw workspace directory [{default_ws}]: ")
        ws_choice = input("> ").strip()
        if not ws_choice:
            ws_choice = default_ws

        # Resolve absolute path
        abs_ws_path = os.path.abspath(os.path.expanduser(ws_choice))

        if os.path.exists(abs_ws_path):
            print(f"  -> External workspace already exists at {abs_ws_path}. Preserving user data.")
        else:
            template_dir = os.path.abspath(".workspace.template")
            if os.path.exists(template_dir):
                print(f"  -> Auto-provisioning workspace from template into: {abs_ws_path}")
                shutil.copytree(template_dir, abs_ws_path)
            else:
                print(f"  -> Creating empty workspace directory: {abs_ws_path}")
                os.makedirs(abs_ws_path)

        # Save to gateway's .env.json so env_instantiate picks it up automatically
        gw_env_json = "services/gateways/openclaw/.env.json"
        os.makedirs(os.path.dirname(gw_env_json), exist_ok=True)
        env_data = {}
        if os.path.exists(gw_env_json):
            with open(gw_env_json, 'r') as f:
                try:
                    env_data = json.load(f)
                except json.JSONDecodeError:
                    pass

        env_data["OPENCLAW_WORKSPACE"] = abs_ws_path
        with open(gw_env_json, 'w') as f:
            json.dump(env_data, f, indent=2)

        print(f"  -> Workspace path saved to OpenClaw configuration.")
    else:
        print("Node does not operate the Control plane. Skipping Gateway customizations.")

if __name__ == "__main__":
    main()
