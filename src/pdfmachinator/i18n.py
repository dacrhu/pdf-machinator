"""Háromnyelvű felület (magyar, angol, német). A forráskulcs a magyar szöveg;
a nyelvet az operációs rendszer nyelve adja, ismeretlen nyelv esetén angol.
Felülírás tesztelésre: PDFMACHINATOR_LANG=hu|en|de."""
import os

from PySide6.QtCore import QLocale, QSettings

SUPPORTED = ("hu", "en", "de")


NAMES = {"hu": "Magyar", "en": "English", "de": "Deutsch"}


def settings():
    return QSettings("PDFMachinator", "PDFMachinator")


def saved():
    """A felhasználó által kézzel választott nyelv; "" = automatikus (OS)."""
    v = str(settings().value("language", "") or "")
    return v if v in SUPPORTED else ""


def save(code):
    s = settings()
    s.setValue("language", code)
    s.sync()


def detect():
    forced = os.environ.get("PDFMACHINATOR_LANG", "").lower()[:2]
    if forced in SUPPORTED:
        return forced
    if saved():
        return saved()
    for name in QLocale.system().uiLanguages() + [QLocale.system().name()]:
        code = name.replace("_", "-").split("-")[0].lower()
        if code in SUPPORTED:
            return code
        if code:  # az első, számunkra ismert/ismeretlen elsődleges nyelv dönt
            return "en"
    return "en"


LANG = detect()

