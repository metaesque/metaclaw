#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description="Create a custom Ollama Modelfile wrapper for MetaClaw models.")
    parser.add_argument('-b', '--base-model', required=True, help="Original model name (e.g., llama4-scout-q4:109b)")
    parser.add_argument('-n', '--new-model', required=True, help="New custom model name (e.g., metaclaw-llama4-scout)")
    parser.add_argument('-s', '--system', type=str, help="Path to a text file containing the system prompt, or a raw string")
    parser.add_argument('-t', '--temperature', type=float, help="Temperature parameter override")
    parser.add_argument('-c', '--num-ctx', type=int, help="Context window size override")
    parser.add_argument('--stop', action='append', help="Stop tokens (can be provided multiple times)")
    parser.add_argument('--template', type=str, help="Path to a text file containing a custom Jinja chat template")

    args = parser.parse_args()

    # Formulate the Modelfile content
    modelfile_content = f"FROM {args.base_model}\n"

    if args.temperature is not None:
        modelfile_content += f"PARAMETER temperature {args.temperature}\n"
    if args.num_ctx is not None:
        modelfile_content += f"PARAMETER num_ctx {args.num_ctx}\n"
    if args.stop:
        for stop_token in args.stop:
            modelfile_content += f"PARAMETER stop \"{stop_token}\"\n"

    if args.system:
        if os.path.exists(args.system):
            with open(args.system, 'r', encoding='utf-8') as f:
                modelfile_content += f"SYSTEM \"\"\"\n{f.read()}\n\"\"\"\n"
        else:
            modelfile_content += f"SYSTEM \"\"\"\n{args.system}\n\"\"\"\n"

    if args.template:
        if os.path.exists(args.template):
            with open(args.template, 'r', encoding='utf-8') as f:
                modelfile_content += f"TEMPLATE \"\"\"\n{f.read()}\n\"\"\"\n"
        else:
            print(f"FATAL: Template file {args.template} not found.")
            sys.exit(1)

    # Write the temporary Modelfile to disk
    modelfile_path = f"Modelfile.{args.new_model.replace(':', '_')}"
    with open(modelfile_path, 'w', encoding='utf-8') as f:
        f.write(modelfile_content)

    print(f"Generated {modelfile_path}:\n")
    print(modelfile_content)
    print("-" * 80)

    # Determine paths based on standard MetaClaw execution root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    ollama_bin = os.path.join(repo_root, "services", "runners", "ollama", "bin", "ollama")

    if not os.path.exists(ollama_bin):
        print(f"Warning: Hermetic Ollama binary not found at {ollama_bin}. Falling back to system PATH.")
        ollama_bin = "ollama"

    cmd = [ollama_bin, "create", args.new_model, "-f", modelfile_path]
    print(f"Executing: {' '.join(cmd)}")

    # Inject the standard Ollama host to ensure we hit the local daemon
    env = os.environ.copy()
    if 'OLLAMA_HOST' not in env:
        env['OLLAMA_HOST'] = '127.0.0.1:11434'

    try:
        subprocess.run(cmd, env=env, check=True)
        print(f"\nSUCCESS: Custom model '{args.new_model}' generated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"\nFAILURE: Model creation failed. {e}")
    finally:
        if os.path.exists(modelfile_path):
            os.remove(modelfile_path)

if __name__ == "__main__":
    main()
