"""Android yerel işlemler: kamera, galeri, ML Kit OCR + etiket ayrıştırma.
Android native helpers: camera, gallery, ML Kit OCR + label parsing."""
import os, re, json, uuid, shutil, threading, unicodedata
import urllib.parse

REQ_CAM, REQ_PICK, REQ_FILE = 4711, 4712, 4713
_st, _KEEP, _L = {}, [], {}


# ---------------------------------------------------------------- ayrıştırma
def fold(s):
    s = unicodedata.normalize("NFKD", s.replace("ı", "i").replace("İ", "I"))
    return re.sub(r"\s+", " ", "".join(c for c in s if not unicodedata.combining(c)).lower())


BRANDS = ["Bambu Lab", "eSUN", "Polymaker", "Sunlu", "Creality", "Elegoo", "Prusament", "Overture", "Hatchbox",
          "Anycubic", "Eryone", "Jayo", "Flashforge", "Kingroon", "Fillamentum", "colorFabb", "Amolen", "Voxelab",
          "Tinmorry", "Siraya Tech", "Atomic", "Geeetech", "Duramic", "Raise3D", "Zortrax", "Gembird", "3DJake",
          "Extrudr", "FormFutura", "Porima", "Filameon", "Kexcelled", "Mika3D", "Tronxy", "Snapmaker", "Recreus",
          "TOU3D", "Filamix", "Microzey", "ABG Filament", "Robonio", "Robo90", "Elas3D", "Zaxe", "Tesla3DP",
          "Fiberlogy", "Spectrum", "Devil Design", "Verbatim", "Rosa3D", "Sakata 3D", "Print-Me"]
BRAND_ALIAS = {"bambu": "Bambu Lab", "siraya": "Siraya Tech", "abg": "ABG Filament", "elas 3d": "Elas3D",
               "tesla 3dp": "Tesla3DP", "tou 3d": "TOU3D"}
GENERIC = ["filament", "printing", "print", "temp", "bed", "nozzle", "diameter", "weight", "tolerance", "color",
           "colour", "made in", "www", "http", "pla", "petg", "abs", "asa", "tpu", "kg", "mm", "spool", "warning", "1.75"]
STOP = {"filament", "filaments", "mm", "kg", "g", "color", "colour", "renk", "net", "diameter", "weight",
        "printing", "print", "temp", "nozzle", "nozul", "bed", "tabla", "for", "printer", "made", "by", "with", "spool",
        "carbon", "fiber", "fibre", "glass"}
LOAD_ERR = ""


def _load_names():
    """Bambu Studio filament isimleri (filaments.txt, BBL profilinden)."""
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "filaments.txt"), encoding="utf-8") as f:
            return [x.strip() for x in f if x.strip()]
    except Exception:
        return []


NAMES = _load_names()

