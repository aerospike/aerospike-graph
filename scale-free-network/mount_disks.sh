#!/bin/bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (with sudo)"
    exit 1
fi

# Function to check if device exists
check_device() {
    if [ ! -b "$1" ]; then
        echo "Error: Device $1 does not exist"
        return 1
    fi
    return 0
}

# Function to check if device is already mounted
check_if_mounted() {
    if mountpoint -q "$1"; then
        echo "Warning: $1 is already mounted"
        return 1
    fi
    return 0
}

# Function to check available space
check_space() {
    local device=$1
    local size=$(blockdev --getsize64 $device)
    echo "Device $device size: $(($size/1024/1024/1024)) GB"
}

# Function to mount a single device
mount_device() {
    local dev=$1
    local dir=$2
    local success=0

    echo "Processing $dev..."
    
    # Check if device exists
    if ! check_device "$dev"; then
        echo "Skipping $dev"
        return 1
    fi
    
    # Create mount point
    echo "Creating mount point $dir..."
    if ! mkdir -p "$dir"; then
        echo "Failed to create $dir"
        return 1
    fi

    # Check if mount point is already in use
    if check_if_mounted "$dir"; then
        echo "Skipping $dir as it's already mounted"
        return 1
    fi
    
    # Display device size
    check_space "$dev"
    
    # Format the device
    echo "Formatting $dev with ext4..."
    if ! mkfs.ext4 -F "$dev"; then
        echo "Failed to format $dev"
        return 1
    fi
    
    # Mount the device
    echo "Mounting $dev to $dir..."
    if ! mount "$dev" "$dir"; then
        echo "Failed to mount $dev to $dir"
        return 1
    fi
    
    # Set permissions
    echo "Setting permissions for $dir..."
    if ! chown "$SUDO_USER:$SUDO_USER" "$dir"; then
        echo "Failed to set permissions on $dir"
        umount "$dir" 2>/dev/null
        return 1
    fi
    
    echo "Successfully processed $dev"
    return 0
}

echo "Starting disk initialization and mounting process..."
echo "This will FORMAT and MOUNT devices /dev/nvme0n1 through /dev/nvme0n24"
echo "ALL DATA ON THESE DEVICES WILL BE LOST!"
read -p "Are you sure you want to continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operation cancelled"
    exit 1
fi

# Track successful mounts
successful_mounts=()

# Process each device
for i in {1..24}; do
    dev="/dev/nvme0n$i"
    dir="/mnt/data$i"
    
    if mount_device "$dev" "$dir"; then
        successful_mounts+=("$dev")
    fi
done

# Add entries to /etc/fstab for persistence across reboots
echo "Adding entries to /etc/fstab..."
for dev in "${successful_mounts[@]}"; do
    dir="/mnt/data${dev##*/nvme0n}"  # Extract number from device path
    
    # Check if entry already exists
    if ! grep -q "$dev" /etc/fstab; then
        echo "$dev $dir ext4 defaults 0 0" >> /etc/fstab
        echo "Added $dev to /etc/fstab"
    fi
done

echo "Verifying mounts..."
df -h | grep "/mnt/data"

echo -e "\nMount summary:"
echo "Successfully mounted: ${#successful_mounts[@]} devices"
echo "Failed to mount: $((24 - ${#successful_mounts[@]})) devices"

if [ ${#successful_mounts[@]} -eq 0 ]; then
    echo "ERROR: No devices were mounted successfully!"
    exit 1
fi

echo "Done! Use these directories in your graph generation script:"
echo "${successful_mounts[@]/#/\/mnt\/data}" | tr ' ' ','