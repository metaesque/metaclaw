import argparse
import requests
import re
import os
import sys

def extract_sections_from_markdown(body_md):
  """
  Parses raw GitHub release Markdown body to extract Breaking and Changes bullets,
  or falls back to capturing all top-level bullet points if custom headings are used.
  """
  breaking = []
  changes = []
  other_bullets = []

  current_section = None
  for raw_line in (body_md or "").splitlines():
    line = raw_line.strip()
    if not line:
      continue

    heading_match = re.match(r'^#{1,4}\s+(.*)$', line)
    if heading_match:
      h_text = heading_match.group(1).strip().lower()
      if 'breaking' in h_text:
        current_section = 'Breaking'
      elif any(k in h_text for k in ['change', 'feature', 'added', 'fix', 'what\'s changed', 'highlights']):
        current_section = 'Changes'
      else:
        current_section = 'Other'
      continue

    bullet_match = re.match(r'^[-*+]\s+(.*)$', line)
    if bullet_match:
      item = bullet_match.group(1).strip()
      if current_section == 'Breaking':
        breaking.append(item)
      elif current_section == 'Changes':
        changes.append(item)
      else:
        other_bullets.append(item)

  if not breaking and not changes and other_bullets:
    changes = other_bullets

  return breaking, changes

def main():
  parser = argparse.ArgumentParser(
    description="Parse OpenClaw GitHub releases for breaking changes via the GitHub REST API."
  )
  parser.add_argument(
    '-t', '--term', type=str, default='2026.6.8',
    help="Stopping version term (e.g., '2026.6.8'). Script stops once it reaches this version."
  )
  parser.add_argument(
    '-u', '--until', type=str, default='',
    help="Optional upper-bound version term (e.g., '2026.10.3'). Skips releases newer than this version."
  )
  args = parser.parse_args()

  term_clean = args.term.lstrip('v').strip()
  until_clean = args.until.lstrip('v').strip() if args.until else ''

  # Split scheme and host so web UI copy-paste never mangles the string into a Markdown link
  api_scheme = "https://"
  api_path = "api.github.com/repos/openclaw/openclaw/releases"
  api_url = api_scheme + api_path
  output_file = 'openclaw_releases.md'

  content_blocks = []
  page = 1
  term_found = False
  started_collecting = False if until_clean else True

  headers = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "MetaClaw-Release-Analyzer"
  }
  github_token = os.environ.get("GITHUB_TOKEN")
  if github_token:
    headers["Authorization"] = f"Bearer {github_token}"

  while not term_found:
    page_url = f"{api_url}?per_page=100&page={page}"
    print(f"Fetching {page_url}...")
    try:
      response = requests.get(page_url, headers=headers, timeout=30)
      response.raise_for_status()
      releases = response.json()
    except Exception as e:
      print(f"Error fetching releases: {e}")
      break

    if not releases:
      print("No additional pages found.")
      break

    for rel in releases:
      tag_name = (rel.get('tag_name') or '').strip()
      rel_name = (rel.get('name') or tag_name).strip()
      version_label = rel_name if rel_name else tag_name

      if until_clean and not started_collecting:
        if until_clean in tag_name or until_clean in rel_name:
          started_collecting = True
        else:
          continue

      if term_clean and (term_clean in tag_name or term_clean in rel_name):
        print(
          f"Termination term '{args.term}' found in '{version_label}'. Stopping."
        )
        term_found = True
        break

      body_md = rel.get('body') or ''
      breaking, changes = extract_sections_from_markdown(body_md)

      content_blocks.append({
        "version": version_label,
        "tag": tag_name,
        "published_at": rel.get('published_at', ''),
        "Breaking": breaking,
        "Changes": changes,
        "raw_body": body_md.strip()
      })

    if len(releases) < 100:
      break
    page += 1

  # Write to Markdown
  with open(output_file, 'w', encoding='utf-8') as f:
    for b in content_blocks:
      pub_str = f" ({b['published_at'][:10]})" if b.get('published_at') else ""
      f.write(f"# Release: {b['version']}{pub_str}\n\n")

      if b['Breaking']:
        f.write("## Breaking\n\n")
        for item in b['Breaking']:
          f.write(f"- {item}\n")
        f.write("\n")

      if b['Changes']:
        f.write("## Changes\n\n")
        for item in b['Changes']:
          f.write(f"- {item}\n")
        f.write("\n")

      if not b['Breaking'] and not b['Changes'] and b['raw_body']:
        f.write("## Notes\n\n")
        f.write(f"{b['raw_body']}\n\n")

  print(
    f"Successfully generated {output_file} with {len(content_blocks)} "
    f"release blocks."
  )

if __name__ == "__main__":
  main()
