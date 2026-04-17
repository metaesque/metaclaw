import json
import os
import re
import subprocess
import shutil
import sys
import argparse

def main():
  parser = argparse.ArgumentParser(description="Instantiate .env files from templates.")
  parser.add_argument('--teardown', action='store_true', help="Remove .env files instead of creating them.")
  parser.add_argument('-v', '--verbose', action='store_true', default=False, help="Print generated variables to stdout.")
  args = parser.parse_args()

  env_json_path = '.env.json'
  env_template_path = '.env.template'
  env_tmp_path = '.env.tmp'
  env_path = '.env'

  skip_env_prompt = args.teardown or os.environ.get('OPENCLAW_SKIP_ENV') == '1'

  if args.teardown:
    for f in [env_path, env_tmp_path]:
      if os.path.exists(f):
        os.remove(f)
    return

  if not os.path.exists(env_template_path):
    return

  env_vars = {}
  if os.path.exists(env_json_path):
    with open(env_json_path, 'r') as f:
      try:
        env_vars = json.load(f)
      except json.JSONDecodeError:
        print(f"Error parsing {env_json_path}. Starting with empty mapping.")

  # Regex matches: KEY=change_me_to_IDENTIFIER[OPTIONAL_DEFAULT] SUFFIX
  # Identifier is optional to handle empty defaults like 'change_me_to_'
  pattern = re.compile(r'^([^=]+)=change_me_to_([A-Za-z0-9_]*)(?:\[(.*?)\])?(.*)$')

  # Ensure framework libraries (like newpwd) are in the path
  sys.path.append(os.path.dirname(os.path.abspath(__file__)))

  with open(env_template_path, 'r') as f_in, open(env_tmp_path, 'w') as f_out:
    for line in f_in:
      line_stripped = line.rstrip('\n')
      match = pattern.match(line_stripped)

      if match:
        var_name = match.group(1).strip()
        identifier = match.group(2)
        explicit_default = match.group(3)
        suffix = match.group(4)

        computed_val = ""
        if explicit_default is not None:
          computed_val = explicit_default
        elif identifier == "AUTO_PWD":
          computed_val = os.getcwd()
        elif identifier == "AUTO_PASSWORD":
          try:
            from newpwd import generate_password
            computed_val = generate_password()
          except ImportError:
            computed_val = "FAILED_TO_GENERATE"
        elif identifier == "AUTO_PASSWORD_SK":
          try:
            from newpwd import generate_password
            computed_val = "sk-" + generate_password()
          except ImportError:
            computed_val = "sk-FAILED_TO_GENERATE"

        # Prioritize the cached value from .env.json
        if var_name in env_vars and not env_vars[var_name].startswith('change_me_to_'):
          val = env_vars[var_name]
        else:
          if skip_env_prompt:
            # Provide safe dummy values for non-interactive teardown
            if "PORT" in var_name:
              val = "8080"
            elif "VERSION" in var_name:
              val = "latest"
            else:
              val = "TEARDOWN_DUMMY_VALUE"
          else:
            prompt_str = f"Enter value for {var_name}"
            display_default = computed_val if computed_val else identifier
            if display_default:
              prompt_str += f" [{display_default}]"
            prompt_str += ": "

            try:
              user_val = input(prompt_str).strip()
              if user_val:
                val = user_val
              elif computed_val:
                val = computed_val
              else:
                val = ""
            except EOFError:
              val = computed_val if computed_val else ""

          # Update the cache for future persistence
          env_vars[var_name] = val

        out_line = f"{var_name}={val}{suffix}\n"
        f_out.write(out_line)

        if args.verbose:
          print(f"  {var_name}={val}{suffix}")
      else:
        # Pass non-variable configuration lines straight through
        f_out.write(line_stripped + '\n')

  if not skip_env_prompt:
    with open(env_json_path, 'w') as f:
      json.dump(env_vars, f, indent=2)

  shutil.move(env_tmp_path, env_path)

if __name__ == '__main__':
  main()
