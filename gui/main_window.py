"""Interface graphique unique et minimaliste."""

import subprocess
import platform
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QProgressBar, QMessageBox,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from core.lmstudio_client import LMStudioClient
from core.ralph_loop import RalphLoop
from core.guides_manager import list_guides


class ConnectionChecker(QThread):
    result = pyqtSignal(dict)

    def run(self):
        client = LMStudioClient()
        info = client.check_connection()
        self.result.emit(info)


class Worker(QThread):
    log = pyqtSignal(str)
    prog = pyqtSignal(int)
    tasks_updated = pyqtSignal(list)
    finished = pyqtSignal(bool, str)

    def __init__(self, demande: str, model: str = None, guide_path: str = None):
        super().__init__()
        self.demande = demande
        self.model = model
        self.guide_path = guide_path
        self.loop = None

    def run(self):
        try:
            self.loop = RalphLoop(
                self.model,
                log_callback=lambda m: self.log.emit(m),
                progress_callback=lambda v: self.prog.emit(v),
                tasks_callback=lambda t: self.tasks_updated.emit(t),
                guide_path=self.guide_path
            )
            path = self.loop.run(self.demande)
            self.finished.emit(True, str(path))
        except Exception as e:
            self.log.emit(f"\u274c {e}")
            self.finished.emit(False, "")

    def stop(self):
        if self.loop:
            self.loop.stop()


