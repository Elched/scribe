# ✅ LAN Deployment Verification Checklist

Use this checklist to verify that SCRIBE is properly configured for LAN access.

---

## Pre-Deployment

### Configuration Files

- [ ] **docker-compose.yml updated**
  - Traefik ports: `0.0.0.0:80:80`, `0.0.0.0:443:443`
  - SCRIBE_HOST using environment variable: `${SCRIBE_HOST:localhost}`
  - CORS_ORIGINS environment variable added
  - File location: `c:\Users\SALACH\Documents\AzureDevOps\SOC4HEALTH\scribe\docker-compose.yml`

- [ ] **traefik/traefik.yml updated**
  - Entry point addresses: `0.0.0.0:80`, `0.0.0.0:443`
  - Provider configuration includes file-based routing
  - File location: `c:\Users\SALACH\Documents\AzureDevOps\SOC4HEALTH\scribe\traefik\traefik.yml`

- [ ] **traefik/dynamic.yml updated**
  - Router rule: `HostRegexp('.*')` (accepts any host)
  - Two routers defined: secure (websecure) and http (web)
  - File location: `c:\Users\SALACH\Documents\AzureDevOps\SOC4HEALTH\scribe\traefik\dynamic.yml`

- [ ] **.env file created**
  - Copy from `.env.example` or `.env.lan.example`
  - SCRIBE_HOST set to server IP or hostname
  - CORS_ORIGINS includes all client addresses
  - SCRIBE_SECRET and ADMIN_PASSWORD changed (not defaults)
  - File location: `c:\Users\SALACH\Documents\AzureDevOps\SOC4HEALTH\scribe\.env`

### Documentation Files

- [ ] **README.md updated**
  - New section: "🌐 Local Network (LAN) Access"
  - Instructions for finding server IP
  - CORS configuration example
  - Location: In Quick Start section after Docker Compose

- [ ] **.env.example created**
  - Simple configuration template
  - File location: `c:\Users\SALACH\Documents\AzureDevOps\SOC4HEALTH\scribe\.env.example`

- [ ] **.env.lan.example created**
  - Detailed LAN configuration template
  - Deployment instructions
  - Security notes
  - File location: `c:\Users\SALACH\Documents\AzureDevOps\SOC4HEALTH\scribe\.env.lan.example`

- [ ] **DEPLOYMENT_LAN.md created**
  - Complete deployment guide
  - Network setup steps
  - Troubleshooting section
  - Security checklist
  - File location: `c:\Users\SALACH\Documents\AzureDevOps\SOC4HEALTH\scribe\DEPLOYMENT_LAN.md`

- [ ] **LAN_UPDATE_SUMMARY.md created**
  - Summary of all changes
  - How it works explanation
  - Configuration options
  - File location: `c:\Users\SALACH\Documents\AzureDevOps\SOC4HEALTH\scribe\LAN_UPDATE_SUMMARY.md`

- [ ] **BEFORE_AFTER_COMPARISON.md created**
  - Detailed before/after comparison
  - Technical changes explained
  - User experience scenarios
  - File location: `c:\Users\SALACH\Documents\AzureDevOps\SOC4HEALTH\scribe\BEFORE_AFTER_COMPARISON.md`

---

## Deployment Preparation

### Environment Setup

- [ ] **Find server IP address**
  - Run: `ipconfig /all`
  - Note the IPv4 Address (e.g., 192.168.1.50)
  - Verify it's on the same subnet as client computers

- [ ] **Verify network connectivity**
  - From server: `ping 192.168.1.50` (should respond)
  - From client: `ping 192.168.1.50` (should respond)

- [ ] **Check firewall rules**
  - Port 80 (HTTP) is open or allowed
  - Port 443 (HTTPS) is open or allowed
  - Port 8000 (if direct access needed) is open

- [ ] **.env file permissions**
  - .env file is readable by Docker daemon
  - Not world-readable (contains secrets)
  - Location: Same directory as docker-compose.yml

### Docker Preparation

- [ ] **Docker daemon running**
  - Windows: Docker Desktop is open
  - Linux: `systemctl status docker` shows active
  - Test: `docker ps` returns container list

