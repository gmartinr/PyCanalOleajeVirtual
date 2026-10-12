import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPolygonF
from PySide6.QtWidgets import QGraphicsPolygonItem


class CanalPlotWidget(pg.PlotWidget):
    """Gráfico 2D interactivo del canal de oleaje, agua, lecho marino y sensores."""

    def __init__(self, parent=None):
        super().__init__(parent, title="Canal de Oleaje")
        self._init_plot()

    def _init_plot(self):
        self.setLabel('bottom', 'x (m)')
        self.setLabel('left', 'z (m)')
        self.setMouseEnabled(x=False, y=False)
        self.hideButtons()
        self.setMenuEnabled(False)
        self.getAxis('left').enableAutoSIPrefix(False)
        self.getAxis('bottom').enableAutoSIPrefix(False)

        axis_x = self.getAxis('bottom')
        ticks_5in5 = [(i, str(i)) for i in range(0, 31, 5)]
        axis_x.setTicks([ticks_5in5])
        self.setXRange(0, 30, padding=0)

        # Curvas y sombreados
        self.curve_agua = pg.PlotCurveItem(pen=pg.mkPen('#0055ff', width=2), name="Superficie Agua")
        self.curve_fondo = pg.PlotCurveItem(pen=pg.mkPen('k', width=2), name="Fondo")
        self.curve_piso = pg.PlotCurveItem(pen=None)

        self.fill_suelo = pg.FillBetweenItem(self.curve_piso, self.curve_fondo, brush=pg.mkBrush(160, 160, 160, 200))
        self.fill_agua = pg.FillBetweenItem(self.curve_fondo, self.curve_agua, brush=pg.mkBrush(30, 144, 255, 130))

        self.addItem(self.fill_suelo)
        self.addItem(self.fill_agua)
        self.addItem(self.curve_fondo)
        self.addItem(self.curve_agua)

        # Elemento Polígono para la Playa Triangular
        self.item_playa = QGraphicsPolygonItem()
        self.item_playa.setBrush(pg.mkBrush(203, 189, 147, 255))   # Color arena
        self.item_playa.setPen(pg.mkPen('k', width=2))            # Borde negro
        self.item_playa.setZValue(5)                              # Nivel Z superior al suelo
        self.addItem(self.item_playa)
        self.item_playa.setVisible(False)

        # Elemento Polígono para la Barrera / Pared Semi-sumergida
        self.item_barrera = QGraphicsPolygonItem()
        self.item_barrera.setBrush(pg.mkBrush(80, 80, 80, 255))   # Gris oscuro concreto
        self.item_barrera.setPen(pg.mkPen('k', width=2))          # Borde negro
        self.item_barrera.setZValue(6)                            # Sobre el agua y fondo
        self.addItem(self.item_barrera)
        self.item_barrera.setVisible(False)

        # Sensores del Carrito Móvil
        self.wg_carrito = pg.InfiniteLine(
            pos=2.0, angle=90, movable=False, pen=pg.mkPen('g', width=2, style=Qt.DashLine),
            label="WG1_Movil: {value:.2f}m", labelOpts={'color': 'g', 'position': 0.92}
        )
        self.addItem(self.wg_carrito)
        self.marker_carrito = self.plot([2.0], [0.3], symbol='o', symbolSize=12, symbolBrush='g')

        # Partícula fluida u órbita
        self.marker_particula = self.plot([10.0], [-0.3], symbol='o', symbolSize=10, symbolBrush='y', symbolPen='k')
        self.curve_orbita = self.plot([], [], pen=pg.mkPen('y', width=1, style=Qt.DashLine))

        self.curve_orbita.setZValue(10)
        self.marker_particula.setZValue(11)

        # Ocultos por defecto
        self.wg_carrito.setVisible(False)
        self.marker_carrito.setVisible(False)
        self.marker_particula.setVisible(False)
        self.curve_orbita.setVisible(False)

    def set_fondo_y_piso(self, xc, y_fondo, y_min):
        self.curve_fondo.setData(xc, y_fondo)
        self.curve_piso.setData(xc, np.full_like(xc, y_min))

    def update_agua(self, xc, eta):
        self.curve_agua.setData(xc, eta)

    def update_playa(self, visible=False, x_ini=20.0, x_fin=30.0, z_base=-0.6, altura=1.0):
        """Construye y muestra/oculta la playa triangular según los parámetros."""
        self.item_playa.setVisible(visible)
        if visible:
            p1 = QPointF(x_ini, z_base)               # Vértice 1: [20, fondo]
            p2 = QPointF(x_fin, z_base)               # Vértice 2: [30, fondo]
            p3 = QPointF(x_fin, z_base + altura)      # Vértice 3: [30, fondo + altura]
            self.item_playa.setPolygon(QPolygonF([p1, p2, p3]))

    def update_barrera(self, visible=False, x_pos=15.0, z_bottom=-0.25, ancho=0.2, z_top=0.4):
        """Construye y muestra/oculta la pared semi-sumergida colgada desde arriba."""
        self.item_barrera.setVisible(visible)
        if visible:
            x_izq = x_pos - ancho / 2.0
            x_der = x_pos + ancho / 2.0
            p1 = QPointF(x_izq, z_bottom)             # Abajo izquierda (-0.25)
            p2 = QPointF(x_der, z_bottom)             # Abajo derecha (-0.25)
            p3 = QPointF(x_der, z_top)                # Arriba derecha (tope del canal)
            p4 = QPointF(x_izq, z_top)                # Arriba izquierda (tope del canal)
            self.item_barrera.setPolygon(QPolygonF([p1, p2, p3, p4]))

    def update_carrito(self, x_pos=0, y_pos=0, visible=True):
        self.wg_carrito.setVisible(visible)
        self.marker_carrito.setVisible(visible)
        if visible:
            self.wg_carrito.setValue(x_pos)
            self.marker_carrito.setData([x_pos], [y_pos])

    def update_particula(self, x_pos=0, y_pos=0, xi_orbita=None, zeta_orbita=None, x0=None, y0=None, visible=True):
        self.marker_particula.setVisible(visible)
        self.curve_orbita.setVisible(visible)
        if visible:
            self.marker_particula.setData([x_pos], [y_pos])
            if xi_orbita is not None and zeta_orbita is not None and x0 is not None and y0 is not None:
                self.curve_orbita.setData(x0 + xi_orbita, y0 + zeta_orbita)