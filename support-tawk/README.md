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

## Stack

- **Backend:** Python 3.11+, FastAPI, Uvicorn, Peewee ORM, SQLite
- **Frontend:** Vanilla JS (no framework)
- **Auth:** PyJWT + bcrypt
- **Deploy:** systemd + Nginx + Let's Encrypt

---

Built by [Crucible Lab](https://github.com/cruciblelab)
