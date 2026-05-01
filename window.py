"""
Forge 3D — Main application window (PySide6, native Windows).
"""
import json
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLabel, QPushButton, QLineEdit, QTextEdit,
    QComboBox, QStackedWidget, QSizeGrip, QFileDialog,
    QScrollArea, QFrame, QPlainTextEdit, QTabWidget,
    QProgressBar, QApplication,
)
from PySide6.QtCore import (
    Qt, QThread, Signal, QSettings, QSize, QPoint, QTimer,
    QRegularExpression,
)
from PySide6.QtGui import (
    QFont, QColor, QPalette, QSyntaxHighlighter, QTextCharFormat,
    QIcon, QCursor, QPainter, QPixmap, QFontMetrics,
)

from viewport import Viewport3D
from generation import generate_model

SETTINGS_ORG  = "ForgeAI"
SETTINGS_APP  = "Forge3D"

# ── QSS Dark theme ──────────────────────────────────────────────────────────
DARK_QSS = """
* {
    font-family: "Segoe UI Variable Display", "Segoe UI", system-ui, sans-serif;
    font-size: 13px;
    color: #e8e8ed;
}
QMainWindow, QDialog { background: #0f0f11; }

/* ── Titlebar ── */
#titleBar {
    background: #18181c;
    border-bottom: 1px solid rgba(84,84,88,0.45);
}
#titleLabel {
    font-size: 13px;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: -0.2px;
}
#titleSub { font-size: 12px; color: rgba(235,235,245,0.35); }

/* ── Sidebar ── */
#sidebar {
    background: #141416;
    border-right: 1px solid rgba(84,84,88,0.35);
    min-width: 268px;
    max-width: 268px;
}
#sectionLabel {
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.55px;
    color: rgba(235,235,245,0.28);
    text-transform: uppercase;
}

/* ── Provider buttons ── */
#providerRow { background: rgba(118,118,128,0.14); border-radius: 10px; padding: 2px; }
ProviderBtn {
    background: transparent;
    border: none;
    border-radius: 8px;
    color: rgba(235,235,245,0.55);
    font-size: 11.5px;
    padding: 5px 2px;
    font-weight: 500;
}
ProviderBtn:hover { color: rgba(235,235,245,0.85); }
ProviderBtn[active="true"] {
    background: rgba(255,255,255,0.11);
    color: #ffffff;
}

/* ── Fields ── */
QLineEdit, QTextEdit, QComboBox, QPlainTextEdit {
    background: rgba(255,255,255,0.055);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 8px;
    padding: 7px 10px;
    color: #e8e8ed;
    selection-background-color: #0a84ff;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #0a84ff;
    background: rgba(10,132,255,0.07);
}
QLineEdit::placeholder, QTextEdit::placeholder { color: rgba(235,235,245,0.22); }

QComboBox { padding-right: 24px; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid rgba(235,235,245,0.35);
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background: #2c2c2e;
    border: 1px solid rgba(84,84,88,0.5);
    border-radius: 8px;
    selection-background-color: #0a84ff;
    padding: 4px;
}
QComboBox QAbstractItemView::item { border-radius: 5px; padding: 5px 8px; }
QComboBox QAbstractItemView::item:selected { background: #0a84ff; color: white; }

/* ── Generate button ── */
#generateBtn {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #1a8fff,stop:1 #0a7ef5);
    border: none;
    border-radius: 11px;
    color: white;
    font-size: 14px;
    font-weight: 700;
    padding: 13px;
    letter-spacing: -0.2px;
}
#generateBtn:hover  { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #2a9fff,stop:1 #1a8ef8); }
#generateBtn:pressed{ background: #0870e0; }
#generateBtn:disabled { background: rgba(10,132,255,0.28); color: rgba(255,255,255,0.4); }

/* ── Action buttons ── */
ActionBtn {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 7px;
    color: rgba(235,235,245,0.7);
    padding: 5px 11px;
    font-size: 12px;
}
ActionBtn:hover  { background: rgba(255,255,255,0.12); color: #ffffff; }
ActionBtn:pressed{ background: rgba(255,255,255,0.06); }

/* ── Splitter ── */
QSplitter::handle:vertical   { background: rgba(84,84,88,0.35); height: 1px; margin: 0; }
QSplitter::handle:horizontal { background: rgba(84,84,88,0.35); width: 1px; margin: 0; }

/* ── Code panel ── */
#codePanel { background: #0c0c10; border-top: 1px solid rgba(84,84,88,0.35); }
#panelHeader { background: #141416; border-bottom: 1px solid rgba(84,84,88,0.25); }

QTabBar { background: transparent; }
QTabBar::tab {
    background: transparent;
    color: rgba(235,235,245,0.5);
    padding: 10px 16px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 12.5px;
    font-weight: 500;
}
QTabBar::tab:selected { color: #ffffff; border-bottom-color: #0a84ff; }
QTabBar::tab:hover:!selected { color: rgba(235,235,245,0.8); }
QTabWidget::pane { border: none; background: #0c0c10; }

/* ── Scrollbar ── */
QScrollBar:vertical   { background: transparent; width: 5px; margin: 0; }
QScrollBar:horizontal { background: transparent; height: 5px; margin: 0; }
QScrollBar::handle    { background: rgba(255,255,255,0.18); border-radius: 3px; min-height: 20px; min-width: 20px; }
QScrollBar::handle:hover { background: rgba(255,255,255,0.30); }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page,  QScrollBar::sub-page { background: transparent; }

/* ── Status badge ── */
#statusBadge {
    background: rgba(12,12,18,0.85);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 14px;
    padding: 4px 12px;
    font-size: 12px;
    color: rgba(235,235,245,0.6);
}
#statusBadge[state="ok"]   { color: #30d158; border-color: rgba(48,209,88,0.3); }
#statusBadge[state="warn"] { color: #ff9f0a; border-color: rgba(255,159,10,0.3); }
#statusBadge[state="err"]  { color: #ff453a; border-color: rgba(255,69,58,0.3); }

/* ── Viewport overlay labels ── */
#vpHint {
    color: rgba(235,235,245,0.18);
    font-size: 12px;
    background: transparent;
}
#vpEmpty {
    color: rgba(235,235,245,0.20);
    font-size: 15px;
    font-weight: 500;
    background: transparent;
}
#vpEmptySub {
    color: rgba(235,235,245,0.12);
    font-size: 12px;
    background: transparent;
}

/* ── Separator ── */
#sep { background: rgba(84,84,88,0.35); max-height: 1px; min-height: 1px; }

/* ── Hint text ── */
#hintText { color: rgba(235,235,245,0.28); font-size: 11.5px; }

/* ── Sidebar tab row ── */
#sideTabRow {
    background: rgba(118,118,128,0.14);
    border-radius: 10px;
    padding: 2px;
}
SideTabBtn {
    background: transparent;
    border: none;
    border-radius: 8px;
    color: rgba(235,235,245,0.50);
    font-size: 12.5px;
    font-weight: 500;
    padding: 5px 4px;
}
SideTabBtn:hover { color: rgba(235,235,245,0.85); }
SideTabBtn[active="true"] {
    background: rgba(255,255,255,0.11);
    color: #ffffff;
    font-weight: 600;
}

/* ── Chat area ── */
#chatScroll {
    background: transparent;
    border: none;
}
#chatContainer { background: transparent; }

/* ── Install toast ── */
#installToast {
    background: rgba(22,22,30,0.97);
    border: 1px solid rgba(255,255,255,0.13);
    border-radius: 14px;
}
#toastTitle {
    font-size: 13px;
    font-weight: 600;
    color: #e8e8ed;
    background: transparent;
}
#toastSub {
    font-size: 11.5px;
    color: rgba(235,235,245,0.45);
    background: transparent;
}
QProgressBar#toastProgress {
    background: rgba(255,255,255,0.10);
    border: none;
    border-radius: 3px;
    min-height: 5px;
    max-height: 5px;
}
QProgressBar#toastProgress::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0a84ff,stop:1 #30d158);
    border-radius: 3px;
}
"""


