#!/bin/bash
# ==============================================================================
# MetaClaw: SSD Dynamics Profiler
# Extracts filesystem cluster sizes, hardware block sizes, and a file size histogram.
# Usage: ./ssd_info.sh [/path/to/mount]
# ==============================================================================

TARGET="${1:-.}"

echo "================================================================================"
echo " SSD Dynamics Profile: $TARGET"
echo "================================================================================"

# Resolve the underlying block device for the target directory
DEVICE=$(df -P "$TARGET" | tail -1 | awk '{print $1}')

echo "--- [1] Filesystem Information (df) ---"
df -hT "$TARGET"
echo ""

echo "--- [2] Filesystem Cluster/Block Size (stat) ---"
stat -f -c "Filesystem Block Size (Bytes): %S" "$TARGET"
echo ""

if [[ "$DEVICE" == /dev/* ]]; then
    echo "--- [3] Hardware Block Device Information (lsblk) ---"
    lsblk -o NAME,SIZE,FSTYPE,PHY-SEC,LOG-SEC "$DEVICE"
    echo ""

    echo "--- [4] Logical Hardware Block Size (blockdev) ---"
    # Requires sudo to read raw block device params
    sudo blockdev --getbsz "$DEVICE" 2>/dev/null || echo "(Requires sudo to execute blockdev)"
    echo ""
else
    echo "--- [3/4] Hardware Info ---"
    echo "Target does not map to a standard physical block device ($DEVICE)."
    echo ""
fi

echo "--- [5] File Size Histogram (Top 10 Bins by MB) ---"
echo "Scanning tree (this may take a moment)..."
# Calculates file sizes in MB, sorts them into bins, and counts occurrences
find "$TARGET" -type f -exec ls -l {} + 2>/dev/null | awk '{print int($5/1048576) " MB"}' | sort -n | uniq -c | sort -nr | head -n 10
echo "================================================================================"

