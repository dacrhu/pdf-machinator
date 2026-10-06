"""PyMuPDF-burkoló. Csak annotációkat ad hozzá, mentéskor inkrementálisan ír,
így az eredeti oldaltartalom (tördelés) bájtra azonos marad."""
import os
import re
import shutil
import tempfile

import pymupdf

from .i18n import tr


class SaveError(Exception):
    pass


class Document:
    def __init__(self, path):
        self.path = path
        # Munkapéldányon dolgozunk: az inkrementális mentés csak a nyitott fájlra
        # megy, így az eredeti érintetlen marad a mentésig / Mentés másként-ig.
        fd, self._work = tempfile.mkstemp(suffix=".pdf", prefix="pdfmachinator-")
        os.close(fd)
        shutil.copyfile(path, self._work)
        self.doc = pymupdf.open(self._work)
        if self.doc.needs_pass:
            self.doc.close()
            raise ValueError(tr("A PDF jelszóval védett."))
        self.dirty = False
        self._pages = {}
        self._undo = []  # (oldalszám, xref) a hozzáadott annotációkhoz

    @property
    def page_count(self):
        return len(self.doc)

    def page(self, n):
        # az annotáció csak addig érvényes, amíg az oldal objektuma él -> tároljuk
        if n not in self._pages:
            self._pages[n] = self.doc[n]
        return self._pages[n]

    def _track(self, pno, annot):
        self._undo.append((pno, annot.xref))
        self.dirty = True
        return annot

    def _snap(self, page, point):
        """A kattintáshoz legközelebbi sor és betűhatár: (x, alapvonal-y, méret, szín)."""
        best = None
        for blk in page.get_text("rawdict")["blocks"]:
            for line in blk.get("lines", []):
                for span in line["spans"]:
                    chars = span["chars"]
                    if not chars:
                        continue
                    bb = pymupdf.Rect(span["bbox"])
                    dy = 0 if bb.y0 <= point.y <= bb.y1 else min(abs(point.y - bb.y0), abs(point.y - bb.y1))
                    dx = 0 if bb.x0 <= point.x <= bb.x1 else min(abs(point.x - bb.x0), abs(point.x - bb.x1))
                    dist = dy * 3 + dx
                    if best is None or dist < best[0]:
                        best = (dist, span)
        if best is None or best[0] > 40:
            return None
        span = best[1]
        edges = [c["bbox"][0] for c in span["chars"]] + [span["chars"][-1]["bbox"][2]]
        x = min(edges, key=lambda e: abs(e - point.x))
        c = span["color"]
        return x, span["origin"][1], span["size"], ((c >> 16 & 255) / 255, (c >> 8 & 255) / 255, (c & 255) / 255)

    def add_text(self, pno, point, text, color, bg=None, bg_alpha=1.0):
        """Beírás a kattintott betűhatárra, a sor méretében és alapvonalán.
        A többi szöveg nem mozdul (tördelés érintetlen); a beírt szöveg fölé kerül."""
        page = self.page(pno)
        snap = self._snap(page, point)
        if snap:
            x, base, size, _ = snap
        else:
            x, base, size = point.x, point.y + 11, 14
        font = pymupdf.Font("helv")
        w = font.text_length(text, size)
        top = base - size * 0.79
        rect = pymupdf.Rect(x, top, x + w + size * 0.2, top + size * 1.4)
        a = page.add_freetext_annot(
            rect, text, fontsize=size, fontname="helv",
            text_color=color, fill_color=bg, border_width=0,
        )
        a.update()
        self._apply_bg_alpha(a, bg_alpha if bg else 1.0)
        return self._track(pno, a)

    def add_note(self, pno, point, text, color):
        a = self.page(pno).add_text_annot(point, text, icon="Note")
        a.set_colors(stroke=color)
        a.update()
        return self._track(pno, a)

    def add_highlight(self, pno, rect, color, alpha=1.0):
        page = self.page(pno)
        quads = [pymupdf.Rect(w[:4]) for w in page.get_text("words") if pymupdf.Rect(w[:4]).intersects(rect)]
        if not quads:
            return None
        a = page.add_highlight_annot(quads=quads)
        a.set_colors(stroke=color)
        a.set_opacity(alpha)
        a.update()
        return self._track(pno, a)

    def add_circle(self, pno, rect, color, width=2):
        a = self.page(pno).add_circle_annot(rect)
        a.set_colors(stroke=color)
        a.set_border(width=width)
        a.update()
        return self._track(pno, a)

    def annot_at(self, pno, point):
        for a in reversed(list(self.page(pno).annots())):
            if a.rect.contains(point):
                return a
        return None

    def set_note_text(self, annot, text):
        # Szerző + Popup is kell, mert sok olvasó csak ezekkel jeleníti meg a megjegyzést
        annot.set_info(content=text, title=tr("Korrektor"), subject=tr("Megjegyzés"))
        if annot.type[1] != "Text" and annot.popup_xref == 0:
            r = annot.rect
            annot.set_popup(pymupdf.Rect(r.x1, r.y0, r.x1 + 180, r.y0 + 90))
        annot.update()
        self.dirty = True

    def _apply_bg_alpha(self, annot, alpha):
        """A háttér áttetszősége úgy, hogy a betűk teljesen fedők maradnak:
        az AP-folyam kitöltő műveletét külön ExtGState-tel (ca) vesszük körbe."""
        doc, xref = self.doc, annot.xref
        doc.xref_set_key(xref, "MahiBgAlpha", f"{alpha:.3f}")
        if alpha >= 0.999:
            return
        ap = doc.xref_get_key(xref, "AP/N")[1]
        n = int(ap.split()[0])
        stream = doc.xref_stream(n).decode("latin1")
        stream, k = re.subn(r"(\d[^\n]*\brg\n)", "q /MahiBg gs\n\\1", stream, count=1)
        if not k:
            return
        stream = stream.replace(" re\nf\n", " re\nf\nQ\n", 1)
        doc.update_stream(n, stream.encode("latin1"))
        doc.xref_set_key(n, "Resources/ExtGState", f"<</MahiBg <</ca {alpha:.3f}>>>>")

    def text_bg_alpha(self, annot):
        v = self.doc.xref_get_key(annot.xref, "MahiBgAlpha")[1]
        try:
            return float(v)
        except ValueError:
            return 1.0

    def set_text_bg(self, annot, bg, alpha=1.0):
        """Beírt szöveg háttere: szín + áttetszőség, vagy None = átlátszó."""
        da = self.doc.xref_get_key(annot.xref, "DA")[1].split()
        try:
            color = tuple(float(v) for v in da[:3]) if da[3] == "rg" else (0, 0, 0)
        except (IndexError, ValueError):
            color = (0, 0, 0)
        if bg is None:
            self.doc.xref_set_key(annot.xref, "C", "[]")
            annot.update(text_color=color)
        else:
            annot.update(fill_color=bg, text_color=color)
            self._apply_bg_alpha(annot, alpha)
        self.dirty = True

    def delete(self, pno, annot):
        xref = annot.xref
        self.page(pno).delete_annot(annot)
        self._undo = [u for u in self._undo if u[1] != xref]
        self.dirty = True

    def undo(self):
        while self._undo:
            pno, xref = self._undo.pop()
            for a in self.page(pno).annots():
                if a.xref == xref:
                    self.page(pno).delete_annot(a)
                    self.dirty = True
                    return True
        return False

    def save(self, path=None):
        """Inkrementális mentés a munkapéldányra, majd másolás a célra
        (alapból az eredeti fájl; Mentés másként esetén új útvonal)."""
        target = path or self.path
        try:
            if self.dirty:
                self.doc.saveIncr()
            shutil.copyfile(self._work, target)
        except Exception as e:  # nincs csendes teljes újraírás: az tördelést érinthet
            raise SaveError(tr("Mentés nem lehetséges: {e}", e=e)) from e
        self.path = target
        self.dirty = False
        self._undo.clear()

    def close(self):
        self.doc.close()
        try:
            os.remove(self._work)
        except OSError:
            pass

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
