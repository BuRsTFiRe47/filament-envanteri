"""Filament Envanteri - Kivy + SQLite (Android APK).
Koyu tema / dark theme by default."""
import os, re, ssl, uuid, sqlite3, threading, html as H
import urllib.parse, urllib.request
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.utils import platform

TURLER = ["PLA", "PLA+", "PETG", "ABS", "ASA", "TPU", "PA", "PPA-CF", "Diğer"]
UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
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
                text: 'Tür'
            Spinner:
                id: tr
                text: 'PLA'
                size_hint_y: None
                height: dp(44)
                background_normal: ''
                background_color: .1,.12,.15,1
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


def msg(t):
    p = Popup(title="", separator_height=0, content=Label(text=t), size_hint=(.85, .25))
    p.open()
    Clock.schedule_once(lambda *_: p.dismiss(), 2.5)


def shrink(src, dst, m=900):
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    im.thumbnail((m, m))
    im.save(dst, "JPEG", quality=82)


def search_images(qy, n=8):
    """Bing görsel sayfasından sonuç adreslerini çeker (sunucu gerekmez)."""
    url = "https://www.bing.com/images/search?q=" + urllib.parse.quote(qy)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    page = urllib.request.urlopen(req, timeout=15, context=CTX).read().decode("utf-8", "ignore")
    return [H.unescape(u) for u in re.findall(r"murl&quot;:&quot;(.*?)&quot;", page)][:n]


