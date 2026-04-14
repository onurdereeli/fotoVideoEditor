import tkinter as tk
from tkinter import ttk

from app.ui import tema


def stil_uygula(root: tk.Tk) -> ttk.Style:
    style = ttk.Style(root)
    style.theme_use("clam")

    root.configure(bg=tema.ARKA_PLAN)
    root.option_add("*Background", tema.IKINCIL_ARKA_PLAN)
    root.option_add("*Foreground", tema.METIN_RENGI)
    root.option_add("*TCombobox*Listbox.background", tema.ONIZLEME_ZEMIN)
    root.option_add("*TCombobox*Listbox.foreground", tema.METIN_RENGI)
    root.option_add("*TCombobox*Listbox.selectBackground", tema.VURGU_MAVI)
    root.option_add("*TCombobox*Listbox.selectForeground", tema.METIN_RENGI)

    style.configure("Genel.TFrame", background=tema.ARKA_PLAN)
    style.configure("Panel.TFrame", background=tema.IKINCIL_ARKA_PLAN, borderwidth=1, relief="solid")
    style.configure("Durum.TFrame", background=tema.IKINCIL_ARKA_PLAN)
    style.configure(
        "Genel.TLabel",
        background=tema.IKINCIL_ARKA_PLAN,
        foreground=tema.METIN_RENGI,
        font=tema.YAZI_TIPI,
    )
    style.configure(
        "Baslik.TLabel",
        background=tema.IKINCIL_ARKA_PLAN,
        foreground=tema.METIN_RENGI,
        font=tema.YAZI_TIPI_BASLIK,
    )
    style.configure(
        "Aciklama.TLabel",
        background=tema.IKINCIL_ARKA_PLAN,
        foreground=tema.SOLUK_METIN,
        font=tema.YAZI_TIPI,
    )
    style.configure(
        "Durum.TLabel",
        background=tema.IKINCIL_ARKA_PLAN,
        foreground=tema.SOLUK_METIN,
        font=tema.YAZI_TIPI,
    )
    style.configure(
        "Arac.TButton",
        background=tema.VURGU_MAVI,
        foreground=tema.METIN_RENGI,
        borderwidth=0,
        focusthickness=0,
        focuscolor=tema.VURGU_MAVI,
        padding=(12, 10),
        font=tema.YAZI_TIPI,
        anchor="center",
    )
    style.map(
        "Arac.TButton",
        background=[("active", tema.VURGU_MAVI_AKTIF), ("pressed", tema.VURGU_MAVI_AKTIF)],
        foreground=[("disabled", tema.SOLUK_METIN)],
    )
    style.configure("Karanlik.TNotebook", background=tema.ARKA_PLAN, borderwidth=0, tabmargins=(0, 0, 0, 0))
    style.configure(
        "Karanlik.TNotebook.Tab",
        background=tema.IKINCIL_ARKA_PLAN,
        foreground=tema.METIN_RENGI,
        padding=(18, 10),
        font=tema.YAZI_TIPI_BASLIK,
        borderwidth=0,
    )
    style.map(
        "Karanlik.TNotebook.Tab",
        background=[("selected", tema.VURGU_MAVI), ("active", tema.VURGU_MAVI_AKTIF)],
        foreground=[("selected", tema.METIN_RENGI)],
    )
    style.configure(
        "Panel.TLabelframe",
        background=tema.IKINCIL_ARKA_PLAN,
        foreground=tema.METIN_RENGI,
        borderwidth=1,
        relief="solid",
        padding=12,
    )
    style.configure(
        "Panel.TLabelframe.Label",
        background=tema.IKINCIL_ARKA_PLAN,
        foreground=tema.METIN_RENGI,
        font=tema.YAZI_TIPI_BASLIK,
    )
    style.configure(
        "Karanlik.TEntry",
        fieldbackground=tema.ONIZLEME_ZEMIN,
        foreground=tema.METIN_RENGI,
        bordercolor=tema.CERCEVE,
        lightcolor=tema.CERCEVE,
        darkcolor=tema.CERCEVE,
        insertcolor=tema.METIN_RENGI,
        padding=6,
    )
    style.configure(
        "Karanlik.TCombobox",
        fieldbackground=tema.ONIZLEME_ZEMIN,
        background=tema.ONIZLEME_ZEMIN,
        foreground=tema.METIN_RENGI,
        arrowcolor=tema.METIN_RENGI,
        bordercolor=tema.CERCEVE,
        lightcolor=tema.CERCEVE,
        darkcolor=tema.CERCEVE,
        padding=4,
    )
    style.map(
        "Karanlik.TCombobox",
        fieldbackground=[("readonly", tema.ONIZLEME_ZEMIN)],
        selectbackground=[("readonly", tema.VURGU_MAVI)],
        selectforeground=[("readonly", tema.METIN_RENGI)],
    )
    style.configure(
        "Karanlik.Horizontal.TScale",
        background=tema.IKINCIL_ARKA_PLAN,
        troughcolor=tema.ONIZLEME_ZEMIN,
        bordercolor=tema.CERCEVE,
        lightcolor=tema.VURGU_MAVI,
        darkcolor=tema.VURGU_MAVI,
    )
    style.configure(
        "Switch.TCheckbutton",
        background=tema.IKINCIL_ARKA_PLAN,
        foreground=tema.METIN_RENGI,
        font=tema.YAZI_TIPI,
        indicatorcolor=tema.ONIZLEME_ZEMIN,
        indicatormargin=4,
    )
    style.map(
        "Switch.TCheckbutton",
        background=[("active", tema.IKINCIL_ARKA_PLAN)],
        foreground=[("active", tema.METIN_RENGI)],
        indicatorcolor=[("selected", tema.VURGU_MAVI)],
    )
    return style


def buton(parent: ttk.Frame, metin: str, komut=None) -> ttk.Button:
    return ttk.Button(parent, text=metin, command=komut, style="Arac.TButton")
