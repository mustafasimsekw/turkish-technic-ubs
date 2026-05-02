import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import json
import os
import base64

st.set_page_config(page_title="Turkish Technic | Uçak Bilgi Sistemi", layout="wide")

st.markdown("""
    <style>
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    
    [data-testid="stAppViewDeployButton"] {display: none !important;}
    .stDeployButton {display: none !important;}
    
    [data-testid="stViewerBadge"] {display: none !important;}
    .viewerBadge_container {display: none !important;}
    .viewerBadge_link {display: none !important;}

    @media (min-width: 768px) {
        header {visibility: hidden !important;}
        [data-testid="collapsedControl"] {display: none !important;}
    }

    @media (max-width: 767px) {
        header {
            visibility: visible !important; 
            background-color: transparent !important; /* Tekrar şeffaf yaptık */
            border-bottom: none !important; /* Çizgiyi kaldırdık */
        }
        [data-testid="collapsedControl"] {display: block !important;}
        [data-testid="stToolbarActions"] {display: none !important;} /* Sağ üst ikonlar (GitHub/Fork) kesinlikle yok */
    }

    [data-testid="stMetricValue"] { font-size: 24px; color: #d32f2f; }
    .stAlert { border-radius: 10px; }
    div.stButton > button { width: 100%; border-radius: 5px; height: 3.5em; background-color: #ffffff; border: 1px solid #ddd; font-weight: bold; }
    div.stButton > button:hover { border: 2px solid #d32f2f; color: #d32f2f; background-color: #fffafa; }
    
    .hangar-box { border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 10px; border: 2px solid #eee; min-height: 220px; display: flex; flex-direction: column; justify-content: center; align-items: center; }
    .occupied { background-color: #fff5f5; border-color: #d32f2f; }
    .empty { background-color: #f8f9fa; border-color: #ddd; color: #666; }
    .ucak-resmi { width: 100px; margin: 10px 0; mix-blend-mode: multiply; }
    
    .customer-card { border: 1px solid #ddd; border-radius: 10px; padding: 20px; margin-bottom: 15px; background-color: #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .customer-header { display: flex; align-items: center; margin-bottom: 15px; }
    .customer-logo { width: 60px; height: 60px; object-fit: contain; margin-right: 15px; border-radius: 5px; }
    .customer-name { font-size: 22px; font-weight: bold; margin: 0; color: #333; }
    .customer-note { background-color: #f8f9fa; padding: 15px; border-left: 4px solid #0056b3; border-radius: 4px; font-size: 16px; color: #222; }
    </style>
    """, unsafe_allow_html=True)

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""
ucak_base64 = get_image_base64("ucak.png")


