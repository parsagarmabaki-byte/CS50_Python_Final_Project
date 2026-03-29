# Docker Compose Deployment Guide (Ubuntu + IP-Based)

Deploy MarketWatch on Ubuntu using Docker Compose with hardcoded IP addresses - no domain name required.

---

## Quick Start (3 Commands)

```bash
# 1. Copy environment file and edit with your IP
cp .env.docker .env
nano .env  # Change SERVER_IP to your Ubuntu server IP

# 2. Start everything
docker compose up -d --build

# 3. Open browser
# http://YOUR_SERVER_IP
```

---

## What is Docker Compose?

Docker Compose is a tool that:
- **Packages your app** in containers (backend + frontend)
- **Works on Ubuntu** (and any OS with Docker)
- **Simplifies deployment** - no need to install Python, Node.js, Nginx manually
- **Isolates dependencies** - nothing installed on your Ubuntu system

### Difference from Manual Ubuntu Setup

| Docker Compose | Manual Ubuntu Setup |
|----------------|---------------------|
| `docker compose up -d` | Install Python, Node.js, Nginx |
| Everything in containers | Everything on bare metal |
| Works on any OS | Ubuntu-specific |
| Easy to update | Manual updates |
| Isolated | Shares system resources |

---

## Step-by-Step for Ubuntu Server

### Step 1: Install Docker on Ubuntu

```bash
# One-line Docker installation
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (no sudo needed)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

### Step 2: Clone Your Project

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git /opt/marketwatch
cd /opt/marketwatch
```

### Step 3: Find Your Server IP

```bash
# Show all IP addresses
hostname -I

# Example output: 192.168.1.100 172.17.0.1
# Use the first one (your network IP)
```

### Step 4: Configure Your IP

```bash
# Copy the example environment file
cp .env.docker .env

# Edit with your server IP
nano .env
```

Change this line:
```env
SERVER_IP=192.168.1.100
```

To your actual IP from Step 3.

### Step 5: Start the Application

```bash
# Build and start all containers (takes 2-3 minutes first time)
docker compose up -d --build

# Check status (should show 2 containers running)
docker compose ps
```

### Step 6: Configure Firewall (if enabled)

```bash
# Allow HTTP traffic
sudo ufw allow 80/tcp

# Check firewall status
sudo ufw status
```

### Step 7: Access the Application

From any device on the same network:
```
http://YOUR_SERVER_IP
```

**Examples:**
- Local network: `http://192.168.1.100`
- Public IP: `http://203.0.113.50`

---

## Docker Compose Files Explained

### `docker-compose.yml` (Production)

```yaml
services:
  backend:     # FastAPI Python backend
    - Runs on port 8000 (internal)
    - Stores data in csv_data volume
  
  frontend:    # Nginx + React frontend
    - Accessible on port 80
    - Proxies API requests to backend
```

### `docker-compose.dev.yml` (Development)

```bash
# Start development mode with hot-reload
docker compose -f docker-compose.dev.yml up -d

# Access:
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## Common Commands

### Start/Stop

```bash
# Start (production)
docker compose up -d

# Stop
docker compose down

# Restart
docker compose restart

# Rebuild after code changes
docker compose up -d --build
```

### View Logs

```bash
# All logs
docker compose logs -f

# Backend only
docker compose logs -f backend

# Frontend only
docker compose logs -f frontend
```

### Access Containers

```bash
# Shell into backend container
docker compose exec backend bash

# Shell into frontend container
docker compose exec frontend sh

# List running containers
docker compose ps
```

### Data Management

```bash
# View CSV data volume
docker volume inspect marketwatch_csv_data

# Backup data
docker run --rm \
  -v marketwatch_csv_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/csv_backup.tar.gz /data

# Restore from backup
docker run --rm \
  -v marketwatch_csv_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/csv_backup.tar.gz -C /data
```

---

## Troubleshooting

### Container won't start

```bash
# Check what's wrong
docker compose ps
docker compose logs backend
docker compose logs frontend
```

### "Port already in use" error

```bash
# Find what's using port 80
sudo lsof -i :80