T = {
    "en": {
        "Kijelölés": "Select",
        "Beleírás": "Insert text",
        "Megjegyzés": "Note",
        "Filc": "Highlight",
        "Karika": "Circle",
        "Annotáció megnyitása, szerkesztése, törlése: kattints rá": "Click an annotation to open, edit or delete it",
        "Kattints a betűk közé, ahová írni szeretnél": "Click between the letters where you want to type",
        "Kattints oda, ahová megjegyzést (post-it) szeretnél tenni": "Click where you want to place a note",
        "Húzd végig a kijelölendő szövegen": "Drag over the text to highlight",
        "Húzással karikázd be; Shift: szabályos kör": "Drag to circle; hold Shift for a perfect circle",
        "Törlés": "Delete",
        "Megnyitás…": "Open…",
        "PDF megnyitása": "Open PDF",
        "Mentés": "Save",
        "Mentés másként…": "Save As…",
        "Kilépés": "Quit",
        "Visszavonás": "Undo",
        "Előző oldal": "Previous page",
        "Következő oldal": "Next page",
        "Nagyítás": "Zoom in",
        "Kicsinyítés": "Zoom out",
        "Szélességhez igazítás": "Fit width",
        "Szín…": "Color…",
        "Az eszköz színe": "Tool color",
        "Háttér…": "Background…",
        "Beírt szöveg háttere és áttetszősége": "Background and opacity of inserted text",
        "Nincs háttér": "No background",
        "Névjegy": "About",
        "&Fájl": "&File",
        "&Szerkesztés": "&Edit",
        "&Eszközök": "&Tools",
        "&Nézet": "&View",
        "&Súgó": "&Help",
        "Eszközök": "Tools",
        "Ugrás az oldalra": "Go to page",
        "Szín: {tool} – kattints a módosításhoz": "Color: {tool} – click to change",
        "Beírt szöveg háttere: nincs – kattints a módosításhoz": "Text background: none – click to change",
        "Beírt szöveg háttere: {pct}% fedés – kattints a módosításhoz": "Text background: {pct}% opacity – click to change",
        "Korrektori PDF-jegyzetelő.": "Proofreader's PDF annotator.",
        "A mentés az eredeti oldaltartalmat nem módosítja, a jegyzetek hozzáfűzve kerülnek a fájlba.":
            "Saving never alters the original page content; annotations are appended to the file.",
        "Hiba": "Error",
        "Nem nyitható meg: {e}": "Cannot open file: {e}",
        "Mentési hiba": "Save error",
        "Mentetlen változtatások": "Unsaved changes",
        "Mentsem a változtatásokat?": "Do you want to save your changes?",
        "Szín – {tool}": "Color – {tool}",
        "Háttérszín és áttetszőség": "Background color and opacity",
        "Szöveg:": "Text:",
        "Beírt szöveg": "Inserted text",
        "Háttér (szín, áttetszőség)…": "Background (color, opacity)…",
        "Átlátszó háttér": "Transparent background",
        "Mégse": "Cancel",
        "Törlöd ezt: {t}?": "Delete this {t}?",
        "Megjegyzés a kijelöléshez (üresen hagyható)": "Note for the highlight (optional)",
        "Nyiss meg egy PDF-et\n(Ctrl+O), vagy húzd ide a fájlt": "Open a PDF (Ctrl+O)\nor drop a file here",
        "A PDF jelszóval védett.": "The PDF is password protected.",
        "Mentés nem lehetséges: {e}": "Cannot save: {e}",
        "Korrektor": "Proofreader",
        "PDF megnyitása…": "Open PDF…",
        "Automatikus (rendszernyelv)": "Automatic (system language)",
        "A nyelv váltásához a program újraindul.": "The application will restart to change the language.",
        "Újraindítás": "Restart",
        "Verzió": "Version",
        "Licenc": "License",
        "Forráskód": "Source code",
    },
    "de": {
        "Kijelölés": "Auswählen",
        "Beleírás": "Text einfügen",
        "Megjegyzés": "Notiz",
        "Filc": "Markieren",
        "Karika": "Kreis",
        "Annotáció megnyitása, szerkesztése, törlése: kattints rá": "Anmerkung anklicken, um sie zu öffnen, zu bearbeiten oder zu löschen",
        "Kattints a betűk közé, ahová írni szeretnél": "Zwischen die Buchstaben klicken, wo Text eingefügt werden soll",
        "Kattints oda, ahová megjegyzést (post-it) szeretnél tenni": "Dorthin klicken, wo die Notiz stehen soll",
        "Húzd végig a kijelölendő szövegen": "Über den zu markierenden Text ziehen",
        "Húzással karikázd be; Shift: szabályos kör": "Ziehen zum Einkreisen; Umschalt für einen exakten Kreis",
        "Törlés": "Löschen",
        "Megnyitás…": "Öffnen…",
        "PDF megnyitása": "PDF öffnen",
        "Mentés": "Speichern",
        "Mentés másként…": "Speichern unter…",
        "Kilépés": "Beenden",
        "Visszavonás": "Rückgängig",
        "Előző oldal": "Vorherige Seite",
        "Következő oldal": "Nächste Seite",
        "Nagyítás": "Vergrößern",
        "Kicsinyítés": "Verkleinern",
        "Szélességhez igazítás": "Breite anpassen",
        "Szín…": "Farbe…",
        "Az eszköz színe": "Werkzeugfarbe",
        "Háttér…": "Hintergrund…",
        "Beírt szöveg háttere és áttetszősége": "Hintergrund und Deckkraft des eingefügten Textes",
        "Nincs háttér": "Kein Hintergrund",
        "Névjegy": "Info",
        "&Fájl": "&Datei",
        "&Szerkesztés": "&Bearbeiten",
        "&Eszközök": "&Werkzeuge",
        "&Nézet": "&Ansicht",
        "&Súgó": "&Hilfe",
        "Eszközök": "Werkzeuge",
        "Ugrás az oldalra": "Zu Seite springen",
        "Szín: {tool} – kattints a módosításhoz": "Farbe: {tool} – zum Ändern klicken",
        "Beírt szöveg háttere: nincs – kattints a módosításhoz": "Texthintergrund: keiner – zum Ändern klicken",
        "Beírt szöveg háttere: {pct}% fedés – kattints a módosításhoz": "Texthintergrund: {pct} % Deckkraft – zum Ändern klicken",
        "Korrektori PDF-jegyzetelő.": "PDF-Anmerkungswerkzeug für Korrektoren.",
        "A mentés az eredeti oldaltartalmat nem módosítja, a jegyzetek hozzáfűzve kerülnek a fájlba.":
            "Beim Speichern bleibt der ursprüngliche Seiteninhalt unverändert; Anmerkungen werden an die Datei angehängt.",
        "Hiba": "Fehler",
        "Nem nyitható meg: {e}": "Datei kann nicht geöffnet werden: {e}",
        "Mentési hiba": "Speicherfehler",
        "Mentetlen változtatások": "Nicht gespeicherte Änderungen",
        "Mentsem a változtatásokat?": "Möchten Sie die Änderungen speichern?",
        "Szín – {tool}": "Farbe – {tool}",
        "Háttérszín és áttetszőség": "Hintergrundfarbe und Deckkraft",
        "Szöveg:": "Text:",
        "Beírt szöveg": "Eingefügter Text",
        "Háttér (szín, áttetszőség)…": "Hintergrund (Farbe, Deckkraft)…",
        "Átlátszó háttér": "Transparenter Hintergrund",
        "Mégse": "Abbrechen",
        "Törlöd ezt: {t}?": "{t} löschen?",
        "Megjegyzés a kijelöléshez (üresen hagyható)": "Notiz zur Markierung (optional)",
        "Nyiss meg egy PDF-et\n(Ctrl+O), vagy húzd ide a fájlt": "PDF öffnen (Strg+O)\noder Datei hierher ziehen",
        "A PDF jelszóval védett.": "Das PDF ist passwortgeschützt.",
        "Mentés nem lehetséges: {e}": "Speichern nicht möglich: {e}",
        "Korrektor": "Korrektor",
        "PDF megnyitása…": "PDF öffnen…",
        "Automatikus (rendszernyelv)": "Automatisch (Systemsprache)",
        "A nyelv váltásához a program újraindul.": "Die Anwendung wird zum Ändern der Sprache neu gestartet.",
        "Újraindítás": "Neustart",
        "Verzió": "Version",
        "Licenc": "Lizenz",
        "Forráskód": "Quellcode",
    },
}


def tr(key, **kw):
    s = key if LANG == "hu" else T[LANG].get(key, key)
    return s.format(**kw) if kw else s
