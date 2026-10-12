import csv
import numpy as np
from PySide6.QtWidgets import QFileDialog, QMessageBox


class CSVExporter:
    """Módulo encargado de generar y guardar los archivos CSV con las series de tiempo medidas."""

    @staticmethod
    def exportar(parent, loader, wg_lines, wg_x_history, has_carrito, carrito_x_ini, carrito_x_fin, 
                 spin_car_vel, requires_particle, u_part, w_part, xi_part, zeta_part, restar_h0):
        if loader.time_vec is None:
            QMessageBox.warning(parent, "Exportación", "No hay datos cargados para exportar.")
            return

        # Nombre dinámico por defecto: mediciones_Exp#_Caso#.csv
        exp_name = str(loader.exp_actual or "Exp").replace(" ", "_")
        case_name = str(loader.caso_actual or "Caso").replace(" ", "_")
        default_filename = f"mediciones_{exp_name}_{case_name}.csv"

        file_path, _ = QFileDialog.getSaveFileName(
            parent, "Guardar Mediciones CSV", default_filename, "Archivos CSV (*.csv)"
        )
        if not file_path:
            return

        try:
            xc = loader.xc
            t_vec = loader.time_vec
            h0 = loader.obtener_profundidad_inicial()
            matriz_raw = loader.ds_eta[:, :]
            eta_matriz = matriz_raw - h0 if restar_h0 else matriz_raw

            encabezados = ["tiempo_s"]
            columnas = [t_vec]

            # 1. Mediciones de Wave Gauges utilizando su historial real x(t)
            for wg_id, line in wg_lines.items():
                if wg_id in wg_x_history:
                    x_hist = wg_x_history[wg_id][:len(t_vec)]
                else:
                    x_hist = np.full(len(t_vec), line.value())

                idxs_x = np.clip(np.searchsorted(xc, x_hist), 0, len(xc) - 1)
                encabezados.append(f"eta_{wg_id}_m")
                columnas.append(eta_matriz[np.arange(len(t_vec)), idxs_x])

            # 2. Mediciones del Carrito Móvil
            if has_carrito:
                case_cfg = loader.obtener_config_caso_actual()
                if "carrito_vel" in case_cfg or "carrito_x" in case_cfg:
                    v_car = spin_car_vel
                    dist_total = abs(carrito_x_fin - carrito_x_ini)
                    direccion = -1.0 if carrito_x_fin < carrito_x_ini else 1.0
                    carrito_espera = float(case_cfg.get("carrito_espera", 0.0))

                    t_mov_vec = np.maximum(0.0, t_vec - carrito_espera)
                    d_vec = np.minimum(v_car * t_mov_vec, dist_total)
                    xs_carrito = carrito_x_ini + direccion * d_vec
                else:
                    t_total = t_vec[-1] if len(t_vec) > 0 else 1.0
                    fracciones = t_vec / t_total
                    xs_carrito = carrito_x_ini + fracciones * (carrito_x_fin - carrito_x_ini)

                idxs_carrito = np.clip(np.searchsorted(xc, xs_carrito), 0, len(xc) - 1)
                encabezados.append("eta_carrito_m")
                columnas.append(eta_matriz[np.arange(len(t_vec)), idxs_carrito])

            # 3. Cinemática de la Partícula
            if requires_particle and u_part is not None:
                encabezados.extend(["u_particula_ms", "w_particula_ms", "xi_desplazamiento_m", "zeta_desplazamiento_m"])
                columnas.extend([u_part, w_part, xi_part, zeta_part])

            # Construir la matriz y limitar a 5 decimales
            matriz_export = np.column_stack(columnas)
            matriz_export = np.round(matriz_export, 5)

            with open(file_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(encabezados)
                writer.writerows(matriz_export)

            QMessageBox.information(parent, "Exportación Éxito", f"Datos exportados correctamente en:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(parent, "Error al exportar", f"Ocurrió un error guardando el CSV:\n{str(e)}")