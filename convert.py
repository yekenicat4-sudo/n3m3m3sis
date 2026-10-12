"""
convert.py -- Tum veriler*.txt dosyalarini tek bir SQLite veritabanina (veriler.db) aktarir.
Bir kere calistir, sonra API bunu kullanir.
"""

import sys, os, json, re, sqlite3, base64, time

# Windows konsolunda UTF-8 karakter sorunu olmasin
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_PATH = "veriler.db"

def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kullanicilar (
            user_id     TEXT NOT NULL,
            kaynak      TEXT NOT NULL,
            alan        TEXT NOT NULL,
            deger       TEXT,
            PRIMARY KEY (user_id, kaynak, alan)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON kullanicilar(user_id)")
    conn.commit()

def toplu_kaydet(conn, rows):
    conn.executemany(
        "INSERT OR IGNORE INTO kullanicilar(user_id, kaynak, alan, deger) VALUES (?,?,?,?)",
        rows
    )
    conn.commit()

def satir_ekle(rows, uid, kaynak, bilgi: dict):
    uid = str(uid).strip()
    if not uid.isdigit():
        return
    for alan, deger in bilgi.items():
        if alan == "kaynak":
            continue
        rows.append((uid, kaynak, str(alan), str(deger)[:2000]))

# ── DOSYA 1,2,3,7 → Standart JSON ──────────────────────────────────────────
def isle_standart_json(dosya, kaynak, conn):
    print(f"[+] {dosya} (Standart JSON) okunuyor...")
    rows = []
    try:
        with open(dosya, "r", encoding="utf-8", errors="ignore") as f:
            try:
                data = json.load(f)
            except Exception:
                f.seek(0)
                content = f.read()
                count = 0
                for obj in re.finditer(r'\{[^{}]+\}', content):
                    try:
                        item = json.loads(obj.group())
                        uid = item.get("discord_id") or item.get("id") or item.get("user_id")
                        if uid and str(uid).isdigit():
                            satir_ekle(rows, uid, kaynak, item)
                            count += 1
                    except:
                        continue
                toplu_kaydet(conn, rows)
                print(f"  → [KURTARILDI] {count} kullanıcı")
                return

        def isle(uid, bilgi):
            if isinstance(bilgi, dict):
                satir_ekle(rows, uid, kaynak, bilgi)
            else:
                rows.append((str(uid), kaynak, "bilgi", str(bilgi)[:2000]))

        if isinstance(data, dict):
            target = data.get("users") or data.get("data") or data
            if isinstance(target, dict):
                for k, v in target.items():
                    isle(k, v)
            elif isinstance(target, list):
                for item in target:
                    if isinstance(item, dict):
                        uid = item.get("discord_id") or item.get("id") or item.get("user_id")
                        if uid:
                            isle(uid, item)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    uid = item.get("discord_id") or item.get("id") or item.get("user_id")
                    if uid:
                        isle(uid, item)

        toplu_kaydet(conn, rows)
        print(f"  → {len(rows)} satır eklendi.")
    except Exception as e:
        print(f"  [HATA] {e}")

# ── DOSYA 4 → ID:IP ─────────────────────────────────────────────────────────
def isle_ip_dosya(dosya, kaynak, conn):
    print(f"[+] {dosya} (ID:IP) okunuyor...")
    rows = []
    try:
        with open(dosya, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                uid, ip = line.split(":", 1)
                uid = uid.strip()
                if uid.isdigit():
                    rows.append((uid, kaynak, "ip", ip.strip()))
        toplu_kaydet(conn, rows)
        print(f"  → {len(rows)} satır eklendi.")
    except Exception as e:
        print(f"  [HATA] {e}")

# ── DOSYA 5 → Bozuk JSON nesneleri ──────────────────────────────────────────
def isle_veriler5(dosya, kaynak, conn):
    print(f"[+] {dosya} (Bozuk JSON) okunuyor...")
    rows = []
    try:
        with open(dosya, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        for obj in re.finditer(r'\{[^{}]*\}', content):
            try:
                data = json.loads(obj.group())
                uid = str(data.get("username", "")).strip()
                if not uid.isdigit():
                    continue
                if data.get("timestamp"):
                    rows.append((uid, kaynak, "ip", str(data["timestamp"])))
                if data.get("ip"):
                    rows.append((uid, kaynak, "nickname", str(data["ip"])))
                if data.get("discordid"):
                    rows.append((uid, kaynak, "discordid", str(data["discordid"])))
            except:
                continue
        toplu_kaydet(conn, rows)
        print(f"  → {len(rows)} satır eklendi.")
    except Exception as e:
        print(f"  [HATA] {e}")

# ── DOSYA 6 → SQL dump ──────────────────────────────────────────────────────
def isle_sql_dosya(dosya, kaynak, conn):
    print(f"[+] {dosya} (SQL dump) okunuyor...")
    rows = []
    count = 0
    try:
        with open(dosya, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line.startswith("("):
                    continue
                parcalar = re.findall(r"'(.*?)'|(NULL)|(\d+)", line)
                temiz = []
                for p in parcalar:
                    val = p[0] or p[1] or p[2]
                    temiz.append(val if val != "NULL" else "")

                if len(temiz) < 2:
                    continue

                uid = temiz[0]
                if not uid.isdigit():
                    continue

                raw_email = temiz[1]
                try:
                    email = base64.b64decode(raw_email).decode("utf-8") if len(raw_email) > 10 else raw_email
                except:
                    email = raw_email

                alanlar = {
                    "email":     email,
                    "sunucular": temiz[3] if len(temiz) > 3 else "",
                    "baglantilar": temiz[4] if len(temiz) > 4 else "",
                    "biyografi": temiz[6] if len(temiz) > 6 else "",
                    "ip":        temiz[8] if len(temiz) > 8 else "",
                    "durum":     "Aktif" if (len(temiz) > 10 and temiz[10] == "1") else "Bilinmiyor",
                }
                for alan, deger in alanlar.items():
                    if deger:
                        rows.append((uid, kaynak, alan, str(deger)[:2000]))
                count += 1

                if len(rows) >= 50000:
                    toplu_kaydet(conn, rows)
                    rows = []

        toplu_kaydet(conn, rows)
        print(f"  → {count} kullanıcı satırı eklendi.")
    except Exception as e:
        print(f"  [HATA] {e}")


def main():
    baslangic = time.time()
    print(f"\n{'='*50}")
    print("  VERİ DÖNÜŞTÜRÜCÜ — SQLite")
    print(f"{'='*50}\n")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=100000")
    init_db(conn)

    dosyalar = [
        ("veriler.txt",  "Ana DB",     "json"),
        ("veriler2.txt", "Eski DB",    "json"),
        ("veriler3.txt", "Premium DB", "json"),
        ("veriler4.txt", "IP DB",      "ip"),
        ("veriler5.txt", "Yeni DB",    "v5"),
        ("veriler6.txt", "SQL DB",     "sql"),
        ("veriler7.txt", "Ek DB",      "json"),
    ]

    for dosya, kaynak, tip in dosyalar:
        if not os.path.exists(dosya):
            print(f"[ATLA] {dosya} bulunamadı.")
            continue
        if tip == "json":
            isle_standart_json(dosya, kaynak, conn)
        elif tip == "ip":
            isle_ip_dosya(dosya, kaynak, conn)
        elif tip == "v5":
            isle_veriler5(dosya, kaynak, conn)
        elif tip == "sql":
            isle_sql_dosya(dosya, kaynak, conn)

    conn.close()

    sure = time.time() - baslangic
    boyut_mb = os.path.getsize(DB_PATH) / 1024 / 1024
    print(f"\n{'='*50}")
    print(f"  TAMAMLANDI! {sure:.1f} saniyede bitti.")
    print(f"  Veritabanı boyutu: {boyut_mb:.1f} MB")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()
