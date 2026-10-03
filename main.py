"""Filament Envanteri - Kivy + SQLite (Android APK).
Koyu tema / dark theme by default."""
import os, re, ssl, uuid, json, time, zipfile, sqlite3, threading, html as H
import urllib.parse, urllib.request
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.utils import platform
import native

__version__ = "1.3.5"  # buildozer.spec ile aynı olmalı / keep in sync with buildozer.spec
COLS = ["marka", "tur", "renk", "boyut", "nozul", "tabla", "etiket", "ornek", "notlar", "ocr"]
TURLER = ["PLA", "PLA+", "PETG", "ABS", "ASA", "TPU", "PA", "PPA-CF", "Diğer"]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    CTX = ssl.create_default_context()
DB = IMG = ""

KV = """
#:import dp kivy.metrics.dp
<Btn@Button>:
    background_normal: ''
    background_color: .17,.2,.25,1
    size_hint_y: None
    height: dp(46)
<Inp@TextInput>:
    background_color: .1,.12,.15,1
    foreground_color: .93,.95,.97,1
    hint_text_color: .45,.5,.56,1
    cursor_color: 1,.48,.24,1
    multiline: False
    size_hint_y: None
    height: dp(44)
<Lbl@Label>:
    color: .6,.65,.72,1
    size_hint_y: None
    height: dp(26)
    text_size: self.width, None
    halign: 'left'
<Row>:
    size_hint_y: None
    height: dp(92)
    padding: dp(6)
    spacing: dp(8)
    canvas.before:
        Color:
            rgba: .1,.12,.15,1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(10)]
    Image:
        source: root.img
        size_hint_x: None
        width: dp(80)
        fit_mode: 'cover'
    BoxLayout:
        orientation: 'vertical'
        Label:
            text: root.title
            bold: True
            text_size: self.size
            halign: 'left'
            valign: 'middle'
        Label:
            text: root.sub
            color: .6,.65,.72,1
            font_size: '13sp'
            text_size: self.size
            halign: 'left'
            valign: 'top'
<ListScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(8)
        spacing: dp(8)
        Label:
            id: cnt
            text: 'Filament Envanteri'
            bold: True
            size_hint_y: None
            height: dp(30)
        BoxLayout:
            size_hint_y: None
            height: dp(46)
            spacing: dp(6)
            Inp:
                id: q
                hint_text: 'Ara: marka, renk, not...'
                on_text: root.refresh()
            Btn:
                text: '+ Ekle'
                size_hint_x: None
                width: dp(90)
                background_color: 1,.48,.24,1
                color: .07,.08,.1,1
                on_release: root.edit(None)
        Btn:
            text: 'Listeyi gönder (CSV)'
            on_release: root.share()
        BoxLayout:
            size_hint_y: None
            height: dp(46)
            spacing: dp(6)
            Btn:
                text: 'Tam yedek al'
                on_release: root.backup()
            Btn:
                text: 'Yedekten yükle'
                on_release: root.restore_pick()
        ScrollView:
            GridLayout:
                id: box
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(6)
<EditScreen>:
    ScrollView:
        GridLayout:
            cols: 1
            size_hint_y: None
            height: self.minimum_height
            padding: dp(10)
            spacing: dp(6)
            Lbl:
                text: 'Marka *'
            Inp:
                id: mk
                hint_text: 'Porima, eSUN, Bambu Lab...'
            Lbl:
                text: 'Tür / Model'
            BoxLayout:
                size_hint_y: None
                height: dp(44)
                spacing: dp(6)
                Inp:
                    id: tr
                    hint_text: 'Bambu PLA Basic, eSUN PLA+...'
                Btn:
                    text: 'Listeden seç'
                    size_hint_x: None
                    width: dp(130)
                    height: dp(44)
                    on_release: root.pick_type()
            Lbl:
                text: 'Renk *'
            Inp:
                id: rk
                hint_text: 'Mat Siyah, Silk Gold...'
            Lbl:
                text: 'Çap / Ağırlık'
            Inp:
                id: by
                text: '1.75mm / 1kg'
            Lbl:
                text: 'Nozul sıcaklığı (C)'
            Inp:
                id: nz
                hint_text: '210-230'
            Lbl:
                text: 'Tabla sıcaklığı (C)'
            Inp:
                id: tb
                hint_text: '60'
            Lbl:
                text: 'Etiket fotoğrafı'
            Image:
                id: im1
                size_hint_y: None
                height: dp(180)
            BoxLayout:
                size_hint_y: None
                height: dp(46)
                spacing: dp(6)
                Btn:
                    text: 'Fotoğraf çek'
                    on_release: root.take_photo()
                Btn:
                    text: 'Galeriden seç'
                    on_release: root.pick('e')
            Lbl:
                text: 'Etiketten okunan metin'
            Inp:
                id: ocr
                multiline: True
                height: dp(100)
                hint_text: 'Etiket fotoğrafı eklenince otomatik dolar'
            Btn:
                text: 'Etiketi tekrar oku'
                on_release: root.reocr()
            Lbl:
                text: 'Örnek görsel (internet)'
            Image:
                id: im2
                size_hint_y: None
                height: dp(180)
            BoxLayout:
                size_hint_y: None
                height: dp(46)
                spacing: dp(6)
                Btn:
                    text: 'İnternetten bul'
                    on_release: root.find_sample()
                Btn:
                    text: 'Sonraki'
                    on_release: root.next_sample()
                Btn:
                    text: 'Galeri'
                    on_release: root.pick('o')
            BoxLayout:
                size_hint_y: None
                height: dp(46)
                spacing: dp(6)
                Btn:
                    text: 'Tarayıcıda ara'
                    on_release: root.open_browser()
                Btn:
                    text: 'Panodan adres al'
                    on_release: root.from_clipboard()
            Lbl:
                id: st
                height: max(dp(26), self.texture_size[1])
            Lbl:
                text: 'Notlar'
            Inp:
                id: nt
                multiline: True
                height: dp(120)
                hint_text: 'Gcode ayarları, kurutma, yapışma...'
            BoxLayout:
                size_hint_y: None
                height: dp(50)
                spacing: dp(6)
                Btn:
                    id: dl
                    text: 'Sil'
                    color: 1,.42,.42,1
                    on_release: root.delete()
                Btn:
                    text: 'Geri'
                    on_release: app.root.current = 'list'
                Btn:
                    text: 'Kaydet'
                    background_color: 1,.48,.24,1
                    color: .07,.08,.1,1
                    on_release: root.save()
"""


