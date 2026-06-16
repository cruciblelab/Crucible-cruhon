#!/usr/bin/env bash
#
# Support Tawk — One-Command Auto Installer
# ------------------------------------------
# Usage (as root on your server):
#
#   bash <(curl -fsSL https://raw.githubusercontent.com/cruciblelab/supporttawk/main/install.sh)
#
# Or if you already cloned the repo:
#
#   cd /opt/support-tawk && sudo bash install.sh
#
# Optional env vars (to skip prompts):
#   DOMAIN=chat.yoursite.com   ADMIN_PASS=StrongPass   SITE_NAME="My Company"
#   EMAIL=you@yoursite.com     LANG_CHOICE=en
#   ADMIN_IP=1.2.3.4,5.6.7.8  SKIP_PROXY=yes          APP_PORT=8000
#
set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
  R=$'\e[31m'; G=$'\e[32m'; Y=$'\e[33m'; B=$'\e[34m'; C=$'\e[36m'; W=$'\e[1m'; X=$'\e[0m'
else
  R=""; G=""; Y=""; B=""; C=""; W=""; X=""
fi
ok()   { echo "${G}✓${X} $*"; }
info() { echo "${C}➜${X} $*"; }
warn() { echo "${Y}!${X} $*"; }
err()  { echo "${R}✗ $*${X}" >&2; }
step() { echo; echo "${W}${B}── $* ${X}"; }

trap 'err "Installation failed at line $LINENO. Check the output above."' ERR

# ── Settings ──────────────────────────────────────────────────────────────────
REPO_URL="https://github.com/cruciblelab/supporttawk.git"
APP_DIR="/opt/support-tawk"
SERVICE="support-tawk"

DOMAIN="${DOMAIN:-}"
ADMIN_PASS="${ADMIN_PASS:-}"
SITE_NAME="${SITE_NAME:-}"
EMAIL="${EMAIL:-}"
LANG_CHOICE="${LANG_CHOICE:-}"
ADMIN_IP="${ADMIN_IP:-}"        # optional: comma-separated IPs to restrict /admin
SKIP_PROXY="${SKIP_PROXY:-}"    # set to "yes" to skip web server setup entirely
APP_PORT="${APP_PORT:-8000}"    # port the app listens on

GENERATED_PASS=0

# ── 0. Pre-checks ─────────────────────────────────────────────────────────────
step "Pre-checks"
if [ "$(id -u)" -ne 0 ]; then
  err "This script must be run as root. Try:  sudo bash install.sh"
  exit 1
fi
if ! grep -qi "ubuntu\|debian" /etc/os-release 2>/dev/null; then
  warn "This script is written for Ubuntu/Debian. Other distributions may have issues."
fi
ok "Running as root"

# ── 1. Collect information ────────────────────────────────────────────────────
step "Setup information"
if [ -z "$LANG_CHOICE" ]; then
  echo "  Choose admin panel language:"
  echo "  1) English (default)"
  echo "  2) Turkish (Türkçe)"
  read -rp "  Selection [1/2]: " _lang_sel
  case "$_lang_sel" in
    2) LANG_CHOICE="tr" ;;
    *) LANG_CHOICE="en" ;;
  esac
fi
ok "Language: $LANG_CHOICE"

if [ -z "$DOMAIN" ]; then
  read -rp "Your domain (e.g. chat.yoursite.com) — leave blank to skip: " DOMAIN
fi
if [ -z "$SITE_NAME" ]; then
  read -rp "Company / site name [Support Desk]: " SITE_NAME
  SITE_NAME="${SITE_NAME:-Support Desk}"
fi
if [ -z "$ADMIN_PASS" ]; then
  read -rsp "Admin password (leave blank to auto-generate): " ADMIN_PASS; echo
fi
if [ -z "$ADMIN_PASS" ]; then
  ADMIN_PASS="$(head -c 9 /dev/urandom | base64 | tr -d '/+=' | head -c 12)"
  GENERATED_PASS=1
fi
if [ -n "$DOMAIN" ] && [ -z "$EMAIL" ]; then
  read -rp "Email for SSL certificate (Let's Encrypt) — leave blank to skip: " EMAIL
