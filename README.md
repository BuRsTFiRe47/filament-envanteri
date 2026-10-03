# Filament Envanteri / Filament Inventory

## Türkçe
Evdeki filamentlerin etiket fotoğraflarını çekip, marka/türe göre internetten örnek görsel bulan ve not tutan Android uygulaması. Veriler telefonda gerçek bir **SQLite** veritabanında (`filamentler.db`) saklanır. Koyu tema varsayılandır.

**Özellikler:** etiket fotoğrafı (kamera/galeri) · **etiketten otomatik okuma (ML Kit OCR: marka, tür, renk, çap, sıcaklıklar)** · otomatik örnek görsel arama (telefonun gerçek tarayıcı motoruyla DuckDuckGo/Google) · sıcaklık ve not alanları · arama · tek **Tür / Model** alanı (Bambu Studio'nun filament adlarından seçilir, `filaments.txt`) ve marka+model ile daha isabetli görsel arama · listeyi CSV olarak gönderme · **tam yedek (kayıtlar + fotoğraflar, zip)**: İndirilenler klasörüne kaydeder ve paylaşım menüsünü açar; **Yedekten yükle** ile geri alır (aynı kayıtları atlar).

### APK nasıl alınır (telefonda derleme gerekmez)
1. GitHub'da `BuRsTFiRe47/filament-envanteri` adlı bir repo aç ve bu dosyaların hepsini yükle:
   `git remote add origin https://github.com/BuRsTFiRe47/filament-envanteri.git && git push -u origin main`
2. Repo'da **Actions** sekmesine gir; derleme otomatik başlar (ilk seferde ~20-40 dk). Gerekirse **Run workflow** ile elle başlat.
3. Bitince çalıştırmanın altındaki **Artifacts → filament-envanteri-apk** dosyasını indir, zip'ten çıkan `.apk`'yı telefona kur ("bilinmeyen kaynaklara izin ver").

### Git: "push reddedildi / remote'ta yerelde olmayan değişiklikler var"
Sebep: GitHub'da (web arayüzünden) yaptığın düzenlemeler yerel klasörde yok. Zip'teki dosyalar zaten güncel olduğu için en kolayı:
```
cd filament-envanteri
git branch -M main
git fetch origin
git push --force-with-lease origin main
```
Git kullanmak istemezsen: repo sayfasında **Add file → Upload files**, zip'ten çıkan klasörün *içindekileri* (`.github` klasörü dahil) sürükle, commit et.

### Sürüm çıkarma / Releasing
`buildozer.spec` içindeki `version` değerini güncelle, sonra: / bump `version` in `buildozer.spec`, then:
```
git add -A && git commit -m "v1.2.0"
git tag v1.3.5
git push origin main --tags
```
`v*` etiketi push'lanınca APK, GitHub **Releases** sayfasına otomatik eklenir. / Pushing a `v*` tag attaches the APK to the GitHub **Releases** page automatically.

### Notlar
- OCR bazı alanları kaçırabilir; 'Etiketten okunan metin' kutusunda ham metni görürsün, alanları elle düzeltebilirsin.
- İnternet görseli bulunamazsa/yanlışsa **Sonraki**'ne bas ya da galeriden kendin seç.
- Veritabanı uygulamanın özel klasöründe durur; uygulamayı silersen veri de silinir. Düzenli olarak **Listeyi gönder** ile yedek al.

## English
An Android app to photograph your filament spool labels, auto-fetch sample images by brand/type, and keep notes. Data lives in a real **SQLite** database on the phone. Dark theme by default.

**Features:** label photo (camera/gallery) · **automatic label reading (on-device ML Kit OCR: brand, type, color, diameter, temps)** · automatic sample-image search (phone's real browser engine, DuckDuckGo/Google) · temperature and notes fields · search · a single **Type / Model** field (pick from Bambu Studio filament names, `filaments.txt`) and brand+model image search · share the list as CSV · **full backup (records + photos, zip)** saved to Downloads with a share sheet; **Yedekten yükle** restores it (skips duplicates).

### Getting the APK (no on-device build needed)
1. Create `BuRsTFiRe47/filament-envanteri` on GitHub and push all these files:
   `git remote add origin https://github.com/BuRsTFiRe47/filament-envanteri.git && git push -u origin main`
2. Open the **Actions** tab; the build starts automatically (~20-40 min the first time) or use **Run workflow**.
3. Download **Artifacts → filament-envanteri-apk**, unzip, and install the `.apk` (allow unknown sources).

### Git: "push rejected / remote contains work you do not have locally"
Cause: edits made in the GitHub web editor are not in your local folder. The files in this zip are already up to date, so the simplest fix is:
```
cd filament-envanteri
git branch -M main
git fetch origin
git push --force-with-lease origin main
```
Without git: on the repo page use **Add file → Upload files**, drag the *contents* of the extracted folder (including `.github`) and commit.

### Notes
- OCR may miss some fields; the raw text is shown in the 'Etiketten okunan metin' box so you can fix fields by hand.
- If no/wrong web image is found, press **Sonraki** (next) or pick one from the gallery.
- The database sits in the app's private storage and is removed on uninstall. Back up regularly with **Listeyi gönder**.
