# Traefik Configuration for Scribe

This directory contains the Traefik reverse proxy configuration for Scribe.

## Files

- `traefik.yml`: Main Traefik configuration
- `dynamic.yml`: Dynamic routing configuration
- `certs/`: Directory for SSL certificates (currently empty - Traefik generates certificates automatically)

## Security Features

- HTTPS enforced on port 443
- Automatic self-signed certificate generation for localhost
- Docker socket access is read-only
- Containers run with minimal privileges (`no-new-privileges:true`)
- Root filesystem is read-only with tmpfs for temporary files
- Traefik dashboard is only accessible locally (development only)

## Usage

The Traefik configuration is automatically loaded by docker-compose.yml. Scribe is now accessible at:
- HTTPS: https://localhost
- HTTP redirects to HTTPS automatically

## Dashboard

For development purposes, the Traefik dashboard is available at:
- http://traefik.localhost:8080 (insecure, development only)

## Production Notes

Before deploying to production:
1. Remove the `api.insecure: true` from traefik.yml
2. Set up proper DNS and use a real certificate resolver
3. Restrict dashboard access or disable it
4. Use proper firewall rules