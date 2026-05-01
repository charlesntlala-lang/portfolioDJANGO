# Production Deployment Guide

## Quick Start

### Local Development
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Production Deployment

#### 1. Environment Setup
```bash
# Copy and configure environment
cp .env.example .env
nano .env  # Edit with your values
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Database Setup
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

#### 4. Run with Gunicorn
```bash
gunicorn config.wsgi:application -c gunicorn.conf.py
```

#### 5. Verify
```bash
# Check system
python manage.py check --deploy

# Run server
python manage.py runserver 0.0.0.0:8000
```

## Configuration

### Required Environment Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Secret key for cryptographic signing | `your-50-char-random-string` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts | `example.com,www.example.com` |
| `DJANGO_SECURE_SSL_REDIRECT` | Force HTTPS | `True` |
| `DJANGO_HSTS_SECONDS` | HSTS max-age in seconds | `31536000` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Trusted origins for CSRF | `https://example.com` |
| `DJANGO_SETTINGS_MODULE_SUFFIX` | Settings to load | `production` |

### Email Configuration
Required for lead notifications and subscriber emails:
- `EMAIL_HOST_USER`: Your SMTP email
- `EMAIL_HOST_PASSWORD`: App-specific password
- `DEFAULT_FROM_EMAIL`: Sender address

## Security Checklist

- [x] `DEBUG = False` in production
- [x] `SECRET_KEY` from environment variable
- [x] `ALLOWED_HOSTS` restricted
- [x] HTTPS enforced (`SECURE_SSL_REDIRECT`)
- [x] HSTS enabled with preload
- [x] Secure cookies (`CSRF_COOKIE_SECURE`, `SESSION_COOKIE_SECURE`)
- [x] XSS protection (`SECURE_BROWSER_XSS_FILTER`)
- [x] Content type sniffing prevention
- [x] Clickjacking protection (`X_FRAME_OPTIONS = 'DENY'`)
- [x] Static files served via WhiteNoise with compression
- [x] Error logging to file

## Platform-Specific Deployments

### Heroku
```bash
heroku create
heroku addons:create heroku-postgresql
heroku config:set DJANGO_SETTINGS_MODULE_SUFFIX=production
heroku config:set DJANGO_SECRET_KEY=$(openssl rand -base64 64)
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

### Railway
```bash
railway init
railway link
railway add postgresql
railway variables set DJANGO_SETTINGS_MODULE_SUFFIX=production
railway variables set DJANGO_SECRET_KEY=$(openssl rand -base64 64)
railway up
```

### DigitalOcean
```bash
# Install dependencies
sudo apt update
sudo apt install python3-pip nginx

# Create systemd service
sudo nano /etc/systemd/system/marketeci.service

[Unit]
Description=Marketeci Django App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/marketeci
EnvironmentFile=/path/to/marketeci/.env
ExecStart=/path/to/venv/bin/gunicorn config.wsgi:application -c gunicorn.conf.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable marketeci
sudo systemctl start marketeci
```

### AWS (EC2)
```bash
# SSH into instance
ssh -i key.pem ubuntu@your-ec2-ip

# Follow DigitalOcean steps above
# Configure security groups for ports 80, 443
# Set up Route53 for domain
# Use ACM for SSL certificates
```

## Nginx Configuration (Reverse Proxy)
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/marketeci/staticfiles/;
    }

    location /media/ {
        alias /path/to/marketeci/media/;
    }
}
```

## Monitoring
- Check logs: `tail -f logs/django_error.log`
- Gunicorn logs: stdout/stderr
- Django admin: `/admin-dashboard/`
- Analytics: `/admin-dashboard/`

## Backup
```bash
# Database
cp db.sqlite3 /backup/db-$(date +%Y%m%d).sqlite3

# Media files
tar -czf /backup/media-$(date +%Y%m%d).tar.gz media/

# Static files
tar -czf /backup/static-$(date +%Y%m%d).tar.gz staticfiles/
```

## Troubleshooting

### Static files not loading
```bash
python manage.py collectstatic --noinput --clear
```

### Permission denied on logs
```bash
chmod 755 logs/
touch logs/django_error.log
chmod 644 logs/django_error.log
```

### 502 Bad Gateway (Nginx + Gunicorn)
```bash
sudo systemctl status marketeci
sudo journalctl -u marketeci -n 50
```
