from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import ImageTk
from app.services.fotograf_servisi import DESTEKLENEN_DOSYALAR, FotografServisi
from app.ui import tema
from app.ui.bilesenler import buton
from app.ui.yerlesim import SekmeDuzeni
from app.utils.sosyal_medya_oranlari import (
    GENEL_HAZIR_CIKTILAR,
    sosyal_medya_bilgisi_getir,
    sosyal_medya_hazir_ciktilari_getir,
    sosyal_medya_oran_adlari,
    sosyal_medya_orani_getir,
)


class FotografSekmesi(SekmeDuzeni):
    TUTAMAC_BOYUTU = 8

    def __init__(self, parent: ttk.Notebook, durum_guncelle) -> None:
        super().__init__(parent, "Fotoğraf Araçları", "Fotoğraf Önizleme")
        self.durum_guncelle = durum_guncelle
        self.fotograf_servisi = FotografServisi()
        self.onizleme_gorseli = None
        self.goruntu_alani = None
        self.kirpma_dikdortgeni = None
        self.kirpma_baslangici = None
        self.kirpma_modu = None
        self.filtre_onizleme_gorselleri = {}
        self.favori_filtreler = ["Orijinal", "Sepya", "Siyah Beyaz", "Keskinleştir"]
        self.onizleme_filtreleri = ["Orijinal", "Sepya", "Bulanıklaştır", "Kabartma"]
        self.boyut_guncelleniyor = False
        self.yakinlastirma_orani = 1.0
        self.ekrana_sigdir_modu = True
        self.goruntu_ofset_x = 0
        self.goruntu_ofset_y = 0
        self.goruntu_tasima_modu_var = tk.BooleanVar(value=False)
        self.goruntu_tasiniyor = False
        self.goruntu_tasima_baslangici = None

        self.boyut_metin = tk.StringVar(value="Boyut: -")
        self.dosya_metin = tk.StringVar(value="Dosya: -")
        self.mod_metin = tk.StringVar(value="Renk Modu: -")
        self.son_islem_var = tk.StringVar(value="Son işlem: Henüz işlem yapılmadı.")
        self.genislik_var = tk.StringVar(value="1280")
        self.yukseklik_var = tk.StringVar(value="720")
        self.orani_koru_var = tk.BooleanVar(value=True)
        self.kirp_x_var = tk.StringVar(value="0")
        self.kirp_y_var = tk.StringVar(value="0")
        self.kirp_genislik_var = tk.StringVar(value="400")
        self.kirp_yukseklik_var = tk.StringVar(value="400")
        self.kirp_orani_var = tk.StringVar(value="Serbest Oran")
        self.sosyal_medya_var = tk.StringVar(value=sosyal_medya_oran_adlari()[0])
        self.sosyal_medya_modu_var = tk.StringVar(value="Otomatik Kırp")
        self.sosyal_medya_oneri_var = tk.StringVar(value="Önerilen Boyut: -")
        self.sosyal_medya_cikti_var = tk.StringVar(value=GENEL_HAZIR_CIKTILAR[0])
        self.parlaklik_var = tk.DoubleVar(value=1.0)
        self.kontrast_var = tk.DoubleVar(value=1.0)
        self.doygunluk_var = tk.DoubleVar(value=1.0)
        self.keskinlik_var = tk.DoubleVar(value=1.0)
        self.ton_var = tk.DoubleVar(value=1.0)
        self.netlik_var = tk.DoubleVar(value=1.2)
        self.filtre_var = tk.StringVar(value="Orijinal")
        self.metin_icerik_var = tk.StringVar()
        self.metin_boyut_var = tk.StringVar(value="28")
        self.metin_renk_var = tk.StringVar(value="Beyaz")
        self.metin_taslagi = None
        self.metin_tasiniyor = False
        self.metin_renkleri = {"Beyaz": "#ffffff", "Siyah": "#111111", "Kırmızı": "#ff5a5a", "Mavi": "#5aa2ff", "Sarı": "#ffd54a", "Yeşil": "#67d38f"}
        self.cizim_araci_var = tk.StringVar(value="Kapalı")
        self.cizim_renk_var = tk.StringVar(value="Mavi")
        self.cizim_boyut_var = tk.StringVar(value="6")
        self.cizim_baslangici = None
        self.cizim_noktalari = []
        self.oge_listesi = []
        self.secili_oge_id = None
        self.son_oge_id = 0

        self._icerik_kur()
        self._sosyal_medya_bilgisini_guncelle()
        self._gecmis_gorunumunu_guncelle()
        self.genislik_var.trace_add("write", lambda *_: self._boyutu_esitle("genislik"))
        self.yukseklik_var.trace_add("write", lambda *_: self._boyutu_esitle("yukseklik"))
        self.sosyal_medya_var.trace_add("write", lambda *_: self._sosyal_medya_bilgisini_guncelle())
        self.onizleme_tuvali.bind("<Configure>", self._onizleme_yenile)
        self.onizleme_tuvali.bind("<ButtonPress-1>", self._kirpma_baslat)
        self.onizleme_tuvali.bind("<B1-Motion>", self._kirpma_surukle)
        self.onizleme_tuvali.bind("<ButtonRelease-1>", self._kirpma_birak)

    def _icerik_kur(self) -> None:
        self.arac_paneli.rowconfigure(99, weight=1)
        dosya = ttk.LabelFrame(self.arac_paneli, text="Dosya İşlemleri", style="Panel.TLabelframe")
        dosya.grid(row=1, column=0, sticky="ew", pady=(0, 12)); dosya.columnconfigure(0, weight=1)
        ttk.Label(dosya, text="Düzenlemek istediğiniz görseli açın ve sonucu kaydedin.", style="Aciklama.TLabel", wraplength=240, justify="left").grid(row=0, column=0, sticky="ew", pady=(0, 8))
        buton(dosya, "Fotoğraf Aç", self.fotograf_ac).grid(row=1, column=0, sticky="ew", pady=(0, 8))
        buton(dosya, "Kaydet", self.kaydet).grid(row=2, column=0, sticky="ew")
        buton(dosya, "Sıfırla", self.ayarlari_sifirla).grid(row=3, column=0, sticky="ew", pady=(8, 0))

        gecmis = ttk.LabelFrame(self.arac_paneli, text="Geçmiş", style="Panel.TLabelframe")
        gecmis.grid(row=2, column=0, sticky="ew", pady=(0, 12)); gecmis.columnconfigure((0, 1), weight=1)
        self.geri_al_butonu = buton(gecmis, "Geri Al", self.geri_al); self.geri_al_butonu.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.yinele_butonu = buton(gecmis, "Yinele", self.yinele); self.yinele_butonu.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        ttk.Label(gecmis, textvariable=self.son_islem_var, style="Aciklama.TLabel", wraplength=240, justify="left").grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 6))
        self.gecmis_liste_kutusu = tk.Listbox(gecmis, height=5, bg=tema.ONIZLEME_ZEMIN, fg=tema.METIN_RENGI, selectbackground=tema.VURGU_MAVI, selectforeground=tema.METIN_RENGI, highlightthickness=1, highlightbackground=tema.CERCEVE, relief="flat", activestyle="none")
        self.gecmis_liste_kutusu.grid(row=2, column=0, columnspan=2, sticky="ew")

        temel = ttk.LabelFrame(self.arac_paneli, text="Temel Dönüştürme", style="Panel.TLabelframe")
        temel.grid(row=3, column=0, sticky="ew", pady=(0, 12)); temel.columnconfigure((0, 1), weight=1)
        buton(temel, "Sola Döndür", lambda: self.dondur(90)).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        buton(temel, "Sağa Döndür", lambda: self.dondur(-90)).grid(row=0, column=1, sticky="ew", padx=(5, 0))
        buton(temel, "Yatay Çevir", self.yatay_cevir).grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(8, 0))
        buton(temel, "Dikey Çevir", self.dikey_cevir).grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(8, 0))

        gorunum = ttk.LabelFrame(self.arac_paneli, text="Görünüm", style="Panel.TLabelframe")
        gorunum.grid(row=4, column=0, sticky="ew", pady=(0, 12)); gorunum.columnconfigure((0, 1), weight=1)
        buton(gorunum, "Yakınlaştır", self.yakinlastir).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        buton(gorunum, "Uzaklaştır", self.uzaklastir).grid(row=0, column=1, sticky="ew", padx=(5, 0))
        buton(gorunum, "Ekrana Sığdır", self.ekrana_sigdir).grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(8, 0))
        buton(gorunum, "%100 Göster", self.orijinal_boyutta_goster).grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(8, 0))
        buton(gorunum, "Ortala", self.goruntuyu_ortala).grid(row=2, column=0, sticky="ew", padx=(0, 5), pady=(8, 0))
        ttk.Checkbutton(gorunum, text="Taşıma Modu", variable=self.goruntu_tasima_modu_var, command=self._tasima_modunu_degistir, style="Switch.TCheckbutton").grid(row=2, column=1, sticky="w", padx=(5, 0), pady=(8, 0))

        boyut = ttk.LabelFrame(self.arac_paneli, text="Yeniden Boyutlandır", style="Panel.TLabelframe")
        boyut.grid(row=5, column=0, sticky="ew", pady=(0, 12)); boyut.columnconfigure((0, 1), weight=1)
        ttk.Label(boyut, text="Piksel girerek boyutu güncelleyin.", style="Aciklama.TLabel", wraplength=240, justify="left").grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self._alan_olustur(boyut, "Genişlik", self.genislik_var, 1, 0)
        self._alan_olustur(boyut, "Yükseklik", self.yukseklik_var, 1, 1)
        ttk.Checkbutton(boyut, text="Oranı Koru", variable=self.orani_koru_var, style="Switch.TCheckbutton").grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 8))
        buton(boyut, "Boyutu Uygula", self.yeniden_boyutlandir).grid(row=4, column=0, columnspan=2, sticky="ew")

        kirp = ttk.LabelFrame(self.arac_paneli, text="Kırpma", style="Panel.TLabelframe")
        kirp.grid(row=6, column=0, sticky="ew", pady=(0, 12)); kirp.columnconfigure((0, 1), weight=1)
        ttk.Label(kirp, text="Önizlemede alan seçebilir veya oran belirleyebilirsiniz.", style="Aciklama.TLabel", wraplength=240, justify="left").grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(kirp, text="Kırpma Oranı", style="Genel.TLabel").grid(row=1, column=0, sticky="w")
        ttk.Combobox(kirp, textvariable=self.kirp_orani_var, values=["Serbest Oran", "1:1", "4:3", "16:9"], state="readonly", style="Karanlik.TCombobox").grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 8))
        self._alan_olustur(kirp, "Başlangıç X", self.kirp_x_var, 3, 0)
        self._alan_olustur(kirp, "Başlangıç Y", self.kirp_y_var, 3, 1)
        self._alan_olustur(kirp, "Genişlik", self.kirp_genislik_var, 5, 0)
        self._alan_olustur(kirp, "Yükseklik", self.kirp_yukseklik_var, 5, 1)
        buton(kirp, "Oranı Uygula", self.kirpma_oranini_uygula).grid(row=7, column=0, columnspan=2, sticky="ew", pady=(8, 6))
        buton(kirp, "Kırpmayı Uygula", self.kirp).grid(row=8, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        buton(kirp, "Kırpmayı Geri Al", self.kirpmayi_geri_al).grid(row=9, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        buton(kirp, "Seçimi Temizle", self.kirpma_secimini_temizle).grid(row=10, column=0, columnspan=2, sticky="ew")

        renk = ttk.LabelFrame(self.arac_paneli, text="Renk Ayarları", style="Panel.TLabelframe")
        renk.grid(row=7, column=0, sticky="ew", pady=(0, 12)); renk.columnconfigure(0, weight=1)
        self._kaydirici_olustur(renk, "Parlaklık", self.parlaklik_var, 0, 0.2, 2.5)
        self._kaydirici_olustur(renk, "Kontrast", self.kontrast_var, 2, 0.2, 2.5)
        self._kaydirici_olustur(renk, "Doygunluk", self.doygunluk_var, 4, 0.2, 2.5)
        self._kaydirici_olustur(renk, "Keskinlik", self.keskinlik_var, 6, 0.2, 3.0)
        self._kaydirici_olustur(renk, "Ton", self.ton_var, 8, 0.4, 2.0)
        buton(renk, "Renk Ayarlarını Uygula", self.ayarlari_uygula).grid(row=10, column=0, sticky="ew")

        netlik = ttk.LabelFrame(self.arac_paneli, text="Netleştirme", style="Panel.TLabelframe")
        netlik.grid(row=8, column=0, sticky="ew", pady=(0, 12)); netlik.columnconfigure(0, weight=1)
        ttk.Label(netlik, text="Bulanık fotoğraflarda detayları daha belirgin hale getirir.", style="Aciklama.TLabel", wraplength=240, justify="left").grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self._kaydirici_olustur(netlik, "Netlik Seviyesi", self.netlik_var, 1, 0.5, 3.0)
        buton(netlik, "Netleştir", self.netlestir).grid(row=3, column=0, sticky="ew", pady=(0, 6))
        buton(netlik, "Netleştirmeyi Geri Al", self.netlestirmeyi_geri_al).grid(row=4, column=0, sticky="ew")

        filtre = ttk.LabelFrame(self.arac_paneli, text="Filtreler", style="Panel.TLabelframe")
        filtre.grid(row=9, column=0, sticky="ew", pady=(0, 12)); filtre.columnconfigure(0, weight=1)
        ttk.Label(filtre, text="Tek adımda görünüm değişikliği uygulayın.", style="Aciklama.TLabel", wraplength=240, justify="left").grid(row=0, column=0, sticky="ew", pady=(0, 8))
        fav = ttk.Frame(filtre, style="Panel.TFrame"); fav.grid(row=1, column=0, sticky="ew", pady=(0, 8)); fav.columnconfigure((0, 1), weight=1)
        for i, ad in enumerate(self.favori_filtreler):
            buton(fav, ad, lambda secilen=ad: self.hizli_filtre_uygula(secilen)).grid(row=i // 2, column=i % 2, sticky="ew", padx=3, pady=3)
        ttk.Combobox(filtre, textvariable=self.filtre_var, values=["Orijinal", "Siyah Beyaz", "Sepya", "Bulanıklaştır", "Keskinleştir", "Kenar Güçlendir", "Kabartma", "Detay Artır", "Yumuşat", "Kontur", "Negatif", "Posterize"], state="readonly", style="Karanlik.TCombobox").grid(row=2, column=0, sticky="ew", pady=(0, 8))
        buton(filtre, "Filtreyi Uygula", self.filtre_uygula).grid(row=3, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(filtre, text="Hızlı önizleme için kartlara tıklayın.", style="Aciklama.TLabel", wraplength=240, justify="left").grid(row=4, column=0, sticky="w", pady=(0, 8))
        self.filtre_kart_alani = tk.Frame(filtre, bg=tema.IKINCIL_ARKA_PLAN); self.filtre_kart_alani.grid(row=5, column=0, sticky="ew"); self.filtre_kart_alani.grid_columnconfigure((0, 1), weight=1)
        self.filtre_kartlari = {}
        for i, ad in enumerate(self.onizleme_filtreleri):
            kart = tk.Label(self.filtre_kart_alani, text=ad, bg=tema.ONIZLEME_ZEMIN, fg=tema.METIN_RENGI, cursor="hand2", justify="center", relief="flat", bd=1, padx=6, pady=6)
            kart.grid(row=i // 2, column=i % 2, sticky="ew", padx=4, pady=4)
            kart.bind("<Button-1>", lambda _e, secilen=ad: self.hizli_filtre_uygula(secilen))
            self.filtre_kartlari[ad] = kart

        metin = ttk.LabelFrame(self.arac_paneli, text="Yazı Ekleme", style="Panel.TLabelframe")
        metin.grid(row=10, column=0, sticky="ew", pady=(0, 12)); metin.columnconfigure((0, 1), weight=1)
        ttk.Label(metin, text="Metni yazın, önizlemede taşıyın ve sonra görsele uygulayın.", style="Aciklama.TLabel", wraplength=240, justify="left").grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(metin, text="Metin", style="Genel.TLabel").grid(row=1, column=0, columnspan=2, sticky="w")
        ttk.Entry(metin, textvariable=self.metin_icerik_var, style="Karanlik.TEntry").grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 8))
        ttk.Label(metin, text="Yazı Boyutu", style="Genel.TLabel").grid(row=3, column=0, sticky="w")
        ttk.Combobox(metin, textvariable=self.metin_boyut_var, values=["18", "24", "28", "32", "40", "48"], state="readonly", style="Karanlik.TCombobox").grid(row=4, column=0, sticky="ew", padx=(0, 6), pady=(4, 8))
        ttk.Label(metin, text="Yazı Rengi", style="Genel.TLabel").grid(row=3, column=1, sticky="w")
        ttk.Combobox(metin, textvariable=self.metin_renk_var, values=list(self.metin_renkleri.keys()), state="readonly", style="Karanlik.TCombobox").grid(row=4, column=1, sticky="ew", pady=(4, 8))
        buton(metin, "Metni Hazırla", self.metin_taslagi_hazirla).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        buton(metin, "Metni Güncelle", self.metin_taslagi_guncelle).grid(row=6, column=0, sticky="ew", padx=(0, 5))
        buton(metin, "Metni Sil", self.metin_taslagi_sil).grid(row=6, column=1, sticky="ew", padx=(5, 0))
        buton(metin, "Metni Görsele Uygula", self.metni_uygula).grid(row=7, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        cizim = ttk.LabelFrame(self.arac_paneli, text="Çizim Araçları", style="Panel.TLabelframe")
        cizim.grid(row=11, column=0, sticky="ew", pady=(0, 12)); cizim.columnconfigure((0, 1), weight=1)
        ttk.Label(cizim, text="Araç", style="Genel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Combobox(cizim, textvariable=self.cizim_araci_var, values=["Kapalı", "Serbest Çizim", "Silgi", "Düz Çizgi", "Dikdörtgen", "Daire", "Ok"], state="readonly", style="Karanlik.TCombobox").grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 8))
        ttk.Label(cizim, text="Renk", style="Genel.TLabel").grid(row=2, column=0, sticky="w")
        ttk.Combobox(cizim, textvariable=self.cizim_renk_var, values=list(self.metin_renkleri.keys()), state="readonly", style="Karanlik.TCombobox").grid(row=3, column=0, sticky="ew", padx=(0, 6), pady=(4, 8))
        ttk.Label(cizim, text="Fırça Boyutu", style="Genel.TLabel").grid(row=2, column=1, sticky="w")
        ttk.Combobox(cizim, textvariable=self.cizim_boyut_var, values=["2", "4", "6", "8", "12", "16"], state="readonly", style="Karanlik.TCombobox").grid(row=3, column=1, sticky="ew", pady=(4, 8))
        ttk.Label(cizim, text="Araç seçiliyse önizlemede sürükleyerek çizebilirsiniz.", style="Aciklama.TLabel", wraplength=240, justify="left").grid(row=4, column=0, columnspan=2, sticky="ew")

        ogeler = ttk.LabelFrame(self.arac_paneli, text="Öğe Listesi", style="Panel.TLabelframe")
        ogeler.grid(row=12, column=0, sticky="ew", pady=(0, 12)); ogeler.columnconfigure((0, 1), weight=1)
        ttk.Label(ogeler, text="Metin ve çizim öğelerini buradan seçebilir, gizleyebilir veya silebilirsiniz.", style="Aciklama.TLabel", wraplength=240, justify="left").grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.oge_liste_kutusu = tk.Listbox(ogeler, height=6, bg=tema.ONIZLEME_ZEMIN, fg=tema.METIN_RENGI, selectbackground=tema.VURGU_MAVI, selectforeground=tema.METIN_RENGI, highlightthickness=1, highlightbackground=tema.CERCEVE, relief="flat", activestyle="none")
        self.oge_liste_kutusu.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.oge_liste_kutusu.bind("<<ListboxSelect>>", self._oge_secimini_degisti)
        buton(ogeler, "Gizle / Göster", self.secili_ogeyi_gizle_goster).grid(row=2, column=0, sticky="ew", padx=(0, 5))
        buton(ogeler, "Seçili Öğeyi Sil", self.secili_ogeyi_sil).grid(row=2, column=1, sticky="ew", padx=(5, 0))
        buton(ogeler, "Görünen Öğeleri Uygula", self.gorunen_ogeleri_uygula).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        bilgi = ttk.LabelFrame(self.arac_paneli, text="Fotoğraf Bilgisi", style="Panel.TLabelframe")
        bilgi.grid(row=13, column=0, sticky="ew"); bilgi.columnconfigure(0, weight=1)
        ttk.Label(bilgi, textvariable=self.dosya_metin, style="Genel.TLabel", wraplength=220).grid(row=0, column=0, sticky="w", pady=(0, 4))
        ttk.Label(bilgi, textvariable=self.boyut_metin, style="Genel.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Label(bilgi, textvariable=self.mod_metin, style="Genel.TLabel").grid(row=2, column=0, sticky="w", pady=(4, 0))

        sosyal = ttk.LabelFrame(self.arac_paneli, text="Sosyal Medya Oranları", style="Panel.TLabelframe")
        sosyal.grid(row=14, column=0, sticky="ew", pady=(12, 0)); sosyal.columnconfigure((0, 1), weight=1)
        ttk.Label(sosyal, text="Instagram, Facebook ve X için hazır oranlara hızlıca geçebilirsiniz.", style="Aciklama.TLabel", wraplength=240, justify="left").grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(sosyal, text="Hazır Oran", style="Genel.TLabel").grid(row=1, column=0, columnspan=2, sticky="w")
        ttk.Combobox(sosyal, textvariable=self.sosyal_medya_var, values=sosyal_medya_oran_adlari(), state="readonly", style="Karanlik.TCombobox").grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 8))
        ttk.Label(sosyal, text="Uygulama Yöntemi", style="Genel.TLabel").grid(row=3, column=0, columnspan=2, sticky="w")
        ttk.Combobox(sosyal, textvariable=self.sosyal_medya_modu_var, values=["Otomatik Kırp", "Kırpmadan Sığdır"], state="readonly", style="Karanlik.TCombobox").grid(row=4, column=0, columnspan=2, sticky="ew", pady=(4, 8))
        ttk.Label(sosyal, textvariable=self.sosyal_medya_oneri_var, style="Aciklama.TLabel", wraplength=240, justify="left").grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(sosyal, text="Hazır Çıktı Boyutu", style="Genel.TLabel").grid(row=6, column=0, columnspan=2, sticky="w")
        self.sosyal_medya_cikti_kutusu = ttk.Combobox(sosyal, textvariable=self.sosyal_medya_cikti_var, values=GENEL_HAZIR_CIKTILAR, state="readonly", style="Karanlik.TCombobox")
        self.sosyal_medya_cikti_kutusu.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(4, 8))
        buton(sosyal, "Oranı Önizlemeye Hazırla", self.sosyal_medya_onizleme_hazirla).grid(row=8, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        buton(sosyal, "Seçili Oranı Uygula", self.sosyal_medya_oranini_uygula).grid(row=9, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        buton(sosyal, "Çıktı Boyutunu Uygula", self.sosyal_medya_cikti_boyutunu_uygula).grid(row=10, column=0, columnspan=2, sticky="ew")

    def _alan_olustur(self, parent, etiket, degisken, satir, sutun):
        ttk.Label(parent, text=etiket, style="Genel.TLabel").grid(row=satir, column=sutun, sticky="w", padx=(0, 6), pady=(0, 4))
        giris = ttk.Entry(parent, textvariable=degisken, style="Karanlik.TEntry", width=10)
        giris.grid(row=satir + 1, column=sutun, sticky="ew", padx=(0, 6 if sutun == 0 else 0), pady=(0, 6))
        return giris

    def _kaydirici_olustur(self, parent, etiket, degisken, satir, baslangic, bitis):
        ttk.Label(parent, text=etiket, style="Genel.TLabel").grid(row=satir, column=0, sticky="w")
        ttk.Scale(parent, from_=baslangic, to=bitis, variable=degisken, orient="horizontal", style="Karanlik.Horizontal.TScale").grid(row=satir + 1, column=0, sticky="ew", pady=(4, 8))

    def _boyutu_esitle(self, kaynak: str) -> None:
        if self.boyut_guncelleniyor or not self.orani_koru_var.get():
            return
        gorsel = self.fotograf_servisi.calisma_gorseli
        if gorsel is None:
            return
        try:
            genislik = int(self.genislik_var.get()); yukseklik = int(self.yukseklik_var.get())
        except ValueError:
            return
        if genislik <= 0 or yukseklik <= 0:
            return
        self.boyut_guncelleniyor = True
        try:
            if kaynak == "genislik":
                self.yukseklik_var.set(str(max(1, round(genislik * gorsel.height / gorsel.width))))
            else:
                self.genislik_var.set(str(max(1, round(yukseklik * gorsel.width / gorsel.height))))
        finally:
            self.boyut_guncelleniyor = False

    def _varsayilan_form_degerlerini_uygula(self, gorsel) -> None:
        self.boyut_guncelleniyor = True
        try:
            self.genislik_var.set(str(gorsel.width)); self.yukseklik_var.set(str(gorsel.height))
        finally:
            self.boyut_guncelleniyor = False
        self.yakinlastirma_orani = 1.0
        self.ekrana_sigdir_modu = True
        self.goruntu_ofset_x = 0
        self.goruntu_ofset_y = 0
        self.metin_taslagi = None
        self.metin_icerik_var.set("")
        self.metin_boyut_var.set("28")
        self.metin_renk_var.set("Beyaz")
        self.cizim_araci_var.set("Kapalı")
        self.cizim_renk_var.set("Mavi")
        self.cizim_boyut_var.set("6")
        self.cizim_baslangici = None
        self.cizim_noktalari = []
        self._bekleyen_ogeleri_temizle()
        self.kirp_x_var.set("0"); self.kirp_y_var.set("0")
        self.kirp_genislik_var.set(str(min(400, gorsel.width))); self.kirp_yukseklik_var.set(str(min(400, gorsel.height)))
        self.kirp_orani_var.set("Serbest Oran")
        self.sosyal_medya_var.set(sosyal_medya_oran_adlari()[0])
        self.sosyal_medya_modu_var.set("Otomatik Kırp")
        self.sosyal_medya_cikti_var.set(GENEL_HAZIR_CIKTILAR[0])
        self.parlaklik_var.set(1.0); self.kontrast_var.set(1.0); self.doygunluk_var.set(1.0); self.keskinlik_var.set(1.0); self.ton_var.set(1.0); self.netlik_var.set(1.2); self.filtre_var.set("Orijinal")

    def fotograf_ac(self) -> None:
        self.durum_guncelle("Fotoğraf seçiliyor...")
        dosya_yolu = filedialog.askopenfilename(title="Fotoğraf Aç", filetypes=DESTEKLENEN_DOSYALAR)
        if not dosya_yolu:
            self.durum_guncelle("Fotoğraf seçimi iptal edildi."); return
        try:
            gorsel = self.fotograf_servisi.ac(dosya_yolu)
        except Exception as hata:
            self._hata_goster(f"Fotoğraf açılamadı: {hata}"); return
        self._varsayilan_form_degerlerini_uygula(gorsel); self._bilgileri_guncelle(); self.kirpma_secimini_temizle(yalnizca_goruntu=False); self._onizleme_yenile(); self._filtre_onizlemelerini_guncelle(); self._durum_yaz("Fotoğraf açıldı. Düzenleme araçları artık kullanılabilir.")

    def kaydet(self) -> None:
        if not self._gorsel_var_mi(): return
        self._varsa_bekleyen_ogeleri_uygula()
        self._onizleme_yenile()
        self.durum_guncelle("Kaydetme konumu seçiliyor...")
        dosya_yolu = filedialog.asksaveasfilename(title="Fotoğrafı Kaydet", defaultextension=".png", filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg"), ("BMP", "*.bmp"), ("WEBP", "*.webp")])
        if not dosya_yolu:
            self.durum_guncelle("Kaydetme işlemi iptal edildi. Mevcut değişiklikler korunuyor."); return
        try:
            self.fotograf_servisi.kaydet(dosya_yolu)
        except Exception as hata:
            self._hata_goster(f"Kaydetme sırasında hata oluştu: {hata}"); return
        self._durum_yaz("Fotoğraf başarıyla kaydedildi.")

    def ayarlari_sifirla(self) -> None:
        if not self._gorsel_var_mi(): return
        try:
            gorsel = self.fotograf_servisi.sifirla()
        except Exception as hata:
            self._hata_goster(str(hata)); return
        self._varsayilan_form_degerlerini_uygula(gorsel); self.kirpma_secimini_temizle(yalnizca_goruntu=False); self._bilgileri_guncelle(); self._onizleme_yenile(); self._filtre_onizlemelerini_guncelle(); self._durum_yaz("Fotoğraf ve ayarlar başlangıç durumuna sıfırlandı.")

    def geri_al(self) -> None:
        if not self._gorsel_var_mi(): return
        try:
            gorsel = self.fotograf_servisi.geri_al()
        except Exception as hata:
            self._hata_goster(str(hata)); return
        self._islem_sonrasi_guncelle(gorsel, "Son işlem geri alındı.")

    def yinele(self) -> None:
        if not self._gorsel_var_mi(): return
        try:
            gorsel = self.fotograf_servisi.yinele()
        except Exception as hata:
            self._hata_goster(str(hata)); return
        self._islem_sonrasi_guncelle(gorsel, "Son işlem yeniden uygulandı.")

    def dondur(self, derece: float) -> None: self._islem_calistir(lambda: self.fotograf_servisi.dondur(derece), f"Fotoğraf {'sola' if derece > 0 else 'sağa'} döndürüldü.")
    def yatay_cevir(self) -> None: self._islem_calistir(self.fotograf_servisi.yatay_cevir, "Fotoğraf yatay olarak çevrildi.")
    def dikey_cevir(self) -> None: self._islem_calistir(self.fotograf_servisi.dikey_cevir, "Fotoğraf dikey olarak çevrildi.")

    def yakinlastir(self) -> None:
        if not self._gorsel_var_mi(): return
        self.ekrana_sigdir_modu = False
        self.yakinlastirma_orani = min(8.0, self.yakinlastirma_orani * 1.25)
        self._onizleme_yenile()
        self._durum_yaz(f"Görünüm yakınlaştırıldı. Ölçek: %{int(self.yakinlastirma_orani * 100)}")

    def uzaklastir(self) -> None:
        if not self._gorsel_var_mi(): return
        self.ekrana_sigdir_modu = False
        self.yakinlastirma_orani = max(0.1, self.yakinlastirma_orani / 1.25)
        self._onizleme_yenile()
        self._durum_yaz(f"Görünüm uzaklaştırıldı. Ölçek: %{int(self.yakinlastirma_orani * 100)}")

    def ekrana_sigdir(self) -> None:
        if not self._gorsel_var_mi(): return
        self.ekrana_sigdir_modu = True
        self.goruntu_ofset_x = 0
        self.goruntu_ofset_y = 0
        self._onizleme_yenile()
        self._durum_yaz("Görsel ekrana sığdırıldı.")

    def orijinal_boyutta_goster(self) -> None:
        if not self._gorsel_var_mi(): return
        self.ekrana_sigdir_modu = False
        self.yakinlastirma_orani = 1.0
        self.goruntu_ofset_x = 0
        self.goruntu_ofset_y = 0
        self._onizleme_yenile()
        self._durum_yaz("Görsel %100 boyutta gösteriliyor.")

    def goruntuyu_ortala(self) -> None:
        if not self._gorsel_var_mi(): return
        self.goruntu_ofset_x = 0
        self.goruntu_ofset_y = 0
        self._onizleme_yenile()
        self._durum_yaz("Görsel önizleme alanında ortalandı.")

    def _tasima_modunu_degistir(self) -> None:
        durum = "açıldı" if self.goruntu_tasima_modu_var.get() else "kapatıldı"
        self._durum_yaz(f"Taşıma modu {durum}.")

    def metin_taslagi_hazirla(self) -> None:
        if not self._gorsel_var_mi(): return
        metin = self.metin_icerik_var.get().strip()
        if not metin:
            self._hata_goster("Lütfen önce eklenecek metni yazın."); return
        try:
            boyut = int(self.metin_boyut_var.get())
        except ValueError:
            self._hata_goster("Yazı boyutu için geçerli bir sayı seçin."); return
        oge = self._secili_ogeyi_getir()
        if oge is not None and oge.get("tur") == "metin":
            oge["metin"] = metin
            oge["boyut"] = boyut
            oge["renk"] = self.metin_renkleri.get(self.metin_renk_var.get(), "#ffffff")
            oge["gorunur"] = True
            self.metin_taslagi = oge
            self._oge_listesini_guncelle()
            self._onizleme_yenile(); self._durum_yaz("Seçili metin öğesi güncellendi.")
            return
        gorsel = self.fotograf_servisi.calisma_gorseli
        oge = {
            "id": self._yeni_oge_id(),
            "tur": "metin",
            "ad": self._yeni_oge_adi("Metin", "metin"),
            "metin": metin,
            "boyut": boyut,
            "renk": self.metin_renkleri.get(self.metin_renk_var.get(), "#ffffff"),
            "x": max(10, gorsel.width // 4),
            "y": max(10, gorsel.height // 4),
            "gorunur": True,
        }
        self.oge_listesi.append(oge)
        self.metin_taslagi = oge
        self._ogeyi_sec(oge["id"])
        self._durum_yaz("Metin öğesi eklendi. Önizlemede sürükleyerek konumlandırabilirsiniz.")

    def metin_taslagi_guncelle(self) -> None:
        oge = self._secili_ogeyi_getir()
        if oge is None or oge.get("tur") != "metin":
            self.metin_taslagi_hazirla(); return
        metin = self.metin_icerik_var.get().strip()
        if not metin:
            self._hata_goster("Lütfen önce eklenecek metni yazın."); return
        try:
            boyut = int(self.metin_boyut_var.get())
        except ValueError:
            self._hata_goster("Yazı boyutu için geçerli bir sayı seçin."); return
        oge["metin"] = metin; oge["boyut"] = boyut; oge["renk"] = self.metin_renkleri.get(self.metin_renk_var.get(), "#ffffff")
        self.metin_taslagi = oge
        self._oge_listesini_guncelle()
        self._onizleme_yenile(); self._durum_yaz("Metin öğesi güncellendi.")

    def metin_taslagi_sil(self) -> None:
        oge = self._secili_ogeyi_getir()
        if oge is None or oge.get("tur") != "metin":
            self._hata_goster("Silinecek bir metin öğesi bulunmuyor."); return
        self.secili_ogeyi_sil()

    def metni_uygula(self) -> None:
        if not self._gorsel_var_mi(): return
        oge = self._secili_ogeyi_getir()
        if oge is None or oge.get("tur") != "metin":
            self._hata_goster("Önce bir metin öğesi seçin."); return
        self._islem_calistir(lambda: self.fotograf_servisi.metin_ekle(oge["metin"], int(oge["x"]), int(oge["y"]), int(oge["boyut"]), oge["renk"]), "Metin görsele uygulandı.", ogeleri_uygula_once=False)
        self._ogeyi_listeden_kaldir(oge["id"])

    def secili_ogeyi_gizle_goster(self) -> None:
        oge = self._secili_ogeyi_getir()
        if oge is None:
            self._hata_goster("Önce listeden bir öğe seçin."); return
        oge["gorunur"] = not oge.get("gorunur", True)
        self._oge_listesini_guncelle()
        self._onizleme_yenile()
        self._durum_yaz(f"{oge['ad']} için görünürlük güncellendi.")

    def secili_ogeyi_sil(self) -> None:
        oge = self._secili_ogeyi_getir()
        if oge is None:
            self._hata_goster("Silmek için önce listeden bir öğe seçin."); return
        ad = oge["ad"]
        self._ogeyi_listeden_kaldir(oge["id"])
        self._durum_yaz(f"{ad} silindi.")

    def gorunen_ogeleri_uygula(self) -> None:
        if not self._gorsel_var_mi(): return
        gorunenler = [oge.copy() for oge in self.oge_listesi if oge.get("gorunur", True)]
        if not gorunenler:
            self._hata_goster("Görsele uygulanacak görünür bir öğe bulunmuyor."); return
        self._islem_calistir(lambda: self.fotograf_servisi.ogeleri_uygula(gorunenler), f"{len(gorunenler)} öğe görsele uygulandı.", ogeleri_uygula_once=False)
        uygulanan_kimlikler = {oge["id"] for oge in gorunenler}
        self.oge_listesi = [oge for oge in self.oge_listesi if oge.get("id") not in uygulanan_kimlikler]
        if self.secili_oge_id in uygulanan_kimlikler:
            self.secili_oge_id = None
            self.metin_taslagi = None
        self._oge_listesini_guncelle()
        self._onizleme_yenile()

    def _yeni_oge_id(self) -> int:
        self.son_oge_id += 1
        return self.son_oge_id

    def _yeni_oge_adi(self, onek: str, tur: str | None = None) -> str:
        hedef_tur = tur or onek.lower()
        adet = sum(1 for oge in self.oge_listesi if oge.get("tur") == hedef_tur)
        return f"{onek} {adet + 1}"

    def _secili_ogeyi_getir(self):
        for oge in self.oge_listesi:
            if oge.get("id") == self.secili_oge_id:
                return oge
        return None

    def _ogeyi_sec(self, oge_id: int | None) -> None:
        self.secili_oge_id = oge_id
        oge = self._secili_ogeyi_getir()
        self.metin_taslagi = oge if oge and oge.get("tur") == "metin" else None
        self._oge_listesini_guncelle()
        if oge and oge.get("tur") == "metin":
            self.metin_icerik_var.set(oge.get("metin", ""))
            self.metin_boyut_var.set(str(oge.get("boyut", 28)))
            secili_renk = next((ad for ad, kod in self.metin_renkleri.items() if kod == oge.get("renk")), "Beyaz")
            self.metin_renk_var.set(secili_renk)
        self._onizleme_yenile()

    def _ogeyi_listeden_kaldir(self, oge_id: int) -> None:
        self.oge_listesi = [oge for oge in self.oge_listesi if oge.get("id") != oge_id]
        if self.secili_oge_id == oge_id:
            self.secili_oge_id = None
            self.metin_taslagi = None
        self._oge_listesini_guncelle()
        self._onizleme_yenile()

    def _oge_listesini_guncelle(self) -> None:
        if not hasattr(self, "oge_liste_kutusu"):
            return
        self.oge_liste_kutusu.delete(0, tk.END)
        secim_indeksi = None
        for indeks, oge in enumerate(self.oge_listesi):
            durum = "Açık" if oge.get("gorunur", True) else "Gizli"
            self.oge_liste_kutusu.insert(tk.END, f"[{durum}] {oge.get('ad', 'Öğe')}")
            if oge.get("id") == self.secili_oge_id:
                secim_indeksi = indeks
        if secim_indeksi is not None:
            self.oge_liste_kutusu.selection_set(secim_indeksi)
            self.oge_liste_kutusu.activate(secim_indeksi)

    def _oge_secimini_degisti(self, _event=None) -> None:
        if not hasattr(self, "oge_liste_kutusu"):
            return
        secim = self.oge_liste_kutusu.curselection()
        if not secim:
            return
        oge = self.oge_listesi[secim[0]]
        self.secili_oge_id = oge["id"]
        self.metin_taslagi = oge if oge.get("tur") == "metin" else None
        if oge.get("tur") == "metin":
            self.metin_icerik_var.set(oge.get("metin", ""))
            self.metin_boyut_var.set(str(oge.get("boyut", 28)))
            secili_renk = next((ad for ad, kod in self.metin_renkleri.items() if kod == oge.get("renk")), "Beyaz")
            self.metin_renk_var.set(secili_renk)
        elif oge.get("tur") == "cizim":
            self.cizim_araci_var.set(oge.get("arac", "Kapalı"))
            self.cizim_boyut_var.set(str(oge.get("kalinlik", 6)))
            secili_renk = next((ad for ad, kod in self.metin_renkleri.items() if kod == oge.get("renk")), "Mavi")
            self.cizim_renk_var.set(secili_renk)
        self._onizleme_yenile()

    def _bekleyen_ogeleri_temizle(self) -> None:
        self.oge_listesi.clear()
        self.secili_oge_id = None
        self.metin_taslagi = None
        self._oge_listesini_guncelle()

    def _varsa_bekleyen_ogeleri_uygula(self) -> None:
        if not self.oge_listesi:
            return
        gorunenler = [oge.copy() for oge in self.oge_listesi if oge.get("gorunur", True)]
        if gorunenler:
            self.fotograf_servisi.ogeleri_uygula(gorunenler)
        uygulanan_kimlikler = {oge["id"] for oge in gorunenler}
        self.oge_listesi = [oge for oge in self.oge_listesi if oge.get("id") not in uygulanan_kimlikler]
        if self.secili_oge_id in uygulanan_kimlikler:
            self.secili_oge_id = None
            self.metin_taslagi = None
        self._oge_listesini_guncelle()

    def yeniden_boyutlandir(self) -> None:
        try:
            genislik = int(self.genislik_var.get()); yukseklik = int(self.yukseklik_var.get())
        except ValueError:
            self._hata_goster("Boyut alanlarına geçerli sayılar girin."); return
        self._islem_calistir(lambda: self.fotograf_servisi.yeniden_boyutlandir(genislik, yukseklik), "Fotoğrafın boyutu güncellendi.")

    def _oran_degerini_getir(self):
        return {"1:1": (1, 1), "4:3": (4, 3), "16:9": (16, 9)}.get(self.kirp_orani_var.get())

    def kirpma_oranini_uygula(self) -> None:
        if not self._gorsel_var_mi(): return
        if self.kirp_orani_var.get() == "Serbest Oran":
            self._durum_yaz("Serbest oran etkin. Kırpma alanını dilediğiniz gibi ayarlayabilirsiniz."); return
        try:
            x = int(self.kirp_x_var.get()); y = int(self.kirp_y_var.get()); genislik = int(self.kirp_genislik_var.get()); yukseklik = int(self.kirp_yukseklik_var.get())
        except ValueError:
            self._hata_goster("Kırpma alanlarına geçerli sayılar girin."); return
        self._kirpma_olculerini_orana_gore_duzelt(x, y, genislik, yukseklik); self._onizleme_yenile(); self._durum_yaz(f"{self.kirp_orani_var.get()} kırpma oranı uygulandı.")

    def sosyal_medya_onizleme_hazirla(self) -> None:
        if not self._gorsel_var_mi(): return
        oran_x, oran_y = sosyal_medya_orani_getir(self.sosyal_medya_var.get())
        x, y, genislik, yukseklik = self._merkezden_oran_hesapla(oran_x, oran_y)
        self.kirp_x_var.set(str(x)); self.kirp_y_var.set(str(y)); self.kirp_genislik_var.set(str(genislik)); self.kirp_yukseklik_var.set(str(yukseklik))
        self._kirpma_dikdortgenini_verilerden_guncelle()
        self._onizleme_yenile()
        if self.sosyal_medya_modu_var.get() == "Kırpmadan Sığdır":
            self._durum_yaz(f"{self.sosyal_medya_var.get()} için merkezleme hazırlandı. Uygulandığında arka plan dolgusu eklenecek.")
        else:
            self._durum_yaz(f"{self.sosyal_medya_var.get()} için otomatik kırpma alanı önizlemeye yerleştirildi.")

    def sosyal_medya_cikti_boyutunu_uygula(self) -> None:
        if not self._gorsel_var_mi(): return
        try:
            genislik_str, yukseklik_str = self.sosyal_medya_cikti_var.get().lower().split("x")
            genislik = int(genislik_str)
            yukseklik = int(yukseklik_str)
        except ValueError:
            self._hata_goster("Hazır çıktı boyutu çözümlenemedi."); return
        self._islem_calistir(lambda: self.fotograf_servisi.yeniden_boyutlandir(genislik, yukseklik), f"Çıktı boyutu {genislik}x{yukseklik} olarak uygulandı.")

    def sosyal_medya_oranini_uygula(self) -> None:
        if not self._gorsel_var_mi(): return
        oran_x, oran_y = sosyal_medya_orani_getir(self.sosyal_medya_var.get())
        if self.sosyal_medya_modu_var.get() == "Kırpmadan Sığdır":
            self._islem_calistir(lambda: self.fotograf_servisi.kirpmadan_orana_sigdir(oran_x, oran_y), f"{self.sosyal_medya_var.get()} oranı kırpmadan uygulandı.")
        else:
            self._islem_calistir(lambda: self.fotograf_servisi.orana_gore_ortadan_kirp(oran_x, oran_y), f"{self.sosyal_medya_var.get()} için otomatik kırpma uygulandı.")

    def _merkezden_oran_hesapla(self, oran_x: int, oran_y: int) -> tuple[int, int, int, int]:
        gorsel = self.fotograf_servisi.calisma_gorseli
        if gorsel is None:
            return 0, 0, 0, 0
        hedef_oran = oran_x / oran_y
        mevcut_oran = gorsel.width / gorsel.height
        if mevcut_oran > hedef_oran:
            genislik = max(1, round(gorsel.height * hedef_oran))
            yukseklik = gorsel.height
        else:
            genislik = gorsel.width
            yukseklik = max(1, round(gorsel.width / hedef_oran))
        x = max(0, (gorsel.width - genislik) // 2)
        y = max(0, (gorsel.height - yukseklik) // 2)
        return x, y, genislik, yukseklik

    def _sosyal_medya_bilgisini_guncelle(self) -> None:
        bilgi = sosyal_medya_bilgisi_getir(self.sosyal_medya_var.get())
        self.sosyal_medya_oneri_var.set(f"Önerilen Boyut: {bilgi['onerilen_boyut']}")
        hazirlar = sosyal_medya_hazir_ciktilari_getir(self.sosyal_medya_var.get())
        if hasattr(self, "sosyal_medya_cikti_kutusu"):
            self.sosyal_medya_cikti_kutusu.configure(values=hazirlar)
        if self.sosyal_medya_cikti_var.get() not in hazirlar:
            self.sosyal_medya_cikti_var.set(hazirlar[0])
        if self.fotograf_servisi.calisma_gorseli is not None:
            self._durum_yaz("Sosyal medya oranı güncellendi.")

    def kirp(self) -> None:
        try:
            x = int(self.kirp_x_var.get()); y = int(self.kirp_y_var.get()); genislik = int(self.kirp_genislik_var.get()); yukseklik = int(self.kirp_yukseklik_var.get())
        except ValueError:
            self._hata_goster("Kırpma alanlarına geçerli sayılar girin."); return
        self._islem_calistir(lambda: self.fotograf_servisi.kirp(x, y, genislik, yukseklik), "Fotoğraf kırpıldı.")

    def kirpmayi_geri_al(self) -> None:
        if not self._gorsel_var_mi(): return
        try:
            gorsel = self.fotograf_servisi.son_kirpmayi_geri_al()
        except Exception as hata:
            self._hata_goster(str(hata)); return
        self._islem_sonrasi_guncelle(gorsel, "Son kırpma işlemi geri alındı.")

    def ayarlari_uygula(self) -> None:
        self._islem_calistir(lambda: self.fotograf_servisi.renk_ayarlari_uygula(self.parlaklik_var.get(), self.kontrast_var.get(), self.doygunluk_var.get(), self.keskinlik_var.get(), self.ton_var.get()), "Parlaklık, kontrast, doygunluk, keskinlik ve ton ayarları uygulandı.")

    def netlestir(self) -> None: self._islem_calistir(lambda: self.fotograf_servisi.netlestir(self.netlik_var.get()), "Fotoğraf netleştirildi.")

    def netlestirmeyi_geri_al(self) -> None:
        if not self._gorsel_var_mi(): return
        try:
            gorsel = self.fotograf_servisi.netlestirmeyi_geri_al()
        except Exception as hata:
            self._hata_goster(str(hata)); return
        self._islem_sonrasi_guncelle(gorsel, "Son netleştirme işlemi geri alındı.")

    def filtre_uygula(self) -> None:
        self._islem_calistir(lambda: self.fotograf_servisi.filtre_uygula(self.filtre_var.get()), f"{self.filtre_var.get()} filtresi uygulandı.")

    def hizli_filtre_uygula(self, filtre_adi: str) -> None:
        self.filtre_var.set(filtre_adi); self.filtre_uygula()

    def _islem_calistir(self, islem, basari_mesaji: str, ogeleri_uygula_once: bool = True) -> None:
        if not self._gorsel_var_mi(): return
        if ogeleri_uygula_once:
            if self.oge_listesi:
                self._hata_goster("Bu işlemi yapmadan önce bekleyen öğeleri listeden görsele uygulayın ya da silin."); return
        try:
            gorsel = islem()
        except Exception as hata:
            self._hata_goster(str(hata)); return
        self._islem_sonrasi_guncelle(gorsel, basari_mesaji)

    def _islem_sonrasi_guncelle(self, gorsel, mesaj: str) -> None:
        self.boyut_guncelleniyor = True
        try:
            self.genislik_var.set(str(gorsel.width)); self.yukseklik_var.set(str(gorsel.height))
        finally:
            self.boyut_guncelleniyor = False
        self.secili_oge_id = None
        self.metin_taslagi = None
        self.cizim_baslangici = None
        self.cizim_noktalari = []
        self._oge_listesini_guncelle()
        self.kirpma_secimini_temizle(yalnizca_goruntu=False); self._bilgileri_guncelle(); self._onizleme_yenile(); self._filtre_onizlemelerini_guncelle(); self._durum_yaz(mesaj)

    def _durum_yaz(self, mesaj: str) -> None:
        dosya = self.fotograf_servisi.kaynak_yol.name if self.fotograf_servisi.kaynak_yol else "Dosya yok"
        gecmis = self.fotograf_servisi.gecmis_bilgisi(); son_islem = self.fotograf_servisi.son_islem_metni
        sosyal = self.sosyal_medya_var.get()
        oneri = self.sosyal_medya_oneri_var.get().replace("Önerilen Boyut: ", "")
        cikti = self.sosyal_medya_cikti_var.get()
        self._gecmis_gorunumunu_guncelle(); self.son_islem_var.set(f"Son işlem: {son_islem}")
        self.durum_guncelle(f"{mesaj} | Aktif dosya: {dosya} | {gecmis} | Öğe: {len(self.oge_listesi)} | Sosyal oran: {sosyal} | Önerilen boyut: {oneri} | Hazır çıktı: {cikti} | Son işlem: {son_islem}")

    def _gecmis_gorunumunu_guncelle(self) -> None:
        if not hasattr(self, "gecmis_liste_kutusu"): return
        self.gecmis_liste_kutusu.delete(0, tk.END)
        kayitlar = self.fotograf_servisi.islem_gecmisi()
        for kayit in reversed(kayitlar or ["Henüz işlem yok."]): self.gecmis_liste_kutusu.insert(tk.END, kayit)
        self.geri_al_butonu.state(["!disabled"] if self.fotograf_servisi.geri_al_yigini else ["disabled"])
        self.yinele_butonu.state(["!disabled"] if self.fotograf_servisi.yinele_yigini else ["disabled"])

    def _gorsel_var_mi(self, sessiz: bool = False) -> bool:
        if self.fotograf_servisi.calisma_gorseli is None:
            if not sessiz: self._hata_goster("Bu işlemi yapabilmek için önce bir fotoğraf açmalısınız.")
            return False
        return True

    def _bilgileri_guncelle(self) -> None:
        bilgiler = self.fotograf_servisi.bilgileri_getir()
        self.dosya_metin.set(f"Dosya: {bilgiler['dosya']}"); self.boyut_metin.set(f"Boyut: {bilgiler['boyut']}"); self.mod_metin.set(f"Renk Modu: {bilgiler['mod']}")

    def _kirpma_olculerini_orana_gore_duzelt(self, x: int, y: int, genislik: int, yukseklik: int) -> None:
        gorsel = self.fotograf_servisi.calisma_gorseli; oran = self._oran_degerini_getir()
        if gorsel is None or oran is None: return
        ow, oh = oran; genislik = max(1, genislik); yukseklik = max(1, yukseklik)
        if genislik / yukseklik >= ow / oh: yukseklik = max(1, round(genislik * oh / ow))
        else: genislik = max(1, round(yukseklik * ow / oh))
        if x + genislik > gorsel.width:
            genislik = max(1, gorsel.width - x); yukseklik = max(1, round(genislik * oh / ow))
        if y + yukseklik > gorsel.height:
            yukseklik = max(1, gorsel.height - y); genislik = max(1, round(yukseklik * ow / oh))
        self.kirp_genislik_var.set(str(genislik)); self.kirp_yukseklik_var.set(str(yukseklik)); self._kirpma_dikdortgenini_verilerden_guncelle()

    def _kirpma_dikdortgenini_verilerden_guncelle(self) -> None:
        if self.goruntu_alani is None or self.fotograf_servisi.calisma_gorseli is None: return
        try:
            x = int(self.kirp_x_var.get()); y = int(self.kirp_y_var.get()); genislik = int(self.kirp_genislik_var.get()); yukseklik = int(self.kirp_yukseklik_var.get())
        except ValueError:
            return
        sol, ust, sag, alt = self.goruntu_alani; gorsel = self.fotograf_servisi.calisma_gorseli
        oran_x = max(sag - sol, 1) / gorsel.width; oran_y = max(alt - ust, 1) / gorsel.height
        self.kirpma_dikdortgeni = (sol + round(x * oran_x), ust + round(y * oran_y), sol + round((x + genislik) * oran_x), ust + round((y + yukseklik) * oran_y))

    def _onizleme_yenile(self, _event=None) -> None:
        if self.fotograf_servisi.calisma_gorseli is None:
            self.onizleme_tuvali.delete("all"); self.onizleme_tuvali.configure(scrollregion=(0, 0, 0, 0)); self.onizleme_etiketi.config(text="Henüz medya yüklenmedi"); self.onizleme_etiketi.place(relx=0.5, rely=0.5, anchor="center"); self.goruntu_alani = None; return
        kaynak = self.fotograf_servisi.calisma_gorseli.copy()
        cw, ch = max(self.onizleme_tuvali.winfo_width(), 1), max(self.onizleme_tuvali.winfo_height(), 1)
        if self.ekrana_sigdir_modu:
            gorsel = kaynak.copy()
            gorsel.thumbnail((max(cw - 20, 1), max(ch - 20, 1)))
        else:
            genislik = max(1, round(kaynak.width * self.yakinlastirma_orani))
            yukseklik = max(1, round(kaynak.height * self.yakinlastirma_orani))
            gorsel = kaynak.resize((genislik, yukseklik))
        x_konum, y_konum = self._goruntu_yerlesimini_hesapla(gorsel.width, gorsel.height, cw, ch)
        self.goruntu_alani = (x_konum, y_konum, x_konum + gorsel.width, y_konum + gorsel.height)
        self.onizleme_gorseli = ImageTk.PhotoImage(gorsel)
        self.onizleme_tuvali.delete("all")
        self.onizleme_tuvali.create_image(x_konum, y_konum, image=self.onizleme_gorseli, anchor="nw")
        self.onizleme_tuvali.configure(scrollregion=(min(0, x_konum - 10), min(0, y_konum - 10), x_konum + gorsel.width + 10, y_konum + gorsel.height + 10))
        self._metin_taslagini_ciz()
        self._cizim_taslagini_ciz()
        self._kirpma_dikdortgenini_ciz()
        self.onizleme_etiketi.place_forget()

    def _goruntu_yerlesimini_hesapla(self, gorsel_genislik: int, gorsel_yukseklik: int, tuval_genislik: int, tuval_yukseklik: int) -> tuple[int, int]:
        taban_x = max(10, (tuval_genislik - gorsel_genislik) // 2) if gorsel_genislik < tuval_genislik - 20 else 10
        taban_y = max(10, (tuval_yukseklik - gorsel_yukseklik) // 2) if gorsel_yukseklik < tuval_yukseklik - 20 else 10
        x_konum = max(10, taban_x + self.goruntu_ofset_x)
        y_konum = max(10, taban_y + self.goruntu_ofset_y)
        return x_konum, y_konum

    def kirpma_secimini_temizle(self, yalnizca_goruntu: bool = True) -> None:
        self.kirpma_baslangici = None; self.kirpma_dikdortgeni = None; self.kirpma_modu = None
        if not yalnizca_goruntu: self.kirp_x_var.set("0"); self.kirp_y_var.set("0")
        self._onizleme_yenile()

    def _kirpma_baslat(self, event) -> None:
        if not self._gorsel_var_mi(sessiz=True): return
        if self.goruntu_tasima_modu_var.get():
            nokta = self._goruntu_icine_sinirla(event.x, event.y)
            if nokta is None:
                return
            self.goruntu_tasiniyor = True
            self.goruntu_tasima_baslangici = (event.x, event.y)
            return
        if self.cizim_araci_var.get() != "Kapalı":
            nokta = self._goruntu_icine_sinirla(event.x, event.y)
            if nokta is None: return
            self.cizim_baslangici = nokta
            self.cizim_noktalari = [nokta]
            return
        if self._metin_uzerine_tiklandi(event.x, event.y):
            self.metin_tasiniyor = True
            return
        nokta = self._goruntu_icine_sinirla(event.x, event.y)
        if nokta is None: return
        tutamac = self._aktif_tutamaci_bul(nokta)
        if tutamac is not None and self.kirpma_dikdortgeni is not None:
            self.kirpma_modu = tutamac; self.kirpma_baslangici = nokta; return
        self.kirpma_baslangici = nokta; self.kirpma_modu = "yeni"; self.kirpma_dikdortgeni = (*nokta, *nokta); self._kirpma_alanini_guncelle(); self._onizleme_yenile()

    def _kirpma_surukle(self, event) -> None:
        if self.goruntu_tasiniyor and self.goruntu_tasima_baslangici is not None:
            onceki_x, onceki_y = self.goruntu_tasima_baslangici
            self.goruntu_ofset_x += event.x - onceki_x
            self.goruntu_ofset_y += event.y - onceki_y
            self.goruntu_tasima_baslangici = (event.x, event.y)
            self._onizleme_yenile()
            return
        if self.cizim_baslangici is not None and self.cizim_araci_var.get() != "Kapalı":
            nokta = self._goruntu_icine_sinirla(event.x, event.y)
            if nokta is None: return
            if self.cizim_araci_var.get() in ("Serbest Çizim", "Silgi"): self.cizim_noktalari.append(nokta)
            else: self.cizim_noktalari = [self.cizim_baslangici, nokta]
            self._onizleme_yenile()
            return
        if self.metin_tasiniyor:
            self._metni_tasi(event.x, event.y)
            return
        if self.kirpma_baslangici is None: return
        nokta = self._goruntu_icine_sinirla(event.x, event.y)
        if nokta is None: return
        if self.kirpma_modu == "yeni": self.kirpma_dikdortgeni = (*self.kirpma_baslangici, *nokta)
        else: self._tutamaci_guncelle(nokta)
        self._kirpma_alanini_guncelle(); self._onizleme_yenile()

    def _kirpma_birak(self, event) -> None:
        if self.goruntu_tasiniyor:
            self.goruntu_tasiniyor = False
            self.goruntu_tasima_baslangici = None
            self._durum_yaz("Görsel yeni konumuna taşındı.")
            return
        if self.cizim_baslangici is not None and self.cizim_araci_var.get() != "Kapalı":
            nokta = self._goruntu_icine_sinirla(event.x, event.y)
            if nokta is not None and self.cizim_araci_var.get() not in ("Serbest Çizim", "Silgi"):
                self.cizim_noktalari = [self.cizim_baslangici, nokta]
            self._cizimi_uygula()
            self.cizim_baslangici = None
            self.cizim_noktalari = []
            return
        if self.metin_tasiniyor:
            self.metin_tasiniyor = False
            self._durum_yaz("Metin taslağı yeni konumuna taşındı.")
            return
        if self.kirpma_baslangici is None: return
        nokta = self._goruntu_icine_sinirla(event.x, event.y)
        if nokta is not None:
            if self.kirpma_modu == "yeni": self.kirpma_dikdortgeni = (*self.kirpma_baslangici, *nokta)
            else: self._tutamaci_guncelle(nokta)
            self._kirpma_alanini_guncelle()
        self.kirpma_baslangici = None; self.kirpma_modu = None; self._onizleme_yenile(); self._durum_yaz("Kırpma alanı önizlemede güncellendi.")

    def _goruntu_icine_sinirla(self, x: int, y: int):
        if self.goruntu_alani is None: return None
        sol, ust, sag, alt = self.goruntu_alani
        return min(max(x, sol), sag), min(max(y, ust), alt)

    def _metin_uzerine_tiklandi(self, x: int, y: int) -> bool:
        for oge in reversed(self.oge_listesi):
            if oge.get("tur") != "metin" or not oge.get("gorunur", True):
                continue
            bbox = self.onizleme_tuvali.bbox(f"oge_{oge['id']}")
            if bbox and bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]:
                self._ogeyi_sec(oge["id"])
                return True
        return False

    def _metni_tasi(self, x: int, y: int) -> None:
        if self.metin_taslagi is None or self.goruntu_alani is None or self.fotograf_servisi.calisma_gorseli is None:
            return
        sol, ust, sag, alt = self.goruntu_alani
        x = min(max(x, sol), sag)
        y = min(max(y, ust), alt)
        gorsel = self.fotograf_servisi.calisma_gorseli
        oran_x = gorsel.width / max(sag - sol, 1)
        oran_y = gorsel.height / max(alt - ust, 1)
        self.metin_taslagi["x"] = int((x - sol) * oran_x)
        self.metin_taslagi["y"] = int((y - ust) * oran_y)
        self._onizleme_yenile()

    def _noktayi_gorsele_cevir(self, nokta):
        if self.goruntu_alani is None or self.fotograf_servisi.calisma_gorseli is None:
            return None
        sol, ust, sag, alt = self.goruntu_alani
        gorsel = self.fotograf_servisi.calisma_gorseli
        oran_x = gorsel.width / max(sag - sol, 1)
        oran_y = gorsel.height / max(alt - ust, 1)
        x, y = nokta
        return int((x - sol) * oran_x), int((y - ust) * oran_y)

    def _cizimi_uygula(self) -> None:
        if not self.cizim_noktalari or self.cizim_araci_var.get() == "Kapalı":
            return
        noktalar = [self._noktayi_gorsele_cevir(nokta) for nokta in self.cizim_noktalari]
        noktalar = [nokta for nokta in noktalar if nokta is not None]
        if len(noktalar) < 2:
            return
        renk = self.metin_renkleri.get(self.cizim_renk_var.get(), "#5aa2ff")
        try:
            kalinlik = int(self.cizim_boyut_var.get())
        except ValueError:
            self._hata_goster("Fırça boyutu için geçerli bir sayı seçin.")
            return
        oge = {
            "id": self._yeni_oge_id(),
            "tur": "cizim",
            "ad": self._yeni_oge_adi("Çizim", "cizim"),
            "arac": self.cizim_araci_var.get(),
            "noktalar": noktalar,
            "renk": renk,
            "kalinlik": kalinlik,
            "gorunur": True,
        }
        self.oge_listesi.append(oge)
        self._ogeyi_sec(oge["id"])
        self._durum_yaz(f"{self.cizim_araci_var.get()} öğesi eklendi. İsterseniz listeden gizleyebilir veya silebilirsiniz.")

    def _kirpma_alanini_guncelle(self) -> None:
        if self.kirpma_dikdortgeni is None or self.goruntu_alani is None or self.fotograf_servisi.calisma_gorseli is None: return
        x1, y1, x2, y2 = self.kirpma_dikdortgeni; sol, ust, sag, alt = self.goruntu_alani; g = self.fotograf_servisi.calisma_gorseli
        oran_x = g.width / max(sag - sol, 1); oran_y = g.height / max(alt - ust, 1)
        bas_x = int((min(x1, x2) - sol) * oran_x); bas_y = int((min(y1, y2) - ust) * oran_y); bit_x = int((max(x1, x2) - sol) * oran_x); bit_y = int((max(y1, y2) - ust) * oran_y)
        genislik = max(1, bit_x - bas_x); yukseklik = max(1, bit_y - bas_y)
        self.kirp_x_var.set(str(max(0, bas_x))); self.kirp_y_var.set(str(max(0, bas_y))); self.kirp_genislik_var.set(str(genislik)); self.kirp_yukseklik_var.set(str(yukseklik))
        if self._oran_degerini_getir() is not None: self._kirpma_olculerini_orana_gore_duzelt(max(0, bas_x), max(0, bas_y), genislik, yukseklik)

    def _kirpma_dikdortgenini_ciz(self) -> None:
        if self.kirpma_dikdortgeni is None: return
        x1, y1, x2, y2 = self.kirpma_dikdortgeni; sol, ust, sag, alt = min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)
        self.onizleme_tuvali.create_rectangle(sol, ust, sag, alt, outline="#5aa2ff", width=2, dash=(6, 3))
        for tx, ty in ((sol, ust), ((sol + sag) // 2, ust), (sag, ust), (sol, (ust + alt) // 2), (sag, (ust + alt) // 2), (sol, alt), ((sol + sag) // 2, alt), (sag, alt)):
            self.onizleme_tuvali.create_rectangle(tx - self.TUTAMAC_BOYUTU, ty - self.TUTAMAC_BOYUTU, tx + self.TUTAMAC_BOYUTU, ty + self.TUTAMAC_BOYUTU, fill="#5aa2ff", outline="#d7e7ff")

    def _metin_taslagini_ciz(self) -> None:
        if self.goruntu_alani is None or self.fotograf_servisi.calisma_gorseli is None:
            return
        gorsel = self.fotograf_servisi.calisma_gorseli
        sol, ust, sag, alt = self.goruntu_alani
        oran_x = max(sag - sol, 1) / gorsel.width
        oran_y = max(alt - ust, 1) / gorsel.height
        for oge in self.oge_listesi:
            if oge.get("tur") != "metin" or not oge.get("gorunur", True):
                continue
            x = sol + round(oge["x"] * oran_x)
            y = ust + round(oge["y"] * oran_y)
            boyut = max(10, round(oge["boyut"] * min(oran_x, oran_y)))
            etiket = f"oge_{oge['id']}"
            self.onizleme_tuvali.create_text(x, y, text=oge["metin"], fill=oge["renk"], font=("Segoe UI", boyut, "bold"), anchor="nw", tags=(etiket, "metin_taslagi"))
            if oge.get("id") == self.secili_oge_id:
                kutu = self.onizleme_tuvali.bbox(etiket)
                if kutu:
                    self.onizleme_tuvali.create_rectangle(kutu[0] - 4, kutu[1] - 4, kutu[2] + 4, kutu[3] + 4, outline="#88c3ff", dash=(4, 2), width=1)

    def _cizim_taslagini_ciz(self) -> None:
        for oge in self.oge_listesi:
            if oge.get("tur") != "cizim" or not oge.get("gorunur", True):
                continue
            self._tek_cizim_ogesini_ciz(oge, secili=oge.get("id") == self.secili_oge_id)
        if not self.cizim_noktalari or self.cizim_araci_var.get() == "Kapalı":
            return
        renk = self.metin_renkleri.get(self.cizim_renk_var.get(), "#5aa2ff")
        try:
            kalinlik = int(self.cizim_boyut_var.get())
        except ValueError:
            kalinlik = 4
        self._tek_cizim_ogesini_ciz({"id": "taslak", "arac": self.cizim_araci_var.get(), "noktalar": self.cizim_noktalari, "renk": renk, "kalinlik": kalinlik}, secili=False)

    def _tek_cizim_ogesini_ciz(self, oge, secili: bool = False) -> None:
        noktalar = oge.get("noktalar", [])
        if len(noktalar) < 2:
            return
        arac = oge.get("arac", "Serbest Çizim")
        renk = oge.get("renk", "#5aa2ff")
        kalinlik = int(oge.get("kalinlik", 4))
        etiket = f"oge_{oge.get('id', 'taslak')}"
        if arac in ("Serbest Çizim", "Silgi") and len(noktalar) > 1:
            self.onizleme_tuvali.create_line(*[koordinat for nokta in noktalar for koordinat in nokta], fill=renk if arac != "Silgi" else "#202020", width=kalinlik, smooth=True, tags=(etiket, "cizim_taslagi"))
        else:
            (x1, y1), (x2, y2) = noktalar[0], noktalar[-1]
            if arac in ("Düz Çizgi", "Ok"):
                self.onizleme_tuvali.create_line(x1, y1, x2, y2, fill=renk, width=kalinlik, tags=(etiket, "cizim_taslagi"))
            elif arac == "Dikdörtgen":
                self.onizleme_tuvali.create_rectangle(x1, y1, x2, y2, outline=renk, width=kalinlik, tags=(etiket, "cizim_taslagi"))
            elif arac == "Daire":
                self.onizleme_tuvali.create_oval(x1, y1, x2, y2, outline=renk, width=kalinlik, tags=(etiket, "cizim_taslagi"))
        if secili:
            kutu = self.onizleme_tuvali.bbox(etiket)
            if kutu:
                self.onizleme_tuvali.create_rectangle(kutu[0] - 4, kutu[1] - 4, kutu[2] + 4, kutu[3] + 4, outline="#88c3ff", dash=(4, 2), width=1)

    def _aktif_tutamaci_bul(self, nokta):
        if self.kirpma_dikdortgeni is None: return None
        x, y = nokta; x1, y1, x2, y2 = self.kirpma_dikdortgeni; sol, ust, sag, alt = min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)
        tutamaclar = {"sol_ust": (sol, ust), "ust": ((sol + sag) // 2, ust), "sag_ust": (sag, ust), "sol": (sol, (ust + alt) // 2), "sag": (sag, (ust + alt) // 2), "sol_alt": (sol, alt), "alt": ((sol + sag) // 2, alt), "sag_alt": (sag, alt)}
        for ad, (tx, ty) in tutamaclar.items():
            if abs(x - tx) <= self.TUTAMAC_BOYUTU * 2 and abs(y - ty) <= self.TUTAMAC_BOYUTU * 2: return ad
        return None

    def _tutamaci_guncelle(self, nokta) -> None:
        if self.kirpma_dikdortgeni is None or self.kirpma_modu is None: return
        x1, y1, x2, y2 = self.kirpma_dikdortgeni; x, y = nokta
        if self.kirpma_modu == "sol_ust": self.kirpma_dikdortgeni = (x, y, x2, y2)
        elif self.kirpma_modu == "ust": self.kirpma_dikdortgeni = (x1, y, x2, y2)
        elif self.kirpma_modu == "sag_ust": self.kirpma_dikdortgeni = (x1, y, x, y2)
        elif self.kirpma_modu == "sol": self.kirpma_dikdortgeni = (x, y1, x2, y2)
        elif self.kirpma_modu == "sag": self.kirpma_dikdortgeni = (x1, y1, x, y2)
        elif self.kirpma_modu == "sol_alt": self.kirpma_dikdortgeni = (x, y1, x2, y)
        elif self.kirpma_modu == "alt": self.kirpma_dikdortgeni = (x1, y1, x2, y)
        elif self.kirpma_modu == "sag_alt": self.kirpma_dikdortgeni = (x1, y1, x, y)

    def _hata_goster(self, mesaj: str) -> None:
        messagebox.showwarning("Uyarı", mesaj); self._durum_yaz(mesaj)

    def _filtre_onizlemelerini_guncelle(self) -> None:
        if self.fotograf_servisi.calisma_gorseli is None:
            for kart in self.filtre_kartlari.values(): kart.configure(image="", text=kart.cget("text"))
            self.filtre_onizleme_gorselleri.clear(); return
        for ad, kart in self.filtre_kartlari.items():
            try: kopya = self.fotograf_servisi.filtreli_kopya_uret(ad)
            except Exception: continue
            kopya.thumbnail((88, 66)); gorsel = ImageTk.PhotoImage(kopya); self.filtre_onizleme_gorselleri[ad] = gorsel; kart.configure(image=gorsel, text=ad, compound="top")
