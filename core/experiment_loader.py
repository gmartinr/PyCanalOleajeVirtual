import os
import h5py
import json
import numpy as np


class ExperimentLoader:
    def __init__(self, data_dir="data", experiments_path="experiments"):
        self.data_dir = data_dir
        self.experiments_path = experiments_path

        # Cargar todos los .json si es carpeta, o uno solo si es archivo
        self.config = self._cargar_configuraciones(experiments_path)
        
        self.h5_file = None
        self.ds_eta = None
        self.ds_x = None
        self.ds_time = None
        self.ds_bottom = None

        self.xc = None
        self.time_vec = None
        self.dt = 0.01
        self.total_steps = 0
        self.h0 = 0.6
        self.restar_h0 = False

        self.exp_actual = None
        self.caso_actual = None

    def _cargar_json(self, path):
        if not os.path.exists(path):
            print(f"Error: No se encontró el archivo de configuración {path}")
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _cargar_configuraciones(self, path):
        """
        Carga la configuración. Si path es una carpeta, lee y combina 
        todos los archivos .json que contiene.
        """
        config_combinada = {}
        
        if os.path.isdir(path):
            for filename in sorted(os.listdir(path)):
                if filename.endswith(".json"):
                    file_path = os.path.join(path, filename)
                    json_data = self._cargar_json(file_path)
                    if isinstance(json_data, dict):
                        config_combinada.update(json_data)
        elif os.path.isfile(path):
            config_combinada = self._cargar_json(path)
        else:
            print(f"Advertencia: La ruta de configuración '{path}' no existe.")

        return config_combinada

    def _obtener_dataset_flexible(self, nombres_posibles):
        """Busca y retorna el primer dataset disponible en el archivo HDF5."""
        for nombre in nombres_posibles:
            if nombre in self.h5_file:
                return self.h5_file[nombre]
        llaves_existentes = list(self.h5_file.keys())
        raise KeyError(
            f"No se encontró ninguna de las claves {nombres_posibles} en el archivo HDF5. "
            f"Claves encontradas en el archivo: {llaves_existentes}"
        )

    def obtener_experimentos(self):
        """Devuelve únicamente los experimentos cuyo campo 'enable' o 'enabled' sea True."""
        return [
            exp_id for exp_id, cfg in self.config.items()
            if cfg.get("enable", cfg.get("enabled", True))
        ]

    def obtener_nombre_experimento(self, exp_id):
        return self.config.get(exp_id, {}).get("name", exp_id)

    def obtener_casos(self, exp_id):
        return list(self.config.get(exp_id, {}).get("casos", {}).keys())

    def cargar_caso(self, exp_id, caso_nombre):
        self.cerrar()
        self.exp_actual = exp_id
        self.caso_actual = caso_nombre

        cfg_caso = self.config[exp_id]["casos"][caso_nombre]
        h5_filename = cfg_caso.get("h5_file")
        h5_path = os.path.join(self.data_dir, h5_filename)

        if not os.path.exists(h5_path):
            raise FileNotFoundError(f"No se encontró el archivo HDF5: {h5_path}")

        self.h5_file = h5py.File(h5_path, 'r')

        # Carga flexible de datasets HDF5
        self.ds_eta = self._obtener_dataset_flexible(['eta', 'Eta', 'ETA', 'elevation'])
        
        ds_x_obj = self._obtener_dataset_flexible(['x', 'xc', 'X', 'x_grid', 'grid_x'])
        self.ds_x = ds_x_obj[:]

        ds_time_obj = self._obtener_dataset_flexible(['time', 't', 'Time', 't_vec', 'tiempo'])
        self.ds_time = ds_time_obj[:]

        # Búsqueda opcional del fondo del canal
        for nombre_bottom in ['bottom', 'fondo', 'b', 'bed']:
            if nombre_bottom in self.h5_file:
                self.ds_bottom = self.h5_file[nombre_bottom][:]
                break
        else:
            self.ds_bottom = None

        self.xc = np.squeeze(self.ds_x)
        self.time_vec = np.squeeze(self.ds_time)

        if len(self.time_vec) > 1:
            self.dt = float(self.time_vec[1] - self.time_vec[0])
        else:
            self.dt = 0.01

        self.total_steps = len(self.time_vec)
        self.h0 = float(cfg_caso.get("profundidad_inicial", 0.6))

        # Verificar si eta incluye h0 como offset
        eta_frame0 = self.ds_eta[0, :]
        self.restar_h0 = (self.h0 > 0 and np.abs(np.mean(eta_frame0)) > (self.h0 / 2.0))

    def obtener_config_caso_actual(self):
        if not self.exp_actual or not self.caso_actual:
            return {}
        cfg = dict(self.config[self.exp_actual])
        cfg_caso = self.config[self.exp_actual]["casos"][self.caso_actual]
        cfg.update(cfg_caso)
        return cfg

    def obtener_descripcion_caso_actual(self):
        cfg = self.obtener_config_caso_actual()
        return cfg.get("descripcion", "")

    def obtener_profundidad_inicial(self):
        return self.h0

    def obtener_fondo(self):
        if self.ds_bottom is not None:
            return self.xc, np.squeeze(self.ds_bottom)
        return self.xc, np.full_like(self.xc, -abs(self.h0))

    def obtener_frame(self, step):
        step = np.clip(step, 0, self.total_steps - 1)
        t = self.time_vec[step]
        eta = self.ds_eta[step, :]
        return t, eta, self.xc

    def calcular_cinematica_particula(self, x_p, y_p):
        """Calcula la velocidad (u, w) y trayectoria (xi, zeta) de una partícula."""
        if self.ds_eta is None:
            return None, None, None, None

        idx_x = int(np.clip(np.searchsorted(self.xc, x_p), 0, len(self.xc) - 1))
        eta_local = self.ds_eta[:, idx_x].astype(np.float64)
        
        if self.restar_h0:
            eta_local = eta_local - self.h0

        n_quiet = min(20, len(eta_local))
        if n_quiet > 0:
            eta_local = eta_local - np.mean(eta_local[:n_quiet])

        N = len(eta_local)
        fft_eta = np.fft.rfft(eta_local)
        freqs = np.fft.rfftfreq(N, d=self.dt)
        
        g = 9.81
        h = abs(self.h0)
        z = -abs(y_p)

        u_fft = np.zeros_like(fft_eta, dtype=complex)
        w_fft = np.zeros_like(fft_eta, dtype=complex)

        for i, f in enumerate(freqs):
            if f <= 0:
                continue
            omega = 2.0 * np.pi * f
            
            k = omega**2 / g if omega**2 * h / g < 1.0 else omega / np.sqrt(g * h)
            for _ in range(5):
                f_k = g * k * np.tanh(k * h) - omega**2
                df_k = g * np.tanh(k * h) + g * k * h * (1.0 - np.tanh(k * h)**2)
                k = k - f_k / df_k

            cosh_kh = np.cosh(k * h)
            if cosh_kh != 0:
                transfer_u = omega * (np.cosh(k * (z + h)) / np.sinh(k * h))
                transfer_w = omega * (np.sinh(k * (z + h)) / np.sinh(k * h))

                u_fft[i] = fft_eta[i] * transfer_u
                w_fft[i] = fft_eta[i] * transfer_w * 1j

        u_part = np.fft.irfft(u_fft, n=N)
        w_part = np.fft.irfft(w_fft, n=N)

        ruido_base = np.std(eta_local[:n_quiet]) if n_quiet > 1 else 0.0001
        umbral_ola = max(0.002, 3.0 * ruido_base)
        supera_umbral = np.abs(eta_local) >= umbral_ola

        if np.any(supera_umbral):
            idx_inicio_ola = int(np.argmax(supera_umbral))
            while idx_inicio_ola > 0 and np.abs(eta_local[idx_inicio_ola - 1]) > (ruido_base * 1.5):
                idx_inicio_ola -= 1

            if idx_inicio_ola > 0:
                u_part[:idx_inicio_ola] = 0.0
                w_part[:idx_inicio_ola] = 0.0

        xi_part = np.cumsum(u_part) * self.dt
        zeta_part = np.cumsum(w_part) * self.dt

        return u_part, w_part, xi_part, zeta_part

    def cerrar(self):
        if self.h5_file is not None:
            try:
                self.h5_file.close()
            except Exception:
                pass
            self.h5_file = None