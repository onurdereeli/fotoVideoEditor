from __future__ import annotations

from pathlib import Path

from PIL import Image

try:
    from moviepy.editor import VideoFileClip
except ModuleNotFoundError:
    from moviepy import VideoFileClip


DESTEKLENEN_VIDEO_DOSYALARI = [
    ("Video Dosyaları", "*.mp4 *.mov *.avi *.mkv *.wmv *.webm"),
    ("Tüm Dosyalar", "*.*"),
]


class VideoServisi:
    def __init__(self) -> None:
        self.video_yolu: Path | None = None
        self.klip: VideoFileClip | None = None

    def ac(self, dosya_yolu: str) -> dict[str, object]:
        self.kapat()
        self.video_yolu = Path(dosya_yolu)
        self.klip = VideoFileClip(dosya_yolu)
        return self.bilgileri_getir()

    def kapat(self) -> None:
        if self.klip is not None:
            self.klip.close()
            self.klip = None

    def video_var_mi(self) -> bool:
        return self.klip is not None

    def bilgileri_getir(self) -> dict[str, object]:
        klip = self._klip_getir()
        return {
            "dosya": self.video_yolu.name if self.video_yolu else "Bilinmiyor",
            "sure": round(float(klip.duration), 2),
            "cozunurluk": f"{klip.w} x {klip.h}",
            "fps": round(float(klip.fps), 2) if klip.fps else 0,
            "ses": "Var" if klip.audio is not None else "Yok",
        }

    def onizleme_karesi_al(self, saniye: float = 0.0) -> Image.Image:
        klip = self._klip_getir()
        guvenli_zaman = min(max(saniye, 0.0), max(float(klip.duration) - 0.05, 0.0))
        kare = klip.get_frame(guvenli_zaman)
        return Image.fromarray(kare)

    def disa_aktar(
        self,
        hedef_yol: str,
        baslangic: float,
        bitis: float | None,
        genislik: int | None,
        yukseklik: int | None,
        sesi_kapat: bool,
        ses_seviyesi: int = 100,
    ) -> None:
        klip = self._klip_getir()
        toplam_sure = float(klip.duration)

        if baslangic < 0:
            raise ValueError("Trim başlangıcı sıfırdan küçük olamaz.")
        if bitis is not None and bitis <= baslangic:
            raise ValueError("Trim bitişi başlangıçtan büyük olmalıdır.")
        if baslangic >= toplam_sure:
            raise ValueError("Trim başlangıcı video süresini aşıyor.")

        efektif_bitis = toplam_sure if bitis is None else min(bitis, toplam_sure)
        if hasattr(klip, "subclip"):
            calisma_klibi = klip.subclip(baslangic, efektif_bitis)
        else:
            calisma_klibi = klip.subclipped(baslangic, efektif_bitis)

        if genislik is not None and yukseklik is not None:
            if genislik <= 0 or yukseklik <= 0:
                calisma_klibi.close()
                raise ValueError("Yeni genişlik ve yükseklik sıfırdan büyük olmalıdır.")
            if hasattr(calisma_klibi, "resize"):
                calisma_klibi = calisma_klibi.resize(newsize=(genislik, yukseklik))
            else:
                calisma_klibi = calisma_klibi.resized(new_size=(genislik, yukseklik))

        ses_seviyesi = max(0, min(int(ses_seviyesi), 200))
        if sesi_kapat or ses_seviyesi == 0:
            calisma_klibi = calisma_klibi.without_audio()
        elif ses_seviyesi != 100 and calisma_klibi.audio is not None:
            katsayi = ses_seviyesi / 100.0
            if hasattr(calisma_klibi, "volumex"):
                calisma_klibi = calisma_klibi.volumex(katsayi)
            elif hasattr(calisma_klibi, "with_volume_scaled"):
                calisma_klibi = calisma_klibi.with_volume_scaled(katsayi)
            elif hasattr(calisma_klibi.audio, "volumex") and hasattr(calisma_klibi, "set_audio"):
                calisma_klibi = calisma_klibi.set_audio(calisma_klibi.audio.volumex(katsayi))
            elif hasattr(calisma_klibi.audio, "volumex") and hasattr(calisma_klibi, "with_audio"):
                calisma_klibi = calisma_klibi.with_audio(calisma_klibi.audio.volumex(katsayi))

        try:
            ses_var = calisma_klibi.audio is not None and not sesi_kapat and ses_seviyesi > 0
            calisma_klibi.write_videofile(
                hedef_yol,
                codec="libx264",
                audio_codec="aac",
                audio=ses_var,
                logger=None,
            )
        finally:
            calisma_klibi.close()

    def _klip_getir(self) -> VideoFileClip:
        if self.klip is None:
            raise ValueError("Önce bir video açılmalıdır.")
        return self.klip
