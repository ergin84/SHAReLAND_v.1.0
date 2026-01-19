# VPS Provider Firewall Configuration

## Current Situation

✅ **VPS Firewall (UFW) is correctly configured:**
- Port 22 (SSH) - ALLOWED
- Port 80 (HTTP) - ALLOWED  
- Port 443 (HTTPS) - ALLOWED

❌ **But port 22 is still not accessible externally**

This suggests there may be a **network-level firewall** at the VPS provider (Aruba Cloud) level.

## Solution: Check Aruba Cloud Firewall

### Step 1: Access Aruba Cloud Control Panel

1. Go to: https://admin.dc1.computing.cloud.it
2. Log in with your Aruba Cloud credentials
3. Navigate to your VPS/server

### Step 2: Check Network/Firewall Settings

Look for:
- **"Firewall"** or **"Security Groups"** section
- **"Network Rules"** or **"Access Rules"**
- **"Port Management"** or **"Inbound Rules"**

### Step 3: Allow SSH (Port 22)

In the Aruba Cloud panel, ensure:
- **Port 22** is allowed for **inbound** connections
- **Source**: Anywhere (0.0.0.0/0) or your IP
- **Protocol**: TCP
- **Action**: Allow

### Step 4: Save and Apply

After configuring, save the rules and wait 1-2 minutes for them to propagate.

## Alternative: Use VPS Console for Deployment

Since you have console access, you can deploy directly from the console:

### Option 1: Run Deployment Commands Manually

In the VPS console, run the deployment steps from `DEPLOYMENT_INSTRUCTIONS.md`

### Option 2: Upload Script via Console

1. Copy the deployment script content
2. In VPS console, create the file:
   ```bash
   nano /tmp/update_vps.sh
   ```
3. Paste the script content
4. Run it:
   ```bash
   bash /tmp/update_vps.sh
   ```

## Quick Test from VPS Console

While in the VPS console, verify SSH is listening:

```bash
# Check SSH is listening
ss -tlnp | grep 22

# Should show:
# LISTEN 0 128 0.0.0.0:22 0.0.0.0:* users:(("sshd",pid=779,fd=3))
```

If SSH is listening but not accessible externally, it's definitely a provider-level firewall.

## Aruba Cloud Specific

Aruba Cloud may have:
- **Network Security Groups** - Check in the control panel
- **DDoS Protection** - May block some connections
- **IP Restrictions** - May need to whitelist your IP

## Next Steps

1. **Check Aruba Cloud Control Panel** for firewall/security settings
2. **Allow port 22** in the provider's firewall
3. **Wait 2-3 minutes** for changes to propagate
4. **Test SSH connection** again
5. **If still blocked**, use VPS console to deploy manually





