#!/bin/bash

TARGET="${1:-.}"

DEVICE=$(df -P "$TARGET" | tail -1 | awk '{print $1}')
FS_BLOCK=$(stat -f -c "%S" "$TARGET")

if [[ "$DEVICE" == /dev/* ]]; then
    LOG_BLOCK=$(sudo blockdev --getbsz "$DEVICE" 2>/dev/null || echo "N/A")
else
    LOG_BLOCK="N/A"
fi

echo "Filesystem Block Size (bytes)  $FS_BLOCK"
echo "Logical Block Size (bytes)    $LOG_BLOCK"
echo ""
df -hT "$TARGET" | head -n 1
df -hT "$TARGET" | tail -n 1
echo ""
if [[ "$DEVICE" == /dev/* ]]; then
    lsblk -o NAME,SIZE,FSTYPE,PHY-SEC,LOG-SEC | head -n 1
    lsblk -o NAME,SIZE,FSTYPE,PHY-SEC,LOG-SEC -n "$DEVICE"
else
    echo "NAME                      SIZE FSTYPE PHY-SEC LOG-SEC"
fi
echo ""
echo "File Size Histogram (Top 10 Bins by MB) .. this may take a moment..."
find "$TARGET" -type f -exec ls -l {} + 2>/dev/null | awk '{print int($5/1048576) " MB"}' | sort -n | uniq -c | sort -nr | head -n 10
