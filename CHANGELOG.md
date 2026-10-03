# Değişiklikler / Changelog

## 1.3.1
**TR** — Listede artık etiket fotoğrafı yerine seçilen örnek görsel gösterilir (örnek görsel yoksa etiket fotoğrafı).
**EN** — The list now shows the chosen sample image instead of the label photo (falls back to the label photo if there is no sample).

## 1.3.0
**TR**
- Tür ve Model tek alan oldu: Bambu Studio'nun filament adları (100 isim, `filaments.txt`) arasından aranıp seçilebilir; etiket okununca en uygun ad otomatik yazılır. Eski kayıtlardaki model, türün içine katıldı
- Renk tanıma genişledi: Türkçe + İngilizce çok sayıda renk ve ek (mat, silk, açık, koyu...); Türkçe normalize edilir, bilinmeyen renk "Color:" sonrasından alınır
- Örnek görsel arama: telefonun gerçek tarayıcı motoruyla (gizli WebView) DuckDuckGo ve Google; indirilemeyen görseller otomatik atlanır; WebP gibi biçimler Android çözücüsüyle açılır; arama durumu ekranda görünür
**EN**
- Type and Model merged into one field: searchable list of Bambu Studio filament names (100 names, `filaments.txt`); the best match is filled in automatically after reading a label. Existing models were folded into the type
- Broader color recognition: many Turkish + English colors and modifiers (matte, silk, light, dark...), normalized to Turkish; unknown colors are taken from the text after "Color:"
- Sample-image search: runs in the phone's real browser engine (hidden WebView) on DuckDuckGo and Google; undownloadable images are skipped automatically; WebP etc. decoded by Android; search status is shown on screen

## 1.2.0
**TR**
- Etiket fotoğrafından otomatik okuma (ML Kit OCR): marka, model, tür, renk, çap/ağırlık, nozul/tabla sıcaklığı
- Türkiye'de yaygın filament markaları + bilinmeyen markalar için web adresi/ilk satır tahmini
- Model/Seri alanı; marka+model ile daha isabetli örnek görsel arama (DuckDuckGo + ürün sayfası görselleri, Bing kaldırıldı)
- Tam yedek (kayıtlar + fotoğraflar, zip) ve yedekten yükleme
- Android'in kendi kamerası ile fotoğraf çekme, galeriden seçme
- Sabit imza anahtarı: sonraki sürümler mevcut uygulamanın üstüne güncellenir

**EN**
- Automatic label reading (ML Kit OCR): brand, model, type, color, diameter/weight, nozzle/bed temps
- Common Turkish-market filament brands + brand guess from website/first line for unknown brands
- Model/Series field; better sample-image search with brand+model (DuckDuckGo + product-page images, Bing removed)
- Full backup (records + photos, zip) and restore
- Photos via Android's own camera app, or pick from gallery
- Fixed signing key: later versions update over the installed app

## 1.0.0
- İlk sürüm / First release: SQLite envanter, fotoğraf, notlar, CSV paylaşım / SQLite inventory, photos, notes, CSV share