def sql(s, a=()):
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    try:
        cur = c.execute(s, a)
        rows = cur.fetchall()
        c.commit()
        return rows
    finally:
        c.close()


def msg(t, secs=4):
    lb = Label(text=t, halign="center", text_size=(Window.width * .75, None))
    p = Popup(title="", separator_height=0, content=lb, size_hint=(.88, .35))
    p.open()
    Clock.schedule_once(lambda *_: p.dismiss(), secs)


def shrink(src, dst, m=900):
    if platform == "android":
        try:
            return native.shrink_file(src, dst, m)
        except Exception:
            pass
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    im.thumbnail((m, m))
    im.save(dst, "JPEG", quality=82)


def _get(url, headers=None, timeout=12, limit=400000):
    h = {"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"}
    h.update(headers or {})
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout, context=CTX) as r:
        return r.read(limit).decode("utf-8", "ignore")


def ddg_images(qy):
    """DuckDuckGo görsel araması."""
    page = _get("https://duckduckgo.com/?" + urllib.parse.urlencode({"q": qy, "ia": "images", "iax": "images"}))
    m = re.search(r"vqd=[\"']?([\d-]+)|\"vqd\":\"([\d-]+)", page)
    if not m:
        raise RuntimeError("DuckDuckGo anahtarı alınamadı")
    url = "https://duckduckgo.com/i.js?" + urllib.parse.urlencode(
        {"l": "tr-tr", "o": "json", "q": qy, "vqd": m.group(1) or m.group(2), "f": ",,,,,", "p": "1", "ct": "AT"})
    data = json.loads(_get(url, {"Referer": "https://duckduckgo.com/", "Accept": "application/json"}))
    return [x["image"] for x in data.get("results", []) if x.get("image")]


