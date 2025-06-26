#!/bin/bash
set -e  # Exit on any error

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
}

# Function to check if device is already mounted
check_if_mounted() {
    if mountpoint -q "$1"; then
        echo "Warning: $1 is already mounted"
        return 1
    fi
}

# Function to check available space
check_space() {
    local device=$1
    local size=$(blockdev --getsize64 $device)
    echo "Device $device size: $(($size/1024/1024/1024)) GB"
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

for i in {1..24}; do
    dev="/dev/nvme0n$i"
    dir="/mnt/data$i"
    
    echo "Processing $dev..."
    
    # Check if device exists
    if ! check_device "$dev"; then
        echo "Skipping $dev"
        continue
    fi
    
    # Check if mount point is already in use
    if check_if_mounted "$dir"; then
        echo "Skipping $dir as it's already mounted"
        continue
    fi
    
    # Display device size
    check_space "$dev"
    
    echo "Formatting $dev with ext4..."
    mkfs.ext4 -F "$dev"
    
    echo "Creating mount point $dir..."
    mkdir -p "$dir"
    
    echo "Mounting $dev to $dir..."
    mount "$dev" "$dir"
    
    echo "Setting permissions for $dir..."
    chown "$SUDO_USER:$SUDO_USER" "$dir"
    
    echo "Successfully processed $dev"
done

# Add entries to /etc/fstab for persistence across reboots
echo "Adding entries to /etc/fstab..."
for i in {1..24}; do
    dev="/dev/nvme0n$i"
    dir="/mnt/data$i"
    
    if [ -b "$dev" ] && [ -d "$dir" ]; then
        # Check if entry already exists
        if ! grep -q "$dev" /etc/fstab; then
            echo "$dev $dir ext4 defaults 0 0" >> /etc/fstab
            echo "Added $dev to /etc/fstab"
        fi
    fi
done

echo "Verifying mounts..."
mount -a

echo "Done! All available devices have been formatted and mounted."
df -h | grep "/mnt/data"