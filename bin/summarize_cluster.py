#!/usr/bin/env python3
"""
Summarizes massive `find . -ls` output files by aggregating sizes across top-level
directories and tallying file extensions to drastically reduce token impact.
"""
import sys
from collections import defaultdict

def summarize(file_path, max_depth=3, min_mb=10):
    dir_stats = defaultdict(lambda: {"size": 0, "count": 0})
    ext_stats = defaultdict(lambda: {"size": 0, "count": 0})

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                parts = line.split()
                # standard find -ls output has 11+ columns
                if len(parts) < 11:
                    continue
                try:
                    # Size is standard at index 6 in `find . -ls`
                    size = int(parts[6])
                except ValueError:
                    continue

                path = " ".join(parts[10:])
                path_parts = [p for p in path.split('/') if p and p != '.']

                # Directory roll-up
                for i in range(1, min(len(path_parts), max_depth) + 1):
                    dir_key = "/" + "/".join(path_parts[:i])
                    dir_stats[dir_key]["size"] += size
                    dir_stats[dir_key]["count"] += 1

                # Extension roll-up
                if path_parts and '.' in path_parts[-1]:
                    ext = path_parts[-1].split('.')[-1].lower()
                    if len(ext) <= 5:
                        ext_stats[ext]["size"] += size
                        ext_stats[ext]["count"] += 1

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        sys.exit(1)

    print(f"--- Top Directories (> {min_mb}MB, Depth {max_depth}) ---")
    for k, v in sorted(dir_stats.items()):
        size_mb = v["size"] / (1024 * 1024)
        if size_mb >= min_mb:
            print(f"{k}: {size_mb:.2f} MB ({v['count']} files)")

    print("\n--- Largest File Extensions by Size ---")
    sorted_exts = sorted(ext_stats.items(), key=lambda x: x[1]["size"], reverse=True)[:25]
    for ext, stats in sorted_exts:
        print(f".{ext}: {stats['size'] / (1024 * 1024):.2f} MB ({stats['count']} files)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 summarize_cluster.py <CLUSTER_FILE>")
        sys.exit(1)
    summarize(sys.argv[1])