def ddg_pages(qy):
    """DuckDuckGo web sonuçlarındaki (mağaza/marka) sayfaların og:image görselleri."""
    page = _get("https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": qy}))
    out, seen = [], set()
    for u in (urllib.parse.unquote(x) for x in re.findall(r"uddg=([^&\"']+)", page)):
        host = urllib.parse.urlparse(u).netloc
        if not u.startswith("http") or host in seen or any(b in host for b in (
                "facebook", "instagram", "youtube", "pinterest", "twitter", "x.com")):
            continue
        seen.add(host)
        try:
            html = _get(u, timeout=8, limit=250000)
        except Exception:
            continue
        for pat in (r"<meta[^>]+(?:property|name)=[\"']og:image[\"'][^>]*content=[\"']([^\"']+)",
                    r"<meta[^>]+content=[\"']([^\"']+)[\"'][^>]*(?:property|name)=[\"']og:image[\"']"):
            m = re.search(pat, html, re.I)
            if m:
                out.append(urllib.parse.urljoin(u, H.unescape(m.group(1))))
                break
        if len(out) >= 6 or len(seen) >= 10:
            break
    return out


def search_images(qy, n=8):
    errs, res = [], []
    for name, f in (("DDG görsel", ddg_images), ("DDG sayfa", ddg_pages)):
        try:
            res += [u for u in f(qy) if u not in res]
        except Exception as ex:
            errs.append("%s: %s: %s" % (name, type(ex).__name__, ex))
        if len(res) >= n:
            break
    if not res:
        raise RuntimeError("; ".join(errs) or "sonuç yok")
    return res[:n]


def download(url, dst):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/webp,image/jpeg,image/png,image/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=15, context=CTX) as r, open(dst, "wb") as f:
        f.write(r.read(8_000_000))


def share_text(t):
    if platform == "android":
        from jnius import autoclass
        Intent = autoclass("android.content.Intent")
        S = autoclass("java.lang.String")
        PA = autoclass("org.kivy.android.PythonActivity")
        i = Intent()
        i.setAction(Intent.ACTION_SEND)
        i.putExtra(Intent.EXTRA_TEXT, S(t))
        i.setType("text/plain")
        PA.mActivity.startActivity(Intent.createChooser(i, S("Listeyi gönder")))
    else:
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(t)
        msg("Panoya kopyalandı")


def make_backup_zip(dst):
    rows = [dict(r) for r in sql("SELECT * FROM f ORDER BY id")]
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for r in rows:
            r.pop("id", None)
            for k in ("etiket", "ornek"):
                p = r.get(k) or ""
                if p and os.path.exists(p):
                    z.write(p, "img/" + os.path.basename(p))
                    r[k] = "img/" + os.path.basename(p)
                else:
                    r[k] = ""
        z.writestr("data.json", json.dumps(rows, ensure_ascii=False))
    return len(rows)


def restore_backup(path):
    """Yedeği mevcut kayıtlara ekler; aynı kayıt varsa atlar."""
    n = 0
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        for r in json.loads(z.read("data.json").decode("utf-8")):
            if r.get("model"):
                r["tur"] = ("%s %s" % (r.get("tur") or "", r["model"])).strip()
            for k in ("etiket", "ornek"):
                rel = r.get(k) or ""
                if rel.startswith("img/") and rel in names:
                    dst = os.path.join(IMG, os.path.basename(rel))
                    if not os.path.exists(dst):
                        with open(dst, "wb") as f:
                            f.write(z.read(rel))
                    r[k] = dst
                else:
                    r[k] = ""
            if sql("SELECT id FROM f WHERE marka=? AND tur=? AND renk=? AND ifnull(notlar,'')=?",
                   (r.get("marka"), r.get("tur"), r.get("renk"), r.get("notlar") or "")):
                continue
            cols = [c for c in COLS if c in r]
            sql("INSERT INTO f (%s) VALUES (%s)" % (",".join(cols), ",".join("?" * len(cols))), [r[c] for c in cols])
            n += 1
    return n


