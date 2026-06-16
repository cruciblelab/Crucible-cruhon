#!/usr/bin/env bash
#
# Support Tawk — One-Command Auto Installer
# ------------------------------------------
# Usage (as root on your server):
#
#   bash <(curl -fsSL https://raw.githubusercontent.com/cruciblelab/support-tawk/main/install.sh)
#
# Or if you already cloned the repo:
#
#   cd /opt/support-tawk && sudo bash install.sh
#
# Optional env vars (to skip prompts):
#   DOMAIN=chat.yoursite.com  ADMIN_PASS=StrongPass  SITE_NAME="My Company"
#   EMAIL=you@yoursite.com    LANG_CHOICE=en
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
REPO_URL="https://github.com/cruciblelab/support-tawk.git"
APP_DIR="/opt/support-tawk"
SERVICE="support-tawk"
PORT="8000"

DOMAIN="${DOMAIN:-}"
ADMIN_PASS="${ADMIN_PASS:-}"
SITE_NAME="${SITE_NAME:-}"
EMAIL="${EMAIL:-}"
LANG_CHOICE="${LANG_CHOICE:-}"

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
ok "Information collected"

# ── 2. System packages ────────────────────────────────────────────────────────
step "Installing system packages (1-3 min)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git nginx \
  libmagic1 certbot python3-certbot-nginx ufw >/dev/null
ok "python3, git, nginx, certbot and dependencies installed"

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

# ── 5. Configure config.yml ───────────────────────────────────────────────────
step "Writing configuration"
PUBLIC_URL="${DOMAIN:+https://$DOMAIN}"; PUBLIC_URL="${PUBLIC_URL:-http://localhost:$PORT}"
python3 - "$SITE_NAME" "$PUBLIC_URL" "$SECRET_KEY" "$ADMIN_PASS" "$LANG_CHOICE" <<'PY'
import re, sys
name, domain, secret, passwd, lang = sys.argv[1:6]
with open("config.yml", encoding="utf-8") as f:
    c = f.read()
def repl(pattern, value):
    global c
    c = re.sub(pattern, value, c, count=1, flags=re.M)
repl(r'^(\s*name:\s*).*$',             r'\g<1>"%s"' % name)
repl(r'^(\s*domain:\s*).*$',           r'\g<1>"%s"' % domain)
repl(r'^(\s*secret_key:\s*).*$',       r'\g<1>"%s"' % secret)
repl(r'^(\s*default_password:\s*).*$', r'\g<1>"%s"' % passwd)
repl(r'^(\s*language:\s*).*$',         r'\g<1>"%s"' % lang)
with open("config.yml", "w", encoding="utf-8") as f:
    f.write(c)
print("config.yml updated")
PY
ok "config.yml written (secret key, admin password, language)"

# ── 6. Systemd service ────────────────────────────────────────────────────────
step "Setting up auto-start service"
cat > "/etc/systemd/system/${SERVICE}.service" <<EOF
[Unit]
Description=Support Tawk Live Chat
After=network.target

[Service]
User=root
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/uvicorn server.main:app --host 127.0.0.1 --port $PORT
Restart=always
RestartSec=5

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

# ── 7. Nginx ──────────────────────────────────────────────────────────────────
if [ -n "$DOMAIN" ]; then
  step "Configuring Nginx reverse proxy"
  cat > "/etc/nginx/sites-available/${SERVICE}" <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:$PORT;
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
EOF
  ln -sf "/etc/nginx/sites-available/${SERVICE}" "/etc/nginx/sites-enabled/${SERVICE}"
  rm -f /etc/nginx/sites-enabled/default
  if nginx -t >/dev/null 2>&1; then
    systemctl reload nginx
    ok "Nginx configured ($DOMAIN → 127.0.0.1:$PORT)"
  else
    err "Nginx configuration error. Check:  nginx -t"
    exit 1
  fi

  # ── 8. SSL ─────────────────────────────────────────────────────────────────
  if [ -n "$EMAIL" ]; then
    step "Obtaining SSL certificate"
    if certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" --redirect >/dev/null 2>&1; then
      ok "HTTPS enabled (certificate auto-renews)"
    else
      warn "SSL failed. Is your domain's DNS pointing to this server? Run manually:"
      warn "  certbot --nginx -d $DOMAIN"
    fi
  else
    warn "No email provided, SSL skipped. Run later:  certbot --nginx -d $DOMAIN"
  fi
fi

# ── 9. Firewall ───────────────────────────────────────────────────────────────
step "Configuring firewall"
ufw allow 22 >/dev/null 2>&1 || true
ufw allow 80 >/dev/null 2>&1 || true
ufw allow 443 >/dev/null 2>&1 || true
yes | ufw enable >/dev/null 2>&1 || true
ok "Ports opened (22, 80, 443)"

# ── Summary ───────────────────────────────────────────────────────────────────
SERVER_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
PANEL_URL="${DOMAIN:+https://$DOMAIN/admin}"; PANEL_URL="${PANEL_URL:-http://$SERVER_IP:$PORT/admin}"
echo
echo "${G}${W}════════════════════════════════════════════════${X}"
echo "${G}${W}  🎉  Support Tawk installed and running!${X}"
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
echo
echo "  ${C}Useful commands:${X}"
echo "    Status:     systemctl status $SERVICE"
echo "    Logs:       journalctl -u $SERVICE -f"
echo "    Restart:    systemctl restart $SERVICE"
echo "    Update:     cd $APP_DIR && git pull && systemctl restart $SERVICE"
echo
if [ -z "$DOMAIN" ]; then
  warn "No domain provided. Access the panel via IP for now:"
  warn "  http://$SERVER_IP:$PORT/admin   (re-run with a domain for HTTPS)"
fi
echo