fi
SECRET_KEY="$(head -c 48 /dev/urandom | base64 | tr -d '/+=' | head -c 48)"
DATA_ENCRYPTION_KEY="$(head -c 48 /dev/urandom | base64 | tr -d '/+=' | head -c 48)"
ok "Information collected"

# ── 2. System packages ────────────────────────────────────────────────────────
# NOTE: web server packages are installed later after detection (Step 7)
step "Installing system packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git libmagic1 ufw >/dev/null
ok "python3, git, and dependencies installed"

# ── 3. Download / update repo ─────────────────────────────────────────────────
step "Downloading application"
if [ -d "$APP_DIR/.git" ]; then
  info "Repository already exists, updating…"
  git -C "$APP_DIR" pull --ff-only || warn "git pull skipped (local changes may exist)"
elif [ -f "$(pwd)/server/main.py" ]; then
  info "Running from inside the repo, using existing files"
  APP_DIR="$(pwd)"
else
  git clone --depth 1 "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"
ok "Application ready: $APP_DIR"

# ── 4. Python environment ─────────────────────────────────────────────────────
step "Setting up Python environment"
python3 -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
ok "Dependencies installed"

# ── 5. Configuration: secrets → .env, non-secrets → config.yml ────────────────
step "Writing configuration"
PUBLIC_URL="${DOMAIN:+https://$DOMAIN}"; PUBLIC_URL="${PUBLIC_URL:-http://localhost:$APP_PORT}"

# Secrets live in .env (chmod 600), never in config.yml / version control.
# DATA_ENCRYPTION_KEY is kept separate from SECRET_KEY so the JWT key can be
# rotated without losing the ability to decrypt stored data.
if [ -f "$APP_DIR/.env" ]; then
  info ".env already exists — keeping existing secrets"
  # Reuse existing keys so we never re-encrypt data with a different key.
  # shellcheck disable=SC1091
  set -a; . "$APP_DIR/.env"; set +a
else
  cat > "$APP_DIR/.env" <<EOF
# Support Tawk secrets — keep this file private (chmod 600).
# These override config.yml. Do NOT commit this file.
SECRET_KEY=$SECRET_KEY
DATA_ENCRYPTION_KEY=$DATA_ENCRYPTION_KEY
ADMIN_PASSWORD=$ADMIN_PASS
# AI_API_KEY=sk-...
EOF
  ok ".env created with generated secrets"
fi
chmod 600 "$APP_DIR/.env"

# config.yml holds only non-secret settings.
python3 - "$SITE_NAME" "$PUBLIC_URL" "$LANG_CHOICE" <<'PY'
import re, sys
name, domain, lang = sys.argv[1:4]
with open("config.yml", encoding="utf-8") as f:
    c = f.read()
def repl(pattern, value):
    global c
    c = re.sub(pattern, value, c, count=1, flags=re.M)
repl(r'^(\s*name:\s*).*$',             r'\g<1>"%s"' % name)
repl(r'^(\s*domain:\s*).*$',           r'\g<1>"%s"' % domain)
repl(r'^(\s*language:\s*).*$',         r'\g<1>"%s"' % lang)
# Scrub secrets from config.yml — they now come from .env.
repl(r'^(\s*secret_key:\s*).*$',       r'\g<1>""  # set via .env (SECRET_KEY)')
repl(r'^(\s*default_password:\s*).*$', r'\g<1>""  # set via .env (ADMIN_PASSWORD)')
with open("config.yml", "w", encoding="utf-8") as f:
    f.write(c)
print("config.yml updated")
PY
ok "config.yml written (site name, language); secrets stored in .env"

# Encrypt any pre-existing plaintext data (idempotent; no-op on fresh installs).
step "Encrypting existing data at rest"
if [ -f "$APP_DIR/data/support.db" ]; then
  ( set -a; . "$APP_DIR/.env"; set +a; "$APP_DIR/venv/bin/python" migrate_encrypt.py ) || warn "Encryption migration skipped"
else
  ok "Fresh install — data is encrypted automatically as it is written"
fi

