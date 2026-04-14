import tkinter as tk
from tkinter import ttk

from app.ui import tema


class SekmeDuzeni(ttk.Frame):
    def __init__(self, parent: ttk.Notebook, arac_baslik: str, onizleme_baslik: str) -> None:
        super().__init__(parent, style="Genel.TFrame", padding=16)
        self.columnconfigure(0, weight=0, minsize=320)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.arac_kapsayici = ttk.Frame(self, style="Panel.TFrame")
        self.arac_kapsayici.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self.arac_kapsayici.columnconfigure(0, weight=1)
        self.arac_kapsayici.rowconfigure(0, weight=1)

        self.arac_tuvali = tk.Canvas(
            self.arac_kapsayici,
            bg=tema.IKINCIL_ARKA_PLAN,
            highlightthickness=0,
            bd=0,
        )
        self.arac_tuvali.grid(row=0, column=0, sticky="nsew")

        self.arac_kaydirma = ttk.Scrollbar(
            self.arac_kapsayici,
            orient="vertical",
            command=self.arac_tuvali.yview,
        )
        self.arac_kaydirma.grid(row=0, column=1, sticky="ns")
        self.arac_tuvali.configure(yscrollcommand=self.arac_kaydirma.set)

        self.arac_paneli = ttk.Frame(self.arac_tuvali, style="Panel.TFrame", padding=16)
        self.arac_paneli.columnconfigure(0, weight=1)

        self._arac_pencere = self.arac_tuvali.create_window((0, 0), window=self.arac_paneli, anchor="nw")

        self.arac_paneli.bind("<Configure>", self._arac_scroll_alani_guncelle)
        self.arac_tuvali.bind("<Configure>", self._arac_genislik_guncelle)

        self._kaydirma_bagla(self.arac_tuvali)
        self._kaydirma_bagla(self.arac_paneli)

        self.onizleme_paneli = ttk.Frame(self, style="Panel.TFrame", padding=16)
        self.onizleme_paneli.grid(row=0, column=1, sticky="nsew")
        self.onizleme_paneli.columnconfigure(0, weight=1)
        self.onizleme_paneli.rowconfigure(1, weight=1)

        ttk.Label(self.arac_paneli, text=arac_baslik, style="Baslik.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 14)
        )
        ttk.Label(self.onizleme_paneli, text=onizleme_baslik, style="Baslik.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 14)
        )

        self.onizleme_tugla = tk.Frame(
            self.onizleme_paneli,
            bg=tema.ONIZLEME_ZEMIN,
            highlightthickness=1,
            highlightbackground=tema.CERCEVE,
        )
        self.onizleme_tugla.grid(row=1, column=0, sticky="nsew")
        self.onizleme_tugla.rowconfigure(0, weight=1)
        self.onizleme_tugla.columnconfigure(0, weight=1)

        self.onizleme_tuvali = tk.Canvas(
            self.onizleme_tugla,
            bg=tema.ONIZLEME_ZEMIN,
            highlightthickness=0,
            bd=0,
        )
        self.onizleme_tuvali.grid(row=0, column=0, sticky="nsew")
        self.onizleme_y_kaydirma = ttk.Scrollbar(
            self.onizleme_tugla,
            orient="vertical",
            command=self.onizleme_tuvali.yview,
        )
        self.onizleme_y_kaydirma.grid(row=0, column=1, sticky="ns")
        self.onizleme_x_kaydirma = ttk.Scrollbar(
            self.onizleme_tugla,
            orient="horizontal",
            command=self.onizleme_tuvali.xview,
        )
        self.onizleme_x_kaydirma.grid(row=1, column=0, sticky="ew")
        self.onizleme_tuvali.configure(
            yscrollcommand=self.onizleme_y_kaydirma.set,
            xscrollcommand=self.onizleme_x_kaydirma.set,
        )

        self.onizleme_etiketi = tk.Label(
            self.onizleme_tugla,
            text="Henüz medya yüklenmedi",
            bg=tema.ONIZLEME_ZEMIN,
            fg=tema.SOLUK_METIN,
            font=tema.YAZI_TIPI_BASLIK,
            justify="center",
        )
        self.onizleme_etiketi.place(relx=0.5, rely=0.5, anchor="center")

    def _arac_scroll_alani_guncelle(self, _event=None) -> None:
        self.arac_tuvali.configure(scrollregion=self.arac_tuvali.bbox("all"))

    def _arac_genislik_guncelle(self, event) -> None:
        self.arac_tuvali.itemconfigure(self._arac_pencere, width=event.width)

    def _kaydirma_bagla(self, widget) -> None:
        widget.bind("<MouseWheel>", self._fare_kaydi, add="+")
        widget.bind("<Button-4>", self._fare_kaydi_linux, add="+")
        widget.bind("<Button-5>", self._fare_kaydi_linux, add="+")

    def _fare_kaydi(self, event) -> None:
        self.arac_tuvali.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _fare_kaydi_linux(self, event) -> None:
        if event.num == 4:
            self.arac_tuvali.yview_scroll(-1, "units")
        elif event.num == 5:
            self.arac_tuvali.yview_scroll(1, "units")
