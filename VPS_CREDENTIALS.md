# VPS Credentials

## SSH Access

- **IP Address**: `5.249.148.147`
- **Username**: `root`
- **Password**: `Sh@r3l@nd2025/26`

## Connection Methods

### Method 1: Using sshpass (Automated)

```bash
# Install sshpass if needed
sudo apt-get install sshpass

# Connect using the script
./connect_vps.sh

# Or connect manually
sshpass -p "Sh@r3l@nd2025/26" ssh root@5.249.148.147
```

### Method 2: Manual SSH (Interactive)

```bash
ssh root@5.249.148.147
# When prompted, enter password: Sh@r3l@nd2025/26
```

### Method 3: Using SSH Keys (Recommended for Security)

Once you can access the VPS, set up SSH keys:

```bash
# On your local machine
ssh-copy-id root@5.249.148.147
# Enter password when prompted

# Then you can connect without password
ssh root@5.249.148.147
```

## Current Issue

**SSH port 22 is currently closed** - The SSH service needs to be started.

### Solution: Access via VPS Provider Console

1. Log into your VPS provider dashboard (Aruba Cloud Panel)
2. Access the VPS via web console/terminal
3. Start SSH service:
   ```bash
   systemctl start ssh
   systemctl enable ssh
   ```
4. Then try connecting again

## Security Notes

⚠️ **Important**: This password is stored in plain text in the repository. For production:

1. **Use SSH keys** instead of passwords
2. **Disable password authentication** once keys are set up
3. **Change the default password** to something stronger
4. **Consider using a password manager** instead of storing in code

## Quick Connect Script

Use the provided script:
```bash
./connect_vps.sh
```

This will automatically use the password to connect.



