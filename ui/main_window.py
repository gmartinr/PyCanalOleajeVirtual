import time
import numpy as np
import pyqtgraph as pg

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel
from PySide6.QtCore import QTimer, Qt

from core.experiment_loader import ExperimentLoader
from core.csv_exporter import CSVExporter

from ui.panels.selection_panel import SelectionPanel
from ui.panels.playback_panel import PlaybackPanel
from ui.widgets.canal_plot import CanalPlotWidget
from ui.widgets.time_series_plot import TimeSeriesPlotWidget
from ui.widgets.velocity_plot import VelocityPlotWidget

WG_PALETTE = [
    '#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', 
    '#a65628', '#f781bf', '#17becf', '#bcbd22', '#8c564b'
]
COLOR_PARTICULA = 'm'
COLOR_CARRITO = 'g'


class MainWindow(QMainWindow):
    """Ventana principal que coordina los paneles de control, gráficos y la simulación."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador y Visualizador de Canal de Oleaje 2D")
        self.resize(1200, 900)

        self.loader = ExperimentLoader(data_dir="data", experiments_path="experiments")

        self.current_time_sim = 0.0
        self.is_playing = False
        self.last_clock_time = 0.0
        self.restar_h0 = False
        self.ts_step = 10.0

        self.wg_lines = {}
        self.ts_curves = {}
        self.wg_x_history = {}
        self.std_wg_ids = []

        self.has_carrito = False
        self.requires_particle = False

        self.u_part = None
        self.w_part = None
        self.xi_part = None
        self.zeta_part = None

        self.timer = QTimer()
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._al_notificar_timer)
        self.wgs_visible = True

        self._init_ui()
        self._poblar_experimentos()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        

        top_layout = QHBoxLayout()

        self.panel_seleccion = SelectionPanel()
        self.panel_seleccion.exp_changed.connect(self._al_cambiar_exp)
        self.panel_seleccion.case_changed.connect(self._al_cambiar_caso)
        self.panel_seleccion.particle_inputs_changed.connect(self._al_cambiar_inputs_particula)
        self.panel_seleccion.carrito_inputs_changed.connect(self._al_cambiar_inputs_carrito)
        self.panel_seleccion.wg_count_changed.connect(self._al_cambiar_num_wgs)

        group_caracteristicas = QGroupBox("Características del caso")
        layout_caracteristicas = QVBoxLayout(group_caracteristicas)
        self.lbl_caso_desc = QLabel("Cargando descripción...")
        self.lbl_caso_desc.setWordWrap(True)
        self.lbl_caso_desc.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout_caracteristicas.addWidget(self.lbl_caso_desc)

        self.panel_controles = PlaybackPanel()
        self.panel_controles.play_toggled.connect(self._toggle_play)
        self.panel_controles.reset_clicked.connect(self._reiniciar)
        self.panel_controles.export_clicked.connect(self._exportar_csv)

        top_layout.addWidget(self.panel_seleccion, stretch=4)
        top_layout.addWidget(group_caracteristicas, stretch=4)
        top_layout.addWidget(self.panel_controles, stretch=4)

        main_layout.addLayout(top_layout)

        self.plot_canal = CanalPlotWidget()
        main_layout.addWidget(self.plot_canal, stretch=1)

        self.plot_ts = TimeSeriesPlotWidget()
        self.plot_ts.scene().sigMouseMoved.connect(
            lambda pos: self.plot_ts.handle_mouse_moved(pos, self.is_playing, self.loader.time_vec, self.ts_curves)
        )
        main_layout.addWidget(self.plot_ts, stretch=1)

        self.plot_part_vel = VelocityPlotWidget()
        self.plot_part_vel.scene().sigMouseMoved.connect(
            lambda pos: self.plot_part_vel.handle_mouse_moved(
                pos, self.is_playing, self.requires_particle, self.u_part, self.w_part, self.loader.time_vec
            )
        )
        main_layout.addWidget(self.plot_part_vel, stretch=1)

    def _poblar_experimentos(self):
        exps = self.loader.obtener_experimentos()
        if exps:
            self.panel_seleccion.combo_exp.blockSignals(True)
            self.panel_seleccion.combo_exp.clear()
            for exp_id in exps:
                nombre = self.loader.obtener_nombre_experimento(exp_id)
                self.panel_seleccion.combo_exp.addItem(nombre, userData=exp_id)
            self.panel_seleccion.combo_exp.blockSignals(False)
            self._al_cambiar_exp(0)

    def _al_cambiar_exp(self, index):
        exp_id = self.panel_seleccion.combo_exp.itemData(index)
        if not exp_id:
            return

        casos = self.loader.obtener_casos(exp_id)
        self.panel_seleccion.combo_case.blockSignals(True)
        self.panel_seleccion.combo_case.clear()
        self.panel_seleccion.combo_case.addItems(casos)
        self.panel_seleccion.combo_case.blockSignals(False)
        if casos:
            self._al_cambiar_caso(casos[0])

    def _limpiar_sensores_dinamicos(self):
        for wg_line in self.wg_lines.values():
            self.plot_canal.removeItem(wg_line)
        for curve in self.ts_curves.values():
            self.plot_ts.removeItem(curve)

        self.plot_ts.limpiar_pills()
        self.wg_lines.clear()
        self.ts_curves.clear()
        self.wg_x_history.clear()
        self.std_wg_ids.clear()

    def _crear_wg(self, wg_id, nombre, x_pos, color):
        """Crea un nuevo sensor y reserva su arreglo de posiciones x(t) intercalando la altura de su etiqueta."""
        total_steps = self.loader.total_steps if self.loader.total_steps > 0 else 1000
        self.wg_x_history[wg_id] = np.full(total_steps, x_pos, dtype=np.float64)

        # Intercalar altura: pares arriba (0.92), impares abajo (0.10)
        if wg_id != "WG_Part":
            idx = len(self.std_wg_ids)
            pos_y = 0.92 if (idx % 2 == 0) else 0.82
        else:
            pos_y = 0.92  # La partícula se mantiene arriba por defecto

        line = pg.InfiniteLine(
            pos=x_pos, angle=90, movable=(wg_id != "WG_Part"),
            pen=pg.mkPen(color, width=2, style=Qt.DashLine),
            label=f"{nombre}: \n{{value:.2f}}m", 
            labelOpts={'color': color, 'position': pos_y}
        )
        line.sigPositionChanged.connect(lambda: self._al_mover_linea_wg(wg_id))
        self.plot_canal.addItem(line)
        self.wg_lines[wg_id] = line

        ts_curve = self.plot_ts.plot(pen=pg.mkPen(color, width=2), name=nombre)
        self.ts_curves[wg_id] = ts_curve

        # Show/Hide ÚNICAMENTE para los sensores fijos estándar (WG1, WG2, etc.)
        if wg_id != "WG_Part":
            self.plot_ts.agregar_pill_toggle(wg_id, nombre, color, ts_curve)

    def _al_mover_linea_wg(self, wg_id):
        """Al arrastrar el sensor en pausa, proyecta la nueva posición hacia el futuro."""
        if wg_id in self.wg_lines and wg_id in self.wg_x_history:
            x_pos = self.wg_lines[wg_id].value()
            paso_actual = min(int(self.current_time_sim / self.loader.dt), self.loader.total_steps - 1)
            self.wg_x_history[wg_id][paso_actual:] = x_pos
            self._actualizar_render(self.current_time_sim)

    def _al_cambiar_caso(self, case_nombre):
        exp_id = self.panel_seleccion.combo_exp.currentData()
        if not exp_id or not case_nombre:
            return

        if self.is_playing:
            self._toggle_play()

        # Fallback si no existe el archivo .h5 asociado
        try:
            self.loader.cargar_caso(exp_id, case_nombre)
        except (FileNotFoundError, KeyError) as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, 
                "Archivo no encontrado", 
                f"No se pudo cargar los datos del caso '{case_nombre}':\n{str(e)}"
            )
            self.lbl_caso_desc.setText(
                f"<b style='color:red;'>Error de Carga:</b><br>"
                f"No se encontró el archivo .h5 asociado a {exp_id} - {case_nombre}."
            )
            self._limpiar_sensores_dinamicos()
            return

        case_cfg = self.loader.obtener_config_caso_actual()
        h0 = self.loader.obtener_profundidad_inicial()

        self.ts_step = float(case_cfg.get("x_limits_ts_steps", 10.0))

        y_min = -abs(h0) if h0 > 0 else -0.6
        y_max = y_min + 1.0
        self.plot_canal.setYRange(y_min, y_max, padding=0)

        desc_caso = self.loader.obtener_descripcion_caso_actual()
        self.lbl_caso_desc.setText(desc_caso)

        _, eta_frame0, _ = self.loader.obtener_frame(0)
        self.restar_h0 = (h0 > 0 and np.abs(np.mean(eta_frame0)) > (h0 / 2.0))

        self._limpiar_sensores_dinamicos()

        self.requires_particle = case_cfg.get("requires_particle", False)
        self.panel_seleccion.panel_particula.setVisible(self.requires_particle)
        self.plot_part_vel.setVisible(self.requires_particle)

        if not self.requires_particle:
            self.u_part = None
            self.w_part = None
            self.xi_part = None
            self.zeta_part = None

        self.has_carrito = case_cfg.get("has_carrito", False)
        tiene_input_carrito = ("carrito_vel" in case_cfg or "carrito_x" in case_cfg)
        self.panel_seleccion.panel_carrito.setVisible(self.has_carrito and tiene_input_carrito)
        self.carrito_espera = float(case_cfg.get("carrito_espera", 0.0))
        
        requires_beach = case_cfg.get("requires_beach", False)
        playa_x = case_cfg.get("playa_x", [20.0, 30.0])
        playa_altura = float(case_cfg.get("playa_altura", 1.0))

        self.plot_canal.update_playa(
            visible=requires_beach,
            x_ini=float(playa_x[0]),
            x_fin=float(playa_x[1]),
            z_base=y_min,
            altura=playa_altura
        )

        requires_barrera = case_cfg.get("requires_barrera", False)
        barrera_x = float(case_cfg.get("barrera_x", 15.0))
        barrera_z_bottom = float(case_cfg.get("barrera_z_bottom", -0.25))
        barrera_ancho = float(case_cfg.get("barrera_ancho", 0.2))

        self.plot_canal.update_barrera(
            visible=requires_barrera,
            x_pos=barrera_x,
            z_bottom=barrera_z_bottom,
            ancho=barrera_ancho,
            z_top=y_max
        )

        self.plot_canal.update_carrito(visible=self.has_carrito)
        self.plot_canal.update_particula(visible=self.requires_particle)
        self.plot_ts.curve_ts_carrito.setVisible(self.has_carrito)

        if "carrito_vel" in case_cfg:
            self.panel_seleccion.spin_car_vel.blockSignals(True)
            self.panel_seleccion.spin_car_vel.setValue(float(case_cfg["carrito_vel"]))
            self.panel_seleccion.spin_car_vel.blockSignals(False)

        if "carrito_x" in case_cfg:
            car_x = case_cfg["carrito_x"]
            self.carrito_x_ini = float(car_x[0])
            self.carrito_x_fin = float(car_x[1])
        else:
            self.carrito_x_ini = 20.0
            self.carrito_x_fin = 0.1

        # Configuración de límites min/max de Wave Gauges desde el JSON
        wgs_cfg = list(case_cfg.get("wave_gauges", []))

        min_wgs = int(case_cfg.get("min_wave_gauges", 0))
        max_wgs = int(case_cfg.get("max_wave_gauges", 10))

        if min_wgs > max_wgs:
            min_wgs = max_wgs

        self.panel_seleccion.set_wg_range(min_wgs, max_wgs)
        self.panel_seleccion.set_inputs_enabled(True)

        # Sincronizar el valor actual del SpinBox dentro del rango permitido
        initial_wgs = int(np.clip(len(wgs_cfg), min_wgs, max_wgs))
        self.panel_seleccion.spin_num_wgs.blockSignals(True)
        self.panel_seleccion.spin_num_wgs.setValue(initial_wgs)
        self.panel_seleccion.spin_num_wgs.blockSignals(False)

        for i in range(initial_wgs):
            if i < len(wgs_cfg):
                wg = wgs_cfg[i]
                wg_id = wg.get("id", f"WG{i+1}")
                x_def = wg.get("x", 5.0 + i * 2.0)
                nombre = wg.get("nombre", wg_id)
            else:
                wg_id = f"WG{i+1}"
                x_def = 5.0 + i * 2.0
                nombre = f"WG{i+1}"

            color = WG_PALETTE[i % len(WG_PALETTE)]
            self._crear_wg(wg_id, nombre, x_def, color)
            self.std_wg_ids.append(wg_id)

        if self.requires_particle:
            pos_p = case_cfg.get("posicion_particula")
            if pos_p and isinstance(pos_p, (list, tuple)) and len(pos_p) >= 2:
                x_p_val = float(pos_p[0])
                y_p_val = float(pos_p[1])
            else:
                x_p_val = float(case_cfg.get("x_particula", 10.0))
                prof_p = case_cfg.get("profundidad_particula")
                y_p_val = float(prof_p) if prof_p is not None else h0 / 2.0

            self.panel_seleccion.spin_px.blockSignals(True)
            self.panel_seleccion.spin_px.setValue(x_p_val)
            self.panel_seleccion.spin_px.blockSignals(False)

            self.panel_seleccion.spin_py.blockSignals(True)
            self.panel_seleccion.spin_py.setRange(-abs(h0) + 0.01, -0.01)
            self.panel_seleccion.spin_py.setValue(-abs(y_p_val))
            self.panel_seleccion.spin_py.blockSignals(False)

            x_p = self.panel_seleccion.spin_px.value()
            self._crear_wg("WG_Part", "WG Partícula", x_p, COLOR_PARTICULA)

        y_limits = case_cfg.get("y_limits_ts")
        if y_limits and len(y_limits) == 2:
            self.plot_ts.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)
            self.plot_ts.setYRange(y_limits[0], y_limits[1], padding=0)
        else:
            self.plot_ts.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)

        y_u = case_cfg.get("y_limits_vel_u")
        y_w = case_cfg.get("y_limits_vel_w")

        if y_u and len(y_u) == 2:
            self.plot_part_vel.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)
            self.plot_part_vel.setYRange(y_u[0], y_u[1], padding=0)
        else:
            self.plot_part_vel.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)

        if y_w and len(y_w) == 2:
            self.plot_part_vel.vb_w.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)
            self.plot_part_vel.vb_w.setYRange(y_w[0], y_w[1], padding=0)
        else:
            self.plot_part_vel.vb_w.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)

        xc, h_fondo = self.loader.obtener_fondo()
        y_fondo = -np.abs(h_fondo) if (h_fondo is not None and np.max(np.abs(h_fondo)) > 0) else np.full_like(xc, y_min)
        self.plot_canal.set_fondo_y_piso(xc, y_fondo, y_min)

        if self.requires_particle:
            self._recalcular_cinematica_particula()

        self.current_time_sim = 0.0
        self.plot_ts.setXRange(0, self.ts_step, padding=0)
        self.plot_part_vel.setXRange(0, self.ts_step, padding=0)
        self._actualizar_render(0.0)

    def _al_cambiar_num_wgs(self, target_count):
        actual_count = len(self.std_wg_ids)

        if target_count > actual_count:
            for i in range(actual_count, target_count):
                wg_id = f"WG{i+1}"
                nombre = f"WG{i+1}"
                color = WG_PALETTE[i % len(WG_PALETTE)]

                if self.std_wg_ids:
                    last_id = self.std_wg_ids[-1]
                    last_x = self.wg_lines[last_id].value()
                    x_pos = min(last_x + 2.0, 29.5)
                else:
                    x_pos = 2.0

                self._crear_wg(wg_id, nombre, x_pos, color)
                self.std_wg_ids.append(wg_id)

        elif target_count < actual_count:
            for _ in range(actual_count - target_count):
                wg_id_to_remove = self.std_wg_ids.pop()
                if wg_id_to_remove in self.wg_lines:
                    self.plot_canal.removeItem(self.wg_lines[wg_id_to_remove])
                    del self.wg_lines[wg_id_to_remove]
                if wg_id_to_remove in self.ts_curves:
                    self.plot_ts.removeItem(self.ts_curves[wg_id_to_remove])
                    del self.ts_curves[wg_id_to_remove]
                if wg_id_to_remove in self.wg_x_history:
                    del self.wg_x_history[wg_id_to_remove]
                self.plot_ts.remover_pill_toggle(wg_id_to_remove)

        self._actualizar_render(self.current_time_sim)

    def _al_cambiar_inputs_particula(self):
        if not self.requires_particle:
            return
        
        x_p = self.panel_seleccion.spin_px.value()
        if "WG_Part" in self.wg_lines:
            self.wg_lines["WG_Part"].setValue(x_p)

        self._recalcular_cinematica_particula()
        self._actualizar_render(self.current_time_sim)

    def _al_cambiar_inputs_carrito(self):
        if self.has_carrito:
            self._actualizar_render(self.current_time_sim)

    def _recalcular_cinematica_particula(self):
        x_p = self.panel_seleccion.spin_px.value()
        y_p = self.panel_seleccion.spin_py.value()

        self.u_part, self.w_part, self.xi_part, self.zeta_part = self.loader.calcular_cinematica_particula(x_p, y_p)
        if self.xi_part is not None and self.zeta_part is not None:
            self.plot_canal.update_particula(
                x_p + self.xi_part[0], y_p + self.zeta_part[0],
                self.xi_part, self.zeta_part, x_p, y_p, visible=self.requires_particle
            )

    def _calcular_posicion_carrito(self, t_sim):
        case_cfg = self.loader.obtener_config_caso_actual()
        dist_total = abs(self.carrito_x_fin - self.carrito_x_ini)
        direccion = -1.0 if self.carrito_x_fin < self.carrito_x_ini else 1.0

        if "carrito_vel" in case_cfg or "carrito_x" in case_cfg:
            v_car = self.panel_seleccion.spin_car_vel.value()
            t_mov = max(0.0, t_sim - self.carrito_espera)
            d_desplazamiento = min(v_car * t_mov, dist_total)
            return self.carrito_x_ini + direccion * d_desplazamiento
        else:
            t_total = self.loader.time_vec[-1] if self.loader.time_vec is not None and len(self.loader.time_vec) > 0 else 1.0
            fraccion = t_sim / t_total
            return self.carrito_x_ini + fraccion * (self.carrito_x_fin - self.carrito_x_ini)

    def _toggle_play(self):
        self.plot_ts.hover_label_ts.hide()
        self.plot_part_vel.hover_label_vel.hide()

        if self.is_playing:
            self.timer.stop()
            self.is_playing = False
            self.panel_controles.set_playing_state(False)
            for wg_id, line in self.wg_lines.items():
                if wg_id != "WG_Part":
                    line.setMovable(True)
        else:
            self.panel_seleccion.set_inputs_enabled(False)

            if self.current_time_sim >= self.loader.time_vec[-1]:
                self.current_time_sim = 0.0

            for line in self.wg_lines.values():
                line.setMovable(False)
            self.last_clock_time = time.time()
            self.timer.start()
            self.is_playing = True
            self.panel_controles.set_playing_state(True)

    def _reiniciar(self):
        if self.is_playing:
            self._toggle_play()
        self.current_time_sim = 0.0

        self.panel_seleccion.set_inputs_enabled(True)

        self.plot_ts.setXRange(0, self.ts_step, padding=0)
        self.plot_part_vel.setXRange(0, self.ts_step, padding=0)
        self._actualizar_render(0.0)

    def _al_notificar_timer(self):
        if not self.is_playing:
            return

        now = time.time()
        dt_real = now - self.last_clock_time
        self.last_clock_time = now

        self.current_time_sim += dt_real
        t_max = self.loader.time_vec[-1]

        if self.current_time_sim >= t_max:
            self.current_time_sim = t_max
            self._actualizar_render(self.current_time_sim)
            self._toggle_play()
            return

        self._actualizar_render(self.current_time_sim)

    def _obtener_eta_interpolado_tiempo(self, t):
        dt = self.loader.dt
        paso_exacto = t / dt
        idx0 = min(int(np.floor(paso_exacto)), self.loader.total_steps - 1)
        idx1 = min(idx0 + 1, self.loader.total_steps - 1)
        alpha = paso_exacto - np.floor(paso_exacto)

        _, eta0, _ = self.loader.obtener_frame(idx0)
        _, eta1, _ = self.loader.obtener_frame(idx1)

        return (1.0 - alpha) * eta0 + alpha * eta1

    def _actualizar_render(self, t_sim):
        xc = self.loader.xc
        t_vec = self.loader.time_vec
        paso_actual = min(int(t_sim / self.loader.dt), self.loader.total_steps - 1)
        h0 = self.loader.obtener_profundidad_inicial()

        eta_raw = self._obtener_eta_interpolado_tiempo(t_sim)
        eta = eta_raw - h0 if self.restar_h0 else eta_raw

        self.plot_canal.update_agua(xc, eta)
        t_historia = t_vec[:paso_actual + 1]

        if len(t_historia) > 0:
            matriz_raw = self.loader.ds_eta[:paso_actual + 1, :]
            eta_matriz_hist = matriz_raw - h0 if self.restar_h0 else matriz_raw
        else:
            eta_matriz_hist = None

        for wg_id, line in self.wg_lines.items():
            if eta_matriz_hist is not None:
                if wg_id not in self.wg_x_history:
                    self.wg_x_history[wg_id] = np.full(self.loader.total_steps, line.value(), dtype=np.float64)

                self.wg_x_history[wg_id][paso_actual:] = line.value()
                x_hist = self.wg_x_history[wg_id][:paso_actual + 1]
                idxs_x = np.clip(np.searchsorted(xc, x_hist), 0, len(xc) - 1)

                y_series = eta_matriz_hist[np.arange(paso_actual + 1), idxs_x]
                self.ts_curves[wg_id].setData(t_historia, y_series)

        if self.requires_particle and self.u_part is not None:
            x_p0 = self.panel_seleccion.spin_px.value()
            y_p0 = self.panel_seleccion.spin_py.value()
            
            x_p_now = x_p0 + self.xi_part[paso_actual]
            y_p_now = y_p0 + self.zeta_part[paso_actual]

            self.plot_canal.update_particula(
                x_p_now, y_p_now, self.xi_part, self.zeta_part, x_p0, y_p0, visible=True
            )
            self.plot_part_vel.curve_u.setData(t_historia, self.u_part[:paso_actual + 1])
            self.plot_part_vel.curve_w.setData(t_historia, self.w_part[:paso_actual + 1])
        else:
            self.plot_canal.update_particula(visible=False)

        if self.has_carrito:
            x_carrito = self._calcular_posicion_carrito(t_sim)
            
            y_bounds = self.plot_canal.viewRange()[1]
            y_marker = y_bounds[0] + 0.92 * (y_bounds[1] - y_bounds[0])
            
            self.plot_canal.update_carrito(x_carrito, y_marker, visible=True)

            if eta_matriz_hist is not None:
                case_cfg = self.loader.obtener_config_caso_actual()
                if "carrito_vel" in case_cfg or "carrito_x" in case_cfg:
                    v_car = self.panel_seleccion.spin_car_vel.value()
                    dist_total = abs(self.carrito_x_fin - self.carrito_x_ini)
                    direccion = -1.0 if self.carrito_x_fin < self.carrito_x_ini else 1.0
                    
                    t_mov_vec = np.maximum(0.0, t_historia - self.carrito_espera)
                    d_vec = np.minimum(v_car * t_mov_vec, dist_total)
                    xs_carrito = self.carrito_x_ini + direccion * d_vec
                else:
                    t_total = t_vec[-1] if len(t_vec) > 0 else 1.0
                    fracciones = t_historia / t_total
                    xs_carrito = self.carrito_x_ini + fracciones * (self.carrito_x_fin - self.carrito_x_ini)

                idxs_carrito = np.clip(np.searchsorted(xc, xs_carrito), 0, len(xc) - 1)
                self.plot_ts.curve_ts_carrito.setData(t_historia, eta_matriz_hist[np.arange(len(t_historia)), idxs_carrito])
        else:
            self.plot_canal.update_carrito(visible=False)

        if self.is_playing:
            bloque = int(t_sim // self.ts_step)
            self.plot_ts.setXRange(bloque * self.ts_step, (bloque + 1) * self.ts_step, padding=0)
            if self.requires_particle:
                self.plot_part_vel.setXRange(bloque * self.ts_step, (bloque + 1) * self.ts_step, padding=0)

        self.panel_controles.update_time_label(t_sim, t_vec[-1])

    def _exportar_csv(self):
        CSVExporter.exportar(
            parent=self,
            loader=self.loader,
            wg_lines=self.wg_lines,
            wg_x_history=self.wg_x_history,
            has_carrito=self.has_carrito,
            carrito_x_ini=self.carrito_x_ini,
            carrito_x_fin=self.carrito_x_fin,
            spin_car_vel=self.panel_seleccion.spin_car_vel.value(),
            requires_particle=self.requires_particle,
            u_part=self.u_part,
            w_part=self.w_part,
            xi_part=self.xi_part,
            zeta_part=self.zeta_part,
            restar_h0=self.restar_h0
        )

    def closeEvent(self, event):
        self.loader.cerrar()
        event.accept()