# ---- renkler: Türkçe + İngilizce -> Türkçe görünen ad
COLOR_TR = {
    "black": "Siyah", "siyah": "Siyah", "white": "Beyaz", "beyaz": "Beyaz", "grey": "Gri", "gray": "Gri", "gri": "Gri",
    "silver": "Gümüş", "gumus": "Gümüş", "gold": "Altın", "altin": "Altın", "red": "Kırmızı", "kirmizi": "Kırmızı",
    "orange": "Turuncu", "turuncu": "Turuncu", "yellow": "Sarı", "sari": "Sarı", "green": "Yeşil", "yesil": "Yeşil",
    "blue": "Mavi", "mavi": "Mavi", "cyan": "Cyan", "magenta": "Magenta", "purple": "Mor", "violet": "Mor", "mor": "Mor",
    "lavender": "Lila", "lilac": "Lila", "lila": "Lila", "pink": "Pembe", "pembe": "Pembe", "brown": "Kahverengi",
    "kahverengi": "Kahverengi", "kahve": "Kahverengi", "beige": "Bej", "bej": "Bej", "cream": "Krem", "krem": "Krem",
    "ivory": "Fildişi", "fildisi": "Fildişi", "navy": "Lacivert", "lacivert": "Lacivert", "turquoise": "Turkuaz",
    "turkuaz": "Turkuaz", "teal": "Petrol Mavisi", "burgundy": "Bordo", "maroon": "Bordo", "bordo": "Bordo",
    "khaki": "Haki", "haki": "Haki", "olive": "Zeytin Yeşili", "zeytin": "Zeytin Yeşili", "mint": "Nane Yeşili",
    "nane": "Nane Yeşili", "coral": "Mercan", "mercan": "Mercan", "salmon": "Somon", "somon": "Somon",
    "bronze": "Bronz", "bronz": "Bronz", "copper": "Bakır", "bakir": "Bakır", "transparent": "Şeffaf",
    "clear": "Şeffaf", "seffaf": "Şeffaf", "saydam": "Şeffaf", "natural": "Doğal", "dogal": "Doğal",
    "charcoal": "Antrasit", "anthracite": "Antrasit", "antrasit": "Antrasit", "smoke": "Füme", "fume": "Füme",
    "lime": "Lime", "peach": "Şeftali", "seftali": "Şeftali", "mustard": "Hardal", "hardal": "Hardal",
    "indigo": "Çivit Mavisi", "plum": "Erik", "erik": "Erik", "sand": "Kum", "kum": "Kum", "ash": "Kül Grisi",
}
PAIR_TR = {("sky", "blue"): "Gökyüzü Mavisi", ("gok", "mavisi"): "Gökyüzü Mavisi", ("rose", "gold"): "Rose Gold",
           ("space", "gray"): "Uzay Grisi", ("space", "grey"): "Uzay Grisi", ("ice", "blue"): "Buz Mavisi",
           ("army", "green"): "Ordu Yeşili", ("hot", "pink"): "Canlı Pembe", ("lime", "green"): "Lime Yeşili"}
PAIR_FIRST = {a for a, _ in PAIR_TR}
MOD_TR = {"matte": "Mat", "mat": "Mat", "silk": "Silk", "glossy": "Parlak", "gloss": "Parlak", "parlak": "Parlak",
          "marble": "Mermer", "mermer": "Mermer", "galaxy": "Galaxy", "glow": "Glow", "fosforlu": "Fosforlu",
          "light": "Açık", "acik": "Açık", "dark": "Koyu", "koyu": "Koyu", "neon": "Neon", "pastel": "Pastel",
          "metallic": "Metalik", "metalik": "Metalik", "sparkle": "Sparkle", "glitter": "Glitter",
          "translucent": "Yarı Saydam"}
COLOR_KEYS = {"color", "colour", "colors", "colours", "colorway", "renk", "renkler"}


def find_color(t):
    toks = re.findall(r"[a-z]+", t)
    hits, i = [], 0
    while i < len(toks):
        if i + 1 < len(toks) and (toks[i], toks[i + 1]) in PAIR_TR:
            hits.append((i, 2, PAIR_TR[(toks[i], toks[i + 1])]))
            i += 2
            continue
        if toks[i] in COLOR_TR:
            hits.append((i, 1, COLOR_TR[toks[i]]))
        i += 1
    pick = None
    for ki, tk in enumerate(toks):  # "Color: ..." anahtarından hemen sonraki renk öncelikli
        if tk in COLOR_KEYS:
            pick = next((h for h in hits if ki < h[0] <= ki + 5), None)
            if pick:
                break
    pick = pick or (hits[0] if hits else None)
    if pick:
        i, n, name = pick
        mods = []
        for j in (i - 2, i - 1):
            if j >= 0 and toks[j] in MOD_TR and MOD_TR[toks[j]] not in mods:
                mods.append(MOD_TR[toks[j]])
        j = i + n
        if j < len(toks) and toks[j] in ("mat", "matte", "silk", "glossy", "parlak", "metalik", "metallic") \
                and MOD_TR[toks[j]] not in mods:
            mods.append(MOD_TR[toks[j]])
        return " ".join(mods + [name])
    for ki, tk in enumerate(toks):  # sözlükte yok: "Color:" sonrasındaki ham değer
        if tk in COLOR_KEYS:
            words = []
            for w in toks[ki + 1: ki + 4]:
                if w in STOP or len(w) < 3 or w in MOD_TR:
                    break
                words.append(w.title())
            if words:
                return " ".join(words)
    return ""