class Row(ButtonBehavior, BoxLayout):
    img = StringProperty("")
    title = StringProperty("")
    sub = StringProperty("")
    rid = NumericProperty(0)


class ListScreen(Screen):
    def on_pre_enter(self, *a):
        self.refresh()

    def refresh(self):
        s = self.ids.q.text.lower().strip()
        box = self.ids.box
        box.clear_widgets()
        rows = sql("SELECT * FROM f ORDER BY id DESC")
        self.ids.cnt.text = "Filament Envanteri (%d)  v%s" % (len(rows), __version__)
        for r in rows:
            if s and s not in " ".join(str(r[k] or "") for k in ("marka", "tur", "renk", "notlar")).lower():
                continue
            w = Row(img=r["ornek"] or r["etiket"] or "", title="%s - %s" % (r["marka"], r["renk"]),
                    sub="%s  %s\nNozul %s / Tabla %s C" % (r["tur"] or "", r["boyut"] or "", r["nozul"] or "-", r["tabla"] or "-"),
                    rid=r["id"])
            w.bind(on_release=lambda x: self.edit(x.rid))
            box.add_widget(w)

    def edit(self, rid):
        e = self.manager.get_screen("edit")
        e.load(rid)
        self.manager.current = "edit"

    def share(self):
        rows = sql("SELECT * FROM f ORDER BY marka, renk")
        L = ["Marka;Tür / Model;Renk;Çap/Ağırlık;Nozul C;Tabla C;Notlar"]
        for r in rows:
            L.append(";".join(str(r[k] or "").replace(";", ",").replace("\n", " ") for k in
                              ("marka", "tur", "renk", "boyut", "nozul", "tabla", "notlar")))
        try:
            share_text("\n".join(L))
        except Exception as ex:
            msg("Paylaşım hatası: %s" % ex)


    def backup(self):
        tmp = os.path.join(App.get_running_app().user_data_dir, "yedek_tmp.zip")
        name = time.strftime("filament-yedek-%Y%m%d-%H%M.zip")
        try:
            n = make_backup_zip(tmp)
            if platform != "android":
                return msg("Yedek (%d kayıt): %s" % (n, tmp), 6)
            res = native.save_download(tmp, name, "application/zip")
            msg("%d kayıt yedeklendi:\n%s" % (n, res["label"]), 5)
            if res["uri"] is not None:
                native.share_uri(res["uri"], "application/zip")
        except Exception as ex:
            msg("Yedekleme hatası: %s: %s" % (type(ex).__name__, ex), 8)

    def restore_pick(self):
        if platform != "android":
            return msg("Bu özellik sadece telefonda çalışır.")
        try:
            native.pick_file(App.get_running_app().user_data_dir, dict(file=self._restore, error=self._err))
        except Exception as ex:
            msg("Dosya seçici açılamadı: %s" % ex, 8)

    @mainthread
    def _restore(self, path):
        try:
            n = restore_backup(path)
            msg("%d kayıt geri yüklendi." % n, 5)
            self.refresh()
        except Exception as ex:
            msg("Yedek okunamadı: %s: %s" % (type(ex).__name__, ex), 8)
        finally:
            try:
                os.remove(path)
            except Exception:
                pass

    @mainthread
    def _err(self, t):
        msg(t, 8)


