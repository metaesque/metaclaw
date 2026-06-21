import os
import sys
import json
import glob
import argparse
import textwrap

# ANSI escape codes for colors
COLOR_RESET = "\033[0m"
COLOR_HUMAN = "\033[94m" # Blue
COLOR_ASSISTANT = "\033[92m" # Green
COLOR_TOOL = "\033[38;5;214m" # Orange
COLOR_TIME = "\033[90m" # Gray

def wrap_markdown(text, width=80):
    lines = text.split('\n')
    output = []
    in_code_block = False
    
    for line in lines:
        if line.startswith('```'):
            in_code_block = not in_code_block
            output.append(line)
            continue
            
        if in_code_block:
            output.append(line)
        else:
            if not line.strip():
                output.append(line)
            else:
                wrapped = textwrap.fill(line, width=width)
                output.append(wrapped)
                
    return '\n'.join(output)

def main():
    parser = argparse.ArgumentParser(description="Parse OpenClaw prompts")
    parser.add_argument("agent_name", help="Name of the agent")
    parser.add_argument("--raw", action="store_true", help="Print raw .jsonl files but cleaned up")
    args = parser.parse_args()

    agent_name = args.agent_name

    # Resolve paths
    script_path = os.path.abspath(__file__)
    bin_dir = os.path.dirname(script_path)
    framework_root = os.path.dirname(bin_dir)
    target_dir = os.path.join(
        framework_root, 
        "services", "gateways", "openclaw", "config", "agents", 
        agent_name, "sessions"
    )

    if not os.path.isdir(target_dir):
        print(f"Directory not found: {target_dir}")
        sys.exit(1)

    # Search for all .jsonl files and files starting with .jsonl, excluding .trajectory.jsonl
    jsonl_files = []
    for file in os.listdir(target_dir):
        if ".jsonl" in file and ".trajectory.jsonl" not in file:
            jsonl_files.append(os.path.join(target_dir, file))

    if not jsonl_files:
        print(f"No .jsonl files found in {target_dir}")

    for filepath in jsonl_files:
        print(f"\n--- Parsing {os.path.basename(filepath)} ---")
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if data.get("type") != "message":
                    continue

                msg = data.get("message", {})
                role = msg.get("role")
                timestamp = data.get("timestamp", "Unknown Time")
                
                if args.raw:
                    # Clean up the raw JSON
                    cleaned_content = []
                    raw_content = msg.get("content")
                    if isinstance(raw_content, str):
                        cleaned_content = raw_content
                    elif isinstance(raw_content, list):
                        for item in raw_content:
                            if item.get("type") == "text":
                                cleaned_content.append({"text": item.get("text")})
                            elif item.get("type") == "toolCall":
                                cleaned_content.append({
                                    "tool": item.get("name"),
                                    "args": item.get("arguments")
                                })
                    elif role == "toolResult":
                        # Attempt to extract text from tool results if possible
                        if isinstance(raw_content, list):
                             for item in raw_content:
                                 if item.get("type") == "text":
                                     cleaned_content.append({"result": item.get("text")})
                                 
                    cleaned_data = {
                        "role": role,
                        "timestamp": timestamp,
                        "content": cleaned_content
                    }
                    print(json.dumps(cleaned_data, separators=(',', ':')))
                    continue

                time_str = f"{COLOR_TIME}[{timestamp}]{COLOR_RESET}"
                separator = "=" * 80

                if role == "user":
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        wrapped_content = wrap_markdown(content)
                        print(f"{separator}\n{time_str} {COLOR_HUMAN}[HUMAN]{COLOR_RESET}\n{wrapped_content}")
                
                elif role == "assistant":
                    content = msg.get("content", [])
                    if isinstance(content, list):
                         for item in content:
                            item_type = item.get("type")
                            if item_type == "text":
                                text = item.get("text", "")
                                wrapped_text = wrap_markdown(text)
                                print(f"{separator}\n{time_str} {COLOR_ASSISTANT}[{agent_name.upper()}]{COLOR_RESET}\n{wrapped_text}")
                            elif item_type == "toolCall":
                                tool_name = item.get("name", "unknown")
                                tool_args = item.get("arguments", {})
                                args_str = json.dumps(tool_args, indent=2)
                                print(f"{separator}\n{time_str} {COLOR_TOOL}[TOOL]{COLOR_RESET}\nExecuted tool: {tool_name}\nArguments:\n{args_str}")

if __name__ == "__main__":
    main()
