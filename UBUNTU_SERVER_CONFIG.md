# Ubuntu Server Deployment Configuration (IP-Based)

Complete configuration files and commands to deploy MarketWatch on a remote Ubuntu server using **hardcoded IP addresses** (no domain name required).

## Quick Start

1. Find your server IP: `hostname -I` or check with your hosting provider
2. Replace `YOUR_SERVER_IP` in this guide with your actual IP (e.g., `192.168.1.100`)
3. Follow the steps below

---

## Server Requirements

- Ubuntu 20.04 LTS or newer
- At least 1GB RAM
- 5GB free disk space
- **Static IP address** (recommended) or note your dynamic IP
- SSH access

---

## Step 1: Server Preparation

### Find your server IP address

```bash
# Show all IP addresses
hostname -I

# Or use ip command
ip addr show | grep inet
```

Note your IP address (e.g., `192.168.1.100` or your public IP).

### SSH into your server

```bash
ssh user@YOUR_SERVER_IP
# Example: ssh user@192.168.1.100
```

### Update system packages

```bash
sudo apt update && sudo apt upgrade -y
```

### Install required software

```bash
# Python and dependencies
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Node.js (v18.x)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Nginx web server
sudo apt install -y nginx

# Git (to clone your repo)
sudo apt install -y git

# Net-tools (to verify IP)
sudo apt install -y net-tools
```

---

## Step 2: Clone Your Project

```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git /opt/marketwatch
cd /opt/marketwatch

# Or upload via SCP from your local machine:
# scp -r c:\Python\CS50\final_project user@YOUR_SERVER_IP:/opt/marketwatch
```

---

## Step 3: Backend Configuration

### Create system user for the app

```bash
sudo useradd -r -s /bin/false marketwatch
```

### Set up Python virtual environment

```bash
cd /opt/marketwatch
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

### Create environment configuration file

```bash
sudo nano /opt/marketwatch/.env
```

Add (replace `YOUR_SERVER_IP` with your actual IP):

```env
# Backend Configuration
HOST=0.0.0.0
PORT=8000

# Your server IP for CORS
SERVER_IP=YOUR_SERVER_IP

# Data directory
DATA_DIR=/opt/marketwatch/csv_files
```

### Update CORS in web.py for your IP

```bash
sudo nano /opt/marketwatch/final_project/web.py
```

Find the `allow_origins` list and add your server IP:

```python
allow_origins=[
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:5173",
    "http://YOUR_SERVER_IP:5173",      # Add your IP here
    "http://YOUR_SERVER_IP:8000",      # Add your IP here
]
```

### Create the systemd service file

```bash
sudo nano /etc/systemd/system/marketwatch.service
```

**Copy this configuration:**

```ini
[Unit]
Description=MarketWatch FastAPI Backend
After=network.target

[Service]
Type=exec
User=marketwatch
Group=www-data
WorkingDirectory=/opt/marketwatch
Environment="PATH=/opt/marketwatch/venv/bin"
ExecStart=/opt/marketwatch/venv/bin/uvicorn final_project.web:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=marketwatch

# Security hardening
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### Set proper permissions

```bash
sudo chown -R marketwatch:www-data /opt/marketwatch
sudo chmod -R 755 /opt/marketwatch
sudo mkdir -p /opt/marketwatch/csv_files
sudo chown marketwatch:www-data /opt/marketwatch/csv_files
```

### Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable marketwatch
sudo systemctl start marketwatch
sudo systemctl status marketwatch
```

### Check logs

```bash
sudo journalctl -u marketwatch -f
```

---

## Step 4: Frontend Configuration

### Build the frontend

```bash
cd /opt/marketwatch/web-client

# Create production .env file with your server IP
cat > .env.production << EOF
VITE_API_BASE_URL=http://YOUR_SERVER_IP:8000
EOF

# Replace YOUR_SERVER_IP with actual IP (example: 192.168.1.100)
# sed -i 's/YOUR_SERVER_IP/192.168.1.100/g' .env.production

# Install dependencies and build
npm install
npm run build
```

### Configure Nginx to serve the frontend (IP-based)

```bash
sudo nano /etc/nginx/sites-available/marketwatch
```

**Copy this Nginx configuration (IP-based, no domain):**

```nginx
server {
    listen 80;
    server_name YOUR_SERVER_IP;  # Replace with your IP

    # Serve React frontend
    location / {
        root /opt/marketwatch/web-client/dist;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Proxy API requests to FastAPI backend
    location / {
        # Check if it's an API request
        if ($request_uri ~ ^/(register|login|logout|me|health)) {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # CORS headers for IP-based access
            add_header Access-Control-Allow-Origin "http://YOUR_SERVER_IP:5173" always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
            add_header Access-Control-Allow-Credentials "true" always;
            
            if ($request_method = OPTIONS) {
                return 204;
            }
        }
    }

    # Health check endpoint (no auth required)
    location = /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        access_log off;
    }
}
```

**Important:** Replace `YOUR_SERVER_IP` with your actual IP address in the Nginx config.

### Enable the Nginx site

```bash
# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Enable marketwatch site
sudo ln -s /etc/nginx/sites-available/marketwatch /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## Step 5: Firewall Configuration (IP-Based)

```bash
# Enable UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (IMPORTANT - do this first!)
sudo ufw allow 22/tcp

# Allow HTTP (for Nginx)
sudo ufw allow 80/tcp

# Allow frontend dev server port (if running dev mode)
sudo ufw allow 5173/tcp

# Enable firewall
sudo ufw --force enable

# Check status
sudo ufw status
```