# ── 6. Systemd service ────────────────────────────────────────────────────────
step "Setting up auto-start service"
# Lock down data directory and DB file (defense-in-depth alongside encryption).
mkdir -p "$APP_DIR/data"
chmod 700 "$APP_DIR/data"
[ -f "$APP_DIR/data/support.db" ] && chmod 600 "$APP_DIR/data/support.db"

cat > "/etc/systemd/system/${SERVICE}.service" <<EOF
[Unit]
Description=Support Tawk Live Chat
After=network.target

[Service]
User=root
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/uvicorn server.main:app --host 127.0.0.1 --port $APP_PORT --loop uvloop --http httptools
Restart=always
RestartSec=5
# Hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable "$SERVICE" >/dev/null 2>&1
systemctl restart "$SERVICE"
sleep 2
if systemctl is-active --quiet "$SERVICE"; then
  ok "Service is running (auto-start enabled)"
else
  err "Service failed to start. Check logs:  journalctl -u $SERVICE -n 40"
  exit 1
fi

# ── 7. Web Server Detection + Configuration ───────────────────────────────────

# Detect which web server is active or installed
detect_webserver() {
  if systemctl is-active --quiet nginx 2>/dev/null; then echo "nginx"
  elif systemctl is-active --quiet apache2 2>/dev/null; then echo "apache2"
  elif systemctl is-active --quiet caddy 2>/dev/null; then echo "caddy"
  elif command -v nginx &>/dev/null; then echo "nginx"
  elif command -v apache2 &>/dev/null; then echo "apache2"
  elif command -v caddy &>/dev/null; then echo "caddy"
  else echo "none"
  fi
}

# Build nginx allow/deny lines for a given set of IPs
# Usage: build_nginx_ip_block "1.2.3.4,5.6.7.8" "        "
build_nginx_ip_block() {
  local ips="$1"
  local indent="${2:-        }"
  local block=""
  IFS=',' read -ra _ip_arr <<< "$ips"
  for _ip in "${_ip_arr[@]}"; do
    _ip="${_ip// /}"  # strip spaces
    [ -z "$_ip" ] && continue
    block+="${indent}allow ${_ip};"$'\n'
  done
  block+="${indent}deny all;"
  echo "$block"
}

# Build Apache Allow/Deny directives
build_apache_ip_block() {
  local ips="$1"
  local indent="${2:-        }"
  local block="${indent}Require ip"
  IFS=',' read -ra _ip_arr <<< "$ips"
  for _ip in "${_ip_arr[@]}"; do
    _ip="${_ip// /}"
    [ -z "$_ip" ] && continue
    block+=" ${_ip}"
  done
  echo "$block"
}

# Print a manual nginx snippet and exit the proxy-setup section
print_manual_snippet() {
  echo
  echo "${Y}Manual proxy configuration — copy and paste this into your web server:${X}"
  echo
  echo "─── nginx ────────────────────────────────────────────────────────────────────"
  cat <<SNIPPET
server {
    listen 80;
    server_name YOUR_DOMAIN;
    client_max_body_size 25M;

    location / {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 3600;
    }
}
SNIPPET
  echo "──────────────────────────────────────────────────────────────────────────────"
  echo
}

