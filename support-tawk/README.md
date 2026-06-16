# Support Tawk

Self-hosted live chat widget for any website. Built with FastAPI + WebSockets — no external services required.

## Quick Install (Ubuntu 22.04)

```bash
sudo apt update && sudo apt install -y git && \
git clone https://github.com/cruciblelab/support-tawk.git /opt/support-tawk && \
sudo bash /opt/support-tawk/install.sh
```

The installer prompts for domain, company name, admin password and language (English / Turkish). Everything else — Python setup, systemd service, Nginx, SSL, firewall — is handled automatically.

**Silent install (no prompts):**
```bash
DOMAIN=chat.yoursite.com SITE_NAME="My Company" ADMIN_PASS="StrongPass" \
  EMAIL=you@yoursite.com LANG_CHOICE=en \
  sudo -E bash /opt/support-tawk/install.sh
```

## Manual / Local Setup

```bash
git clone https://github.com/cruciblelab/support-tawk.git
cd support-tawk
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Edit config.yml, then:
python3 -m uvicorn server.main:app --reload
```

Admin panel: http://localhost:8000/admin  
Default login: **admin** / **admin123**

## Embed the Widget

```html
<script src="https://chat.yoursite.com/widget.js"></script>
</body>
```

Works with any tech stack — plain HTML, PHP, React, Vue, etc.

## Features

- Live chat widget (vanilla JS, zero dependencies)
- Real-time WebSocket messaging
- Agent roles with granular permissions
- Department routing
- Bot flows (keyword-triggered auto-replies)
- Proactive chat bubbles
- File & image sharing
- Visitor info panel (browser, OS, location, page history)
- Canned replies with `/shortcuts`
- Conversation tagging and priority
- Work hour schedules per agent
- Webhooks / integrations
- CSV export & audit log
- AI assistant (OpenAI / Anthropic)
- **English and Turkish UI** (set in config, changeable in admin settings)

## Languages

`config.yml`:
```yaml
site:
  language: "en"   # en | tr
```

Change at any time in the admin panel under **Site Settings** — no restart needed.

## AI Integration

```yaml
ai:
  enabled: true
  provider: "openai"   # openai | anthropic
  api_key: "sk-..."
  auto_reply: true
```

## File Limits

```yaml
limits:
  max_file_size_mb: 10
  allowed_file_types: [jpg, png, pdf, docx, zip]
```

## Security

Defense in depth, configured automatically by the installer:

- **Encryption at rest** — chat messages, visitor names/emails, internal notes
  and ratings are AES-encrypted in the database (Fernet). Copying the SQLite
  file does not reveal conversation contents.
- **Secrets in `.env`** — `SECRET_KEY`, `DATA_ENCRYPTION_KEY` and the admin
  password live in `.env` (chmod 600), never in `config.yml` or git.
- **TLS everywhere** — HTTPS/WSS via Let's Encrypt; transit is encrypted end
  to end between the visitor's browser and the server.
- **Login hardening** — server-side password strength rules, login rate
  limiting at the proxy, and Fail2ban bans after repeated failures.
- **Security headers** — `nosniff`, `X-Frame-Options`, HSTS, Referrer-Policy
  from both the app and the reverse proxy.
- **Admin IP allowlist** — optionally restrict `/admin` to specific IPs
  (`ADMIN_IP=1.2.3.4,5.6.7.8`).

Existing installs: run `venv/bin/python migrate_encrypt.py` once to encrypt
data already in the database (safe to re-run).

## Performance

Tuned to run comfortably on a 1 GB VPS:

- SQLite in WAL mode with tuned pragmas (NORMAL sync, 64 MB cache, mmap)
- In-process settings cache for the high-traffic `/api/config` endpoint
- GZip compression on JSON/HTML/JS responses
- uvloop + httptools event loop
- Static assets cached at the proxy

Rough capacity on 1 GB RAM: a few thousand concurrent WebSocket chats and
thousands of HTTP requests per second.

## Stack

- **Backend:** Python 3.11+, FastAPI, Uvicorn (uvloop), Peewee ORM, SQLite
- **Frontend:** Vanilla JS (no framework)
- **Auth:** PyJWT + bcrypt
- **Encryption:** cryptography (Fernet / AES)
- **Deploy:** systemd + Nginx/Apache/Caddy + Let's Encrypt + Fail2ban

---

Built by [Crucible Lab](https://github.com/cruciblelab)
