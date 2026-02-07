from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI()

# ==========================================
# 1. GÜVENLİK AYARLARI (API KEY) 🔒
# ==========================================
API_KEY = "6MX3H2W4ni7cP367sygmwxabiylqUlJ"  
API_KEY_NAME = "access_token" # Header'da bu isimle bekliyoruz

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Depends(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Giriş izni yok! Lütfen geçerli bir API Key kullanın."
        )

# ==========================================
# 2. CORS AYARLARI (Web Siteleri İçin) 🌐
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tüm sitelere izin ver
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 3. VERİTABANI BAĞLANTI FONKSİYONLARI 💾
# ==========================================

# Oyuncular veritabanına bağlanır (futbol.db)
def baglanti_kur_oyuncular():
    conn = sqlite3.connect('futbol.db')
    conn.row_factory = sqlite3.Row  # Verileri sözlük formatında çekmek için
    return conn

# Kulüpler veritabanına bağlanır (kulupler.db)
def baglanti_kur_kulupler():
    conn = sqlite3.connect('kulupler.db')
    conn.row_factory = sqlite3.Row
    return conn

# ==========================================
# 4. API ENDPOINT'LERİ (Uç Noktalar) 🚀
# ==========================================

# Ana Sayfa (Şifre istemez, herkes görebilir)
@app.get("/")
def ana_sayfa():
    return {
        "Durum": "Aktif",
        "Mesaj": "Futbol API Sistemine Hoşgeldiniz! Verilere erişmek için API Key gereklidir. 🔐"
    }

# --- OYUNCU İŞLEMLERİ ---

# Tüm Oyuncuları Getir
@app.get("/oyuncular", dependencies=[Depends(get_api_key)])
def oyunculari_listele():
    conn = baglanti_kur_oyuncular()
    veriler = conn.execute("SELECT * FROM oyuncular").fetchall()
    conn.close()
    return veriler

# Takıma Göre Oyuncuları Getir (Sadece oyuncu listesi)
@app.get("/oyuncular/{takim_adi}", dependencies=[Depends(get_api_key)])
def takima_gore_oyuncu_getir(takim_adi: str):
    conn = baglanti_kur_oyuncular()
    # LIKE komutu ile esnek arama (büyük/küçük harf sorununu azaltır)
    sorgu = "SELECT * FROM oyuncular WHERE Team LIKE ?"
    veriler = conn.execute(sorgu, (f"%{takim_adi}%",)).fetchall()
    conn.close()
    return veriler

# --- KULÜP İŞLEMLERİ ---

# Tüm Kulüpleri Listele (Sadece kulüp bilgileri)
@app.get("/kulupler", dependencies=[Depends(get_api_key)])
def kulupleri_listele():
    conn = baglanti_kur_kulupler()
    veriler = conn.execute("SELECT * FROM kulupler").fetchall()
    conn.close()
    return veriler

# Kulüp Detayı + Oyuncu Kadrosu (BÜYÜK BİRLEŞTİRME)
@app.get("/kulupler/{takim_adi}", dependencies=[Depends(get_api_key)])
def kulup_detayi_ve_kadro(takim_adi: str):
    # 1. Adım: Kulüp bilgilerini 'kulupler.db'den çek
    conn_k = baglanti_kur_kulupler()
    kulup_bilgisi = conn_k.execute("SELECT * FROM kulupler WHERE Team LIKE ?", (f"%{takim_adi}%",)).fetchone()
    conn_k.close()
    
    if not kulup_bilgisi:
        return {"Hata": f"'{takim_adi}' isminde bir kulüp bulunamadı."}
    
    # 2. Adım: O kulübün oyuncularını 'futbol.db'den çek
    conn_o = baglanti_kur_oyuncular()
    oyuncular = conn_o.execute("SELECT * FROM oyuncular WHERE Team LIKE ?", (f"%{takim_adi}%",)).fetchall()
    conn_o.close()
    
    # 3. Adım: Hepsini tek bir pakette sun
    return {
        "KulupBilgileri": kulup_bilgisi,
        "Kadro": oyuncular
    }