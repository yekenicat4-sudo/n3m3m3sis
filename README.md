# Discord Lookup API

Discord ID ile kullanıcı bilgisi sorgulayan REST API.

## Kurulum

### 1. Verileri SQLite'a Aktar (Bir Kere Çalıştır)

```bash
python convert.py
```

Bu işlem tüm `veriler*.txt` dosyalarını `veriler.db` adlı tek bir veritabanına aktarır.

### 2. API'yi Yerel Olarak Başlat

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

API açık olduğunda:
- `http://localhost:8000/api/v1/<discord_id>` → Kullanıcı sorgusu
- `http://localhost:8000/docs` → Swagger belgesi
- `http://localhost:8000/health` → Durum kontrolü

---

## Deploy (Railway.app — Ücretsiz)

1. [railway.app](https://railway.app) hesabı aç
2. "New Project → Deploy from GitHub Repo" seç
3. Repoyu seç
4. Ortam değişkeni ekle: `PORT=8000`
5. Start komutu: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

> **Not:** `veriler.db` dosyasını repoya koymadan önce `.gitignore`'a bak.
> 100 MB üzerindeki ham veri dosyaları (`veriler6.txt` vb.) repoya eklenmez,
> sadece üretilen `veriler.db` eklenir.

---

## Web Arayüzü (Netlify)

1. `web/index.html` dosyasını aç
2. `API_BASE` satırını Railway'den aldığın URL ile güncelle:
   ```js
   const API_BASE = "https://senin-api-adresin.railway.app";
   ```
3. `web/` klasörünü Netlify'a sürükle-bırak → Site anında yayına girer.

---

## Endpoint

### `GET /api/v1/{user_id}`

| Durum | HTTP Kodu | Yanıt |
|---|---|---|
| Bulundu | 200 | `{"status":"success", "kayitlar":[...]}` |
| Bulunamadı | 404 | `{"status":"not_found", "message":"Kayıtsız kullanıcı"}` |
| Hatalı ID | 400 | `{"detail":"Geçersiz ID"}` |

**Örnek Başarılı Yanıt:**
```json
{
  "status": "success",
  "user_id": "1210275552485707849",
  "toplam_kaynak": 2,
  "kayitlar": [
    {
      "kaynak": "IP DB",
      "ip": "1.2.3.4"
    },
    {
      "kaynak": "SQL DB",
      "email": "ornek@gmail.com",
      "biyografi": "...",
      "durum": "Aktif"
    }
  ]
}
```

**Bulunamadı Yanıtı:**
```json
{
  "status": "not_found",
  "user_id": "999999999",
  "message": "Kayıtsız kullanıcı — veritabanında bu ID bulunamadı."
}
```