def download(url, dst):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
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
        self.ids.cnt.text = "Filament Envanteri (%d)" % len(rows)
        for r in rows:
            if s and s not in " ".join(str(r[k] or "") for k in ("marka", "tur", "renk", "notlar")).lower():
                continue
            w = Row(img=r["etiket"] or r["ornek"] or "", title="%s - %s" % (r["marka"], r["renk"]),
                    sub="%s  %s\nNozul %s / Tabla %s C" % (r["tur"], r["boyut"] or "", r["nozul"] or "-", r["tabla"] or "-"),
                    rid=r["id"])
            w.bind(on_release=lambda x: self.edit(x.rid))
            box.add_widget(w)

    def edit(self, rid):
        e = self.manager.get_screen("edit")
        e.load(rid)
        self.manager.current = "edit"

    def share(self):
        rows = sql("SELECT * FROM f ORDER BY marka, renk")
        L = ["Marka;Tür;Renk;Çap/Ağırlık;Nozul C;Tabla C;Notlar"]
        for r in rows:
            L.append(";".join(str(r[k] or "").replace(";", ",").replace("\n", " ") for k in
                              ("marka", "tur", "renk", "boyut", "nozul", "tabla", "notlar")))
        try:
            share_text("\n".join(L))
        except Exception as ex:
            msg("Paylaşım hatası: %s" % ex)


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
        i.tr.values = TURLER
        i.tr.text = r["tur"] if r else "PLA"
        for k, w in self.F:
            i[w].text = (r[k] or "") if r else ("1.75mm / 1kg" if k == "boyut" else "")
        self.e = r["etiket"] or "" if r else ""
        self.o = r["ornek"] or "" if r else ""
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
        v = [i.mk.text.strip(), i.tr.text, i.rk.text.strip(), i.by.text, i.nz.text, i.tb.text, self.e, self.o, i.nt.text]
        if self.rid:
            sql("UPDATE f SET marka=?,tur=?,renk=?,boyut=?,nozul=?,tabla=?,etiket=?,ornek=?,notlar=? WHERE id=?", v + [self.rid])
        else:
            sql("INSERT INTO f (marka,tur,renk,boyut,nozul,tabla,etiket,ornek,notlar) VALUES (?,?,?,?,?,?,?,?,?)", v)
        self.manager.current = "list"

    def delete(self):
        if self.rid:
            sql("DELETE FROM f WHERE id=?", (self.rid,))
        self.manager.current = "list"

    # --- fotoğraf ---
    def take_photo(self):
        dst = os.path.join(IMG, "cam_" + uuid.uuid4().hex + ".jpg")
        try:
            from plyer import camera
            camera.take_picture(filename=dst, on_complete=lambda p: self._got("e", p))
        except Exception as ex:
            msg("Kamera açılamadı (%s). Galeriden seç." % ex)

    def pick(self, which):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=lambda s: s and self._got(which, s[0]),
                                  filters=[["Resim", "*.jpg", "*.jpeg", "*.png", "*.webp"]])
        except Exception as ex:
            msg("Galeri açılamadı: %s" % ex)

    @mainthread
    def _got(self, which, path):
        if not path or not os.path.exists(path):
            return
        dst = os.path.join(IMG, which + uuid.uuid4().hex + ".jpg")
        try:
            shrink(path, dst)
        except Exception as ex:
            return msg("Görsel okunamadı: %s" % ex)
        setattr(self, which, dst)
        self.show()

    # --- internetten örnek görsel ---
    def find_sample(self):
        i = self.ids
        if not i.mk.text.strip():
            return msg("Önce marka yaz.")
        msg("Aranıyor...")
        qy = ("%s %s %s filament" % (i.mk.text, i.tr.text, i.rk.text)).strip()
        threading.Thread(target=self._search, args=(qy,), daemon=True).start()

    def _search(self, qy):
        try:
            c = search_images(qy)
        except Exception as ex:
            return self._err("Arama hatası: %s" % ex)
        self._cands(c)

    @mainthread
    def _cands(self, c):
        self.cands, self.ci = c, 0
        if not c:
            return msg("Sonuç bulunamadı.")
        self._fetch()

    def next_sample(self):
        if not self.cands:
            return msg("Önce 'İnternetten bul'a bas.")
        self.ci = (self.ci + 1) % len(self.cands)
        self._fetch()

    def _fetch(self):
        threading.Thread(target=self._dl, args=(self.cands[self.ci],), daemon=True).start()

    def _dl(self, url):
        tmp = os.path.join(IMG, "tmp_" + uuid.uuid4().hex)
        dst = os.path.join(IMG, "o" + uuid.uuid4().hex + ".jpg")
        try:
            download(url, tmp)
            shrink(tmp, dst)
            os.remove(tmp)
        except Exception:
            return self._err("Bu görsel indirilemedi, 'Sonraki'ne bas.")
        self._set(dst)

    @mainthread
    def _set(self, dst):
        self.o = dst
        self.show()

    @mainthread
    def _err(self, t):
        msg(t)


class FilamentApp(App):
    def build(self):
        global DB, IMG
        d = self.user_data_dir
        IMG = os.path.join(d, "img")
        os.makedirs(IMG, exist_ok=True)
        DB = os.path.join(d, "filamentler.db")
        sql("""CREATE TABLE IF NOT EXISTS f (id INTEGER PRIMARY KEY AUTOINCREMENT, marka TEXT, tur TEXT,
               renk TEXT, boyut TEXT, nozul TEXT, tabla TEXT, etiket TEXT, ornek TEXT, notlar TEXT)""")
        Window.clearcolor = (.07, .08, .1, 1)
        Builder.load_string(KV)
        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(ListScreen(name="list"))
        sm.add_widget(EditScreen(name="edit"))
        Window.bind(on_keyboard=self.key)
        if platform == "android":
            try:
                from android.permissions import request_permissions
                request_permissions(["android.permission.CAMERA", "android.permission.READ_EXTERNAL_STORAGE",
                                     "android.permission.WRITE_EXTERNAL_STORAGE", "android.permission.READ_MEDIA_IMAGES"])
            except Exception:
                pass
        return sm

    def key(self, w, k, *a):
        if k == 27 and self.root.current == "edit":
            self.root.current = "list"
            return True


if __name__ == "__main__":
    FilamentApp().run()
