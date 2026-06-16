#!/usr/bin/env bash
#
# Support Tawk — Tek Komutluk Otomatik Kurulum
# ---------------------------------------------
# Kullanım (sunucuda root olarak):
#
#   bash <(curl -fsSL https://raw.githubusercontent.com/cruciblelab/crucible-cruhon/main/support-tawk/install.sh)
#
# ya da depo zaten indirildiyse:
#
#   cd /opt/crucible-cruhon/support-tawk && sudo bash install.sh
#
# İsteğe bağlı ortam değişkenleri (sormadan kurmak için):
#   DOMAIN=chat.siteniz.com  ADMIN_PASS=GucluSifre  SITE_NAME="Şirketim"  EMAIL=ben@siteniz.com
#
set -euo pipefail

# ── Renkler ───────────────────────────────────────────────────────────────────
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

trap 'err "Kurulum bir hatayla durdu (satır $LINENO). Yukarıdaki mesaja bakın."' ERR

# ── Ayarlar ───────────────────────────────────────────────────────────────────
REPO_URL="https://github.com/cruciblelab/crucible-cruhon.git"
APP_DIR="/opt/crucible-cruhon"
SUB_DIR="$APP_DIR/support-tawk"
SERVICE="support-tawk"
PORT="8000"

DOMAIN="${DOMAIN:-}"
ADMIN_PASS="${ADMIN_PASS:-}"
SITE_NAME="${SITE_NAME:-}"
EMAIL="${EMAIL:-}"

# ── 0. Ön kontroller ──────────────────────────────────────────────────────────
step "Ön kontroller"
if [ "$(id -u)" -ne 0 ]; then
  err "Bu betik root yetkisiyle çalışmalı. Şunu deneyin:  sudo bash install.sh"
  exit 1
fi
if ! grep -qi "ubuntu\|debian" /etc/os-release 2>/dev/null; then
  warn "Bu betik Ubuntu/Debian için yazıldı. Farklı dağıtımda sorun çıkabilir."
fi
ok "root yetkisi var"

# ── 1. Bilgileri topla ────────────────────────────────────────────────────────
step "Kurulum bilgileri"
if [ -z "$DOMAIN" ]; then
  read -rp "Alan adınız (örn: chat.siteniz.com) — yoksa boş bırakın: " DOMAIN
fi
if [ -z "$SITE_NAME" ]; then
  read -rp "Şirket/Site adı [Destek Hattı]: " SITE_NAME
  SITE_NAME="${SITE_NAME:-Destek Hattı}"
fi
if [ -z "$ADMIN_PASS" ]; then
  read -rsp "Admin şifresi belirleyin (boş bırakırsanız otomatik üretilir): " ADMIN_PASS; echo
fi
if [ -z "$ADMIN_PASS" ]; then
  ADMIN_PASS="$(head -c 9 /dev/urandom | base64 | tr -d '/+=' | head -c 12)"
  GENERATED_PASS=1
fi
if [ -n "$DOMAIN" ] && [ -z "$EMAIL" ]; then
  read -rp "SSL sertifikası için e-posta (Let's Encrypt) — atlamak için boş bırakın: " EMAIL
fi
SECRET_KEY="$(head -c 48 /dev/urandom | base64 | tr -d '/+=' | head -c 48)"
ok "Bilgiler alındı"

# ── 2. Sistem paketleri ───────────────────────────────────────────────────────
step "Sistem paketleri kuruluyor (1-3 dk)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git nginx \
  libmagic1 certbot python3-certbot-nginx ufw >/dev/null
ok "python3, git, nginx, certbot ve bağımlılıklar kuruldu"

# ── 3. Depoyu indir / güncelle ────────────────────────────────────────────────
step "Uygulama indiriliyor"
if [ -d "$SUB_DIR/.git" ] || [ -d "$APP_DIR/.git" ]; then
  info "Depo zaten var, güncelleniyor…"
  git -C "$APP_DIR" pull --ff-only || warn "git pull atlandı (yerel değişiklikler olabilir)"
elif [ -f "$(pwd)/server/main.py" ]; then
  info "Betik depo içinden çalıştırıldı, mevcut dosyalar kullanılıyor"
  APP_DIR="$(cd .. && pwd)"; SUB_DIR="$(pwd)"
else
  git clone --depth 1 "$REPO_URL" "$APP_DIR"
fi
cd "$SUB_DIR"
ok "Uygulama hazır: $SUB_DIR"

# ── 4. Python ortamı ──────────────────────────────────────────────────────────
step "Python ortamı kuruluyor"
python3 -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
ok "Bağımlılıklar yüklendi"