class EditScreen(Screen):
    F = [("marka", "mk"), ("renk", "rk"), ("boyut", "by"), ("nozul", "nz"), ("tabla", "tb"), ("notlar", "nt")]
    rid = None
    e = o = ""
    cands = []
    ci = 0

    def load(self, rid):
        i = self.ids
        self.rid = rid
        r = sql("SELECT * FROM f WHERE id=?", (rid,))[0] if rid else None
        i.tr.text = (r["tur"] or "") if r else ""
        for k, w in self.F:
            i[w].text = (r[k] or "") if r else ("1.75mm / 1kg" if k == "boyut" else "")
        self.e = r["etiket"] or "" if r else ""
        self.o = r["ornek"] or "" if r else ""
        i.ocr.text = (r["ocr"] or "") if r else ""
        i.dl.disabled = not r
        self.cands, self.ci = [], 0
        self.show()

    def show(self):
        self.ids.im1.source = self.e
        self.ids.im2.source = self.o

    def save(self):
        i = self.ids
        if not i.mk.text.strip() or not i.rk.text.strip():
            return msg("En az Marka ve Renk gerekli.")
        v = [i.mk.text.strip(), i.tr.text, i.rk.text.strip(), i.by.text, i.nz.text, i.tb.text, self.e, self.o, i.nt.text, i.ocr.text]
        if self.rid:
            sql("UPDATE f SET marka=?,tur=?,renk=?,boyut=?,nozul=?,tabla=?,etiket=?,ornek=?,notlar=?,ocr=? WHERE id=?", v + [self.rid])
        else:
            sql("INSERT INTO f (marka,tur,renk,boyut,nozul,tabla,etiket,ornek,notlar,ocr) VALUES (?,?,?,?,?,?,?,?,?,?)", v)
        self.manager.current = "list"

    def delete(self):
        if self.rid:
            sql("DELETE FROM f WHERE id=?", (self.rid,))
        self.manager.current = "list"

    # --- fotoğraf ---
    def take_photo(self):
        self._start("cam", "e")

    def pick(self, which):
        self._start("pick", which)

    def _start(self, kind, which):
        if platform != "android":
            return msg("Bu özellik sadece telefonda çalışır.")
        try:
            cbs = dict(photo=lambda p: self._photo(which, p), text=self._text, error=self._err)
            f = native.start_camera if kind == "cam" else native.start_pick
            f(IMG, cbs, ocr=(which == "e"))
        except Exception as ex:
            msg("%s açılamadı: %s: %s" % ("Kamera" if kind == "cam" else "Galeri", type(ex).__name__, ex), 8)

    @mainthread
    def _photo(self, which, path):
        setattr(self, which, path)
        self.show()
        if which == "e":
            msg("Fotoğraf alındı, etiket okunuyor...", 2)

    @mainthread
    def _text(self, txt):
        self.ids.ocr.text = txt or ""
        d = native.parse_label(txt)
        i = self.ids
        got = []
        for k, w in (("marka", "mk"), ("renk", "rk"), ("nozul", "nz"), ("tabla", "tb")):
            if d.get(k) and not i[w].text.strip():
                i[w].text = d[k]
                got.append(d[k])
        if d.get("boyut") and i.by.text.strip() in ("", "1.75mm / 1kg"):
            i.by.text = d["boyut"]
            got.append(d["boyut"])
        if d.get("tur") and not i.tr.text.strip():
            i.tr.text = d["tur"]
            got.append(d["tur"])
        msg("Okunan: " + ", ".join(got) if got else
            "Metin okundu ama alanlar ayrıştırılamadı. 'Etiketten okunan metin'e bak, elle doldur.", 5)

    def reocr(self):
        if not self.e:
            return msg("Önce etiket fotoğrafı ekle.")
        if platform != "android":
            return msg("Bu özellik sadece telefonda çalışır.")
        try:
            native.recognize_file(self.e, self._text, self._err)
        except Exception as ex:
            msg("OCR hatası: %s: %s" % (type(ex).__name__, ex), 8)

    # --- Tür / Model listesi (Bambu Studio) ---
    def pick_type(self):
        box = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(6))
        q = TextInput(hint_text="Ara: pla, petg, bambu, sunlu...", multiline=False, size_hint_y=None, height=dp(44),
                      background_color=(.1, .12, .15, 1), foreground_color=(.93, .95, .97, 1),
                      hint_text_color=(.45, .5, .56, 1), cursor_color=(1, .48, .24, 1))
        grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(4))
        grid.bind(minimum_height=grid.setter("height"))
        sv = ScrollView()
        sv.add_widget(grid)
        pop = Popup(title="Tür / Model (Bambu Studio listesi)", content=box, size_hint=(.95, .9))

        def choose(name):
            self.ids.tr.text = name
            pop.dismiss()

        def fill(*_):
            grid.clear_widgets()
            words = native.fold(q.text).split()
            n = 0
            for name in native.NAMES:
                f = native.fold(name)
                if all(w in f for w in words):
                    b = Button(text=name, size_hint_y=None, height=dp(44), background_normal="",
                               background_color=(.17, .2, .25, 1))
                    b.bind(on_release=lambda x, nm=name: choose(nm))
                    grid.add_widget(b)
                    n += 1
                    if n >= 80:
                        break

        q.bind(text=fill)
        fill()
        box.add_widget(q)
        box.add_widget(sv)
        pop.open()

    # --- internetten örnek görsel ---
    qs, errs, plan = [], [], []

    @mainthread
    def status(self, t):
        self.ids.st.text = t

    def _queries(self):
        i = self.ids
        ocr = " ".join(i.ocr.text.split()[:5])
        b, t, c = (x.strip() for x in (i.mk.text, i.tr.text, i.rk.text))
        if not (b or t or ocr):
            return []
        b = b or ocr
        out = []
        for q in ("%s %s %s filament" % (b, t, c), "%s %s filament spool" % (b, t), "%s %s filament" % (b, c)):
            q = " ".join(q.split())
            if q not in out:
                out.append(q)
        return out

    def find_sample(self):
        self.qs = self._queries()
        if not self.qs:
            return msg("Önce marka/tür yaz ya da etiket fotoğrafı ekle.")
        self.errs = []
        self.plan = [("ddg", 0), ("google", 0), ("ddg", 1)] if platform == "android" else []
        self._step(0)

    def _step(self, n):
        if n >= len(self.plan):
            self.status("Tarayıcı motoru sonuç vermedi, hızlı yöntemler deneniyor...")
            return threading.Thread(target=self._fallback, daemon=True).start()
        kind, qi = self.plan[n]
        q = self.qs[min(qi, len(self.qs) - 1)]
        self.status("%d/%d  %s aranıyor: %s" % (n + 1, len(self.plan), "DuckDuckGo" if kind == "ddg" else "Google", q))
        try:
            native.web_images(q, kind, lambda urls: self._got_urls(urls, n), lambda e: self._fail(n, e))
        except Exception as ex:
            self._fail(n, "%s: %s" % (type(ex).__name__, ex))

    def _fail(self, n, e):
        self.errs.append("%s: %s" % (self.plan[n][0], e))
        Clock.schedule_once(lambda dt: self._step(n + 1), 0)

    def _got_urls(self, urls, n):
        self.cands, self.ci = urls, 0
        self.status("%d görsel adresi bulundu, indiriliyor..." % len(urls))
        threading.Thread(target=self._dl_loop, args=(n,), daemon=True).start()

    def _fallback(self):
        res = []
        for name, f in (("DDG görsel", ddg_images), ("DDG sayfa", ddg_pages)):
            for q in self.qs[:2]:
                try:
                    res += [u for u in f(q) if u not in res]
                except Exception as ex:
                    self.errs.append("%s: %s: %s" % (name, type(ex).__name__, ex))
                if res:
                    break
            if res:
                break
        if not res:
            return self.status("Bulunamadı. " + " | ".join(self.errs)[:400])
        self.cands, self.ci = res, 0
        self._dl_loop(None)

    def _dl_loop(self, n):
        """Adayları sırayla dener; indirilemeyeni/çözülemeyeni atlar."""
        last = ""
        for k in range(len(self.cands)):
            idx = (self.ci + k) % len(self.cands)
            tmp = os.path.join(IMG, "tmp_" + uuid.uuid4().hex)
            dst = os.path.join(IMG, "o" + uuid.uuid4().hex + ".jpg")
            try:
                download(self.cands[idx], tmp)
                shrink(tmp, dst)
            except Exception as ex:
                last = "%s: %s" % (type(ex).__name__, ex)
                continue
            finally:
                try:
                    os.remove(tmp)
                except Exception:
                    pass
            self.ci = idx
            return self._set(dst, "Görsel %d/%d. Beğenmediysen 'Sonraki'." % (idx + 1, len(self.cands)))
        self.errs.append("indirme: " + last)
        if n is None:
            self.status("Görseller indirilemedi. " + " | ".join(self.errs)[:400])
        else:
            Clock.schedule_once(lambda dt: self._step(n + 1), 0)

    @mainthread
    def _set(self, dst, note=""):
        self.o = dst
        self.show()
        if note:
            self.ids.st.text = note

    def next_sample(self):
        if not self.cands:
            return msg("Önce 'İnternetten bul'a bas.")
        self.ci = (self.ci + 1) % len(self.cands)
        self.status("Sonraki görsel indiriliyor...")
        threading.Thread(target=self._dl_loop, args=(None,), daemon=True).start()

    def open_browser(self):
        q = (self._queries() or [""])[0]
        try:
            native.open_url("https://www.google.com/search?tbm=isch&q=" + urllib.parse.quote(q))
        except Exception as ex:
            msg("Tarayıcı açılamadı: %s" % ex, 6)

    def from_clipboard(self):
        from kivy.core.clipboard import Clipboard
        u = (Clipboard.paste() or "").strip()
        if not u.startswith("http"):
            return msg("Panoda resim adresi yok. Tarayıcıda resme uzun bas > 'Resim adresini kopyala', sonra dön.", 7)
        self.cands, self.ci = [u], 0
        self.status("Adres indiriliyor...")
        threading.Thread(target=self._dl_loop, args=(None,), daemon=True).start()


