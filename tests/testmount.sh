# 1. Stop the service
sudo systemctl stop mount-usb.service

# 2. Manually test mount
sudo mount /home/kit/project1/cameraimg  # Should fail or show what's wrong

# 3. Check what should be mounted
lsblk

# 4. Test with complete command
sudo mount /dev/sda1 /home/kit/project1/cameraimg

# 5. Verify it appears in df
df -h

# 6. Unmount and test service
sudo umount /home/kit/project1/cameraimg
sudo systemctl start mount-usb.service
df -h
