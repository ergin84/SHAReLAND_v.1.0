#!/bin/bash
# Script to configure PostgreSQL server in pgAdmin
# This script should be run after pgAdmin is started and you've logged in at least once

echo "Configuring PostgreSQL server in pgAdmin..."

# Wait a bit for pgAdmin to be ready
sleep 5

# Find the user directory (email-based)
USER_DIR=$(docker exec shareland-pgadmin find /var/lib/pgadmin/storage -type d -name "*admin*" 2>/dev/null | head -1)

if [ -z "$USER_DIR" ]; then
    echo "User directory not found. Please login to pgAdmin first at http://localhost:5050"
    echo "After logging in, run this script again."
    exit 1
fi

echo "Found user directory: $USER_DIR"

# Create servers.json
cat > /tmp/servers.json << 'EOF'
{
  "Servers": {
    "1": {
      "Name": "ShareLand PostgreSQL",
      "Group": "Servers",
      "Host": "db",
      "Port": 5432,
      "MaintenanceDB": "Open_Landscapes",
      "Username": "postgres",
      "Password": "admin",
      "SSLMode": "prefer",
      "Timeout": 10,
      "UseSSHTunnel": 0,
      "TunnelPort": "22",
      "TunnelAuthentication": 0
    }
  }
}
EOF

# Copy servers.json to pgAdmin container
docker cp /tmp/servers.json shareland-pgadmin:"$USER_DIR/servers.json"

# Set correct permissions
docker exec shareland-pgadmin chown pgadmin:pgadmin "$USER_DIR/servers.json"
docker exec shareland-pgadmin chmod 600 "$USER_DIR/servers.json"

echo "Server configuration completed!"
echo "Refresh pgAdmin page (http://localhost:5050) to see the configured server."

rm /tmp/servers.json