# ---- tür / model
MAT1 = re.compile(r"(?<![a-z0-9])(pla|petg|pet|abs|asa|tpu|pc|pa\d*|pva|hips|ppa|pps|pctg)"
                  r"(\+|-?(?:cf|gf|hf|hs|rcf))?(?![a-z0-9+])")
MAT2 = re.compile(r"(?<![a-z0-9])(pla)(?=(?:origin|silk|matte|basic|lite|max|tough|meta|galaxy|marble|wood|carbon"
                  r"|premium|hs|hf)(?![a-z0-9]))")


def norm_text(t):
    t = re.sub(r"\bpet[ -]g\b", "petg", t)
    t = re.sub(r"\b(pla|petg|abs|asa|tpu|pa\d*) ?(\+|plus)(?![a-z0-9])", r"\1+", t)
    t = re.sub(r"\bnylon\b", "pa", t)
    return re.sub(r"\b(pla|petg|abs|asa|pa\d*|pet) ?- ?(cf|gf|hf)\b", r"\1-\2", t)


def match_bambu(t):
    """Metindeki sözcüklerle tam örtüşen en özgül Bambu Studio filament adı."""
    toks = set(x for x in re.split(r"[\s,;:()/\\|]+", t) if x)
    best, bn = "", 0
    for name in NAMES:
        if name.startswith(("Generic ", "Bambu Support")):
            continue
        nt = fold(name).split()
        if len(nt) >= 2 and len(nt) > bn and all(w in toks for w in nt):
            best, bn = name, len(nt)
    return best


def _near(t, keys, lo, hi):
    for k in keys:
        for m in re.finditer(re.escape(k), t):
            seg = t[m.end(): m.end() + 45]
            n = re.search(r"(\d{2,3})(?:\s*(?:°|º)?\s*c?\s*(?:-|–|—|~|to)\s*(\d{2,3}))?", seg)
            if not n:
                continue
            a = int(n.group(1))
            b = int(n.group(2)) if n.group(2) else None
            if lo <= a <= hi and (b is None or lo <= b <= hi):
                return "%d-%d" % (a, b) if b else str(a)
    return ""


