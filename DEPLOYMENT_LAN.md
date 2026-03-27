# 🌐 SCRIBE LAN Deployment Guide

This guide explains how to deploy SCRIBE so it's accessible from multiple computers on your hospital network (LAN).

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Network Setup](#network-setup)
3. [Configuration](#configuration)
4. [Deployment](#deployment)
5. [Troubleshooting](#troubleshooting)
6. [Security Checklist](#security-checklist)

---

## Prerequisites

- Docker and Docker Compose installed on your server
- Windows, Linux, or macOS server on the hospital network
- Network connectivity between all computers
- Administrator access to configure firewall (if needed)

---

## Network Setup

### Step 1: Find Your Server's IP Address

**Windows:**
```powershell
ipconfig /all
```
Look for "IPv4 Address" under your active network adapter (e.g., `192.168.1.50`)

**Linux/macOS:**
```bash
ip addr show
# or
ifconfig
```

### Step 2: Note the IP Address

Example server IPs:
- Hospital LAN: `192.168.1.50` or `10.0.0.100`
- VPN/Remote: May need reverse proxy or VPN setup

### Step 3: Verify Network Connectivity

From a client computer, test if the server is reachable:

**Windows:**
```powershell
ping 192.168.1.50
```

**Linux/macOS:**
```bash
ping -c 4 192.168.1.50
```

If successful, you should see replies. If not, check:
- Firewall rules
- Network connectivity
- Server is powered on

---

## Configuration

### Option 1: Using `.env` File (Recommended)

1. **Create a `.env` file** in the scribe directory:

```bash
cp .env.example .env
```

2. **Edit the `.env` file** with your server details:

```bash
# Your server's IP address on the LAN
SCRIBE_HOST=192.168.1.50

# Allow access from any computer on the LAN
CORS_ORIGINS=http://192.168.1.50,http://192.168.1.50:80,https://192.168.1.50:443,http://localhost

# Security (CHANGE THESE!)
SCRIBE_SECRET=YourSecureRandomSecret32CharsOrMore
ADMIN_PASSWORD=YourSecureAdminPassword

# Other settings
SCRIBE_IA_PROVIDER=albert
LOG_LEVEL=info
```

3. **Important security notes:**
   - `SCRIBE_SECRET` signs JWT tokens — change this!
   - `ADMIN_PASSWORD` controls admin login — change this!
   - `.env` file contains secrets — never commit to git

### Option 2: Using Environment Variables

If you prefer not to use a `.env` file, set environment variables directly:

```powershell
$env:SCRIBE_HOST = "192.168.1.50"
$env:SCRIBE_SECRET = "your-secure-secret"
$env:ADMIN_PASSWORD = "your-admin-password"
$env:CORS_ORIGINS = "http://192.168.1.50,http://localhost"
```

---

## Deployment

### Step 1: Pull Latest Images

```bash
docker compose pull
```

### Step 2: Start Services

```bash
docker compose up -d
```

### Step 3: Verify Services Started

```bash
docker compose ps
```

Expected output:
```
NAME                  STATUS
scribe-traefik        Up (healthy)
scribe                Up (healthy)
scribe-collecteur     Up (healthy)
```

### Step 4: View Logs

```bash
docker compose logs -f
```

Wait for messages like: `"Uvicorn running on 0.0.0.0:8000"`

### Step 5: Test Access

From the **server computer** (localhost):
```
http://localhost
http://localhost:8000
```

From a **remote computer on the LAN:**
```
http://192.168.1.50
http://192.168.1.50:8000
```

Default login:
- **Username:** `dircrise`
- **Password:** Value of `ADMIN_PASSWORD` in `.env`

---

## Troubleshooting

### Issue: Cannot access from remote computer

**Check 1: Verify server IP**
```powershell
# From the server
ipconfig /all

# From remote computer, ping server
ping 192.168.1.50
```

**Check 2: Verify SCRIBE_HOST in .env**
```bash
# Should match your server's IP
SCRIBE_HOST=192.168.1.50
```

**Check 3: Check if ports are open**

From remote computer:
```powershell
Test-NetConnection -ComputerName 192.168.1.50 -Port 80 -InformationLevel Detailed
Test-NetConnection -ComputerName 192.168.1.50 -Port 443 -InformationLevel Detailed
```

Expected: `TcpTestSucceeded: True`

If fails: Check firewall rules

**Check 4: Review container logs**
```bash
docker compose logs traefik
docker compose logs scribe
```

Look for error messages or connectivity issues.

### Issue: CORS errors in browser console

**Solution:** Update `CORS_ORIGINS` in `.env` to include the client's URL:

```bash
# Add the client computer's address
CORS_ORIGINS=http://192.168.1.50,http://192.168.1.100,http://localhost
```

Then restart:
```bash
docker compose up -d
```

### Issue: "Connection refused" error

**Solution:** Check if containers are running:
```bash
docker compose ps
docker compose logs scribe
```

Restart if needed:
```bash
docker compose restart
```

### Issue: Firewall blocking connections

**Windows Firewall (from server):**
```powershell
# Check if port 80 is open
netsh advfirewall show allprofiles

# Open port 80 for inbound (if closed)
netsh advfirewall firewall add rule name="Allow HTTP" dir=in action=allow protocol=tcp localport=80
netsh advfirewall firewall add rule name="Allow HTTPS" dir=in action=allow protocol=tcp localport=443
```

**Linux (ufw):**
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## Security Checklist

Before deploying to production:

### Before Going Live

- [ ] Change `SCRIBE_SECRET` to a strong random value (32+ characters)
- [ ] Change `ADMIN_PASSWORD` to a strong password
- [ ] Generate `ADMIN_PASSWORD` securely: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] Test access from multiple client computers
- [ ] Verify firewall rules allow only necessary ports
- [ ] Use HTTPS/TLS with valid certificates (not self-signed)

### Network Security

- [ ] Use a firewall to restrict access to SCRIBE
- [ ] Consider VPN for remote access from outside hospital network
- [ ] Use strong passwords for all user accounts
- [ ] Enable audit logging (`LOG_LEVEL=info`)
- [ ] Regularly review access logs

### Database Security

- [ ] For production: Use PostgreSQL instead of SQLite
- [ ] Backup database regularly
- [ ] Set `DATABASE_URL` in `.env` if using PostgreSQL

### Container Security

- [ ] Run `docker compose pull` regularly for security updates
- [ ] Keep Docker daemon updated
- [ ] Use non-root user in containers (already configured)
- [ ] Set `read_only: true` where possible (already configured)

### Monitoring

- [ ] Monitor container health: `docker compose ps`
- [ ] Review logs regularly: `docker compose logs -f`
- [ ] Set up alerts for service failures
- [ ] Monitor disk usage: `docker system df`

---

## Advanced Scenarios

### Using a Custom Domain Name

If you have a DNS server on your network:

1. **Add DNS record:**
   ```
   scribe.hospital.local → 192.168.1.50
   ```

2. **Update `.env`:**
   ```bash
   SCRIBE_HOST=scribe.hospital.local
   CORS_ORIGINS=http://scribe.hospital.local,http://localhost
   ```

3. **Restart:**
   ```bash
   docker compose up -d
   ```

### Using HTTPS/TLS with Self-Signed Certificates

For development (not production):

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout traefik/server.key -out traefik/server.crt -days 365 -nodes

# Add to docker-compose.yml volumes:
# - ./traefik/server.crt:/etc/traefik/server.crt:ro
# - ./traefik/server.key:/etc/traefik/server.key:ro
```

**⚠️ Warning:** Browsers will show security warnings for self-signed certificates.

### Using PostgreSQL for Production

1. **Add PostgreSQL service to `docker-compose.yml`**
2. **Set in `.env`:**
   ```bash
   DATABASE_URL=postgresql://scribe_user:secure_password@db:5432/scribe
   ```

---

## Support

For issues or questions:
1. Check logs: `docker compose logs -f`
2. Review this guide
3. Open an issue on GitHub
4. Contact your hospital's IT support

---

**Made with ❤️ for healthcare crisis management**