# ── 5. config.yml ayarla ──────────────────────────────────────────────────────
step "Yapılandırma yazılıyor"
[ -f config.yml ] || cp config.example.yml config.yml 2>/dev/null || true
# Mevcut config.yml üzerinde anahtarları güncelle
PUBLIC_URL="${DOMAIN:+https://$DOMAIN}"; PUBLIC_URL="${PUBLIC_URL:-http://localhost:$PORT}"
python3 - "$SITE_NAME" "$PUBLIC_URL" "$SECRET_KEY" "$ADMIN_PASS" <<'PY'
import re, sys
name, domain, secret, passwd = sys.argv[1:5]
with open("config.yml", encoding="utf-8") as f:
    c = f.read()
def repl(pattern, value):
    global c
    c = re.sub(pattern, value, c, count=1, flags=re.M)
repl(r'^(\s*name:\s*).*$',            r'\g<1>"%s"' % name)
repl(r'^(\s*domain:\s*).*$',          r'\g<1>"%s"' % domain)
repl(r'^(\s*secret_key:\s*).*$',      r'\g<1>"%s"' % secret)
repl(r'^(\s*default_password:\s*).*$',r'\g<1>"%s"' % passwd)
with open("config.yml", "w", encoding="utf-8") as f:
    f.write(c)
print("config.yml güncellendi")
PY
ok "config.yml yazıldı (gizli anahtar + admin şifresi)"

# ── 6. Systemd servisi ────────────────────────────────────────────────────────
step "Otomatik başlatma servisi"
cat > "/etc/systemd/system/${SERVICE}.service" <<EOF
[Unit]
Description=Support Tawk Live Chat
After=network.target

[Service]
User=root
WorkingDirectory=$SUB_DIR
ExecStart=$SUB_DIR/venv/bin/uvicorn server.main:app --host 127.0.0.1 --port $PORT
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
  ok "Servis çalışıyor (otomatik başlatma açık)"
else
  err "Servis başlamadı. Log için:  journalctl -u $SERVICE -n 40"
  exit 1
fi

# ── 7. Nginx ──────────────────────────────────────────────────────────────────
if [ -n "$DOMAIN" ]; then
  step "Nginx ters proxy ayarlanıyor"
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
    ok "Nginx ayarlandı ($DOMAIN → 127.0.0.1:$PORT)"
  else
    err "Nginx yapılandırması hatalı. Kontrol:  nginx -t"
    exit 1
  fi

  # ── 8. SSL ─────────────────────────────────────────────────────────────────
  if [ -n "$EMAIL" ]; then
    step "SSL sertifikası alınıyor"
    if certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" --redirect >/dev/null 2>&1; then
      ok "HTTPS etkin (sertifika otomatik yenilenecek)"
    else
      warn "SSL alınamadı. Alan adının DNS'i bu sunucuya bakıyor mu? Sonra şunu çalıştırın:"
      warn "  certbot --nginx -d $DOMAIN"
    fi
  else
    warn "E-posta verilmedi, SSL atlandı. Sonra:  certbot --nginx -d $DOMAIN"
  fi
fi

# ── 9. Güvenlik duvarı ────────────────────────────────────────────────────────
step "Güvenlik duvarı"
ufw allow 22 >/dev/null 2>&1 || true
ufw allow 80 >/dev/null 2>&1 || true
ufw allow 443 >/dev/null 2>&1 || true
yes | ufw enable >/dev/null 2>&1 || true
ok "Portlar açıldı (22, 80, 443)"

# ── Özet ──────────────────────────────────────────────────────────────────────
SERVER_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
PANEL_URL="${DOMAIN:+https://$DOMAIN/admin}"; PANEL_URL="${PANEL_URL:-http://$SERVER_IP:$PORT/admin}"
echo
echo "${G}${W}════════════════════════════════════════════════${X}"
echo "${G}${W}  🎉  Support Tawk kuruldu ve çalışıyor!${X}"
echo "${G}${W}════════════════════════════════════════════════${X}"
echo
echo "  ${W}Admin paneli:${X}  $PANEL_URL"
echo "  ${W}Kullanıcı:${X}     admin"
if [ "${GENERATED_PASS:-0}" = "1" ]; then
  echo "  ${W}Şifre:${X}        ${Y}$ADMIN_PASS${X}   ${R}(bunu kaydedin! otomatik üretildi)${X}"
else
  echo "  ${W}Şifre:${X}        (belirlediğiniz şifre)"
fi
echo
echo "  ${C}Faydalı komutlar:${X}"
echo "    Durum:      systemctl status $SERVICE"
echo "    Loglar:     journalctl -u $SERVICE -f"
echo "    Yeniden:    systemctl restart $SERVICE"
echo "    Güncelle:   cd $APP_DIR && git pull && systemctl restart $SERVICE"
echo
if [ -z "$DOMAIN" ]; then
  warn "Alan adı vermediniz. Panele şu an IP üzerinden erişebilirsiniz:"
  warn "  http://$SERVER_IP:$PORT/admin   (HTTPS için alan adıyla tekrar çalıştırın)"
fi
echo
