import sys
import os
import pyqtgraph as pg
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

# Configuración global de PyQtGraph
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOption('antialias', True)

from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    app.setApplicationName("Canal de Oleaje Virtual")
    app.setApplicationDisplayName("Canal de Oleaje Virtual")
    app.setOrganizationName("CanalOleaje")
    
    # Ruta al archivo del ícono
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "Icon_WaveLab.png")
    
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)  # Establece el ícono global de la aplicación / Dock
    
    window = MainWindow()
    if os.path.exists(icon_path):
        window.setWindowIcon(app_icon)  # Refuerza el ícono en la ventana principal
        
    window.show()
    sys.exit(app.exec())