#!/bin/bash
# Generate self-signed certificates for Traefik
# This script runs inside the Traefik container to generate HTTPS certificates
# Suitable for hospital LAN deployments without internet access

set -e

CERT_DIR="/data/certs"
CERT_FILE="$CERT_DIR/scribe.crt"
KEY_FILE="$CERT_DIR/scribe.key"

# Create directory if it doesn't exist
mkdir -p "$CERT_DIR"

# Only generate if certificates don't exist
if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo "Generating self-signed certificate..."
    
    # Generate 2048-bit RSA key and self-signed certificate
    # Valid for 365 days, suitable for internal hospital use
    openssl req -x509 \
        -newkey rsa:2048 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -days 365 \
        -nodes \
        -subj "/C=FR/ST=Local/L=Hospital/O=Healthcare/CN=scribe"
    
    echo "Certificate generated: $CERT_FILE"
    echo "Key generated: $KEY_FILE"
    
    # Set proper permissions
    chmod 600 "$KEY_FILE"
    chmod 644 "$CERT_FILE"
    
    echo "Self-signed certificate ready for HTTPS"
else
    echo "Certificate already exists, skipping generation"
fi

exit 0
