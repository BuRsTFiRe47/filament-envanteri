# Filament Envanteri / Filament Inventory

## Türkçe
Evdeki filamentlerin etiket fotoğraflarını çekip, marka/türe göre internetten örnek görsel bulan ve not tutan Android uygulaması. Veriler telefonda gerçek bir **SQLite** veritabanında (`filamentler.db`) saklanır. Koyu tema varsayılandır.

**Özellikler:** etiket fotoğrafı (kamera/galeri) · **etiketten otomatik okuma (ML Kit OCR: marka, tür, renk, çap, sıcaklıklar)** · otomatik örnek görsel arama (Bing) · sıcaklık ve not alanları · arama · listeyi CSV olarak WhatsApp/Telegram vb. ile gönderme.

### APK nasıl alınır (telefonda derleme gerekmez)
1. GitHub'da `BuRsTFiRe47/filament-envanteri` adlı bir repo aç ve bu dosyaların hepsini yükle:
   `git remote add origin https://github.com/BuRsTFiRe47/filament-envanteri.git && git push -u origin main`
2. Repo'da **Actions** sekmesine gir; derleme otomatik başlar (ilk seferde ~20-40 dk). Gerekirse **Run workflow** ile elle başlat.
3. Bitince çalıştırmanın altındaki **Artifacts → filament-envanteri-apk** dosyasını indir, zip'ten çıkan `.apk`'yı telefona kur ("bilinmeyen kaynaklara izin ver").

### Notlar
- OCR bazı alanları kaçırabilir; 'Etiketten okunan metin' kutusunda ham metni görürsün, alanları elle düzeltebilirsin.
- İnternet görseli bulunamazsa/yanlışsa **Sonraki**'ne bas ya da galeriden kendin seç.
- Veritabanı uygulamanın özel klasöründe durur; uygulamayı silersen veri de silinir. Düzenli olarak **Listeyi gönder** ile yedek al.

## English
An Android app to photograph your filament spool labels, auto-fetch sample images by brand/type, and keep notes. Data lives in a real **SQLite** database on the phone. Dark theme by default.

**Features:** label photo (camera/gallery) · **automatic label reading (on-device ML Kit OCR: brand, type, color, diameter, temps)** · automatic sample-image search (Bing) · temperature and notes fields · search · share the list as CSV via any messaging app.

### Getting the APK (no on-device build needed)
1. Create `BuRsTFiRe47/filament-envanteri` on GitHub and push all these files:
   `git remote add origin https://github.com/BuRsTFiRe47/filament-envanteri.git && git push -u origin main`
2. Open the **Actions** tab; the build starts automatically (~20-40 min the first time) or use **Run workflow**.
3. Download **Artifacts → filament-envanteri-apk**, unzip, and install the `.apk` (allow unknown sources).

### Notes
- OCR may miss some fields; the raw text is shown in the 'Etiketten okunan metin' box so you can fix fields by hand.
- If no/wrong web image is found, press **Sonraki** (next) or pick one from the gallery.
- The database sits in the app's private storage and is removed on uninstall. Back up regularly with **Listeyi gönder**.