def parse_label(text):
    t = fold(text or "")
    t2 = norm_text(t)
    r = {}
    # marka
    best = None
    for b in BRANDS + list(BRAND_ALIAS):
        m = re.search(r"\b" + re.escape(fold(b)) + r"\b", t)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), BRAND_ALIAS.get(b, b))
    if best:
        r["marka"] = best[1]
    else:  # bilinmeyen marka: web adresi, yoksa en üstteki satır
        dm = re.search(r"(?:www\.|https?://)([a-z0-9][a-z0-9\-]{2,24})\.(?:com|net|org|co|tr)\b", t)
        if dm and dm.group(1) not in ("google", "facebook", "instagram"):
            r["marka"] = dm.group(1).upper() if re.search(r"\d", dm.group(1)) else dm.group(1).title()
        else:
            for ln in (text or "").splitlines():
                f = fold(ln)
                if (3 <= len(ln.strip()) <= 22 and re.search(r"[a-z]{2}", f) and not re.search(r"\d{3,}", f)
                        and not any(w in f for w in GENERIC)
                        and not any(w in COLOR_TR for w in re.findall(r"[a-z]+", f))):
                    r["marka"] = ln.strip()
                    break
    # tür / model: önce Bambu Studio listesiyle eşleştir, olmazsa malzeme + varyant sözcükleri
    bam = match_bambu(t2)
    if bam:
        r["tur"] = bam
    else:
        ms = [m for m in (MAT1.search(t2), MAT2.search(t2)) if m]
        if ms:
            m = min(ms, key=lambda x: x.start())
            mat = (m.group(1) + (m.group(2) or "")).upper() if m.re is MAT1 else m.group(1).upper()
            words = []
            for w in re.findall(r"[a-z0-9]+\+?", t2[m.end(): m.end() + 40]):
                if (w in STOP or w in COLOR_TR or w in MOD_TR or w in PAIR_FIRST or len(words) == 2
                        or not re.fullmatch(r"[a-z][a-z0-9]{1,9}\+?", w)):
                    break
                words.append(w.upper() if len(w) <= 3 else w.title())
            r["tur"] = " ".join([mat] + words)
    # çap / ağırlık
    d = re.search(r"\b(1[.,]75|2[.,]85)\s*mm", t)
    w = re.search(r"\b(\d+(?:[.,]\d+)?)\s*kg\b", t)
    g = (re.search(r"net\s*(?:weight|wt)?\D{0,6}(\d{3,4})\s*(?:g|gr|gram)\b", t)
         or re.search(r"\b(\d{3,4})\s*(?:g|gr|gram)\b", t))
    parts = []
    if d:
        parts.append(d.group(1).replace(",", ".") + "mm")
    if w:
        parts.append(w.group(1).replace(",", ".") + "kg")
    elif g and 100 <= int(g.group(1)) <= 5000:
        parts.append(g.group(1) + "g")
    if parts:
        r["boyut"] = " / ".join(parts)
    # sıcaklıklar
    bed = _near(t, ["bed", "tabla", "platform", "plate"], 20, 130)
    noz = _near(t, ["nozzle", "nozul", "extruder", "hotend", "printing temp", "print temp", "baski", "temp"], 150, 350)
    if not noz:
        for m in re.finditer(r"(\d{3})\s*(?:°|º)?\s*c?\s*(?:-|–|~|to)\s*(\d{3})", t):
            if 170 <= int(m.group(1)) <= 320 and 170 <= int(m.group(2)) <= 350:
                noz = "%s-%s" % m.groups()
                break
    if not bed:
        for m in re.finditer(r"\b(\d{2,3})\s*(?:°|º)?\s*c?\s*(?:-|–|~|to)\s*(\d{2,3})\b", t):
            if 20 <= int(m.group(1)) <= 110 and 20 <= int(m.group(2)) <= 130:
                bed = "%s-%s" % m.groups()
                break
    if noz:
        r["nozul"] = noz
    if bed:
        r["tabla"] = bed
    c = find_color(t2)
    if c:
        r["renk"] = c
    return r


# ---------------------------------------------------------------- Android
def _act():
    from jnius import autoclass
    return autoclass("org.kivy.android.PythonActivity").mActivity


def init():
    """Ana iş parçacığında çağrılmalı: sınıfları burada yükleriz, çünkü Python'un kendi
    thread'lerinde uygulama sınıfları (ML Kit) bulunamıyor (ClassNotFoundException)."""
    global LOAD_ERR
    from android import activity
    activity.bind(on_activity_result=_on_result)
    try:
        from jnius import autoclass
        for c in ("org.kivy.android.PythonActivity", "android.graphics.BitmapFactory",
                  "android.graphics.BitmapFactory$Options", "android.graphics.Bitmap",
                  "android.graphics.Bitmap$CompressFormat", "android.graphics.Matrix", "android.media.ExifInterface",
                  "java.io.FileOutputStream", "com.google.mlkit.vision.text.TextRecognition",
                  "com.google.mlkit.vision.text.latin.TextRecognizerOptions",
                  "com.google.mlkit.vision.common.InputImage", "com.google.mlkit.vision.text.Text",
                  "android.webkit.WebView", "android.view.View$MeasureSpec"):
            autoclass(c)
        _listeners()
    except Exception as ex:
        LOAD_ERR = "%s: %s" % (type(ex).__name__, ex)


