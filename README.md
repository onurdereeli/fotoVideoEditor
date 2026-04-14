# Karanlık Kare

Karanlık Kare, Python ve Tkinter ile geliştirilen özgün bir masaüstü medya düzenleme uygulamasıdır. Uygulama koyu temalı bir arayüz sunar ve fotoğraf ile video işlemlerini ayrı sekmeler altında toplar.

## Özellikler

- Fotoğraf açma ve önizleme
- Fotoğraf döndürme
- Fotoğraf yeniden boyutlandırma
- Fotoğraf kırpma
- Parlaklık ve kontrast ayarı
- Temel fotoğraf filtreleri
- Fotoğraf kaydetme
- Video açma ve temel bilgi gösterimi
- İlk kareden basit video önizlemesi
- Video trim
- Video yeniden boyutlandırma
- Sesi kapatarak veya normal biçimde dışa aktarma

## Proje Yapısı

```text
main.py
requirements.txt
README.md
app/
  ui/
  editors/
  services/
  utils/
assets/
  icons/
```

## Kurulum

1. Python 3.11 veya daha güncel bir sürüm kurun.
2. Proje klasöründe bir sanal ortam oluşturun:

```bash
python -m venv .venv
```

3. Sanal ortamı etkinleştirin:

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

4. Gerekli paketleri yükleyin:

```bash
pip install -r requirements.txt
```

## Çalıştırma

Uygulamayı proje klasöründe şu komutla başlatabilirsiniz:

```bash
python main.py
```

## Notlar

- Video dışa aktarma için `moviepy` kullanılır.
- Bazı sistemlerde video işlemleri için `ffmpeg` arka planda gerekli olabilir.
- Uygulamadaki tüm kullanıcı metinleri Türkçedir.