# ── Helpers ──────────────────────────────────────────────────────────────────

def label(text, obj_name=None):
    l = QLabel(text)
    if obj_name:
        l.setObjectName(obj_name)
    return l

def field(placeholder="", password=False, fixed_h=34):
    e = QLineEdit()
    e.setPlaceholderText(placeholder)
    if password:
        e.setEchoMode(QLineEdit.Password)
    e.setFixedHeight(fixed_h)
    return e

def combo(*items):
    c = QComboBox()
    c.addItems(items)
    return c

def sep():
    w = QWidget()
    w.setObjectName("sep")
    w.setFixedHeight(1)
    return w


# ── Python syntax highlighter ────────────────────────────────────────────────

class PythonHL(QSyntaxHighlighter):
    def __init__(self, doc):
        super().__init__(doc)
        self._rules = []

        def add(pat, color, bold=False, italic=False):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            if bold:   fmt.setFontWeight(700)
            if italic: fmt.setFontItalic(True)
            self._rules.append((QRegularExpression(pat), fmt))

        kw = (r"\b(import|from|as|def|class|return|if|elif|else|for|while|"
              r"try|except|finally|with|in|not|and|or|True|False|None|"
              r"lambda|pass|break|continue|raise|yield|global|nonlocal)\b")
        add(kw, "#c678dd", bold=True)
        add(r"\b(trimesh|np|numpy|math|print|len|range|max|min|abs|str|int|float|bool|list|dict)\b", "#e5c07b")
        add(r'"[^"\n]*"',  "#98c379")
        add(r"'[^'\n]*'",  "#98c379")
        add(r"\b\d+\.?\d*([eE][+-]?\d+)?\b", "#d19a66")
        add(r"#[^\n]*",    "#5c6370", italic=True)

    def highlightBlock(self, text):
        for regex, fmt in self._rules:
            it = regex.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


# ── Windows-style caption button ─────────────────────────────────────────────

