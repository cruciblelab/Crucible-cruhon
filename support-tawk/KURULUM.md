# Support Tawk — VDS/VPS Kurulum Rehberi

> **Seviye:** Başlangıç · Ubuntu 22.04 LTS · ~20 dakika

---

## Gereksinimler

| Ne | Minimum |
|----|---------|
| İşletim sistemi | Ubuntu 22.04 LTS (önerilen) |
| RAM | 512 MB (1 GB önerilen) |
| Disk | 2 GB boş alan |
| Alan adı | Opsiyonel ama SSL için gerekli |
| Açık portlar | 80, 443, 22 |

---

## Adım 1 — Sunucuya Bağlan

Bilgisayarından terminali (Windows'ta **CMD** veya **PowerShell**) aç ve şunu yaz:

```
ssh root@SUNUCU_IP_ADRESİN
```

`SUNUCU_IP_ADRESİN` yerine VDS panelindeki IP'yi yaz. Şifre sorduğunda VDS şifreni gir (yazarken ekranda görünmez, bu normal).

---

## Adım 2 — Sistemi Güncelle

Bağlandıktan sonra sırayla şunları çalıştır:

```bash
apt update && apt upgrade -y
```

Birkaç dakika sürebilir, bekle.

---

## Adım 3 — Gerekli Programları Kur

```bash
apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx
```

---

## Adım 4 — Projeyi İndir

```bash
cd /opt
git clone https://github.com/cruciblelab/crucible-cruhon.git
cd crucible-cruhon/support-tawk
```

---

## Adım 5 — Python Ortamı Oluştur

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`(venv)` ifadesinin başa geldiğini görürsen doğru yoldasın.

---

## Adım 6 — Ayar Dosyasını Düzenle

```bash
cp config.example.yml config.yml
nano config.yml
```

Açılan ekranda şunları değiştir:

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  secret_key: "BURAYA_RASTGELE_UZUN_BİR_ŞİFRE_YAZ"   # ← değiştir

admin:
  username: "admin"
  password: "GÜÇLܓBİR_ŞİFRE"                         # ← değiştir
  session_hours: 8

site:
  name: "Destek Hattı"
  domain: "chat.siteadın.com"                          # ← kendi alan adın
```

Kaydetmek için: **Ctrl+X** → **Y** → **Enter**

> **İpucu:** `secret_key` için rastgele bir şey üretmek istersen şunu çalıştır:
> ```bash
> python3 -c "import secrets; print(secrets.token_hex(32))"
> ```
> Çıkan metni kopyalayıp `secret_key` kısmına yapıştır.

---

## Adım 7 — İlk Çalıştırma Testi (Opsiyonel)

Kurulumun çalışıp çalışmadığını test etmek için:

```bash
source /opt/crucible-cruhon/support-tawk/venv/bin/activate
cd /opt/crucible-cruhon/support-tawk
python3 -m uvicorn server.main:app --host 0.0.0.0 --port 8000
```

Tarayıcıda `http://SUNUCU_IP:8000/admin` adresine git. Admin panelini görürsen tamam. **Ctrl+C** ile durdur, devam et.

---

## Adım 8 — Otomatik Başlangıç (Systemd Servisi)

Sunucu her açıldığında otomatik çalışması için bir servis oluştur:

```bash
nano /etc/systemd/system/support-tawk.service
```

İçine şunu yapıştır (alan adını ve kullanıcı adını değiştirme, olduğu gibi bırak):

```ini
[Unit]
Description=Support Tawk Live Chat
After=network.target

[Service]
User=root
WorkingDirectory=/opt/crucible-cruhon/support-tawk
ExecStart=/opt/crucible-cruhon/support-tawk/venv/bin/uvicorn server.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Kaydet: **Ctrl+X** → **Y** → **Enter**

Sonra etkinleştir:

```bash
systemctl daemon-reload
systemctl enable support-tawk
systemctl start support-tawk
```

Çalışıp çalışmadığını kontrol et:

```bash
systemctl status support-tawk
```

Yeşil **active (running)** yazısını görürsen servis ayakta.

---

## Adım 9 — Nginx Ayarla (Alan Adı ile Erişim)

> Alan adın yoksa bu adımı atlayabilirsin, ama HTTPS için alan adı şart.

```bash
nano /etc/nginx/sites-available/support-tawk
```

İçine yapıştır (`chat.siteadin.com` yerine kendi alan adını yaz):

```nginx
server {
    listen 80;
    server_name chat.siteadin.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 3600;
    }
}
```

Kaydet: **Ctrl+X** → **Y** → **Enter**

Sonra etkinleştir:

```bash
ln -s /etc/nginx/sites-available/support-tawk /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

`nginx -t` komutu `syntax is ok` yazarsa devam et.

---

## Adım 10 — SSL Sertifikası (HTTPS)

Alan adın DNS'inde bu sunucunun IP'si kayıtlıysa şunu çalıştır:

```bash
certbot --nginx -d chat.siteadin.com
```

Sana e-posta sorar, kabul sorusu sorar — `A` yazıp Enter bas. Otomatik tamamlanır.

Artık `https://chat.siteadin.com/admin` adresi çalışıyor olmalı.

---

## Adım 11 — Güvenlik Duvarı

```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable
```

`y` yazıp Enter bas.

---

## Adım 12 — Widget Kodunu Siteye Ekle

Admin panelinde **Site Ayarları** → **Widget** bölümüne git. Orada hazır script kodunu kopyalayacaksın. Kopyaladığın kodu sitenin `</body>` etiketinden hemen önce yapıştır:

```html
<script src="https://chat.siteadin.com/widget.js" ...></script>
</body>
```

---

## Sorun Giderme

### Servis çalışmıyor mu?
```bash
journalctl -u support-tawk -n 50
```
Son 50 satır hatayı gösterir.

### Nginx hata mı veriyor?
```bash
nginx -t
journalctl -u nginx -n 20
```

### Şifremi unuttum
```bash
cd /opt/crucible-cruhon/support-tawk
source venv/bin/activate
python3 -c "
from server.auth import hash_password
from server.database import Agent
Agent._meta.database.connect()
a = Agent.get(Agent.username == 'admin')
a.password_hash = hash_password('YeniŞifren123')
a.save()
print('Tamam')
"
```

### Güncelleme yapmak istersen
```bash
cd /opt/crucible-cruhon
git pull
systemctl restart support-tawk
```

---

## Kurulum Özeti

```
✅ Adım 1  → Sunucuya SSH ile bağlandık
✅ Adım 2  → Sistem güncellendi
✅ Adım 3  → Python, git, nginx kuruldu
✅ Adım 4  → Proje indirildi
✅ Adım 5  → Python ortamı hazırlandı
✅ Adım 6  → config.yml düzenlendi
✅ Adım 8  → Systemd servisi kuruldu (otomatik başlangıç)
✅ Adım 9  → Nginx ayarlandı (alan adı yönlendirme)
✅ Adım 10 → SSL sertifikası alındı (HTTPS)
✅ Adım 11 → Güvenlik duvarı açıldı
✅ Adım 12 → Widget sitene eklendi
```

**Admin paneli:** `https://chat.siteadin.com/admin`
