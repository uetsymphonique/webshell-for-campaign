#!/bin/bash

# Define the IP address
ipAddr=$1

# If ipAddr is empty, find the first connected IPv4 interface's IP
if [ -z "$ipAddr" ]; then
    # Get the first IPv4 address from a connected interface
    ipAddr=$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -n1)
    if [ -z "$ipAddr" ]; then
        echo "No connected IPv4 interface found."
        exit 1
    fi
    echo "[i] Using IP $ipAddr"
fi

# List of ports to check
ports=(53 80 443 22 25 123 587 21 20 3306 3000 5432 9418 3128 8080 8443 8888 514 9200 27017 1812 9001 8000 6033)

# Check each port
for port in "${ports[@]}"; do
    if timeout 0.2 bash -c "echo > /dev/tcp/$ipAddr/$port" 2>/dev/null; then
        echo "Port $port is open on $ipAddr"
    fi
done
