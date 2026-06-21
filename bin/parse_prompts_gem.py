#!/usr/bin/env python3
import os
import sys
import glob
import json
from datetime import datetime

# ANSI Escape Codes for Terminal Colors
COLOR_RESET = "\033[0m"
COLOR_HUMAN = "\033[94m"     # Blue
COLOR_ASSISTANT = "\033[92m" # Green
COLOR_TOOL = "\033[93m"      # Yellow
COLOR_TIME = "\033[90m"      # Dark Gray
COLOR_ERROR = "\033[91m"     # Red

def format_timestamp(ts_str):
    try:
        # Handle format: 2026-06-19T22:37:16.366Z
        dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return ts_str

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_prompts_gem.py <agent_name>")
        print("Example: python parse_prompts_gem.py lead_developer")
        sys.exit(1)

    agent_name = sys.argv[1]

    # Determine framework root dynamically
    bin_dir = os.path.dirname(os.path.abspath(__file__))
    framework_root = os.path.dirname(bin_dir)

    # Construct the path to the agent's sessions
    session_dir = os.path.join(
        framework_root,
        'services', 'gateways', 'openclaw', 'config', 'agents', agent_name, 'sessions'
    )

    if not os.path.exists(session_dir):
        print(f"{COLOR_ERROR}ERROR: Session directory not found for agent '{agent_name}'.{COLOR_RESET}")
        print(f"Looked in: {session_dir}")
        sys.exit(1)

    # Find all .jsonl files
    search_pattern = os.path.join(session_dir, '*.jsonl')
    jsonl_files = glob.glob(search_pattern)

    if not jsonl_files:
        print(f"No session logs (*.jsonl) found in {session_dir}")
        sys.exit(0)

    print(f"Found {len(jsonl_files)} session log(s) for agent '{agent_name}'.\n")

    for file_path in jsonl_files:
        session_id = os.path.basename(file_path).replace('.jsonl', '')
        print("=" * 80)
        print(f"SESSION ID: {session_id}")
        print("=" * 80)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        print(f"{COLOR_ERROR}[Parse Error] Line {line_num}: Invalid JSON{COLOR_RESET}")
                        continue

                    # Filter: We only care about standard 'message' events containing actual chat content
                    if data.get('type') != 'message':
                        continue

                    msg_obj = data.get('message', {})
                    role = msg_obj.get('role')
                    timestamp = format_timestamp(data.get('timestamp', ''))

                    # HUMAN PROMPT
                    if role == 'user':
                        content = msg_obj.get('content', '')
                        print(f"\n{COLOR_TIME}[{timestamp}]{COLOR_RESET} {COLOR_HUMAN}▶ HUMAN (Prompt){COLOR_RESET}")
                        print("-" * 40)
                        print(content)
                        print("-" * 40)

                    # ASSISTANT RESPONSE
                    elif role == 'assistant':
                        content_array = msg_obj.get('content', [])

                        # The assistant content can be an array containing text AND/OR toolCalls
                        for item in content_array:
                            if item.get('type') == 'text':
                                print(f"\n{COLOR_TIME}[{timestamp}]{COLOR_RESET} {COLOR_ASSISTANT}▶ {agent_name.upper()} (Response){COLOR_RESET}")
                                print("-" * 40)
                                print(item.get('text', ''))
                                print("-" * 40)
                            elif item.get('type') == 'toolCall':
                                tool_name = item.get('name', 'unknown')
                                print(f"\n{COLOR_TIME}[{timestamp}]{COLOR_RESET} {COLOR_TOOL}⚙ {agent_name.upper()} executed tool: {tool_name}{COLOR_RESET}")

                    # TOOL RESULT (Optional: Usually noisy, uncomment to debug tool execution)
                    # elif role == 'toolResult':
                    #     tool_name = msg_obj.get('toolName', 'unknown')
                    #     print(f"\n{COLOR_TIME}[{timestamp}]{COLOR_RESET} {COLOR_TOOL}⚙ Tool Result ({tool_name}) logged to session.{COLOR_RESET}")

        except Exception as e:
            print(f"{COLOR_ERROR}Error reading file {file_path}: {e}{COLOR_RESET}")

        print("\n")

if __name__ == "__main__":
    main()
