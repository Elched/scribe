# 🌐 SCRIBE LAN Access — Visual Quick Reference Guide

## Network Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Hospital LAN (192.168.1.0/24)       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   Server: 192.168.1.50           Workstations          │
│   ┌──────────────────────┐        ┌────────────────┐   │
│   │                      │        │ Workstation 1  │   │
│   │ ┌─────────────────┐  │        │ 192.168.1.51   │   │
│   │ │ Traefik Proxy   │  │◄───────│ http://192...50│   │
│   │ │ 0.0.0.0:80/443  │  │        └────────────────┘   │
│   │ └────────┬────────┘  │                              │
│   │          │           │        ┌────────────────┐   │
│   │          ▼           │        │ Workstation 2  │   │
│   │ ┌─────────────────┐  │        │ 192.168.1.52   │   │
│   │ │ SCRIBE App :80  │  │◄───────│ http://192...50│   │
│   │ │ (8000 internal) │  │        └────────────────┘   │
│   │ └─────────────────┘  │                              │
│   │                      │        ┌────────────────┐   │
│   └──────────────────────┘        │ Admin PC       │   │
│                                   │ 192.168.1.53   │   │
│                                   │ http://192...50│   │
│                                   └────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘

✅ All computers can access http://192.168.1.50
✅ Traefik listens on 0.0.0.0:80 (all interfaces)
✅ Routing accepts any Host header (IP, hostname, FQDN)
```

---

## Configuration at a Glance

```bash
# === .env File (Place next to docker-compose.yml) ===

# Network: Set to your server's IP address
SCRIBE_HOST=192.168.1.50

# CORS: List all client computers or use IP range
CORS_ORIGINS=http://192.168.1.50,http://192.168.1.51,http://192.168.1.52,http://localhost

# Security: CHANGE THESE!
SCRIBE_SECRET=ReplaceWithSecureRandomValue_32CharsOrMore
ADMIN_PASSWORD=ChangeThisSecurePassword

# Optional: AI & Database settings
SCRIBE_IA_PROVIDER=albert
# DATABASE_URL=postgresql://user:password@db:5432/scribe
```

---

## Deployment in 4 Steps

```powershell
# STEP 1: Find server IP
ipconfig /all
# ↓ Look for: IPv4 Address (e.g., 192.168.1.50)

# STEP 2: Create .env file
cp .env.example .env

# STEP 3: Edit .env with your server IP and passwords
# (Use Notepad or your favorite editor)

# STEP 4: Deploy
docker compose pull
docker compose up -d

# DONE! Access from remote computer:
# http://192.168.1.50
```

---

## Access URLs

| Location | URL | Status |
|----------|-----|--------|
| From Server | `http://localhost` | ✅ Works |
| From Server | `http://127.0.0.1` | ✅ Works |
| From Server | `http://192.168.1.50` | ✅ Works |
| From Workstation 1 | `http://192.168.1.50` | ✅ Works |
| From Workstation 2 | `http://192.168.1.50` | ✅ Works |
| From Workstation 3 | `http://192.168.1.50` | ✅ Works |
| From Outside Network | `http://192.168.1.50` | ❌ Blocked (use VPN) |

---

## Troubleshooting Flow

```
🔴 Can't access from remote computer?

  ↓
  
1. Check network connectivity
   ping 192.168.1.50 (from remote computer)
   ↓ No reply?
   └─→ Network/firewall issue → Check network cable, firewall rules
   
  ↓ Ping works?
  
2. Check .env file
   cat .env | grep SCRIBE_HOST
   ↓ Wrong IP?
   └─→ Update SCRIBE_HOST to correct IP
   
  ↓ Correct?
  
3. Check container status
   docker compose ps
   ↓ Not "Up"?
   └─→ Check logs: docker compose logs traefik
   
  ↓ Up?
  
4. Check port 80
   Test-NetConnection -ComputerName 192.168.1.50 -Port 80
   ↓ Failed?
   └─→ Firewall blocking → Open port 80/443
   
  ↓ Succeeded?
  
5. Try again
   http://192.168.1.50 in browser
   
  ✅ Works now!
```

---

## Key Configuration Files

### docker-compose.yml
```yaml
# Traefik listens on ALL network interfaces
ports:
  - "0.0.0.0:80:80"       ← HTTP on all interfaces
  - "0.0.0.0:443:443"     ← HTTPS on all interfaces

# Scribe routes accept SCRIBE_HOST from .env
labels:
  - "traefik.http.routers.scribe.rule=Host(`${SCRIBE_HOST:localhost}`)"
  - "traefik.http.routers.scribe.entrypoints=websecure,web"

# CORS configured per deployment
environment:
  - CORS_ORIGINS=${CORS_ORIGINS:-http://localhost,http://localhost:8000}
```

### traefik/traefik.yml
```yaml
# Entry points bind to all interfaces
entryPoints:
  web:
    address: "0.0.0.0:80"      ← All interfaces, port 80
  websecure:
    address: "0.0.0.0:443"     ← All interfaces, port 443
```

### traefik/dynamic.yml
```yaml
# Routing accepts any hostname or IP
routers:
  scribe-router-http:
    rule: "HostRegexp(`.*`)"   ← Accepts ANY Host header
    entryPoints:
      - web
```

