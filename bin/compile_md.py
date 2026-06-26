import argparse
import os
import sys

# Ensure we can import metaclaw from the lib directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib')))
import metaclaw

def main():
  parser = argparse.ArgumentParser(description="Parse markdown to AST and optionally HTML.")
  parser.add_argument('-i', '--input', help="Input markdown file")
  parser.add_argument('--html', action='store_true', help="Convert to HTML")
  parser.add_argument('-s', '--setup', action='store_true', help="Auto-generate service markdown from structure.json")
  args = parser.parse_args()

  if args.setup:
    doc = metaclaw.Markdown()
    doc.metaclawSetup()
    print("Setup complete. Auto-generated service markdown files.")
    if not args.input:
      sys.exit(0)

  if not args.input:
    print("Error: -i/--input is required when not running setup mode.")
    sys.exit(1)

  try:
    doc = metaclaw.Markdown(args.input)
  except FileNotFoundError as e:
    print(e)
    sys.exit(1)

  if args.html:
    html_content = doc.toHtml()
    out_file = os.path.splitext(args.input)[0] + '.html'
    metaclaw.Inst.saveFile(out_file, html_content)
  else:
    doc.parse_ast()
    print(f"Parsed {args.input} to AST. No --html flag provided, skipping HTML generation.")

if __name__ == '__main__':
  main()
