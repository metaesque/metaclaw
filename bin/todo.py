import os
import sys

# Ensure we can import metaclaw from the lib directory
sys.path.insert(
  0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
)
import metaclaw

def main():
  print("================================================================================")
  print(" CURRENT ROADMAP")
  print("================================================================================")
  roadmap_path = os.path.join(metaclaw.Inst.rootdir(), 'docs', 'ROADMAP.md')
  if os.path.exists(roadmap_path):
    with open(roadmap_path, 'r', encoding='utf-8') as f:
      print(f.read())
  else:
    print("ROADMAP.md not found.")

  print("\n================================================================================")
  print(" TAXONOMY VALIDATION (MISSING DATA)")
  print("================================================================================")
  metaclaw.Inst.validate()

if __name__ == '__main__':
  main()