# Configure nginx as reverse proxy
configure_nginx() {
  local domain="$1"
  local port="$2"
  local admin_ip="$3"
  local cfg_site="/etc/nginx/sites-available/support-tawk"
  local cfg_http="/etc/nginx/conf.d/support-tawk.conf"

  if [ -f "$cfg_site" ]; then
    warn "Existing nginx config found at $cfg_site — updating it."
  fi

  # rate-limit zone must live in the http{} context
  # /etc/nginx/conf.d/ files are included inside http{} by Ubuntu's nginx.conf
  cat > "$cfg_http" <<'NGXHTTP'
# Support Tawk — rate-limit zone (http context)
limit_req_zone $binary_remote_addr zone=st_login:10m rate=10r/m;
NGXHTTP

  # Build the admin IP block for nginx (or empty string if no restriction)
  local admin_block=""
  if [ -n "$admin_ip" ]; then
    admin_block="$(build_nginx_ip_block "$admin_ip" "        ")"$'\n'
  fi

  # Proxy header snippet (reused in multiple locations)
  local proxy_headers
  proxy_headers='        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;'

  cat > "$cfg_site" <<NGXEOF
# Support Tawk — reverse proxy
# Generated by install.sh on $(date -u +"%Y-%m-%d %T UTC")

server {
    listen 80;
    server_name ${domain};
    client_max_body_size 25M;

    # Hide nginx version
    server_tokens off;

    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Cache static assets served by the app
    location /static/ {
        proxy_pass http://127.0.0.1:${port};
        proxy_set_header Host \$host;
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }

    # Rate-limit the login endpoint (zone defined in /etc/nginx/conf.d/support-tawk.conf)
    location /api/admin/login {
        limit_req zone=st_login burst=5 nodelay;
        proxy_pass http://127.0.0.1:${port};
${proxy_headers}
    }

    # Admin panel — optional IP restriction
    location /admin {
${admin_block}        proxy_pass http://127.0.0.1:${port};
${proxy_headers}
    }

    # Admin API — optional IP restriction
    location /api/admin {
${admin_block}        proxy_pass http://127.0.0.1:${port};
${proxy_headers}
    }

    # Everything else (WebSocket-capable)
    location / {
        proxy_pass http://127.0.0.1:${port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 3600;
    }
}
NGXEOF

  ln -sf "$cfg_site" "/etc/nginx/sites-enabled/support-tawk"

  if nginx -t >/dev/null 2>&1; then
    systemctl reload nginx
    ok "nginx configured ($domain → 127.0.0.1:$port)"
  else
    err "nginx configuration test failed. Review:  nginx -t"
    exit 1
  fi
}

# Configure apache2 as reverse proxy
configure_apache() {
  local domain="$1"
  local port="$2"
  local admin_ip="$3"
  local cfg="/etc/apache2/sites-available/support-tawk.conf"

  if [ -f "$cfg" ]; then
    warn "Existing apache2 config found at $cfg — updating it."
  fi

  # Enable required modules
  a2enmod proxy proxy_http rewrite headers >/dev/null 2>&1
  ok "Apache modules enabled: proxy proxy_http rewrite headers"

  local admin_block_text
  if [ -n "$admin_ip" ]; then
    admin_block_text="$(build_apache_ip_block "$admin_ip" "            ")"
  else
    admin_block_text="            Require all granted"
  fi

  cat > "$cfg" <<APACHEEOF
# Support Tawk — reverse proxy
# Generated by install.sh on $(date -u +"%Y-%m-%d %T UTC")

<VirtualHost *:80>
    ServerName ${domain}

    ProxyPreserveHost On
    ProxyPass        / http://127.0.0.1:${port}/
    ProxyPassReverse / http://127.0.0.1:${port}/

    RequestHeader set X-Forwarded-Proto "http"

    # Admin panel — optional IP restriction
    <Location /admin>
${admin_block_text}
    </Location>

    # Admin API — optional IP restriction
    <Location /api/admin>
${admin_block_text}
    </Location>
</VirtualHost>
APACHEEOF

  a2ensite support-tawk >/dev/null 2>&1
  systemctl reload apache2
  ok "apache2 configured ($domain → 127.0.0.1:$port)"
}

# Configure Caddy as reverse proxy
configure_caddy() {
  local domain="$1"
  local port="$2"
  local admin_ip="$3"

  # Caddy handles SSL automatically — no certbot needed
  local caddy_conf_dir="/etc/caddy/conf.d"
  local caddy_target
  if [ -d "$caddy_conf_dir" ]; then
    caddy_target="$caddy_conf_dir/support-tawk.conf"
  else
    caddy_target="/etc/caddy/Caddyfile"
    warn "No /etc/caddy/conf.d/ found — appending to $caddy_target"
  fi

  # Build admin IP restriction block for Caddy
  local ip_restriction=""
  if [ -n "$admin_ip" ]; then
    local allow_list=""
    IFS=',' read -ra _ip_arr <<< "$admin_ip"
    for _ip in "${_ip_arr[@]}"; do
      _ip="${_ip// /}"
      [ -z "$_ip" ] && continue
      allow_list+=" ${_ip}"
    done
    ip_restriction="
    # Admin IP restriction
    @admin_blocked {
        path /admin* /api/admin*
        not remote_ip${allow_list}
    }
    respond @admin_blocked 403"
  fi

  # Note: caddy-ratelimit is a third-party plugin; we include the config
  # but note it requires the plugin to be compiled in.
  local caddy_block
  caddy_block="
# Support Tawk — generated by install.sh on $(date -u +"%Y-%m-%d %T UTC")
${domain} {
    reverse_proxy 127.0.0.1:${port}
${ip_restriction}

    # Rate limiting on login requires the caddy-ratelimit plugin.
    # If not installed, remove this block.
    # rate_limit {
    #     zone st_login {
    #         match path /api/admin/login
    #         key {remote_host}
    #         events 10
    #         window 1m
    #     }
    # }
}
"

  if [ "$caddy_target" = "/etc/caddy/Caddyfile" ]; then
    echo "$caddy_block" >> "$caddy_target"
  else
    echo "$caddy_block" > "$caddy_target"
  fi

  systemctl reload caddy 2>/dev/null || systemctl restart caddy 2>/dev/null || true
  ok "Caddy configured ($domain → 127.0.0.1:$port) — SSL handled automatically by Caddy"
}

