"""
api/main.py — FastAPI tabanlı Discord ID sorgulama API'si
Çalıştır: uvicorn api.main:app --reload
"""

import sqlite3
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Veritabanı yolu (api klasörünün bir üstünde)
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "veriler.db")

app = FastAPI(
    title="Discord Lookup API",
    description="Discord ID ile kullanıcı bilgisi sorgulama",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — Web arayüzünden istek gelebilsin diye
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def sorgula(user_id: str):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT kaynak, alan, deger FROM kullanicilar WHERE user_id = ?",
            (user_id,)
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return None

    # Kaynakları grupla
    kaynaklar: dict = {}
    for row in rows:
        k = row["kaynak"]
        if k not in kaynaklar:
            kaynaklar[k] = {"kaynak": k}
        kaynaklar[k][row["alan"]] = row["deger"]

    return list(kaynaklar.values())


# ─────────────────────────────────────────────────────────────
#  ANA ENDPOINT
# ─────────────────────────────────────────────────────────────

@app.get("/api/v1/{user_id}", summary="Discord ID ile kullanıcı sorgula")
def kullanici_sorgula(user_id: str):
    """
    Discord kullanıcı ID'sini sorgulanır ve tüm veritabanlarından bulunan
    bilgiler döndürülür.

    - **user_id**: Discord kullanıcı ID (sayısal, örn: 1210275552485707849)
    """
    if not user_id.isdigit():
        raise HTTPException(status_code=400, detail="Geçersiz ID — sadece rakam olmalı.")

    sonuc = sorgula(user_id)

    if sonuc is None:
        return JSONResponse(
            status_code=404,
            content={
                "status": "not_found",
                "user_id": user_id,
                "message": "Kayıtsız kullanıcı — veritabanında bu ID bulunamadı.",
            },
        )

    return {
        "status": "success",
        "user_id": user_id,
        "toplam_kaynak": len(sonuc),
        "kayitlar": sonuc,
    }


@app.get("/api/v1/", summary="API bilgisi")
def api_info():
    return {
        "status": "online",
        "version": "1.0.0",
        "kullanim": "/api/v1/{discord_id}",
        "ornek": "/api/v1/1210275552485707849",
    }


@app.get("/health")
def health():
    try:
        conn = get_db()
        sayi = conn.execute("SELECT COUNT(DISTINCT user_id) FROM kullanicilar").fetchone()[0]
        conn.close()
        return {"status": "ok", "toplam_kullanici": sayi}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})
