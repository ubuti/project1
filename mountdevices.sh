#!/bin/bash

# Script to automatically mount all USB devices starting with sda
# Requires root privileges to mount devices

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script requires root privileges. Please run with sudo."
    exit 1
fi

# Base mount point directory
MOUNT_BASE="/home/kit/project1/cameraimg"

# Create base mount directory if it doesn't exist
mkdir -p "$MOUNT_BASE"

echo "Scanning for USB devices (sda*)..."
echo "=================================="

# Counter for mounted devices
mounted_count=0

# Find all block devices starting with sda
for device in /dev/sda*; do
    # Check if the device file actually exists (not just a glob pattern)
    if [ ! -b "$device" ]; then
        continue
    fi
    
    # Skip if it's just /dev/sda (the main device, not a partition)
    if [ "$device" = "/dev/sda" ]; then
        continue
    fi
    
    # Extract device name (e.g., sda1 from /dev/sda1)
    device_name=$(basename "$device")
    
    echo "Found device: $device"
    
    # Check if device is already mounted
    if mount | grep -q "$device"; then
        mount_point=$(mount | grep "$device" | awk '{print $3}')
        echo "  → Already mounted at: $mount_point"
        continue
    fi
    
    # Create mount point
    mount_point="$MOUNT_BASE/$device_name"
    mkdir -p "$mount_point"
    
    # Try to determine filesystem type
    fs_type=$(blkid -o value -s TYPE "$device" 2>/dev/null)
    
    if [ -n "$fs_type" ]; then
        echo "  → Filesystem: $fs_type"
        
        # Mount the device
        if mount -t "$fs_type" "$device" "$mount_point" 2>/dev/null; then
            echo "  → Successfully mounted at: $mount_point"
            
            # Set permissions for user access
            chmod 755 "$mount_point"
            
            # Show mount info
            df -h "$mount_point" | tail -1 | awk '{printf "  → Size: %s, Used: %s, Available: %s\n", $2, $3, $4}'
            
            ((mounted_count++))
        else
            echo "  → Failed to mount $device"
            rmdir "$mount_point" 2>/dev/null
        fi
    else
        echo "  → Unknown or unsupported filesystem"
        rmdir "$mount_point" 2>/dev/null
    fi
    
    echo ""
done

echo "=================================="
echo "Summary: $mounted_count USB device(s) mounted"

if [ $mounted_count -gt 0 ]; then
    echo ""
    echo "Mounted USB devices:"
    echo "-------------------"
    mount | grep "$MOUNT_BASE" | while read line; do
        device=$(echo "$line" | awk '{print $1}')
        mount_point=$(echo "$line" | awk '{print $3}')
        echo "  $device → $mount_point"
    done
    
    echo ""
    echo "To unmount all USB devices later, you can run:"
    echo "  sudo umount $MOUNT_BASE/*"
fi
