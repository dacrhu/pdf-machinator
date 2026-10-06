import os
import sys

from PySide6.QtCore import QEvent, QProcess, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QColor, QKeySequence
from PySide6.QtWidgets import (
    QColorDialog, QDialog, QDialogButtonBox, QFileDialog, QInputDialog, QLabel,
    QMainWindow, QMessageBox, QPlainTextEdit, QSpinBox, QToolBar, QToolButton,
    QVBoxLayout, QWidget,
)

from . import icons
from .document import Document, SaveError
from . import LICENSE, REPO_URL, __version__, i18n
from .i18n import tr
from .viewer import Viewer

TOOLS = {  # név: (felirat, alapszín, húzásos?, alakzat, gyorsgomb, súgó)
    "select": (tr("Kijelölés"), None, False, "rect", "V",
               tr("Annotáció megnyitása, szerkesztése, törlése: kattints rá")),
    "text": (tr("Beleírás"), (0.85, 0, 0), False, "rect", "T",
             tr("Kattints a betűk közé, ahová írni szeretnél")),
    "note": (tr("Megjegyzés"), (1, 0.8, 0), False, "rect", "N",
             tr("Kattints oda, ahová megjegyzést (post-it) szeretnél tenni")),
    "highlight": (tr("Filc"), (1, 1, 0), True, "rect", "H",
                  tr("Húzd végig a kijelölendő szövegen")),
    "circle": (tr("Karika"), (1, 0, 0), True, "ellipse", "C",
               tr("Húzással karikázd be; Shift: szabályos kör")),
}


def to_rgb(c):
    return (c.redF(), c.greenF(), c.blueF())


def to_qcolor(t):
    return QColor.fromRgbF(*t)


PRESETS = ["#ffff00", "#7CFC00", "#00e5ff", "#ff69b4", "#ffa500", "#ff0000",
           "#ffffff", "#ffd966", "#b4a7d6", "#9fc5e8", "#b6d7a8", "#ea9999", "#000000", "#0000ff", "#808080", "#00aa00"]


def choose_color(parent, title, initial, alpha=None):
    """Teljes színválasztó (HSV/RGB/HTML, pipetta) kedvenc színekkel.
    alpha=None: nincs áttetszőség-csúszka; különben (rgb, alpha) a visszatérés."""
    dlg = QColorDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
    for i, h in enumerate(PRESETS):
        dlg.setCustomColor(i, QColor(h))
        dlg.setStandardColor(i, QColor(h))
    c = QColor(*[int(v * 255) for v in initial])
    if alpha is not None:
        dlg.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, True)
        c.setAlphaF(alpha)
    dlg.setCurrentColor(c)
    if not dlg.exec():
        return None
    c = dlg.currentColor()
    return (to_rgb(c), c.alphaF()) if alpha is not None else to_rgb(c)


class NoteDialog(QDialog):
    def __init__(self, parent, text="", deletable=False):
        super().__init__(parent)
        self.setWindowTitle(tr("Megjegyzés"))
        self.deleted = False
        self.edit = QPlainTextEdit(text)
        lay = QVBoxLayout(self)
        lay.addWidget(self.edit)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        if deletable:
            d = bb.addButton(tr("Törlés"), QDialogButtonBox.ButtonRole.DestructiveRole)
            d.clicked.connect(self._delete)
        lay.addWidget(bb)

    def _delete(self):
        self.deleted = True
        self.accept()


def icons_size():
    from PySide6.QtCore import QSize
    return QSize(22, 22)


STYLE = """
QToolBar { spacing: 3px; padding: 5px 8px; border: 0; border-bottom: 1px solid rgba(128,128,128,70); }
QToolBar::separator { width: 1px; margin: 5px 8px; background: rgba(128,128,128,90); }
QToolButton { border: 1px solid transparent; border-radius: 7px; padding: 6px; }
QToolButton:hover { background: rgba(128,128,128,45); }
QToolButton:pressed { background: rgba(128,128,128,80); }
QToolButton:checked { background: rgba(60,130,255,55); border: 1px solid rgba(60,130,255,150); }
QToolButton:disabled { background: transparent; }
QSpinBox { border: 1px solid rgba(128,128,128,110); border-radius: 6px; padding: 3px 4px; }
QStatusBar { border-top: 1px solid rgba(128,128,128,70); }
"""