def start_camera(d, cbs, ocr=True):
    from jnius import autoclass, cast
    Intent = autoclass("android.content.Intent")
    MS = autoclass("android.provider.MediaStore")
    Media = autoclass("android.provider.MediaStore$Images$Media")
    cv = autoclass("android.content.ContentValues")()
    act = _act()
    cv.put("_display_name", "filament_%s.jpg" % uuid.uuid4().hex[:8])
    cv.put("mime_type", "image/jpeg")
    if autoclass("android.os.Build$VERSION").SDK_INT >= 29:
        cv.put("relative_path", "Pictures/Filament")
    uri = act.getContentResolver().insert(Media.EXTERNAL_CONTENT_URI, cv)
    if uri is None:
        raise RuntimeError("Fotoğraf dosyası oluşturulamadı")
    i = Intent(MS.ACTION_IMAGE_CAPTURE)
    i.putExtra(MS.EXTRA_OUTPUT, cast("android.os.Parcelable", uri))
    i.addFlags(3)
    _st["cb"], _st["uri"] = (d, cbs, ocr), uri
    act.startActivityForResult(i, REQ_CAM)


def start_pick(d, cbs, ocr=True):
    from jnius import autoclass, cast
    Intent = autoclass("android.content.Intent")
    S = autoclass("java.lang.String")
    i = Intent(Intent.ACTION_GET_CONTENT)
    i.setType("image/*")
    i.addCategory(Intent.CATEGORY_OPENABLE)
    _st["cb"] = (d, cbs, ocr)
    _act().startActivityForResult(Intent.createChooser(i, cast("java.lang.CharSequence", S("Resim seç"))), REQ_PICK)


def _on_result(req, res, data):
    if req not in (REQ_CAM, REQ_PICK, REQ_FILE):
        return
    cb = _st.pop("cb", None)
    uri = _st.pop("uri", None)
    if not cb:
        return
    d, cbs, ocr = cb
    try:
        if res != -1:  # iptal
            if uri is not None:
                try:
                    _act().getContentResolver().delete(uri, None, None)
                except Exception:
                    pass
            return
        if req in (REQ_PICK, REQ_FILE):
            uri = data.getData()
    except Exception as ex:
        return cbs["error"]("Sonuç alınamadı: %s" % ex)
    if req == REQ_FILE:
        return threading.Thread(target=_copy_file, args=(uri, d, cbs), daemon=True).start()
    threading.Thread(target=_work, args=(uri, d, ocr, cbs), daemon=True).start()


def _load_bitmap(uri, maxd=1600):
    from jnius import autoclass
    BF = autoclass("android.graphics.BitmapFactory")
    Bitmap = autoclass("android.graphics.Bitmap")
    cr = _act().getContentResolver()
    o = autoclass("android.graphics.BitmapFactory$Options")()
    o.inSampleSize = 2
    ins = cr.openInputStream(uri)
    bm = BF.decodeStream(ins, None, o)
    ins.close()
    deg = 0
    try:
        ins = cr.openInputStream(uri)
        ori = autoclass("android.media.ExifInterface")(ins).getAttributeInt("Orientation", 1)
        ins.close()
        deg = {6: 90, 3: 180, 8: 270}.get(ori, 0)
    except Exception:
        pass
    w, h = bm.getWidth(), bm.getHeight()
    s = min(1.0, maxd / float(max(w, h)))
    if deg or s < 1.0:
        m = autoclass("android.graphics.Matrix")()
        m.postRotate(float(deg))
        m.postScale(float(s), float(s))
        bm = Bitmap.createBitmap(bm, 0, 0, w, h, m, True)
    return bm


