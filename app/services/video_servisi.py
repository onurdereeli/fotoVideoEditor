from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

try:
    from moviepy.editor import CompositeVideoClip, TextClip, VideoFileClip
except ModuleNotFoundError:
    from moviepy import CompositeVideoClip, TextClip, VideoFileClip

try:
    from moviepy.audio.fx.AudioFadeIn import AudioFadeIn
except Exception:
    AudioFadeIn = None

try:
    from moviepy.audio.fx.AudioFadeOut import AudioFadeOut
except Exception:
    AudioFadeOut = None

try:
    from moviepy.audio.fx.all import audio_fadein as legacy_audio_fadein
    from moviepy.audio.fx.all import audio_fadeout as legacy_audio_fadeout
except Exception:
    legacy_audio_fadein = None
    legacy_audio_fadeout = None

try:
    from moviepy.video.fx.BlackAndWhite import BlackAndWhite
except Exception:
    BlackAndWhite = None

try:
    from moviepy.video.fx.GammaCorrection import GammaCorrection
except Exception:
    GammaCorrection = None

try:
    from moviepy.video.fx.Rotate import Rotate
except Exception:
    Rotate = None

try:
    from moviepy.video.fx.MirrorX import MirrorX
except Exception:
    MirrorX = None

try:
    from moviepy.video.fx.MirrorY import MirrorY
except Exception:
    MirrorY = None

try:
    from moviepy.video.fx.MultiplySpeed import MultiplySpeed