class FilamentApp(App):
    def build(self):
        global DB, IMG
        d = self.user_data_dir
        IMG = os.path.join(d, "img")
        os.makedirs(IMG, exist_ok=True)
        DB = os.path.join(d, "filamentler.db")
        sql("""CREATE TABLE IF NOT EXISTS f (id INTEGER PRIMARY KEY AUTOINCREMENT, marka TEXT, tur TEXT,
               renk TEXT, boyut TEXT, nozul TEXT, tabla TEXT, etiket TEXT, ornek TEXT, notlar TEXT, ocr TEXT, model TEXT)""")
        have = [r["name"] for r in sql("PRAGMA table_info(f)")]
        for col in ("ocr", "model"):
            if col not in have:
                sql("ALTER TABLE f ADD COLUMN %s TEXT" % col)
        sql("UPDATE f SET tur=trim(ifnull(tur,'')||' '||model), model=NULL WHERE ifnull(model,'')<>''")
        Window.clearcolor = (.07, .08, .1, 1)
        Builder.load_string(KV)
        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(ListScreen(name="list"))
        sm.add_widget(EditScreen(name="edit"))
        Window.bind(on_keyboard=self.key)
        if platform == "android":
            try:
                native.init()
                if native.LOAD_ERR:
                    Clock.schedule_once(lambda *_: msg("ML Kit yüklenemedi: %s" % native.LOAD_ERR, 12), 1)
                from android.permissions import request_permissions
                request_permissions(["android.permission.WRITE_EXTERNAL_STORAGE"])
            except Exception as ex:
                Clock.schedule_once(lambda *_: msg("Başlatma hatası: %s" % ex, 8), 1)
        return sm

    def key(self, w, k, *a):
        if k == 27 and self.root.current == "edit":
            self.root.current = "list"
            return True


if __name__ == "__main__":
    FilamentApp().run()
