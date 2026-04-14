import tkinter as tk
from tkinter import ttk

from app.ui import tema
from app.ui.bilesenler import stil_uygula
from app.ui.fotograf_sekmesi import FotografSekmesi
from app.ui.video_sekmesi import VideoSekmesi


class MedyaDuzenleyiciUygulamasi:
    def __init__(self) -> None:
        self.pencere = tk.Tk()
        self.pencere.title("Karanlık Kare")
        self.pencere.geometry(f"{tema.PENCERE_GENISLIK}x{tema.PENCERE_YUKSEKLIK}")
        self.pencere.minsize(1080, 680)
        self.pencere.protocol("WM_DELETE_WINDOW", self._uygulamayi_kapat)

        stil_uygula(self.pencere)

        self.durum_metni = tk.StringVar(value="Uygulama hazır.")
        self._ana_yapiyi_kur()

    def _ana_yapiyi_kur(self) -> None:
        ana_cerceve = ttk.Frame(self.pencere, style="Genel.TFrame", padding=12)
        ana_cerceve.pack(fill="both", expand=True)
        ana_cerceve.columnconfigure(0, weight=1)
        ana_cerceve.rowconfigure(1, weight=1)

        baslik = ttk.Label(
            ana_cerceve,
            text="Karanlık Kare Medya Düzenleyici",
            style="Baslik.TLabel",
        )
        baslik.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.sekme_alani = ttk.Notebook(ana_cerceve, style="Karanlik.TNotebook")
        self.sekme_alani.grid(row=1, column=0, sticky="nsew")

        self.fotograf_sekmesi = FotografSekmesi(self.sekme_alani, self.durum_guncelle)
        self.video_sekmesi = VideoSekmesi(self.sekme_alani, self.durum_guncelle)

        self.sekme_alani.add(self.fotograf_sekmesi, text="Fotoğraf Düzenleme")
        self.sekme_alani.add(self.video_sekmesi, text="Video Düzenleme")
        self.sekme_alani.bind("<<NotebookTabChanged>>", self._sekme_degisti)

        durum_cubugu = ttk.Frame(ana_cerceve, style="Durum.TFrame", padding=(12, 8))
        durum_cubugu.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        durum_cubugu.columnconfigure(0, weight=1)

        ttk.Label(durum_cubugu, textvariable=self.durum_metni, style="Durum.TLabel").grid(
            row=0, column=0, sticky="w"
        )

    def _sekme_degisti(self, _event=None) -> None:
        secili = self.sekme_alani.tab(self.sekme_alani.select(), "text")
        self.durum_guncelle(f"{secili} sekmesi görüntüleniyor.")

    def durum_guncelle(self, mesaj: str) -> None:
        self.durum_metni.set(mesaj)
        self.pencere.update_idletasks()

    def _uygulamayi_kapat(self) -> None:
        self.video_sekmesi.kapat()
        self.pencere.destroy()

    def calistir(self) -> None:
        self.pencere.mainloop()
