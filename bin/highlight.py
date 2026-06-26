import sys
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: python highlight.py <logfile> [strings_to_highlight...]")
        sys.exit(1)

    logfile = sys.argv[1]
    targets = sys.argv[2:]

    if not os.path.exists(logfile):
        print(f"Error: {logfile} not found.")
        sys.exit(1)

    # ANSI 256 color code for Orange (approximate match to HTML #ce9178)
    COLOR_START = "\033[38;5;208m"
    COLOR_END = "\033[0m"

    with open(logfile, 'r', encoding='utf-8') as f:
        content = f.read()

    for target in targets:
        if not target:
            continue
        # Replace occurrences of target with colored target
        content = content.replace(target, f"{COLOR_START}{target}{COLOR_END}")

    # Output the processed content
    print(content, end='')

if __name__ == "__main__":
    main()
