from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QWidget, QDoubleSpinBox, QSpinBox)
from PySide6.QtCore import Signal, Qt


class SelectionPanel(QGroupBox):
    """Panel para la selección de experimento, caso y ajuste de parámetros de entrada."""

    exp_changed = Signal(int)
    case_changed = Signal(str)
    particle_inputs_changed = Signal()
    carrito_inputs_changed = Signal()
    wg_count_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__("Selección de Experimento", parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Selector de Experimento
        row_exp = QHBoxLayout()
        lbl_exp = QLabel("Experimento:")
        lbl_exp.setStyleSheet("font-weight: bold;")
        self.combo_exp = QComboBox()
        self.combo_exp.currentIndexChanged.connect(self.exp_changed.emit)
        row_exp.addWidget(lbl_exp)
        row_exp.addWidget(self.combo_exp, stretch=1)

        # Selector de Caso
        row_case = QHBoxLayout()
        lbl_caso = QLabel("Caso:")
        lbl_caso.setStyleSheet("font-weight: bold;")
        self.combo_case = QComboBox()
        self.combo_case.currentTextChanged.connect(self.case_changed.emit)
        row_case.addWidget(lbl_caso)
        row_case.addWidget(self.combo_case, stretch=1)

        # Control para la cantidad dinámica de Wave Gauges
        self.panel_wgs = QWidget()
        layout_wgs = QHBoxLayout(self.panel_wgs)
        layout_wgs.setContentsMargins(0, 0, 0, 0)

        lbl_wgs = QLabel("Cantidad Wave Gauges:")
        lbl_wgs.setStyleSheet("font-weight: bold;")
        self.spin_num_wgs = QSpinBox()
        self.spin_num_wgs.setRange(0, 10)
        self.spin_num_wgs.setValue(2)
        self.spin_num_wgs.valueChanged.connect(self.wg_count_changed.emit)

        layout_wgs.addWidget(lbl_wgs)
        layout_wgs.addWidget(self.spin_num_wgs)

        # Controles numéricos para la partícula
        self.panel_particula = QWidget()
        layout_part_inputs = QHBoxLayout(self.panel_particula)
        layout_part_inputs.setContentsMargins(0, 0, 0, 0)

        lbl_px = QLabel("X Partícula (m):")
        self.spin_px = QDoubleSpinBox()
        self.spin_px.setRange(0.5, 29.5)
        self.spin_px.setValue(10.0)
        self.spin_px.setSingleStep(0.5)

        lbl_py = QLabel("Y Partícula (m):")
        self.spin_py = QDoubleSpinBox()
        self.spin_py.setRange(-0.59, -0.01)
        self.spin_py.setValue(-0.30)
        self.spin_py.setSingleStep(0.05)

        self.spin_px.valueChanged.connect(lambda _: self.particle_inputs_changed.emit())
        self.spin_py.valueChanged.connect(lambda _: self.particle_inputs_changed.emit())

        layout_part_inputs.addWidget(lbl_px)
        layout_part_inputs.addWidget(self.spin_px)
        layout_part_inputs.addWidget(lbl_py)
        layout_part_inputs.addWidget(self.spin_py)

        # Controles para la velocidad del Carrito Móvil
        self.panel_carrito = QWidget()
        layout_car_inputs = QHBoxLayout(self.panel_carrito)
        layout_car_inputs.setContentsMargins(0, 0, 0, 0)

        lbl_car_vel = QLabel("Velocidad carrito:")
        lbl_car_vel.setStyleSheet("font-weight: bold;")
        self.spin_car_vel = QDoubleSpinBox()
        self.spin_car_vel.setRange(0.01, 10.0)
        self.spin_car_vel.setValue(0.5)
        self.spin_car_vel.setSingleStep(0.1)
        self.spin_car_vel.setDecimals(2)
        self.spin_car_vel.setSuffix(" m/s")
        self.spin_car_vel.valueChanged.connect(lambda _: self.carrito_inputs_changed.emit())

        layout_car_inputs.addWidget(lbl_car_vel)
        layout_car_inputs.addWidget(self.spin_car_vel)

        layout.addLayout(row_exp)
        layout.addLayout(row_case)
        layout.addWidget(self.panel_wgs)
        layout.addWidget(self.panel_particula)
        layout.addWidget(self.panel_carrito)

    def set_wg_range(self, min_val: int, max_val: int):
        """Ajusta los límites min/max del SpinBox y oculta el selector si min == max."""
        self.spin_num_wgs.blockSignals(True)
        self.spin_num_wgs.setRange(min_val, max_val)
        self.spin_num_wgs.blockSignals(False)

        # Ocultar si min == max, de lo contrario mostrar
        self.panel_wgs.setVisible(min_val != max_val)

    def set_inputs_enabled(self, enabled: bool):
        """Bloquea o desbloquea los controles durante la ejecución."""
        self.combo_exp.setEnabled(enabled)
        self.combo_case.setEnabled(enabled)
        self.spin_num_wgs.setEnabled(enabled)
        self.spin_px.setEnabled(enabled)
        self.spin_py.setEnabled(enabled)
        self.spin_car_vel.setEnabled(enabled)