class WinCtrlBtn(QPushButton):
    """Minimize / maximize / close button styled like Windows 11."""

    _CLOSE_HOVER  = "#c42b1c"
    _CLOSE_PRESS  = "#b52719"
    _STD_HOVER    = "rgba(255,255,255,0.10)"
    _STD_PRESS    = "rgba(255,255,255,0.05)"

    def __init__(self, symbol: str, is_close: bool = False, parent=None):
        super().__init__(symbol, parent)
        self._is_close = is_close
        self.setFixedSize(46, 36)
        self.setCursor(Qt.ArrowCursor)
        self._set_style(False, False)

    def enterEvent(self, e):
        self._set_style(True, False)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._set_style(False, False)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        self._set_style(True, True)
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self._set_style(True, False)
        super().mouseReleaseEvent(e)

    def _set_style(self, hovered: bool, pressed: bool):
        if self._is_close:
            bg = self._CLOSE_PRESS if pressed else (self._CLOSE_HOVER if hovered else "transparent")
            fg = "white"
        else:
            bg = self._STD_PRESS if pressed else (self._STD_HOVER if hovered else "transparent")
            fg = "rgba(235,235,245,0.80)"
        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                border: none;
                color: {fg};
                font-size: 13px;
                font-family: "Segoe UI", "Segoe Fluent Icons", system-ui, sans-serif;
                padding-bottom: 1px;
            }}
        """)


# ── Custom title bar ──────────────────────────────────────────────────────────

class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self._win      = parent
        self._drag_pos = None
        self.setObjectName("titleBar")
        self.setFixedHeight(36)

        # No right margin — control buttons go flush to the edge
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 0, 0)
        lay.setSpacing(0)

        # LEFT: icon + title + subtitle
        self.icon_lbl  = QLabel("\U0001f537")   # blue diamond
        self.icon_lbl.setStyleSheet("font-size: 14px; background: transparent;")
        self.title_lbl = QLabel("Forge 3D")
        self.title_lbl.setObjectName("titleLabel")
        self.sub_lbl   = QLabel("")
        self.sub_lbl.setObjectName("titleSub")
        for w in (self.icon_lbl, self.title_lbl):
            lay.addWidget(w)
            lay.addSpacing(5)
        lay.addWidget(self.sub_lbl)

        lay.addStretch()

        # CENTRE-RIGHT: download action buttons
        self.btn_dl_stl = self._tbtn("↓ STL")
        self.btn_dl_py  = self._tbtn("↓ .py")
        self.btn_dl_stl.setVisible(False)
        self.btn_dl_py.setVisible(False)
        lay.addWidget(self.btn_dl_stl)
        lay.addSpacing(4)
        lay.addWidget(self.btn_dl_py)
        lay.addSpacing(10)

        # RIGHT: Windows caption buttons (flush to edge)
        self.btn_min   = WinCtrlBtn("−")          # −
        self.btn_max   = WinCtrlBtn("□")          # □
        self.btn_close = WinCtrlBtn("✕", is_close=True)   # ✕
        for b in (self.btn_min, self.btn_max, self.btn_close):
            lay.addWidget(b)

        # Connect
        self.btn_close.clicked.connect(parent.close)
        self.btn_min.clicked.connect(parent.showMinimized)
        self.btn_max.clicked.connect(self._toggle_max)

    def _tbtn(self, text):
        b = QPushButton(text)
        b.setFixedHeight(26)
        b.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.07);
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 7px;
                color: rgba(235,235,245,0.65);
                padding: 0 11px;
                font-size: 12px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.12); color: white; }
        """)
        return b

    def _toggle_max(self):
        if self._win.isMaximized():
            self._win.showNormal()
            self.btn_max.setText("□")   # □
        else:
            self._win.showMaximized()
            self.btn_max.setText("▣")   # ⬛ (restore symbol)

    def set_subtitle(self, text):
        self.sub_lbl.setText(text)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self._win.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton and self._drag_pos:
            self._win.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, e):
        self._toggle_max()


# ── Provider button ───────────────────────────────────────────────────────────

class ProviderBtn(QPushButton):
    def __init__(self, icon, name, parent=None):
        super().__init__(parent)
        self.setText(f"{icon}\n{name}")
        self.setCheckable(False)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(52)
        self._active = False

    def set_active(self, active: bool):
        self._active = active
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


# ── Install-progress toast ────────────────────────────────────────────────────

