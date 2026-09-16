#!/usr/bin/env python3
import os
import argparse
import sys

# Extensible set for directories to ignore
IGNORED_DIRS = {'mnt'}

def get_dir_size(path: str) -> int:
    """
    Recursively calculates the total size of a directory in bytes.
    Ignores symlinks and gracefully skips inaccessible files/folders.
    """
    total_size = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_file(follow_symlinks=False):
                        total_size += entry.stat(follow_symlinks=False).st_size
                    elif entry.is_dir(follow_symlinks=False):
                        total_size += get_dir_size(entry.path)
                except (OSError, PermissionError):
                    # Continue processing other entries if access is denied to one
                    continue
    except (OSError, PermissionError):
        # Skip directories we cannot read at all
        pass

    return total_size

def find_large_directories(directory: str, threshold_gb: float) -> None:
    """
    Identifies immediate child subdirectories and their disk usage.
    Recurses into subdirectories that exceed the GiB threshold.
    """
    threshold_bytes = threshold_gb * (1024 ** 3)

    try:
        with os.scandir(directory) as it:
            entries = list(it)
    except (OSError, PermissionError) as e:
        print(f"Error accessing {directory}: {e}", file=sys.stderr)
        return

    for entry in entries:
        # Only process directories, skipping symlinks acting as directories
        if not entry.is_dir(follow_symlinks=False):
            continue

        if entry.name in IGNORED_DIRS:
            print(f"Ignoring directory: {entry.path}")
            continue

        size_bytes = get_dir_size(entry.path)
        size_gb = size_bytes / (1024 ** 3)

        print(f"Directory: {entry.path} | Size: {size_bytes} bytes ({size_gb:.2f} GiB)")

        if size_bytes > threshold_bytes:
            find_large_directories(entry.path, threshold_gb)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recursively identify large subdirectories on disk."
    )
    parser.add_argument(
        "-t", "--threshold",
        type=float,
        default=1.0,
        help="Size threshold in GiB to trigger recursive scanning (default: 1.0)"
    )

    args = parser.parse_args()
    target_dir = '/'

    print(f"Scanning '{target_dir}' with a recursive threshold of {args.threshold} GiB...")
    find_large_directories(target_dir, args.threshold)

if __name__ == "__main__":
    main()
