import os
import sys
import argparse
import shutil

# Ensure we can import metaclaw from the lib directory
sys.path.insert(
  0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
)
import metaclaw


def main():
  parser = argparse.ArgumentParser(description="Instantiate .env files from templates.")
  parser.add_argument('--teardown', action='store_true', help="Remove .env files instead of creating them.")
  parser.add_argument('-v', '--verbose', action='store_true', default=False, help="Print generated variables to stdout.")
  args = parser.parse_args()

  metaclaw.Inst.envInstantiate(teardown=args.teardown, verbose=args.verbose)

if __name__ == '__main__':
  main()
