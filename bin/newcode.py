import sys
import os
import re
import subprocess
import argparse

# Ensure we can import metaclaw from the lib directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib')))
import metaclaw

def diff_files(old_path, new_content):
  with open(old_path, 'r', encoding='utf-8') as f:
    old_content = f.read()

  if old_content == new_content:
    print(f"No changes detected for {old_path}. Skipping backup and write.")
    return False

  print(f"\n{'-'*80}\nDiff for {old_path}:\n{'-'*80}")
  temp_path = old_path + ".tmp"
  with open(temp_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

  try:
    subprocess.run([
      'diff',
      '--width=160',
      '--suppress-common-lines',
      '-y',
      old_path,
      temp_path
    ])
  except FileNotFoundError:
    print("System 'diff' command not found. Please install it.")
  finally:
    if os.path.exists(temp_path):
      os.remove(temp_path)

  print(f"{'-'*80}\n")
  return True

def process_block(text, batch=False):
  delim = "^" + "====>"
  pattern = re.compile(delim + r"\s*(.*?)\s*<====\n(.*?)(?=" + delim + r"|\Z)", re.MULTILINE | re.DOTALL)
  matches = pattern.findall(text)

  file_contents = {}

  for filename, content in matches:
    filename = filename.strip()
    if filename.startswith('./'):
      filename = filename[2:]
    content = "\n".join(line.rstrip() for line in content.splitlines()) + "\n"

    if filename in file_contents:
      print(f"\n{'!'*80}")
      print(f"! WARNING: Multiple references to '{filename}' detected in input stream.")
      print(f"! Discarding earlier references. Only the final occurrence will be applied.")
      print(f"{'!'*80}\n")

    file_contents[filename] = content

  for filename, content in file_contents.items():
    print(f"\n{'#'*80}")
    print(f"# PROCESSING: {filename}")
    print(f"{'#'*80}")

    if os.path.exists(filename):
      if diff_files(filename, content):
        apply = True
        if not batch:
          while True:
            choice = input(f"Apply changes to {filename}? (y/n/q): ").strip().lower()
            if choice in ['y', 'yes']:
              break
            elif choice in ['n', 'no']:
              apply = False
              print(f"Skipping {filename}.")
              break
            elif choice in ['q', 'quit']:
              print("Aborting processing.")
              sys.exit(0)

        if apply:
          metaclaw.Inst.saveFile(filename, content)
    else:
      apply = True
      if not batch:
        while True:
          choice = input(f"Create new file {filename}? (y/n/q): ").strip().lower()
          if choice in ['y', 'yes']:
            break
          elif choice in ['n', 'no']:
            apply = False
            print(f"Skipping {filename}.")
            break
          elif choice in ['q', 'quit']:
            print("Aborting processing.")
            sys.exit(0)

      if apply:
        metaclaw.Inst.saveFile(filename, content)

def generate_setup_output(setup_file):
  if not os.path.exists(setup_file):
    print(f"Error: Setup file '{setup_file}' not found.")
    sys.exit(1)

  with open(setup_file, 'r', encoding='utf-8') as f:
    filepaths = [line.strip() for line in f if line.strip()]

  for filepath in filepaths:
    if not os.path.exists(filepath):
      print(f"Warning: File '{filepath}' not found. Skipping.")
      continue

    print(f"====> {filepath} <====")
    with open(filepath, 'r', encoding='utf-8') as file_obj:
      content = file_obj.read()
      print(content, end='')
      if not content.endswith('\n'):
        print()

def verify_structure(input_file):
  struct_file = 'docs/MANIFEST.files'
  ignore_file = 'docs/.MANIFEST.files.ignore'

  if not os.path.exists(struct_file):
    print(f"\nWarning: {struct_file} not found for verification.")
    return

  with open(struct_file, 'r', encoding='utf-8') as f:
    expected_files = set(line.strip() for line in f if line.strip())

  ignore_dirs = set()
  ignore_files = set()
  ignore_patterns = set()

  # input_file is absolute; make it relative to the root for ignore rules
  try:
    rel_input = os.path.relpath(input_file, '.')
  except ValueError:
    rel_input = os.path.basename(input_file)

  internal_ignores = {rel_input, 'tmp/metaclaw.txt', 'docs/.MANIFEST.files.ignore'}
  for item in internal_ignores:
    ignore_files.add(item)

  if os.path.exists(ignore_file):
    with open(ignore_file, 'r', encoding='utf-8') as f:
      for line in f:
        line = re.sub(r'\s+#.*$', '', line.strip())
        if not line or line[0] == '#':
          continue
        if line[0] == '~':
          ignore_patterns.add(re.compile(line[1:]))
        elif line.endswith('/'):
          ignore_dirs.add(line[:-1])
        else:
          ignore_dirs.add(line)
          ignore_files.add(line)

  actual_files = set()
  for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if os.path.relpath(os.path.join(root, d), '.') not in ignore_dirs]
    for file in files:
      rel_path = os.path.relpath(os.path.join(root, file), '.')
      if rel_path in ignore_files:
        print(f'NOTE: ignoring {rel_path}')
        continue

      pmatch = False
      for ipattern in ignore_patterns:
        if ipattern.search(rel_path):
          print(f'NOTE: ignoring {rel_path} (pattern {ipattern.pattern})')
          pmatch = True
          break
      if pmatch:
        continue

      actual_files.add(rel_path)

  unexpected_files = actual_files - expected_files
  missing_files = expected_files - actual_files

  if missing_files:
    print(f"\n{'-'*80}\nMissing Expected Files (from {struct_file}):\n{'-'*80}")
    for f in sorted(missing_files):
      print(f"  - {f}")

  if unexpected_files:
    print(f"\n{'-'*80}\nUnexpected Files Found:\n{'-'*80}")
    for f in sorted(unexpected_files):
      try:
        choice = input(f"Delete unexpected file '{f}'? (y/N): ").strip().lower()
        if choice in ['y', 'yes']:
          os.remove(f)
          print(f"  -> Deleted {f}")
        else:
          print(f"  -> Kept {f}")
      except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting.")
        sys.exit(1)

