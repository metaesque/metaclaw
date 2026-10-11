#!/usr/bin/env python3
"""
Profiles a massive `find . -ls` cluster dump by tracking SSD boundaries (marked by '#')
and aggregating sizes into a semantic directory tree. Filters out noise to preserve
LLM context windows.
"""
import sys

def build_tree(cluster_file, min_mb=250):
    ssd_trees = {}
    current_ssd = "UNKNOWN_SSD"

    try:
        with open(cluster_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Detect SSD/Host boundaries
                if line.startswith('#'):
                    current_ssd = line.lstrip('#').strip()
                    if current_ssd not in ssd_trees:
                        ssd_trees[current_ssd] = {}
                    continue

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

                # Normalize path
                if path.startswith('./'):
                    path = path[1:]
                if not path.startswith('/'):
                    path = '/' + path

                path_parts = [p for p in path.split('/') if p]

                # Roll up sizes for all parent directories
                for i in range(1, len(path_parts) + 1):
                    dir_key = "/" + "/".join(path_parts[:i])
                    if dir_key not in ssd_trees[current_ssd]:
                        ssd_trees[current_ssd][dir_key] = 0
                    ssd_trees[current_ssd][dir_key] += size

    except Exception as e:
        print(f"Error reading {cluster_file}: {e}")
        sys.exit(1)

    # Print the aggregated tree
    for ssd, dirs in ssd_trees.items():
        print(f"==================================================")
        print(f"💽 SSD / HOST: {ssd}")
        print(f"==================================================")

        # Sort by path to print as a hierarchical tree
        sorted_dirs = sorted(dirs.keys())
        for d in sorted_dirs:
            size_mb = dirs[d] / (1024 * 1024)
            if size_mb >= min_mb:
                depth = d.count('/') - 1
                indent = "  " * depth
                dir_name = d.split('/')[-1]

                if size_mb > 1024:
                    print(f"{indent}├── {dir_name}/ ({size_mb/1024:.2f} GB)")
                else:
                    print(f"{indent}├── {dir_name}/ ({size_mb:.0f} MB)")
        print("\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 profile_ssd_clusters.py <CLUSTER_FILE>")
        sys.exit(1)

    # Optional threshold override (e.g., python3 profile_ssd_clusters.py CLUSTER 500)
    threshold = int(sys.argv[2]) if len(sys.argv) > 2 else 250
    build_tree(sys.argv[1], min_mb=threshold)
