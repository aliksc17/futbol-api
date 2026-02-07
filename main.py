from fastapi import FastAPI
import sqlite3

app = FastAPI()

# Veritabanına bağlanmak için yardımcı fonksiyon
def baglanti_kur():
    conn = sqlite3.connect('futbol.db')
    conn.row_factory = sqlite3.Row  # Verileri sözlük (dict) gibi çekmemizi sağlar
    return conn

# 1. Ana Sayfa (API çalışıyor mu kontrolü)
@app.get("/")
def ana_sayfa():
    return {"Mesaj": "Futbol API'sine Hoşgeldiniz! ⚽️"}

# 2. Tüm Oyuncuları Getir
@app.get("/oyuncular")
def oyunculari_listele():
    conn = baglanti_kur()
    # Veritabanındaki tüm satırları çek
    veriler = conn.execute("SELECT * FROM oyuncular").fetchall()
    conn.close()
    return veriler

# 3. Takıma Göre Oyuncuları Getir (Filtreleme)
@app.get("/oyuncular/{takim_adi}")
def takima_gore_getir(takim_adi: str):
    conn = baglanti_kur()
    # SQL sorgusu ile filtrele (LIKE komutu büyük/küçük harf duyarlılığını azaltır)
    sorgu = "SELECT * FROM oyuncular WHERE Team LIKE ?"
    veriler = conn.execute(sorgu, (f"%{takim_adi}%",)).fetchall()
    conn.close()
    return veriler

# 4. Takım Kadrolarını Gruplayarak Getir
@app.get("/takimlar")
def takimlari_grupla():
    conn = baglanti_kur()
    # Önce tüm oyuncuları çekelim
    oyuncular = conn.execute("SELECT * FROM oyuncular").fetchall()
    conn.close()

    # Python ile veriyi gruplayalım
    takimlar = {}
    for oyuncu in oyuncular:
        takim = oyuncu['Team']
        if takim not in takimlar:
            takimlar[takim] = []
        takimlar[takim].append(oyuncu)
    
    return takimlar

# --- YENİ EKLENEN KISIM: KULÜPLER ---

# 1. Tüm Kulüpleri Listele
@app.get("/kulupler", dependencies=[Depends(get_api_key)])
def kulupleri_listele():
    conn = baglanti_kur()
    veriler = conn.execute("SELECT * FROM kulupler").fetchall()
    conn.close()
    return veriler

# 2. Kulüp Detayı ve Oyuncularını Birlikte Getir (Gelişmiş)
@app.get("/kulupler/{takim_adi}", dependencies=[Depends(get_api_key)])
def kulup_detayi_getir(takim_adi: str):
    conn = baglanti_kur()
    
    # Önce kulüp bilgilerini çek
    kulup_bilgisi = conn.execute("SELECT * FROM kulupler WHERE Team LIKE ?", (f"%{takim_adi}%",)).fetchone()
    
    if not kulup_bilgisi:
        return {"Hata": "Böyle bir kulüp bulunamadı."}
    
    # Sonra o kulübün oyuncularını çek
    oyuncular = conn.execute("SELECT * FROM oyuncular WHERE Team LIKE ?", (f"%{takim_adi}%",)).fetchall()
    conn.close()
    
    # İkisini birleştirip tek paket yap
    return {
        "KulupBilgileri": kulup_bilgisi,
        "Kadro": oyuncular
    }