def _save(bm, dst):
    from jnius import autoclass
    out = autoclass("java.io.FileOutputStream")(dst)
    bm.compress(autoclass("android.graphics.Bitmap$CompressFormat").JPEG, 85, out)
    out.close()


def _work(uri, d, ocr, cbs):
    try:
        bm = _load_bitmap(uri)
        dst = os.path.join(d, "p%s.jpg" % uuid.uuid4().hex)
        _save(bm, dst)
        cbs["photo"](dst)
        if ocr:  # ML Kit'i ana thread'den başlat
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: _safe_recognize(bm, cbs), 0)
    except Exception as ex:
        cbs["error"]("Fotoğraf işlenemedi: %s" % ex)


def _safe_recognize(bm, cbs):
    try:
        recognize(bm, cbs["text"], cbs["error"])
    except Exception as ex:
        cbs["error"]("OCR başlatılamadı: %s: %s" % (type(ex).__name__, ex))


def open_url(url):
    from jnius import autoclass
    Intent = autoclass("android.content.Intent")
    _act().startActivity(Intent(Intent.ACTION_VIEW, autoclass("android.net.Uri").parse(url)))


def _listeners():
    if _L:
        return _L
    from jnius import PythonJavaClass, java_method, cast

    class OK(PythonJavaClass):
        __javainterfaces__ = ["com/google/android/gms/tasks/OnSuccessListener"]
        __javacontext__ = "app"

        def __init__(self, cb):
            super().__init__()
            self.cb = cb

        @java_method("(Ljava/lang/Object;)V")
        def onSuccess(self, r):
            try:
                txt = str(cast("com.google.mlkit.vision.text.Text", r).getText())
            except Exception as ex:
                return self.cb(None, str(ex))
            self.cb(txt, None)

    class BAD(PythonJavaClass):
        __javainterfaces__ = ["com/google/android/gms/tasks/OnFailureListener"]
        __javacontext__ = "app"

        def __init__(self, cb):
            super().__init__()
            self.cb = cb

        @java_method("(Ljava/lang/Exception;)V")
        def onFailure(self, e):
            self.cb(None, str(e.toString()))

    class VCB(PythonJavaClass):
        __javainterfaces__ = ["android/webkit/ValueCallback"]
        __javacontext__ = "app"

        def __init__(self, cb):
            super().__init__()
            self.cb = cb

        @java_method("(Ljava/lang/Object;)V")
        def onReceiveValue(self, v):
            self.cb(v)

    _L.update(OK=OK, BAD=BAD, VCB=VCB)
    return _L


def recognize(bm, on_text, on_err):
    from jnius import autoclass
    L = _listeners()
    rec = autoclass("com.google.mlkit.vision.text.TextRecognition").getClient(
        autoclass("com.google.mlkit.vision.text.latin.TextRecognizerOptions").DEFAULT_OPTIONS)
    img = autoclass("com.google.mlkit.vision.common.InputImage").fromBitmap(bm, 0)

    def done(txt, err):
        on_text(txt) if txt is not None else on_err("Etiket okunamadı: %s" % err)

    ok, bad = L["OK"](done), L["BAD"](done)
    _KEEP.extend([ok, bad, rec])
    task = rec.process(img)
    task.addOnSuccessListener(ok)
    task.addOnFailureListener(bad)


def recognize_file(path, on_text, on_err):
    from jnius import autoclass
    bm = autoclass("android.graphics.BitmapFactory").decodeFile(path)
    if bm is None:
        return on_err("Fotoğraf dosyası açılamadı.")
    recognize(bm, on_text, on_err)


def pick_file(d, cbs):
    """Herhangi bir dosya seç (yedek zip'i). Seçilen dosya d klasörüne kopyalanır."""
    from jnius import autoclass, cast
    Intent = autoclass("android.content.Intent")
    S = autoclass("java.lang.String")
    i = Intent(Intent.ACTION_GET_CONTENT)
    i.setType("*/*")
    i.addCategory(Intent.CATEGORY_OPENABLE)
    _st["cb"] = (d, cbs, False)
    _act().startActivityForResult(Intent.createChooser(i, cast("java.lang.CharSequence", S("Yedek dosyası seç"))), REQ_FILE)


