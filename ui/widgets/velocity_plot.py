import numpy as np
import pyqtgraph as pg


class VelocityPlotWidget(pg.PlotWidget):
    """Gráfico con doble eje Y para mostrar u (horizontal) y w (vertical) de la partícula fluida."""

    def __init__(self, parent=None):
        super().__init__(parent, title="Medición de las componentes de velocidad de la partícula")
        self._init_plot()

    def _init_plot(self):
        self.setLabel('bottom', 'Tiempo (s)')
        self.setLabel('left', 'u (m/s)', color='r')
        
        axis_left = self.getAxis('left')
        axis_left.setPen('r')
        axis_left.setTextPen('r')
        axis_left.enableAutoSIPrefix(False)

        self.showGrid(x=True, y=True, alpha=0.3)
        self.setMouseEnabled(x=True, y=False)
        self.hideButtons()
        self.setMenuEnabled(False)
        self.getAxis('bottom').enableAutoSIPrefix(False)
        self.setXRange(0, 10, padding=0)

        # Configuración del eje Y derecho (w - vertical)
        self.vb_w = pg.ViewBox()
        self.vb_w.setMenuEnabled(False)
        self.scene().addItem(self.vb_w)

        self.axis_w = pg.AxisItem('right')
        self.axis_w.setLabel('w (m/s)', color='b')
        self.axis_w.setPen('b')
        self.axis_w.setTextPen('b')
        self.axis_w.enableAutoSIPrefix(False)

        self.plotItem.layout.addItem(self.axis_w, 2, 3)
        self.axis_w.linkToView(self.vb_w)
        self.vb_w.setXLink(self.plotItem)

        self.plotItem.vb.sigResized.connect(self._update_views)

        self.curve_u = self.plot(pen=pg.mkPen('r', width=2), name="u (horizontal)")
        self.curve_w = pg.PlotCurveItem(pen=pg.mkPen('b', width=2), name="w (vertical)")
        self.vb_w.addItem(self.curve_w)

        # INSPECCIÓN EN PAUSA
        self.hover_label_vel = pg.TextItem("", anchor=(0, 1), fill=pg.mkBrush(255, 255, 255, 220), border=pg.mkPen('k'))
        self.addItem(self.hover_label_vel)
        self.hover_label_vel.hide()

    def _update_views(self):
        self.vb_w.setGeometry(self.plotItem.vb.sceneBoundingRect())
        self.vb_w.linkedViewChanged(self.plotItem.vb, self.vb_w.XAxis)

    def handle_mouse_moved(self, pos, is_playing, requires_particle, u_part, w_part, time_vec):
        if is_playing or not requires_particle or u_part is None or time_vec is None:
            self.hover_label_vel.hide()
            return

        if self.plotItem.sceneBoundingRect().contains(pos):
            mouse_point = self.plotItem.vb.mapSceneToView(pos)
            t_val = mouse_point.x()
            
            if 0 <= t_val <= time_vec[-1]:
                idx = int(np.clip(np.searchsorted(time_vec, t_val), 0, len(time_vec) - 1))
                t_exact = time_vec[idx]
                u_val = u_part[idx]
                w_val = w_part[idx]

                text = f"t = {t_exact:.2f} s\nu = {u_val:.3f} m/s\nw = {w_val:.3f} m/s"
                self.hover_label_vel.setText(text)
                self.hover_label_vel.setPos(mouse_point.x(), mouse_point.y())
                self.hover_label_vel.show()
                return

        self.hover_label_vel.hide()