def apply_executable_permissions():
  manifest = '.executable.txt'
  if not os.path.exists(manifest):
    return

  print(f"\n{'-'*80}\n# ENFORCING EXECUTABLE PERMISSIONS\n{'-'*80}")
  with open(manifest, 'r', encoding='utf-8') as f:
    paths = [line.strip() for line in f if line.strip()]

  for path in paths:
    if os.path.exists(path):
      st = os.stat(path)
      os.chmod(path, st.st_mode | 0o111)
      print(f"  -> Marked executable: {path}")
    else:
      print(f"\n{'!'*80}")
      print(f"! WARNING: Target '{path}' listed in {manifest} does not exist.")
      print(f"{'!'*80}\n")

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Process code blocks or generate setup files.")
  parser.add_argument('input_file', nargs='?', default=None, help="Input file containing markdown blocks.")
  parser.add_argument('-s', '--setup', type=str, default='', help="Path to a file containing a list of files to package.")
  parser.add_argument('-b', '--batch', action='store_true', help="Run in batch mode (no prompts). Defaults to False.")

  args = parser.parse_args()

  # Resolve paths absolutely before changing the working directory
  if args.input_file:
    args.input_file = os.path.abspath(args.input_file)
  if args.setup:
    args.setup = os.path.abspath(args.setup)

  # Force working directory to the MetaClaw root so all relative paths
  # in processed blocks anchor correctly, regardless of invoke location.
  root_dir = metaclaw.Inst.rootdir()
  os.chdir(root_dir)

  if args.setup:
    generate_setup_output(args.setup)
    sys.exit(0)

  if not args.input_file:
    parser.print_help()
    sys.exit(1)

  if not os.path.exists(args.input_file):
    print(f"Error: {args.input_file} not found.")
    sys.exit(1)

  with open(args.input_file, 'r', encoding='utf-8') as f:
    text = f.read()

  process_block(text, batch=args.batch)
  apply_executable_permissions()
  verify_structure(args.input_file)

  try:
    if args.batch:
      print(f"\nBatch mode: leaving input file '{args.input_file}' intact.")
    else:
      choice = input(f"\nDelete input file '{args.input_file}'? (y/N): ").strip().lower()
      if choice in ['y', 'yes']:
        os.remove(args.input_file)
        print(f"Deleted {args.input_file}")
      else:
        print(f"Warn: {args.input_file} not deleted")
  except KeyboardInterrupt:
    print(f"\nWarn: {args.input_file} not deleted. Exiting.")
    sys.exit(1)
