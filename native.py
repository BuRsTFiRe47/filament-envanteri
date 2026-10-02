"""Android yerel işlemler: kamera, galeri, ML Kit OCR + etiket ayrıştırma.
Android native helpers: camera, gallery, ML Kit OCR + label parsing."""
import os, re, uuid, shutil, threading, unicodedata

REQ_CAM, REQ_PICK, REQ_FILE = 4711, 4712, 4713
_st, _KEEP, _L = {}, [], {}


# ---------------------------------------------------------------- ayrıştırma
def fold(s):
    s = unicodedata.normalize("NFKD", s.replace("ı", "i").replace("İ", "I"))
    return re.sub(r"\s+", " ", "".join(c for c in s if not unicodedata.combining(c)).lower())


BRANDS = ["Bambu Lab", "eSUN", "Polymaker", "Sunlu", "Creality", "Elegoo", "Prusament", "Overture", "Hatchbox",
          "Anycubic", "Eryone", "Jayo", "Flashforge", "Kingroon", "Fillamentum", "colorFabb", "Amolen", "Voxelab",
          "Tinmorry", "Siraya Tech", "Atomic", "Geeetech", "Duramic", "Raise3D", "Zortrax", "Gembird", "3DJake",
          "Extrudr", "FormFutura", "Porima", "Filameon", "Kexcelled", "Mika3D", "Tronxy", "Snapmaker", "Recreus", "TOU3D", "Filamix", "Microzey", "ABG Filament", "Robonio",
          "Robo90", "Elas3D", "Zaxe", "Tesla3DP", "Fiberlogy", "Spectrum", "Devil Design", "Verbatim", "Rosa3D",
          "Sakata 3D", "Print-Me"]
BRAND_ALIAS = {"bambu": "Bambu Lab", "siraya": "Siraya Tech", "abg": "ABG Filament", "elas 3d": "Elas3D",
               "tesla 3dp": "Tesla3DP", "tou 3d": "TOU3D"}
TR_KEYS = {"siyah", "beyaz", "gri", "kirmizi", "mavi", "yesil", "sari", "turuncu", "mor", "pembe", "gumus", "altin",
           "seffaf", "kahverengi"}
GENERIC = ["filament", "printing", "print", "temp", "bed", "nozzle", "diameter", "weight", "tolerance", "color",
           "colour", "made in", "www", "http", "pla", "petg", "abs", "asa", "tpu", "kg", "mm", "spool", "warning", "1.75"]
LOAD_ERR = ""
TYPES = [("ppa-cf", r"\bppa[- ]?cf\b"), ("PLA+", r"\bpla ?(\+|plus|pro)"), ("PETG", r"\bpet-?g\b"),
         ("ABS", r"\babs\b"), ("ASA", r"\basa\b"), ("TPU", r"\btpu\b"), ("PA", r"\b(nylon|pa ?12|pa ?6|pa)\b"),
         ("PLA", r"\bpla\b|\bpla(?=(?:origin|silk|matte|basic|lite|max|tough|meta|galaxy|marble|wood|carbon|premium|hs|hf)\b)")]
COLORS = {"black": "Black", "white": "White", "grey": "Grey", "gray": "Grey", "red": "Red", "blue": "Blue",
          "green": "Green", "yellow": "Yellow", "orange": "Orange", "purple": "Purple", "pink": "Pink",
          "silver": "Silver", "gold": "Gold", "transparent": "Transparent", "natural": "Natural",
          "brown": "Brown", "beige": "Beige", "siyah": "Siyah", "beyaz": "Beyaz", "gri": "Gri",
          "kirmizi": "Kırmızı", "mavi": "Mavi", "yesil": "Yeşil", "sari": "Sarı", "turuncu": "Turuncu",
          "mor": "Mor", "pembe": "Pembe", "gumus": "Gümüş", "altin": "Altın", "seffaf": "Şeffaf",
          "kahverengi": "Kahverengi"}
STOP = {"filament", "filaments", "mm", "kg", "g", "color", "colour", "renk", "net", "diameter", "weight",
        "printing", "print", "temp", "nozzle", "nozul", "bed", "tabla", "for", "printer", "made", "by", "with", "spool"}
MODS = ["matte", "mat", "silk", "glossy", "marble", "galaxy", "glow", "light", "dark", "neon", "pastel"]


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
    r = {}
    # marka
    best = None
    for b in BRANDS + list(BRAND_ALIAS):
        m = re.search(r"\b" + re.escape(fold(b)) + r"\b", t)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), BRAND_ALIAS.get(b, b))
    if best:
        r["marka"] = best[1]
    if "marka" not in r:  # bilinmeyen marka: web adresi, yoksa en üstteki satır
        dm = re.search(r"(?:www\.|https?://)([a-z0-9][a-z0-9\-]{2,24})\.(?:com|net|org|co|tr)\b", t)
        if dm and dm.group(1) not in ("google", "facebook", "instagram"):
            r["marka"] = dm.group(1).upper() if re.search(r"\d", dm.group(1)) else dm.group(1).title()
        else:
            for ln in (text or "").splitlines():
                f = fold(ln)
                if (3 <= len(ln.strip()) <= 22 and re.search(r"[a-z]{2}", f) and not re.search(r"\d{3,}", f)
                        and not any(w in f for w in GENERIC) and not any(c in f for c in COLORS)):
                    r["marka"] = ln.strip()
                    break
    # tür (metindeki ilk geçen; eşitlikte listedeki sıra)
    hits = [(m.start(), i, n) for i, (n, p) in enumerate(TYPES) for m in [re.search(p, t)] if m]
    if hits:
        n = min(hits)[2]
        r["tur"] = "PPA-CF" if n == "ppa-cf" else n
        tm = re.search(dict(TYPES)[n], t)
        mod = []
        for w in re.findall(r"[a-z0-9]+", t[tm.end(): tm.end() + 40]):
            if (w in STOP or w in COLORS or w in MODS or len(mod) == 3
                    or not re.fullmatch(r"[a-z][a-z0-9]{1,9}", w)):
                break
            mod.append(w)
        if mod:
            r["model"] = " ".join(x.upper() if len(x) <= 3 else x.title() for x in mod)
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
    # renk
    m = re.search(r"(?:colou?r|renk)\s*[:=]?\s*([a-z ]{3,24})", t)
    seg = m.group(1) if m else t
    ms = list(re.finditer(r"\b(" + "|".join(COLORS) + r")\b", seg))
    found = next((x for x in ms if x.group(1) in TR_KEYS), ms[0] if ms else None)
    if found:
        pre = seg[:found.start()].split()[-1:] if seg[:found.start()].strip() else []
        mod = pre[0].title() + " " if pre and pre[0] in MODS else ""
        r["renk"] = mod + COLORS[found.group(1)]
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
                  "com.google.mlkit.vision.common.InputImage", "com.google.mlkit.vision.text.Text"):
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

    _L.update(OK=OK, BAD=BAD)
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
