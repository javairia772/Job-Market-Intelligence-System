"""
ui/chart_widget.py
==================
Embeds a matplotlib Figure in a PyQt6 widget with a safe fullscreen button.

THE BUG EXPLAINED:
  NavigationToolbar2QT creates a QLabel (locLabel) for mouse coordinates.
  When a QDialog closes, Qt destroys all child widgets including that label.
  But matplotlib's C-level mouse_move callback is still connected and calls
  locLabel.setText() on the deleted C++ object → RuntimeError every mouse move.

THE FIX:
  • Never use NavigationToolbar2QT inside a QDialog.
  • For fullscreen: render the figure to a PNG buffer, open a NEW standalone
    matplotlib figure window showing that image.
    matplotlib owns that window entirely — no Qt parenting issues possible.
  • Inline canvas: disconnect all event callbacks before deleteLater().
"""

import io
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSizePolicy, QLabel,
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ChartCanvas(QWidget):
    """
    Embeds one matplotlib Figure safely.

        canvas.set_figure(fig)   → show fig
        canvas.set_figure(None)  → show placeholder
        (extra positional args silently ignored — backward compat)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fig: Figure | None = None
        self._canvas: FigureCanvas | None = None
        self._png_buf: bytes | None = None   # cached PNG for fullscreen

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(2)

        # ── top bar ───────────────────────────────────────────────────────────
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 2, 0)
        top.addStretch()
        self._fs_btn = QPushButton("⛶  Full Screen")
        self._fs_btn.setFixedHeight(22)
        self._fs_btn.setStyleSheet(
            "QPushButton{background:#1a2540;color:#475569;"
            "border:1px solid #1e293b;border-radius:4px;"
            "font-size:10px;padding:0 8px;}"
            "QPushButton:hover{color:#e2e8f0;border-color:#38bdf8;}"
        )
        self._fs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fs_btn.clicked.connect(self._open_fullscreen)
        self._fs_btn.setVisible(False)
        top.addWidget(self._fs_btn)
        root.addLayout(top)

        # ── placeholder ───────────────────────────────────────────────────────
        self._placeholder = QLabel("No chart data")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet(
            "color:#1e3a5f;font-size:12px;"
            "background:#0a0f1e;border-radius:8px;"
        )
        self._placeholder.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        root.addWidget(self._placeholder)

        self._root = root

    # ─────────────────────────────────────────────────────────────────────────
    #  Public API
    # ─────────────────────────────────────────────────────────────────────────

    def set_figure(self, fig: Figure | None, *_ignored):
        """
        Display *fig* (matplotlib Figure) or clear with None.
        Extra args are silently ignored for backward compatibility.
        """
        # ── save PNG before any canvas operations ─────────────────────────────
        if fig is not None:
            try:
                buf = io.BytesIO()
                fig.savefig(buf, format="png", dpi=150,
                            bbox_inches="tight",
                            facecolor=fig.get_facecolor())
                buf.seek(0)
                self._png_buf = buf.read()
            except Exception:
                self._png_buf = None
        else:
            self._png_buf = None

        self._fig = fig

        # ── tear down old canvas ──────────────────────────────────────────────
        if self._canvas is not None:
            # Disconnect ALL matplotlib event callbacks before Qt deletes
            # the widget. This prevents the locLabel / mouse_move RuntimeError.
            try:
                cbs = self._canvas.figure.canvas.callbacks.callbacks
                for event_name in list(cbs.keys()):
                    cbs[event_name].clear()
            except Exception:
                pass
            self._root.removeWidget(self._canvas)
            self._canvas.setParent(None)   # unparent first
            self._canvas.deleteLater()
            self._canvas = None

        if fig is None:
            self._placeholder.setVisible(True)
            self._fs_btn.setVisible(False)
            return

        # ── embed new canvas ──────────────────────────────────────────────────
        self._placeholder.setVisible(False)
        self._canvas = FigureCanvas(fig)
        self._canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._root.addWidget(self._canvas)
        self._canvas.draw_idle()
        self._fs_btn.setVisible(True)

    # ─────────────────────────────────────────────────────────────────────────
    #  Fullscreen — uses PIL-free PNG → new matplotlib figure approach
    # ─────────────────────────────────────────────────────────────────────────

    def _open_fullscreen(self):
        """
        Open the chart in a maximised QDialog using a fresh FigureCanvas.

        We render the stored PNG buffer into a NEW matplotlib Figure (never
        sharing the embedded figure between two canvases).  The dialog owns
        a plain FigureCanvas — no NavigationToolbar, so the locLabel
        use-after-free bug cannot occur.
        """
        if self._png_buf is None:
            return

        import matplotlib.image as mpimg
        from PyQt6.QtWidgets import QDialog, QVBoxLayout

        try:
            # PNG bytes → image array → new figure
            img = mpimg.imread(io.BytesIO(self._png_buf))

            bg = self._fig.get_facecolor() if self._fig else "#0a0f1e"
            fig_fs = Figure(figsize=(14, 8), facecolor=bg)
            ax = fig_fs.add_subplot(111)
            ax.imshow(img, aspect="auto", interpolation="lanczos")
            ax.axis("off")
            ax.set_facecolor(bg)
            fig_fs.tight_layout(pad=0)

            # Dialog — owns the canvas completely, no parent toolbar issues
            dlg = QDialog(self)
            dlg.setWindowTitle("Chart — Full Screen")
            dlg.setWindowFlags(
                Qt.WindowType.Dialog |
                Qt.WindowType.WindowMaximizeButtonHint |
                Qt.WindowType.WindowCloseButtonHint
            )
            dlg.resize(1200, 750)
            dlg.setStyleSheet("background:#0a0f1e;")

            lay = QVBoxLayout(dlg)
            lay.setContentsMargins(0, 0, 0, 0)

            fs_canvas = FigureCanvas(fig_fs)
            fs_canvas.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            lay.addWidget(fs_canvas)
            fs_canvas.draw()

            # When dialog closes, cleanly disconnect canvas events
            def _on_close():
                try:
                    cbs = fs_canvas.figure.canvas.callbacks.callbacks
                    for k in list(cbs.keys()):
                        cbs[k].clear()
                except Exception:
                    pass

            dlg.finished.connect(lambda _: _on_close())
            dlg.exec()

        except Exception as e:
            print(f"[ChartCanvas] fullscreen failed: {e}")