class InstallToast(QWidget):
    """Bottom-right floating notification shown while installing packages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("installToast")
        self.setFixedWidth(300)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(8)

        # ── Title row ──
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(8)

        self._icon = QLabel("📦")
        self._icon.setStyleSheet("font-size: 16px; background: transparent;")
        self._title = QLabel("Installing dependencies…")
        self._title.setObjectName("toastTitle")
        rl.addWidget(self._icon)
        rl.addWidget(self._title, 1)
        outer.addWidget(row)

        # ── Subtitle ──
        self._sub = QLabel("Preparing…")
        self._sub.setObjectName("toastSub")
        outer.addWidget(self._sub)

        # ── Progress bar ──
        self._bar = QProgressBar()
        self._bar.setObjectName("toastProgress")
        self._bar.setTextVisible(False)
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        outer.addWidget(self._bar)

        self.adjustSize()

    def set_progress(self, value: int, text: str):
        self._bar.setValue(value)
        self._sub.setText(text)
        self.adjustSize()

    def set_done(self):
        self._icon.setText("✅")
        self._title.setText("All set!")
        self._sub.setText("Dependencies installed successfully")
        self._bar.setValue(100)
        self.adjustSize()

    def set_error(self, msg: str):
        self._icon.setText("⚠️")
        self._title.setText("Install error")
        self._sub.setText(msg[:60])
        self.adjustSize()


# ── Sidebar tab button ───────────────────────────────────────────────────────

class SideTabBtn(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(30)
        self._active = False

    def set_active(self, active: bool):
        self._active = active
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


# ── Chat message bubble ───────────────────────────────────────────────────────

class ChatBubble(QWidget):
    """Single message bubble — right-aligned (user) or left-aligned (AI)."""

    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(4, 2, 4, 2)
        outer.setSpacing(0)

        self._lbl = QLabel(text)
        self._lbl.setWordWrap(True)
        self._lbl.setMaximumWidth(218)
        self._lbl.setMinimumWidth(32)
        self._lbl.setAttribute(Qt.WA_StyledBackground, True)
        self._lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)

        if is_user:
            self._lbl.setStyleSheet("""
                QLabel {
                    background: #0a84ff;
                    color: #ffffff;
                    border-radius: 14px;
                    padding: 9px 13px;
                    font-size: 12.5px;
                    line-height: 1.4;
                }
            """)
            outer.addStretch()
            outer.addWidget(self._lbl)
        else:
            self._lbl.setStyleSheet("""
                QLabel {
                    background: rgba(38,38,56,0.95);
                    color: #e8e8ed;
                    border-radius: 14px;
                    padding: 9px 13px;
                    font-size: 12.5px;
                    line-height: 1.4;
                }
            """)
            outer.addWidget(self._lbl)
            outer.addStretch()

    def set_text(self, text: str):
        self._lbl.setText(text)
        self._lbl.adjustSize()
        self.adjustSize()


# ── Settings pages ────────────────────────────────────────────────────────────

def _settings_layout():
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(10)
    return w, v

def _row(lbl_text, widget):
    r = QWidget()
    lay = QVBoxLayout(r)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(4)
    lbl = QLabel(lbl_text)
    lbl.setStyleSheet("color: rgba(235,235,245,0.55); font-size: 12px; font-weight:500;")
    lay.addWidget(lbl)
    lay.addWidget(widget)
    return r

def make_anthropic_page():
    w, v = _settings_layout()
    key_f  = field("sk-ant-api03-…", password=True)
    model_c = combo("claude-opus-4-5", "claude-sonnet-4-5", "claude-haiku-4-5")
    model_c.setCurrentIndex(1)
    v.addWidget(_row("API Key", key_f))
    v.addWidget(_row("Model",   model_c))
    v.addStretch()
    return w, {"api_key": key_f, "model": model_c}

def make_openai_page():
    w, v = _settings_layout()
    key_f   = field("sk-…", password=True)
    model_c = combo("gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1", "o3-mini")
    v.addWidget(_row("API Key", key_f))
    v.addWidget(_row("Model",   model_c))
    v.addStretch()
    return w, {"api_key": key_f, "model": model_c}

def make_openrouter_page():
    w, v = _settings_layout()
    key_f   = field("sk-or-…", password=True)
    model_f = field("anthropic/claude-3.5-sonnet")
    hint = QLabel("Browse models at openrouter.ai/models")
    hint.setObjectName("hintText")
    hint.setWordWrap(True)
    v.addWidget(_row("API Key",  key_f))
    v.addWidget(_row("Model ID", model_f))
    v.addWidget(hint)
    v.addStretch()
    return w, {"api_key": key_f, "model": model_f}

def make_azure_page():
    w, v = _settings_layout()
    key_f  = field("Azure API key", password=True)
    ep_f   = field("https://YOUR-RESOURCE.openai.azure.com")
    dep_f  = field("gpt-5-chat")
    ver_f  = field("2025-01-01-preview")
    for lbl_t, wid in [("API Key",    key_f), ("Endpoint", ep_f),
                        ("Deployment", dep_f), ("API Version", ver_f)]:
        v.addWidget(_row(lbl_t, wid))
    v.addStretch()
    return w, {"api_key": key_f, "endpoint": ep_f, "deployment": dep_f, "api_version": ver_f}

def make_local_page():
    w, v = _settings_layout()
    url_f   = field("http://localhost:11434")
    model_f = field("llama3.2")
    hint = QLabel("Run  ollama pull llama3.2  first.\nWorks with any Ollama-compatible server.")
    hint.setObjectName("hintText")
    hint.setWordWrap(True)
    v.addWidget(_row("Ollama URL", url_f))
    v.addWidget(_row("Model",      model_f))
    v.addWidget(hint)
    v.addStretch()
    return w, {"base_url": url_f, "model": model_f}


# ── Generation worker ─────────────────────────────────────────────────────────

class Worker(QThread):
    done  = Signal(dict)
    error = Signal(str)

    def __init__(self, prompt, provider, settings, history=None):
        super().__init__()
        self.prompt   = prompt
        self.provider = provider
        self.settings = settings
        self.history  = history or []

    def run(self):
        try:
            result = generate_model(self.prompt, self.provider,
                                    self.settings, self.history)
            self.done.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# ── Main window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Forge 3D")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.resize(1340, 840)
        self.setMinimumSize(960, 640)

        self._worker      = None
        self._result      = None
        self._qsettings   = QSettings(SETTINGS_ORG, SETTINGS_APP)
        self._history     = []          # conversation history for multi-turn chat
        self._last_prompt = ""          # prompt of the in-flight request
        self._ai_bubble   = None        # placeholder bubble updated on response

        self._build_ui()
        self._load_settings()

        # Install toast (parented to main window so it floats above everything)
        self._install_toast = InstallToast(self)
        self._install_toast.setVisible(False)

        # Resize grip (bottom-right corner)
        grip = QSizeGrip(self)
        grip.setFixedSize(16, 16)
        grip.move(self.width() - 16, self.height() - 16)
        grip.raise_()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_lay = QVBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # Title bar
        self.titlebar = TitleBar(self)
        root_lay.addWidget(self.titlebar)
        self.titlebar.btn_dl_stl.clicked.connect(lambda: self._download("stl"))
        self.titlebar.btn_dl_py.clicked.connect(lambda: self._download("py"))

        # Body
        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)
        root_lay.addWidget(body)

        # Sidebar
        sidebar = self._build_sidebar()
        body_lay.addWidget(sidebar)

        # Workspace (viewport + code panel)
        workspace = self._build_workspace()
        body_lay.addWidget(workspace, 1)

    def _build_sidebar(self):
        side = QWidget()
        side.setObjectName("sidebar")
        root = QVBoxLayout(side)
        root.setContentsMargins(12, 10, 12, 14)
        root.setSpacing(0)

        # ── Tab row ──────────────────────────────────────────────────────────
        tab_row = QWidget()
        tab_row.setObjectName("sideTabRow")
        trl = QHBoxLayout(tab_row)
        trl.setContentsMargins(3, 3, 3, 3)
        trl.setSpacing(2)

        self._tab_chat     = SideTabBtn("💬  Chat")
        self._tab_settings = SideTabBtn("⚙  Settings")
        self._tab_chat.clicked.connect(lambda: self._switch_sidebar(0))
        self._tab_settings.clicked.connect(lambda: self._switch_sidebar(1))
        trl.addWidget(self._tab_chat, 1)
        trl.addWidget(self._tab_settings, 1)
        root.addWidget(tab_row)
        root.addSpacing(10)

        # ── Stacked pages ─────────────────────────────────────────────────────
        self._sidebar_stack = QStackedWidget()
        self._sidebar_stack.addWidget(self._build_chat_page())
        self._sidebar_stack.addWidget(self._build_settings_page())
        root.addWidget(self._sidebar_stack, 1)

        self._switch_sidebar(0)
        return side

    # ── Sidebar tab switching ─────────────────────────────────────────────────

    def _switch_sidebar(self, idx: int):
        self._sidebar_stack.setCurrentIndex(idx)
        for i, b in enumerate([self._tab_chat, self._tab_settings]):
            b.set_active(i == idx)

    # ── Chat page ─────────────────────────────────────────────────────────────

    def _build_chat_page(self):
        page = QWidget()
        lay  = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # Message history
        self._chat_scroll = QScrollArea()
        self._chat_scroll.setObjectName("chatScroll")
        self._chat_scroll.setWidgetResizable(True)
        self._chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._chat_container = QWidget()
        self._chat_container.setObjectName("chatContainer")
        self._chat_vlay = QVBoxLayout(self._chat_container)
        self._chat_vlay.setContentsMargins(2, 6, 2, 6)
        self._chat_vlay.setSpacing(6)
        self._chat_vlay.addStretch()   # pushes bubbles to bottom initially
        self._chat_scroll.setWidget(self._chat_container)
        lay.addWidget(self._chat_scroll, 1)

        # ── Input + button ────────────────────────────────────────────────────
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText(
            "Describe a model, or reply to refine it…\n"
            "e.g. \"a bike phone mount\" or \"make the clamp thicker\"")
        self.prompt_edit.setFixedHeight(84)
        lay.addWidget(self.prompt_edit)

        self.gen_btn = QPushButton("Generate Model")
        self.gen_btn.setObjectName("generateBtn")
        self.gen_btn.setFixedHeight(44)
        self.gen_btn.setCursor(Qt.PointingHandCursor)
        self.gen_btn.clicked.connect(self._generate)
        lay.addWidget(self.gen_btn)

        return page

    # ── Settings page ─────────────────────────────────────────────────────────

    def _build_settings_page(self):
        page = QWidget()
        lay  = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        lay.addWidget(label("AI Provider", "sectionLabel"))

        provider_row = QWidget()
        provider_row.setObjectName("providerRow")
        pr_lay = QHBoxLayout(provider_row)
        pr_lay.setContentsMargins(3, 3, 3, 3)
        pr_lay.setSpacing(2)

        self._providers = ["anthropic","openai","openrouter","azure","local"]
        self._prov_btns = []
        icons  = ["🟠","🟢","🟣","🔵","💻"]
        plabels = ["Anthropic","OpenAI","Router","Azure","Local"]
        for i, (ic, lb) in enumerate(zip(icons, plabels)):
            b = ProviderBtn(ic, lb)
            b.clicked.connect(lambda _, idx=i: self._select_provider(idx))
            pr_lay.addWidget(b, 1)
            self._prov_btns.append(b)
        lay.addWidget(provider_row)

        lay.addWidget(sep())
        lay.addWidget(label("API Settings", "sectionLabel"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self._settings_stack = QStackedWidget()
        pages_factories = [make_anthropic_page, make_openai_page,
                           make_openrouter_page, make_azure_page, make_local_page]
        self._field_maps = []
        for factory in pages_factories:
            pg, fields = factory()
            self._settings_stack.addWidget(pg)
            self._field_maps.append(fields)

        scroll.setWidget(self._settings_stack)
        lay.addWidget(scroll, 1)

        self._cur_provider = 0
        self._select_provider(0)
        return page

    # ── Chat helpers ──────────────────────────────────────────────────────────

    def _add_message(self, text: str, is_user: bool) -> "ChatBubble":
        """Append a bubble to the chat view; returns it so it can be updated."""
        bubble = ChatBubble(text, is_user)
        # Insert before the bottom stretch (last item)
        idx = self._chat_vlay.count() - 1
        self._chat_vlay.insertWidget(idx, bubble)
        # Auto-scroll to bottom
        QTimer.singleShot(30, lambda:
            self._chat_scroll.verticalScrollBar().setValue(
                self._chat_scroll.verticalScrollBar().maximum()))
        return bubble

    def _build_workspace(self):
        self.vsplit = QSplitter(Qt.Vertical)
        self.vsplit.setHandleWidth(1)

        # ── Viewport ──
        vp_wrap = QWidget()
        vp_lay  = QVBoxLayout(vp_wrap)
        vp_lay.setContentsMargins(0, 0, 0, 0)
        vp_lay.setSpacing(0)

        self.viewport = Viewport3D()
        vp_lay.addWidget(self.viewport)

        # Overlays on viewport
        self._vp_empty = QLabel("No model yet\nDescribe an object and click Generate")
        self._vp_empty.setObjectName("vpEmpty")
        self._vp_empty.setAlignment(Qt.AlignCenter)
        self._vp_empty.setAttribute(Qt.WA_TransparentForMouseEvents)

        self._vp_empty_sub = QLabel("")
        self._vp_empty_sub.setObjectName("vpEmptySub")
        self._vp_empty_sub.setAlignment(Qt.AlignCenter)
        self._vp_empty_sub.setAttribute(Qt.WA_TransparentForMouseEvents)

        self._vp_hint = QLabel("Left-drag to orbit  ·  Right-drag to pan  ·  Scroll to zoom")
        self._vp_hint.setObjectName("vpHint")
        self._vp_hint.setAlignment(Qt.AlignCenter)
        self._vp_hint.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._vp_hint.setVisible(False)

        self._status_badge = QLabel("")
        self._status_badge.setObjectName("statusBadge")
        self._status_badge.setVisible(False)

        # Viewport toolbar
        self._vp_toolbar = QWidget()
        tb_lay = QHBoxLayout(self._vp_toolbar)
        tb_lay.setContentsMargins(0, 0, 0, 0)
        tb_lay.setSpacing(6)
        self._btn_reset = self._vp_btn("⟲ Reset")
        self._btn_grid  = self._vp_btn("⊞ Grid",  checkable=True, checked=True)
        self._btn_wire  = self._vp_btn("⬡ Wire",  checkable=True)
        self._btn_reset.clicked.connect(self.viewport.reset_view)
        self._btn_grid.clicked.connect(self._toggle_grid)
        self._btn_wire.clicked.connect(self._toggle_wire)
        for b in (self._btn_reset, self._btn_grid, self._btn_wire):
            tb_lay.addWidget(b)
        self._vp_toolbar.setVisible(False)

        # Layout overlays inside the viewport using absolute positions
        # We put them via an overlay widget
        overlay = QWidget(vp_wrap)
        overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        overlay.setStyleSheet("background: transparent;")
        self._vp_overlay = overlay

        # Position overlays properly after show
        self.vsplit.addWidget(vp_wrap)

        # ── Code panel ──
        self._code_panel = self._build_code_panel()
        self.vsplit.addWidget(self._code_panel)

        self.vsplit.setSizes([560, 280])
        self.vsplit.setStretchFactor(0, 1)
        self.vsplit.setStretchFactor(1, 0)

        return self.vsplit

    def _vp_btn(self, text, checkable=False, checked=False):
        b = QPushButton(text)
        b.setCheckable(checkable)
        b.setChecked(checked)
        b.setStyleSheet("""
            QPushButton {
                background: rgba(12,12,20,0.80);
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 7px;
                color: rgba(235,235,245,0.65);
                padding: 5px 11px;
                font-size: 12px;
            }
            QPushButton:hover   { background: rgba(30,30,45,0.90); color: white; }
            QPushButton:checked { color: #0a84ff; border-color: rgba(10,132,255,0.35); }
        """)
        return b

    def _build_code_panel(self):
        panel = QWidget()
        panel.setObjectName("codePanel")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Code tab
        self.code_edit = QPlainTextEdit()
        self.code_edit.setReadOnly(True)
        self.code_edit.setObjectName("codeEdit")
        self.code_edit.setFont(QFont("Cascadia Code", 12) if QFont("Cascadia Code").exactMatch()
                               else QFont("Consolas", 12))
        self.code_edit.setPlaceholderText("Generated Python code will appear here…")
        PythonHL(self.code_edit.document())

        # Details tab
        self.details_edit = QPlainTextEdit()
        self.details_edit.setReadOnly(True)
        self.details_edit.setObjectName("codeEdit")
        self.details_edit.setPlaceholderText("Model details and design notes will appear here…")

        self.tabs.addTab(self.code_edit,    "Python Code")
        self.tabs.addTab(self.details_edit, "Details")
        lay.addWidget(self.tabs)

        # Bottom action bar
        bar = QWidget()
        bar.setObjectName("panelHeader")
        bar.setFixedHeight(40)
        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(12, 0, 12, 0)
        bar_lay.setSpacing(8)

        self.btn_copy    = self._action_btn("📋  Copy")
        self.btn_dl_stl2 = self._action_btn("↓ STL")
        self.btn_dl_py2  = self._action_btn("↓ .py")
        self.btn_copy.clicked.connect(self._copy_code)
        self.btn_dl_stl2.clicked.connect(lambda: self._download("stl"))
        self.btn_dl_py2.clicked.connect(lambda: self._download("py"))
        for b in (self.btn_copy, self.btn_dl_stl2, self.btn_dl_py2):
            bar_lay.addWidget(b)
            b.setVisible(False)

        bar_lay.addStretch()
        lay.addWidget(bar)
        return panel

    def _action_btn(self, text):
        b = QPushButton(text)
        b.setFixedHeight(28)
        b.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.07);
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 7px;
                color: rgba(235,235,245,0.65);
                padding: 0 12px;
                font-size: 12px;
            }
            QPushButton:hover  { background: rgba(255,255,255,0.12); color: white; }
            QPushButton:pressed{ background: rgba(255,255,255,0.05); }
        """)
        return b

    # ── Provider switching ────────────────────────────────────────────────────

    def _select_provider(self, idx):
        self._cur_provider = idx
        for i, b in enumerate(self._prov_btns):
            b.set_active(i == idx)
        self._settings_stack.setCurrentIndex(idx)

    # ── Viewport overlays (positioned after resize) ───────────────────────────

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._reposition_overlays()

    def showEvent(self, e):
        super().showEvent(e)
        QTimer.singleShot(50, self._reposition_overlays)

    def _reposition_overlays(self):
        vp = self.viewport
        if not vp.isVisible():
            return
        vp_global = vp.mapToGlobal(QPoint(0, 0))
        parent    = self.centralWidget()
        local     = parent.mapFromGlobal(vp_global)
        W, H      = vp.width(), vp.height()

        # Status badge — top-left of viewport
        self._status_badge.setParent(parent)
        self._status_badge.adjustSize()
        self._status_badge.move(local.x() + 14, local.y() + 14)
        self._status_badge.raise_()

        # Toolbar — top-right of viewport
        self._vp_toolbar.setParent(parent)
        self._vp_toolbar.adjustSize()
        tw = self._vp_toolbar.sizeHint().width()
        self._vp_toolbar.move(local.x() + W - tw - 12, local.y() + 12)
        self._vp_toolbar.raise_()

        # Empty state — centred
        self._vp_empty.setParent(parent)
        self._vp_empty.adjustSize()
        ew = self._vp_empty.sizeHint().width()
        eh = self._vp_empty.sizeHint().height()
        self._vp_empty.move(local.x() + (W-ew)//2, local.y() + (H-eh)//2 - 16)
        self._vp_empty.raise_()

        self._vp_empty_sub.setParent(parent)
        self._vp_empty_sub.adjustSize()
        sw = self._vp_empty_sub.sizeHint().width()
        self._vp_empty_sub.move(local.x() + (W-sw)//2, local.y() + (H)//2 + 12)
        self._vp_empty_sub.raise_()

        # Hint — bottom centre
        self._vp_hint.setParent(parent)
        self._vp_hint.adjustSize()
        hw = self._vp_hint.sizeHint().width()
        self._vp_hint.move(local.x() + (W-hw)//2, local.y() + H - 34)
        self._vp_hint.raise_()

        # Install toast — bottom-right of main window
        if hasattr(self, "_install_toast") and self._install_toast.isVisible():
            self._install_toast.adjustSize()
            tw = self._install_toast.width()
            th = self._install_toast.height()
            self._install_toast.move(self.width() - tw - 20, self.height() - th - 20)
            self._install_toast.raise_()

    # ── Generation ────────────────────────────────────────────────────────────

    def _get_settings(self):
        fmap = self._field_maps[self._cur_provider]
        out  = {}
        for key, widget in fmap.items():
            if isinstance(widget, QComboBox):
                out[key] = widget.currentText()
            else:
                out[key] = widget.text().strip()
        return out

    def _generate(self):
        if self._worker and self._worker.isRunning():
            return
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            self.prompt_edit.setFocus()
            return

        self._last_prompt = prompt
        self.prompt_edit.clear()

        # Add user bubble to chat
        self._add_message(prompt, is_user=True)
        # Add placeholder AI bubble (updated on response)
        self._ai_bubble = self._add_message("Generating…  ⏳", is_user=False)

        self.gen_btn.setEnabled(False)
        self.gen_btn.setText("Generating…")
        self._set_status("Thinking…", "")
        # Switch to Chat tab so the user sees activity
        self._switch_sidebar(0)

        self._worker = Worker(prompt, self._providers[self._cur_provider],
                              self._get_settings(), list(self._history))
        self._worker.done.connect(self._on_result)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_result(self, data):
        self._result = data
        self.gen_btn.setEnabled(True)
        self.gen_btn.setText("Generate Model")

        # ── Update conversation history ───────────────────────────────────────
        ai_reply = data.get("ai_reply") or data.get("explanation","")
        self._history.append({"role": "user",      "content": self._last_prompt})
        self._history.append({"role": "assistant",  "content": ai_reply})
        # Keep last 10 turns (20 messages) to avoid very long context
        if len(self._history) > 20:
            self._history = self._history[-20:]

        # ── Update AI chat bubble ─────────────────────────────────────────────
        explanation = (data.get("explanation") or "").strip()
        if self._ai_bubble:
            if data.get("ok"):
                snippet = explanation[:180] + ("…" if len(explanation) > 180 else "")
                self._ai_bubble.set_text(
                    f"✅ Model ready  ({data.get('faces',0):,} faces)\n\n{snippet}" if snippet
                    else f"✅ Model ready  ({data.get('faces',0):,} faces)")
            else:
                err_short = (data.get("error_msg","")).splitlines()[-1][:90]
                self._ai_bubble.set_text(f"❌ Failed\n{err_short}")

        # ── Title bar ────────────────────────────────────────────────────────
        words = self._last_prompt.split()
        sub   = "— " + " ".join(words[:5]) + ("…" if len(words) > 5 else "")
        self.titlebar.set_subtitle(sub)

        # ── Code / Details panels ─────────────────────────────────────────────
        self.code_edit.setPlainText(data.get("code",""))

        details  = f"Model ID : {data.get('model_id','')}\n"
        details += f"Faces    : {data.get('faces',0):,}\n"
        details += f"Provider : {self._providers[self._cur_provider]}\n"
        details += f"Status   : {'✅ Ready' if data.get('ok') else '❌ Failed'}\n"
        details += "\n" + explanation
        if not data.get("ok"):
            details += "\n\nError:\n" + (data.get("error_msg",""))
        self.details_edit.setPlainText(details)

        # ── Action buttons ────────────────────────────────────────────────────
        has_stl = data.get("ok") and data.get("stl_path")
        for b in (self.btn_copy, self.btn_dl_py2):
            b.setVisible(True)
        self.btn_dl_stl2.setVisible(bool(has_stl))
        self.titlebar.btn_dl_py.setVisible(True)
        self.titlebar.btn_dl_stl.setVisible(bool(has_stl))

        # ── Viewport ──────────────────────────────────────────────────────────
        if has_stl:
            self._set_status(f"✅  {data['faces']:,} faces", "ok")
            self._vp_empty.setVisible(False)
            self._vp_empty_sub.setVisible(False)
            self._vp_hint.setVisible(True)
            self._vp_toolbar.setVisible(True)
            self.viewport.load_stl(data["stl_path"])
        else:
            err = (data.get("error_msg") or "Generation failed").split("\n")[-1]
            self._set_status(f"⚠  {err[:60]}", "err")
            self._vp_empty.setText("Generation failed")
            self._vp_empty_sub.setText(err[:80])

        self._reposition_overlays()

    def _on_error(self, msg):
        self.gen_btn.setEnabled(True)
        self.gen_btn.setText("Generate Model")
        self._set_status(f"❌  {msg[:80]}", "err")
        self._vp_empty.setText("Error")
        self._vp_empty_sub.setText(msg[:100])
        if self._ai_bubble:
            self._ai_bubble.set_text(f"❌ Error\n{msg[:120]}")
        self._reposition_overlays()

    def _set_status(self, text, state):
        self._status_badge.setText(text)
        self._status_badge.setProperty("state", state)
        self._status_badge.style().unpolish(self._status_badge)
        self._status_badge.style().polish(self._status_badge)
        self._status_badge.adjustSize()
        self._status_badge.setVisible(bool(text))
        self._reposition_overlays()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _copy_code(self):
        QApplication.clipboard().setText(self.code_edit.toPlainText())
        self.btn_copy.setText("✅  Copied")
        QTimer.singleShot(2000, lambda: self.btn_copy.setText("📋  Copy"))

    def _download(self, kind):
        if not self._result:
            return
        if kind == "stl":
            src = self._result.get("stl_path")
            ext, ft = "stl", "STL Files (*.stl)"
        else:
            src = self._result.get("py_path")
            ext, ft = "py",  "Python Files (*.py)"
        if not src or not Path(src).exists():
            return
        dest, _ = QFileDialog.getSaveFileName(
            self, f"Save .{ext}", f"forge3d_model.{ext}", ft)
        if dest:
            Path(dest).write_bytes(Path(src).read_bytes())

    def _toggle_grid(self):
        on = self.viewport.toggle_grid()
        self._btn_grid.setChecked(on)

    def _toggle_wire(self):
        on = self.viewport.toggle_wireframe()
        self._btn_wire.setChecked(on)

    # ── Settings persistence ──────────────────────────────────────────────────

    def _load_settings(self):
        providers = ["anthropic","openai","openrouter","azure","local"]
        defaults  = {
            "anthropic/api_key":"","anthropic/model":"claude-sonnet-4-6",
            "openai/api_key":"","openai/model":"gpt-4o",
            "openrouter/api_key":"","openrouter/model":"anthropic/claude-3.5-sonnet",
            "azure/api_key":"","azure/endpoint":"","azure/deployment":"gpt-5-chat","azure/api_version":"2025-01-01-preview",
            "local/base_url":"http://localhost:11434","local/model":"llama3.2",
        }
        for i, prov in enumerate(providers):
            fmap = self._field_maps[i]
            for key, widget in fmap.items():
                val = self._qsettings.value(f"{prov}/{key}", defaults.get(f"{prov}/{key}",""))
                if isinstance(widget, QComboBox):
                    idx = widget.findText(val)
                    if idx >= 0: widget.setCurrentIndex(idx)
                else:
                    widget.setText(val)

        cur = int(self._qsettings.value("current_provider", 0))
        self._select_provider(cur)

    def _save_settings(self):
        providers = ["anthropic","openai","openrouter","azure","local"]
        for i, prov in enumerate(providers):
            for key, widget in self._field_maps[i].items():
                val = widget.currentText() if isinstance(widget, QComboBox) else widget.text()
                self._qsettings.setValue(f"{prov}/{key}", val)
        self._qsettings.setValue("current_provider", self._cur_provider)

    # ── Install-toast API (called from main.py) ───────────────────────────────

    def show_install_toast(self):
        self._install_toast.setVisible(True)
        self._reposition_overlays()

    def update_install_toast(self, progress: int, text: str):
        self._install_toast.set_progress(progress, text)
        self._reposition_overlays()

    def finish_install_toast(self):
        self._install_toast.set_done()
        QTimer.singleShot(3500, lambda: self._install_toast.setVisible(False))

    def error_install_toast(self, msg: str):
        self._install_toast.set_error(msg)

    # ─────────────────────────────────────────────────────────────────────────

    def closeEvent(self, e):
        self._save_settings()
        super().closeEvent(e)
