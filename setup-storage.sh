#!/bin/bash
# Script finds attached storage on device and sets correct path to save files to

lines=$(df -H | grep "/dev/sda" | wc -l)
echo "There are $lines USB device(s) mounted"

if [ $lines -eq 0 ]; then
    echo "No USB devices found. Exiting."
    exit 1
fi

if [ $lines -eq 1 ]; then
    echo "One USB device found. Trying set up."
    best_path=$(df -H | grep "/dev/sda" | awk '{print $6}')
    touch storagepath
    echo "$best_path" > storagepath
    exit 1
fi

# Store df output in array - each line as separate element
mapfile -t output < <(df -H | grep "/dev/sda")

maxcap=0
best_path="empty"

# Process each line (device) separately
for line in "${output[@]}"; do
    current_path=$(echo "$line" | awk '{print $6}')
    current_cap=$(echo "$line" | awk '{print $4}')
    
    # Remove units (G, M, K) and convert to comparable number
    # Extract numeric part only
    cap_numeric=$(echo "$current_cap" | sed 's/[^0-9.]//g')
    
    # Handle empty or invalid capacity
    if [ -z "$cap_numeric" ]; then
        continue
    fi
    
    # Convert to bytes for proper comparison (approximate)
    if [[ "$current_cap" == *"T"* ]]; then
        cap_bytes=$(echo "$cap_numeric * 1000000000000" | bc -l 2>/dev/null || echo "$cap_numeric")
    elif [[ "$current_cap" == *"G"* ]]; then
        cap_bytes=$(echo "$cap_numeric * 1000000000" | bc -l 2>/dev/null || echo "$cap_numeric")
    elif [[ "$current_cap" == *"M"* ]]; then
        cap_bytes=$(echo "$cap_numeric * 1000000" | bc -l 2>/dev/null || echo "$cap_numeric")
    elif [[ "$current_cap" == *"K"* ]]; then
        cap_bytes=$(echo "$cap_numeric * 1000" | bc -l 2>/dev/null || echo "$cap_numeric")
    else
        cap_bytes=$cap_numeric
    fi
    
    # Convert to integer for comparison (remove decimal part)
    cap_bytes=${cap_bytes%.*}
    
    echo "Device: $(echo "$line" | awk '{print $1}') - Available: $current_cap - Path: $current_path"
    
    # Compare and update if this device has more available space
    if (( cap_bytes > maxcap )); then
        maxcap=$cap_bytes
        best_path=$current_path
    fi
done

# Create config file with the path
touch storagepath
echo "$best_path" > storagepath

echo "=================================="
echo "Selected storage path: $best_path"
echo "Available space: $(df -H | grep "$best_path" | awk '{print $4}')"
echo "Path stored in 'storagepath' config file"