def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    
    if not st.session_state["password_correct"]:
        def get_base64(bin_file):
            with open(bin_file, 'rb') as f:
                data = f.read()
            return base64.b64encode(data).decode()

        try:
            bin_str = get_base64('wallpaper.png')
            bg_image_css = f'data:image/png;base64,{bin_str}'
        except Exception:
            bg_image_css = ""

        st.markdown(
            f"""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@700&display=swap');

            .stApp {{
                background-image: url("{bg_image_css}");
                background-size: cover;
                background-position: center; 
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            
            h1 {{
                color: white !important;
                font-family: 'Roboto', 'Arial', sans-serif !important;
                font-weight: 700;
                text-shadow: 3px 3px 8px rgba(0,0,0,0.8);
                text-align: center;
                padding-top: 40px;
            }}
            
            [data-testid="stForm"] {{
                background-color: rgba(255, 255, 255, 0.9);
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 15px 35px rgba(0,0,0,0.5);
                max-width: 500px;
                margin: 20px auto;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

        st.title("Turkish Technic Uçak Bilgi Sistemi")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                st.subheader("Güvenli Giriş") 
                sifre = st.text_input("Erişim Şifresi:", type="password", placeholder="Şifrenizi yazın...")
                if st.form_submit_button("Sisteme Giriş Yap"):
                    if sifre == st.secrets["db_password"]:
                        st.session_state["password_correct"] = True
                        st.rerun()
                    else: 
                        st.error("Hatalı Şifre!")
        return False
    return True

if not check_password():
    st.stop()

@st.cache_data(ttl=60)
def veriyi_getir():
    try:
        df = pd.read_excel("TurkishTechnic_Ucak_Bilgileri.xlsx")
        df.columns = df.columns.str.strip()
        df['Son Bakım'] = pd.to_datetime(df['Son Bakım'], dayfirst=True, errors='coerce')
        return df
    except Exception as e:
        st.error(f"Uçak Verisi Okuma Hatası: {e}"); return None

@st.cache_data(ttl=60)
def malzeme_verisi_getir():
    try:
        df_malz = pd.read_excel("Malzemeler.xlsx")
        df_malz.columns = df_malz.columns.str.strip()
        df_malz['Sistem_Uyarı'] = np.where(df_malz['Mevcut_Stok'] == 0, 'Tükendi',
                             np.where(df_malz['Mevcut_Stok'] <= df_malz['Kritik_Seviye'], 'Kritik', 'Yeterli'))
        return df_malz
    except Exception as e:
        st.error(f"Malzeme Excel Okuma Hatası: {e}"); return None

HANGAR_DOSYASI = "Hangar_Durumu.json"
MUSTERI_DOSYASI = "Musteri_Degerlendirme.json"

def hangar_yukle():
    if os.path.exists(HANGAR_DOSYASI):
        with open(HANGAR_DOSYASI, "r", encoding="utf-8") as f:
            veri = json.load(f)
            if "Bay-1" in veri: return {f"Slot-{i+1}": None for i in range(6)}
            return veri
    return {f"Slot-{i+1}": None for i in range(6)}

def hangar_kaydet(veri):
    with open(HANGAR_DOSYASI, "w", encoding="utf-8") as f: json.dump(veri, f, ensure_ascii=False, indent=4)

def musteri_yukle():
    if os.path.exists(MUSTERI_DOSYASI):
        with open(MUSTERI_DOSYASI, "r", encoding="utf-8") as f: return json.load(f)
    return {}

def musteri_kaydet(veri):
    with open(MUSTERI_DOSYASI, "w", encoding="utf-8") as f: json.dump(veri, f, ensure_ascii=False, indent=4)

df = veriyi_getir()
df_malzeme = malzeme_verisi_getir()

if df is not None:
    if "sayfa" not in st.session_state: st.session_state["sayfa"] = "Uçak Bilgileri"
    if "secilen_tescil" not in st.session_state: st.session_state["secilen_tescil"] = df["Tescil"].iloc[0]
    if "gelinen_yer" not in st.session_state: st.session_state["gelinen_yer"] = None
    if "hangar_durumu" not in st.session_state: st.session_state["hangar_durumu"] = hangar_yukle()
    if "musteriler" not in st.session_state: st.session_state["musteriler"] = musteri_yukle()

    st.sidebar.image("https://sponsorlogo.informamarkets.com/sites/default/files/TurkTech422x292_0.png", width=200)
    st.sidebar.title("Kontrol Merkezi")
    
    menü_listesi = ["Uçak Bilgileri", "Bakım Aciliyet Durumu", "Filo İstatistikleri", "Malzeme Takibi", "Hangar Yönetimi", "Müşteri Değerlendirme"]
    choice = st.sidebar.radio("Menü Seçimi", menü_listesi, index=menü_listesi.index(st.session_state["sayfa"]), label_visibility="collapsed")
    if choice != st.session_state["sayfa"]:
        st.session_state["sayfa"] = choice
        st.rerun()

    if st.session_state["sayfa"] == "Uçak Bilgileri":
        if st.session_state["gelinen_yer"] == "Bakım Aciliyet Durumu":
            if st.button("Bakım Aciliyet Sayfasına Dön"):
                st.session_state["sayfa"] = "Bakım Aciliyet Durumu"
                st.session_state["gelinen_yer"] = None
                st.rerun()

        tescil_list = df["Tescil"].tolist()
        st.sidebar.divider()
        st.sidebar.selectbox("Uçak Seçiniz:", tescil_list, key="secilen_tescil")
        
        secilen = st.session_state["secilen_tescil"]
        u = df[df["Tescil"] == secilen].iloc[0]

        st.title(f"{secilen} Uçak Veri Paneli")
        nato = {'A': 'Alpha', 'B': 'Bravo', 'C': 'Charlie', 'D': 'Delta', 'E': 'Echo', 'F': 'Foxtrot', 'G': 'Golf', 'H': 'Hotel', 'I': 'India', 'J': 'Juliet', 'K': 'Kilo', 'L': 'Lima', 'M': 'Mike', 'N': 'November', 'O': 'Oscar', 'P': 'Papa', 'Q': 'Quebec', 'R': 'Romeo', 'S': 'Sierra', 'T': 'Tango', 'U': 'Uniform', 'V': 'Victor', 'W': 'Whiskey', 'X': 'X-ray', 'Y': 'Yankee', 'Z': 'Zulu', '-': '-'}
        st.write(f"**Okunuşu:** {' '.join([nato.get(c.upper(), c) for c in secilen])}")
        
        st.subheader(f"{u['Uçak Tipi']}")

        guncel_fh = int(u.get('Güncel FH', 0)) if pd.notna(u.get('Güncel FH')) else 0
        limit_fh = int(u.get('Limit FH', 1)) if pd.notna(u.get('Limit FH')) else 1
        guncel_fc = int(u.get('Güncel FC', 0)) if pd.notna(u.get('Güncel FC')) else 0
        limit_fc = int(u.get('Limit FC', 1)) if pd.notna(u.get('Limit FC')) else 1

        kalan_fh = limit_fh - guncel_fh
        kalan_fc = limit_fc - guncel_fc

        bakim_hedefi = u['Son Bakım'] + timedelta(days=int(u['Periyot (Gün)']))
        kalan_gun = (bakim_hedefi - datetime.now()).days
        
        if u['Durum'] == "AOG" or kalan_gun <= 0 or kalan_fh <= 0 or kalan_fc <= 0: 
            st.error(f"KRİTİK: Uçak AOG statüsünde veya uçuş limitlerinden biri aşıldı!")
        elif kalan_gun < 15 or kalan_fh < 500 or kalan_fc < 100: 
            st.warning(f"DİKKAT: Bakım Yaklaşıyor! (Kalan: {kalan_gun} Gün | {kalan_fh} FH | {kalan_fc} FC)")
        else: 
            st.success(f"OPERASYONEL: Tüm limitler dahilinde uçuşa hazır.")

        st.divider()
        sol, sag = st.columns([1.2, 2])
        with sol:
            if pd.notna(u["Foto"]) and str(u["Foto"]).startswith("http"):
                st.image(u["Foto"], use_container_width=True)
            else: st.info("Fotoğraf bulunamadı.")
            
        with sag:
            st.write("### Teknik Bilgiler")
            m1, m2, m3 = st.columns(3)
            m1.metric("Kapasite", f"{u['Kapasite']} PAX")
            m2.metric("Menzil", f"{u['Menzil (km)']} KM")
            m3.metric("Uçak Yaşı", f"{u['Yaş']} Yıl")
            
            m4, m5, m6 = st.columns(3)
            m4.metric("Gövde", u['Gövde Tipi'])
            m5.metric("Winglet", u['Winglet'])
            m6.metric("Motor", u['Motor Modeli'])

            st.write("---")
            st.write("### Uçuş Limitleri")
            
            oran_fh = min(guncel_fh / limit_fh, 1.0) if limit_fh > 0 else 0.0
            st.write(f"**Uçuş Saati (Flight Hours):** {guncel_fh:,} / {limit_fh:,} ({kalan_fh:,} saat kaldı)")
            st.progress(oran_fh)
            
            oran_fc = min(guncel_fc / limit_fc, 1.0) if limit_fc > 0 else 0.0
            st.write(f"**Uçuş Döngüsü (Flight Cycles):** {guncel_fc:,} / {limit_fc:,} ({kalan_fc:,} döngü kaldı)")
            st.progress(oran_fc)

            st.write("---")
            st.write("### Kayıt Bilgileri")
            k1, k2, k3 = st.columns(3)
            k1.metric("Son Bakım", u['Son Bakım'].strftime('%d.%m.%Y'))
            k2.metric("Bakım Periyodu", f"{u['Periyot (Gün)']} G")
            menzil_sinifi = "Uzun Menzil" if u['Menzil (km)'] > 8000 else "Orta/Kısa Menzil"
            k3.metric("Menzil Sınıfı", menzil_sinifi)

            k4, k5, k6 = st.columns(3)
            k4.metric("Güncel Konum", u['Konum'])
            k5.metric("Operasyonel Durum", u['Durum'])
            k6.metric("Kayıtlı Tescil", secilen)

    elif st.session_state["sayfa"] == "Bakım Aciliyet Durumu":
        st.title("Bakım Aciliyet Merkezi")
        st.info("Uçaklar güncel durumuna göre kategorize edilmiştir. Detaylı bilgi için için tescil koduna tıklayınız.")
        st.divider()

        bugun = datetime.now()
        kritik, dikkat, operasyonel = [], [], []

        for _, row in df.iterrows():
            kalan_gun = ((row['Son Bakım'] + timedelta(days=int(row['Periyot (Gün)']))) - bugun).days
            kalan_fh = int(row.get('Limit FH', 1)) - int(row.get('Güncel FH', 0))
            kalan_fc = int(row.get('Limit FC', 1)) - int(row.get('Güncel FC', 0))

            if row['Durum'] == "AOG" or kalan_gun <= 0 or kalan_fh <= 0 or kalan_fc <= 0: 
                kritik.append(row['Tescil'])
            elif kalan_gun < 15 or kalan_fh < 500 or kalan_fc < 100: 
                dikkat.append(row['Tescil'])
            else: 
                operasyonel.append(row['Tescil'])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.error("Kritik Durum")
            for t in kritik:
                if st.button(t, key=f"k_{t}"):
                    st.session_state["secilen_tescil"] = t
                    st.session_state["sayfa"] = "Uçak Bilgileri"
                    st.session_state["gelinen_yer"] = "Bakım Aciliyet Durumu"
                    st.rerun()
        with col2:
            st.warning("Dikkat")
            for t in dikkat:
                if st.button(t, key=f"d_{t}"):
                    st.session_state["secilen_tescil"] = t
                    st.session_state["sayfa"] = "Uçak Bilgileri"
                    st.session_state["gelinen_yer"] = "Bakım Aciliyet Durumu"
                    st.rerun()
        with col3:
            st.success("Operasyonel")
            for t in operasyonel:
                if st.button(t, key=f"o_{t}"):
                    st.session_state["secilen_tescil"] = t
                    st.session_state["sayfa"] = "Uçak Bilgileri"
                    st.session_state["gelinen_yer"] = "Bakım Aciliyet Durumu"
                    st.rerun()

    elif st.session_state["sayfa"] == "Filo İstatistikleri":
        st.title("Filo Geneli Analiz Raporu")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam Uçak", len(df))
        c2.metric("Aktif Filo Oranı", f"%{len(df[df['Durum']=='Operasyonel'])/len(df)*100:.0f}")
        c3.metric("AOG Uçak Sayısı", len(df[df['Durum']=='AOG']))
        c4.metric("Ortalama Filo Yaşı", f"{df['Yaş'].mean():.1f} Yıl")
        
        st.write("") 
        
        c5, c6, c7, c8 = st.columns(4)
        c5.metric("En Yüksek Kapasite", f"{df['Kapasite'].max()} PAX")
        c6.metric("En Düşük Kapasite", f"{df['Kapasite'].min()} PAX")
        c7.metric("En Yaşlı Uçak", f"{df['Yaş'].max()} Yıl")
        c8.metric("En Genç Uçak", f"{df['Yaş'].min()} Yıl")
        
        st.divider()
        
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Konum Bazlı Dağılım")
            renk_ayari = {'Operasyonel': '#388e3c', 'AOG': '#d32f2f'}
            fig = px.bar(df, x='Konum', color='Durum', barmode='group', 
                         color_discrete_map=renk_ayari, 
                         category_orders={
                             'Durum': ['Operasyonel', 'AOG'],
                             'Konum': ['İstanbul (IST)', 'Ankara (ESB)', 'Sabiha Gökçen (SAW)', 'İstanbul (ISL - Atatürk)']
                         })
            fig.update_yaxes(title_text="Uçak Sayısı", dtick=1, tick0=0)
            fig.update_xaxes(title_text="")
            st.plotly_chart(fig, use_container_width=True)
            
        with g2:
            st.subheader("Uçak Tipi Dağılımı")
            df_pie = df['Uçak Tipi'].value_counts().reset_index()
            df_pie.columns = ['Uçak Tipi', 'Sayı']
            toplam = df_pie['Sayı'].sum()
            df_pie['Özel_Etiket'] = df_pie.apply(lambda row: f"{row['Uçak Tipi']}<br>%{int(round((row['Sayı']/toplam)*100, 0))} ({row['Sayı']})", axis=1)
            
            fig2 = px.pie(df_pie, names='Uçak Tipi', values='Sayı', hole=0.4)
            fig2.update_traces(textposition='inside', textinfo='text', text=df_pie['Özel_Etiket'])
            st.plotly_chart(fig2, use_container_width=True)
            
        st.subheader("Tüm Envanter Listesi")
        st.dataframe(df, use_container_width=True)

    elif st.session_state["sayfa"] == "Malzeme Takibi":
        st.title("Malzeme ve Depo Yönetimi")
        st.write("Envanterdeki malzemeler ve güncel stok durumları tabloda verilmiştir.")
        
        if df_malzeme is not None:
            c1, c2, c3, c4 = st.columns(4)
            toplam_kalem = len(df_malzeme)
            tukenmis = len(df_malzeme[df_malzeme['Mevcut_Stok'] == 0])
            kritik = len(df_malzeme[(df_malzeme['Mevcut_Stok'] > 0) & (df_malzeme['Mevcut_Stok'] <= df_malzeme['Kritik_Seviye'])])
            siparisler = len(df_malzeme[df_malzeme['Tedarik_Durumu'].isin(['Siparişte'])])
            
            c1.metric("Toplam Malzeme Çeşidi", toplam_kalem)
            c2.metric("Tükenenler", tukenmis)
            c3.metric("Kritik Stoktakiler", kritik)
            c4.metric("Siparişteki Ürünler", siparisler)
            
            st.divider()
            
            tab1, tab2 = st.tabs(["Tüm Envanter Listesi", "Acil Aksiyon Gerekenler"])
            
            with tab1:
                col_filtre, col_ara = st.columns(2)
                with col_filtre:
                    kategoriler = ["Tümü"] + list(df_malzeme['Kategori'].unique())
                    secilen_kat = st.selectbox("Kategori Filtresi:", kategoriler)
                with col_ara:
                    arama = st.text_input("Parça Adı veya P/N Ara:")
                
                df_goster = df_malzeme.copy()
                if secilen_kat != "Tümü":
                    df_goster = df_goster[df_goster['Kategori'] == secilen_kat]
                if arama:
                    df_goster = df_goster[df_goster['Parca_No'].str.contains(arama, case=False, na=False) | df_goster['Parca_Tanimi'].str.contains(arama, case=False, na=False)]
                
                df_goster['Dolulu_Orani'] = ((df_goster['Mevcut_Stok'] / df_goster['Kritik_Seviye']) * 100).clip(upper=100)
                
                st.dataframe(
                    df_goster[['Parca_No', 'Parca_Tanimi', 'Kategori', 'Mevcut_Stok', 'Kritik_Seviye', 'Dolulu_Orani', 'Tedarik_Durumu']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Dolulu_Orani": st.column_config.ProgressColumn(
                            "Kritik Eşik Doluluğu",
                            help="Çubuk doluluğu kritik eşiğe olan mesafeyi gösterir. %100 veya üzeri stok güvenli demektir.",
                            format="%d%%",
                            min_value=0,
                            max_value=100, 
                        ),
                        "Kritik_Seviye": st.column_config.NumberColumn("Kritik Eşik"),
                        "Mevcut_Stok": st.column_config.NumberColumn("Güncel Adet")
                    }
                )
                
            with tab2:
                st.subheader("Stok Seviyesi Kritik veya Tükenmiş Malzemeler")
                
                acil_df = df_malzeme[df_malzeme['Mevcut_Stok'] <= df_malzeme['Kritik_Seviye']].sort_values(by='Mevcut_Stok')
                
                if acil_df.empty:
                    st.success("Tüm stok seviyeleri yeterli durumda. Acil aksiyon gerektiren malzeme bulunmuyor.")
                else:
                    for _, row in acil_df.iterrows():
                        if row['Mevcut_Stok'] == 0:
                            st.error(f"TÜKENDİ: {row['Parca_Tanimi']} (P/N: {row['Parca_No']}) | Kategori: {row['Kategori']} | Durum: {row['Tedarik_Durumu']}")
                        else:
                            st.warning(f"KRİTİK: {row['Parca_Tanimi']} (P/N: {row['Parca_No']}) | Kalan: {row['Mevcut_Stok']} Adet (Sınır: {row['Kritik_Seviye']}) | Durum: {row['Tedarik_Durumu']}")

        else:
            st.warning("Malzeme verisi yüklenemedi. 'Malzemeler.xlsx' dosyasını kontrol ediniz.")

    elif st.session_state["sayfa"] == "Hangar Yönetimi":
        st.title("Hangar Slot Yönetimi")
        st.write("Hangardaki bakım alanlarının doluluk durumu.")
        st.divider()

        bay_keys = list(st.session_state["hangar_durumu"].keys())
        rows = [st.columns(3), st.columns(3)]
        
        for i, bay_id in enumerate(bay_keys):
            row_idx = i // 3
            col_idx = i % 3
            
            with rows[row_idx][col_idx]:
                bay_data = st.session_state["hangar_durumu"][bay_id]
                if bay_data is not None:
                    if isinstance(bay_data, str): tescil, bitis_tarihi = bay_data, "Belirsiz"
                    else: tescil, bitis_tarihi = bay_data["tescil"], bay_data["bitis"]
                    
                    st.markdown(f"""
                        <div class="hangar-box occupied">
                            <h4 style='margin:0; color:#bb1114;'>{bay_id}</h4>
                            <img class="ucak-resmi" src="data:image/png;base64,{ucak_base64}">
                            <br>
                            <b style='font-size:24px;'>{tescil}</b>
                            <p style='margin-top:10px; color:#555; font-weight:bold;'>Çıkış: {bitis_tarihi}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Slotu Boşalt", key=f"btn_bosalt_{bay_id}"):
                        st.session_state["hangar_durumu"][bay_id] = None
                        hangar_kaydet(st.session_state["hangar_durumu"]); st.success(f"{tescil} hangardan çıkarıldı."); st.rerun()
                else:
                    st.markdown(f"""
                        <div class="hangar-box empty">
                            <h4 style='margin:0;'>{bay_id}</h4>
                            <p style='margin:5px 0;'>MÜSAİT SLOT</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    uygun_ucaklar = df["Tescil"].tolist()
                    secilen_yeni_ucak = st.selectbox("Uçak Seç:", ["Seçiniz..."] + uygun_ucaklar, key=f"sel_{bay_id}", label_visibility="collapsed")
                    kalacagi_gun = st.number_input("Kaç gün kalacak?", min_value=1, max_value=180, value=7, key=f"gun_{bay_id}")
                    
                    if st.button("Slotu Doldur", key=f"btn_yerlestir_{bay_id}"):
                        if secilen_yeni_ucak != "Seçiniz...":
                            hesaplanan_bitis = (datetime.now() + timedelta(days=kalacagi_gun)).strftime('%d.%m.%Y')
                            st.session_state["hangar_durumu"][bay_id] = {"tescil": secilen_yeni_ucak, "bitis": hesaplanan_bitis}
                            hangar_kaydet(st.session_state["hangar_durumu"]); st.success(f"{secilen_yeni_ucak} {bay_id} alanına alındı."); st.rerun()
                        else: st.warning("Lütfen bir uçak seçin.")

    elif st.session_state["sayfa"] == "Müşteri Değerlendirme":
        st.title("Müşteri Analiz ve Değerlendirme")
        st.write("Hizmet verilen havayolu şirketlerinin değerlendirme notları.")
        st.divider()

        st.subheader("Mevcut Müşteri Portföyü")
        musteriler = st.session_state["musteriler"]
        
        if not musteriler:
            st.info("Sistemde henüz kayıtlı bir müşteri bulunmuyor.")
        else:
            kart_kolonlari = st.columns(3)
            for i, (m_adi, v) in enumerate(musteriler.items()):
                p = v["puan"]
                renk_kodu = "#d32f2f" if p <= 4 else "#fbc02d" if p <= 7 else "#388e3c"
                yuzde = p * 10
                
                with kart_kolonlari[i % 3]:
                    st.markdown(f"""
                        <div class="customer-card">
                            <div class="customer-header">
                                <img src="{v['logo']}" class="customer-logo">
                                <div><h3 class="customer-name">{m_adi}</h3><span style="font-weight:bold; font-size:16px;">Değerlendirme: {p}/10</span></div>
                            </div>
                            <div style="width: 100%; background-color: #e0e0e0; border-radius: 10px; height: 16px; margin: 10px 0 15px 0; overflow: hidden; box-shadow: inset 0 1px 3px rgba(0,0,0,0.2);">
                                <div style="width: {yuzde}%; height: 100%; background-color: {renk_kodu}; border-radius: 10px; transition: width 0.5s ease-in-out;"></div>
                            </div>
                            <div class="customer-note">Not: {v['not']}</div>
                        </div>
                    """, unsafe_allow_html=True)

        st.divider()

        st.subheader("Müşteri Yönetim Paneli")
        st.write("Yeni bir müşteri eklemek veya var olanı güncellemek/silmek için formu doldurun.")
        
        panel_sol, panel_sag = st.columns([1, 1]) 
        with panel_sol:
            m_isim = st.text_input("Müşteri/Havayolu Adı:")
            m_logo = st.text_input("Logo URL (Boş bırakılabilir):", placeholder="https://...logo.png")
            m_puan = st.slider("Puan (1-10):", 1, 10, 7)
            m_not = st.text_area("Müşteri Notu:")

            btn_c1, btn_c2 = st.columns(2)
            if btn_c1.button("Kaydet / Güncelle", use_container_width=True):
                m_isim_temiz = m_isim.strip()
                if m_isim_temiz:
                    logo = m_logo if m_logo.strip() else "https://cdn-icons-png.flaticon.com/512/993/993888.png"
                    st.session_state["musteriler"][m_isim_temiz] = {"logo": logo, "puan": m_puan, "not": m_not}
                    musteri_kaydet(st.session_state["musteriler"]); st.success(f"'{m_isim_temiz}' kaydedildi!"); st.rerun()
                else: st.error("Lütfen bir müşteri adı girin.")
            
            if btn_c2.button("Müşteriyi Sil", use_container_width=True):
                m_isim_temiz = m_isim.strip()
                if m_isim_temiz in st.session_state["musteriler"]:
                    del st.session_state["musteriler"][m_isim_temiz]
                    musteri_kaydet(st.session_state["musteriler"]); st.warning(f"'{m_isim_temiz}' sistemden silindi."); st.rerun()
                else: st.error("Silinecek müşteri bulunamadı.")

    st.sidebar.divider()
    if st.sidebar.button("Verileri Yenile"):
        st.cache_data.clear(); st.rerun()
