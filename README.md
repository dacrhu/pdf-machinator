# PDF Machinator

<img src="assets/icon.png" width="96" align="right" alt="PDF Machinator icon">

A small desktop PDF annotator for proofreaders (Windows, macOS, Linux).

**The page layout is never touched.** Everything you add is a standard PDF annotation, and saving
appends the changes to the end of the file (incremental save) — the original page content stays
byte-for-byte identical, which is what typesetters need.

## Features

- **Insert text** right between the letters (e.g. a missing comma), in the size and baseline of the
  surrounding line, with a custom text colour and an optional background with adjustable opacity
- **Notes** (sticky-note icon): click to read, edit or delete
- **Highlighter**, with an optional comment on each highlight
- **Circle / ellipse** (hold <kbd>Shift</kbd> for a perfect circle), with optional comments
- Save and Save As, undo, zoom, fit width, page navigation
- Colour picker with favourites, eyedropper and opacity
- UI in **English, German and Hungarian**; follows the OS language, switchable from the *Language* menu

Shortcuts: <kbd>V</kbd> select · <kbd>T</kbd> text · <kbd>N</kbd> note · <kbd>H</kbd> highlight · <kbd>C</kbd> circle.

## Download

Get the latest build from the [Releases](https://github.com/dacrhu/pdf-machinator/releases) page.

| Platform | File |
| --- | --- |
| Windows 10/11 | `.exe` (portable) |
| macOS (Apple Silicon / Intel) | `.dmg` |
| Linux | `.AppImage` (`chmod +x`, then run) |

**macOS:** these builds aren't signed with an Apple Developer ID, so Gatekeeper may call the app
"damaged and can't be opened" on first launch instead of just warning about an unidentified developer —
that's not a bad download, just an unsigned-app warning, and it's fixed with one Terminal command.
See [Troubleshooting](#macos-app-reported-as-damaged-gatekeeper).

**Linux:** needs a desktop with X11 or Wayland and `libxcb-cursor0` (Qt 6 requirement; preinstalled on most distros).

## Run from source

```sh
python -m venv .venv
.venv/bin/pip install -e . pytest      # Windows: .venv\Scripts\pip
.venv/bin/pdfmachinator [file.pdf]
.venv/bin/python -m pytest
```

## Building the apps

Releases are built by GitHub Actions for every OS ([release.yml](.github/workflows/release.yml)):
push a tag like `v1.0.0` and the `.exe`, both `.dmg` files and the `.AppImage` are attached to a new release.
Locally: `pip install pyinstaller && pyinstaller packaging/pdfmachinator.spec`.
The icon is generated from `assets/icon.svg` by `tools/make_icons.py`.

## Troubleshooting

### macOS: app reported as "damaged" (Gatekeeper)

Not an actual corrupted download — this is Gatekeeper's message for an app that isn't signed with an
Apple Developer ID and notarized. The browser tags whatever you download with the
`com.apple.quarantine` extended attribute, and Gatekeeper reports an unsigned, quarantined app as
"damaged and can't be opened" instead of admitting it just doesn't trust it.

Fix from Terminal (the most reliable route, especially on macOS Sequoia, where right-click →
*Open* doesn't always offer an "Open Anyway" button anymore):

```sh
xattr -cr "/Applications/PDF Machinator.app"
```

If the `.dmg` already reports "damaged" at mount time, run it on the `.dmg` file itself before mounting.
If it's still flagged afterwards, open **System Settings → Privacy & Security → Security**, scroll down
and try to open the app once — an "Open Anyway" button then appears there.

## License

[GNU AGPL-3.0](LICENSE). The app is built on [PyMuPDF](https://pymupdf.readthedocs.io/) (AGPL-3.0),
so the whole project is AGPL: free to use, modify and share; modified versions must be shared under
the same terms, with source.
