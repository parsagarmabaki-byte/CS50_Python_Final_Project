# Deployment Options Summary

MarketWatch can be deployed on Ubuntu using **three different methods**. Choose the one that fits your needs.

---

## Quick Comparison

| Feature | Docker Compose | Manual Ubuntu Setup | Development |
|---------|---------------|---------------------|-------------|
| **Best for** | Production | Production | Local testing |
| **Setup time** | 5 minutes | 15 minutes | 2 minutes |
| **Commands to start** | `docker compose up -d` | Multiple systemctl commands | `npm run dev` + `uvicorn` |
| **Requirements** | Docker only | Python, Node.js, Nginx | Python, Node.js |
| **Isolation** | Full (containers) | None (bare metal) | None |
| **Portability** | High (any OS) | Ubuntu only | Local only |
| **Updates** | Easy (`docker compose pull`) | Manual | N/A |
| **Performance** | ~5% overhead | 100% native | N/A |

---

## Method 1: Docker Compose (Recommended)

**File:** `DOCKER_COMPOSE_DEPLOYMENT.md`

### When to Use
- ✅ You want **simplest deployment**
- ✅ You might deploy to **multiple servers**
- ✅ You want **easy updates and rollbacks**
- ✅ You prefer **container isolation**

### Quick Start
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh

# Configure and start
cp .env.docker .env
nano .env  # Set SERVER_IP
docker compose up -d --build
```

### Access
```
http://YOUR_SERVER_IP
```

---

## Method 2: Manual Ubuntu Setup

**File:** `UBUNTU_SERVER_CONFIG.md`

### When to Use
- ✅ You want **maximum performance**
- ✅ You need **full control** over components
- ✅ You can't use Docker (policy reasons)
- ✅ You want to **understand every layer**

### Quick Start
```bash
# Install dependencies
sudo apt install -y python3 python3-pip python3-venv nodejs nginx git

# Clone and configure
git clone <repo> /opt/marketwatch
cd /opt/marketwatch

# Set up backend (systemd service)
# Set up frontend (Nginx config)
# Start services
```

### Access
```
http://YOUR_SERVER_IP
```

---

## Method 3: Local Development

**For:** Testing on your Windows/Mac/Linux desktop

### Backend (Terminal 1)
```bash
cd c:\Python\CS50\final_project
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn final_project.web:app --reload
```

### Frontend (Terminal 2)
```bash
cd c:\Python\CS50\final_project\web-client
npm install
npm run dev
```

### Access
```
Frontend: http://localhost:5173
Backend:  http://localhost:8000
API Docs: http://localhost:8000/docs
```

---

## Detailed Comparison

### Installation Requirements

| Component | Docker Compose | Manual Ubuntu |
|-----------|---------------|---------------|
| Python | In container | Install on Ubuntu |
| Node.js | In container | Install on Ubuntu |
| Nginx | In container | Install on Ubuntu |
| Docker | Required | Not needed |
| Systemd | Not used | Required |

### Configuration Files

| File | Docker Compose | Manual Ubuntu |
|------|---------------|---------------|
| App config | `.env` | `/opt/marketwatch/.env` |
| Backend service | `docker-compose.yml` | `/etc/systemd/system/marketwatch.service` |
| Frontend server | `web-client/nginx.conf` | `/etc/nginx/sites-available/marketwatch` |
| CORS settings | In `web.py` (auto) | In `web.py` (manual) |

### Maintenance

| Task | Docker Compose | Manual Ubuntu |
|------|---------------|---------------|
| Start app | `docker compose up -d` | `sudo systemctl start marketwatch nginx` |
| Stop app | `docker compose down` | `sudo systemctl stop marketwatch nginx` |
| View logs | `docker compose logs -f` | `journalctl -u marketwatch -f` |
| Update app | `docker compose pull && up -d` | `git pull && pip install && rebuild` |
| Backup data | `docker volume inspect` | `tar -czf backup csv_files/` |

### Security

| Aspect | Docker Compose | Manual Ubuntu |
|--------|---------------|---------------|
| Isolation | Full container isolation | Shared system |
| User permissions | Container user | System user |
| Network | Isolated Docker network | System network |
| Attack surface | Smaller (minimal images) | Larger (full system) |

---

## Decision Tree

```
Do you want to deploy on Ubuntu server?
│
├─ Yes, and I want easiest setup → Docker Compose
│
├─ Yes, and I want maximum control → Manual Ubuntu Setup
│
└─ No, I want to test locally → Development Mode
```

---

## Migration Paths

### From Development to Docker

1. Build Docker images:
   ```bash
   docker compose build
   ```

2. Set your server IP in `.env`

3. Deploy:
   ```bash
   docker compose up -d
   ```

### From Manual to Docker

1. Backup your data:
   ```bash
   tar -czf csv_backup.tar.gz /opt/marketwatch/csv_files/
   ```

2. Stop manual services:
   ```bash
   sudo systemctl stop marketwatch nginx
   ```

3. Start Docker:
   ```bash
   docker compose up -d
   ```

4. Restore data:
   ```bash
   docker run --rm -v marketwatch_csv_data:/data -v $(pwd):/backup alpine \
     tar xzf /backup/csv_backup.tar.gz -C /data
   ```

---

## Common Scenarios

### Scenario 1: Home Server (Local Network)

**Recommended:** Docker Compose

```bash
# Set your local IP (e.g., 192.168.1.100)
echo "SERVER_IP=192.168.1.100" > .env
docker compose up -d

