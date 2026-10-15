import os
from PySide6.QtWidgets import (QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QGroupBox, QFrame)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt


class AboutPanel(QScrollArea):
    """Pestaña con información de autores, licencia Creative Commons y patrocinadores."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self._init_ui()

    def _init_ui(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Sección Autores
        grp_autores = QGroupBox("Autores y Desarrollo")
        lay_autores = QVBoxLayout(grp_autores)
        
        lbl_autores = QLabel(
            "<h2>Simulador y Visualizador de Canal de Oleaje 2D</h2>"
            "Versión 1.0.0_py (2026)<br>"
            "<p><b>Autores del proyecto:</b></p>"
            "<ul>"
            "<li><b>Gonzalo U. Martín Ruiz</b> - <i>Instituto de Ingeniería / UNAM</i></li>"
            "<li><b>Alec Torres Freyermuth</b> - <i>Instituto de Ingeniería / UNAM</i></li>"
            "<li><b>Gabriela Medellín Mayoral</b> - <i>Instituto de Ingeniería / UNAM</i></li>"
            "</ul>"
            "<p>Proyecto desarrollado para el soporte a la docencia e investigación en ingeniería hidráulica, de costas y ciencias del mar.</p>"
        )
        lbl_autores.setWordWrap(True)
        lbl_autores.setOpenExternalLinks(True)
        lay_autores.addWidget(lbl_autores)

        # 2. Sección Licencia Creative Commons
        grp_cc = QGroupBox("Licencia y Términos de Uso")
        lay_cc = QHBoxLayout(grp_cc)

        lbl_img_cc = QLabel()
        path_cc = os.path.join("assets", "cc-by-nc-sa.png")
        pixmap_cc = QPixmap(path_cc)
        
        if not pixmap_cc.isNull():
            lbl_img_cc.setPixmap(pixmap_cc.scaledToWidth(140, Qt.SmoothTransformation))
        else:
            lbl_img_cc.setText("[ Logo CC ]")
            lbl_img_cc.setStyleSheet("border: 1px dashed gray; padding: 15px; color: gray;")
        lbl_img_cc.setAlignment(Qt.AlignCenter)

        lbl_txt_cc = QLabel(
            "<b>Material Educativo bajo Licencia Creative Commons</b><br>"
            "La documentación pedagógica, guías teóricas y material didáctico asociados a este software "
            "están licenciados bajo <b>Creative Commons Atribución 4.0 Internacional (CC BY 4.0)</b>.<br><br>"
            "<i>Usted es libre de compartir, copiar, redistribuir y adaptar el material para cualquier propósito, "
            "siempre que otorgue el crédito correspondiente a los autores originales.</i>"
        )
        lbl_txt_cc.setWordWrap(True)

        lay_cc.addWidget(lbl_img_cc, stretch=1)
        lay_cc.addWidget(lbl_txt_cc, stretch=4)

        # 3. Sección Patrocinadores
        grp_patrocinador = QGroupBox("Patrocinador y Agradecimientos")
        lay_patrocinador = QHBoxLayout(grp_patrocinador)

        lbl_img_patrocinador = QLabel()
        path_patrocinador = os.path.join("assets", "UNAM-Logo.png")
        pixmap_patrocinador = QPixmap(path_patrocinador)

        if not pixmap_patrocinador.isNull():
            lbl_img_patrocinador.setPixmap(pixmap_patrocinador.scaledToWidth(180, Qt.SmoothTransformation))
        else:
            lbl_img_patrocinador.setText("[ Logo Patrocinador ]")
            lbl_img_patrocinador.setStyleSheet("border: 1px dashed gray; padding: 15px; color: gray;")
        lbl_img_patrocinador.setAlignment(Qt.AlignCenter)

        lbl_txt_patrocinador = QLabel(
            "<b>Agradecimiento Especial</b><br>"
            "Este proyecto de traducción de Matlab a Python del Canal de Oleaje ha sido desarrollado con el patrocinio y apoyo institucional del proyecto:<br>"
            "<h3>DGAPA-UNAM PAPIME PE101725</h3>"
            "<p>Programa de Apoyo a Proyectos para Innovar y Mejorar la Educación</p>"
        )
        lbl_txt_patrocinador.setWordWrap(True)

        lay_patrocinador.addWidget(lbl_img_patrocinador, stretch=1)
        lay_patrocinador.addWidget(lbl_txt_patrocinador, stretch=4)

        # Agregar bloques al layout principal
        layout.addWidget(grp_autores)
        layout.addWidget(grp_cc)
        layout.addWidget(grp_patrocinador)
        layout.addStretch()

        self.setWidget(container)