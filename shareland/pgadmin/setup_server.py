#!/usr/bin/env python3
"""
Script to automatically configure PostgreSQL server in pgAdmin
"""
import time
import requests
import json

# Wait for pgAdmin to be ready
time.sleep(10)

# pgAdmin configuration
PGADMIN_URL = "http://localhost:5050"
PGADMIN_EMAIL = "admin@shareland.it"
PGADMIN_PASSWORD = "admin"

# PostgreSQL server configuration
SERVER_CONFIG = {
    "name": "ShareLand PostgreSQL",
    "host": "db",
    "port": 5432,
    "maintenance_db": "Open_Landscapes",
    "username": "postgres",
    "password": "admin",
    "ssl_mode": "prefer"
}

try:
    # Login to pgAdmin
    login_url = f"{PGADMIN_URL}/misc/login"
    session = requests.Session()
    
    login_data = {
        "email": PGADMIN_EMAIL,
        "password": PGADMIN_PASSWORD
    }
    
    response = session.post(login_url, json=login_data)
    
    if response.status_code == 200:
        print("Logged in to pgAdmin successfully")
        
        # Get CSRF token from cookies or headers
        csrf_token = session.cookies.get('csrf_token', '')
        
        # Add server
        server_url = f"{PGADMIN_URL}/browser/server/object/"
        headers = {
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_token
        }
        
        server_data = {
            "name": SERVER_CONFIG["name"],
            "host": SERVER_CONFIG["host"],
            "port": SERVER_CONFIG["port"],
            "maintenance_db": SERVER_CONFIG["maintenance_db"],
            "username": SERVER_CONFIG["username"],
            "password": SERVER_CONFIG["password"],
            "ssl_mode": SERVER_CONFIG["ssl_mode"]
        }
        
        response = session.post(server_url, json=server_data, headers=headers)
        
        if response.status_code in [200, 201]:
            print("Server added successfully!")
        else:
            print(f"Failed to add server: {response.status_code} - {response.text}")
    else:
        print(f"Login failed: {response.status_code}")
        
except Exception as e:
    print(f"Error configuring pgAdmin: {e}")