- [ ] **Docker Compose installed**
  - Run: `docker compose version`
  - Version should be 2.0 or higher

- [ ] **Latest images pulled**
  - Run: `docker compose pull`
  - Traefik v3.0 image downloaded
  - SCRIBE image updated

---

## Deployment Execution

### Pre-Flight Checks

- [ ] **Syntax validation**
  - Run: `docker compose config --quiet`
  - No output = valid syntax
  - If errors: Fix and re-run

- [ ] **Required files exist**
  - docker-compose.yml ✓
  - traefik/traefik.yml ✓
  - traefik/dynamic.yml ✓
  - .env file ✓

- [ ] **No naming conflicts**
  - `docker ps -a` shows no existing scribe containers (or they're stopped)
  - No port 80/443 conflicts

### Starting Containers

- [ ] **Stop existing containers (if any)**
  - Run: `docker compose down`
  - Wait for complete shutdown

- [ ] **Start new containers**
  - Run: `docker compose up -d`
  - Wait 10-15 seconds for services to start

- [ ] **Verify all containers started**
  - Run: `docker compose ps`
  - Expected output:
    ```
    scribe-traefik    Up (healthy)
    scribe            Up (healthy)
    scribe-collecteur Up
    ```

- [ ] **Check container health**
  - All STATUS columns show "Up"
  - No "Exited" or "Unhealthy" status

### Service Validation

- [ ] **Review logs for errors**
  - Run: `docker compose logs traefik | tail -20`
  - Run: `docker compose logs scribe | tail -20`
  - Look for ERROR or FAIL messages
  - Expected: "Listening on 0.0.0.0:80" in traefik logs

- [ ] **Verify Traefik listening**
  - Run: `docker compose logs traefik | grep -i "listening"`
  - Should show port 80, 443, 8080

- [ ] **Verify Scribe started**
  - Run: `docker compose logs scribe | grep -i "application startup"`
  - Should show "Uvicorn running on" message

---

## Testing — Localhost

### From Server Computer

- [ ] **Access via localhost**
  - URL: `http://localhost`
  - Expected: SCRIBE login page loads
  - If HTTPS used, accept certificate warning

- [ ] **Access via localhost:8000 (direct)**
  - URL: `http://localhost:8000`
  - Expected: SCRIBE login page loads
  - Should redirect to port 80/443

- [ ] **Access via loopback IP**
  - URL: `http://127.0.0.1`
  - Expected: SCRIBE login page loads

- [ ] **Login test**
  - Username: `dircrise`
  - Password: Value of ADMIN_PASSWORD in .env
  - Expected: Dashboard loads

---

## Testing — LAN (Remote Computer)

### From Remote Computer on Same Network

- [ ] **Verify network connectivity to server**
  - Run: `ping 192.168.1.50`
  - Expected: Ping replies (0% loss)

- [ ] **Test port connectivity**
  - Windows: `Test-NetConnection -ComputerName 192.168.1.50 -Port 80`
  - Expected: `TcpTestSucceeded: True`

- [ ] **Access via server IP**
  - URL: `http://192.168.1.50`
  - Expected: SCRIBE login page loads
  - Note: May take 10-15 seconds for first request

- [ ] **Access from multiple computers**
  - Test from Workstation 1: ✓ Works
  - Test from Workstation 2: ✓ Works
  - Test from Workstation 3: ✓ Works
  - Expected: All can access simultaneously

- [ ] **Check CORS in browser console**
  - Open Developer Tools (F12)
  - Go to Console tab
  - Expected: No CORS errors
  - If errors: Update CORS_ORIGINS in .env

- [ ] **Login from remote computer**
  - Username: `dircrise`
  - Password: Value of ADMIN_PASSWORD
  - Expected: Dashboard loads and functions normally

---

## Testing — Advanced

### HTTPS/TLS (if configured)

- [ ] **Access via HTTPS**
  - URL: `https://192.168.1.50`
  - Expected: Page loads (may show certificate warning for self-signed)
  - Production: Should show valid certificate

- [ ] **HTTP redirect to HTTPS**
  - URL: `http://192.168.1.50`
  - Expected: Redirects to `https://192.168.1.50`

### DNS Resolution (if hostname used)

- [ ] **DNS lookup works**
  - From server: `nslookup scribe.hospital.local`
  - From client: `nslookup scribe.hospital.local`
  - Expected: Resolves to server IP

- [ ] **Access via hostname**
  - URL: `http://scribe.hospital.local`
  - Expected: SCRIBE login page loads

- [ ] **Hostname in certificate (for HTTPS)**
  - URL: `https://scribe.hospital.local`
  - Expected: Certificate valid for hostname

### Multi-Client Simultaneous Access

- [ ] **Concurrent sessions**
  - 3+ computers access SCRIBE at same time
  - Each login with different account (if available)
  - Expected: No conflicts, all sessions persist

- [ ] **Load on server**
  - Run: `docker stats` on server
  - Watch CPU and memory usage
  - Expected: Normal operation under load

---

## Post-Deployment Verification

### Security Checks

- [ ] **Secrets are not in source control**
  - Run: `git status`
  - .env file should NOT appear (in .gitignore)
  - docker-compose.yml should show env vars, not secrets

- [ ] **Default passwords changed**
  - ADMIN_PASSWORD != "Scribe2026!"
  - SCRIBE_SECRET != "change-me-in-production"

- [ ] **CORS is restrictive**
  - CORS_ORIGINS does not contain "*"
  - Only includes necessary client addresses

### Operational Checks

- [ ] **Container restart behavior**
  - Docker machine reboots
  - Wait 30 seconds
  - Run: `docker compose ps`
  - Expected: All containers Up again (restart: unless-stopped)

- [ ] **Volume persistence**
  - Access SCRIBE and create a test incident
  - Run: `docker compose restart`
  - Expected: Test incident still exists (data persisted)

- [ ] **Log monitoring**
  - Run: `docker compose logs -f` in background terminal
  - Generate activity (login, create incident)
  - Expected: Logs show activity, no errors

### Documentation Checks

- [ ] **README.md is up-to-date**
  - Contains LAN access section
  - Accurate instructions for current setup

- [ ] **DEPLOYMENT_LAN.md is complete**
  - All troubleshooting steps documented
  - Security checklist provided

- [ ] **.env.example is helpful**
  - All variables documented
  - Comments explain each setting

---

## Rollback Procedure (if needed)

- [ ] **Stop containers**
  - Run: `docker compose down`

- [ ] **Restore previous configuration**
  - Use git to restore old docker-compose.yml
  - Use git to restore old traefik/traefik.yml
  - Use git to restore old traefik/dynamic.yml

- [ ] **Start with old configuration**
  - Run: `docker compose up -d`

- [ ] **Verify rollback**
  - Services should be running
  - Only localhost access available

---

## Sign-Off

| Item | Status | Notes |
|------|--------|-------|
| Configuration files updated | ✓ / ✗ | |
| Documentation created | ✓ / ✗ | |
| Docker syntax validated | ✓ / ✗ | |
| Localhost access verified | ✓ / ✗ | |
| LAN access verified | ✓ / ✗ | |
| Multiple clients tested | ✓ / ✗ | |
| Security checks passed | ✓ / ✗ | |
| Logs reviewed for errors | ✓ / ✗ | |
| Documentation reviewed | ✓ / ✗ | |

**Deployment Approved By:** __________________ **Date:** ______________

---

## Support & Next Steps

If issues occur:
1. Check DEPLOYMENT_LAN.md → Troubleshooting section
2. Review docker-compose logs: `docker compose logs -f`
3. Verify network connectivity: `ping` and `Test-NetConnection`
4. Check CORS_ORIGINS configuration
5. Restart containers: `docker compose restart`

For additional features:
1. Configure HTTPS/TLS with proper certificates
2. Set up custom DNS hostname
3. Upgrade to PostgreSQL for production
4. Enable monitoring and alerting
5. Configure VPN for external access

---

**SCRIBE LAN Deployment Complete!** 🎉
