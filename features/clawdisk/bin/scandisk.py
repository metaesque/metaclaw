#!/usr/bin/env python3
import os
import argparse
import sys
import time

# Extensible set for directories to ignore
IGNORED_DIRS = {'mnt'}

class ScanTimeout(Exception):
    """Raised when directory scanning exceeds the allocated time limit."""
    pass

def get_dir_size(path: str, deadline: float) -> int:
    """
    Recursively calculates the total size of a directory in bytes.
    Ignores symlinks and gracefully skips inaccessible files/folders.
    Raises ScanTimeout if execution time exceeds the deadline.
    """
    if time.time() > deadline:
        raise ScanTimeout()

    total_size = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                if time.time() > deadline:
                    raise ScanTimeout()
                try:
                    if entry.is_file(follow_symlinks=False):
                        total_size += entry.stat(follow_symlinks=False).st_size
                    elif entry.is_dir(follow_symlinks=False):
                        total_size += get_dir_size(entry.path, deadline)
                except (OSError, PermissionError):
                    # Continue processing other entries if access is denied to one
                    continue
    except (OSError, PermissionError):
        # Skip directories we cannot read at all
        pass

    return total_size

def find_large_directories(directory: str, threshold_gb: float, min_gb: float, maxtime: float, is_full: bool, depth: int = 0) -> None:
    """
    Identifies immediate child subdirectories and files and their disk usage.
    Ignores items under min_gb, but aggregates their sum.
    Prints the aggregated sum if is_full is True OR if the sum exceeds threshold_gb.
    Recurses into subdirectories that exceed the threshold_gb.
    Times out if directory calculation takes longer than maxtime seconds,
    but still recurses into the timed-out directory.
    Indents the printed path based on traversal depth.
    """
    threshold_bytes = threshold_gb * (1024 ** 3)
    min_bytes = min_gb * (1024 ** 3)

    try:
        with os.scandir(directory) as it:
            entries = list(it)
    except (OSError, PermissionError) as e:
        print(f"Error accessing {directory}: {e}", file=sys.stderr)
        return

    small_size_sum = 0
    small_files_count = 0
    small_dirs_count = 0

    for entry in entries:
        if entry.is_symlink():
            continue

        if entry.is_file(follow_symlinks=False):
            try:
                size_bytes = entry.stat(follow_symlinks=False).st_size
            except (OSError, PermissionError):
                continue

            if size_bytes < min_bytes:
                small_size_sum += size_bytes
                small_files_count += 1
                continue

            size_gb = size_bytes / (1024 ** 3)
            display_path = entry.path if depth == 0 else ("  " * depth) + entry.name

            # Columns: size in GiB (8 chars), size in bytes (12 chars), path
            print(f"{size_gb:>8.3f} {size_bytes:>12} {display_path}")

        elif entry.is_dir(follow_symlinks=False):
            # Format the display path: full path for depth 0, indented basename for deeper levels, trailing slash for dirs
            display_path = (entry.path if depth == 0 else ("  " * depth) + entry.name) + "/"

            if entry.name in IGNORED_DIRS:
                print(f"{'N/A':>8} {'Ignored':>12} {display_path}")
                continue

            deadline = time.time() + maxtime

            try:
                size_bytes = get_dir_size(entry.path, deadline)
            except ScanTimeout:
                print(f"{' ':>8} {'unknown':>12} {display_path}")
                # Recurse into the directory assuming it exceeds the size threshold
                find_large_directories(entry.path, threshold_gb, min_gb, maxtime, is_full, depth + 1)
                continue

            if size_bytes < min_bytes:
                small_size_sum += size_bytes
                small_dirs_count += 1
                continue

            size_gb = size_bytes / (1024 ** 3)

            # Columns: size in GiB (8 chars), size in bytes (12 chars), path
            print(f"{size_gb:>8.3f} {size_bytes:>12} {display_path}")

            if size_bytes > threshold_bytes:
                find_large_directories(entry.path, threshold_gb, min_gb, maxtime, is_full, depth + 1)

    # Output the aggregated small files/dirs row for this directory if requested or if sum exceeds threshold
    if (is_full or small_size_sum > threshold_bytes) and (small_files_count > 0 or small_dirs_count > 0):
        size_gb = small_size_sum / (1024 ** 3)
        indent = "  " * depth
        summary_path = f"{indent}{small_files_count} files, {small_dirs_count} dirs"
        print(f"{size_gb:>8.3f} {small_size_sum:>12} {summary_path}")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recursively identify large subdirectories and files on disk."
    )
    parser.add_argument(
        "-t", "--threshold",
        type=float,
        default=1.0,
        help="Size threshold in GiB to trigger recursive scanning (default: 1.0)"
    )
    parser.add_argument(
        "-m", "--min",
        type=float,
        default=0.1,
        help="Minimum size in GiB to report a directory or file (default: 0.1)"
    )
    parser.add_argument(
        "-x", "--maxtime",
        type=float,
        default=10.0,
        help="Maximum time in seconds to determine the size of a directory (default: 10.0)"
    )
    parser.add_argument(
        "-f", "--full",
        action="store_true",
        help="Print a summary row mapping the aggregate size of all child files/dirs under the minimum threshold"
    )

    args = parser.parse_args()
    target_dir = '/'

    print(f"Scanning '{target_dir}' with recursive threshold >= {args.threshold} GiB and minimum display >= {args.min} GiB...")
    print(f"{'GiB':>8} {'Bytes':>12} Path")
    print("-" * 50)

    find_large_directories(target_dir, args.threshold, args.min, args.maxtime, args.full, depth=0)

if __name__ == "__main__":
    main()
