# VPS Connection Troubleshooting Guide

## Current Issue: SSH Connection Refused

You're getting `ssh: connect to host 5.249.148.147 port 22: Connection refused`

This means the VPS is either:
1. **Not running** (powered off)
2. **SSH service is stopped**
3. **Firewall is blocking port 22**
4. **SSH is on a different port**

## Quick Diagnosis

Run the diagnostic script:
```bash
./check_vps_status.sh
```

This will check:
- If VPS is reachable (ping)
- If SSH port 22 is open
- If HTTP port 80 is open (web server)
- If HTTPS port 443 is open
- Alternative SSH ports

## Solutions

### Solution 1: Check VPS Provider Dashboard

1. Log into your VPS provider's control panel (Aruba, etc.)
2. Check if the VPS is **running**
3. Check if it's been **suspended** or **stopped**
4. Look for any **alerts** or **notifications**

### Solution 2: Use VPS Provider's Web Console

Most VPS providers offer a web-based console:

1. Log into your VPS provider dashboard
2. Find "Console" or "Terminal" or "VNC" access
3. Access the VPS directly through the web interface
4. Once inside, you can:
   ```bash
   # Check SSH service status
   systemctl status ssh
   # or
   systemctl status sshd
   
   # Start SSH if it's stopped
   systemctl start ssh
   # or
   systemctl start sshd
   
   # Enable SSH to start on boot
   systemctl enable ssh
   ```

### Solution 3: Check Firewall

If you can access via web console:

```bash
# Check firewall status
ufw status
# or
iptables -L

# If firewall is blocking, allow SSH
ufw allow 22/tcp
# or
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
```

### Solution 4: Check SSH Service

```bash
# Check if SSH is installed and running
systemctl status ssh
systemctl status sshd

# If not running, start it
systemctl start ssh
systemctl enable ssh

# Check SSH configuration
cat /etc/ssh/sshd_config | grep Port
```

### Solution 5: Alternative SSH Port

Some VPS providers use non-standard SSH ports:

```bash
# Try common alternative ports
ssh -p 2222 root@5.249.148.147
ssh -p 22022 root@5.249.148.147
ssh -p 2200 root@5.249.148.147
```

## If VPS is Completely Inaccessible

### Option A: Contact VPS Provider Support

Contact your VPS provider (Aruba) support and ask:
- Is the VPS running?
- Has the IP address changed?
- Is there a service outage?
- Can you restart the VPS?

### Option B: Check VPS Provider Dashboard

1. **Power Status**: Is the VPS powered on?
2. **Network**: Are there network issues?
3. **IP Address**: Has the IP changed?
4. **Resources**: Is the VPS out of resources (CPU/RAM)?

### Option C: Restart VPS from Dashboard

If your VPS provider dashboard allows:
1. **Reboot** the VPS from the control panel
2. Wait 2-3 minutes for it to come back online
3. Try SSH again

## Alternative Deployment Methods

### Method 1: Deploy via VPS Provider's Console

If you can access via web console:

1. Access VPS through provider's console
2. Run the deployment commands manually (see `DEPLOYMENT_INSTRUCTIONS.md`)
3. Or upload and run the deployment script

### Method 2: Use SCP/RSYNC (if port 22 opens)

Once SSH is working:

```bash
# Copy deployment script to VPS
scp update_vps_code.sh root@5.249.148.147:/tmp/

# SSH and run it
ssh root@5.249.148.147 'bash /tmp/update_vps_code.sh'
```

### Method 3: Manual Deployment via Console

If you can only access via web console, follow the manual steps in `DEPLOYMENT_INSTRUCTIONS.md`

## Checking VPS Status Remotely

### Check if Web Server is Running

```bash
# Test HTTP
curl -I http://5.249.148.147

# If this works, VPS is running but SSH might be down
```

### Check DNS/Website

```bash
# If you have a domain
curl -I http://shareland.it

# This will tell you if the web server is responding
```

## Common VPS Provider Issues

### Aruba VPS Specific

1. **Check Aruba Cloud Panel**: https://panel.arubacloud.com
2. **Look for**: Server status, IP address, console access
3. **Check**: Billing status (suspended accounts can't access)
4. **Verify**: IP address hasn't changed

### General VPS Issues

1. **Out of Resources**: VPS might be frozen due to high CPU/RAM usage
2. **Network Issues**: Provider might have network problems
3. **Maintenance**: VPS might be in maintenance mode
4. **Suspension**: Account might be suspended

## Next Steps

1. **Run diagnostic**: `./check_vps_status.sh`
2. **Check VPS provider dashboard**
3. **Try web console access**
4. **Contact support if needed**
5. **Once accessible, run deployment**: `./update_vps_code.sh`

## Emergency: If VPS is Down

If the VPS is completely down and you need to deploy:

1. **Wait for VPS to come back online**
2. **Or contact VPS provider to restart it**
3. **Once back online, SSH will work again**
4. **Then run the deployment script**

## Summary

**Most likely causes:**
- VPS is powered off (check dashboard)
- SSH service is stopped (restart via console)
- Firewall is blocking (allow port 22)
- Network issues (contact provider)

**Quick fix:**
1. Access VPS via provider's web console
2. Start SSH service: `systemctl start ssh`
3. Try SSH again: `ssh root@5.249.148.147`



