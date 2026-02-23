"""
ui/styles.py — Premium dark dashboard stylesheet for Job Market Intelligence System.

Design language: Refined dark intelligence dashboard.
  • Charcoal/slate base with electric blue + amber accent system
  • Card-based layout with subtle depth shadows
  • Crisp typography with clear visual hierarchy
  • Smooth hover/focus transitions throughout
  • Color-coded stat indicators (green = good, amber = warning)
"""

STYLESHEET = """

/* ── Root / Window ────────────────────────────────────────────────────────── */
QMainWindow, QDialog {
    background-color: #0a0f1e;
}

QWidget {
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", sans-serif;
    font-size: 13px;
    color: #e2e8f0;
    background-color: transparent;
}

/* ── Tab Bar ──────────────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: none;
    background-color: #0f172a;
    padding: 0px;
}

QTabBar {
    background-color: #0a0f1e;
}

QTabBar::tab {
    background-color: transparent;
    color: #64748b;
    padding: 12px 24px;
    margin-right: 2px;
    border-bottom: 3px solid transparent;
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

QTabBar::tab:selected {
    color: #38bdf8;
    border-bottom: 3px solid #38bdf8;
    background-color: rgba(56, 189, 248, 0.05);
}

QTabBar::tab:hover:!selected {
    color: #94a3b8;
    background-color: rgba(255,255,255,0.03);
}

/* ── Group Box (used as cards) ────────────────────────────────────────────── */
QGroupBox {
    background-color: #131c30;
    border: 1px solid #1e2d45;
    border-radius: 12px;
    margin-top: 14px;
    padding: 16px 14px 12px 14px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: #475569;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    top: -1px;
    padding: 2px 10px;
    background-color: #131c30;
    color: #38bdf8;
    border-radius: 4px;
    font-size: 10px;
    letter-spacing: 1.2px;
}

/* ── Buttons ──────────────────────────────────────────────────────────────── */
QPushButton {
    background-color: #1e293b;
    color: #94a3b8;
    border: 1px solid #2d3f55;
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 600;
    font-size: 12px;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #243347;
    color: #e2e8f0;
    border-color: #38bdf8;
}

QPushButton:pressed {
    background-color: #1a2540;
    border-color: #0ea5e9;
}

QPushButton:disabled {
    background-color: #111827;
    color: #374151;
    border-color: #1f2937;
}

/* Primary — Fetch All */
QPushButton#fetchAllBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0ea5e9, stop:0.5 #3b82f6, stop:1 #6366f1);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 14px 28px;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.3px;
    min-height: 20px;
}

QPushButton#fetchAllBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #38bdf8, stop:0.5 #60a5fa, stop:1 #818cf8);
}

QPushButton#fetchAllBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0284c7, stop:0.5 #2563eb, stop:1 #4f46e5);
}

/* Analyse/Sort action buttons */
QPushButton#analyzeBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #059669, stop:1 #10b981);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 22px;
    font-weight: 700;
}

QPushButton#analyzeBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #10b981, stop:1 #34d399);
}

/* Compare button */
QPushButton#compareBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #d97706, stop:1 #f59e0b);
    color: #000000;
    border: none;
    border-radius: 8px;
    padding: 10px 22px;
    font-weight: 700;
}

QPushButton#compareBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #f59e0b, stop:1 #fbbf24);
}

/* Sort / secondary action button */
QPushButton#sortBtn {
    background-color: #1e3a5f;
    color: #93c5fd;
    border: 1px solid #1d4ed8;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton#sortBtn:hover {
    background-color: #1d4b7a;
    color: #bfdbfe;
    border-color: #3b82f6;
}

QPushButton#sortBtn:pressed {
    background-color: #1e3a8a;
}

/* Pause / Resume / Stop */
QPushButton#pauseBtn {
    background-color: #1e3a4a;
    color: #38bdf8;
    border: 1px solid #1d4ed8;
}
QPushButton#pauseBtn:hover { background-color: #1d4b61; }

QPushButton#resumeBtn {
    background-color: #14372a;
    color: #34d399;
    border: 1px solid #065f46;
}
QPushButton#resumeBtn:hover { background-color: #1a4a38; }

QPushButton#stopBtn {
    background-color: #3b1a1a;
    color: #f87171;
    border: 1px solid #7f1d1d;
}
QPushButton#stopBtn:hover { background-color: #4c2020; }

/* ── Inputs ───────────────────────────────────────────────────────────────── */
QLineEdit {
    background-color: #0f172a;
    color: #f1f5f9;
    border: 1.5px solid #1e2d45;
    border-radius: 8px;
    padding: 9px 13px;
    font-size: 13px;
    selection-background-color: #1d4ed8;
}

QLineEdit:focus {
    border-color: #38bdf8;
    background-color: #0d1929;
}

QLineEdit:hover:!focus {
    border-color: #334155;
}

/* ── ComboBox ─────────────────────────────────────────────────────────────── */
QComboBox {
    background-color: #0f172a;
    color: #f1f5f9;
    border: 1.5px solid #1e2d45;
    border-radius: 8px;
    padding: 9px 13px;
    font-size: 13px;
    min-width: 130px;
}

QComboBox:hover   { border-color: #334155; }
QComboBox:focus   { border-color: #38bdf8; }

QComboBox::drop-down {
    border: none;
    width: 28px;
}

QComboBox::down-arrow {
    width: 10px;
    height: 10px;
}

QComboBox QAbstractItemView {
    background-color: #131c30;
    color: #f1f5f9;
    border: 1px solid #1e2d45;
    border-radius: 8px;
    padding: 4px;
    selection-background-color: #1d4ed8;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 8px 12px;
    border-radius: 4px;
    min-height: 28px;
}

/* ── Labels ───────────────────────────────────────────────────────────────── */
QLabel {
    color: #94a3b8;
    font-size: 13px;
}

QLabel#sectionTitle {
    color: #f1f5f9;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.3px;
}

QLabel#statValue {
    color: #38bdf8;
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -1px;
}

QLabel#statLabel {
    color: #475569;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

QLabel#statusGood  { color: #34d399; font-weight: 600; font-size: 12px; }
QLabel#statusWarn  { color: #f59e0b; font-weight: 600; font-size: 12px; }
QLabel#statusInfo  { color: #38bdf8; font-weight: 600; font-size: 12px; }
QLabel#timeLabel   { color: #818cf8; font-weight: 700; font-size: 13px; }
QLabel#resultLabel { color: #fbbf24; font-weight: 700; font-size: 13px; }

/* ── Table ────────────────────────────────────────────────────────────────── */
QTableWidget {
    background-color: #0f172a;
    alternate-background-color: #111827;
    color: #e2e8f0;
    gridline-color: #1e2d45;
    border: 1px solid #1e2d45;
    border-radius: 10px;
    font-size: 12px;
    selection-background-color: #1d4ed8;
    selection-color: #ffffff;
    outline: none;
}

QTableWidget::item {
    padding: 8px 10px;
    border: none;
}

QTableWidget::item:selected {
    background-color: #1e3a8a;
    color: #ffffff;
}

QTableWidget::item:hover:!selected {
    background-color: rgba(56, 189, 248, 0.07);
}

QHeaderView::section {
    background-color: #0d1929;
    color: #38bdf8;
    padding: 11px 10px;
    border: none;
    border-right: 1px solid #1e2d45;
    border-bottom: 2px solid #1e3a8a;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

QHeaderView::section:first  { border-top-left-radius: 10px; }
QHeaderView::section:last   { border-top-right-radius: 10px; border-right: none; }

/* ── Checkbox ─────────────────────────────────────────────────────────────── */
QCheckBox {
    color: #94a3b8;
    font-size: 12px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px; height: 18px;
    border-radius: 5px;
    border: 2px solid #334155;
    background-color: #0f172a;
}

QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #2563eb;
}

QCheckBox::indicator:hover {
    border-color: #38bdf8;
}

/* ── Status Bar ───────────────────────────────────────────────────────────── */
QStatusBar {
    background-color: #080d1a;
    color: #475569;
    border-top: 1px solid #1e2d45;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 500;
}

QStatusBar::item { border: none; }

/* ── Scrollbars ───────────────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: #0a0f1e;
    width: 8px;
    border-radius: 4px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #1e2d45;
    border-radius: 4px;
    min-height: 32px;
}

QScrollBar::handle:vertical:hover { background: #334155; }

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: #0a0f1e;
    height: 8px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #1e2d45;
    border-radius: 4px;
    min-width: 32px;
}

QScrollBar::handle:horizontal:hover { background: #334155; }

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal { width: 0; }

/* ── Progress / Message dialogs ───────────────────────────────────────────── */
QMessageBox {
    background-color: #131c30;
    color: #e2e8f0;
}

QMessageBox QLabel { color: #e2e8f0; font-size: 13px; }

QMessageBox QPushButton {
    min-width: 90px;
    padding: 8px 20px;
}

/* ── Splitter ─────────────────────────────────────────────────────────────── */
QSplitter::handle {
    background-color: #1e2d45;
    height: 1px;
}

/* ── Tooltip ──────────────────────────────────────────────────────────────── */
QToolTip {
    background-color: #131c30;
    color: #e2e8f0;
    border: 1px solid #38bdf8;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}
"""