class MainWindow(QMainWindow):
    def __init__(self, path=None):
        super().__init__()
        self.setWindowTitle("PDF Machinator")
        self.resize(1000, 900)
        self.doc = None
        self.pno = 0
        self.tool = "select"
        self.colors = {k: v[1] for k, v in TOOLS.items()}
        self.text_bg = None
        self.text_bg_alpha = 1.0
        self.hl_alpha = 1.0
        self.viewer = Viewer()
        self.setCentralWidget(self.viewer)
        self.viewer.clicked.connect(self.on_click)
        self.viewer.drag_done.connect(self.on_drag)
        self.viewer.zoom_changed.connect(self._zoom_changed)
        self.color_tool = "text"  # a Szín gomb melyik eszközé (Kijelölésnél: az utolsó rajzoló eszközé)
        self._icon_cache = {}
        self._build_actions()
        self._build_menus()
        self._build_toolbar()
        self.statusBar().showMessage(TOOLS["select"][5])
        self.setAcceptDrops(True)
        self.refresh_icons()
        self.update_enabled()
        self.setStyleSheet(STYLE)
        if path:
            self.open_path(path)
        else:
            QTimer.singleShot(0, self.open_dialog)

    # ---- felépítés
    def _mk(self, text, slot, shortcut=None, icon=None, tip=None, checkable=False):
        a = QAction(text, self)
        a.setCheckable(checkable)
        a.triggered.connect(slot)
        if shortcut:
            a.setShortcut(shortcut)
        if icon:
            self._icons.append((a, icon))
        tip = tip or text.rstrip("…")
        a.setToolTip(f"{tip} ({a.shortcut().toString(QKeySequence.SequenceFormat.NativeText)})" if shortcut else tip)
        a.setIconVisibleInMenu(False)
        return a

    def _build_actions(self):
        self._icons = []
        K = QKeySequence.StandardKey
        self.a_open = self._mk(tr("Megnyitás…"), self.open_dialog, K.Open, "open", tr("PDF megnyitása"))
        self.a_save = self._mk(tr("Mentés"), self.save, K.Save, "save")
        self.a_save_as = self._mk(tr("Mentés másként…"), self.save_as, K.SaveAs)
        self.a_quit = self._mk(tr("Kilépés"), self.close, K.Quit)
        self.a_undo = self._mk(tr("Visszavonás"), self.undo, K.Undo, "undo")
        self.a_prev = self._mk(tr("Előző oldal"), lambda: self.go(-1), Qt.Key.Key_PageUp, "prev")
        self.a_next = self._mk(tr("Következő oldal"), lambda: self.go(1), Qt.Key.Key_PageDown, "next")
        self.a_zin = self._mk(tr("Nagyítás"), lambda: self.viewer.set_zoom(self.viewer.zoom * 1.2), K.ZoomIn, "zoom_in")
        self.a_zout = self._mk(tr("Kicsinyítés"), lambda: self.viewer.set_zoom(self.viewer.zoom / 1.2), K.ZoomOut, "zoom_out")
        self.a_fit = self._mk(tr("Szélességhez igazítás"), self.viewer.fit_width, "Ctrl+0", "fit")
        self.a_color = self._mk(tr("Szín…"), self.pick_color, tip=tr("Az eszköz színe"))
        self.a_bg = self._mk(tr("Háttér…"), self.pick_bg, tip=tr("Beírt szöveg háttere és áttetszősége"))
        self.a_nobg = self._mk(tr("Nincs háttér"), self.clear_bg)
        self.a_about = self._mk(tr("Névjegy"), self.about)
        self.tool_actions = {}
        grp = QActionGroup(self)
        for key, (label, _c, _d, _s, sc, hint) in TOOLS.items():
            a = self._mk(label, lambda _=False, k=key: self.set_tool(k), sc, key, hint, checkable=True)
            a.setToolTip(f"{label} ({sc}) – {hint}")
            grp.addAction(a)
            self.tool_actions[key] = a
        self.tool_actions["select"].setChecked(True)

    def _build_menus(self):
        mb = self.menuBar()
        m = mb.addMenu(tr("&Fájl"))
        m.addActions([self.a_open, self.a_save, self.a_save_as])
        m.addSeparator()
        m.addAction(self.a_quit)
        m = mb.addMenu(tr("&Szerkesztés"))
        m.addAction(self.a_undo)
        m = mb.addMenu(tr("&Eszközök"))
        m.addActions(list(self.tool_actions.values()))
        m.addSeparator()
        m.addActions([self.a_color, self.a_bg, self.a_nobg])
        m = mb.addMenu(tr("&Nézet"))
        m.addActions([self.a_zin, self.a_zout, self.a_fit])
        m.addSeparator()
        m.addActions([self.a_prev, self.a_next])
        m = mb.addMenu(tr("&Súgó"))
        m.addAction(self.a_about)
        # A menücím szándékosan minden nyelven angol, hogy rosszul beállított OS mellett is megtalálható legyen
        lm = mb.addMenu("&Language")
        grp = QActionGroup(self)
        self.lang_actions = {}
        for code, label in [("", tr("Automatikus (rendszernyelv)"))] + list(i18n.NAMES.items()):
            a = QAction(label, self, checkable=True)
            a.setChecked(code == i18n.saved())
            a.triggered.connect(lambda _=False, c=code: self.change_language(c))
            grp.addAction(a)
            lm.addAction(a)
            self.lang_actions[code] = a

    def _build_toolbar(self):
        tb = self.tb = QToolBar(tr("Eszközök"))
        tb.setMovable(False)
        tb.setIconSize(icons_size())
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.addToolBar(tb)
        tb.addActions([self.a_open, self.a_save, self.a_undo])
        tb.addSeparator()
        tb.addActions(list(self.tool_actions.values()))
        tb.addSeparator()
        # színminta-gombok (az ikonjuk a pillanatnyi színt mutatja)
        self.color_btn = QToolButton()
        self.color_btn.setDefaultAction(self.a_color)
        tb.addWidget(self.color_btn)
        self.bg_btn = QToolButton()
        self.bg_btn.setDefaultAction(self.a_bg)
        tb.addWidget(self.bg_btn)
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().horizontalPolicy().Expanding, spacer.sizePolicy().verticalPolicy())
        tb.addWidget(spacer)
        tb.addAction(self.a_prev)
        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.page_spin.setKeyboardTracking(False)
        self.page_spin.setFixedWidth(96)
        self.page_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_spin.setToolTip(tr("Ugrás az oldalra"))
        self.page_spin.valueChanged.connect(self._spin_page)
        tb.addWidget(self.page_spin)
        tb.addAction(self.a_next)
        tb.addSeparator()
        tb.addActions([self.a_zout])
        self.zoom_label = QLabel("150%")
        self.zoom_label.setFixedWidth(46)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tb.addWidget(self.zoom_label)
        tb.addActions([self.a_zin, self.a_fit])

    def _spin_page(self, v):
        if self.doc and v - 1 != self.pno:
            self.pno = v - 1
            self.show_page()

    def _zoom_changed(self, z):
        self.zoom_label.setText(f"{round(z * 100)}%")

    def refresh_icons(self):
        """Ikonok újrafestése a pillanatnyi témához (világos/sötét) és színekhez."""
        pal = self.palette()
        text = pal.windowText().color()
        hi = QColor("#7ab4ff") if text.lightness() > 128 else QColor("#1f6feb")
        dis = pal.color(pal.ColorGroup.Disabled, pal.ColorRole.WindowText)
        for act, name in self._icons:
            act.setIcon(icons.make_icon(name, text, hi, dis))
        k = self.color_tool
        self.a_color.setIcon(icons.swatch_icon(to_qcolor(self.colors[k]), text,
                                               alpha=self.hl_alpha if k == "highlight" else 1.0))
        self.a_color.setToolTip(tr("Szín: {tool} – kattints a módosításhoz", tool=TOOLS[k][0]))
        self.a_bg.setIcon(icons.swatch_icon(to_qcolor(self.text_bg) if self.text_bg else None, text,
                                            alpha=self.text_bg_alpha))
        self.a_bg.setToolTip(tr("Beírt szöveg háttere: nincs – kattints a módosításhoz") if not self.text_bg else
                             tr("Beírt szöveg háttere: {pct}% fedés – kattints a módosításhoz", pct=round(self.text_bg_alpha * 100)))
        self.a_bg.setEnabled(self.tool in ("text", "select"))

    def changeEvent(self, e):
        if e.type() == QEvent.Type.PaletteChange and hasattr(self, "a_color"):
            self.refresh_icons()
        super().changeEvent(e)

    def update_enabled(self):
        has = self.doc is not None
        for a in (self.a_save, self.a_save_as, self.a_undo, self.a_prev, self.a_next, self.a_zin,
                  self.a_zout, self.a_fit, self.a_color, self.a_bg, self.a_nobg, *self.tool_actions.values()):
            a.setEnabled(has)
        self.page_spin.setEnabled(has)
        if has:
            self.refresh_icons()

    def clear_bg(self):
        self.text_bg = None
        self.refresh_icons()

    def change_language(self, code):
        if code == i18n.saved():
            return
        if not self.confirm_discard():
            self.lang_actions[i18n.saved()].setChecked(True)  # mégse: marad a régi jelölés
            return
        i18n.save(code)
        QMessageBox.information(self, "PDF Machinator", tr("A nyelv váltásához a program újraindul."))
        args = [] if getattr(sys, "frozen", False) else ["-m", "pdfmachinator"]
        if self.doc:
            args.append(self.doc.path)
        QProcess.startDetached(sys.executable, args)
        if self.doc:
            self.doc.close()
            self.doc = None
        self.close()

    def about(self):
        QMessageBox.about(
            self, tr("Névjegy"),
            f"<h3>PDF Machinator</h3>"
            f"<p>{tr('Korrektori PDF-jegyzetelő.')}<br>"
            f"{tr('A mentés az eredeti oldaltartalmat nem módosítja, a jegyzetek hozzáfűzve kerülnek a fájlba.')}</p>"
            f"<p>{tr('Verzió')}: {__version__}<br>{tr('Licenc')}: {LICENSE}<br>"
            f"{tr('Forráskód')}: <a href=\"{REPO_URL}\">{REPO_URL}</a></p>")

    # ---- fájl
    def open_dialog(self):
        if not self.confirm_discard():
            return
        p, _ = QFileDialog.getOpenFileName(self, tr("PDF megnyitása"), "", "PDF (*.pdf)")
        if p:
            self.open_path(p)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        if urls and urls[0].toLocalFile().lower().endswith(".pdf") and self.confirm_discard():
            self.open_path(urls[0].toLocalFile())

    def open_path(self, p):
        try:
            d = Document(p)
        except Exception as e:
            QMessageBox.critical(self, tr("Hiba"), tr("Nem nyitható meg: {e}", e=e))
            return
        if self.doc:
            self.doc.close()
        self.doc, self.pno = d, 0
        self.show_page()
        self.viewer.fit_width()
        self.update_enabled()

    def save(self):
        if not self.doc:
            return
        try:
            self.doc.save()
        except SaveError as e:
            QMessageBox.critical(self, tr("Mentési hiba"), str(e))
            return
        self.update_title()

    def save_as(self):
        if not self.doc:
            return
        p, _ = QFileDialog.getSaveFileName(self, tr("Mentés másként…").rstrip("…"), self.doc.path, "PDF (*.pdf)")
        if not p:
            return
        if not p.lower().endswith(".pdf"):
            p += ".pdf"
        try:
            self.doc.save(p)
        except SaveError as e:
            QMessageBox.critical(self, tr("Mentési hiba"), str(e))
            return
        self.update_title()

    def undo(self):
        if self.doc and self.doc.undo():
            self.show_page()

    def confirm_discard(self):
        if not self.doc or not self.doc.dirty:
            return True
        r = QMessageBox.question(self, tr("Mentetlen változtatások"), tr("Mentsem a változtatásokat?"),
                                 QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        if r == QMessageBox.StandardButton.Save:
            self.save()
            return not self.doc.dirty
        return r == QMessageBox.StandardButton.Discard

    def closeEvent(self, e):
        e.accept() if self.confirm_discard() else e.ignore()

    # ---- nézet
    def show_page(self):
        self.viewer.show_page(self.doc.page(self.pno))
        self.page_spin.blockSignals(True)
        self.page_spin.setMaximum(self.doc.page_count)
        self.page_spin.setSuffix(f" / {self.doc.page_count}")
        self.page_spin.setValue(self.pno + 1)
        self.page_spin.blockSignals(False)
        self.update_title()

    def update_title(self):
        mark = "*" if self.doc.dirty else ""
        self.setWindowTitle(f"{mark}{os.path.basename(self.doc.path)} – PDF Machinator")

    def go(self, d):
        if self.doc and 0 <= self.pno + d < self.doc.page_count:
            self.pno += d
            self.show_page()

    # ---- eszközök
    def set_tool(self, k):
        self.tool = k
        self.tool_actions[k].setChecked(True)
        if k != "select":
            self.color_tool = k
        self.viewer.wants_drag = TOOLS[k][2]
        self.viewer.drag_shape = TOOLS[k][3]
        self.viewer.setCursor(Qt.CursorShape.ArrowCursor if k == "select" else Qt.CursorShape.CrossCursor)
        self.statusBar().showMessage(f"{TOOLS[k][0]}: {TOOLS[k][5]}")
        self.refresh_icons()

    def pick_color(self):
        k = self.color_tool
        r = choose_color(self, tr("Szín – {tool}", tool=TOOLS[k][0]), self.colors[k], alpha=self.hl_alpha if k == "highlight" else None)
        if r is None:
            return
        if k == "highlight":
            self.colors[k], self.hl_alpha = r
        else:
            self.colors[k] = r
        self.refresh_icons()

    def pick_bg(self):
        r = choose_color(self, tr("Háttérszín és áttetszőség"), self.text_bg or (1, 1, 0), alpha=self.text_bg_alpha)
        if r is not None:
            self.text_bg, self.text_bg_alpha = r
            self.refresh_icons()

    def refresh(self):
        self.viewer.render_page()
        self.update_title()

    def on_click(self, pt):
        if not self.doc:
            return
        if self.tool == "text":
            text, ok = QInputDialog.getText(self, tr("Beleírás"), tr("Szöveg:"))
            if ok and text:
                self.doc.add_text(self.pno, pt, text, self.colors["text"], self.text_bg, self.text_bg_alpha)
                self.refresh()
        elif self.tool == "note":
            dlg = NoteDialog(self)
            if dlg.exec() and dlg.edit.toPlainText().strip():
                self.doc.add_note(self.pno, pt, dlg.edit.toPlainText(), self.colors["note"])
                self.refresh()
        elif self.tool == "select":
            a = self.doc.annot_at(self.pno, pt)
            if a is None:
                return
            if a.type[1] in ("Text", "Highlight", "Circle"):
                dlg = NoteDialog(self, a.info.get("content", ""), deletable=True)
                if dlg.exec():
                    if dlg.deleted:
                        self.doc.delete(self.pno, a)
                    else:
                        self.doc.set_note_text(a, dlg.edit.toPlainText())
                    self.refresh()
            elif a.type[1] == "FreeText":
                box = QMessageBox(self)
                box.setWindowTitle(tr("Beírt szöveg"))
                box.setText(f"„{a.info.get('content', '')}”")
                b_bg = box.addButton(tr("Háttér (szín, áttetszőség)…"), QMessageBox.ButtonRole.ActionRole)
                b_clear = box.addButton(tr("Átlátszó háttér"), QMessageBox.ButtonRole.ActionRole)
                b_del = box.addButton(tr("Törlés"), QMessageBox.ButtonRole.DestructiveRole)
                box.addButton(tr("Mégse"), QMessageBox.ButtonRole.RejectRole)
                box.exec()
                c = box.clickedButton()
                if c is b_bg:
                    r = choose_color(self, tr("Háttérszín és áttetszőség"), self.text_bg or (1, 1, 0),
                                     alpha=self.doc.text_bg_alpha(a))
                    if r is None:
                        return
                    self.doc.set_text_bg(a, *r)
                elif c is b_clear:
                    self.doc.set_text_bg(a, None)
                elif c is b_del:
                    self.doc.delete(self.pno, a)
                else:
                    return
                self.refresh()
            elif QMessageBox.question(self, tr("Törlés"), tr("Törlöd ezt: {t}?", t=a.type[1])) == QMessageBox.StandardButton.Yes:
                self.doc.delete(self.pno, a)
                self.refresh()

    def on_drag(self, rect):
        if not self.doc:
            return
        if self.tool == "highlight":
            a = self.doc.add_highlight(self.pno, rect, self.colors["highlight"], self.hl_alpha)
            if a is not None:  # rögtön felkínáljuk a megjegyzést; üresen/Mégse-vel kihagyható
                dlg = NoteDialog(self)
                dlg.setWindowTitle(tr("Megjegyzés a kijelöléshez (üresen hagyható)"))
                if dlg.exec() and dlg.edit.toPlainText().strip():
                    self.doc.set_note_text(a, dlg.edit.toPlainText())
        elif self.tool == "circle":
            self.doc.add_circle(self.pno, rect, self.colors["circle"])
        self.refresh()