# Stop conflicting service (e.g., existing Nginx)
sudo systemctl stop nginx
sudo systemctl disable nginx
```

### CORS errors in browser

1. Check your IP in `.env`:
   ```bash
   cat .env
   ```

2. Update if wrong:
   ```bash
   nano .env  # Fix SERVER_IP
   ```

3. Rebuild frontend:
   ```bash
   docker compose up -d --build frontend
   ```

### Can't access from other devices

```bash
# Check firewall
sudo ufw status

# Allow port 80 if needed
sudo ufw allow 80/tcp

# Check if server is reachable
ping YOUR_SERVER_IP
```

### Backend unhealthy

```bash
# Check backend logs
docker compose logs backend

# Restart backend
docker compose restart backend

# Check health manually
docker compose exec backend python -c "import requests; print(requests.get('http://localhost:8000/health').json())"
```

---

## Update Application

```bash
# Pull latest code (if using git)
cd /opt/marketwatch
sudo git pull

# Rebuild and restart
docker compose up -d --build
```

---

## File Structure

```
/opt/marketwatch/
├── docker-compose.yml      # Production config
├── docker-compose.dev.yml  # Development config
├── .env.docker            # Environment template
├── .env                   # Your configuration (created from template)
├── Dockerfile             # Backend Docker image
├── final_project/         # Backend code
├── web-client/
│   ├── Dockerfile         # Frontend Docker image
│   ├── nginx.conf         # Nginx configuration
│   └── src/               # React source code
└── csv_files/             # Data (inside Docker volume)
```

---

## Environment Variables

### `.env` file (create from `.env.docker`)

```env
# Your Ubuntu server IP (REQUIRED)
SERVER_IP=192.168.1.100

# Frontend port (default: 80)
FRONTEND_PORT=80

# API URL (auto-generated from SERVER_IP)
VITE_API_BASE_URL=http://${SERVER_IP}:8000
```

---

## Production Checklist

- [ ] Set static IP address on Ubuntu server
- [ ] Configure `.env` with correct IP
- [ ] Enable firewall (UFW)
- [ ] Allow only port 80 (HTTP)
- [ ] Set up automatic Docker updates
- [ ] Configure log rotation
- [ ] Set up regular backups of CSV data
- [ ] Monitor disk space

---

## Quick Reference

| Task | Command |
|------|---------|
| Start app | `docker compose up -d` |
| Stop app | `docker compose down` |
| View logs | `docker compose logs -f` |
| Check status | `docker compose ps` |
| Restart | `docker compose restart` |
| Rebuild | `docker compose up -d --build` |
| Backup data | `docker run --rm -v marketwatch_csv_data:/data ...` |

### Ports

| Service | Port | Access |
|---------|------|--------|
| Frontend | 80 | `http://YOUR_SERVER_IP` |
| Backend | 8000 | Internal only |
| Dev Frontend | 5173 | `http://localhost:5173` (dev mode) |

---

## Next Steps

1. **Set up automatic updates:**
   ```bash
   # Install watchtower for auto-updates
   docker run -d \
     --name watchtower \
     -v /var/run/docker.sock:/var/run/docker.sock \
     containrrr/watchtower \
     --interval 86400
   ```

2. **Add HTTPS (optional):**
   - See `UBUNTU_SERVER_CONFIG.md` for SSL setup
   - Or use a reverse proxy like Traefik

3. **Monitor your server:**
   ```bash
   # Install Docker stats viewer
   docker run -d \
     --name dozzle \
     -p 8080:8080 \
     -v /var/run/docker.sock:/var/run/docker.sock \
     amir20/dozzle
   ```

4. **Schedule backups:**
   ```bash
   # Add to crontab
   sudo crontab -e
   
   # Daily backup at 3 AM
   0 3 * * * cd /opt/marketwatch && docker run --rm -v marketwatch_csv_data:/data -v /backups:/backup alpine tar czf /backup/csv_$(date +\%Y\%m\%d).tar.gz /data
   ```

---

## Support

For issues:
1. Check logs: `docker compose logs -f`
2. Verify IP configuration: `cat .env`
3. Test health endpoint: `curl http://localhost/health`
4. Review this guide's troubleshooting section
