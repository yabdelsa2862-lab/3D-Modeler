"""
Forge 3D — Bootstrap / loading screen.

Flow
----
1. Redirect stdout/stderr to forge3d.log (pythonw.exe has no console).
2. Pure-Python phase: if PySide6 is missing, pip-install it (logged to file).
3. Qt phase: show the centered splash screen immediately.
4. Check every other package with importlib.util.find_spec — only pip-install
   the ones that are actually missing; already-installed packages are skipped.
5. When everything is ready, close the splash and open MainWindow.
"""
import sys
import os
import subprocess
import importlib.util
from pathlib import Path

# ── Redirect output to log file ───────────────────────────────────────────────
# pythonw.exe has no console; without this, any exception is silently lost.
_APP_DIR  = Path(__file__).resolve().parent
_LOG_PATH = _APP_DIR / "forge3d.log"
try:
    _log_fh       = open(_LOG_PATH, "w", encoding="utf-8", buffering=1)
    sys.stdout    = _log_fh
    sys.stderr    = _log_fh
except Exception:
    pass   # If we can't open the log, continue anyway


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _installed(mod: str) -> bool:
    """True iff the Python module can be found without importing it."""
    return importlib.util.find_spec(mod) is not None


def _pip_install(*specs: str):
    """Run pip install -q <specs>. Returns (success, error_text)."""
    r = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", *specs],
        capture_output=True, text=True, timeout=360,
    )
    return r.returncode == 0, (r.stderr or r.stdout or "").strip()


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — Install PySide6 without any GUI (required to show the splash)
# ─────────────────────────────────────────────────────────────────────────────

if not _installed("PySide6"):
    print("[Forge 3D] First-run setup: installing PySide6...")
    ok, err = _pip_install("PySide6>=6.6.0")
    if not ok:
        print(f"ERROR: Could not install PySide6.\n{err}")
        sys.exit(1)
    print("PySide6 installed.")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — Qt is available; build the splash and install everything else
# ─────────────────────────────────────────────────────────────────────────────

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore    import Qt, QThread, Signal, QTimer
from PySide6.QtGui     import QGuiApplication, QPalette, QColor

# Qt 6 already sets per-monitor DPI awareness — no ctypes needed.
# AA_UseHighDpiPixmaps is deprecated in Qt 6 — don't set it.

app = QApplication.instance() or QApplication(sys.argv)
app.setApplicationName("Forge 3D")
app.setOrganizationName("ForgeAI")
app.setApplicationVersion("1.0.0")


# ── All packages required by the app (besides PySide6 which is already done) ─
# Format: (module_to_check, [pip_specs_to_install])
_ALL_PKGS = [
    ("OpenGL",     ["PyOpenGL>=3.1.6", "PyOpenGL-accelerate>=3.1.6"]),
    ("trimesh",    ["trimesh>=4.4.0"]),
    ("manifold3d", ["manifold3d>=2.4.0"]),
    ("shapely",    ["shapely>=2.0.0"]),
    ("networkx",   ["networkx>=3.0"]),
    ("scipy",      ["scipy>=1.11.0"]),
    ("anthropic",  ["anthropic>=0.34.0"]),
    ("openai",     ["openai>=1.40.0"]),
    ("requests",   ["requests>=2.31.0"]),
]


def _missing_pkgs():
    """Return only the packages whose module cannot be found."""
    return [(mod, specs) for mod, specs in _ALL_PKGS if not _installed(mod)]