# Obtain SSL via certbot (nginx or apache only; caddy handles it natively)
get_ssl() {
  local webserver="$1"   # "nginx" or "apache2" / "apache"
  local domain="$2"
  local email="$3"

  if [ -z "$email" ]; then
    warn "No email provided — SSL skipped. Run later:"
    warn "  certbot --${webserver} -d ${domain}"
    return
  fi

  step "Obtaining SSL certificate (Let's Encrypt)"

  # certbot uses --apache flag for apache2
  local certbot_plugin="--${webserver}"
  [ "$webserver" = "apache2" ] && certbot_plugin="--apache"

  if certbot "$certbot_plugin" -d "$domain" \
      --non-interactive --agree-tos -m "$email" --redirect >/dev/null 2>&1; then
    ok "HTTPS enabled (certificate auto-renews)"
  else
    warn "SSL certificate failed. Is your domain's DNS pointing to this server?"
    warn "Run manually once DNS propagates:  certbot ${certbot_plugin} -d ${domain}"
  fi
}

# ── Main proxy-setup logic ────────────────────────────────────────────────────
step "Web server detection + configuration"

if [ "${SKIP_PROXY:-}" = "yes" ] || [ -z "$DOMAIN" ]; then
  if [ "${SKIP_PROXY:-}" = "yes" ]; then
    info "SKIP_PROXY=yes — skipping web server setup."
  else
    info "No domain provided — skipping web server setup."
  fi
  print_manual_snippet
else
  WEB_SERVER="$(detect_webserver)"
  info "Detected web server: ${WEB_SERVER:-none}"

  if [ "$WEB_SERVER" = "none" ]; then
    echo
    read -rp "  No web server found. Install nginx for automatic HTTPS setup? [Y/n]: " _install_nginx
    _install_nginx="${_install_nginx:-Y}"
    if [[ "$_install_nginx" =~ ^[Yy]$ ]]; then
      apt-get install -y -qq nginx certbot python3-certbot-nginx >/dev/null
      ok "nginx and certbot installed"
      WEB_SERVER="nginx"
      systemctl enable nginx >/dev/null 2>&1
      systemctl start nginx
    else
      warn "Skipping web server installation."
      print_manual_snippet
      WEB_SERVER=""
    fi
  fi

  case "$WEB_SERVER" in
    nginx)
      # Install certbot for nginx if not already present
      if ! command -v certbot &>/dev/null; then
        apt-get install -y -qq certbot python3-certbot-nginx >/dev/null
      fi
      configure_nginx "$DOMAIN" "$APP_PORT" "$ADMIN_IP"
      get_ssl "nginx" "$DOMAIN" "$EMAIL"
      ;;
    apache2|apache)
      if ! command -v certbot &>/dev/null; then
        apt-get install -y -qq certbot python3-certbot-apache >/dev/null
      fi
      configure_apache "$DOMAIN" "$APP_PORT" "$ADMIN_IP"
      get_ssl "apache2" "$DOMAIN" "$EMAIL"
      ;;
    caddy)
      # Caddy manages its own SSL — no certbot
      configure_caddy "$DOMAIN" "$APP_PORT" "$ADMIN_IP"
      ;;
    *)
      # User declined nginx install — snippet already printed above
      ;;
  esac
