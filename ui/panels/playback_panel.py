from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal, Qt


class PlaybackPanel(QGroupBox):
    """Panel con los botones de control (Play, Reiniciar, Exportar) y estado de tiempo."""

    play_toggled = Signal()
    reset_clicked = Signal()
    export_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__("Controles del experimento", parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        row_btns = QHBoxLayout()
        self.btn_play = QPushButton("▶ Reproducir")
        self.btn_play.clicked.connect(self.play_toggled.emit)

        self.btn_reset = QPushButton("↺ Reiniciar")
        self.btn_reset.clicked.connect(self.reset_clicked.emit)

        self.btn_export = QPushButton("💾 Exportar CSV")
        self.btn_export.clicked.connect(self.export_clicked.emit)

        row_btns.addWidget(self.btn_play)
        row_btns.addWidget(self.btn_reset)
        row_btns.addWidget(self.btn_export)

        self.lbl_tiempo = QLabel("Tiempo: 0.00 s / 0.00 s")
        self.lbl_tiempo.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.lbl_tiempo.setAlignment(Qt.AlignCenter)

        layout.addLayout(row_btns)
        layout.addWidget(self.lbl_tiempo)

    def set_playing_state(self, is_playing: bool):
        self.btn_play.setText("⏸ Pausar" if is_playing else "▶ Reproducir")

    def update_time_label(self, current_time: float, total_time: float):
        self.lbl_tiempo.setText(f"Tiempo: {current_time:.2f} s / {total_time:.2f} s")