except Exception:
    MultiplySpeed = None


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

    def onizleme_karesi_al(
        self,
        saniye: float = 0.0,
        *,
        rotate_degrees: int = 0,
        flip_horizontal: bool = False,
        flip_vertical: bool = False,
        aspect_ratio: str = "Original",
        brightness: int = 0,
        contrast: int = 0,
        saturation: int = 100,
        gamma: float = 1.0,
        black_white: bool = False,
        style_effects: list[str] | None = None,
        overlay_text: str = "",
        overlay_font_size: int = 36,
        overlay_color: str = "white",
        overlay_position: str = "bottom",
        overlay_start: float | None = None,
        overlay_end: float | None = None,
    ) -> Image.Image:
        klip = self._klip_getir()
        guvenli_zaman = min(max(saniye, 0.0), max(float(klip.duration) - 0.05, 0.0))
        kare = klip.get_frame(guvenli_zaman)
        kare = self._onizleme_donusumlerini_uygula(
            np.asarray(kare),
            rotate_degrees=rotate_degrees,
            flip_horizontal=flip_horizontal,
            flip_vertical=flip_vertical,
            aspect_ratio=aspect_ratio,
        )

        if (
            brightness != 0
            or contrast != 0
            or saturation != 100
            or gamma != 1.0
            or black_white
        ):
            kare = self._frame_efekti_uygula(
                np.asarray(kare),
                brightness=brightness,
                contrast=contrast,
                saturation=saturation,
                gamma=gamma,
                black_white=black_white,
            )

        if style_effects:
            kare = self._stil_frame_uygula(np.asarray(kare), style_effects)

        gorsel = Image.fromarray(kare)
        return self._metin_onizleme_uygula(
            gorsel,
            saniye=guvenli_zaman,
            overlay_text=overlay_text,
            overlay_font_size=overlay_font_size,
            overlay_color=overlay_color,
            overlay_position=overlay_position,
            overlay_start=overlay_start,
            overlay_end=overlay_end,
        )

    def disa_aktar(
        self,
        hedef_yol: str,
        baslangic: float,
        bitis: float | None,
        genislik: int | None,
        yukseklik: int | None,
        rotate_degrees: int = 0,
        flip_horizontal: bool = False,
        flip_vertical: bool = False,
        aspect_ratio: str = "Original",
        speed_factor: float = 1.0,
        sesi_kapat: bool = False,
        ses_seviyesi: int = 100,
        fade_in: float = 0.0,
        fade_out: float = 0.0,
        brightness: int = 0,
        contrast: int = 0,
        saturation: int = 100,
        gamma: float = 1.0,
        black_white: bool = False,
        style_effects: list[str] | None = None,
        overlay_text: str = "",
        overlay_font_size: int = 36,
        overlay_color: str = "white",
        overlay_position: str = "bottom",
        overlay_start: float | None = None,
        overlay_end: float | None = None,
    ) -> None:
        klip = self._klip_getir()
        toplam_sure = float(klip.duration)

        if baslangic < 0:
            raise ValueError("Trim başlangıcı sıfırdan küçük olamaz.")
        if bitis is not None and bitis <= baslangic:
            raise ValueError("Trim bitişi başlangıçtan büyük olmalıdır.")
        if baslangic >= toplam_sure:
            raise ValueError("Trim başlangıcı video süresini aşıyor.")
        if fade_in < 0 or fade_out < 0:
            raise ValueError("Fade süreleri negatif olamaz.")
        if gamma <= 0:
            raise ValueError("Gamma sıfırdan büyük olmalıdır.")

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

        calisma_klibi = self._hiz_uygula(calisma_klibi, speed_factor)

        calisma_klibi = self._video_donusumlerini_uygula(
            calisma_klibi,
            rotate_degrees=rotate_degrees,
            flip_horizontal=flip_horizontal,
            flip_vertical=flip_vertical,
            aspect_ratio=aspect_ratio,
        )

        calisma_klibi = self._gorsel_efektleri_uygula(
            calisma_klibi,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            gamma=gamma,
            black_white=black_white,
        )
        calisma_klibi = self._stil_efektleri_uygula(calisma_klibi, style_effects or [])
        calisma_klibi = self._metin_katmani_uygula(
            calisma_klibi,
            overlay_text=overlay_text,
            overlay_font_size=overlay_font_size,
            overlay_color=overlay_color,
            overlay_position=overlay_position,
            overlay_start=overlay_start,
            overlay_end=overlay_end,
        )

        ses_seviyesi = max(0, min(int(ses_seviyesi), 200))
        klip_suresi = max(float(getattr(calisma_klibi, "duration", 0.0) or 0.0), 0.0)
        fade_in = min(max(float(fade_in), 0.0), klip_suresi)
        fade_out = min(max(float(fade_out), 0.0), klip_suresi)

        if sesi_kapat or ses_seviyesi == 0:
            calisma_klibi = calisma_klibi.without_audio()
        else:
            if ses_seviyesi != 100 and calisma_klibi.audio is not None:
                katsayi = ses_seviyesi / 100.0
                if hasattr(calisma_klibi, "volumex"):
                    calisma_klibi = calisma_klibi.volumex(katsayi)
                elif hasattr(calisma_klibi, "with_volume_scaled"):
                    calisma_klibi = calisma_klibi.with_volume_scaled(katsayi)
                elif hasattr(calisma_klibi.audio, "volumex") and hasattr(calisma_klibi, "set_audio"):
                    calisma_klibi = calisma_klibi.set_audio(calisma_klibi.audio.volumex(katsayi))
                elif hasattr(calisma_klibi.audio, "volumex") and hasattr(calisma_klibi, "with_audio"):
                    calisma_klibi = calisma_klibi.with_audio(calisma_klibi.audio.volumex(katsayi))

            if calisma_klibi.audio is not None:
                if fade_in > 0:
                    calisma_klibi = self._fade_uygula(calisma_klibi, fade_in, fade_out=False)
                if fade_out > 0:
                    calisma_klibi = self._fade_uygula(calisma_klibi, fade_out, fade_out=True)

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

    def _onizleme_donusumlerini_uygula(
        self,
        frame: np.ndarray,
        *,
        rotate_degrees: int,
        flip_horizontal: bool,
        flip_vertical: bool,
        aspect_ratio: str,
    ) -> np.ndarray:
        image = Image.fromarray(np.asarray(frame).astype(np.uint8))

        rotate_degrees = int(rotate_degrees) % 360
        if rotate_degrees:
            image = image.rotate(-rotate_degrees, expand=True)

        if flip_horizontal:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
        if flip_vertical:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)

        image = self._onizleme_aspect_ratio_kirp(image, aspect_ratio)
        return np.asarray(image)

    def _onizleme_aspect_ratio_kirp(self, image: Image.Image, aspect_ratio: str) -> Image.Image:
        oran_haritasi = {
            "16:9": 16 / 9,
            "9:16": 9 / 16,
            "1:1": 1.0,
            "4:5": 4 / 5,
        }
        hedef_oran = oran_haritasi.get(aspect_ratio)
        if hedef_oran is None:
            return image

        genislik, yukseklik = image.size
        if genislik <= 0 or yukseklik <= 0:
            return image

        mevcut_oran = genislik / yukseklik
        if abs(mevcut_oran - hedef_oran) < 0.001:
            return image

        if mevcut_oran > hedef_oran:
            yeni_genislik = max(int(yukseklik * hedef_oran), 1)
            x1 = max((genislik - yeni_genislik) // 2, 0)
            return image.crop((x1, 0, min(x1 + yeni_genislik, genislik), yukseklik))

        yeni_yukseklik = max(int(genislik / hedef_oran), 1)
        y1 = max((yukseklik - yeni_yukseklik) // 2, 0)
        return image.crop((0, y1, genislik, min(y1 + yeni_yukseklik, yukseklik)))

    def _hiz_uygula(self, klip: VideoFileClip, speed_factor: float) -> VideoFileClip:
        speed_factor = max(0.5, min(float(speed_factor), 2.0))
        if abs(speed_factor - 1.0) < 0.001:
            return klip
        if hasattr(klip, "with_speed_scaled"):
            return klip.with_speed_scaled(speed_factor)
        if MultiplySpeed is not None and hasattr(klip, "with_effects"):
            return klip.with_effects([MultiplySpeed(speed_factor)])
        return klip

    def _video_donusumlerini_uygula(
        self,
        klip: VideoFileClip,
        *,
        rotate_degrees: int,
        flip_horizontal: bool,
        flip_vertical: bool,
        aspect_ratio: str,
    ) -> VideoFileClip:
        rotate_degrees = int(rotate_degrees) % 360
        if rotate_degrees:
            if hasattr(klip, "rotated"):
                klip = klip.rotated(rotate_degrees)
            elif Rotate is not None and hasattr(klip, "with_effects"):
                klip = klip.with_effects([Rotate(rotate_degrees)])

        if flip_horizontal:
            if MirrorX is not None and hasattr(klip, "with_effects"):
                klip = klip.with_effects([MirrorX()])
            elif hasattr(klip, "image_transform"):
                klip = klip.image_transform(np.fliplr)

        if flip_vertical:
            if MirrorY is not None and hasattr(klip, "with_effects"):
                klip = klip.with_effects([MirrorY()])
            elif hasattr(klip, "image_transform"):
                klip = klip.image_transform(np.flipud)

        if aspect_ratio != "Original":
            klip = self._aspect_ratio_kirp(klip, aspect_ratio)

        return klip

    def _aspect_ratio_kirp(self, klip: VideoFileClip, aspect_ratio: str) -> VideoFileClip:
        oran_haritasi = {
            "16:9": 16 / 9,
            "9:16": 9 / 16,
            "1:1": 1.0,
            "4:5": 4 / 5,
        }
        hedef_oran = oran_haritasi.get(aspect_ratio)
        if hedef_oran is None:
            return klip

        genislik = float(getattr(klip, "w", 0) or 0)
        yukseklik = float(getattr(klip, "h", 0) or 0)
        if genislik <= 0 or yukseklik <= 0:
            return klip

        mevcut_oran = genislik / yukseklik
        if abs(mevcut_oran - hedef_oran) < 0.001:
            return klip

        if mevcut_oran > hedef_oran:
            yeni_genislik = yukseklik * hedef_oran
            x1 = max((genislik - yeni_genislik) / 2, 0)
            x2 = x1 + yeni_genislik
            if hasattr(klip, "cropped"):
                return klip.cropped(x1=x1, y1=0, x2=x2, y2=yukseklik)
            return klip

        yeni_yukseklik = genislik / hedef_oran
        y1 = max((yukseklik - yeni_yukseklik) / 2, 0)
        y2 = y1 + yeni_yukseklik
        if hasattr(klip, "cropped"):
            return klip.cropped(x1=0, y1=y1, x2=genislik, y2=y2)
        return klip

    def _gorsel_efektleri_uygula(
        self,
        klip: VideoFileClip,
        *,
        brightness: int,
        contrast: int,
        saturation: int,
        gamma: float,
        black_white: bool,
    ) -> VideoFileClip:
        brightness = max(-100, min(int(brightness), 100))
        contrast = max(-100, min(int(contrast), 100))
        saturation = max(0, min(int(saturation), 200))
        gamma = max(0.1, min(float(gamma), 3.0))

        if black_white and BlackAndWhite is not None and hasattr(klip, "with_effects"):
            try:
                klip = klip.with_effects([BlackAndWhite()])
                black_white = False
            except Exception:
                pass

        if gamma != 1.0 and GammaCorrection is not None and hasattr(klip, "with_effects"):
            try:
                klip = klip.with_effects([GammaCorrection(gamma)])
                gamma = 1.0
            except Exception:
                pass

        if (
            brightness == 0
            and contrast == 0
            and saturation == 100
            and gamma == 1.0
            and not black_white
        ):
            return klip

        if hasattr(klip, "image_transform"):
            return klip.image_transform(
                lambda frame: self._frame_efekti_uygula(
                    frame,
                    brightness=brightness,
                    contrast=contrast,
                    saturation=saturation,
                    gamma=gamma,
                    black_white=black_white,
                )
            )

        return klip

    def _frame_efekti_uygula(
        self,
        frame: np.ndarray,
        *,
        brightness: int,
        contrast: int,
        saturation: int,
        gamma: float,
        black_white: bool,
    ) -> np.ndarray:
        alfa = frame.astype(np.float32)

        if brightness != 0:
            alfa += (brightness / 100.0) * 255.0

        if contrast != 0:
            contrast_factor = 1.0 + (contrast / 100.0)
            alfa = (alfa - 127.5) * contrast_factor + 127.5

        if saturation != 100 or black_white:
            gri = np.dot(alfa[..., :3], [0.299, 0.587, 0.114])[..., None]
            sat_factor = 0.0 if black_white else (saturation / 100.0)
            alfa[..., :3] = gri + (alfa[..., :3] - gri) * sat_factor

        if gamma != 1.0:
            normalized = np.clip(alfa[..., :3] / 255.0, 0.0, 1.0)
            alfa[..., :3] = np.power(normalized, 1.0 / gamma) * 255.0

        return np.clip(alfa, 0, 255).astype(np.uint8)


    def _stil_efektleri_uygula(self, klip: VideoFileClip, style_effects: list[str]) -> VideoFileClip:
        if not style_effects:
            return klip
        if hasattr(klip, "image_transform"):
            return klip.image_transform(lambda frame: self._stil_frame_uygula(frame, style_effects))
        return klip

    def _stil_frame_uygula(self, frame: np.ndarray, style_effects: list[str]) -> np.ndarray:
        if not style_effects:
            return frame

        result = np.asarray(frame).astype(np.uint8)
        ordered_effects = []
        for effect in style_effects:
            if effect not in ordered_effects:
                ordered_effects.append(effect)

        for effect in ordered_effects:
            image = Image.fromarray(result)

            if effect == "black_white":
                image = ImageOps.grayscale(image).convert("RGB")
                result = np.asarray(image)
                continue

            if effect == "sepia":
                arr = np.asarray(image).astype(np.float32)
                transformed = np.empty_like(arr)
                transformed[..., 0] = arr[..., 0] * 0.393 + arr[..., 1] * 0.769 + arr[..., 2] * 0.189
                transformed[..., 1] = arr[..., 0] * 0.349 + arr[..., 1] * 0.686 + arr[..., 2] * 0.168
                transformed[..., 2] = arr[..., 0] * 0.272 + arr[..., 1] * 0.534 + arr[..., 2] * 0.131
                result = np.clip(transformed, 0, 255).astype(np.uint8)
                continue

            if effect == "vignette":
                height, width = result.shape[:2]
                y, x = np.ogrid[:height, :width]
                center_x = width / 2.0
                center_y = height / 2.0
                distance = np.sqrt(((x - center_x) / max(center_x, 1.0)) ** 2 + ((y - center_y) / max(center_y, 1.0)) ** 2)
                mask = np.clip(1.0 - (distance * 0.7), 0.35, 1.0)[..., None]
                result = np.clip(result.astype(np.float32) * mask, 0, 255).astype(np.uint8)
                continue

            if effect == "blur":
                result = np.asarray(image.filter(ImageFilter.GaussianBlur(radius=2)))
                continue

            if effect == "sharpen":
                result = np.asarray(image.filter(ImageFilter.UnsharpMask(radius=1, percent=180, threshold=3)))
                continue

            if effect == "film_grain":
                noise = np.random.normal(0, 14, result.shape).astype(np.float32)
                result = np.clip(result.astype(np.float32) + noise, 0, 255).astype(np.uint8)
                continue

            if effect == "vintage":
                arr = result.astype(np.float32)
                arr[..., 0] *= 1.08
                arr[..., 1] *= 1.0
                arr[..., 2] *= 0.9
                arr = (arr - 127.5) * 0.92 + 127.5
                result = np.clip(arr, 0, 255).astype(np.uint8)
                noise = np.random.normal(0, 8, result.shape).astype(np.float32)
                result = np.clip(result.astype(np.float32) + noise, 0, 255).astype(np.uint8)
                continue

            if effect == "cool_tone":
                arr = result.astype(np.float32)
                arr[..., 0] *= 0.95
                arr[..., 2] *= 1.12
                result = np.clip(arr, 0, 255).astype(np.uint8)
                continue

            if effect == "warm_tone":
                arr = result.astype(np.float32)
                arr[..., 0] *= 1.12
                arr[..., 2] *= 0.92
                result = np.clip(arr, 0, 255).astype(np.uint8)
                continue

            if effect == "posterize":
                result = np.asarray(ImageOps.posterize(image, bits=4))
                continue

            if effect == "pixelate":
                width, height = image.size
                small = image.resize((max(1, width // 12), max(1, height // 12)), Image.Resampling.BILINEAR)
                result = np.asarray(small.resize((width, height), Image.Resampling.NEAREST))
                continue

            if effect == "rgb_split":
                arr = result.astype(np.uint8)
                red = np.roll(arr[..., 0], 4, axis=1)
                green = arr[..., 1]
                blue = np.roll(arr[..., 2], -4, axis=1)
                result = np.stack((red, green, blue), axis=-1)
                continue

        return result.astype(np.uint8)

    def _metin_onizleme_uygula(
        self,
        gorsel: Image.Image,
        *,
        saniye: float,
        overlay_text: str,
        overlay_font_size: int,
        overlay_color: str,
        overlay_position: str,
        overlay_start: float | None,
        overlay_end: float | None,
    ) -> Image.Image:
        if not overlay_text.strip():
            return gorsel

        baslangic = 0.0 if overlay_start is None else max(0.0, float(overlay_start))
        bitis = float("inf") if overlay_end is None else max(0.0, float(overlay_end))
        if not (baslangic <= saniye <= bitis):
            return gorsel

        renk = {
            "white": "white",
            "black": "black",
            "yellow": "yellow",
            "red": "red",
            "blue": "blue",
        }.get(overlay_color, "white")
        image = gorsel.convert("RGB")
        draw = ImageDraw.Draw(image)
        font_boyutu = max(12, int(overlay_font_size))
        try:
            font = ImageFont.truetype("arial.ttf", font_boyutu)
        except Exception:
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", font_boyutu)
            except Exception:
                font = ImageFont.load_default()

        metin = overlay_text.strip()
        sol, ust, sag, alt = draw.textbbox((0, 0), metin, font=font)
        metin_genisligi = sag - sol
        metin_yuksekligi = alt - ust
        padding = 16
        x = max((image.width - metin_genisligi) // 2, padding)
        if overlay_position == "top":
            y = padding
        elif overlay_position == "center":
            y = max((image.height - metin_yuksekligi) // 2, padding)
        else:
            y = max(image.height - metin_yuksekligi - padding, padding)

        draw.rectangle(
            [x - 10, y - 6, min(x + metin_genisligi + 10, image.width - 1), min(y + metin_yuksekligi + 6, image.height - 1)],
            fill=(0, 0, 0),
        )
        draw.text((x, y), metin, font=font, fill=renk)
        return image

    def _metin_katmani_uygula(
        self,
        klip: VideoFileClip,
        *,
        overlay_text: str,
        overlay_font_size: int,
        overlay_color: str,
        overlay_position: str,
        overlay_start: float | None,
        overlay_end: float | None,
    ) -> VideoFileClip:
        if not overlay_text.strip():
            return klip

        klip_suresi = max(float(getattr(klip, "duration", 0.0) or 0.0), 0.0)
        baslangic = 0.0 if overlay_start is None else max(0.0, float(overlay_start))
        bitis = klip_suresi if overlay_end is None else min(float(overlay_end), klip_suresi)
        if baslangic >= klip_suresi:
            raise ValueError("Metin başlangıç zamanı video süresini aşıyor.")
        if bitis <= baslangic:
            raise ValueError("Metin bitiş zamanı başlangıçtan büyük olmalıdır.")

        renk_haritasi = {
            "white": "white",
            "black": "black",
            "yellow": "yellow",
            "red": "red",
            "blue": "blue",
        }
        konum_haritasi = {
            "top": ("center", "top"),
            "center": ("center", "center"),
            "bottom": ("center", "bottom"),
        }
        renk = renk_haritasi.get(overlay_color, "white")
        konum = konum_haritasi.get(overlay_position, ("center", "bottom"))
        font_boyutu = max(12, int(overlay_font_size))

        try:
            text_clip = TextClip(
                text=overlay_text,
                font="Arial",
                font_size=font_boyutu,
                color=renk,
                method="label",
                margin=(20, 10),
                duration=max(bitis - baslangic, 0.1),
            )
        except Exception:
            text_clip = TextClip(
                text=overlay_text,
                font_size=font_boyutu,
                color=renk,
                method="label",
                margin=(20, 10),
                duration=max(bitis - baslangic, 0.1),
            )

        if hasattr(text_clip, "with_position"):
            text_clip = text_clip.with_position(konum)
        if hasattr(text_clip, "with_start"):
            text_clip = text_clip.with_start(baslangic)
        if hasattr(text_clip, "with_end"):
            text_clip = text_clip.with_end(bitis)
        elif hasattr(text_clip, "with_duration"):
            text_clip = text_clip.with_duration(max(bitis - baslangic, 0.1))

        composite = CompositeVideoClip([klip, text_clip], size=getattr(klip, "size", None))
        if hasattr(composite, "with_audio") and getattr(klip, "audio", None) is not None:
            composite = composite.with_audio(klip.audio)
        elif hasattr(composite, "set_audio") and getattr(klip, "audio", None) is not None:
            composite = composite.set_audio(klip.audio)
        return composite

    def _fade_uygula(self, klip: VideoFileClip, sure: float, *, fade_out: bool) -> VideoFileClip:
        if klip.audio is None or sure <= 0:
            return klip

        effect_class = AudioFadeOut if fade_out else AudioFadeIn
        legacy_fx = legacy_audio_fadeout if fade_out else legacy_audio_fadein
        effect_name = "audio_fadeout" if fade_out else "audio_fadein"

        if effect_class is not None and hasattr(klip, "with_effects"):
            try:
                return klip.with_effects([effect_class(sure)])
            except Exception:
                pass

        clip_method = getattr(klip, effect_name, None)
        if callable(clip_method):
            try:
                return clip_method(sure)
            except Exception:
                pass

        if callable(legacy_fx) and hasattr(klip, "fx"):
            try:
                return klip.fx(legacy_fx, sure)
            except Exception:
                pass

        audio_method = getattr(klip.audio, effect_name, None)
        if callable(audio_method):
            try:
                yeni_ses = audio_method(sure)
                return self._sesi_klibe_bagla(klip, yeni_ses)
            except Exception:
                pass

        if effect_class is not None and hasattr(effect_class, "apply"):
            try:
                yeni_ses = effect_class(sure).apply(klip.audio)
                return self._sesi_klibe_bagla(klip, yeni_ses)
            except Exception:
                pass

        return klip

    def _sesi_klibe_bagla(self, klip: VideoFileClip, ses) -> VideoFileClip:
        if hasattr(klip, "set_audio"):
            return klip.set_audio(ses)
        if hasattr(klip, "with_audio"):
            return klip.with_audio(ses)
        return klip

    def _klip_getir(self) -> VideoFileClip:
        if self.klip is None:
            raise ValueError("Önce bir video açılmalıdır.")
        return self.klip
