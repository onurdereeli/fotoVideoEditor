from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import ImageTk

from app.services.video_servisi import DESTEKLENEN_VIDEO_DOSYALARI, VideoServisi
from app.ui.bilesenler import buton
from app.ui.timeline_widget import TimelineWidget
from app.ui.video_player import VideoPlayer
from app.ui.yerlesim import SekmeDuzeni


class VideoSekmesi(SekmeDuzeni):
    PRESET_ORIGINAL = "Orijinal Çözünürlük"
    PRESET_1080P = "MP4 1080p"
    PRESET_720P = "MP4 720p"
    PRESET_SILENT = "Sessiz MP4"
    STYLE_EFFECT_OPTIONS = [
        ("black_white", "Black & White"),
        ("sepia", "Sepia"),
        ("vignette", "Vignette"),
        ("blur", "Blur"),
        ("sharpen", "Sharpen"),
        ("film_grain", "Film Grain"),
        ("vintage", "Vintage"),
        ("cool_tone", "Cool Tone"),
        ("warm_tone", "Warm Tone"),
        ("posterize", "Posterize"),
        ("pixelate", "Pixelate"),
        ("rgb_split", "RGB Split"),
    ]

    def __init__(self, parent: ttk.Notebook, durum_guncelle) -> None:
        super().__init__(parent, "Video Araçları", "Video Önizleme")
        self.durum_guncelle = durum_guncelle
        self.video_servisi = VideoServisi()
        self.onizleme_gorseli = None
        self.export_kuyrugu: queue.Queue[tuple[str, str]] = queue.Queue()
        self.export_thread: threading.Thread | None = None
        self.disa_aktariliyor = False
        self.kontrol_bilesenleri: list[ttk.Widget] = []
        self._trim_sync_locked = False

        self.dosya_metin = tk.StringVar(value="Dosya: -")
        self.sure_metin = tk.StringVar(value="Süre: -")
        self.cozunurluk_metin = tk.StringVar(value="Çözünürlük: -")
        self.fps_metin = tk.StringVar(value="Kare Hızı: -")
        self.ses_metin = tk.StringVar(value="Ses: -")
        self.ses_seviyesi_metin = tk.StringVar(value="100%")
        self.brightness_metin = tk.StringVar(value="0")
        self.contrast_metin = tk.StringVar(value="0")
        self.saturation_metin = tk.StringVar(value="100%")
        self.gamma_metin = tk.StringVar(value="1.0")
        self.preset_var = tk.StringVar(value=self.PRESET_ORIGINAL)
        self.export_ilerleme_metin = tk.StringVar(value="Export hazır")

        self.baslangic_var = tk.StringVar(value="0")
        self.bitis_var = tk.StringVar(value="")
        self.genislik_var = tk.StringVar(value="")
        self.yukseklik_var = tk.StringVar(value="")
        self.fade_in_var = tk.StringVar(value="0")
        self.fade_out_var = tk.StringVar(value="0")
        self.hiz_var = tk.StringVar(value="1x")
        self.hiz_metin = tk.StringVar(value="1x")
        self.rotate_var = tk.StringVar(value="0\N{DEGREE SIGN}")
        self.aspect_ratio_var = tk.StringVar(value="Original")
        self.sosyal_oran_var = tk.StringVar(value="Orijinal")
        self.metin_var = tk.StringVar(value="")
        self.metin_font_boyutu_var = tk.StringVar(value="36")
        self.metin_renk_var = tk.StringVar(value="Beyaz")
        self.metin_konum_var = tk.StringVar(value="Alt")
        self.metin_baslangic_var = tk.StringVar(value="0")
        self.metin_bitis_var = tk.StringVar(value="")
        self.sesi_kapat_var = tk.BooleanVar(value=False)
        self.flip_horizontal_var = tk.BooleanVar(value=False)
        self.flip_vertical_var = tk.BooleanVar(value=False)
        self.ses_seviyesi_var = tk.IntVar(value=100)
        self.brightness_var = tk.IntVar(value=0)
        self.contrast_var = tk.IntVar(value=0)
        self.saturation_var = tk.IntVar(value=100)
        self.gamma_var = tk.DoubleVar(value=1.0)
        self.blackwhite_var = tk.BooleanVar(value=False)
        self._efekt_gecmisi: list[dict[str, float | bool]] = []
        self._bekleyen_efekt_durumu: dict[str, float | bool] | None = None
        self._efekt_guncelleniyor = False
        self.efekt_onizleme_gorseli = None
        self.selected_effects: list[str] = []
        self.style_effect_vars: dict[str, tk.BooleanVar] = {}
        self.style_effect_checkbuttons: list[ttk.Checkbutton] = []

        self._icerik_kur()
        self._video_playeri_kur()
        self._timeline_kur()
        self._trim_izleyicileri_bagla()
        self._fade_izleyicileri_bagla()
        self._donusum_izleyicileri_bagla()
        self._metin_izleyicileri_bagla()
        self._goster_statik_onizleme()
        self.onizleme_tuvali.bind("<Configure>", self._onizleme_yenile)

    def _icerik_kur(self) -> None:
        self.arac_paneli.rowconfigure(99, weight=1)

        dosya_kutu = ttk.LabelFrame(self.arac_paneli, text="Dosya İşlemleri", style="Panel.TLabelframe")
        dosya_kutu.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        dosya_kutu.columnconfigure(0, weight=1)
        ttk.Label(
            dosya_kutu,
            text="Bir video açın ve gerekli ayarlardan sonra dışa aktarın.",
            style="Aciklama.TLabel",
            wraplength=240,
            justify="left",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.video_ac_butonu = buton(dosya_kutu, "Video Aç", self.video_ac)
        self.video_ac_butonu.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.disa_aktar_butonu = buton(dosya_kutu, "Dışa Aktar", self.disa_aktar)
        self.disa_aktar_butonu.grid(row=2, column=0, sticky="ew")

        export_kutu = ttk.LabelFrame(self.arac_paneli, text="Export Seçenekleri", style="Panel.TLabelframe")
        export_kutu.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        export_kutu.columnconfigure(0, weight=1)
        ttk.Label(export_kutu, text="Preset", style="Genel.TLabel").grid(row=0, column=0, sticky="w")
        self.preset_combobox = ttk.Combobox(
            export_kutu,
            textvariable=self.preset_var,
            state="readonly",
            values=[
                self.PRESET_ORIGINAL,
                self.PRESET_1080P,
                self.PRESET_720P,
                self.PRESET_SILENT,
            ],
        )
        self.preset_combobox.grid(row=1, column=0, sticky="ew", pady=(4, 8))
        self.preset_combobox.bind("<<ComboboxSelected>>", self._preset_secildi)
        self.export_progress = ttk.Progressbar(export_kutu, mode="determinate", maximum=100, value=0)
        self.export_progress.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(
            export_kutu,
            textvariable=self.export_ilerleme_metin,
            style="Aciklama.TLabel",
            wraplength=220,
            justify="left",
        ).grid(row=3, column=0, sticky="w")

        trim_kutu = ttk.LabelFrame(self.arac_paneli, text="Trim Ayarları", style="Panel.TLabelframe")
        trim_kutu.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        trim_kutu.columnconfigure((0, 1), weight=1)
        self.baslangic_entry = self._alan_olustur(trim_kutu, "Başlangıç (sn)", self.baslangic_var, 0, 0)
        self.bitis_entry = self._alan_olustur(trim_kutu, "Bitiş (sn)", self.bitis_var, 0, 1)

        boyut_kutu = ttk.LabelFrame(self.arac_paneli, text="Yeniden Boyutlandır", style="Panel.TLabelframe")
        boyut_kutu.grid(row=4, column=0, sticky="ew", pady=(0, 12))
        boyut_kutu.columnconfigure((0, 1), weight=1)
        self.genislik_entry = self._alan_olustur(boyut_kutu, "Genişlik", self.genislik_var, 0, 0)
        self.yukseklik_entry = self._alan_olustur(boyut_kutu, "Yükseklik", self.yukseklik_var, 0, 1)
        ttk.Label(
            boyut_kutu,
            text="Boş bırakırsanız özgün boyut korunur.",
            style="Genel.TLabel",
            wraplength=220,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))

        hiz_kutu = ttk.LabelFrame(self.arac_paneli, text="Hız Kontrolü", style="Panel.TLabelframe")
        hiz_kutu.grid(row=5, column=0, sticky="ew", pady=(0, 12))
        hiz_kutu.columnconfigure((0, 1), weight=1)
        ttk.Label(hiz_kutu, text="Hız", style="Genel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(hiz_kutu, textvariable=self.hiz_metin, style="Genel.TLabel").grid(row=0, column=1, sticky="e")
        self.hiz_combobox = ttk.Combobox(
            hiz_kutu,
            textvariable=self.hiz_var,
            state="readonly",
            values=["0.5x", "0.75x", "1x", "1.25x", "1.5x", "2x"],
        )
        self.hiz_combobox.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 8))
        self.hiz_combobox.bind("<<ComboboxSelected>>", self._hiz_degisti)
        self.hiz_sifirla_butonu = buton(hiz_kutu, "Hızı Sıfırla", self._hizi_sifirla)
        self.hiz_sifirla_butonu.grid(row=2, column=0, columnspan=2, sticky="ew")

        oran_kutu = ttk.LabelFrame(self.arac_paneli, text="Sosyal Medya Oranları", style="Panel.TLabelframe")
        oran_kutu.grid(row=6, column=0, sticky="ew", pady=(0, 12))
        oran_kutu.columnconfigure(0, weight=1)
        ttk.Label(oran_kutu, text="Oran Seçimi", style="Genel.TLabel").grid(row=0, column=0, sticky="w")
        self.sosyal_oran_combobox = ttk.Combobox(
            oran_kutu,
            textvariable=self.sosyal_oran_var,
            state="readonly",
            values=[
                "Orijinal",
                "YouTube Shorts / TikTok / Reels (9:16)",
                "Instagram Kare (1:1)",
                "Instagram Dikey (4:5)",
                "YouTube Yatay (16:9)",
            ],
        )
        self.sosyal_oran_combobox.grid(row=1, column=0, sticky="ew", pady=(4, 8))
        self.sosyal_oran_combobox.bind("<<ComboboxSelected>>", self._sosyal_oran_degisti)
        donusum_kutu = ttk.LabelFrame(self.arac_paneli, text="Video Dönüştürme", style="Panel.TLabelframe")
        donusum_kutu.grid(row=7, column=0, sticky="ew", pady=(0, 12))
        donusum_kutu.columnconfigure((0, 1), weight=1)
        ttk.Label(donusum_kutu, text="Rotate", style="Genel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(donusum_kutu, text="Aspect Ratio", style="Genel.TLabel").grid(row=0, column=1, sticky="w")
        self.rotate_combobox = ttk.Combobox(
            donusum_kutu,
            textvariable=self.rotate_var,
            state="readonly",
            values=["0\N{DEGREE SIGN}", "90\N{DEGREE SIGN}", "180\N{DEGREE SIGN}", "270\N{DEGREE SIGN}"],
        )
        self.rotate_combobox.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(4, 8))
        self.rotate_combobox.bind("<<ComboboxSelected>>", self._donusum_onizleme_degisti)
        self.aspect_ratio_combobox = ttk.Combobox(
            donusum_kutu,
            textvariable=self.aspect_ratio_var,
            state="readonly",
            values=["Original", "16:9", "9:16", "1:1", "4:5"],
        )
        self.aspect_ratio_combobox.grid(row=1, column=1, sticky="ew", pady=(4, 8))
        self.aspect_ratio_combobox.bind("<<ComboboxSelected>>", self._donusum_onizleme_degisti)
        self.flip_horizontal_checkbox = ttk.Checkbutton(
            donusum_kutu,
            text="Horizontal",
            variable=self.flip_horizontal_var,
            command=self._donusum_onizleme_degisti,
            style="Switch.TCheckbutton",
        )
        self.flip_horizontal_checkbox.grid(row=2, column=0, sticky="w", padx=(0, 6))
        self.flip_vertical_checkbox = ttk.Checkbutton(
            donusum_kutu,
            text="Vertical",
            variable=self.flip_vertical_var,
            command=self._donusum_onizleme_degisti,
            style="Switch.TCheckbutton",
        )
        self.flip_vertical_checkbox.grid(row=2, column=1, sticky="w")
        self.donusum_sifirla_butonu = buton(donusum_kutu, "Transformları Sıfırla", self._donusumleri_sifirla)
        self.donusum_sifirla_butonu.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        ses_kutu = ttk.LabelFrame(self.arac_paneli, text="Ses Ayarı", style="Panel.TLabelframe")
        ses_kutu.grid(row=8, column=0, sticky="ew", pady=(0, 12))
        ses_kutu.columnconfigure((0, 1), weight=1)
        ttk.Label(ses_kutu, text="Ses Seviyesi", style="Genel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(ses_kutu, textvariable=self.ses_seviyesi_metin, style="Genel.TLabel").grid(
            row=0, column=1, sticky="e"
        )
        self.ses_seviyesi_slider = ttk.Scale(
            ses_kutu,
            from_=0,
            to=200,
            orient="horizontal",
            command=self._ses_seviyesi_degisti,
        )
        self.ses_seviyesi_slider.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 8))
        self.ses_seviyesi_slider.set(self.ses_seviyesi_var.get())

        ttk.Label(ses_kutu, text="Fade In (sn)", style="Genel.TLabel").grid(row=2, column=0, sticky="w")
        ttk.Label(ses_kutu, text="Fade Out (sn)", style="Genel.TLabel").grid(row=2, column=1, sticky="w")
        self.fade_in_entry = ttk.Entry(ses_kutu, textvariable=self.fade_in_var, style="Karanlik.TEntry", width=10)
        self.fade_in_entry.grid(row=3, column=0, sticky="ew", padx=(0, 6), pady=(4, 8))
        self.fade_out_entry = ttk.Entry(ses_kutu, textvariable=self.fade_out_var, style="Karanlik.TEntry", width=10)
        self.fade_out_entry.grid(row=3, column=1, sticky="ew", pady=(4, 8))

        self.ses_checkbox = ttk.Checkbutton(
            ses_kutu,
            text="Videoyu sessiz dışa aktar",
            variable=self.sesi_kapat_var,
            style="Switch.TCheckbutton",
        )
        self.ses_checkbox.grid(row=4, column=0, columnspan=2, sticky="w")

        efekt_kutu = ttk.LabelFrame(self.arac_paneli, text="Görsel Efektler", style="Panel.TLabelframe")
        efekt_kutu.grid(row=9, column=0, sticky="ew", pady=(0, 12))
        efekt_kutu.columnconfigure((0, 1), weight=1)
        ttk.Label(efekt_kutu, text="Brightness", style="Genel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(efekt_kutu, textvariable=self.brightness_metin, style="Genel.TLabel").grid(
            row=0, column=1, sticky="e"
        )
        self.brightness_slider = ttk.Scale(
            efekt_kutu,
            from_=-100,
            to=100,
            orient="horizontal",
            command=self._brightness_degisti,
        )
        self.brightness_slider.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 8))
        self.brightness_slider.set(self.brightness_var.get())

        ttk.Label(efekt_kutu, text="Contrast", style="Genel.TLabel").grid(row=2, column=0, sticky="w")
        ttk.Label(efekt_kutu, textvariable=self.contrast_metin, style="Genel.TLabel").grid(
            row=2, column=1, sticky="e"
        )
        self.contrast_slider = ttk.Scale(
            efekt_kutu,
            from_=-100,
            to=100,
            orient="horizontal",
            command=self._contrast_degisti,
        )
        self.contrast_slider.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(4, 8))
        self.contrast_slider.set(self.contrast_var.get())

        ttk.Label(efekt_kutu, text="Saturation", style="Genel.TLabel").grid(row=4, column=0, sticky="w")
        ttk.Label(efekt_kutu, textvariable=self.saturation_metin, style="Genel.TLabel").grid(
            row=4, column=1, sticky="e"
        )
        self.saturation_slider = ttk.Scale(
            efekt_kutu,
            from_=0,
            to=200,
            orient="horizontal",
            command=self._saturation_degisti,
        )
        self.saturation_slider.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(4, 8))
        self.saturation_slider.set(self.saturation_var.get())

        ttk.Label(efekt_kutu, text="Gamma", style="Genel.TLabel").grid(row=6, column=0, sticky="w")
        ttk.Label(efekt_kutu, textvariable=self.gamma_metin, style="Genel.TLabel").grid(
            row=6, column=1, sticky="e"
        )
        self.gamma_slider = ttk.Scale(
            efekt_kutu,
            from_=0.1,
            to=3.0,
            orient="horizontal",
            command=self._gamma_degisti,
        )
        self.gamma_slider.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(4, 8))
        self.gamma_slider.set(self.gamma_var.get())

        self.blackwhite_checkbox = ttk.Checkbutton(
            efekt_kutu,
            text="Black & White",
            variable=self.blackwhite_var,
            command=self._blackwhite_degisti,
            style="Switch.TCheckbutton",
        )
        self.blackwhite_checkbox.grid(row=8, column=0, columnspan=2, sticky="w")
        self.blackwhite_checkbox.bind("<Button-1>", self._efekt_gecmisini_hazirla, add="+")

        self.efekt_geri_al_butonu = buton(efekt_kutu, "Geri Al", self._efektleri_geri_al)
        self.efekt_geri_al_butonu.grid(row=9, column=0, sticky="ew", padx=(0, 6), pady=(10, 0))
        self.efekt_sifirla_butonu = buton(efekt_kutu, "Efektleri Sıfırla", self._efektleri_sifirla)
        self.efekt_sifirla_butonu.grid(row=9, column=1, sticky="ew", pady=(10, 0))

        self.efekt_onizleme_kutu = ttk.LabelFrame(efekt_kutu, text="Canlı Efekt Önizleme", style="Panel.TLabelframe")
        self.efekt_onizleme_kutu.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        self.efekt_onizleme_kutu.columnconfigure(0, weight=1)
        self.efekt_onizleme_resim = ttk.Label(self.efekt_onizleme_kutu, text="Video açıldığında burada görünür", anchor="center", style="Genel.TLabel")
        self.efekt_onizleme_resim.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))
        ttk.Label(
            self.efekt_onizleme_kutu,
            text="Efektler export öncesi bu kare üzerinde önizlenir.",
            style="Aciklama.TLabel",
            wraplength=220,
            justify="left",
        ).grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))

        for slider in (
            self.brightness_slider,
            self.contrast_slider,
            self.saturation_slider,
            self.gamma_slider,
        ):
            slider.bind("<ButtonPress-1>", self._efekt_gecmisini_hazirla, add="+")
            slider.bind("<ButtonRelease-1>", self._efekt_degisimini_kaydet, add="+")

        stil_kutu = ttk.LabelFrame(self.arac_paneli, text="Stil Efektleri", style="Panel.TLabelframe")
        stil_kutu.grid(row=10, column=0, sticky="ew", pady=(0, 12))
        stil_kutu.columnconfigure((0, 1), weight=1)
        self.style_effect_checkbuttons = []
        for index, (effect_key, effect_label) in enumerate(self.STYLE_EFFECT_OPTIONS):
            effect_var = tk.BooleanVar(value=False)
            self.style_effect_vars[effect_key] = effect_var
            checkbox = ttk.Checkbutton(
                stil_kutu,
                text=effect_label,
                variable=effect_var,
                command=self._stil_efektlerini_guncelle,
                style="Switch.TCheckbutton",
            )
            checkbox.grid(
                row=index // 2,
                column=index % 2,
                sticky="w",
                padx=(0, 8) if index % 2 == 0 else 0,
                pady=(0, 6),
            )
            self.style_effect_checkbuttons.append(checkbox)

        self.reset_effects_butonu = buton(stil_kutu, "Reset Effects", self._stil_efektlerini_sifirla)
        self.reset_effects_butonu.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        metin_kutu = ttk.LabelFrame(self.arac_paneli, text="Metin Ekle", style="Panel.TLabelframe")
        metin_kutu.grid(row=11, column=0, sticky="ew", pady=(0, 12))
        metin_kutu.columnconfigure((0, 1), weight=1)
        ttk.Label(metin_kutu, text="Metin İçeriği", style="Genel.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        self.metin_entry = ttk.Entry(metin_kutu, textvariable=self.metin_var, style="Karanlik.TEntry")
        self.metin_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 8))
        self.metin_font_entry = self._alan_olustur(metin_kutu, "Font Boyutu", self.metin_font_boyutu_var, 2, 0)
        ttk.Label(metin_kutu, text="Renk", style="Genel.TLabel").grid(row=2, column=1, sticky="w", pady=(0, 4))
        self.metin_renk_combobox = ttk.Combobox(
            metin_kutu,
            textvariable=self.metin_renk_var,
            state="readonly",
            values=["Beyaz", "Siyah", "Sarı", "Kırmızı", "Mavi"],
        )
        self.metin_renk_combobox.grid(row=3, column=1, sticky="ew", pady=(0, 6))
        ttk.Label(metin_kutu, text="Konum", style="Genel.TLabel").grid(row=4, column=0, sticky="w", pady=(0, 4))
        self.metin_konum_combobox = ttk.Combobox(
            metin_kutu,
            textvariable=self.metin_konum_var,
            state="readonly",
            values=["Üst", "Alt", "Merkez"],
        )
        self.metin_konum_combobox.grid(row=5, column=0, sticky="ew", padx=(0, 6), pady=(0, 6))
        self.metin_baslangic_entry = self._alan_olustur(
            metin_kutu, "Başlangıç Zamanı (sn)", self.metin_baslangic_var, 4, 1
        )
        self.metin_bitis_entry = self._alan_olustur(
            metin_kutu, "Bitiş Zamanı (sn)", self.metin_bitis_var, 6, 0
        )
        self.metin_sifirla_butonu = buton(metin_kutu, "Metni Sıfırla", self._metni_sifirla)
        self.metin_sifirla_butonu.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        ttk.Label(
            metin_kutu,
            text="Yazı canlı önizleme kutusunda hemen gösterilir.",
            style="Aciklama.TLabel",
            wraplength=220,
            justify="left",
        ).grid(row=8, column=0, columnspan=2, sticky="w", pady=(8, 0))

        bilgi_kutu = ttk.LabelFrame(self.arac_paneli, text="Video Bilgisi", style="Panel.TLabelframe")
        bilgi_kutu.grid(row=12, column=0, sticky="ew")
        bilgi_kutu.columnconfigure(0, weight=1)
        ttk.Label(bilgi_kutu, textvariable=self.dosya_metin, style="Genel.TLabel", wraplength=220).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        ttk.Label(bilgi_kutu, textvariable=self.sure_metin, style="Genel.TLabel").grid(
            row=1, column=0, sticky="w", pady=4
        )
        ttk.Label(bilgi_kutu, textvariable=self.cozunurluk_metin, style="Genel.TLabel").grid(
            row=2, column=0, sticky="w", pady=4
        )
        ttk.Label(bilgi_kutu, textvariable=self.fps_metin, style="Genel.TLabel").grid(
            row=3, column=0, sticky="w", pady=4
        )
        ttk.Label(bilgi_kutu, textvariable=self.ses_metin, style="Genel.TLabel").grid(
            row=4, column=0, sticky="w", pady=(4, 0)
        )

        self.kontrol_bilesenleri = [
            self.video_ac_butonu,
            self.disa_aktar_butonu,
            self.preset_combobox,
            self.baslangic_entry,
            self.bitis_entry,
            self.genislik_entry,
            self.yukseklik_entry,
            self.hiz_combobox,
            self.hiz_sifirla_butonu,
            self.sosyal_oran_combobox,
            self.rotate_combobox,
            self.aspect_ratio_combobox,
            self.flip_horizontal_checkbox,
            self.flip_vertical_checkbox,
            self.donusum_sifirla_butonu,
            self.ses_seviyesi_slider,
            self.fade_in_entry,
            self.fade_out_entry,
            self.ses_checkbox,
            self.brightness_slider,
            self.contrast_slider,
            self.saturation_slider,
            self.gamma_slider,
            self.blackwhite_checkbox,
            self.efekt_geri_al_butonu,
            self.efekt_sifirla_butonu,
            self.reset_effects_butonu,
            self.metin_entry,
            self.metin_font_entry,
            self.metin_renk_combobox,
            self.metin_konum_combobox,
            self.metin_baslangic_entry,
            self.metin_bitis_entry,
            self.metin_sifirla_butonu,
            *self.style_effect_checkbuttons,
        ]

    def _video_playeri_kur(self) -> None:
        self.video_player = VideoPlayer(
            self.onizleme_tugla,
            on_status_change=self._video_player_durumu_guncelle,
        )
        self.video_player.grid(row=0, column=0, sticky="nsew")
        self.video_player.grid_remove()
        self.efekt_onizleme_etiketi = tk.Label(
            self.video_player.render_host,
            bg="#000000",
            bd=0,
            highlightthickness=0,
        )
        self.efekt_onizleme_etiketi.place_forget()

    def _timeline_kur(self) -> None:
        self.onizleme_paneli.rowconfigure(2, weight=0)

        self.timeline_kontrol_alani = ttk.Frame(self.onizleme_paneli, style="Panel.TFrame")
        self.timeline_kontrol_alani.grid(row=2, column=0, sticky="ew", pady=(12, 6))
        self.timeline_kontrol_alani.columnconfigure(3, weight=1)

        self.split_butonu = buton(self.timeline_kontrol_alani, "Split at Playhead", self._clip_bol)
        self.split_butonu.grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.clip_sil_butonu = buton(
            self.timeline_kontrol_alani,
            "Delete Selected Clip",
            self._secili_clipi_sil,
        )
        self.clip_sil_butonu.grid(row=0, column=1, sticky="w", padx=(0, 8))

        self.timeline_sifirla_butonu = buton(
            self.timeline_kontrol_alani,
            "Reset Timeline",
            self._timeline_sifirla,
        )
        self.timeline_sifirla_butonu.grid(row=0, column=2, sticky="w")

        self.timeline = TimelineWidget(
            self.onizleme_paneli,
            on_trim_changed=self._timeline_trim_guncelle,
            thumbnail_provider=self.video_servisi.onizleme_karesi_al,
        )
        self.timeline.grid(row=3, column=0, sticky="ew", pady=(0, 0))

    def _trim_izleyicileri_bagla(self) -> None:
        self.baslangic_var.trace_add("write", self._trim_girdileri_degisti)
        self.bitis_var.trace_add("write", self._trim_girdileri_degisti)

    def _fade_izleyicileri_bagla(self) -> None:
        self.fade_in_var.trace_add("write", self._fade_onizleme_degisti)
        self.fade_out_var.trace_add("write", self._fade_onizleme_degisti)

    def _fade_onizleme_degisti(self, *_args) -> None:
        self._uygula_onizleme_ses_zarfi()

    def _hiz_katsayisini_al(self) -> float:
        hiz_metin = self.hiz_var.get().strip().lower().replace("x", "")
        try:
            hiz = float(hiz_metin or "1")
        except ValueError:
            hiz = 1.0
        return max(0.5, min(hiz, 2.0))

    def _hiz_degisti(self, _event=None) -> None:
        hiz = self._hiz_katsayisini_al()
        self.hiz_metin.set(f"{hiz:g}x")
        if hasattr(self, "video_player"):
            self.video_player.set_playback_rate(hiz)
        self.durum_guncelle(f"Video hızı {hiz:g}x olarak ayarlandı.")

    def _hizi_sifirla(self) -> None:
        self.hiz_var.set("1x")
        self.hiz_metin.set("1x")
        if hasattr(self, "hiz_combobox"):
            self.hiz_combobox.set("1x")
        if hasattr(self, "video_player"):
            self.video_player.set_playback_rate(1.0)
        self.durum_guncelle("Video hızı varsayılan değere döndürüldü.")

    def _donusum_izleyicileri_bagla(self) -> None:
        self.rotate_var.trace_add("write", self._donusum_onizleme_degisti)
        self.aspect_ratio_var.trace_add("write", self._donusum_onizleme_degisti)
        self.flip_horizontal_var.trace_add("write", self._donusum_onizleme_degisti)
        self.flip_vertical_var.trace_add("write", self._donusum_onizleme_degisti)

    def _donusum_onizleme_degisti(self, *_args) -> None:
        self._sosyal_oran_secimini_esitle()
        self.after_idle(self._efekt_onizlemesini_guncelle)

    def _donusumleri_sifirla(self) -> None:
        self.rotate_var.set("0°")
        self.aspect_ratio_var.set("Original")
        self.sosyal_oran_var.set("Orijinal")
        self.flip_horizontal_var.set(False)
        self.flip_vertical_var.set(False)
        self._efekt_onizlemesini_guncelle()
        self.durum_guncelle("Transformlar sıfırlandı.")

    def _metin_izleyicileri_bagla(self) -> None:
        for degisken in (
            self.metin_var,
            self.metin_font_boyutu_var,
            self.metin_renk_var,
            self.metin_konum_var,
            self.metin_baslangic_var,
            self.metin_bitis_var,
        ):
            degisken.trace_add("write", self._metin_onizleme_degisti)

    def _metin_onizleme_degisti(self, *_args) -> None:
        self._efekt_onizlemesini_guncelle()

    def _metni_sifirla(self) -> None:
        self.metin_var.set("")
        self.metin_font_boyutu_var.set("36")
        self.metin_renk_var.set("Beyaz")
        self.metin_konum_var.set("Alt")
        self.metin_baslangic_var.set("0")
        self.metin_bitis_var.set("")
        self._efekt_onizlemesini_guncelle()
        self.durum_guncelle("Metin alanları sıfırlandı.")

    def _preset_secildi(self, _event=None) -> None:
        preset = self.preset_var.get()
        if preset == self.PRESET_1080P:
            self.genislik_var.set("1920")
            self.yukseklik_var.set("1080")
            self.sesi_kapat_var.set(False)
            self.export_ilerleme_metin.set("Preset: 1080p MP4 uygulanacak")
        elif preset == self.PRESET_720P:
            self.genislik_var.set("1280")
            self.yukseklik_var.set("720")
            self.sesi_kapat_var.set(False)
            self.export_ilerleme_metin.set("Preset: 720p MP4 uygulanacak")
        elif preset == self.PRESET_SILENT:
            self.sesi_kapat_var.set(True)
            self.export_ilerleme_metin.set("Preset: sessiz MP4 uygulanacak")
        else:
            self.export_ilerleme_metin.set("Preset: özgün çözünürlük korunacak")

    def _progress_baslat(self) -> None:
        self.export_progress.stop()
        self.export_progress.configure(mode="indeterminate")
        self.export_progress.start(12)
        self.export_ilerleme_metin.set("Export sürüyor...")

    def _progress_tamamla(self) -> None:
        self.export_progress.stop()
        self.export_progress.configure(mode="determinate", value=100)
        self.export_ilerleme_metin.set("Export tamamlandı")

    def _progress_sifirla(self, mesaj: str = "Export hazır") -> None:
        self.export_progress.stop()
        self.export_progress.configure(mode="determinate", value=0)
        self.export_ilerleme_metin.set(mesaj)

    def _cozunurluk_coz(self) -> tuple[int | None, int | None, bool]:
        preset = self.preset_var.get()
        sessiz = self.sesi_kapat_var.get()

        if preset == self.PRESET_1080P:
            return 1920, 1080, False
        if preset == self.PRESET_720P:
            return 1280, 720, False
        if preset == self.PRESET_SILENT:
            return None, None, True
        return None, None, sessiz

    def _sosyal_oran_degisti(self, _event=None) -> None:
        sosyal_harita = {
            "Orijinal": "Original",
            "YouTube Shorts / TikTok / Reels (9:16)": "9:16",
            "Instagram Kare (1:1)": "1:1",
            "Instagram Dikey (4:5)": "4:5",
            "YouTube Yatay (16:9)": "16:9",
        }
        secim = self.sosyal_oran_var.get()
        self.aspect_ratio_var.set(sosyal_harita.get(secim, "Original"))
        self._donusum_onizleme_degisti()

    def _sosyal_oran_secimini_esitle(self) -> None:
        sosyal_harita = {
            "Original": "Orijinal",
            "9:16": "YouTube Shorts / TikTok / Reels (9:16)",
            "1:1": "Instagram Kare (1:1)",
            "4:5": "Instagram Dikey (4:5)",
            "16:9": "YouTube Yatay (16:9)",
        }
        hedef_etiket = sosyal_harita.get(self.aspect_ratio_var.get(), "Orijinal")
        if self.sosyal_oran_var.get() != hedef_etiket:
            self.sosyal_oran_var.set(hedef_etiket)

    def _donusum_ayarlarini_al(self) -> tuple[int, bool, bool, str]:
        donus_haritasi = {
            "0\N{DEGREE SIGN}": 0,
            "90\N{DEGREE SIGN}": 90,
            "180\N{DEGREE SIGN}": 180,
            "270\N{DEGREE SIGN}": 270,
        }
        oran = self.aspect_ratio_var.get().strip() or "Original"
        return (
            donus_haritasi.get(self.rotate_var.get(), 0),
            self.flip_horizontal_var.get(),
            self.flip_vertical_var.get(),
            oran,
        )

    def _ses_seviyesi_degisti(self, deger: str) -> None:
        try:
            ses_seviyesi = int(round(float(deger)))
        except ValueError:
            return
        ses_seviyesi = max(0, min(ses_seviyesi, 200))
        self.ses_seviyesi_var.set(ses_seviyesi)
        self.ses_seviyesi_metin.set(f"{ses_seviyesi}%")
        if hasattr(self, "video_player"):
            self._uygula_onizleme_ses_zarfi()

    def _brightness_degisti(self, deger: str) -> None:
        self.brightness_var.set(int(round(float(deger))))
        self.brightness_metin.set(str(self.brightness_var.get()))
        self._efekt_onizlemesini_guncelle()

    def _contrast_degisti(self, deger: str) -> None:
        self.contrast_var.set(int(round(float(deger))))
        self.contrast_metin.set(str(self.contrast_var.get()))
        self._efekt_onizlemesini_guncelle()

    def _saturation_degisti(self, deger: str) -> None:
        self.saturation_var.set(int(round(float(deger))))
        self.saturation_metin.set(f"{self.saturation_var.get()}%")
        self._efekt_onizlemesini_guncelle()

    def _gamma_degisti(self, deger: str) -> None:
        gamma = round(float(deger), 2)
        self.gamma_var.set(gamma)
        self.gamma_metin.set(f"{gamma:.2f}")
        self._efekt_onizlemesini_guncelle()

    def _blackwhite_degisti(self) -> None:
        self._efekt_degisimini_kaydet()
        self._efekt_onizlemesini_guncelle()

    def _efekt_ayarlarini_getir(self) -> dict[str, float | bool]:
        return {
            "brightness": self.brightness_var.get(),
            "contrast": self.contrast_var.get(),
            "saturation": self.saturation_var.get(),
            "gamma": self.gamma_var.get(),
            "black_white": self.blackwhite_var.get(),
        }

    def _efektler_varsayilan_mi(self) -> bool:
        ayarlar = self._efekt_ayarlarini_getir()
        return (
            ayarlar["brightness"] == 0
            and ayarlar["contrast"] == 0
            and ayarlar["saturation"] == 100
            and abs(float(ayarlar["gamma"]) - 1.0) < 0.001
            and not ayarlar["black_white"]
        )

    def _efekt_gecmisini_hazirla(self, _event=None) -> None:
        if self._efekt_guncelleniyor:
            return
        self._bekleyen_efekt_durumu = dict(self._efekt_ayarlarini_getir())

    def _efekt_degisimini_kaydet(self, _event=None) -> None:
        if self._efekt_guncelleniyor:
            return
        onceki = self._bekleyen_efekt_durumu
        self._bekleyen_efekt_durumu = None
        simdiki = self._efekt_ayarlarini_getir()
        if onceki is not None and onceki != simdiki:
            self._efekt_gecmisi.append(onceki)
            self._efekt_gecmisi = self._efekt_gecmisi[-30:]

    def _efektleri_uygula(self, ayarlar: dict[str, float | bool]) -> None:
        self._efekt_guncelleniyor = True
        try:
            self.brightness_var.set(int(ayarlar["brightness"]))
            self.contrast_var.set(int(ayarlar["contrast"]))
            self.saturation_var.set(int(ayarlar["saturation"]))
            self.gamma_var.set(float(ayarlar["gamma"]))
            self.blackwhite_var.set(bool(ayarlar["black_white"]))
            self.brightness_slider.set(self.brightness_var.get())
            self.contrast_slider.set(self.contrast_var.get())
            self.saturation_slider.set(self.saturation_var.get())
            self.gamma_slider.set(self.gamma_var.get())
            self.brightness_metin.set(str(self.brightness_var.get()))
            self.contrast_metin.set(str(self.contrast_var.get()))
            self.saturation_metin.set(f"{self.saturation_var.get()}%")
            self.gamma_metin.set(f"{self.gamma_var.get():.2f}")
        finally:
            self._efekt_guncelleniyor = False

        self._efekt_onizlemesini_guncelle()

    def _efektleri_geri_al(self) -> None:
        if not self._efekt_gecmisi:
            self.durum_guncelle("Geri alınacak bir görsel efekt değişikliği yok.")
            return
        self._efektleri_uygula(self._efekt_gecmisi.pop())
        self.durum_guncelle("Son görsel efekt değişikliği geri alındı.")

    def _efektleri_sifirla(self) -> None:
        varsayilan = {
            "brightness": 0,
            "contrast": 0,
            "saturation": 100,
            "gamma": 1.0,
            "black_white": False,
        }
        mevcut = self._efekt_ayarlarini_getir()
        if mevcut == varsayilan:
            self.durum_guncelle("Görsel efektler zaten varsayılan durumda.")
            return
        self._efekt_gecmisi.append(dict(mevcut))
        self._efekt_gecmisi = self._efekt_gecmisi[-30:]
        self._efektleri_uygula(varsayilan)
        self.durum_guncelle("Görsel efektler sıfırlandı.")

    def _stil_efektlerini_guncelle(self) -> None:
        self.selected_effects = [
            effect_key for effect_key, _label in self.STYLE_EFFECT_OPTIONS if self.style_effect_vars[effect_key].get()
        ]
        self._efekt_onizlemesini_guncelle()

    def _stil_efektlerini_sifirla(self) -> None:
        for effect_var in self.style_effect_vars.values():
            effect_var.set(False)
        self.selected_effects = []
        self._efekt_onizlemesini_guncelle()
        self.durum_guncelle("Stil efektleri sıfırlandı.")

    def _efekt_onizlemesini_guncelle(self) -> None:
        if not hasattr(self, "efekt_onizleme_resim"):
            return
        if hasattr(self, "efekt_onizleme_etiketi"):
            self.efekt_onizleme_etiketi.place_forget()
        if not self.video_servisi.video_var_mi():
            self.efekt_onizleme_resim.configure(image="", text="Video açıldığında burada görünür")
            return

        try:
            zaman = self.video_player.controller.state.current_time if hasattr(self, "video_player") else 0.0
            rotate_degrees, flip_horizontal, flip_vertical, aspect_ratio = self._donusum_ayarlarini_al()
            gorsel = self.video_servisi.onizleme_karesi_al(
                zaman,
                rotate_degrees=rotate_degrees,
                flip_horizontal=flip_horizontal,
                flip_vertical=flip_vertical,
                aspect_ratio=aspect_ratio,
                **self._efekt_ayarlarini_getir(),
                style_effects=self.selected_effects,
                **self._metin_katmani_verisini_al(strict=False),
            )
        except Exception:
            self.efekt_onizleme_resim.configure(image="", text="Önizleme alınamadı")
            return

        gorsel.thumbnail((220, 124))
        self.efekt_onizleme_gorseli = ImageTk.PhotoImage(gorsel)
        self.efekt_onizleme_resim.configure(image=self.efekt_onizleme_gorseli, text="")

    def _fade_degerlerini_al(self, *, strict: bool) -> tuple[float, float]:
        return (
            self._tek_fade_degeri_al(self.fade_in_var.get(), "Fade In", strict=strict),
            self._tek_fade_degeri_al(self.fade_out_var.get(), "Fade Out", strict=strict),
        )

    def _tek_fade_degeri_al(self, ham_deger: str, alan_adi: str, *, strict: bool) -> float:
        metin = ham_deger.strip()
        if not metin:
            return 0.0
        try:
            deger = float(metin)
        except ValueError:
            if strict:
                raise ValueError(f"{alan_adi} alanına geçerli sayı girin.")
            return 0.0
        if deger < 0:
            if strict:
                raise ValueError(f"{alan_adi} negatif olamaz.")
            return 0.0
        return deger

    def _metin_katmani_verisini_al(self, *, strict: bool = True) -> dict[str, object]:
        bos_deger = {
            "overlay_text": "",
            "overlay_font_size": 36,
            "overlay_color": "white",
            "overlay_position": "bottom",
            "overlay_start": None,
            "overlay_end": None,
        }

        metin = self.metin_var.get().strip()
        if not metin:
            return bos_deger

        try:
            font_boyutu = int(self.metin_font_boyutu_var.get().strip() or "36")
        except ValueError as hata:
            if not strict:
                return bos_deger
            raise ValueError("Font boyutu için geçerli tam sayı girin.") from hata
        if font_boyutu <= 0:
            if not strict:
                return bos_deger
            raise ValueError("Font boyutu sıfırdan büyük olmalıdır.")

        try:
            baslangic = float(self.metin_baslangic_var.get().strip() or "0")
        except ValueError as hata:
            if not strict:
                return bos_deger
            raise ValueError("Metin başlangıç zamanı için geçerli sayı girin.") from hata

        bitis_metin = self.metin_bitis_var.get().strip()
        try:
            bitis = float(bitis_metin) if bitis_metin else None
        except ValueError as hata:
            if not strict:
                return bos_deger
            raise ValueError("Metin bitiş zamanı için geçerli sayı girin.") from hata

        if baslangic < 0:
            if not strict:
                return bos_deger
            raise ValueError("Metin başlangıç zamanı negatif olamaz.")
        if bitis is not None and bitis <= baslangic:
            if not strict:
                return bos_deger
            raise ValueError("Metin bitiş zamanı başlangıçtan büyük olmalıdır.")

        renk_haritasi = {
            "Beyaz": "white",
            "Siyah": "black",
            "Sarı": "yellow",
            "Kırmızı": "red",
            "Mavi": "blue",
        }
        konum_haritasi = {
            "Üst": "top",
            "Alt": "bottom",
            "Merkez": "center",
        }

        return {
            "overlay_text": metin,
            "overlay_font_size": font_boyutu,
            "overlay_color": renk_haritasi.get(self.metin_renk_var.get(), "white"),
            "overlay_position": konum_haritasi.get(self.metin_konum_var.get(), "bottom"),
            "overlay_start": baslangic,
            "overlay_end": bitis,
        }


    def _uygula_onizleme_ses_zarfi(self) -> None:
        if not hasattr(self, "video_player"):
            return
        if not self.video_player.controller.state.is_loaded:
            return

        taban_ses = self.ses_seviyesi_var.get()
        fade_in, fade_out = self._fade_degerlerini_al(strict=False)
        mevcut_zaman = self.video_player.controller.state.current_time
        toplam_sure = self.video_player.controller.state.total_duration or self.timeline.duration

        try:
            baslangic = float(self.baslangic_var.get().strip() or "0")
        except ValueError:
            baslangic = 0.0

        try:
            bitis = float(self.bitis_var.get().strip()) if self.bitis_var.get().strip() else toplam_sure
        except ValueError:
            bitis = toplam_sure

        bitis = max(baslangic, min(bitis, toplam_sure if toplam_sure > 0 else bitis))
        clip_suresi = max(bitis - baslangic, 0.0)
        fade_in = min(fade_in, clip_suresi)
        fade_out = min(fade_out, clip_suresi)

        ses_katsayisi = 1.0
        if fade_in > 0 and baslangic <= mevcut_zaman <= baslangic + fade_in:
            ses_katsayisi = min(ses_katsayisi, max(0.0, (mevcut_zaman - baslangic) / fade_in))
        if fade_out > 0 and bitis - fade_out <= mevcut_zaman <= bitis:
            ses_katsayisi = min(ses_katsayisi, max(0.0, (bitis - mevcut_zaman) / fade_out))
        if mevcut_zaman > bitis and fade_out > 0:
            ses_katsayisi = 0.0

        self.video_player.set_volume(int(round(taban_ses * ses_katsayisi)))

    def _clip_bol(self) -> None:
        if not self.video_servisi.video_var_mi():
            self._hata_goster("Önce bir video açmalısınız.")
            return

        playhead = self.video_player.controller.state.current_time
        if not self.timeline.split_at(playhead):
            self.durum_guncelle("Clip, mevcut oynatma konumunda bölünemedi.")
            return

        self._timeline_trim_guncelle(self.timeline.get_trim_start(), self.timeline.get_trim_end())
        self.durum_guncelle(f"Clip {playhead:.2f} saniyede bölündü.")

    def _secili_clipi_sil(self) -> None:
        if not self.video_servisi.video_var_mi():
            self._hata_goster("Önce bir video açmalısınız.")
            return

        if not self.timeline.delete_selected_clip():
            self.durum_guncelle("En az bir clip kalmalıdır; seçili clip silinemedi.")
            return

        self._timeline_trim_guncelle(self.timeline.get_trim_start(), self.timeline.get_trim_end())
        self.durum_guncelle("Seçili clip silindi.")

    def _timeline_sifirla(self) -> None:
        if not self.video_servisi.video_var_mi():
            self._hata_goster("Önce bir video açmalısınız.")
            return

        self.timeline.reset()
        self._timeline_trim_guncelle(self.timeline.get_trim_start(), self.timeline.get_trim_end())
        self.durum_guncelle("Timeline sıfırlandı; tek clip görünümüne dönüldü.")

    def _goster_video_player(self) -> None:
        self.onizleme_tuvali.grid_remove()
        self.onizleme_y_kaydirma.grid_remove()
        self.onizleme_x_kaydirma.grid_remove()
        self.onizleme_etiketi.place_forget()
        self.video_player.grid()
        self.video_player.tkraise()

    def _goster_statik_onizleme(self) -> None:
        if hasattr(self, "video_player"):
            self.video_player.grid_remove()
        self.onizleme_tuvali.grid(row=0, column=0, sticky="nsew")
        self.onizleme_y_kaydirma.grid(row=0, column=1, sticky="ns")
        self.onizleme_x_kaydirma.grid(row=1, column=0, sticky="ew")

    def _timeline_trim_guncelle(self, baslangic: float, bitis: float) -> None:
        self._trim_sync_locked = True
        try:
            self.baslangic_var.set(f"{baslangic:.2f}".rstrip("0").rstrip("."))
            self.bitis_var.set(f"{bitis:.2f}".rstrip("0").rstrip("."))
        finally:
            self._trim_sync_locked = False

        if self.video_servisi.video_var_mi() and self.video_player.controller.state.is_loaded:
            self.video_player.controller.seek(baslangic)
            self.timeline.update_scrubber(baslangic)
            self._uygula_onizleme_ses_zarfi()
            self._efekt_onizlemesini_guncelle()

    def _trim_girdileri_degisti(self, *_args) -> None:
        if self._trim_sync_locked or not hasattr(self, "timeline"):
            return
        if self.timeline.duration <= 0:
            return

        try:
            baslangic = float(self.baslangic_var.get().strip() or "0")
            bitis = float(self.bitis_var.get().strip()) if self.bitis_var.get().strip() else self.timeline.duration
        except ValueError:
            return

        if baslangic < 0:
            baslangic = 0.0
        if bitis > self.timeline.duration:
            bitis = self.timeline.duration
        if baslangic >= bitis:
            return

        self.timeline.set_trim(baslangic, bitis)

    def _sync_timeline_trim_to_inputs(self) -> None:
        if not hasattr(self, "timeline"):
            return
        self._timeline_trim_guncelle(
            self.timeline.get_trim_start(),
            self.timeline.get_trim_end(),
        )

    def _video_player_durumu_guncelle(self, mesaj: str) -> None:
        if hasattr(self, "timeline") and hasattr(self, "video_player"):
            self.timeline.update_scrubber(self.video_player.controller.state.current_time)
            self._uygula_onizleme_ses_zarfi()
            self._efekt_onizlemesini_guncelle()
        if self.video_servisi.video_var_mi():
            self.durum_guncelle(mesaj)

    def _alan_olustur(
        self, parent: ttk.LabelFrame, etiket: str, degisken: tk.StringVar, satir: int, sutun: int
    ) -> ttk.Entry:
        ttk.Label(parent, text=etiket, style="Genel.TLabel").grid(
            row=satir, column=sutun, sticky="w", padx=(0, 6), pady=(0, 4)
        )
        giris = ttk.Entry(parent, textvariable=degisken, style="Karanlik.TEntry", width=10)
        giris.grid(row=satir + 1, column=sutun, sticky="ew", padx=(0, 6 if sutun == 0 else 0), pady=(0, 6))
        return giris

    def video_ac(self) -> None:
        if self.disa_aktariliyor:
            self.durum_guncelle("Dışa aktarma devam ederken yeni video açılamaz.")
            return

        self.durum_guncelle("Video seçiliyor...")
        dosya_yolu = filedialog.askopenfilename(title="Video Aç", filetypes=DESTEKLENEN_VIDEO_DOSYALARI)
        if not dosya_yolu:
            self.durum_guncelle("Video seçimi iptal edildi.")
            return

        try:
            bilgiler = self.video_servisi.ac(dosya_yolu)
        except Exception as hata:
            self._hata_goster(f"Video açılamadı: {hata}")
            return

        self.baslangic_var.set("0")
        self.bitis_var.set(str(bilgiler["sure"]))
        self.genislik_var.set("")
        self.yukseklik_var.set("")
        self.fade_in_var.set("0")
        self.fade_out_var.set("0")
        self.rotate_var.set("0\N{DEGREE SIGN}")
        self.aspect_ratio_var.set("Original")
        self.sosyal_oran_var.set("Orijinal")
        self.flip_horizontal_var.set(False)
        self.flip_vertical_var.set(False)
        self.metin_var.set("")
        self.metin_font_boyutu_var.set("36")
        self.metin_renk_var.set("Beyaz")
        self.metin_konum_var.set("Alt")
        self.metin_baslangic_var.set("0")
        self.metin_bitis_var.set("")
        self.sesi_kapat_var.set(False)
        self.ses_seviyesi_var.set(100)
        self.ses_seviyesi_slider.set(100)
        self.ses_seviyesi_metin.set("100%")
        self.brightness_var.set(0)
        self.contrast_var.set(0)
        self.saturation_var.set(100)
        self.gamma_var.set(1.0)
        self.blackwhite_var.set(False)
        for effect_var in self.style_effect_vars.values():
            effect_var.set(False)
        self.selected_effects = []
        self.brightness_slider.set(0)
        self.contrast_slider.set(0)
        self.saturation_slider.set(100)
        self.gamma_slider.set(1.0)
        self.brightness_metin.set("0")
        self.contrast_metin.set("0")
        self.saturation_metin.set("100%")
        self.gamma_metin.set("1.0")
        self.preset_var.set(self.PRESET_ORIGINAL)
        self._progress_sifirla()
        cozunurluk = str(bilgiler["cozunurluk"]).split(" x ")
        if len(cozunurluk) == 2:
            self.genislik_var.set(cozunurluk[0])
            self.yukseklik_var.set(cozunurluk[1])
        self._bilgileri_guncelle()
        self._onizleme_yenile()
        self.timeline.set_clip(float(bilgiler["sure"]))
        self.timeline.update_scrubber(0.0)
        self.video_player.load_video(dosya_yolu, duration=float(bilgiler["sure"]))
        self.video_player.set_playback_rate(self._hiz_katsayisini_al())
        self._uygula_onizleme_ses_zarfi()
        self._efekt_gecmisi.clear()
        self._bekleyen_efekt_durumu = None
        self._goster_video_player()
        self._efekt_onizlemesini_guncelle()
        self.durum_guncelle("Video açıldı. Trim ve dışa aktarma ayarları hazır.")

    def disa_aktar(self) -> None:
        if self.disa_aktariliyor:
            self.durum_guncelle("Zaten devam eden bir dışa aktarma işlemi var.")
            return
        if not self.video_servisi.video_var_mi():
            self._hata_goster("Bu işlemi yapabilmek için önce bir video açmalısınız.")
            return

        self._sync_timeline_trim_to_inputs()
        self.durum_guncelle("Dışa aktarma konumu seçiliyor...")
        hedef_yol = filedialog.asksaveasfilename(
            title="Videoyu Dışa Aktar",
            defaultextension=".mp4",
            filetypes=[
                ("MP4", "*.mp4"),
                ("MOV", "*.mov"),
                ("AVI", "*.avi"),
                ("Tüm Dosyalar", "*.*"),
            ],
        )
        if not hedef_yol:
            self.durum_guncelle("Dışa aktarma işlemi iptal edildi. Video üzerinde değişiklik yapılmadı.")
            return

        try:
            baslangic = float(self.baslangic_var.get() or "0")
            bitis = float(self.bitis_var.get()) if self.bitis_var.get().strip() else None
            fade_in, fade_out = self._fade_degerlerini_al(strict=True)
            hiz_katsayisi = self._hiz_katsayisini_al()
            metin_ayarlari = self._metin_katmani_verisini_al()
        except ValueError as hata:
            self._hata_goster(str(hata))
            return

        try:
            manuel_genislik, manuel_yukseklik = self._boyut_al()
        except ValueError as hata:
            self._hata_goster(str(hata))
            return

        rotate_degrees, flip_horizontal, flip_vertical, aspect_ratio = self._donusum_ayarlarini_al()
        preset_genislik, preset_yukseklik, preset_sessiz = self._cozunurluk_coz()
        genislik = preset_genislik if preset_genislik is not None else manuel_genislik
        yukseklik = preset_yukseklik if preset_yukseklik is not None else manuel_yukseklik
        sesi_kapat = preset_sessiz if self.preset_var.get() == self.PRESET_SILENT else self.sesi_kapat_var.get()

        self._kontrolleri_ayarla(False)
        self.disa_aktariliyor = True
        self._progress_baslat()
        self.durum_guncelle("Video dışa aktarma başladı. Arayüz açık kalacak, lütfen bekleyin.")

        self.export_thread = threading.Thread(
            target=self._disa_aktar_is_parcasi,
            args=(
                hedef_yol,
                baslangic,
                bitis,
                genislik,
                yukseklik,
                rotate_degrees,
                flip_horizontal,
                flip_vertical,
                aspect_ratio,
                hiz_katsayisi,
                sesi_kapat,
                self.ses_seviyesi_var.get(),
                fade_in,
                fade_out,
                self.brightness_var.get(),
                self.contrast_var.get(),
                self.saturation_var.get(),
                self.gamma_var.get(),
                self.blackwhite_var.get(),
                list(self.selected_effects),
                metin_ayarlari,
            ),
            daemon=True,
        )
        self.export_thread.start()
        self.after(200, self._export_sonucunu_kontrol_et)

    def _disa_aktar_is_parcasi(
        self,
        hedef_yol: str,
        baslangic: float,
        bitis: float | None,
        genislik: int | None,
        yukseklik: int | None,
        rotate_degrees: int,
        flip_horizontal: bool,
        flip_vertical: bool,
        aspect_ratio: str,
        speed_factor: float,
        sesi_kapat: bool,
        ses_seviyesi: int,
        fade_in: float,
        fade_out: float,
        brightness: int,
        contrast: int,
        saturation: int,
        gamma: float,
        black_white: bool,
        style_effects: list[str],
        metin_ayarlari: dict[str, object],
    ) -> None:
        try:
            self.video_servisi.disa_aktar(
                hedef_yol=hedef_yol,
                baslangic=baslangic,
                bitis=bitis,
                genislik=genislik,
                yukseklik=yukseklik,
                rotate_degrees=rotate_degrees,
                flip_horizontal=flip_horizontal,
                flip_vertical=flip_vertical,
                aspect_ratio=aspect_ratio,
                speed_factor=speed_factor,
                sesi_kapat=sesi_kapat,
                ses_seviyesi=ses_seviyesi,
                fade_in=fade_in,
                fade_out=fade_out,
                brightness=brightness,
                contrast=contrast,
                saturation=saturation,
                gamma=gamma,
                black_white=black_white,
                style_effects=style_effects,
                **metin_ayarlari,
            )
        except Exception as hata:
            self.export_kuyrugu.put(("hata", str(hata)))
            return

        self.export_kuyrugu.put(("basari", hedef_yol))

    def _export_sonucunu_kontrol_et(self) -> None:
        try:
            durum, icerik = self.export_kuyrugu.get_nowait()
        except queue.Empty:
            if self.disa_aktariliyor:
                self.after(500, self._export_sonucunu_kontrol_et)
            return

        self.disa_aktariliyor = False
        self._kontrolleri_ayarla(True)
        self.export_thread = None

        if durum == "basari":
            self._progress_tamamla()
            self.durum_guncelle("Video başarıyla dışa aktarıldı.")
            messagebox.showinfo("İşlem Tamamlandı", f"Video başarıyla dışa aktarıldı.\n\nDosya konumu:\n{icerik}")
            return

        self._progress_sifirla("Export başarısız oldu")
        self._hata_goster(f"Dışa aktarma sırasında hata oluştu: {icerik}")

    def _kontrolleri_ayarla(self, etkin: bool) -> None:
        durum = "normal" if etkin else "disabled"
        for bilesen in self.kontrol_bilesenleri:
            bilesen.configure(state=durum)

    def _boyut_al(self) -> tuple[int | None, int | None]:
        genislik_metin = self.genislik_var.get().strip()
        yukseklik_metin = self.yukseklik_var.get().strip()
        if not genislik_metin and not yukseklik_metin:
            return None, None
        if not genislik_metin or not yukseklik_metin:
            raise ValueError("Yeni boyut için genişlik ve yükseklik birlikte girilmelidir.")

        try:
            genislik = int(genislik_metin)
            yukseklik = int(yukseklik_metin)
        except ValueError as hata:
            raise ValueError("Boyut alanlarına geçerli tam sayı girin.") from hata
        return genislik, yukseklik

    def _bilgileri_guncelle(self) -> None:
        bilgiler = self.video_servisi.bilgileri_getir()
        self.dosya_metin.set(f"Dosya: {bilgiler['dosya']}")
        self.sure_metin.set(f"Süre: {bilgiler['sure']} saniye")
        self.cozunurluk_metin.set(f"Çözünürlük: {bilgiler['cozunurluk']}")
        self.fps_metin.set(f"Kare Hızı: {bilgiler['fps']} FPS")
        self.ses_metin.set(f"Ses: {bilgiler['ses']}")

    def _onizleme_yenile(self, _event=None) -> None:
        if not self.video_servisi.video_var_mi():
            self._goster_statik_onizleme()
            self.timeline.set_clip(0.0)
            self.timeline.update_scrubber(0.0)
            self.onizleme_tuvali.delete("all")
            self.onizleme_etiketi.config(text="Henüz medya yüklenmedi")
            self.onizleme_etiketi.place(relx=0.5, rely=0.5, anchor="center")
            return

        try:
            gorsel = self.video_servisi.onizleme_karesi_al()
        except Exception as hata:
            self._goster_statik_onizleme()
            self.onizleme_tuvali.delete("all")
            self.onizleme_etiketi.config(text=f"Önizleme alınamadı\n{hata}")
            self.onizleme_etiketi.place(relx=0.5, rely=0.5, anchor="center")
            return

        canvas_genislik = max(self.onizleme_tuvali.winfo_width(), 1)
        canvas_yukseklik = max(self.onizleme_tuvali.winfo_height(), 1)
        gorsel.thumbnail((canvas_genislik - 20, canvas_yukseklik - 20))

        self.onizleme_gorseli = ImageTk.PhotoImage(gorsel)
        self.onizleme_tuvali.delete("all")
        self.onizleme_tuvali.create_image(
            canvas_genislik // 2,
            canvas_yukseklik // 2,
            image=self.onizleme_gorseli,
            anchor="center",
        )
        self.onizleme_etiketi.place_forget()

    def _hata_goster(self, mesaj: str) -> None:
        messagebox.showwarning("Uyarı", mesaj)
        self.durum_guncelle(mesaj)

    def kapat(self) -> None:
        if hasattr(self, "video_player"):
            self.video_player.unload_video()
        self.video_servisi.kapat()
