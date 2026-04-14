from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

DESTEKLENEN_DOSYALAR = [
    ("Görsel Dosyaları", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
    ("Tüm Dosyalar", "*.*"),
]


class FotografServisi:
    def __init__(self) -> None:
        self.kaynak_yol: Path | None = None
        self.orijinal_gorsel: Image.Image | None = None
        self.calisma_gorseli: Image.Image | None = None
        self.filtre_temeli_gorsel: Image.Image | None = None
        self.kirpma_oncesi_gorsel: Image.Image | None = None
        self.netlestirme_oncesi_gorsel: Image.Image | None = None
        self.geri_al_yigini: list[Image.Image] = []
        self.yinele_yigini: list[Image.Image] = []
        self.gecmis_etiketleri: list[str] = []
        self.yinele_etiketleri: list[str] = []
        self.son_islem_metni = "Henüz işlem yapılmadı."

    def ac(self, dosya_yolu: str) -> Image.Image:
        gorsel = Image.open(dosya_yolu).convert("RGB")
        self.kaynak_yol = Path(dosya_yolu)
        self.orijinal_gorsel = gorsel.copy()
        self.calisma_gorseli = gorsel.copy()
        self.filtre_temeli_gorsel = gorsel.copy()
        self.geri_al_yigini.clear()
        self.yinele_yigini.clear()
        self.gecmis_etiketleri.clear()
        self.yinele_etiketleri.clear()
        self.son_islem_metni = "Fotoğraf açıldı."
        return self.calisma_gorseli

    def sifirla(self) -> Image.Image:
        if self.orijinal_gorsel is None:
            raise ValueError("Sıfırlamak için önce bir fotoğraf açılmalıdır.")
        self._durumu_kaydet("Tüm ayarları sıfırla")
        self.calisma_gorseli = self.orijinal_gorsel.copy()
        self.filtre_temeli_gorsel = self.calisma_gorseli.copy()
        self.kirpma_oncesi_gorsel = None
        self.netlestirme_oncesi_gorsel = None
        self.son_islem_metni = "Tüm ayarlar sıfırlandı."
        return self.calisma_gorseli

    def kaydet(self, hedef_yol: str) -> None:
        if self.calisma_gorseli is None:
            raise ValueError("Kaydedilecek bir fotoğraf bulunmuyor.")
        self.calisma_gorseli.save(hedef_yol)

    def mevcut_gorsel(self) -> Image.Image:
        if self.calisma_gorseli is None:
            raise ValueError("Önce bir fotoğraf açılmalıdır.")
        return self.calisma_gorseli

    def bilgileri_getir(self) -> dict[str, str]:
        gorsel = self.mevcut_gorsel()
        return {
            "boyut": f"{gorsel.width} x {gorsel.height} piksel",
            "mod": gorsel.mode,
            "dosya": self.kaynak_yol.name if self.kaynak_yol else "Bilinmiyor",
        }

    def dondur(self, derece: float) -> Image.Image:
        gorsel = self.mevcut_gorsel()
        yon = "Sola döndür" if derece > 0 else "Sağa döndür"
        self._durumu_kaydet(yon)
        self.calisma_gorseli = gorsel.rotate(-derece, expand=True)
        self._filtre_tabanini_guncelle()
        self.son_islem_metni = f"{yon} uygulandı."
        return self.calisma_gorseli

    def yeniden_boyutlandir(self, genislik: int, yukseklik: int) -> Image.Image:
        if genislik <= 0 or yukseklik <= 0:
            raise ValueError("Genişlik ve yükseklik sıfırdan büyük olmalıdır.")
        gorsel = self.mevcut_gorsel()
        self._durumu_kaydet(f"Yeniden boyutlandır: {genislik} x {yukseklik}")
        self.calisma_gorseli = gorsel.resize((genislik, yukseklik), Image.Resampling.LANCZOS)
        self._filtre_tabanini_guncelle()
        self.son_islem_metni = f"Boyut {genislik} x {yukseklik} olarak güncellendi."
        return self.calisma_gorseli

    def kirp(self, x: int, y: int, genislik: int, yukseklik: int) -> Image.Image:
        gorsel = self.mevcut_gorsel()
        if min(x, y, genislik, yukseklik) < 0:
            raise ValueError("Kırpma değerleri negatif olamaz.")
        if genislik == 0 or yukseklik == 0:
            raise ValueError("Kırpma genişliği ve yüksekliği sıfırdan büyük olmalıdır.")
        sag = min(gorsel.width, x + genislik)
        alt = min(gorsel.height, y + yukseklik)
        if x >= gorsel.width or y >= gorsel.height or sag <= x or alt <= y:
            raise ValueError("Kırpma alanı görsel sınırları dışında.")
        self._durumu_kaydet(f"Kırp: x={x}, y={y}, g={genislik}, yk={yukseklik}")
        self.kirpma_oncesi_gorsel = gorsel.copy()
        self.calisma_gorseli = gorsel.crop((x, y, sag, alt))
        self._filtre_tabanini_guncelle()
        self.son_islem_metni = "Kırpma uygulandı."
        return self.calisma_gorseli

    def son_kirpmayi_geri_al(self) -> Image.Image:
        if self.kirpma_oncesi_gorsel is None:
            raise ValueError("Geri alınacak bir kırpma işlemi bulunmuyor.")
        self._durumu_kaydet("Kırpmayı geri al")
        self.calisma_gorseli = self.kirpma_oncesi_gorsel.copy()
        self.kirpma_oncesi_gorsel = None
        self._filtre_tabanini_guncelle()
        self.son_islem_metni = "Son kırpma geri alındı."
        return self.calisma_gorseli

    def orana_gore_ortadan_kirp(self, oran_x: int, oran_y: int) -> Image.Image:
        if oran_x <= 0 or oran_y <= 0:
            raise ValueError("Oran değerleri sıfırdan büyük olmalıdır.")
        gorsel = self.mevcut_gorsel()
        hedef_oran = oran_x / oran_y
        mevcut_oran = gorsel.width / gorsel.height
        if mevcut_oran > hedef_oran:
            yeni_genislik = max(1, round(gorsel.height * hedef_oran))
            yeni_yukseklik = gorsel.height
        else:
            yeni_genislik = gorsel.width
            yeni_yukseklik = max(1, round(gorsel.width / hedef_oran))
        bas_x = max(0, (gorsel.width - yeni_genislik) // 2)
        bas_y = max(0, (gorsel.height - yeni_yukseklik) // 2)
        return self.kirp(bas_x, bas_y, yeni_genislik, yeni_yukseklik)

    def kirpmadan_orana_sigdir(self, oran_x: int, oran_y: int) -> Image.Image:
        if oran_x <= 0 or oran_y <= 0:
            raise ValueError("Oran değerleri sıfırdan büyük olmalıdır.")
        gorsel = self.mevcut_gorsel()
        hedef_oran = oran_x / oran_y
        mevcut_oran = gorsel.width / gorsel.height
        if abs(mevcut_oran - hedef_oran) < 0.0001:
            self._durumu_kaydet(f"Orana sığdır: {oran_x}:{oran_y}")
            self.calisma_gorseli = gorsel.copy()
            self._filtre_tabanini_guncelle()
            self.son_islem_metni = f"Görsel zaten {oran_x}:{oran_y} oranında."
            return self.calisma_gorseli
        if mevcut_oran > hedef_oran:
            yeni_genislik = gorsel.width
            yeni_yukseklik = max(gorsel.height, round(gorsel.width / hedef_oran))
        else:
            yeni_yukseklik = gorsel.height
            yeni_genislik = max(gorsel.width, round(gorsel.height * hedef_oran))
        self._durumu_kaydet(f"Orana sığdır: {oran_x}:{oran_y}")
        dolgu = self._arka_plan_rengi_bul(gorsel)
        tuval = Image.new("RGB", (yeni_genislik, yeni_yukseklik), dolgu)
        konum = ((yeni_genislik - gorsel.width) // 2, (yeni_yukseklik - gorsel.height) // 2)
        tuval.paste(gorsel, konum)
        self.calisma_gorseli = tuval
        self._filtre_tabanini_guncelle()
        self.son_islem_metni = f"Görsel {oran_x}:{oran_y} oranına kırpmadan sığdırıldı."
        return self.calisma_gorseli

    def renk_ayarlari_uygula(
        self,
        parlaklik: float,
        kontrast: float,
        doygunluk: float,
        keskinlik: float,
        ton: float,
    ) -> Image.Image:
        if ton <= 0:
            raise ValueError("Ton ayarı sıfırdan büyük olmalıdır.")
        gorsel = self.mevcut_gorsel()
        self._durumu_kaydet(
            f"Renk ayarları: parlaklık {parlaklik:.2f}, kontrast {kontrast:.2f}, "
            f"doygunluk {doygunluk:.2f}, keskinlik {keskinlik:.2f}, ton {ton:.2f}"
        )
        gorsel = ImageEnhance.Brightness(gorsel).enhance(parlaklik)
        gorsel = ImageEnhance.Contrast(gorsel).enhance(kontrast)
        gorsel = ImageEnhance.Color(gorsel).enhance(doygunluk)
        gorsel = ImageEnhance.Sharpness(gorsel).enhance(keskinlik)
        self.calisma_gorseli = self._gamma_duzelt(gorsel, ton)
        self._filtre_tabanini_guncelle()
        self.son_islem_metni = "Renk ayarları uygulandı."
        return self.calisma_gorseli

    def yatay_cevir(self) -> Image.Image:
        gorsel = self.mevcut_gorsel()
        self._durumu_kaydet("Yatay çevir")
        self.calisma_gorseli = ImageOps.mirror(gorsel)
        self._filtre_tabanini_guncelle()
        self.son_islem_metni = "Fotoğraf yatay çevrildi."
        return self.calisma_gorseli

    def dikey_cevir(self) -> Image.Image:
        gorsel = self.mevcut_gorsel()
        self._durumu_kaydet("Dikey çevir")
        self.calisma_gorseli = ImageOps.flip(gorsel)
        self._filtre_tabanini_guncelle()
        self.son_islem_metni = "Fotoğraf dikey çevrildi."
        return self.calisma_gorseli

    def netlestir(self, miktar: float) -> Image.Image:
        if miktar < 0:
            raise ValueError("Netleştirme miktarı negatif olamaz.")
        gorsel = self.mevcut_gorsel()
        self._durumu_kaydet(f"Netleştir: {miktar:.2f}")
        self.netlestirme_oncesi_gorsel = gorsel.copy()
        self.calisma_gorseli = gorsel.filter(
            ImageFilter.UnsharpMask(radius=2, percent=max(50, int(miktar * 100)), threshold=3)
        )
        self._filtre_tabanini_guncelle()
        self.son_islem_metni = "Netleştirme uygulandı."
        return self.calisma_gorseli

    def netlestirmeyi_geri_al(self) -> Image.Image:
        if self.netlestirme_oncesi_gorsel is None:
            raise ValueError("Geri alınacak bir netleştirme işlemi bulunmuyor.")
        self._durumu_kaydet("Netleştirmeyi geri al")
        self.calisma_gorseli = self.netlestirme_oncesi_gorsel.copy()
        self.netlestirme_oncesi_gorsel = None
        self._filtre_tabanini_guncelle()
        self.son_islem_metni = "Son netleştirme geri alındı."
        return self.calisma_gorseli

    def metin_ekle(self, metin: str, x: int, y: int, boyut: int, renk: str) -> Image.Image:
        if not metin.strip():
            raise ValueError("Eklenecek metin boş olamaz.")
        if boyut <= 0:
            raise ValueError("Yazı boyutu sıfırdan büyük olmalıdır.")
        gorsel = self.mevcut_gorsel()
        self._durumu_kaydet(f"Metin ekle: {metin[:20]}")
        sonuc = gorsel.copy()
        self._metni_ciz(sonuc, metin, x, y, boyut, renk)
        self.calisma_gorseli = sonuc
        self._filtre_tabanini_guncelle()
        self.son_islem_metni = "Metin görsele uygulandı."
        return self.calisma_gorseli

    def cizim_uygula(self, arac: str, noktalar, renk: str, kalinlik: int) -> Image.Image:
        if not noktalar or len(noktalar) < 2:
            raise ValueError("Çizim için yeterli nokta yok.")
        if kalinlik <= 0:
            raise ValueError("Fırça boyutu sıfırdan büyük olmalıdır.")
        gorsel = self.mevcut_gorsel()
        self._durumu_kaydet(f"Çizim: {arac}")
        sonuc = gorsel.copy()
        self._cizimi_ciz(sonuc, arac, noktalar, renk, kalinlik)
        self.calisma_gorseli = sonuc
        self._filtre_tabanini_guncelle()
        self.son_islem_metni = f"{arac} uygulandı."
        return self.calisma_gorseli

    def ogeleri_uygula(self, ogeler) -> Image.Image:
        if not ogeler:
            raise ValueError("Görsele uygulanacak herhangi bir öğe bulunmuyor.")
        gorsel = self.mevcut_gorsel()
        self._durumu_kaydet(f"{len(ogeler)} öğeyi uygula")
        sonuc = gorsel.copy()
        for oge in ogeler:
            if not oge.get("gorunur", True):
                continue
            if oge.get("tur") == "metin":
                self._metni_ciz(
                    sonuc,
                    oge.get("metin", ""),
                    int(oge.get("x", 0)),
                    int(oge.get("y", 0)),
                    int(oge.get("boyut", 24)),
                    oge.get("renk", "#ffffff"),
                )
            elif oge.get("tur") == "cizim":
                self._cizimi_ciz(
                    sonuc,
                    oge.get("arac", "Serbest Çizim"),
                    oge.get("noktalar", []),
                    oge.get("renk", "#5aa2ff"),
                    int(oge.get("kalinlik", 4)),
                )
        self.calisma_gorseli = sonuc
        self._filtre_tabanini_guncelle()
        self.son_islem_metni = f"{len(ogeler)} öğe görsele uygulandı."
        return self.calisma_gorseli

    def filtre_uygula(self, filtre_adi: str) -> Image.Image:
        gorsel = self.filtre_temeli_gorsel or self.mevcut_gorsel()
        self._durumu_kaydet(f"Filtre: {filtre_adi}")
        self.calisma_gorseli = self._filtreyi_uygula_gorsele(gorsel, filtre_adi)
        self.son_islem_metni = f"{filtre_adi} filtresi uygulandı."
        return self.calisma_gorseli

    def filtreli_kopya_uret(self, filtre_adi: str) -> Image.Image:
        return self._filtreyi_uygula_gorsele(
            (self.filtre_temeli_gorsel or self.mevcut_gorsel()).copy(),
            filtre_adi,
        )

    def _filtreyi_uygula_gorsele(self, gorsel: Image.Image, filtre_adi: str) -> Image.Image:
        filtreler = {
            "Bulanıklaştır": ImageFilter.BLUR,
            "Blur": ImageFilter.BLUR,
            "Keskinleştir": ImageFilter.SHARPEN,
            "Sharpen": ImageFilter.SHARPEN,
            "Detay": ImageFilter.DETAIL,
            "Detay Artır": ImageFilter.DETAIL,
            "Detail Enhancement": ImageFilter.DETAIL,
            "Kenar Vurgula": ImageFilter.EDGE_ENHANCE,
            "Kenar Güçlendir": ImageFilter.EDGE_ENHANCE,
            "Edge Enhance": ImageFilter.EDGE_ENHANCE,
            "Yumuşat": ImageFilter.SMOOTH,
            "Kabartma": ImageFilter.EMBOSS,
            "Emboss": ImageFilter.EMBOSS,
            "Kontur": ImageFilter.CONTOUR,
            "Daha Net": ImageFilter.EDGE_ENHANCE_MORE,
        }
        if filtre_adi == "Orijinal":
            return gorsel.copy()
        if filtre_adi == "Siyah Beyaz":
            return gorsel.convert("L").convert("RGB")
        if filtre_adi == "Sepya":
            return ImageOps.colorize(ImageOps.grayscale(gorsel), "#2b1a10", "#f0d7a1").convert("RGB")
        if filtre_adi == "Negatif":
            return ImageOps.invert(gorsel.convert("RGB"))
        if filtre_adi == "Posterize":
            return ImageOps.posterize(gorsel.convert("RGB"), 4)
        secilen = filtreler.get(filtre_adi)
        if secilen is None:
            raise ValueError("Bilinmeyen filtre seçimi.")
        return gorsel.filter(secilen)

    def _filtre_tabanini_guncelle(self) -> None:
        if self.calisma_gorseli is not None:
            self.filtre_temeli_gorsel = self.calisma_gorseli.copy()

    def geri_al(self) -> Image.Image:
        if not self.geri_al_yigini:
            raise ValueError("Geri alınacak bir işlem bulunmuyor.")
        mevcut = self.mevcut_gorsel().copy()
        self.yinele_yigini.append(mevcut)
        son = self.gecmis_etiketleri.pop() if self.gecmis_etiketleri else "İsimsiz işlem"
        self.yinele_etiketleri.append(son)
        self.calisma_gorseli = self.geri_al_yigini.pop()
        self._filtre_tabanini_guncelle()
        self.son_islem_metni = f"Geri alındı: {son}"
        return self.calisma_gorseli

    def yinele(self) -> Image.Image:
        if not self.yinele_yigini:
            raise ValueError("Yinelenecek bir işlem bulunmuyor.")
        mevcut = self.mevcut_gorsel().copy()
        self.geri_al_yigini.append(mevcut)
        son = self.yinele_etiketleri.pop() if self.yinele_etiketleri else "İsimsiz işlem"
        self.gecmis_etiketleri.append(son)
        self.calisma_gorseli = self.yinele_yigini.pop()
        self._filtre_tabanini_guncelle()
        self.son_islem_metni = f"Yinelendi: {son}"
        return self.calisma_gorseli

    def gecmis_bilgisi(self) -> str:
        return f"Geri Al: {len(self.geri_al_yigini)} | Yinele: {len(self.yinele_yigini)}"

    def islem_gecmisi(self) -> list[str]:
        return self.gecmis_etiketleri[-8:]

    def _durumu_kaydet(self, islem_adi: str) -> None:
        if self.calisma_gorseli is not None:
            self.geri_al_yigini.append(self.calisma_gorseli.copy())
            self.gecmis_etiketleri.append(islem_adi)
            self.yinele_yigini.clear()
            self.yinele_etiketleri.clear()

    def _gamma_duzelt(self, gorsel: Image.Image, gamma: float) -> Image.Image:
        tablo = [min(255, max(0, int(((i / 255) ** (1.0 / gamma)) * 255))) for i in range(256)]
        return gorsel.point(tablo * 3)

    def _metni_ciz(self, gorsel: Image.Image, metin: str, x: int, y: int, boyut: int, renk: str) -> None:
        cizim = ImageDraw.Draw(gorsel)
        try:
            yazi_tipi = ImageFont.truetype("DejaVuSans.ttf", boyut)
        except OSError:
            yazi_tipi = ImageFont.load_default()
        cizim.text((x, y), metin, fill=renk, font=yazi_tipi)

    def _cizimi_ciz(self, gorsel: Image.Image, arac: str, noktalar, renk: str, kalinlik: int) -> None:
        if not noktalar or len(noktalar) < 2:
            return
        cizim = ImageDraw.Draw(gorsel)
        if arac in ("Serbest Çizim", "Silgi"):
            x = min(gorsel.width - 1, max(0, int(noktalar[-1][0])))
            y = min(gorsel.height - 1, max(0, int(noktalar[-1][1])))
            cizgi_rengi = gorsel.getpixel((x, y)) if arac == "Silgi" else renk
            cizim.line(noktalar, fill=cizgi_rengi, width=kalinlik, joint="curve")
            return
        (x1, y1), (x2, y2) = noktalar[0], noktalar[-1]
        if arac == "Düz Çizgi":
            cizim.line((x1, y1, x2, y2), fill=renk, width=kalinlik)
        elif arac == "Dikdörtgen":
            cizim.rectangle((x1, y1, x2, y2), outline=renk, width=kalinlik)
        elif arac == "Daire":
            cizim.ellipse((x1, y1, x2, y2), outline=renk, width=kalinlik)
        elif arac == "Ok":
            cizim.line((x1, y1, x2, y2), fill=renk, width=kalinlik)
            self._ok_ucu_ciz(cizim, x1, y1, x2, y2, renk, kalinlik)

    def _arka_plan_rengi_bul(self, gorsel: Image.Image) -> tuple[int, int, int]:
        kucuk = gorsel.copy()
        kucuk.thumbnail((1, 1))
        renk = kucuk.getpixel((0, 0))
        if isinstance(renk, int):
            return (renk, renk, renk)
        return tuple(renk[:3])

    def _ok_ucu_ciz(self, cizim: ImageDraw.ImageDraw, x1: int, y1: int, x2: int, y2: int, renk: str, kalinlik: int) -> None:
        import math

        aci = math.atan2(y2 - y1, x2 - x1)
        uzunluk = max(10, kalinlik * 3)
        sol = (x2 - uzunluk * math.cos(aci - math.pi / 6), y2 - uzunluk * math.sin(aci - math.pi / 6))
        sag = (x2 - uzunluk * math.cos(aci + math.pi / 6), y2 - uzunluk * math.sin(aci + math.pi / 6))
        cizim.line((x2, y2, sol[0], sol[1]), fill=renk, width=kalinlik)
        cizim.line((x2, y2, sag[0], sag[1]), fill=renk, width=kalinlik)
