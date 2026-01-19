#!/bin/bash
# Wait for pgAdmin to be ready
sleep 5

# Create servers.json in the pgAdmin storage directory
PGADMIN_DIR="/var/lib/pgadmin/storage/admin_shareland.it"
mkdir -p "$PGADMIN_DIR"

# Create servers.json with PostgreSQL server configuration
cat > "$PGADMIN_DIR/servers.json" << 'EOF'
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

chown -R pgadmin:pgadmin "$PGADMIN_DIR"
chmod 600 "$PGADMIN_DIR/servers.json"

echo "pgAdmin server configuration completed"










