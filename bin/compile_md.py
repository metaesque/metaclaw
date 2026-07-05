import argparse
import os
import sys
import re
import markdown as md_lib
import textwrap

# Ensure we can import metaclaw from the lib directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib')))
import metaclaw

# Dynamic injection into metaclaw.py Markdown class for correct scope
def patched_toHtml(self):
  """
  Parses the Markdown AST and converts it to styled HTML.
  Preprocesses under-indented lists to satisfy the strict 4-space rule.
  """
  text = re.sub(
    r'^[ \t\xa0]{1,3}([-*+]\s)', r'    \1', self.raw_text, flags=re.MULTILINE
  )

  md = md_lib.Markdown(extensions=['tables', 'fenced_code', 'sane_lists'])
  html_body = md.convert(text)

  doc_title = (
    os.path.basename(self.filepath) if self.filepath else 'Generated'
  )

  html_content = (
    f"<!DOCTYPE html>\n"
    f"<html lang=\"en\">\n"
    f"<head>\n"
    f"  <meta charset=\"UTF-8\">\n"
    f"  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
    f"  <title>{doc_title}</title>\n"
    f"  <style>\n"
    f"    body {{ font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, Helvetica, Arial, sans-serif; background-color: #1e1e1e; color: #d4d4d4; max-width: 800px; margin: 0 auto; padding: 40px 20px 80vh 20px; line-height: 1.6; }}\n"
    f"    h1 {{ color: #569cd6; border-bottom: 1px solid #333; padding-bottom: 10px; scroll-margin-top: 80px; }}\n"
    f"    h2 {{ color: #4ec9b0; margin-top: 30px; border-bottom: 1px solid #333; padding-bottom: 5px; scroll-margin-top: 80px; }}\n"
    f"    h3 {{ color: #ce9178; margin-top: 25px; scroll-margin-top: 80px; }}\n"
    f"    .guide {{ background-color: #252526; padding: 20px; border-left: 4px solid #4ec9b0; margin-bottom: 30px; }}\n"
    f"    pre {{ background-color: #000; padding: 15px; border-radius: 6px; font-family: 'Courier New', Courier, monospace; border: 1px solid #333; overflow-x: auto; color: #dcdcaa; }}\n"
    f"    code {{ background-color: #333; padding: 2px 4px; border-radius: 4px; color: #ce9178; font-family: monospace; }}\n"
    f"    pre code {{ background-color: transparent; padding: 0; }}\n"
    f"    a {{ color: #569cd6; text-decoration: none; }}\n"
    f"    a:hover {{ text-decoration: underline; }}\n"
    f"    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}\n"
    f"    th, td {{ border: 1px solid #333; padding: 8px; text-align: left; }}\n"
    f"    th {{ background-color: #252526; color: #4ec9b0; }}\n"
    f"    ul, ol {{ padding-left: 20px; }}\n"
    f"    li {{ margin-bottom: 5px; }}\n"
    f"  </style>\n"
    f"  <script>\n"
    f"    function applyBanners() {{\n"
    f"      var existing = document.getElementById('meta-banner');\n"
    f"      if (existing) existing.remove();\n"
    f"      if (window.location.hash.includes('env.vars')) {{\n"
    f"        var banner = document.createElement('div');\n"
    f"        banner.id = 'meta-banner';\n"
    f"        banner.innerHTML = '&#9432; <strong>PRE-FLIGHT CHECK:</strong> This page is informational only. Please review the service overview and return to your terminal to continue.';\n"
    f"        banner.style = 'background-color: #0e639c; color: white; padding: 10px; text-align: center; font-weight: bold; position: sticky; top: 0; z-index: 1000; margin-bottom: 20px; border-radius: 4px;';\n"
    f"        document.body.insertBefore(banner, document.body.firstChild);\n"
    f"      }} else if (window.location.hash.includes('diagnostic-checks')) {{\n"
    f"        var banner = document.createElement('div');\n"
    f"        banner.id = 'meta-banner';\n"
    f"        banner.innerHTML = '&#9432; <strong>BOOT SEQUENCE:</strong> Scroll down to the <strong>Diagnostic Checks</strong> section and verify your terminal output matches the expected results.';\n"
    f"        banner.style = 'background-color: #d7ba7d; color: black; padding: 10px; text-align: center; font-weight: bold; position: sticky; top: 0; z-index: 1000; margin-bottom: 20px; border-radius: 4px;';\n"
    f"        document.body.insertBefore(banner, document.body.firstChild);\n"
    f"        setTimeout(function() {{ var el = document.getElementById('diagnostic-checks'); if(el) el.scrollIntoView({{behavior: \"smooth\"}}); }}, 200);\n"
    f"      }}\n"
    f"    }}\n"
    f"    window.addEventListener('load', applyBanners);\n"
    f"    window.addEventListener('hashchange', applyBanners);\n"
    f"  </script>\n"
    f"</head>\n"
    f"<body>\n"
    f"  {html_body}\n"
    f"</body>\n"
    f"</html>"
  )
  return html_content