fi

# ── 8. Firewall ───────────────────────────────────────────────────────────────
step "Configuring firewall"
ufw allow 22 >/dev/null 2>&1 || true
ufw allow 80 >/dev/null 2>&1 || true
ufw allow 443 >/dev/null 2>&1 || true
yes | ufw enable >/dev/null 2>&1 || true
ok "Ports opened (22, 80, 443)"

# ── 9. Fail2ban — ban IPs that brute-force the admin login ─────────────────────
step "Configuring Fail2ban for login protection"
if apt-get install -y -qq fail2ban >/dev/null 2>&1; then
  # Filter: match the AUTH_FAIL lines written by the app's security log.
  cat > /etc/fail2ban/filter.d/support-tawk.conf <<'F2BFILTER'
[Definition]
failregex = ^.*AUTH_FAIL ip=<HOST> user=.*$
ignoreregex =
F2BFILTER

  # Jail: 5 failures within 10 min → ban for 1 hour.
  cat > /etc/fail2ban/jail.d/support-tawk.conf <<F2BJAIL
[support-tawk]
enabled  = true
filter   = support-tawk
logpath  = $APP_DIR/data/security.log
maxretry = 5
findtime = 600
bantime  = 3600
F2BJAIL

  # Ensure the log file exists so fail2ban can start watching it.
  mkdir -p "$APP_DIR/data"
  touch "$APP_DIR/data/security.log"
  systemctl enable fail2ban >/dev/null 2>&1 || true
  systemctl restart fail2ban >/dev/null 2>&1 || true
  if systemctl is-active --quiet fail2ban; then
    ok "Fail2ban active (5 failed logins in 10 min → 1 hour ban)"
  else
    warn "Fail2ban installed but not running. Check:  systemctl status fail2ban"
  fi
else
  warn "Fail2ban could not be installed — login brute-force protection skipped."
fi

# ── Summary ───────────────────────────────────────────────────────────────────
SERVER_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
PANEL_URL="${DOMAIN:+https://$DOMAIN/admin}"; PANEL_URL="${PANEL_URL:-http://$SERVER_IP:$APP_PORT/admin}"
echo
echo "${G}${W}════════════════════════════════════════════════${X}"
echo "${G}${W}   Support Tawk installed and running!${X}"
echo "${G}${W}════════════════════════════════════════════════${X}"
echo
echo "  ${W}Admin panel:${X}   $PANEL_URL"
echo "  ${W}Username:${X}      admin"
if [ "${GENERATED_PASS:-0}" = "1" ]; then
  echo "  ${W}Password:${X}      ${Y}$ADMIN_PASS${X}   ${R}← save this! auto-generated${X}"
else
  echo "  ${W}Password:${X}      (the password you set)"
fi
echo "  ${W}Language:${X}      $LANG_CHOICE"
if [ -n "$ADMIN_IP" ]; then
  echo "  ${W}Admin IP restriction:${X} $ADMIN_IP"
fi
echo
echo "  ${C}Security:${X}"
echo "    • Messages, names, emails & notes encrypted at rest (AES)"
echo "    • Secrets stored in $APP_DIR/.env (chmod 600)"
echo "    • Security headers + login rate limiting via reverse proxy"
echo "    • Fail2ban bans brute-force login attempts"
if [ -n "$ADMIN_IP" ]; then
  echo "    • Admin panel restricted to: $ADMIN_IP"
fi
echo
echo "  ${C}Useful commands:${X}"
echo "    Status:     systemctl status $SERVICE"
echo "    Logs:       journalctl -u $SERVICE -f"
echo "    Restart:    systemctl restart $SERVICE"
echo "    Update:     cd $APP_DIR && git pull && systemctl restart $SERVICE"
echo "    Banned IPs: fail2ban-client status support-tawk"
echo
if [ -z "$DOMAIN" ]; then
  warn "No domain provided. Access the panel via IP for now:"
  warn "  http://$SERVER_IP:$APP_PORT/admin   (re-run with a domain for HTTPS)"
fi
echo
