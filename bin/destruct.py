import os
import sys
import json

# Ensure we can import metaclaw from the lib directory
sys.path.insert(
  0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
)
import metaclaw

def main():
  """
  Reads the monolithic structure.json and delegates to MetaClaw.destructure()
  to split it into modular fragments.
  """
  root_dir = metaclaw.Inst.rootdir()
  struct_path = os.path.join(root_dir, 'bin', 'structure.json')

  if not os.path.exists(struct_path):
    print(f"FATAL: {struct_path} not found.")
    sys.exit(1)

  print(f"Reading monolithic taxonomy from {struct_path}...")
  with open(struct_path, 'r', encoding='utf-8') as f:
    try:
      struct_data = json.load(f)
    except json.JSONDecodeError as e:
      print(f"FATAL: Failed to parse structure.json: {e}")
      sys.exit(1)

  print("Destructuring taxonomy into modular JSON fragments...")
  metaclaw.Inst.destructure(struct_data)

  #print(f"Destructuring complete. Removing legacy {struct_path}...")
  # os.remove(struct_path)
  print("SUCCESS: MetaClaw taxonomy has been modularized.")

if __name__ == '__main__':
  main()
