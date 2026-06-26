import argparse
import requests
from lxml import html
import os
import sys

def main():
  parser = argparse.ArgumentParser(
    description="Parse OpenClaw GitHub releases for breaking changes."
  )
  parser.add_argument(
    '-t', '--term', type=str, default='2026.3.28',
    help="Stopping term (e.g., '2026.3.28'). Script stops when h2 contains it."
  )
  args = parser.parse_args()

  url = 'https://github.com/openclaw/openclaw/releases'
  output_file = 'openclaw_releases.md'

  content_blocks = []

  while url:
    print(f"Fetching {url}...")
    try:
      response = requests.get(url, timeout=30)
      response.raise_for_status()
    except Exception as e:
      print(f"Error fetching releases: {e}")
      break

    tree = html.fromstring(response.content)

    # Find the div that has attributes data-pjax and data-hpc both empty
    # GitHub often uses these for PJAX navigation containers.
    main_divs = tree.xpath('//div[@data-pjax="" and @data-hpc=""]')
    if not main_divs:
      print("Could not find the target releases container.")
      break

    container = main_divs[0]
    sections = container.xpath('./section')

    term_found = False

    for section in sections:
      # First child of section is an h2 containing the version
      h2_nodes = section.xpath('./h2')
      if not h2_nodes:
        continue

      version_text = h2_nodes[0].text_content().strip()

      # Check for termination
      if args.term in version_text:
        print(
          f"Termination term '{args.term}' found in {version_text}. Stopping."
        )
        term_found = True
        break

      block = {
        "version": version_text,
        "Breaking": [],
        "Changes": []
      }

      # Find all h3 nodes in the section tree
      h3_nodes = section.xpath('.//h3')
      for h3 in h3_nodes:
        text = h3.text_content().strip()
        if text in ['Breaking', 'Changes']:
          # Obtain the next sibling of h3 (expected to be a <ul>)
          ul_candidates = h3.xpath('./following-sibling::ul[1]')
          if ul_candidates:
            items = ul_candidates[0].xpath('./li')
            for li in items:
              block[text].append(li.text_content().strip())

      content_blocks.append(block)

    if term_found:
      break

    # Extract the Next page URL from the pagination block
    next_link = tree.xpath('//a[contains(text(), "Next")]/@href')
    if next_link:
      next_url = next_link[0]
      url = f"https://github.com{next_url}" if next_url.startswith('/') else next_url
    else:
      print("No additional pages found.")
      url = None

  # Write to Markdown
  with open(output_file, 'w', encoding='utf-8') as f:
    for b in content_blocks:
      f.write(f"# Release: {b['version']}\n\n")

      if b['Breaking']:
        f.write("## Breaking\n")
        for item in b['Breaking']:
          f.write(f"- {item}\n")
        f.write("\n")

      if b['Changes']:
        f.write("## Changes\n")
        for item in b['Changes']:
          f.write(f"- {item}\n")
        f.write("\n")

  print(
    f"Successfully generated {output_file} with {len(content_blocks)} "
    f"release blocks."
  )

if __name__ == "__main__":
  main()