def _copy_file(uri, d, cbs):
    try:
        fd = _act().getContentResolver().openFileDescriptor(uri, "r").detachFd()
        dst = os.path.join(d, "yedek_%s.zip" % uuid.uuid4().hex[:6])
        with os.fdopen(fd, "rb") as f, open(dst, "wb") as g:
            shutil.copyfileobj(f, g)
        cbs["file"](dst)
    except Exception as ex:
        cbs["error"]("Dosya okunamadı: %s" % ex)


def save_download(src, name, mime):
    """Dosyayı telefonun İndirilenler klasörüne kaydeder."""
    from jnius import autoclass
    act = _act()
    if autoclass("android.os.Build$VERSION").SDK_INT >= 29:
        cv = autoclass("android.content.ContentValues")()
        cv.put("_display_name", name)
        cv.put("mime_type", mime)
        cv.put("relative_path", "Download")
        cr = act.getContentResolver()
        uri = cr.insert(autoclass("android.provider.MediaStore$Downloads").EXTERNAL_CONTENT_URI, cv)
        if uri is None:
            raise RuntimeError("İndirilenler'de dosya oluşturulamadı")
        fd = cr.openFileDescriptor(uri, "w").detachFd()
        with os.fdopen(fd, "wb") as f, open(src, "rb") as g:
            shutil.copyfileobj(g, f)
        return {"uri": uri, "label": "İndirilenler/" + name}
    d = autoclass("android.os.Environment").getExternalStoragePublicDirectory("Download").getAbsolutePath()
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, name)
    shutil.copyfile(src, dst)
    return {"uri": None, "label": dst}


def share_uri(uri, mime):
    from jnius import autoclass, cast
    Intent = autoclass("android.content.Intent")
    S = autoclass("java.lang.String")
    i = Intent(Intent.ACTION_SEND)
    i.setType(mime)
    i.putExtra(Intent.EXTRA_STREAM, cast("android.os.Parcelable", uri))
    i.addFlags(1)
    _act().startActivity(Intent.createChooser(i, cast("java.lang.CharSequence", S("Yedeği gönder"))))


# ---------------------------------------------------------------- görsel işleme / arama
def shrink_file(src, dst, maxd=900):
    """Android'in kendi çözücüsü: jpg/png/webp (ve destekliyorsa avif) -> küçük jpg."""
    from jnius import autoclass
    BF = autoclass("android.graphics.BitmapFactory")
    Opts = autoclass("android.graphics.BitmapFactory$Options")
    o = Opts()
    o.inJustDecodeBounds = True
    BF.decodeFile(src, o)
    sample = 1
    while max(o.outWidth, o.outHeight) // sample > 2000:
        sample *= 2
    o2 = Opts()
    o2.inSampleSize = sample
    bm = BF.decodeFile(src, o2)
    if bm is None:
        raise RuntimeError("görsel çözülemedi")
    w, h = bm.getWidth(), bm.getHeight()
    s = min(1.0, maxd / float(max(w, h)))
    if s < 1.0:
        bm = autoclass("android.graphics.Bitmap").createScaledBitmap(bm, int(w * s), int(h * s), True)
    out = autoclass("java.io.FileOutputStream")(dst)
    bm.compress(autoclass("android.graphics.Bitmap$CompressFormat").JPEG, 85, out)
    out.close()


UA_D = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36")
JS_DDG = ("(function(){var o=[];document.querySelectorAll('img').forEach(function(i){"
          "var s=i.currentSrc||i.src||'';if(s.indexOf('external-content.duckduckgo.com')>-1)o.push(s)});"
          "return JSON.stringify(o)})()")
