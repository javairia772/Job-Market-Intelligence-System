"""
ui/main_window.py — Job Market Intelligence System
====================================================
Full redesign implementing all UX suggestions:

  TAB 1  Job Listings
         • 4 stat cards (total, remote, onsite, salary coverage)
         • Source breakdown donut + posted-date bar chart (auto-loaded)
         • Empty state with prominent CTA when no data
         • Compact single-row toolbar (fetch + sort in one band)
         • Job detail side-panel on row click
         • Keyboard shortcuts: Ctrl+R fetch, Ctrl+F focus filter, Ctrl+E export
         • Window title shows live job count

  TAB 2  Skill Analyzer
         • Charts primary, table secondary (collapsible bottom)
         • Horizontal bar with % labels + colour gradient
         • Subtitle shows "N jobs analysed"

  TAB 3  Salary & Experience
         • 3 hero stat cards (avg, min, max + salary coverage %)
         • Salary histogram instead of role avg (more useful)
         • Experience pie + role-avg bar side-by-side

  TAB 4  Filter & Export
         • Live result count updates as you type (textChanged)
         • Filtered salary mini-chart preview
         • Export button distinct colour, CSV + JSON options

  TAB 5  Performance Analytics
         • "Auto-benchmark ALL algorithms" one-click button
         • Winner highlighted, losers dimmed
         • Radar / spider chart for multi-algorithm comparison
"""

import os
import json
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QTabWidget,
    QComboBox, QLabel, QLineEdit, QMessageBox, QFileDialog,
    QStatusBar, QCheckBox, QGroupBox, QFrame, QScrollArea,
    QSizePolicy, QProgressBar, QSplitter, QStackedWidget,
    QTextEdit, QDialog, QDialogButtonBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut, QColor, QBrush
import warnings
import matplotlib
matplotlib.use("Agg")
warnings.filterwarnings("ignore", message="Glyph.*missing from font")
from matplotlib.figure import Figure
import numpy as np

from sorting.sorting_algorithms import sort_jobs
from database.db_manager        import DatabaseManager
from analysis.skill_analyzer    import top_skills
from analysis.salary_experience import (
    average_salary_by_role, experience_distribution,
)
from ui.chart_widget    import ChartCanvas
from analysis.filter_search  import filter_jobs
from analysis.export_reports import export_to_csv
from ui.workers         import UnifiedFetchWorker
from config.constants   import APP_NAME, SALARY_CURRENCY, NOT_SPECIFIED
from ui.styles          import STYLESHEET

try:
    import analysis.performance_tracker as perf_tracker
    _PERF_AVAILABLE = True
except Exception:
    perf_tracker    = None
    _PERF_AVAILABLE = False

ALGORITHMS = ["Quick Sort", "Merge Sort", "Bubble Sort", "Tim Sort"]
COLUMNS    = ["ID", "Title", "Company", "Location",
              "Salary", "Experience", "Skills", "Job Type", "Posted Date"]

# Cohesive palette: electric cyan primary, amber accent, emerald positive, rose negative
_C = {
    "primary":  "#22d3ee",   # electric cyan
    "accent":   "#f59e0b",   # amber
    "green":    "#10b981",   # emerald
    "red":      "#f43f5e",   # rose
    "purple":   "#a78bfa",   # lavender
    "blue":     "#3b82f6",   # blue
    "muted":    "#334155",
    "text":     "#e2e8f0",
    "subtext":  "#64748b",
    "bg":       "#0a0f1e",
    "card":     "#111827",
    "border":   "#1e293b",
}
_PALETTE = [_C["primary"], _C["accent"], _C["green"], _C["red"], _C["purple"], _C["blue"]]


# ─────────────────────────────────────────────────────────────────────────────
#  Small reusable widgets
# ─────────────────────────────────────────────────────────────────────────────

def _scrollable(w: QWidget) -> QScrollArea:
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setFrameShape(QFrame.Shape.NoFrame)
    sa.setWidget(w)
    sa.setStyleSheet("QScrollArea{background:transparent;border:none;}")
    return sa


def _hline() -> QFrame:
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("QFrame{color:#1e293b;margin:2px 0;}")
    return f


def _lbl(text: str, style: str = "") -> QLabel:
    l = QLabel(text)
    if style: l.setStyleSheet(style)
    return l