# Access from any device: http://192.168.1.100
```

### Scenario 2: VPS (Public Internet)

**Recommended:** Docker Compose + SSL

```bash
# Set your public IP
echo "SERVER_IP=203.0.113.50" > .env
docker compose up -d

# Add SSL (see UBUNTU_SERVER_CONFIG.md)
sudo apt install certbot
sudo certbot --nginx
```

### Scenario 3: Development Testing

**Recommended:** Development Mode

```bash
# Terminal 1 - Backend
uvicorn final_project.web:app --reload

# Terminal 2 - Frontend
npm run dev

# Access: http://localhost:5173
```

### Scenario 4: Multiple Environments

**Recommended:** Docker Compose with multiple files

```bash
# Development
docker compose -f docker-compose.dev.yml up -d

# Staging
docker compose -f docker-compose.staging.yml up -d

# Production
docker compose -f docker-compose.yml up -d
```

---

## Troubleshooting by Method

### Docker Compose Issues

```bash
# Check container status
docker compose ps

# View logs
docker compose logs -f

# Restart everything
docker compose down && docker compose up -d
```

### Manual Ubuntu Issues

```bash
# Check service status
sudo systemctl status marketwatch
sudo systemctl status nginx

# View logs
sudo journalctl -u marketwatch -f
sudo tail -f /var/log/nginx/error.log

# Restart services
sudo systemctl restart marketwatch
sudo systemctl restart nginx
```

### Development Issues

```bash
# Kill stuck processes
pkill -f uvicorn
pkill -f vite

# Clear cache
rm -rf web-client/node_modules
rm -rf web-client/dist
rm -rf __pycache__

# Reinstall
npm install
pip install -r requirements.txt
```

---

## Performance Benchmarks

| Metric | Docker Compose | Manual Ubuntu |
|--------|---------------|---------------|
| Startup time | ~30 seconds | ~10 seconds |
| Memory usage | ~300 MB | ~250 MB |
| CPU overhead | ~5% | 0% |
| Disk usage | ~1.5 GB | ~500 MB |
| Request latency | +1-2ms | Baseline |

**Note:** Performance difference is negligible for most applications.

---

## Cost Comparison

| Cost Factor | Docker Compose | Manual Ubuntu |
|-------------|---------------|---------------|
| Server cost | Same | Same |
| Setup time | 5 min | 15 min |
| Maintenance | Low | Medium |
| Learning curve | Low | Medium |
| Portability | High | Low |

---

## Summary Recommendations

| Your Situation | Recommended Method |
|----------------|-------------------|
| First-time deployment | Docker Compose |
| Small business server | Docker Compose |
| Enterprise with Docker policy | Docker Compose |
| Enterprise without Docker | Manual Ubuntu |
| Performance-critical | Manual Ubuntu |
| Learning/Testing | Development Mode |
| Multiple environments | Docker Compose |
| CI/CD pipeline | Docker Compose |

---

## Get Started

1. **Choose your method** (see table above)
2. **Follow the guide:**
   - Docker: `DOCKER_COMPOSE_DEPLOYMENT.md`
   - Manual: `UBUNTU_SERVER_CONFIG.md`
   - Dev: `README.md` (root directory)
3. **Deploy and test**
4. **Monitor and maintain**

For questions or issues, check the troubleshooting section in your chosen guide.
