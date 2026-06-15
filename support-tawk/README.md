# Support Tawk

Ücretsiz, self-hosted, her web teknolojisiyle çalışan canlı destek chat sistemi.

## Kurulum (3 adım)

### 1. config.yml'i düzenle
```yaml
site:
  name: "Şirketim"
admin:
  default_username: "admin"
  default_password: "guclu_sifre_yaz"
```

### 2. Başlat
```bash
docker compose up -d
```

### 3. Widgeti sitenize ekle (tek satır)
```html
<script src="https://sunucunuz.com/widget.js"></script>
```

PHP, HTML, Python Flask, Node.js — herhangi bir teknoloji çalışır.

---

## Admin Panel

`https://sunucunuz.com/admin` → config.yml'deki bilgilerle giriş yapın.

### Özellikler
- Tüm konuşmalar tek havuzda
- "Üstüme Al" ile konuşma devralma
- Gerçek zamanlı WebSocket mesajlaşma
- Hazır yanıtlar (`/selamla` gibi kısayollarla)
- Dosya / resim yükleme
- AI otomatik yanıt (OpenAI veya Anthropic)
- Temsilci hesabı yönetimi
- Tarayıcı bildirimleri

---

## AI Entegrasyonu

config.yml:
```yaml
ai:
  enabled: true
  provider: "openai"      # openai | anthropic
  api_key: "sk-..."
  auto_reply: true
```

---

## Docker'sız Kurulum

```bash
pip install -r requirements.txt
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
```

---

## Dosya Limitleri (config.yml)

```yaml
limits:
  max_file_size_mb: 10
  max_image_size_mb: 5
  allowed_file_types: [jpg, png, pdf, docx]
```
