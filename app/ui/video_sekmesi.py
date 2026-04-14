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

        self.baslangic_var = tk.StringVar(value="0")
        self.bitis_var = tk.StringVar(value="")
        self.genislik_var = tk.StringVar(value="")
        self.yukseklik_var = tk.StringVar(value="")
        self.fade_in_var = tk.StringVar(value="0")
        self.fade_out_var = tk.StringVar(value="0")
        self.sesi_kapat_var = tk.BooleanVar(value=False)
        self.ses_seviyesi_var = tk.IntVar(value=100)

        self._icerik_kur()
        self._video_playeri_kur()
        self._timeline_kur()
        self._trim_izleyicileri_bagla()
        self._fade_izleyicileri_bagla()
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

        trim_kutu = ttk.LabelFrame(self.arac_paneli, text="Trim Ayarları", style="Panel.TLabelframe")
        trim_kutu.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        trim_kutu.columnconfigure((0, 1), weight=1)
        self.baslangic_entry = self._alan_olustur(trim_kutu, "Başlangıç (sn)", self.baslangic_var, 0, 0)
        self.bitis_entry = self._alan_olustur(trim_kutu, "Bitiş (sn)", self.bitis_var, 0, 1)

        boyut_kutu = ttk.LabelFrame(self.arac_paneli, text="Yeniden Boyutlandır", style="Panel.TLabelframe")
        boyut_kutu.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        boyut_kutu.columnconfigure((0, 1), weight=1)
        self.genislik_entry = self._alan_olustur(boyut_kutu, "Genişlik", self.genislik_var, 0, 0)
        self.yukseklik_entry = self._alan_olustur(boyut_kutu, "Yükseklik", self.yukseklik_var, 0, 1)
        ttk.Label(
            boyut_kutu,
            text="Boş bırakırsanız özgün boyut korunur.",
            style="Genel.TLabel",
            wraplength=220,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))

        ses_kutu = ttk.LabelFrame(self.arac_paneli, text="Ses Ayarı", style="Panel.TLabelframe")
        ses_kutu.grid(row=4, column=0, sticky="ew", pady=(0, 12))
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

        bilgi_kutu = ttk.LabelFrame(self.arac_paneli, text="Video Bilgisi", style="Panel.TLabelframe")
        bilgi_kutu.grid(row=5, column=0, sticky="ew")
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
            self.baslangic_entry,
            self.bitis_entry,
            self.genislik_entry,
            self.yukseklik_entry,
            self.ses_seviyesi_slider,
            self.fade_in_entry,
            self.fade_out_entry,
            self.ses_checkbox,
        ]

    def _video_playeri_kur(self) -> None:
        """Create the player as the main preview component, hidden until video load."""
        self.video_player = VideoPlayer(
            self.onizleme_tugla,
            on_status_change=self._video_player_durumu_guncelle,
        )
        self.video_player.grid(row=0, column=0, sticky="nsew")
        self.video_player.grid_remove()

    def _timeline_kur(self) -> None:
        """Create timeline controls and passive timeline below the preview area."""
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

    def _ses_seviyesi_degisti(self, deger: str) -> None:
        try:
            ses_seviyesi = int(round(float(deger)))
        except ValueError:
            return
        ses_seviyesi = max(0, min(ses_seviyesi, 200))
        self.ses_seviyesi_var.set(ses_seviyesi)
        self.ses_seviyesi_metin.set(f"{ses_seviyesi}%")
        self._uygula_onizleme_ses_zarfi()

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

    def _uygula_onizleme_ses_zarfi(self) -> None:
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
        """Split the selected clip at the current playhead position."""
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
        """Delete the selected clip while keeping at least one clip on the timeline."""
        if not self.video_servisi.video_var_mi():
            self._hata_goster("Önce bir video açmalısınız.")
            return

        if not self.timeline.delete_selected_clip():
            self.durum_guncelle("En az bir clip kalmalıdır; seçili clip silinemedi.")
            return

        self._timeline_trim_guncelle(self.timeline.get_trim_start(), self.timeline.get_trim_end())
        self.durum_guncelle("Seçili clip silindi.")

    def _timeline_sifirla(self) -> None:
        """Reset split and trim edits back to the original single-clip state."""
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
        """Sync selected clip bounds into trim inputs and player position."""
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

    def _trim_girdileri_degisti(self, *_args) -> None:
        """Push left-side trim input changes back into the timeline."""
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
        """Ensure export uses the latest trim values coming from the timeline."""
        if not hasattr(self, "timeline"):
            return
        self._timeline_trim_guncelle(
            self.timeline.get_trim_start(),
            self.timeline.get_trim_end(),
        )

    def _video_player_durumu_guncelle(self, mesaj: str) -> None:
        """Forward player shell status and keep timeline synced to playback state."""
        if hasattr(self, "timeline") and hasattr(self, "video_player"):
            self.timeline.update_scrubber(self.video_player.controller.state.current_time)
            self._uygula_onizleme_ses_zarfi()
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
        except Exception as hata:  # pragma: no cover - arayuz hatasi
            self._hata_goster(f"Video açılamadı: {hata}")
            return

        self.baslangic_var.set("0")
        self.bitis_var.set(str(bilgiler["sure"]))
        self.genislik_var.set("")
        self.yukseklik_var.set("")
        self.fade_in_var.set("0")
        self.fade_out_var.set("0")
        self.sesi_kapat_var.set(False)
        self.ses_seviyesi_var.set(100)
        self.ses_seviyesi_slider.set(100)
        self.ses_seviyesi_metin.set("100%")
        cozunurluk = str(bilgiler["cozunurluk"]).split(" x ")
        if len(cozunurluk) == 2:
            self.genislik_var.set(cozunurluk[0])
            self.yukseklik_var.set(cozunurluk[1])
        self._bilgileri_guncelle()
        self._onizleme_yenile()
        self.timeline.set_clip(float(bilgiler["sure"]))
        self.timeline.update_scrubber(0.0)
        self.video_player.load_video(dosya_yolu, duration=float(bilgiler["sure"]))
        self._uygula_onizleme_ses_zarfi()
        self._goster_video_player()
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
        except ValueError as hata:
            self._hata_goster(str(hata))
            return

        try:
            genislik, yukseklik = self._boyut_al()
        except ValueError as hata:
            self._hata_goster(str(hata))
            return

        self._kontrolleri_ayarla(False)
        self.disa_aktariliyor = True
        self.durum_guncelle("Video dışa aktarma başladı. Arayüz açık kalacak, lütfen bekleyin.")

        self.export_thread = threading.Thread(
            target=self._disa_aktar_is_parcasi,
            args=(
                hedef_yol,
                baslangic,
                bitis,
                genislik,
                yukseklik,
                self.sesi_kapat_var.get(),
                self.ses_seviyesi_var.get(),
                fade_in,
                fade_out,
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
        sesi_kapat: bool,
        ses_seviyesi: int,
        fade_in: float,
        fade_out: float,
    ) -> None:
        try:
            self.video_servisi.disa_aktar(
                hedef_yol=hedef_yol,
                baslangic=baslangic,
                bitis=bitis,
                genislik=genislik,
                yukseklik=yukseklik,
                sesi_kapat=sesi_kapat,
                ses_seviyesi=ses_seviyesi,
                fade_in=fade_in,
                fade_out=fade_out,
            )
        except Exception as hata:  # pragma: no cover - arayuz hatasi
            self.export_kuyrugu.put(("hata", str(hata)))
            return

        self.export_kuyrugu.put(("basari", hedef_yol))

    def _export_sonucunu_kontrol_et(self) -> None:
        try:
            durum, icerik = self.export_kuyrugu.get_nowait()
        except queue.Empty:
            if self.disa_aktariliyor:
                self.durum_guncelle("Video dışa aktarılıyor. İşlem tamamlanana kadar ayarlar geçici olarak kilitli.")
                self.after(500, self._export_sonucunu_kontrol_et)
            return

        self.disa_aktariliyor = False
        self._kontrolleri_ayarla(True)
        self.export_thread = None

        if durum == "basari":
            self.durum_guncelle("Video başarıyla dışa aktarıldı.")
            messagebox.showinfo("İşlem Tamamlandı", f"Video başarıyla dışa aktarıldı.\n\nDosya konumu:\n{icerik}")
            return

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
        except Exception as hata:  # pragma: no cover - arayuz hatasi
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