JS_GOOGLE = ("(function(){var o=[],h=document.documentElement.innerHTML,"
             "re=/\\[\"(https?:\\/\\/[^\"]+?)\",\\s*(\\d{2,4}),\\s*(\\d{2,4})\\]/g,m;"
             "while((m=re.exec(h))!==null){var u=m[1].replace(/\\\\u003d/g,'=').replace(/\\\\u0026/g,'&');"
             "if(u.indexOf('gstatic.com')<0&&u.indexOf('google.')<0&&parseInt(m[2])>=150)o.push(u);if(o.length>=20)break}"
             "if(o.length<3){document.querySelectorAll('img').forEach(function(i){var s=i.src||'';"
             "if(s.indexOf('http')==0&&s.indexOf('gstatic.com')>-1&&i.naturalWidth>80)o.push(s)})}"
             "return JSON.stringify(o)})()")


def web_images(query, kind, on_urls, on_err, waits=(6, 5, 6, 8)):
    """Gizli WebView (telefonun gerçek Chrome motoru) ile görsel adresleri toplar.
    kind: 'ddg' | 'google'. Sonuç ana thread'de on_urls(list) / on_err(str) ile döner."""
    from kivy.clock import Clock
    from android.runnables import run_on_ui_thread
    from jnius import autoclass
    enc = urllib.parse.quote(query)
    if kind == "ddg":
        url, js = "https://duckduckgo.com/?q=%s&iax=images&ia=images&kl=tr-tr" % enc, JS_DDG
    else:
        url, js = "https://www.google.com/search?tbm=isch&hl=tr&q=%s" % enc, JS_GOOGLE
    st = {"wv": None, "n": 0, "done": False}
    VCB = _listeners()["VCB"]

    @run_on_ui_thread
    def destroy():
        try:
            if st["wv"] is not None:
                st["wv"].stopLoading()
                st["wv"].destroy()
                st["wv"] = None
        except Exception:
            pass

    def finish(urls=None, err=None):
        if st["done"]:
            return
        st["done"] = True
        destroy()
        if urls:
            Clock.schedule_once(lambda dt: on_urls(urls), 0)
        else:
            Clock.schedule_once(lambda dt: on_err(err or "sonuç yok"), 0)

    def got(v):
        try:
            s = "null" if v is None else (v if isinstance(v, str) else str(v.toString()))
            arr = json.loads(json.loads(s)) if s not in ("null", "") else []
        except Exception:
            arr = []
        urls = list(dict.fromkeys(arr))
        st["n"] += 1
        if len(urls) >= 3:
            return finish(urls=urls[:12])
        if st["n"] >= len(waits):
            return finish(urls=urls or None, err="sayfa görsel vermedi")
        Clock.schedule_once(lambda dt: grab(), waits[st["n"]])

    @run_on_ui_thread
    def grab():
        if st["done"] or st["wv"] is None:
            return
        try:
            cb = VCB(got)
            _KEEP.append(cb)
            st["wv"].evaluateJavascript(js, cb)
        except Exception as ex:
            finish(err="JS çalıştırılamadı: %s: %s" % (type(ex).__name__, ex))

    @run_on_ui_thread
    def start():
        try:
            wv = autoclass("android.webkit.WebView")(_act())
            s = wv.getSettings()
            s.setJavaScriptEnabled(True)
            s.setDomStorageEnabled(True)
            s.setUserAgentString(UA_D)
            ms = autoclass("android.view.View$MeasureSpec")
            wv.measure(ms.makeMeasureSpec(1080, ms.EXACTLY), ms.makeMeasureSpec(2400, ms.EXACTLY))
            wv.layout(0, 0, 1080, 2400)
            st["wv"] = wv
            wv.loadUrl(url)
        except Exception as ex:
            return finish(err="WebView açılamadı: %s: %s" % (type(ex).__name__, ex))
        Clock.schedule_once(lambda dt: grab(), waits[0])

    start()
