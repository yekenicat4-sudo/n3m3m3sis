"""
setup.py — Railway baslarken otomatik calisir.
veriler.db yoksa gofile'dan indirir, gz'yi acar, DB hazir eder.
Start command: python setup.py && python run.py
"""
import os
import gzip
import shutil
import urllib.request

DB_GZ  = "veriler.db.gz"
DB     = "veriler.db"

# GitHub Releases - kalici link, token gerekmez
GOFILE_TOKEN = None
GOFILE_URL   = "https://github.com/yekenicat4-sudo/n3m3m3sis/releases/download/veri/veriler.db.gz"


def indir():
    print("[setup] veriler.db.gz indiriliyor (GitHub Releases)...")
    req = urllib.request.Request(
        GOFILE_URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=300) as resp, open(DB_GZ, "wb") as f:
        toplam = int(resp.headers.get("Content-Length", 0))
        indirilen = 0
        parca = 1024 * 1024  # 1MB parcalar
        while True:
            veri = resp.read(parca)
            if not veri:
                break
            f.write(veri)
            indirilen += len(veri)
            if toplam:
                yuzde = indirilen / toplam * 100
                print(f"  {yuzde:.1f}% ({indirilen // 1024 // 1024} MB)", end="\r")
    print(f"\n[setup] Indirildi: {os.path.getsize(DB_GZ) / 1024 / 1024:.1f} MB")


def ac():
    print("[setup] veriler.db.gz aciliyor...")
    with gzip.open(DB_GZ, "rb") as f_in, open(DB, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    print(f"[setup] Tamam! veriler.db olusturuldu ({os.path.getsize(DB) / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    if os.path.exists(DB):
        print(f"[setup] veriler.db zaten mevcut ({os.path.getsize(DB) / 1024 / 1024:.1f} MB), atlanıyor.")
    else:
        if not os.path.exists(DB_GZ):
            indir()
        ac()
        # gz artık gerekmiyor, disk tasarrufu için sil
        try:
            os.remove(DB_GZ)
        except:
            pass

    # Kara listedeki ID'leri veritabanından kalıcı olarak sil
    try:
        import sqlite3
        conn = sqlite3.connect(DB)
        conn.execute("DELETE FROM kullanicilar WHERE user_id IN ('1140677611710840954')")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[setup] Filtreleme uyarisi: {e}")

    print("[setup] Hazir!")
