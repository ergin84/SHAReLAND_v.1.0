#!/bin/bash

################################################################################
# Fix VPS Firewall for SSH Access
# Commands to run on VPS console to allow SSH
# Usage: Copy and paste these commands into VPS console
################################################################################

cat << 'EOF'
========================================
Firewall Configuration for SSH Access
========================================

Run these commands in the VPS console (where you're logged in):

1. Check if UFW (firewall) is active:
   ufw status

2. If UFW is active, allow SSH:
   ufw allow 22/tcp
   ufw allow ssh

3. If using iptables, allow SSH:
   iptables -A INPUT -p tcp --dport 22 -j ACCEPT
   iptables-save > /etc/iptables/rules.v4

4. Check SSH service is listening:
   netstat -tlnp | grep 22
   # or
   ss -tlnp | grep 22

5. Verify SSH is accessible:
   systemctl status ssh

6. If needed, restart SSH:
   systemctl restart ssh

========================================
Quick Fix (All-in-one):
========================================

Run this single command block in VPS console:

ufw allow 22/tcp 2>/dev/null || iptables -A INPUT -p tcp --dport 22 -j ACCEPT
systemctl restart ssh
systemctl status ssh

========================================
EOF