# ─────────────────────────────────────────────────────────────────────────────
# Splash screen
# ─────────────────────────────────────────────────────────────────────────────

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(440, 290)
        self._center()
        self._build_ui()

    def _center(self):
        geo = QGuiApplication.primaryScreen().availableGeometry()
        self.move(
            geo.x() + (geo.width()  - self.width())  // 2,
            geo.y() + (geo.height() - self.height()) // 2,
        )

    def _build_ui(self):
        card = QWidget(self)
        card.setObjectName("splashCard")
        card.setGeometry(0, 0, 440, 290)
        card.setAttribute(Qt.WA_StyledBackground, True)
        card.setStyleSheet("""
            #splashCard {
                background-color: #0e0e15;
                border: 1px solid rgba(255,255,255,0.13);
                border-radius: 20px;
            }
        """)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(48, 42, 48, 32)
        lay.setSpacing(0)

        icon_lbl = QLabel("\U0001f537")   # blue diamond — no raw emoji in source
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 42px; background: transparent;")
        lay.addWidget(icon_lbl)

        lay.addSpacing(12)

        title_lbl = QLabel("Forge 3D")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(
            "font-size: 26px; font-weight: 700; color: #ffffff;"
            "background: transparent; letter-spacing: -0.6px;"
        )
        lay.addWidget(title_lbl)

        lay.addSpacing(5)

        tagline = QLabel("AI-powered 3D model generator")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setStyleSheet(
            "font-size: 13px; color: rgba(235,235,245,0.38); background: transparent;"
        )
        lay.addWidget(tagline)

        lay.addSpacing(34)

        self._bar = QProgressBar()
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(5)
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255,255,255,0.09);
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0a84ff, stop:1 #30d158
                );
                border-radius: 3px;
            }
        """)
        lay.addWidget(self._bar)

        lay.addSpacing(13)

        self._status_lbl = QLabel("Checking dependencies...")
        self._status_lbl.setAlignment(Qt.AlignCenter)
        self._status_lbl.setStyleSheet(
            "font-size: 12px; color: rgba(235,235,245,0.48); background: transparent;"
        )
        lay.addWidget(self._status_lbl)

        lay.addStretch()

        ver_lbl = QLabel("v1.0")
        ver_lbl.setAlignment(Qt.AlignCenter)
        ver_lbl.setStyleSheet(
            "font-size: 11px; color: rgba(235,235,245,0.17); background: transparent;"
        )
        lay.addWidget(ver_lbl)

    def set_progress(self, pct: int, text: str):
        self._bar.setValue(max(0, min(100, pct)))
        self._status_lbl.setText(text)
        app.processEvents()

    def set_done(self):
        self._bar.setValue(100)
        self._status_lbl.setText("Ready!")
        app.processEvents()

    def set_error(self, msg: str):
        self._status_lbl.setText(f"Warning: {msg}")
        print(f"[install error] {msg}")
        app.processEvents()


# ─────────────────────────────────────────────────────────────────────────────
# Background installer thread
# ─────────────────────────────────────────────────────────────────────────────

class InstallerThread(QThread):
    progress    = Signal(int, str)
    finished_ok = Signal()
    failed      = Signal(str)

    def __init__(self, missing):
        super().__init__()
        self._missing = missing

    def run(self):
        total = len(self._missing)
        for i, (mod, specs) in enumerate(self._missing):
            pct   = 5 + int(i / total * 90)
            label = f"Installing {mod}  ({i + 1} / {total})"
            self.progress.emit(pct, label)
            print(f"[bootstrap] installing {mod}: {specs}")

            ok, err = _pip_install(*specs)
            if not ok:
                print(f"[bootstrap] FAILED {mod}: {err}")
                self.failed.emit(f"Failed to install {mod}")
                return
            print(f"[bootstrap] ok: {mod}")

        self.finished_ok.emit()


# ─────────────────────────────────────────────────────────────────────────────
# Launch the main window once all packages are confirmed present
# ─────────────────────────────────────────────────────────────────────────────

def _open_main_window(splash: SplashScreen):
    splash.set_done()

    def _do_open():
        try:
            splash.close()

            from window import MainWindow, DARK_QSS

            app.setStyle("Fusion")

            p = QPalette()
            _c = QColor
            p.setColor(QPalette.Window,          _c(0x08, 0x08, 0x0e))
            p.setColor(QPalette.WindowText,      _c(0xe8, 0xe8, 0xed))
            p.setColor(QPalette.Base,            _c(0x12, 0x12, 0x1c))
            p.setColor(QPalette.AlternateBase,   _c(0x1c, 0x1c, 0x2a))
            p.setColor(QPalette.ToolTipBase,     _c(0x1c, 0x1c, 0x2a))
            p.setColor(QPalette.ToolTipText,     _c(0xe8, 0xe8, 0xed))
            p.setColor(QPalette.Text,            _c(0xe8, 0xe8, 0xed))
            p.setColor(QPalette.Button,          _c(0x1c, 0x1c, 0x2a))
            p.setColor(QPalette.ButtonText,      _c(0xe8, 0xe8, 0xed))
            p.setColor(QPalette.BrightText,      _c(255, 255, 255))
            p.setColor(QPalette.Link,            _c(0x2e, 0x7c, 0xff))
            p.setColor(QPalette.Highlight,       _c(0x2e, 0x7c, 0xff))
            p.setColor(QPalette.HighlightedText, _c(255, 255, 255))
            p.setColor(QPalette.PlaceholderText, _c(0x88, 0x88, 0x99))
            p.setColor(QPalette.Mid,             _c(0x28, 0x28, 0x38))
            p.setColor(QPalette.Dark,            _c(0x08, 0x08, 0x0e))
            p.setColor(QPalette.Shadow,          _c(0, 0, 0, 180))
            for role in (QPalette.WindowText, QPalette.Text,
                         QPalette.ButtonText, QPalette.Highlight):
                p.setColor(QPalette.Disabled, role,
                           p.color(QPalette.PlaceholderText))
            app.setPalette(p)
            app.setStyleSheet(DARK_QSS)

            from PySide6.QtGui import QFont
            font = QFont()
            font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
            for face in ("SF Pro Display", "Segoe UI", "Helvetica Neue", "Arial"):
                font.setFamily(face)
                if font.exactMatch():
                    break
            font.setPointSize(10)
            app.setFont(font)

            win = MainWindow()
            app._main_win = win
            win.show()
            print("[bootstrap] MainWindow shown.")

        except Exception as exc:
            import traceback
            print("[bootstrap] ERROR opening MainWindow:")
            traceback.print_exc()

    QTimer.singleShot(550, _do_open)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

print("[bootstrap] starting")

splash = SplashScreen()
splash.show()
splash.set_progress(0, "Checking dependencies...")
app.processEvents()

missing = _missing_pkgs()
print(f"[bootstrap] missing packages: {[m for m,_ in missing]}")

if not missing:
    splash.set_progress(100, "All packages present — launching...")
    app.processEvents()
    QTimer.singleShot(500, lambda: _open_main_window(splash))
else:
    _thread = InstallerThread(missing)
    _thread.progress.connect(splash.set_progress)
    _thread.finished_ok.connect(lambda: _open_main_window(splash))
    _thread.failed.connect(splash.set_error)
    app._installer = _thread
    _thread.start()

sys.exit(app.exec())
