import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame
from PySide6.QtCore import Qt


def color_a_hex(color):
    """Mapea nombres abreviados de color a formato Hexadecimal CSS."""
    colores_map = {
        'r': '#e41a1c', 'g': '#2ca02c', 'b': '#1f77b4',
        'm': '#d62728', 'y': '#bcbd22', 'k': '#333333'
    }
    return colores_map.get(color, color)


class TimeSeriesPlotWidget(QWidget):
    """Widget de series de tiempo de superficie libre con botones interactivos tipo 'pill'."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pills = {}
        self.curves = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Barra de desplazamiento horizontal para las Pills
        self.scroll_pills = QScrollArea()
        self.scroll_pills.setFixedHeight(32)
        self.scroll_pills.setWidgetResizable(True)
        self.scroll_pills.setFrameShape(QFrame.NoFrame)
        self.scroll_pills.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_pills.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.pills_container = QWidget()
        self.layout_pills = QHBoxLayout(self.pills_container)
        self.layout_pills.setContentsMargins(2, 2, 2, 2)
        self.layout_pills.setSpacing(6)
        self.layout_pills.setAlignment(Qt.AlignLeft)

        # 1. Etiqueta indicadora
        self.lbl_pills = QLabel("WG Visibles:")
        self.layout_pills.addWidget(self.lbl_pills)

        self.scroll_pills.setWidget(self.pills_container)
        self.scroll_pills.setVisible(False)  # 3. Oculto por defecto si no hay pills

        # Gráfico PyQtGraph interno
        self.plot_widget = pg.PlotWidget(title="Medición en superficie libre")
        self.plot_widget.setLabel('bottom', 'Tiempo (s)')
        self.plot_widget.setLabel('left', '\u03B7 (m)')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setMouseEnabled(x=True, y=False)
        self.plot_widget.hideButtons()
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.getAxis('left').enableAutoSIPrefix(False)
        self.plot_widget.getAxis('bottom').enableAutoSIPrefix(False)
        self.plot_widget.setXRange(0, 10, padding=0)

        # Curva especial para el carrito móvil
        self.curve_ts_carrito = self.plot_widget.plot(pen=pg.mkPen('g', width=2), name="WG1_Movil")

        # Etiqueta de inspección al pausar
        self.hover_label_ts = pg.TextItem("", anchor=(0, 1), fill=pg.mkBrush(255, 255, 255, 220), border=pg.mkPen('k'))
        self.plot_widget.addItem(self.hover_label_ts)
        self.hover_label_ts.hide()

        layout.addWidget(self.scroll_pills)
        layout.addWidget(self.plot_widget)

    # Delegación de métodos de PlotWidget para mantener compatibilidad
    def scene(self):
        return self.plot_widget.scene()

    @property
    def plotItem(self):
        return self.plot_widget.plotItem

    def setXRange(self, *args, **kwargs):
        self.plot_widget.setXRange(*args, **kwargs)

    def setYRange(self, *args, **kwargs):
        self.plot_widget.setYRange(*args, **kwargs)

    def enableAutoRange(self, *args, **kwargs):
        self.plot_widget.enableAutoRange(*args, **kwargs)

    def plot(self, *args, **kwargs):
        return self.plot_widget.plot(*args, **kwargs)

    def removeItem(self, item):
        self.plot_widget.removeItem(item)

    # Lógica de Pills Interactivas
    def agregar_pill_toggle(self, wg_id, nombre, color, curve):
        """Agrega un botón 'Pill' para encender/apagar una serie temporal."""
        if wg_id in self.pills:
            return

        btn = QPushButton(nombre)
        btn.setCheckable(True)
        btn.setChecked(True)

        hex_col = color_a_hex(color)
        # 2. Hojas de estilo explícitas para checked / unchecked
        btn.setStyleSheet(f"""
            QPushButton {{
                border-radius: 11px;
                padding: 2px 9px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:checked {{
                background-color: {hex_col};
                color: white;
                border: 1px solid {hex_col};
            }}
            QPushButton:unchecked {{
                background-color: #e0e0e0;
                color: #777777;
                border: 1px solid #cccccc;
            }}
            QPushButton:hover {{
                opacity: 0.85;
            }}
        """)

        btn.toggled.connect(curve.setVisible)
        self.layout_pills.addWidget(btn)
        self.pills[wg_id] = btn
        self.curves[wg_id] = curve

        # Mostrar la barra al registrar al menos un botón
        self.scroll_pills.setVisible(True)

    def remover_pill_toggle(self, wg_id):
        """Elimina la pill asociada a un WG."""
        if wg_id in self.pills:
            btn = self.pills.pop(wg_id)
            self.layout_pills.removeWidget(btn)
            btn.deleteLater()
        if wg_id in self.curves:
            del self.curves[wg_id]

        if len(self.pills) == 0:
            self.scroll_pills.setVisible(False)

    def limpiar_pills(self):
        """Elimina todas las pills registradas."""
        for wg_id, btn in list(self.pills.items()):
            self.layout_pills.removeWidget(btn)
            btn.deleteLater()
        self.pills.clear()
        self.curves.clear()
        self.scroll_pills.setVisible(False)

    def handle_mouse_moved(self, pos, is_playing, time_vec, ts_curves):
        if is_playing or time_vec is None:
            self.hover_label_ts.hide()
            return

        if self.plot_widget.plotItem.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            t_val = mouse_point.x()
            
            if 0 <= t_val <= time_vec[-1]:
                idx = int(np.clip(np.searchsorted(time_vec, t_val), 0, len(time_vec) - 1))
                t_exact = time_vec[idx]
                
                info = [f"t = {t_exact:.2f} s"]
                for wg_id, curve in ts_curves.items():
                    if curve.isVisible():
                        xdata, ydata = curve.getData()
                        if ydata is not None and len(ydata) > idx:
                            info.append(f"{wg_id}: {ydata[idx]:.3f} m")

                self.hover_label_ts.setText("\n".join(info))
                self.hover_label_ts.setPos(mouse_point.x(), mouse_point.y())
                self.hover_label_ts.show()
                return

        self.hover_label_ts.hide()