---

## Step 6: Verify Deployment (IP-Based)

### Check all services are running

```bash
# Backend service
sudo systemctl status marketwatch

# Nginx
sudo systemctl status nginx

# View backend logs
sudo journalctl -u marketwatch -n 50
```

### Get your server IP (for testing URLs)

```bash
# Local IP
hostname -I

# Public IP (from within server)
curl ifconfig.me
```

### Test endpoints (replace YOUR_SERVER_IP)

```bash
# Health check
curl http://YOUR_SERVER_IP/health

# Register a test user
curl -X POST http://YOUR_SERVER_IP/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"secret123","email":"test@example.com"}'

# Login
curl -X POST http://YOUR_SERVER_IP/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"secret123"}'
```

### Open browser

Visit: `http://YOUR_SERVER_IP`

Or from another computer on the same network: `http://192.168.1.100`

---

## Step 7: Access from Other Devices

### Local network access

If your server is on a local network (e.g., `192.168.x.x`):

1. Find server IP: `hostname -I`
2. From another device, open: `http://192.168.x.x`

### Public internet access

If your server has a public IP:

1. Find public IP: `curl ifconfig.me`
2. Open from anywhere: `http://YOUR_PUBLIC_IP`

**Note:** For public access, ensure your router/firewall allows port 80.

### Port forwarding (for home servers)

If behind a router:

1. Log into your router admin panel
2. Forward port 80 to your server's local IP
3. Use your public IP from outside your network

---

## Step 8: Maintenance Commands

### View logs

```bash
# Backend logs
sudo journalctl -u marketwatch -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Restart services

```bash
sudo systemctl restart marketwatch
sudo systemctl restart nginx
```

### Update the application

```bash
cd /opt/marketwatch

# Pull latest changes
sudo -u marketwatch git pull

# Install any new dependencies
source venv/bin/activate
pip install -r requirements.txt
deactivate

# Rebuild frontend if changed
cd web-client
npm install
npm run build

# Restart services
sudo systemctl restart marketwatch
sudo systemctl restart nginx
```

### Backup data

```bash
# Create backup
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
sudo tar -czf /opt/backups/marketwatch_$BACKUP_DATE.tar.gz /opt/marketwatch/csv_files/

# List backups
ls -lh /opt/backups/

# Restore from backup (example)
# sudo tar -xzf /opt/backups/marketwatch_20260314.tar.gz -C /
```

### Database cleanup (optional)

Create a cleanup script:

```bash
sudo nano /opt/marketwatch/scripts/cleanup_old_data.sh
```

```bash
#!/bin/bash
# Delete accounts not logged in for 90 days
# (Implement your cleanup logic here)
echo "Cleanup completed at $(date)"
```

Schedule with cron:

```bash
sudo crontab -e
```

Add:

```cron
# Run cleanup every Sunday at 3 AM
0 3 * * 0 /opt/marketwatch/scripts/cleanup_old_data.sh
```

---

## Quick Reference

| Service | Command | Status Check |
|---------|---------|--------------|
| Backend | `sudo systemctl start marketwatch` | `sudo systemctl status marketwatch` |
| Frontend | Served by Nginx | `sudo systemctl status nginx` |
| SSL Renew | `sudo certbot renew` | Auto-renews |

| File | Path |
|------|------|
| Backend code | `/opt/marketwatch/final_project/` |
| Frontend build | `/opt/marketwatch/web-client/dist/` |
| Data (CSV) | `/opt/marketwatch/csv_files/` |
| Backend logs | `journalctl -u marketwatch` |
| Nginx logs | `/var/log/nginx/` |
| Systemd service | `/etc/systemd/system/marketwatch.service` |
| Nginx config | `/etc/nginx/sites-available/marketwatch` |

---

## Troubleshooting

### Backend won't start

```bash
# Check service status
sudo systemctl status marketwatch

# View detailed logs
sudo journalctl -u marketwatch -n 100 --no-pager

# Test manually
cd /opt/marketwatch
source venv/bin/activate
uvicorn final_project.web:app --host 0.0.0.0 --port 8000
```

### Nginx errors

```bash
# Test configuration
sudo nginx -t

# View error log
sudo tail -50 /var/log/nginx/error.log

# Reload Nginx
sudo systemctl reload nginx
```

### SSL certificate issues

```bash
# Check certificate expiry
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal
```

### Permission denied errors

```bash
# Fix ownership
sudo chown -R marketwatch:www-data /opt/marketwatch

# Fix permissions
sudo chmod -R 755 /opt/marketwatch
sudo chmod -R 775 /opt/marketwatch/csv_files
```

### Port already in use

```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill the process (replace PID)
sudo kill -9 PID
```

---

## Security Checklist

- [ ] SSH key authentication enabled (disable password login)
- [ ] Firewall configured (UFW)
- [ ] SSL certificate installed and auto-renewing
- [ ] Backend running as non-root user
- [ ] Regular system updates scheduled
- [ ] Backups configured and tested
- [ ] Failed2ban installed (optional, for SSH protection)

```bash
# Install fail2ban (recommended)
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## Contact & Support

For issues, check:
- Application logs: `sudo journalctl -u marketwatch -f`
- Nginx logs: `sudo tail -f /var/log/nginx/error.log`
- FastAPI docs: `https://your_domain.com/docs`