def patched_metaclawSetup(self):
  """
  Auto-generates documentation Markdown files from the central registry
  to enforce absolute consistency across the ecosystem. Modifies structure
  to split into PLANES.md, TIERS.md, and SERVICES.md.
  """
  struct = metaclaw.Inst.structure()
  services = struct.get('services', {})
  planes = struct.get('planes', {})
  tiers = struct.get('tiers', {})

  # --- Generate PLANES.md ---
  if planes:
    planes_md = [
      "# MetaClaw Hardware Planes\n",
      "The MetaClaw architecture isolates infrastructure into functional planes based on their resource utilization profiles and security trust levels.\n"
    ]
    for p_uid, plane in planes.items():
      planes_md.append(f"## {plane['name']} {{#{plane['uid']}}}")
      planes_md.append("")

      if 'aka' in plane:
        aka_text = f"* **Aka**: {plane['aka']}"
        planes_md.append(textwrap.fill(aka_text, width=80, subsequent_indent="  "))
      if 'profile' in plane:
        profile_text = f"* **Profile**: {plane['profile']}"
        planes_md.append(textwrap.fill(profile_text, width=80, subsequent_indent="  "))
      if 'justification' in plane:
        just_text = f"* **Justification**: {plane['justification']}"
        planes_md.append(textwrap.fill(just_text, width=80, subsequent_indent="  "))
      if 'services' in plane:
        svcs_text = f"* **Services**: {', '.join(plane['services'])}"
        planes_md.append(textwrap.fill(svcs_text, width=80, subsequent_indent="  "))

      planes_md.append("")

      if 'hardware_recommendations' in plane:
        planes_md.append(f"### Hardware Recommendations for {plane['name']}\n")
        for hw in plane['hardware_recommendations']:
          planes_md.append(f"#### {hw['name']}")
          planes_md.append(f"* **Price**: {hw['price']}")
          planes_md.append(f"* **Specs**: {hw['specs']}")
          planes_md.append(f"* **URL**: [Link]({hw['url']})")
          planes_md.append(textwrap.fill(f"* **Strengths**: {hw['strengths']}", width=80, subsequent_indent="  "))
          planes_md.append(textwrap.fill(f"* **Weaknesses**: {hw['weaknesses']}", width=80, subsequent_indent="  "))
          planes_md.append("")

    metaclaw.Inst.saveFile('docs/PLANES.md', '\n'.join(planes_md), backup=False)

  # --- Generate TIERS.md ---
  if tiers:
    tiers_md = [
      "# MetaClaw Architectural Tiers\n",
      "A Tier represents a discrete stage in the growth of your overall local cluster. It dictates the scale of hardware deployed across the planes.\n"
    ]
    for t_uid, tier in tiers.items():
      tiers_md.append(f"## {tier['name']} {{#{tier['uid']}}}")
      tiers_md.append("")
      if 'setup' in tier:
        setup_text = f"* **Setup**: {tier['setup']}"
        tiers_md.append(textwrap.fill(setup_text, width=80, subsequent_indent="  "))
      if 'benefit' in tier:
        benefit_text = f"* **Benefit**: {tier['benefit']}"
        tiers_md.append(textwrap.fill(benefit_text, width=80, subsequent_indent="  "))
      tiers_md.append("")

    metaclaw.Inst.saveFile('docs/TIERS.md', '\n'.join(tiers_md), backup=False)

  # --- Generate SERVICES.md ---
  categories = {}
  for uid, svc in services.items():
    cat = svc.get('category', 'Uncategorized')
    if cat not in categories:
      categories[cat] = []
    categories[cat].append(svc)

  services_md = [
    "# MetaClaw Service Registry\n",
    "This document serves as the canonical registry categorizing and explaining the purpose of every infrastructure service supported by the framework.\n"
  ]

  if categories:
    for cat, svcs in categories.items():
      services_md.append(f"## {cat}\n")
      for svc in svcs:
        services_md.append(f"### {svc['name']} {{#{svc['uids']}}}")
        services_md.append("")
        services_md.append(f"* **Path**: `services/{svc['uids']}/`")

        purpose_text = f"* **Purpose**: {svc.get('purpose', '')}"
        purpose = textwrap.fill(purpose_text, width=80, subsequent_indent="  ")
        services_md.append(purpose)

        provider_names = [p['name'] for p in svc.get('providers', {}).values()]
        if provider_names:
          options_text = f"* **Options**: {', '.join(provider_names)}."
        else:
          options_text = "* **Options**: None currently defined."

        options = textwrap.fill(options_text, width=80, subsequent_indent="  ")
        services_md.append(options + "\n")

  metaclaw.Inst.saveFile('docs/SERVICES.md', '\n'.join(services_md), backup=False)

  # Generate the directory index.md files for each service and provider
  for uid, svc in services.items():
    svc_md = [f"# {svc['name']} Overview\n", "## Providers\n"]
    for p_uid, provider in svc.get('providers', {}).items():
      svc_md.append(f"### {provider['name']}")
      if provider.get('overview'):
        overview = textwrap.fill(provider['overview'], width=80)
        svc_md.append(overview + "\n")
      else:
        svc_md.append("\n")

      # Auto-generate the specific provider index.md
      p_md = [f"# {p_uid}: {provider['name']}\n", "## Overview\n"]
      for paragraph in provider.get('details', []):
        p_md.append(textwrap.fill(paragraph, width=80))
        p_md.append("")

      provider_index_path = f"services/{svc['uids']}/{p_uid}/index.md"
      template_path = f"services/{svc['uids']}/{p_uid}/index.template.md"

      if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as tf:
          t_md = tf.read()
        if 'diagnostics' in provider and provider['diagnostics'].strip():
          diag_block = f"<h2 id=\"diagnostic-checks\">Diagnostic Checks ({svc.get('uid', 'unknown')} {p_uid})</h2>\n\n{provider['diagnostics']}\n\n"
          if '__DIAGNOSTICS__' in t_md:
            t_md = t_md.replace('__DIAGNOSTICS__', diag_block)
          else:
            t_md += "\n" + diag_block
        metaclaw.Inst.saveFile(provider_index_path, t_md, backup=False)
      else:
        if 'diagnostics' in provider and provider['diagnostics'].strip():
          p_md.append(f"<h2 id=\"diagnostic-checks\">Diagnostic Checks ({svc.get('uid', 'unknown')} {p_uid})</h2>")
          p_md.append(provider['diagnostics'])
          p_md.append("")
        metaclaw.Inst.saveFile(provider_index_path, '\n'.join(p_md), backup=False)

    index_path = f"services/{svc['uids']}/index.md"
    metaclaw.Inst.saveFile(index_path, '\n'.join(svc_md), backup=False)

# Apply patches BEFORE main() is called
metaclaw.Markdown.toHtml = patched_toHtml
metaclaw.Markdown.metaclawSetup = patched_metaclawSetup

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
