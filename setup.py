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

# Gofile bilgileri
GOFILE_TOKEN = "7NmbrWn0J8vIKOlolwMj85UoPbZOFafM"
GOFILE_URL   = "https://store8.gofile.io/download/direct/4fe4749d-881c-4f5f-84a1-c078961a44fc/veriler.db.gz"


def indir():
    print("[setup] veriler.db.gz indiriliyor...")
    req = urllib.request.Request(
        GOFILE_URL,
        headers={"Authorization": f"Bearer {GOFILE_TOKEN}"}
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
    print("[setup] Hazir!")