class MainWindow(QMainWindow):
    def __init__(self, emoji_font: str = None):
        super().__init__()
        self.setWindowTitle("Ralph Loop Manager")
        self.setMinimumSize(900, 600)
        self.worker = None
        self.emoji_font = emoji_font
        self.build_ui()
        self.check_connection()
        self.load_guides()

    def _emoji_font(self, size: int = 10) -> QFont:
        """Retourne une police avec support emoji si disponible."""
        if self.emoji_font:
            return QFont(self.emoji_font, size)
        return QFont("DejaVu Sans", size)

    def build_ui(self):
        cw = QWidget()
        self.setCentralWidget(cw)
        lo = QVBoxLayout(cw)
        lo.setSpacing(12)
        lo.setContentsMargins(20, 20, 20, 20)

        # Titre avec police emoji
        title = QLabel("\U0001f504 Ralph Loop Manager")
        title.setFont(self._emoji_font(16))
        title.setStyleSheet("font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lo.addWidget(title)

        # Statut connexion LM Studio
        self.conn_label = QLabel()
        self.conn_label.setFont(self._emoji_font(9))
        self.conn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.conn_label.setStyleSheet("padding: 4px; border-radius: 4px;")
        self.conn_label.setText("\u23f3 Connexion a LM Studio...")
        lo.addWidget(self.conn_label)

        # Zone de saisie
        lbl_demand = QLabel("\U0001f4cb Collez votre demande :")
        lbl_demand.setFont(self._emoji_font(10))
        lo.addWidget(lbl_demand)

        self.input = QTextEdit()
        self.input.setPlaceholderText("Ex: Cree un voltmetre Arduino sur A0 avec affichage LCD...")
        self.input.setMinimumHeight(120)
        self.input.setFont(QFont("Consolas", 10))
        lo.addWidget(self.input)

        # Sélecteur de guide
        lbl_guide = QLabel("\U0001f4c2 Guide de décomposition :")
        lbl_guide.setFont(self._emoji_font(10))
        lo.addWidget(lbl_guide)

        self.guide_combo = QComboBox()
        self.guide_combo.setFont(QFont("Consolas", 10))
        self.guide_combo.addItem("-- Aucun (LLM libre) --", None)
        lo.addWidget(self.guide_combo)

        # Boutons
        btn = QHBoxLayout()
        self.btn_clear = QPushButton("\U0001f5d1\ufe0f Effacer")
        self.btn_clear.setFont(self._emoji_font(10))
        self.btn_clear.clicked.connect(self.input.clear)
        btn.addWidget(self.btn_clear)
        btn.addStretch()

        self.btn_go = QPushButton("\U0001f680 Lancer Ralph")
        self.btn_go.setFont(self._emoji_font(11))
        self.btn_go.setStyleSheet("QPushButton{background:#2ecc71;color:white;font-weight:bold;padding:10px 25px;border-radius:6px}QPushButton:hover{background:#27ae60}")
        self.btn_go.clicked.connect(self.launch)
        btn.addWidget(self.btn_go)
        lo.addLayout(btn)

        # Progression
        self.status = QLabel("\u23f3 En attente...")
        self.status.setFont(self._emoji_font(10))
        lo.addWidget(self.status)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        lo.addWidget(self.bar)

        # Liste des tâches
        lbl_tasks = QLabel("\U0001f4cb Tâches :")
        lbl_tasks.setFont(self._emoji_font(10))
        lo.addWidget(lbl_tasks)

        self.task_table = QTableWidget(0, 3)
        self.task_table.setHorizontalHeaderLabels(["ID", "Titre", "Statut"])
        self.task_table.horizontalHeader().setStretchLastSection(True)
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.task_table.setColumnWidth(0, 40)
        self.task_table.setColumnWidth(2, 100)
        self.task_table.setMaximumHeight(160)
        self.task_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.task_table.setAlternatingRowColors(True)
        lo.addWidget(self.task_table)

        # Console
        lbl_logs = QLabel("\U0001f5a5\ufe0f Logs :")
        lbl_logs.setFont(self._emoji_font(10))
        lo.addWidget(lbl_logs)

        self.console = QTextEdit()
        self.console.setReadOnly(True)

        if self.emoji_font:
            font = QFont(self.emoji_font, 10)
            print(f"[FONT] Console utilise: {self.emoji_font}")
        else:
            font = QFont("DejaVu Sans", 10)
            print("[FONT] Console: DejaVu Sans (fallback)")

        self.console.setFont(font)

        self.console.setStyleSheet("background:#1e1e1e;color:#d4d4d4;border-radius:5px")
        self.console.setMinimumHeight(200)
        lo.addWidget(self.console)

        # Stop
        self.btn_stop = QPushButton("\u23f9\ufe0f Arreter")
        self.btn_stop.setFont(self._emoji_font(10))
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop)
        lo.addWidget(self.btn_stop, alignment=Qt.AlignmentFlag.AlignCenter)

    def log(self, msg: str):
        from datetime import datetime
        self.console.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        sb = self.console.verticalScrollBar()
        sb.setValue(sb.maximum())

    def check_connection(self):
        self.conn_label.setText("\u23f3 Connexion a LM Studio...")
        self.conn_label.setStyleSheet("padding: 4px; border-radius: 4px; color: #888;")
        self.checker = ConnectionChecker()
        self.checker.result.connect(self.on_connection_result)
        self.checker.start()

    def load_guides(self):
        self.guide_combo.clear()
        self.guide_combo.addItem("-- Aucun (LLM libre) --", None)
        guides = list_guides()
        for g in guides:
            self.guide_combo.addItem(g["title"], g["path"])

    def on_connection_result(self, info: dict):
        if info["connected"]:
            model = info.get("loaded_model") or "Inconnu"
            models_list = info.get("models", [])
            model_count = len(models_list)
            detail = f" ({model_count} modele(s) disponible(s))" if model_count > 0 else ""
            self.conn_label.setText(f"\u2705 LM Studio connecte \u2014 {model}{detail}")
            self.conn_label.setStyleSheet(
                "padding: 4px; border-radius: 4px; background: #d4edda; color: #155724;"
            )
        else:
            self.conn_label.setText("\u274c LM Studio non joignable")
            self.conn_label.setStyleSheet(
                "padding: 4px; border-radius: 4px; background: #f8d7da; color: #721c24;"
            )

    def update_task_list(self, tasks: list):
        """Met à jour la table des tâches avec leurs statuts."""
        self.task_table.setRowCount(len(tasks))
        colors = {
            "pending": QColor("#888"),
            "running": QColor("#2196F3"),
            "done":    QColor("#4CAF50"),
            "failed":  QColor("#F44336")
        }
        labels = {
            "pending": "⏳ En attente",
            "running": "🔄 En cours",
            "done":    "✅ Terminé",
            "failed":  "❌ Échec"
        }
        for row, t in enumerate(tasks):
            id_item = QTableWidgetItem(t["id"])
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.task_table.setItem(row, 0, id_item)

            title_item = QTableWidgetItem(t["title"])
            self.task_table.setItem(row, 1, title_item)

            status = t.get("status", "pending")
            status_item = QTableWidgetItem(labels.get(status, status))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            color = colors.get(status, QColor("#888"))
            status_item.setForeground(color)
            self.task_table.setItem(row, 2, status_item)

    def launch(self):
        txt = self.input.toPlainText().strip()
        if not txt:
            QMessageBox.warning(self, "Vide", "Collez une demande d'abord.")
            return
        self.btn_go.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.bar.setValue(0)
        self.status.setText("\u23f3 Decomposition...")
        self.console.clear()
        self.task_table.setRowCount(0)

        guide_path = self.guide_combo.currentData()
        self.worker = Worker(txt, guide_path=guide_path)
        self.worker.log.connect(self.log)
        self.worker.prog.connect(self.bar.setValue)
        self.worker.tasks_updated.connect(self.update_task_list)
        self.worker.finished.connect(self.done)
        self.worker.start()

    def done(self, ok: bool, path: str):
        self.btn_go.setEnabled(True)
        self.btn_stop.setEnabled(False)
        if ok:
            self.bar.setValue(100)
            self.status.setText("\u2705 Termine !")
            self.log(f"\U0001f4c1 {path}")
            msg = "Ouvrir le dossier ?\n" + path
            if QMessageBox.question(self, "Fini", msg) == QMessageBox.StandardButton.Yes:
                cmd = {"Windows": ["explorer"], "Darwin": ["open"]}.get(platform.system(), ["xdg-open"])
                subprocess.run(cmd + [path])
        else:
            self.status.setText("\u274c Echec")

    def stop(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait(3000)