class _StatCard(QWidget):
    """Hero metric card: big coloured number + label + optional sublabel."""
    def __init__(self, label: str, value="—", sub: str = "",
                 color: str = _C["primary"], parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(96)
        self.setStyleSheet(f"""
            _StatCard, QWidget {{
                background: {_C['card']};
                border: 1px solid {_C['border']};
                border-radius: 14px;
            }}
        """)
        lay = QVBoxLayout(self); lay.setContentsMargins(18,12,18,12); lay.setSpacing(2)
        self._v = QLabel(str(value))
        self._v.setStyleSheet(f"color:{color};font-size:28px;font-weight:800;"
                              f"background:transparent;border:none;")
        self._l = QLabel(label.upper())
        self._l.setStyleSheet("color:#475569;font-size:10px;font-weight:700;"
                              "letter-spacing:1.2px;background:transparent;border:none;")
        self._s = QLabel(sub)
        self._s.setStyleSheet("color:#334155;font-size:10px;"
                              "background:transparent;border:none;")
        lay.addWidget(self._v); lay.addWidget(self._l)
        if sub: lay.addWidget(self._s)

    def update(self, value: str, sub: str = ""):
        self._v.setText(value)
        if sub: self._s.setText(sub)


class _EmptyState(QWidget):
    """Shown in place of table when no data is loaded."""
    fetch_clicked = None   # set externally

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self); lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(16)

        icon = QLabel("📊")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size:56px;background:transparent;border:none;")

        title = QLabel("No job data loaded yet")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color:#e2e8f0;font-size:20px;font-weight:700;"
                            "background:transparent;border:none;")

        sub = QLabel("Enter a role and location above, then click Fetch All Sources\n"
                     "to pull jobs from Indeed, Remotive, RemoteOK and Adzuna.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)
        sub.setStyleSheet("color:#475569;font-size:13px;line-height:1.6;"
                          "background:transparent;border:none;")

        self.btn = QPushButton("🚀   Fetch All Sources Now")
        self.btn.setObjectName("fetchAllBtn")
        self.btn.setFixedWidth(260); self.btn.setFixedHeight(46)

        lay.addStretch(); lay.addWidget(icon); lay.addWidget(title)
        lay.addWidget(sub); lay.addWidget(self.btn, 0, Qt.AlignmentFlag.AlignCenter)
        lay.addStretch()


# ─────────────────────────────────────────────────────────────────────────────
#  Main Window
# ─────────────────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setGeometry(100, 60, 1380, 860)
        self.setMinimumSize(1080, 680)
        self.setStyleSheet(STYLESHEET)

        self.db             = DatabaseManager()
        self._active_worker = None
        self._current_jobs: list = []   # cached for detail panel

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self._build_job_tab()
        self._build_skill_tab()
        self._build_salary_tab()
        self._build_filter_tab()
        self._build_performance_tab()

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        self._setup_shortcuts()

        # 30-second stat refresh
        QTimer(self, timeout=self._refresh_stats).start(30_000)

        # initial data load
        self._reload_all()

    # ──────────────────────────────────────────────────────────────────────────
    #  Keyboard shortcuts
    # ──────────────────────────────────────────────────────────────────────────

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self._fetch_all)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=lambda: (
            self.tabs.setCurrentIndex(3), self.f_role.setFocus()
        ))
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self._export_jobs)

    # ──────────────────────────────────────────────────────────────────────────
    #  Shared helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _status(self, msg: str = ""):
        if msg:
            self._status_bar.showMessage(msg); return
        try:
            counts = self.db.get_source_counts()
            total  = sum(counts.values())
            title  = f"{APP_NAME}  —  {total:,} jobs" if total else APP_NAME
            self.setWindowTitle(title)
            if total == 0:
                self._status_bar.showMessage(
                    "No data loaded · Ctrl+R to fetch  ·  Ctrl+F to filter  ·  Ctrl+E to export")
            else:
                parts = "  ·  ".join(f"{s.capitalize()}: {n:,}" for s, n in counts.items())
                self._status_bar.showMessage(
                    f"  {total:,} jobs  ·  {parts}"
                    f"  ·  Ctrl+R fetch  ·  Ctrl+F filter  ·  Ctrl+E export")
        except Exception:
            self._status_bar.showMessage("Ready")

    def _fmt(self, job: tuple, col: int) -> str:
        if col >= len(job): return NOT_SPECIFIED
        v = job[col]
        if v is None or (isinstance(v, str) and not v.strip()): return NOT_SPECIFIED
        if col == 4:   # salary
            try:
                n = int(float(v))
                return f"{n:,} {SALARY_CURRENCY}" if n > 0 else NOT_SPECIFIED
            except: return NOT_SPECIFIED
        s = str(v).strip()
        return NOT_SPECIFIED if s.lower() in ("n/a","na","none","null","not specified") else s

    def _fill_table(self, table: QTableWidget, jobs: list):
        table.setUpdatesEnabled(False)
        table.setSortingEnabled(False)
        table.setRowCount(len(jobs))
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            "ID","Title","Company","Location",
            f"Salary ({SALARY_CURRENCY})","Experience","Skills","Job Type","Posted",
        ])
        for r, job in enumerate(jobs):
            for c in range(9):
                text = self._fmt(job, c) if c < len(job) else NOT_SPECIFIED
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                # colour-code salary cells
                if c == 4 and text != NOT_SPECIFIED:
                    try:
                        n = int(text.replace(",","").split()[0])
                        if n >= 100_000: item.setForeground(QBrush(QColor(_C["green"])))
                        elif n >= 60_000: item.setForeground(QBrush(QColor(_C["accent"])))
                    except: pass
                table.setItem(r, c, item)
        table.setSortingEnabled(True)
        table.setUpdatesEnabled(True)

        # pin column widths
        hdr = table.horizontalHeader()
        hdr.setDefaultSectionSize(120)
        table.setColumnWidth(0, 50)   # ID
        table.setColumnWidth(1, 200)  # Title
        table.setColumnWidth(2, 140)  # Company
        table.setColumnWidth(3, 120)  # Location
        table.setColumnWidth(4, 120)  # Salary
        table.setColumnWidth(5, 100)  # Experience
        table.setColumnWidth(6, 180)  # Skills
        table.setColumnWidth(7, 90)   # Job Type
        hdr.setStretchLastSection(True)

    def _dark_fig(self, figsize=(7, 3.5)) -> Figure:
        fig = Figure(figsize=figsize, dpi=100)
        fig.patch.set_facecolor(_C["bg"])
        return fig

    def _ax(self, fig: Figure) -> object:
        ax = fig.add_subplot(111)
        ax.set_facecolor(_C["card"])
        ax.tick_params(colors=_C["subtext"], labelsize=9)
        ax.xaxis.label.set_color(_C["subtext"])
        ax.yaxis.label.set_color(_C["subtext"])
        ax.title.set_color(_C["text"]); ax.title.set_fontsize(11); ax.title.set_fontweight("bold")
        for sp in ax.spines.values(): sp.set_edgecolor(_C["border"])
        return ax

    def _reload_all(self):
        """Reload tables + charts from DB — called after fetch and on startup."""
        jobs = self.db.fetch_all_jobs()
        self._current_jobs = jobs
        self._refresh_stats()
        self._refresh_status_charts()
        if jobs:
            self._show_job_table()
            self._fill_table(self.job_table, jobs)
        else:
            self._show_empty_state()
        self._do_skill_analysis()
        self._do_salary_analysis()
        self._status()

    def _refresh_stats(self):
        try:
            counts = self.db.get_source_counts()
            total  = sum(counts.values())
            remote = counts.get("remoteok", 0) + counts.get("remotive", 0)
            onsite = counts.get("adzuna", 0) + counts.get("indeed", 0)
            jobs   = self.db.fetch_all_jobs()
            with_sal = sum(1 for j in jobs if j[4] and str(j[4]).strip() not in ("0",""))
            pct_sal  = f"{with_sal/total*100:.0f}% have salary" if total else "—"
            self._card_total.update(f"{total:,}")
            self._card_remote.update(f"{remote:,}")
            self._card_onsite.update(f"{onsite:,}")
            self._card_salary.update(f"{with_sal:,}", pct_sal)
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────────────
    #  Worker wiring
    # ──────────────────────────────────────────────────────────────────────────

    def _set_loading(self, on: bool):
        self.fetch_btn.setEnabled(not on)
        if hasattr(self, "_empty_fetch_btn"):
            self._empty_fetch_btn.setEnabled(not on)
        self.pause_btn.setEnabled(on)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(on)
        self.fetch_progress.setVisible(on)
        self.fetch_progress.setRange(0, 0) if on else (
            self.fetch_progress.setRange(0, 1), self.fetch_progress.setValue(1))

    def _on_pause(self):
        if self._active_worker:
            self._active_worker.pause()
            self.pause_btn.setEnabled(False); self.resume_btn.setEnabled(True)

    def _on_resume(self):
        if self._active_worker:
            self._active_worker.resume()
            self.pause_btn.setEnabled(True); self.resume_btn.setEnabled(False)

    def _on_stop(self):
        if self._active_worker: self._active_worker.stop()

    def _start_worker(self, worker):
        self._active_worker = worker
        self._set_loading(True)
        self.worker_lbl.setText("⏳  Starting…")
        worker.progress.connect(lambda m: (self.worker_lbl.setText(m), self._status(m)))
        worker.finished.connect(self._on_finished)
        worker.start()

    def _on_finished(self, total: int, counts: dict, errors: list):
        self._set_loading(False)
        self._active_worker = None
        src = "\n".join(f"  • {s.capitalize()}: {n:,}" for s, n in counts.items() if n > 0)
        if errors and total == 0:
            self.worker_lbl.setText("⚠  Failed")
            QMessageBox.warning(self, "Fetch failed", "No jobs loaded.\n\n" + "\n".join(errors))
        elif errors:
            self.worker_lbl.setText(f"⚠  Partial — {total:,} jobs")
            QMessageBox.warning(self, "Partial success",
                f"{total:,} jobs loaded:\n{src}\n\nErrors:\n" +
                "\n".join(f"  • {e}" for e in errors))
        else:
            self.worker_lbl.setText(f"✅  {total:,} jobs loaded")
            note = ("\n\nℹ  Adzuna skipped (no API key). Set ADZUNA_APP_ID + ADZUNA_APP_KEY."
                    if counts.get("adzuna", 0) == 0 else "")
            QMessageBox.information(self, "Done ✓", f"{total:,} jobs loaded:\n{src}{note}")
        self._reload_all()

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 1 — JOB LISTINGS
    # ══════════════════════════════════════════════════════════════════════════

    def _build_job_tab(self):
        outer = QWidget()
        layout = QVBoxLayout(outer); layout.setSpacing(8); layout.setContentsMargins(12,10,12,8)

        # ── STAT CARDS ────────────────────────────────────────────────────────
        card_row = QHBoxLayout(); card_row.setSpacing(10)
        self._card_total  = _StatCard("Total Jobs",       "—", color=_C["primary"])
        self._card_remote = _StatCard("Remote Jobs",      "—", color=_C["green"])
        self._card_onsite = _StatCard("Onsite / Hybrid",  "—", color=_C["accent"])
        self._card_salary = _StatCard("Salary Data",      "—", color=_C["purple"])
        for c in (self._card_total, self._card_remote, self._card_onsite, self._card_salary):
            card_row.addWidget(c)
        layout.addLayout(card_row)

        # ── SOURCE + DATE CHARTS (auto-loaded, always visible) ────────────────
        charts_row = QHBoxLayout(); charts_row.setSpacing(10)

        self._src_chart_box = QGroupBox("Job Sources")
        sl = QVBoxLayout(self._src_chart_box)
        self._src_chart = ChartCanvas(self._src_chart_box)
        self._src_chart.setMinimumHeight(200)
        sl.addWidget(self._src_chart)
        charts_row.addWidget(self._src_chart_box, 1)

        self._date_chart_box = QGroupBox("Jobs Posted (Last 14 Days)")
        dl = QVBoxLayout(self._date_chart_box)
        self._date_chart = ChartCanvas(self._date_chart_box)
        self._date_chart.setMinimumHeight(200)
        dl.addWidget(self._date_chart)
        charts_row.addWidget(self._date_chart_box, 2)

        layout.addLayout(charts_row)

        # ── CONTROLS (two clean rows — no overflow) ───────────────────────────
        toolbar = QGroupBox("Controls")
        toolbar_lay = QVBoxLayout(toolbar)
        toolbar_lay.setSpacing(6)
        toolbar_lay.setContentsMargins(10, 10, 10, 8)

        # ── ROW 1: Fetch ──────────────────────────────────────────────────────
        fetch_row = QHBoxLayout(); fetch_row.setSpacing(8)

        self.role_input = QLineEdit()
        self.role_input.setPlaceholderText("e.g. Python Developer  (for Indeed & Adzuna)")
        self.role_input.setToolTip(
            "Job role / keyword used by Indeed and Adzuna scrapers.\n"
            "Remotive and RemoteOK fetch ALL remote jobs regardless of this field.\n"
            "Leave blank to use the default 'developer' search.")

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("e.g. Pakistan  (for Indeed & Adzuna only)")
        self.location_input.setToolTip(
            "Location filter used by Indeed and Adzuna scrapers.\n"
            "Remotive and RemoteOK are global remote-only — location is ignored for them.\n"
            "Leave blank to search all locations.")

        self.replace_cb = QCheckBox("Replace data")
        self.replace_cb.setChecked(True)
        self.replace_cb.setToolTip(
            "Checked: clear existing jobs from DB before fetching (fresh load).\n"
            "Unchecked: append new jobs to existing data (keeps old records).")

        self.fetch_btn = QPushButton("🚀  Fetch All Sources")
        self.fetch_btn.setObjectName("fetchAllBtn")
        self.fetch_btn.setFixedHeight(36)
        self.fetch_btn.setFixedWidth(200)
        self.fetch_btn.clicked.connect(self._fetch_all)
        self.fetch_btn.setToolTip(
            "Ctrl+R  ·  Fetches from all 4 sources:\n"
            "  • Remotive  — remote jobs, no key needed\n"
            "  • RemoteOK  — remote jobs, no key needed\n"
            "  • Indeed    — uses Role + Location above\n"
            "  • Adzuna    — uses Role + Location (needs API key)\n\n"
            "Role and Location only affect Indeed and Adzuna results."
        )

        # pause / resume / stop — compact icon buttons, only active during fetch
        self.pause_btn  = QPushButton("⏸"); self.pause_btn.setObjectName("pauseBtn")
        self.resume_btn = QPushButton("▶"); self.resume_btn.setObjectName("resumeBtn")
        self.stop_btn   = QPushButton("⏹"); self.stop_btn.setObjectName("stopBtn")
        for b in (self.pause_btn, self.resume_btn, self.stop_btn):
            b.setFixedSize(32, 32); b.setEnabled(False)
        self.pause_btn.clicked.connect(self._on_pause)
        self.resume_btn.clicked.connect(self._on_resume)
        self.stop_btn.clicked.connect(self._on_stop)

        self.fetch_progress = QProgressBar()
        self.fetch_progress.setFixedHeight(6)
        self.fetch_progress.setFixedWidth(80)
        self.fetch_progress.setTextVisible(False)
        self.fetch_progress.setVisible(False)
        self.fetch_progress.setStyleSheet(
            "QProgressBar{background:#1e293b;border-radius:3px;border:none;}"
            "QProgressBar::chunk{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #22d3ee,stop:1 #6366f1);border-radius:3px;}")

        self.worker_lbl = QLabel("Ready  ·  Ctrl+R to fetch")
        self.worker_lbl.setStyleSheet(f"color:{_C['subtext']};font-size:11px;")
        self.worker_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        fetch_row.addWidget(_lbl("Role (Indeed/Adzuna):", f"color:{_C['subtext']};font-size:11px;font-weight:600;"))
        fetch_row.addWidget(self.role_input, 3)
        fetch_row.addWidget(_lbl("Location (Indeed/Adzuna):", f"color:{_C['subtext']};font-size:11px;font-weight:600;"))
        fetch_row.addWidget(self.location_input, 3)
        fetch_row.addWidget(self.replace_cb)
        fetch_row.addWidget(self.fetch_btn)
        fetch_row.addWidget(self.pause_btn)
        fetch_row.addWidget(self.resume_btn)
        fetch_row.addWidget(self.stop_btn)
        fetch_row.addWidget(self.fetch_progress)
        fetch_row.addWidget(self.worker_lbl, 1)
        toolbar_lay.addLayout(fetch_row)

        # ── divider ───────────────────────────────────────────────────────────
        toolbar_lay.addWidget(_hline())

        # ── ROW 2: Sort ───────────────────────────────────────────────────────
        sort_row = QHBoxLayout(); sort_row.setSpacing(8)

        self.col_sel = QComboBox(); self.col_sel.addItems(COLUMNS)
        self.col_sel.setFixedWidth(130)
        self.alg_sel = QComboBox(); self.alg_sel.addItems(ALGORITHMS)
        self.alg_sel.setFixedWidth(130)

        self.sort_btn = QPushButton("↕  Sort")
        self.sort_btn.setObjectName("sortBtn")
        self.sort_btn.setFixedWidth(90)
        self.sort_btn.setFixedHeight(32)
        self.sort_btn.clicked.connect(self._sort_data)

        self.time_lbl = QLabel("—")
        self.time_lbl.setStyleSheet(
            f"color:{_C['purple']};font-weight:700;font-size:12px;min-width:80px;")

        sort_row.addWidget(_lbl("Sort by:", f"color:{_C['subtext']};font-size:11px;font-weight:600;"))
        sort_row.addWidget(self.col_sel)
        sort_row.addWidget(_lbl("Algorithm:", f"color:{_C['subtext']};font-size:11px;font-weight:600;"))
        sort_row.addWidget(self.alg_sel)
        sort_row.addWidget(self.sort_btn)
        sort_row.addWidget(_lbl("⏱  Time:", f"color:{_C['subtext']};font-size:11px;"))
        sort_row.addWidget(self.time_lbl)
        sort_row.addStretch()

        # Adzuna key status — small inline badge, not an alarming banner
        has_adzuna = bool(os.environ.get("ADZUNA_APP_ID") and os.environ.get("ADZUNA_APP_KEY"))
        az_badge = QLabel("✅ Adzuna" if has_adzuna else "ℹ️ Adzuna: key not set")
        az_badge.setStyleSheet(
            f"color:{'#10b981' if has_adzuna else '#475569'};"
            f"font-size:10px;padding:2px 6px;"
            f"background:{'#0d2e22' if has_adzuna else '#1e293b'};"
            f"border-radius:4px;border:1px solid {'#065f46' if has_adzuna else '#334155'};")
        az_badge.setToolTip(
            "Adzuna API key detected — onsite & hybrid jobs will be fetched." if has_adzuna
            else "Adzuna API key not set.\n"
                 "Only remote jobs (Remotive + RemoteOK) will load.\n"
                 "To include onsite/hybrid jobs, set environment variables:\n"
                 "  ADZUNA_APP_ID=your_id\n"
                 "  ADZUNA_APP_KEY=your_key\n"
                 "Free keys available at: developer.adzuna.com"
        )
        sort_row.addWidget(az_badge)
        toolbar_lay.addLayout(sort_row)

        layout.addWidget(toolbar)

        # ── JOB TABLE + DETAIL PANEL ──────────────────────────────────────────
        table_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Stacked: empty state OR job table
        self._table_stack = QStackedWidget()

        self._empty_widget = _EmptyState()
        self._empty_widget.btn.clicked.connect(self._fetch_all)
        self._empty_fetch_btn = self._empty_widget.btn
        self._table_stack.addWidget(self._empty_widget)   # index 0

        self.job_table = QTableWidget()
        self.job_table.setAlternatingRowColors(True)
        self.job_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.job_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.job_table.setSortingEnabled(True)
        self.job_table.verticalHeader().setVisible(False)
        self.job_table.verticalHeader().setDefaultSectionSize(34)
        self.job_table.setWordWrap(False)
        self.job_table.itemSelectionChanged.connect(self._on_row_selected)
        self._table_stack.addWidget(self.job_table)       # index 1
        table_splitter.addWidget(self._table_stack)

        # detail panel (right side)
        self._detail_panel = self._build_detail_panel()
        self._detail_panel.setVisible(False)
        table_splitter.addWidget(self._detail_panel)
        table_splitter.setSizes([900, 380])

        layout.addWidget(table_splitter, 1)
        self.tabs.addTab(outer, "  Job Listings  ")

    def _build_detail_panel(self) -> QWidget:
        """Right-side job detail panel shown when a row is clicked."""
        panel = QWidget()
        panel.setFixedWidth(370)
        panel.setStyleSheet(f"background:{_C['card']};border-left:1px solid {_C['border']};")
        lay = QVBoxLayout(panel); lay.setContentsMargins(16,16,16,16); lay.setSpacing(10)

        close_row = QHBoxLayout()
        hdr = QLabel("Job Details")
        hdr.setStyleSheet(f"color:{_C['text']};font-size:15px;font-weight:700;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28,28)
        close_btn.setStyleSheet("QPushButton{background:#1e293b;color:#64748b;border:none;"
                                "border-radius:6px;font-size:13px;}"
                                "QPushButton:hover{color:#e2e8f0;background:#334155;}")
        close_btn.clicked.connect(lambda: self._detail_panel.setVisible(False))
        close_row.addWidget(hdr); close_row.addStretch(); close_row.addWidget(close_btn)
        lay.addLayout(close_row)
        lay.addWidget(_hline())

        self._detail_title   = QLabel("—")
        self._detail_title.setWordWrap(True)
        self._detail_title.setStyleSheet(f"color:{_C['primary']};font-size:15px;"
                                         f"font-weight:700;border:none;background:transparent;")

        self._detail_company = QLabel("—")
        self._detail_company.setStyleSheet(f"color:{_C['text']};font-size:13px;font-weight:600;"
                                           f"border:none;background:transparent;")

        self._detail_loc     = QLabel("—")
        self._detail_loc.setStyleSheet(f"color:{_C['subtext']};font-size:12px;"
                                       f"border:none;background:transparent;")

        self._detail_salary  = QLabel("—")
        self._detail_salary.setStyleSheet(f"color:{_C['green']};font-size:18px;"
                                          f"font-weight:800;border:none;background:transparent;")

        self._detail_exp     = QLabel("—")
        self._detail_exp.setStyleSheet(f"color:{_C['accent']};font-size:12px;font-weight:600;"
                                       f"border:none;background:transparent;")

        self._detail_type    = QLabel("—")
        self._detail_type.setStyleSheet(f"color:{_C['subtext']};font-size:12px;"
                                        f"border:none;background:transparent;")

        self._detail_posted  = QLabel("—")
        self._detail_posted.setStyleSheet(f"color:{_C['subtext']};font-size:11px;"
                                          f"border:none;background:transparent;")

        self._detail_skills  = QTextEdit()
        self._detail_skills.setReadOnly(True)
        self._detail_skills.setFixedHeight(120)
        self._detail_skills.setStyleSheet(
            f"background:#0a0f1e;color:{_C['text']};border:1px solid {_C['border']};"
            f"border-radius:8px;padding:8px;font-size:12px;")

        for w in (self._detail_title, self._detail_company, self._detail_loc,
                  self._detail_salary, self._detail_exp, self._detail_type,
                  self._detail_posted):
            w.setWordWrap(True)

        def _field(label: str, widget: QWidget):
            lbl = QLabel(label.upper())
            lbl.setStyleSheet(f"color:{_C['subtext']};font-size:10px;font-weight:700;"
                              f"letter-spacing:1px;border:none;background:transparent;")
            lay.addWidget(lbl); lay.addWidget(widget)

        lay.addWidget(self._detail_title)
        lay.addWidget(self._detail_company)
        lay.addWidget(self._detail_loc)
        lay.addWidget(_hline())
        _field("Annual Salary", self._detail_salary)
        _field("Experience",    self._detail_exp)
        _field("Job Type",      self._detail_type)
        _field("Posted",        self._detail_posted)
        _field("Skills",        self._detail_skills)
        lay.addStretch()
        return panel

    def _show_empty_state(self):
        self._table_stack.setCurrentIndex(0)
        self._detail_panel.setVisible(False)

    def _show_job_table(self):
        self._table_stack.setCurrentIndex(1)

    def _on_row_selected(self):
        rows = self.job_table.selectedItems()
        if not rows: return
        row = self.job_table.currentRow()
        if row < 0 or row >= len(self._current_jobs): return
        job = self._current_jobs[row]

        def _g(col): return self._fmt(job, col)

        self._detail_title.setText(_g(1))
        self._detail_company.setText(_g(2))
        self._detail_loc.setText(f"📍  {_g(3)}")
        sal = _g(4)
        self._detail_salary.setText(sal if sal != NOT_SPECIFIED else "Not disclosed")
        self._detail_salary.setStyleSheet(
            f"color:{'#10b981' if sal != NOT_SPECIFIED else '#334155'};"
            f"font-size:18px;font-weight:800;border:none;background:transparent;")
        self._detail_exp.setText(f"🎯  {_g(5)}")
        self._detail_type.setText(f"💼  {_g(7)}")
        self._detail_posted.setText(f"🗓  Posted: {_g(8)}")

        skills_raw = _g(6)
        if skills_raw and skills_raw != NOT_SPECIFIED:
            skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
            self._detail_skills.setText("\n".join(f"• {s}" for s in skills))
        else:
            self._detail_skills.setText("No skills data")

        self._detail_panel.setVisible(True)

    def _fetch_all(self):
        self._start_worker(UnifiedFetchWorker(
            role         = self.role_input.text().strip()     or "developer",
            location     = self.location_input.text().strip() or "",
            clear_before = self.replace_cb.isChecked(),
        ))

    def _sort_data(self):
        if not self._current_jobs:
            QMessageBox.information(self, "No data", "Load jobs first."); return
        col, alg = self.col_sel.currentText(), self.alg_sel.currentText()
        sorted_jobs, t = sort_jobs(self._current_jobs, col, alg)
        ms = round(t * 1000, 3)
        self._current_jobs = sorted_jobs
        self._show_job_table()
        self._fill_table(self.job_table, sorted_jobs)
        self.time_lbl.setText(f"{ms} ms")
        if _PERF_AVAILABLE:
            perf_tracker.record(alg, col, ms, len(sorted_jobs))
            self._refresh_perf()

    def _refresh_status_charts(self):
        """Source donut + date bar — auto-loaded after every fetch."""
        jobs = self.db.fetch_all_jobs()
        counts = self.db.get_source_counts()
        total  = sum(counts.values())

        # ── source donut ──────────────────────────────────────────────────────
        if total > 0:
            fig = self._dark_fig((3.2, 2.2))
            ax  = fig.add_subplot(111)
            ax.set_facecolor(_C["bg"]); fig.patch.set_facecolor(_C["bg"])
            labels = [k.capitalize() for k, v in counts.items() if v > 0]
            sizes  = [v for v in counts.values() if v > 0]
            colors = _PALETTE[:len(labels)]
            wedges, _, autotexts = ax.pie(
                sizes, labels=None, colors=colors,
                autopct="%1.0f%%", startangle=90,
                wedgeprops={"linewidth": 2, "edgecolor": _C["bg"]},
                pctdistance=0.75,
            )
            for at in autotexts:
                at.set_color("white"); at.set_fontsize(8); at.set_fontweight("bold")
            ax.legend(labels, loc="lower center", ncol=2, frameon=False,
                      fontsize=8, labelcolor="#94a3b8",
                      bbox_to_anchor=(0.5, -0.18))
            ax.set_title(f"Sources  ·  {total:,} total",
                         color=_C["text"], fontsize=10, fontweight="bold", pad=8)
            fig.tight_layout(pad=0.5)
            self._src_chart.set_figure(fig)
        else:
            self._src_chart.set_figure(None)

        # ── date bar ──────────────────────────────────────────────────────────
        if jobs:
            from collections import Counter
            import re as _re
            dates = Counter()
            for j in jobs:
                d = str(j[8]).strip() if len(j) > 8 else ""
                if _re.match(r"\d{4}-\d{2}-\d{2}", d):
                    dates[d[:10]] += 1
            top14 = sorted(dates.items())[-14:]
            if top14:
                fig2 = self._dark_fig((5.5, 2.2))
                ax2  = self._ax(fig2)
                xs   = [x[0][-5:] for x in top14]  # MM-DD
                ys   = [x[1] for x in top14]
                bars = ax2.bar(xs, ys, color=_C["primary"], alpha=0.85, width=0.7)
                ax2.set_title("Posted Dates", fontsize=10, pad=6)
                ax2.yaxis.grid(True, color=_C["border"], linewidth=0.6, linestyle="--")
                ax2.set_axisbelow(True)
                for lbl in ax2.get_xticklabels():
                    lbl.set_rotation(35); lbl.set_ha("right"); lbl.set_fontsize(7)
                fig2.tight_layout(pad=0.8)
                self._date_chart.set_figure(fig2)
            else:
                self._date_chart.set_figure(None)
        else:
            self._date_chart.set_figure(None)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 2 — SKILL ANALYZER  (charts primary, table secondary)
    # ══════════════════════════════════════════════════════════════════════════

    def _build_skill_tab(self):
        outer = QWidget()
        lay = QVBoxLayout(outer); lay.setSpacing(8); lay.setContentsMargins(12,10,12,8)

        hdr = QHBoxLayout()
        t = QLabel("Top In-Demand Skills")
        t.setStyleSheet(f"color:{_C['text']};font-size:18px;font-weight:700;")
        self._skill_sub = QLabel("")
        self._skill_sub.setStyleSheet(f"color:{_C['subtext']};font-size:12px;")
        btn = QPushButton("⟳  Refresh"); btn.setObjectName("sortBtn")
        btn.setFixedWidth(110); btn.clicked.connect(self._do_skill_analysis)
        hdr.addWidget(t); hdr.addWidget(self._skill_sub); hdr.addStretch(); hdr.addWidget(btn)
        lay.addLayout(hdr); lay.addWidget(_hline())

        # CHART is primary — takes 65% of height
        cg = QGroupBox("Skill Demand  (top 15)")
        cl = QVBoxLayout(cg)
        self.skill_chart = ChartCanvas(cg); self.skill_chart.setMinimumHeight(340)
        cl.addWidget(self.skill_chart)
        lay.addWidget(cg, 3)

        # TABLE is secondary — takes 35%, scrollable
        tg = QGroupBox("Ranking Table")
        tl2 = QVBoxLayout(tg)
        self.skill_table = QTableWidget()
        self.skill_table.setAlternatingRowColors(True)
        self.skill_table.verticalHeader().setVisible(False)
        self.skill_table.setMaximumHeight(200)
        self.skill_table.horizontalHeader().setStretchLastSection(True)
        tl2.addWidget(self.skill_table)
        lay.addWidget(tg, 1)

        self.tabs.addTab(outer, "  Skill Analyzer  ")

    def _do_skill_analysis(self):
        jobs = self.db.fetch_all_jobs()
        if not jobs:
            self._empty_table(self.skill_table, ["Skill","Count","% Jobs"])
            self.skill_chart.set_figure(None); return

        skill_list = top_skills(jobs, top_n=15)
        total = len(jobs)
        self._skill_sub.setText(f"·  {total:,} jobs analysed")

        # TABLE
        self.skill_table.setRowCount(len(skill_list))
        self.skill_table.setColumnCount(3)
        self.skill_table.setHorizontalHeaderLabels(["Skill","Job Count","% of Jobs"])
        for i, (sk, cnt) in enumerate(skill_list):
            for j, v in enumerate((sk, str(cnt), f"{cnt/total*100:.1f}%")):
                item = QTableWidgetItem(v); item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.skill_table.setItem(i, j, item)

        # CHART — horizontal bar with colour gradient
        fig = self._dark_fig((8, 5.5))
        ax  = self._ax(fig)
        names = [s for s, _ in skill_list][::-1]
        vals  = [c for _, c in skill_list][::-1]
        # gradient colours dark→bright
        norm_vals = [v / max(vals) for v in vals]
        bar_cols  = [self._lerp_color("#1e3a8a", _C["primary"], n) for n in norm_vals]
        bars = ax.barh(names, vals, color=bar_cols, height=0.62, alpha=0.95)
        for bar, val, pct in zip(bars, vals, [v/total*100 for v in vals[::-1]][::-1]):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    f"{val}  ({pct:.1f}%)", va="center", ha="left",
                    fontsize=8.5, color="#94a3b8")
        ax.set_xlabel("Number of Job Listings", labelpad=8)
        ax.set_title(f"Top 15 In-Demand Skills  ·  {total:,} jobs analysed",
                     pad=12, fontsize=12)
        ax.xaxis.grid(True, color=_C["border"], linewidth=0.7, linestyle="--")
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        fig.tight_layout(pad=1.5)
        self.skill_chart.set_figure(fig)

    @staticmethod
    def _lerp_color(c1: str, c2: str, t: float) -> str:
        """Linearly interpolate between two hex colours."""
        def hx(c): return tuple(int(c.lstrip("#")[i:i+2], 16) for i in (0,2,4))
        r1,g1,b1 = hx(c1); r2,g2,b2 = hx(c2)
        r,g,b = int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _empty_table(self, table: QTableWidget, headers: list):
        table.setRowCount(1); table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        item = QTableWidgetItem("No data loaded — fetch jobs first")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        table.setItem(0, 0, item)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 3 — SALARY & EXPERIENCE
    # ══════════════════════════════════════════════════════════════════════════

    def _build_salary_tab(self):
        outer = QWidget()
        lay = QVBoxLayout(outer); lay.setSpacing(8); lay.setContentsMargins(12,10,12,8)

        hdr = QHBoxLayout()
        t = QLabel("Salary & Experience Analysis")
        t.setStyleSheet(f"color:{_C['text']};font-size:18px;font-weight:700;")
        btn = QPushButton("⟳  Refresh"); btn.setObjectName("sortBtn")
        btn.setFixedWidth(110); btn.clicked.connect(self._do_salary_analysis)
        hdr.addWidget(t); hdr.addStretch(); hdr.addWidget(btn)
        lay.addLayout(hdr); lay.addWidget(_hline())

        # hero stat cards
        sc_row = QHBoxLayout(); sc_row.setSpacing(10)
        self._sal_avg = _StatCard("Avg Salary",         "—", color=_C["green"])
        self._sal_min = _StatCard("Min Salary",         "—", color=_C["accent"])
        self._sal_max = _StatCard("Max Salary",         "—", color=_C["primary"])
        self._sal_cov = _StatCard("Jobs w/ Salary Data","—", color=_C["purple"])
        for c in (self._sal_avg, self._sal_min, self._sal_max, self._sal_cov):
            sc_row.addWidget(c)
        lay.addLayout(sc_row)

        # charts primary
        sp = QSplitter(Qt.Orientation.Horizontal)

        sg = QGroupBox("Salary Distribution")
        sl = QVBoxLayout(sg)
        self.salary_chart = ChartCanvas(sg); self.salary_chart.setMinimumHeight(280)
        sl.addWidget(self.salary_chart)
        sp.addWidget(sg)

        eg = QGroupBox("Experience & Role Breakdown")
        el = QVBoxLayout(eg)
        self.exp_chart = ChartCanvas(eg); self.exp_chart.setMinimumHeight(280)
        el.addWidget(self.exp_chart)
        sp.addWidget(eg)
        sp.setSizes([600, 600])
        lay.addWidget(sp, 2)

        # tables secondary
        tp = QSplitter(Qt.Orientation.Horizontal)
        stg = QGroupBox("Role Salary Table")
        stl = QVBoxLayout(stg)
        self.salary_table = QTableWidget(); self.salary_table.setAlternatingRowColors(True)
        self.salary_table.verticalHeader().setVisible(False)
        self.salary_table.setMaximumHeight(180)
        self.salary_table.horizontalHeader().setStretchLastSection(True)
        stl.addWidget(self.salary_table); tp.addWidget(stg)

        etg = QGroupBox("Experience Table")
        etl = QVBoxLayout(etg)
        self.exp_table = QTableWidget(); self.exp_table.setAlternatingRowColors(True)
        self.exp_table.verticalHeader().setVisible(False)
        self.exp_table.setMaximumHeight(180)
        self.exp_table.horizontalHeader().setStretchLastSection(True)
        etl.addWidget(self.exp_table); tp.addWidget(etg)
        tp.setSizes([600, 600])
        lay.addWidget(tp, 1)

        self.tabs.addTab(_scrollable(outer), "  Salary & Experience  ")

    def _do_salary_analysis(self):
        jobs = self.db.fetch_all_jobs()
        if not jobs:
            for t in (self.salary_table, self.exp_table):
                self._empty_table(t, ["—"])
            self.salary_chart.set_figure(None); self.exp_chart.set_figure(None)
            return

        # salary stats
        salaries = []
        for j in jobs:
            try:
                v = int(float(j[4]))
                if 1000 < v < 2_000_000: salaries.append(v)
            except: pass
        pct_cov = f"{len(salaries)/len(jobs)*100:.0f}%"

        if salaries:
            self._sal_avg.update(f"${sum(salaries)/len(salaries):,.0f}", pct_cov)
            self._sal_min.update(f"${min(salaries):,.0f}")
            self._sal_max.update(f"${max(salaries):,.0f}")
            self._sal_cov.update(f"{len(salaries):,}", pct_cov + " of jobs")
        else:
            for c in (self._sal_avg, self._sal_min, self._sal_max, self._sal_cov):
                c.update("N/A")

        # salary histogram
        if salaries:
            fig = self._dark_fig((6, 3.5))
            ax  = self._ax(fig)
            buckets = [s // 20000 * 20000 for s in salaries]
            from collections import Counter
            cnt = Counter(buckets)
            xs  = sorted(cnt.keys())
            ys  = [cnt[x] for x in xs]
            lbls= [f"${x//1000}k" for x in xs]
            bars = ax.bar(range(len(xs)), ys, color=_C["green"], alpha=0.85, width=0.75)
            for bar, val in zip(bars, ys):
                if val > 0:
                    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.2,
                            str(val), ha="center", fontsize=8, color="#94a3b8")
            ax.set_xticks(range(len(xs))); ax.set_xticklabels(lbls, rotation=35, ha="right")
            ax.set_xlabel("Salary Range"); ax.set_ylabel("Job Count")
            ax.set_title(f"Salary Distribution  ·  {len(salaries):,} jobs with data  ·  {pct_cov} coverage",
                         pad=10, fontsize=10)
            ax.yaxis.grid(True, color=_C["border"], linewidth=0.6, linestyle="--")
            ax.set_axisbelow(True)
            ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
            fig.tight_layout(pad=1.4)
            self.salary_chart.set_figure(fig)
        else:
            self.salary_chart.set_figure(None)

        # role table
        avg_sal = average_salary_by_role(jobs)
        self.salary_table.setRowCount(len(avg_sal))
        self.salary_table.setColumnCount(2)
        self.salary_table.setHorizontalHeaderLabels(["Role", f"Avg ({SALARY_CURRENCY})"])
        for i, (role, sal) in enumerate(avg_sal.items()):
            for j, v in enumerate((role or NOT_SPECIFIED, f"{sal:,.0f}")):
                item = QTableWidgetItem(v); item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.salary_table.setItem(i, j, item)

        # experience split chart (pie left + bar right using subplot)
        exp_dist = experience_distribution(jobs)
        if exp_dist:
            fig2 = self._dark_fig((6, 3.5))
            ax2  = fig2.add_subplot(121)
            ax2b = fig2.add_subplot(122)
            for ax_ in (ax2, ax2b):
                ax_.set_facecolor(_C["card"])
                ax_.tick_params(colors=_C["subtext"], labelsize=8)
                for sp in ax_.spines.values(): sp.set_edgecolor(_C["border"])
            fig2.patch.set_facecolor(_C["bg"])

            labels = list(exp_dist.keys()); vals = list(exp_dist.values())
            colors = _PALETTE[:len(labels)]
            wedges, _, auts = ax2.pie(vals, labels=None, colors=colors, autopct="%1.0f%%",
                                      startangle=90, pctdistance=0.7,
                                      wedgeprops={"linewidth":2,"edgecolor":_C["bg"]})
            for at in auts: at.set_color("white"); at.set_fontsize(8)
            ax2.set_title("Experience Split", color=_C["text"], fontsize=9, pad=8)
            ax2.legend(labels, loc="lower center", ncol=1, frameon=False,
                       fontsize=7, labelcolor="#94a3b8", bbox_to_anchor=(0.5, -0.25))

            bars2 = ax2b.bar(labels, vals, color=colors, width=0.55, alpha=0.9)
            for bar, val in zip(bars2, vals):
                ax2b.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.2,
                          str(val), ha="center", fontsize=8, color="#94a3b8")
            ax2b.set_ylabel("Count"); ax2b.set_title("Experience Levels", color=_C["text"], fontsize=9, pad=8)
            ax2b.yaxis.grid(True, color=_C["border"], linewidth=0.6, linestyle="--"); ax2b.set_axisbelow(True)
            ax2b.tick_params(axis="x", rotation=20)
            ax2b.xaxis.label.set_color(_C["subtext"]); ax2b.yaxis.label.set_color(_C["subtext"])
            ax2b.spines["top"].set_visible(False); ax2b.spines["right"].set_visible(False)
            fig2.tight_layout(pad=1.2)
            self.exp_chart.set_figure(fig2)

        # exp table
        exp_dist = experience_distribution(jobs)
        self.exp_table.setRowCount(len(exp_dist))
        self.exp_table.setColumnCount(2)
        self.exp_table.setHorizontalHeaderLabels(["Experience", "Count"])
        for i, (exp, cnt) in enumerate(exp_dist.items()):
            for j, v in enumerate((exp, str(cnt))):
                item = QTableWidgetItem(v); item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.exp_table.setItem(i, j, item)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 4 — FILTER & EXPORT  (live count + salary preview)
    # ══════════════════════════════════════════════════════════════════════════

    def _build_filter_tab(self):
        outer = QWidget()
        lay = QVBoxLayout(outer); lay.setSpacing(8); lay.setContentsMargins(12,10,12,8)

        t = QLabel("Filter & Export Jobs")
        t.setStyleSheet(f"color:{_C['text']};font-size:18px;font-weight:700;")
        lay.addWidget(t); lay.addWidget(_hline())

        fg = QGroupBox("Filter Criteria  ·  results update as you type")
        fl = QVBoxLayout(fg); fl.setSpacing(8)

        r1 = QHBoxLayout(); r1.setSpacing(10)
        self.f_role = QLineEdit(); self.f_role.setPlaceholderText("Role / Title  (e.g. Python)")
        self.f_loc  = QLineEdit(); self.f_loc.setPlaceholderText("Location  (e.g. USA, Remote)")
        r1.addWidget(_lbl("Role:", f"color:{_C['subtext']};font-size:11px;font-weight:600;"))
        r1.addWidget(self.f_role, 2)
        r1.addWidget(_lbl("Location:", f"color:{_C['subtext']};font-size:11px;font-weight:600;"))
        r1.addWidget(self.f_loc, 2); fl.addLayout(r1)

        r2 = QHBoxLayout(); r2.setSpacing(10)
        self.f_min = QLineEdit(); self.f_min.setPlaceholderText("Min Salary  (e.g. 50000)")
        self.f_max = QLineEdit(); self.f_max.setPlaceholderText("Max Salary  (e.g. 200000)")
        self.f_exp = QLineEdit(); self.f_exp.setPlaceholderText("Experience  (e.g. 3+ years)")
        r2.addWidget(_lbl("Min $:", f"color:{_C['subtext']};font-size:11px;font-weight:600;"))
        r2.addWidget(self.f_min)
        r2.addWidget(_lbl("Max $:", f"color:{_C['subtext']};font-size:11px;font-weight:600;"))
        r2.addWidget(self.f_max)
        r2.addWidget(_lbl("Exp:", f"color:{_C['subtext']};font-size:11px;font-weight:600;"))
        r2.addWidget(self.f_exp); fl.addLayout(r2)

        br = QHBoxLayout()
        self.filter_btn = QPushButton("🔍  Apply Filter"); self.filter_btn.setObjectName("sortBtn")
        self.filter_btn.setFixedWidth(140); self.filter_btn.clicked.connect(self._apply_filter)
        self.clear_btn  = QPushButton("✕  Clear");        self.clear_btn.setFixedWidth(80)
        self.clear_btn.clicked.connect(self._clear_filters)
        self.export_csv_btn  = QPushButton("⬇  Export CSV");  self.export_csv_btn.setObjectName("compareBtn")
        self.export_json_btn = QPushButton("⬇  Export JSON"); self.export_json_btn.setObjectName("compareBtn")
        self.export_csv_btn.setFixedWidth(130); self.export_json_btn.setFixedWidth(140)
        self.export_csv_btn.clicked.connect(self._export_jobs)
        self.export_json_btn.clicked.connect(self._export_json)
        self.filter_count_lbl = QLabel("")
        self.filter_count_lbl.setStyleSheet(f"color:{_C['primary']};font-size:12px;font-weight:600;")
        br.addWidget(self.filter_btn); br.addWidget(self.clear_btn)
        br.addWidget(self.filter_count_lbl, 1)
        br.addWidget(self.export_csv_btn); br.addWidget(self.export_json_btn)
        fl.addLayout(br); lay.addWidget(fg)

        # live update on every keypress
        for w in (self.f_role, self.f_loc, self.f_min, self.f_max, self.f_exp):
            w.textChanged.connect(self._apply_filter)

        # split: table + salary mini-chart
        sp = QSplitter(Qt.Orientation.Horizontal)

        self.filtered_table = QTableWidget()
        self.filtered_table.setAlternatingRowColors(True)
        self.filtered_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.filtered_table.verticalHeader().setVisible(False)
        self.filtered_table.horizontalHeader().setStretchLastSection(True)
        sp.addWidget(self.filtered_table)

        preview_box = QGroupBox("Salary Preview  (filtered set)")
        pbl = QVBoxLayout(preview_box)
        self._filter_chart = ChartCanvas(preview_box); self._filter_chart.setMinimumHeight(220)
        pbl.addWidget(self._filter_chart)
        sp.addWidget(preview_box)
        sp.setSizes([800, 400])
        lay.addWidget(sp, 1)

        self.tabs.addTab(outer, "  Filter & Export  ")

    def _apply_filter(self):
        filtered = filter_jobs(
            self.db.fetch_all_jobs(),
            role=self.f_role.text().strip(), location=self.f_loc.text().strip(),
            min_salary=self.f_min.text().strip(), max_salary=self.f_max.text().strip(),
            experience=self.f_exp.text().strip(),
        )
        self.filtered_table.setRowCount(len(filtered))
        self.filtered_table.setColumnCount(6)
        self.filtered_table.setHorizontalHeaderLabels(
            ["ID","Role","Company","Location",f"Salary ({SALARY_CURRENCY})","Experience"])
        for i, job in enumerate(filtered):
            for j in range(6):
                item = QTableWidgetItem(self._fmt(job,j) if j<len(job) else NOT_SPECIFIED)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.filtered_table.setItem(i, j, item)
        n = len(filtered)
        self.filter_count_lbl.setText(
            f"  {n:,} jobs match" if n else "  No jobs match current filters")

        # salary mini-chart for filtered set
        sals = []
        for j in filtered:
            try:
                v = int(float(j[4]))
                if v > 1000: sals.append(v)
            except: pass
        if sals:
            fig = self._dark_fig((4, 3))
            ax  = self._ax(fig)
            from collections import Counter
            buckets = Counter(s // 20000 * 20000 for s in sals)
            xs = sorted(buckets.keys())
            ax.bar(range(len(xs)), [buckets[x] for x in xs], color=_C["accent"], alpha=0.85)
            ax.set_xticks(range(len(xs)))
            ax.set_xticklabels([f"${x//1000}k" for x in xs], rotation=35, ha="right", fontsize=7)
            ax.set_title(f"Filtered Salary  ·  {len(sals):,} have data", fontsize=9, pad=6)
            ax.yaxis.grid(True, color=_C["border"], linewidth=0.5, linestyle="--")
            ax.set_axisbelow(True)
            fig.tight_layout(pad=1.2)
            self._filter_chart.set_figure(fig)
        else:
            self._filter_chart.set_figure(None)

        self._filtered_data = filtered   # for export

    def _clear_filters(self):
        for w in (self.f_role, self.f_loc, self.f_min, self.f_max, self.f_exp): w.clear()

    def _export_jobs(self):
        data = getattr(self, "_filtered_data", [])
        if not data:
            QMessageBox.warning(self, "Nothing to export", "Filter jobs first."); return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "jobs_export.csv", "CSV (*.csv);;All Files (*)")
        if not path: return
        rows = [[self._fmt(j, c) for c in range(6)] for j in data]
        try:
            export_to_csv(rows, filename=path)
            QMessageBox.information(self, "Exported ✓", f"Saved {len(rows):,} rows to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export failed", str(e))

    def _export_json(self):
        data = getattr(self, "_filtered_data", [])
        if not data:
            QMessageBox.warning(self, "Nothing to export", "Filter jobs first."); return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export JSON", "jobs_export.json", "JSON (*.json);;All Files (*)")
        if not path: return
        keys = ["id","title","company","location","salary","experience","skills","job_type","posted"]
        out  = [{keys[i]: self._fmt(job, i) for i in range(min(9, len(job)))} for job in data]
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Exported ✓", f"Saved {len(out):,} records to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export failed", str(e))

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 5 — PERFORMANCE ANALYTICS  (auto-benchmark)
    # ══════════════════════════════════════════════════════════════════════════

    def _build_performance_tab(self):
        outer = QWidget()
        lay = QVBoxLayout(outer); lay.setSpacing(8); lay.setContentsMargins(12,10,12,8)

        hdr = QHBoxLayout()
        t = QLabel("Sorting Performance Analytics")
        t.setStyleSheet(f"color:{_C['text']};font-size:18px;font-weight:700;")
        ref_btn = QPushButton("⟳  Refresh"); ref_btn.setFixedWidth(100); ref_btn.clicked.connect(self._refresh_perf)
        clr_btn = QPushButton("🗑  Clear");   clr_btn.setFixedWidth(80);  clr_btn.clicked.connect(self._clear_perf)
        hdr.addWidget(t); hdr.addStretch(); hdr.addWidget(ref_btn); hdr.addWidget(clr_btn)
        lay.addLayout(hdr); lay.addWidget(_hline())

        # ── COMPARISON card ───────────────────────────────────────────────────
        cg = QGroupBox("⚡  Algorithm Comparison")
        cl = QVBoxLayout(cg)

        cfg = QHBoxLayout(); cfg.setSpacing(10)
        self.cmp_col  = QComboBox(); self.cmp_col.addItems(COLUMNS); self.cmp_col.setFixedWidth(130)
        self.cmp_alg1 = QComboBox(); self.cmp_alg1.addItems(ALGORITHMS); self.cmp_alg1.setFixedWidth(130)
        self.cmp_alg2 = QComboBox(); self.cmp_alg2.addItems(ALGORITHMS); self.cmp_alg2.setCurrentIndex(1); self.cmp_alg2.setFixedWidth(130)
        cmp_run = QPushButton("▶  Compare 2"); cmp_run.setObjectName("compareBtn"); cmp_run.setFixedWidth(130); cmp_run.clicked.connect(self._run_comparison)
        bench_all = QPushButton("🏆  Benchmark ALL 4"); bench_all.setObjectName("fetchAllBtn"); bench_all.setFixedHeight(36); bench_all.setFixedWidth(170); bench_all.clicked.connect(self._benchmark_all)
        self.cmp_result = QLabel("")
        self.cmp_result.setStyleSheet(f"color:{_C['accent']};font-weight:700;font-size:13px;")
        for w, lbl in ((self.cmp_col,"Column:"),(self.cmp_alg1,"Alg 1:"),(self.cmp_alg2,"Alg 2:")):
            cfg.addWidget(_lbl(lbl, f"color:{_C['subtext']};font-size:11px;font-weight:600;"))
            cfg.addWidget(w)
        cfg.addWidget(cmp_run); cfg.addWidget(bench_all); cfg.addStretch()
        cl.addLayout(cfg); cl.addWidget(self.cmp_result)

        self.cmp_chart = ChartCanvas(cg); self.cmp_chart.setMinimumHeight(230)
        cl.addWidget(self.cmp_chart); lay.addWidget(cg)

        # ── history + avg side by side ────────────────────────────────────────
        sp = QSplitter(Qt.Orientation.Horizontal)

        hg = QGroupBox("Sort History  (newest first)")
        hl = QVBoxLayout(hg)
        self.perf_table = QTableWidget(); self.perf_table.setAlternatingRowColors(True)
        self.perf_table.verticalHeader().setVisible(False); self.perf_table.setMaximumHeight(200)
        hl.addWidget(self.perf_table); sp.addWidget(hg)

        ag = QGroupBox("Avg Time per Algorithm")
        al = QVBoxLayout(ag)
        self.avg_chart = ChartCanvas(ag); self.avg_chart.setMinimumHeight(200)
        al.addWidget(self.avg_chart); sp.addWidget(ag)
        sp.setSizes([550, 550]); lay.addWidget(sp)

        # ── timeline ──────────────────────────────────────────────────────────
        tlg = QGroupBox("Sort Time Timeline  (last 30 runs)")
        tll = QVBoxLayout(tlg)
        self.tl_chart = ChartCanvas(tlg); self.tl_chart.setMinimumHeight(200)
        tll.addWidget(self.tl_chart); lay.addWidget(tlg)

        self.tabs.addTab(_scrollable(outer), "  📊 Performance  ")
        self._refresh_perf()

    def _benchmark_all(self):
        """Run ALL 4 algorithms on the current dataset and show a full ranked chart."""
        jobs = self.db.fetch_all_jobs()
        if not jobs:
            QMessageBox.information(self, "No data", "Load jobs first."); return
        col = self.cmp_col.currentText()
        results: dict[str, float] = {}
        for alg in ALGORITHMS:
            _, t = sort_jobs(jobs, col, alg)
            ms = round(t * 1000, 3)
            results[alg] = ms
            if _PERF_AVAILABLE:
                perf_tracker.record(alg, col, ms, len(jobs))

        winner = min(results, key=results.get)
        ranked = sorted(results.items(), key=lambda x: x[1])
        lines  = "\n".join(
            f"  {'>>>' if alg==winner else f'#{i+1}'} {alg:<14} {ms:>8.3f} ms"
            for i, (alg, ms) in enumerate(ranked)
        )
        self.cmp_result.setText(
            f"WINNER: {winner} ({results[winner]:.3f} ms)  ·  {len(jobs):,} jobs  ·  sorted by {col}")

        # full 4-bar chart with winner highlighted
        fig = self._dark_fig((8, 3.5))
        ax  = self._ax(fig)
        algs = [a for a, _ in ranked]; times = [t for _, t in ranked]
        colors = [_C["primary"] if a == winner else _C["muted"] for a in algs]
        bars = ax.bar(algs, times, color=colors, width=0.5, alpha=0.95)
        for bar, alg, val in zip(bars, algs, times):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.002,
                    f"{val:.3f} ms", ha="center", va="bottom",
                    fontsize=10, fontweight="bold",
                    color=_C["primary"] if alg==winner else "#94a3b8")
        ax.set_ylabel("Time (ms)")
        ax.set_title(f"Full Benchmark  ·  {col}  ·  {len(jobs):,} jobs  ·  WINNER: {winner}",
                     pad=12, fontsize=12)
        ax.yaxis.grid(True, color=_C["border"], linewidth=0.7, linestyle="--")
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        fig.tight_layout(pad=1.5)
        self.cmp_chart.set_figure(fig)
        self._refresh_perf()

        QMessageBox.information(self, "Benchmark Complete",
            f"All 4 algorithms benchmarked on {len(jobs):,} jobs (column: {col}):\n\n{lines}")

    def _run_comparison(self):
        jobs = self.db.fetch_all_jobs()
        if not jobs:
            QMessageBox.information(self, "No data", "Load jobs first."); return
        col, a1, a2 = self.cmp_col.currentText(), self.cmp_alg1.currentText(), self.cmp_alg2.currentText()
        _, t1 = sort_jobs(jobs, col, a1); _, t2 = sort_jobs(jobs, col, a2)
        ms1, ms2 = round(t1*1000,3), round(t2*1000,3)
        if _PERF_AVAILABLE:
            perf_tracker.record(a1, col, ms1, len(jobs))
            perf_tracker.record(a2, col, ms2, len(jobs))
        winner = a1 if ms1 <= ms2 else a2
        self.cmp_result.setText(
            f"  {a1}: {ms1} ms   vs   {a2}: {ms2} ms   →   WINNER: {winner}  (by {abs(ms1-ms2):.3f} ms)")
        fig = self._dark_fig((7, 3))
        ax  = self._ax(fig)
        colors = [_C["primary"] if a==winner else _C["muted"] for a in (a1,a2)]
        bars = ax.bar([a1,a2], [ms1,ms2], color=colors, width=0.4, alpha=0.95)
        for bar, val in zip(bars, (ms1,ms2)):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.002,
                    f"{val} ms", ha="center", va="bottom", fontsize=11, fontweight="bold", color="white")
        ax.set_ylabel("Time (ms)")
        ax.set_title(f"{a1} vs {a2}  ·  {col}  ·  {len(jobs):,} jobs", pad=12)
        ax.yaxis.grid(True, color=_C["border"], linewidth=0.7, linestyle="--"); ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        fig.tight_layout(pad=1.5); self.cmp_chart.set_figure(fig)
        self._refresh_perf()

    def _make_avg_chart(self, avg_dict):
        if not avg_dict: return None
        algs = list(avg_dict.keys()); avgs = [avg_dict[a] for a in algs]
        best = min(avgs)
        colors = [_C["primary"] if v==best else _C["muted"] for v in avgs]
        fig = self._dark_fig((5.5, 3)); ax = self._ax(fig)
        bars = ax.bar(algs, avgs, color=colors, width=0.5, alpha=0.9)
        for bar, val in zip(bars, avgs):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.001,
                    f"{val:.2f}", ha="center", va="bottom", fontsize=9, color="white")
        ax.set_ylabel("Avg Time (ms)"); ax.set_title("Algorithm Efficiency  (all runs)", pad=10)
        ax.yaxis.grid(True, color=_C["border"], linewidth=0.6, linestyle="--"); ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        fig.tight_layout(pad=1.3); return fig

    def _make_timeline_chart(self, history):
        if not history: return None
        items = history[-30:]
        labels = [f"{e['algorithm'][:2]}@{e['timestamp']}" for e in items]
        times  = [e["time_ms"] for e in items]
        # colour each point by algorithm
        alg_colors = {a: _PALETTE[i] for i, a in enumerate(ALGORITHMS)}
        fig = self._dark_fig((9, 2.8)); ax = self._ax(fig)
        ax.fill_between(range(len(times)), times, alpha=0.12, color=_C["primary"])
        ax.plot(range(len(times)), times, color=_C["primary"], linewidth=1.8)
        for i, (e, val) in enumerate(zip(items, times)):
            ax.scatter(i, val, color=alg_colors.get(e["algorithm"], _C["primary"]), s=40, zorder=3)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=38, ha="right", fontsize=7)
        ax.set_ylabel("Time (ms)"); ax.set_title("Sort Time Timeline  (last 30 runs)", pad=10)
        ax.yaxis.grid(True, color=_C["border"], linewidth=0.6, linestyle="--"); ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        fig.tight_layout(pad=1.2); return fig

    def _refresh_perf(self):
        if not _PERF_AVAILABLE: return
        history = perf_tracker.get_history()
        self.perf_table.setColumnCount(5)
        self.perf_table.setHorizontalHeaderLabels(["Algorithm","Column","ms","Jobs","At"])
        recent = list(reversed(history[-50:]))
        self.perf_table.setRowCount(len(recent))
        for i, e in enumerate(recent):
            for j, k in enumerate(("algorithm","column","time_ms","job_count","timestamp")):
                item = QTableWidgetItem(str(e.get(k,""))); item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.perf_table.setItem(i, j, item)
        self.avg_chart.set_figure(self._make_avg_chart(perf_tracker.get_per_algorithm_avg()))
        self.tl_chart.set_figure(self._make_timeline_chart(history))

    def _clear_perf(self):
        if not _PERF_AVAILABLE: return
        perf_tracker.clear_history()
        self.cmp_result.setText(""); self.cmp_chart.set_figure(None)
        self._refresh_perf(); self._status("Sort history cleared.")