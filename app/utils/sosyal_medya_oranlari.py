SOSYAL_MEDYA_ORANLARI = {
    "Instagram Kare (1:1)": {
        "oran": (1, 1),
        "hedef": "Instagram",
        "onerilen_boyut": "1080 x 1080",
        "hazir_ciktilar": ["1080x1080"],
    },
    "Instagram Dikey (4:5)": {
        "oran": (4, 5),
        "hedef": "Instagram",
        "onerilen_boyut": "1080 x 1350",
        "hazir_ciktilar": ["1080x1350", "1200x1500"],
    },
    "Instagram Hikâye / Reels (9:16)": {
        "oran": (9, 16),
        "hedef": "Instagram",
        "onerilen_boyut": "1080 x 1920",
        "hazir_ciktilar": ["1080x1920"],
    },
    "Facebook Kare (1:1)": {
        "oran": (1, 1),
        "hedef": "Facebook",
        "onerilen_boyut": "1080 x 1080",
        "hazir_ciktilar": ["1080x1080"],
    },
    "Facebook Dikey (4:5)": {
        "oran": (4, 5),
        "hedef": "Facebook",
        "onerilen_boyut": "1200 x 1500",
        "hazir_ciktilar": ["1080x1350", "1200x1500"],
    },
    "X Kare (1:1)": {
        "oran": (1, 1),
        "hedef": "X",
        "onerilen_boyut": "1080 x 1080",
        "hazir_ciktilar": ["1080x1080"],
    },
    "X Dikey (3:4)": {
        "oran": (3, 4),
        "hedef": "X",
        "onerilen_boyut": "1200 x 1600",
        "hazir_ciktilar": ["1200x1500"],
    },
    "X Geniş (16:9)": {
        "oran": (16, 9),
        "hedef": "X",
        "onerilen_boyut": "1920 x 1080",
        "hazir_ciktilar": ["1920x1080"],
    },
    "X Geniş (1.91:1)": {
        "oran": (191, 100),
        "hedef": "X",
        "onerilen_boyut": "1200 x 628",
        "hazir_ciktilar": ["1920x1080"],
    },
}

GENEL_HAZIR_CIKTILAR = [
    "1080x1080",
    "1080x1350",
    "1080x1920",
    "1200x1500",
    "1920x1080",
]


def sosyal_medya_oran_adlari() -> list[str]:
    return list(SOSYAL_MEDYA_ORANLARI.keys())


def sosyal_medya_orani_getir(ad: str) -> tuple[int, int]:
    veri = sosyal_medya_bilgisi_getir(ad)
    return veri["oran"]


def sosyal_medya_bilgisi_getir(ad: str) -> dict:
    veri = SOSYAL_MEDYA_ORANLARI.get(ad)
    if veri is None:
        raise ValueError("Bilinmeyen sosyal medya oranı seçildi.")
    return veri


def sosyal_medya_hazir_ciktilari_getir(ad: str) -> list[str]:
    veri = sosyal_medya_bilgisi_getir(ad)
    return veri.get("hazir_ciktilar", GENEL_HAZIR_CIKTILAR)
