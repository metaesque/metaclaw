import argparse
import requests
import re
import os
import sys

# Keywords that indicate a change is relevant to MetaClaw's gateway, routing,
# agent orchestration, Docker sandboxing, or LLM provider integrations.
RELEVANT_KEYWORDS = re.compile(
  r'\b('
  r'gateway|config|openclaw\.json|plugin|extension|hook|before_model_resolve|'
  r'before_agent_resolve|routing|router|model|provider|litellm|ollama|openai|'
  r'gemini|session|sessions_send|sessions_spawn|sessions_list|sessions_yield|'
  r'subagent|sub-agent|agenttoagent|swarm|tool|loopdetection|sandbox|docker|'
  r'searxng|web_search|web_fetch|browser|memory|context|workspace|soul\.md|'
  r'agents\.md|identity\.md|heartbeat|auth|token|controlui|allowedorigins|'
  r'chatcompletions|http|webhook|update|banner|version|env|timeout|stream|'
  r'thinking|embedding|vector|tui|dashboard|devices'
  r')\b',
  re.IGNORECASE
)

# Prefixes for third-party chat channels and native mobile/desktop apps
# that are not used by the headless MetaClaw cluster infrastructure.
IRRELEVANT_PREFIXES = re.compile(
  r'^(?:fix|feat|chore|refactor|docs)?\s*(?:\([^)]+\))?:\s*'
  r'(?:ios|macos|android|watchos|whatsapp|telegram|discord|slack|signal|'
  r'imessage|bluebubbles|matrix|msteams|mattermost|line|nostr|twitch|zalo|feishu)\b',
  re.IGNORECASE
)

def clean_bullet_text(text):
  """
  Strips verbose GitHub PR attribution links and commit hashes to minimize
  token footprint while preserving all technical substance.
  """
  text = re.sub(r'\s+by\s+@[A-Za-z0-9_-]+\s+in\s+https?://\S+', '', text)
  text = re.sub(r'\s+in\s+https?://github\.com/\S+/pull/\d+', '', text)
  text = re.sub(r'\s*\(https?://github\.com/\S+\)', '', text)
  text = re.sub(r'\s*\(#\d+\)', '', text)
  text = re.sub(r'\s+Thanks\s+@[A-Za-z0-9_-]+\.?', '', text, flags=re.IGNORECASE)
  return text.strip()

def is_relevant_change(item):
  """
  Determines if a standard changelog bullet affects MetaClaw's core architecture.
  """
  if IRRELEVANT_PREFIXES.search(item):
    return False
  return bool(RELEVANT_KEYWORDS.search(item))

def extract_sections_from_markdown(body_md, seen_bullets, all_changes=False):
  """
  Parses raw GitHub release Markdown body to extract Breaking and Changes bullets,
  deduplicating items that were already reported in newer point releases.
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
      item = clean_bullet_text(bullet_match.group(1))
      if not item or item in seen_bullets:
        continue

      if current_section == 'Breaking':
        seen_bullets.add(item)
        breaking.append(item)
      elif all_changes or is_relevant_change(item):
        seen_bullets.add(item)
        if current_section == 'Changes':
          changes.append(item)
        else:
          other_bullets.append(item)

  if not breaking and not changes and other_bullets:
    changes = other_bullets

  return breaking, changes

def is_official_stable_release(rel):
  """
  Returns True only if the release is an official stable release matching
  vYYYY.M.D (excluding -beta, -rc, and non-version announcements).
  """
  if rel.get('prerelease') or rel.get('draft'):
    return False
  tag_name = (rel.get('tag_name') or '').strip()
  rel_name = (rel.get('name') or '').strip()
  if 'beta' in tag_name.lower() or 'beta' in rel_name.lower():
    return False
  return bool(re.match(r'^v?\d{4}\.\d+\.\d+(?:-\d+)?$', tag_name))

def main():
  parser = argparse.ArgumentParser(
    description="Parse OpenClaw GitHub releases for breaking and MetaClaw-relevant changes via the GitHub REST API."
  )
  parser.add_argument(
    '-t', '--term', type=str, default='v2026.6.8',
    help="Stopping version term (e.g., 'v2026.6.8'). Script stops once it reaches this version."
  )
  parser.add_argument(
    '-u', '--until', type=str, default='',
    help="Optional upper-bound version term (e.g., 'v2026.10.3'). Skips releases newer than this version."
  )
  parser.add_argument(
    '--include-betas', action='store_true',
    help="Include beta and pre-release versions (excluded by default to save context tokens)."
  )
  parser.add_argument(
    '--all-changes', action='store_true',
    help="Include all platform/channel bullets instead of filtering for MetaClaw-relevant changes."
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
  seen_bullets = set()
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

      # Check termination BEFORE filtering betas so we always stop at the requested boundary
      if term_clean and (term_clean == tag_name.lstrip('v') or term_clean in version_label):
        print(
          f"Termination term '{args.term}' found in '{version_label}'. Stopping."
        )
        term_found = True
        break

      if until_clean and not started_collecting:
        if until_clean == tag_name.lstrip('v') or until_clean in version_label:
          started_collecting = True
        else:
          continue

      if not args.include_betas and not is_official_stable_release(rel):
        continue

      body_md = rel.get('body') or ''
      breaking, changes = extract_sections_from_markdown(
        body_md, seen_bullets, all_changes=args.all_changes
      )

      if not breaking and not changes:
        continue

      content_blocks.append({
        "version": version_label,
        "tag": tag_name,
        "published_at": rel.get('published_at', ''),
        "Breaking": breaking,
        "Changes": changes
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

  print(
    f"Successfully generated {output_file} with {len(content_blocks)} "
    f"official release blocks."
  )

if __name__ == "__main__":
  main()
