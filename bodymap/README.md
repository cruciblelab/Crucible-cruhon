# BodyMap — Haritalama Aracı

Yüz, vücut ve el haritalama uygulaması.
MediaPipe Holistic (478 yüz + 33 vücut + 42 el noktası).

## Proje Yapısı

```
bodymap/
├── server.py          ← FastAPI backend
├── requirements.txt   ← pip bağımlılıkları
├── static/
│   └── index.html     ← Web arayüzü (Three.js dahil)
└── exports/           ← ZIP çıktıları (otomatik oluşur)
```

## Kurulum (VDS / Ubuntu)

```bash
pip install -r requirements.txt
python server.py
```

Tarayıcıdan: `http://SUNUCU_IP:8000`

## Kullanım Akışı

1. Hedef seç: **Yüz** / **Vücut** / **Tam**
2. Kamera seç: Ön / Arka
3. Stil seç (kaydırılabilir şerit): Çizgili / Nokta / Kalıp / Bölge / Derinlik / X-Ray / Termal / İskelet
4. **●** butonuna bas → kamerayı gezdir → tekrar bas (kayıt durur)
5. **EXPORT** → ZIP otomatik indirilir
6. **3D** butonuyla tarayıcıda nokta bulutunu incele (döndür/yakınlaştır)
7. **📸 SNAP** → anlık ekran görüntüsü al, SNAP sekmesinden indir

## Stiller

| Stil | Açıklama |
|---|---|
| Çizgili | Tel kafes |
| Nokta | Sadece landmark noktaları |
| Kalıp | Dolu siluet |
| Bölge | Her anatomik bölge farklı renk |
| Derinlik | Z değerine göre ısı rengi |
| X-Ray | Yarı saydam tarama |
| Termal | Plasma renk haritası (önbellekli, hızlı) |
| İskelet | Kemik bağlantıları |

## Export İçeriği (ZIP)

- `face_mesh.obj` — 3D yüz mesh
- `face_mesh.stl` — 3D print hazır
- `face_pointcloud.ply` — Renkli nokta bulutu
- `body_skeleton.ply` — Vücut iskelet noktaları
- `left_hand.ply` / `right_hand.ply` — El nokta bulutları
- `landmarks.json` — Tüm landmark koordinatları (JSON)
- `README.txt` — Tarama raporu

## Klavye Kısayolları

| Tuş | Eylem |
|---|---|
| `Space` | Kayıt başlat/durdur |
| `E` | Export |
| `P` veya `S` | Snapshot al |
| `3` | Kamera ↔ 3D görünüm |
| `Ctrl+R` | Sıfırla |

## Düzeltilen Buglar

- **WebSocket HTTPS**: `ws://` → `wss://` otomatik seçim
- **HUD alpha efekti**: `addWeighted` ile gerçek şeffaflık
- **REC/FPS çakışması**: HUD'daki metin üst üste binmesi düzeltildi
- **El algılama**: El varsa `detected=True` olarak işaretleniyor
- **Thermal önbellek**: `_tris_from_tess` her frame'de değil bir kez hesaplanıyor
- **Frame limiti**: Max 2000 frame, dolduktan sonra otomatik durdurma + badge uyarısı
- **FPS hesabı**: Payda hatası (`len(buf)+1e-9`) düzeltildi
- **Path traversal**: Export endpoint'inde güvenlik kontrolü eklendi
- **WS yeniden bağlanma**: Reconnect sonrası ayarlar otomatik gönderiliyor

## Yeni Özellikler

- **JSON export**: `landmarks.json` ile koordinatlar makine-okunabilir formatta
- **El verisi export**: Sol/sağ el PLY dosyaları
- **📸 Snapshot**: Anlık PNG görüntü, galeriden indirilebilir (max 30 bellekte)
- **SNAP sekmesi**: Drawer'da galeri görünümü
- **Log temizle**: LOG sekmesinde TEMİZLE butonu
- **`/health` endpoint**: Sunucu durum kontrolü
- **trimesh yoksa açık uyarı**: Export raporunda belirtiliyor

## Geliştirme Notları

- `server.py → FACE_REGIONS` → yeni bölge eklemek için landmark indeksleri
- `server.py → STYLES` → yeni stil: dict'e ekle + `draw_face()` içine elif bloğu
- `server.py → build_export()` → ZIP içeriğini değiştir
- `server.py → MAX_FRAMES` → kayıt frame limiti
- `static/index.html → REGIONS` → frontend renk eşleşmesi (server ile senkron tut)

## Gerçekçi Notlar

RGB kamera kullanılıyor. Koordinatlar **göreceli** (mm değil).
Gerçek mm hassasiyeti için: Intel RealSense / OAK-D gereklidir.
