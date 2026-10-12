import os
import time
from pathlib import Path
import numpy as np
import scipy.io as sio
import h5py

def es_mat_v73(mat_path):
    """Comprueba si el archivo .mat ya es internamente un HDF5 (v7.3)."""
    try:
        with h5py.File(mat_path, 'r') as f:
            return True
    except (OSError, ValueError):
        return False

def inspeccionar_y_convertir(directorio_origen, directorio_destino=None, prefijo = ""):
    """
    Escanea la carpeta de origen, analiza la versión de cada .mat y
    lo convierte a .h5 si es necesario.
    """
    origen_path = Path(directorio_origen)
    destino_path = Path(directorio_destino) if directorio_destino else origen_path
    destino_path.mkdir(parents=True, exist_ok=True)

    archivos_mat = sorted(list(origen_path.glob("*.mat")))

    if not archivos_mat:
        print(f"❌ No se encontraron archivos .mat en: {origen_path.resolve()}")
        return

    print(f"🔍 Encontrados {len(archivos_mat)} archivos .mat\n" + "="*60)

    for i, archivo in enumerate(archivos_mat, start=1):
        tamano_mb = archivo.stat().st_size / (1024 * 1024)
        print(f"[{i}/{len(archivos_mat)}] Procesando: {archivo.name} ({tamano_mb:.1f} MB)")

        es_v73 = es_mat_v73(archivo)

        if es_v73:
            print("   └─ Versión: MATLAB v7.3 (Compatibilidad HDF5 nativa).")
            print("   └─ Status: ✅ Listo para lectura directa. No requiere conversión.")
        else:
            print("   └─ Versión: MATLAB v5/v7 (Formato binario heredado).")
            print("   └─ Iniciando conversión a HDF5...")
            
            h5_salida = destino_path / f"{prefijo}_{archivo.stem}.h5"
            t0 = time.time()
            
            try:
                # Carga de datos legados
                data = sio.loadmat(archivo, squeeze_me=True)
                
                with h5py.File(h5_salida, 'w') as h5f:
                    for key, val in data.items():
                        # Omitir metadatos internos de MATLAB
                        if key.startswith('__'):
                            continue
                        
                        if isinstance(val, np.ndarray):
                            # Compresión lzf/gzip para acelerar la lectura en disco
                            h5f.create_dataset(
                                key, 
                                data=val, 
                                compression="gzip", 
                                compression_opts=4
                            )
                            print(f"      ├─ Variable '{key}': Forma {val.shape}, Tipo {val.dtype}")
                        else:
                            h5f.attrs[key] = val

                t_total = time.time() - t0
                tamano_h5 = h5_salida.stat().st_size / (1024 * 1024)
                print(f"   └─ ✅ Convertido a {h5_salida.name} ({tamano_h5:.1f} MB) en {t_total:.2f}s")

            except Exception as e:
                print(f"   └─ ❌ Error al convertir {archivo.name}: {e}")

        print("-" * 60)

if __name__ == "__main__":
    # Sustituye '.' por la ruta donde se encuentran tus 7 archivos .mat
    RUTA_DATOS = "../Experiment7"
    DESTINO = "./data"
    PREFIJO = "Exp7"
    inspeccionar_y_convertir(RUTA_DATOS, DESTINO, PREFIJO)