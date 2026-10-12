# Simulador y Visualizador de Canal de Oleaje 2D

Aplicación de escritorio interactiva en Python desarrollada con **PySide6** y **PyQtGraph** para la simulación, inspección y análisis cinemático de ensayos en canales de oleaje 2D a partir de hidrogramas en formato HDF5 (`.h5`).

## 🚀 Características Principales

* **Arquitectura Modular JSON**: Experimentos y casos de estudio independientes organizados en archivos de configuración (`experiments/expN.json`) con límites flexibles de sensores.
* **Modelación Física y Estructuras**:
  * Playas triangulares disipadoras con pendiente personalizable.
  * Barreras / paredes semi-sumergidas colgadas con control de cota inferior.
  * Carrito móvil instrumental con simulación de tiempo de espera (`carrito_espera`) y avance controlado.
* **Sensórica Dinámica y Control en Pantalla**:
  * Control dinámico de la cantidad de Wave Gauges (WG) con restricción por experimento (`min_wave_gauges` y `max_wave_gauges`).
  * Posicionamiento espacial intercalado de etiquetas para evitar superposiciones visuales.
  * Botones alternadores (*Pill Toggles*) para conmutar visibilidad (*Show/Hide*) de trazas individuales en tiempo real.
  * Bloqueo automático de paneles durante la ejecución del temporizador (liberable con el botón *Reiniciar*).
* **Cinemática de Partícula Fluida**: Cálculo y representación gráfica de componentes de velocidad ($u, w$) y orbitales de desplazamiento ($\xi, \zeta$) mediante transformada de Fourier y teoría lineal.
* **Exportación Fiel de Datos (CSV)**:
  * Generación automática de nombres estandarizados: `mediciones_ExpX_CasoY.csv`.
  * Preservación del historial real de arrastre espacial de sensores (`wg_x_history`).
  * Redondeo controlado a 4 decimales para eficiencia sin pérdida de precisión física.
* **Robustez de la Interfaz**: Notificaciones dinámicas mediante diálogos y etiquetas ante la ausencia de archivos HDF5 o inconsistencias en claves de datos.

## 🛠️ Instalación y Uso

### Crear entorno virtual e instalar dependencias

Instalar python, se recomienda utilizar la versión python *3.12.13* ya que fue con esta que se creó este proyecto.

```
python3 -m venv .venv

# En Linux/macOS:
source .venv/bin/activate

# En Windows:
.venv\Scripts\activate

pip install -r requirements.txt

python main.py
```

## *Descarga adicional*
Debido a limitaciones del peso de los archivos que se pueden subir a github, se requiere una descarga adicional de datos utilziados para el experimento 2. Los datos los puedes descargar de:

https://cloud.lipc.unam.mx/s/HzeRdT5D5pk3rbA

Es necesario descomprimirlos en el directorio data/.

### Ejecución
```
python main.py
```

---

## 📂 Estructura del Proyecto

```text
CanalOleaje/
├── core/                    # Lógica del sistema y procesamiento
│   ├── csv_exporter.py      # Exportador de series temporales a CSV
│   └── experiment_loader.py # Carga y parsing de .h5 y archivos JSON
├── data/                    # Base de datos física (.h5)
├── experiments/             # Archivos de configuración por experimento
│   ├── exp1.json
│   ├── exp2.json
│   └── ...
├── ui/                      # Interfaz gráfica de usuario (PySide6)
│   ├── panels/              # Paneles de control y selección
│   ├── widgets/             # Gráficos PyQtGraph interactivos
│   └── main_window.py       # Ventana principal y coordinación
├── main.py                  # Punto de entrada de la aplicación
├── requirements.txt         # Dependencias del proyecto
└── README.md                # Documentación