---

## Security Checklist

Before deploying to production, verify:

```
☐ SCRIBE_SECRET changed (not "change-me-in-production")
☐ ADMIN_PASSWORD changed (strong password)
☐ CORS_ORIGINS includes only necessary IPs
☐ .env file is in .gitignore (secrets not in git)
☐ Firewall allows only ports 80/443 (not 8000/8080)
☐ .env file permissions are restrictive (not world-readable)
☐ Database backup strategy in place
☐ HTTPS/TLS configured with valid certificates (not self-signed)
☐ Users created with strong passwords (not using admin account)
☐ Access logs reviewed for security
```

---

## Performance Tips

```
✅ Use PostgreSQL instead of SQLite for production
✅ Run docker compose logs -f for monitoring
✅ Check docker stats for resource usage
✅ Set LOG_LEVEL=warning in production (reduce log volume)
✅ Backup database regularly
✅ Keep Docker daemon updated
✅ Monitor disk space for /data volume
✅ Use health checks (already configured)
```

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| **Connection refused** | Port/firewall blocked | Open port 80/443 in firewall |
| **CORS errors** | CORS_ORIGINS incomplete | Add client IP to CORS_ORIGINS |
| **No HTTPS** | TLS not configured | Set valid certificates in Traefik |
| **Slow login** | DNS resolution | Configure local DNS or use IP |
| **Can't access from VPN** | Network routing | Use reverse proxy + VPN |
| **Database full** | SQLite not maintained | Switch to PostgreSQL, prune old data |
| **Memory leak** | Container running out of memory | Increase Docker memory limit, check logs |

---

## File Locations

```
scribe/
├── .env ← YOU CREATE THIS (copy from .env.example)
├── .env.example ← Template file
├── .env.lan.example ← Detailed LAN template
├── docker-compose.yml ← Updated for LAN
├── DEPLOYMENT_LAN.md ← Full deployment guide
├── DEPLOYMENT_VERIFICATION_CHECKLIST.md ← Validation checklist
├── BEFORE_AFTER_COMPARISON.md ← Technical details
├── LAN_UPDATE_SUMMARY.md ← Change summary
├── FILE_MANIFEST.md ← File documentation
├── README.md ← Main documentation
├── traefik/
│  ├── traefik.yml ← Updated for LAN
│  └── dynamic.yml ← Updated routing rules
└── docker-compose.yml
```

---

## Quick Reference Commands

```bash
# Check server IP
ipconfig /all

# Test network connectivity
ping 192.168.1.50

# Test port accessibility
Test-NetConnection -ComputerName 192.168.1.50 -Port 80

# Start containers
docker compose up -d

# View status
docker compose ps

# View logs
docker compose logs -f

# Stop containers
docker compose down

# Restart containers
docker compose restart

# Check resource usage
docker stats

# View configuration
docker compose config
```

---

## Network Ports

| Port | Service | Purpose | Access |
|------|---------|---------|--------|
| **80** | Traefik HTTP | Web entry point | Public |
| **443** | Traefik HTTPS | Secure entry point | Public |
| **8000** | SCRIBE | Internal API | Internal (via Traefik) |
| **8080** | Traefik Dashboard | Admin interface | Local only (restrict) |

---

## Docker Networking

```
┌─────────────────────────────────────┐
│ Host Network Interface (0.0.0.0)    │
├─────────────────────────────────────┤
│                                     │
│ :80   → Docker Traefik :80          │
│ :443  → Docker Traefik :443         │
│ :8080 → Docker Traefik :8080        │
│                                     │
├─────────────────────────────────────┤
│ Docker Internal Network             │
├─────────────────────────────────────┤
│                                     │
│ Traefik → Scribe:8000               │
│ (internal routing)                  │
│                                     │
└─────────────────────────────────────┘

External (192.168.1.50:80) → Host Port 80 → Traefik 
Traefik routes to SCRIBE via internal network (8000)
```

---

## Success Indicators

✅ **Server:**
- `docker compose ps` shows all containers "Up (healthy)"
- `docker compose logs traefik` shows "Listening on 0.0.0.0:80"
- `http://localhost` loads SCRIBE login page

✅ **Remote Computer:**
- `ping 192.168.1.50` shows replies (0% packet loss)
- `Test-NetConnection -ComputerName 192.168.1.50 -Port 80` shows TcpTestSucceeded: True
- `http://192.168.1.50` loads SCRIBE login page in browser
- Login works with `dircrise` username and ADMIN_PASSWORD

---

## Next Steps After Deployment

1. **Create user accounts** → Don't use admin account for daily work
2. **Enable monitoring** → Set up alerts for container health
3. **Backup strategy** → Database backups, disaster recovery plan
4. **HTTPS/TLS** → Get valid certificates (not self-signed)
5. **DNS setup** → Register `scribe.hospital.local` (optional)
6. **PostgreSQL** → Upgrade from SQLite for production
7. **Reverse proxy** → Set up for external/VPN access (optional)
8. **Audit logging** → Review and archive logs regularly

---

**SCRIBE is now ready for your hospital network! 🏥**

Login at: `http://192.168.1.50`  
Username: `dircrise`  
Password: Check your `.env` file (ADMIN_PASSWORD)
