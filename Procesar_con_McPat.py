import subprocess
from pathlib import Path

# --- CONFIGURACIÓN DE RUTAS BASE ---
BASE_DIR = Path("experimentos_gem5_McPat")

# Script conversor y plantilla de arquitectura ARM Cortex-A76
CONVERTER_SCRIPT = Path("scripts/McPAT/gem5toMcPAT_cortexA76.py").resolve()
TEMPLATE_XML = Path("scripts/McPAT/ARM_A76_2.1GHz.xml").resolve()

# Ejecutable de McPAT y nivel de detalle de salida
MCPAT_EXEC = Path("/home/camed/gem5/mcpat/mcpat").resolve()
PRINT_LEVEL = 5


def procesar_experimentos():
    base_path = Path(BASE_DIR)

    if not base_path.exists():
        print(f" Error: La carpeta '{BASE_DIR}' no existe.")
        return

    # Busca recursivamente todas las subcarpetas que contengan 'stats.txt'
    stats_files = list(base_path.glob("**/stats.txt"))

    if not stats_files:
        print(" No se encontraron archivos 'stats.txt'.")
        return

    print(f"Se encontraron {len(stats_files)} experimentos en '{BASE_DIR}'. Iniciando...\n")

    for i, stats_path in enumerate(stats_files, 1):
        exp_dir = stats_path.parent
        config_json = exp_dir / "config.json"
        config_xml = exp_dir / "config.xml"
        mcpat_out = exp_dir / "mcpat_out.txt"

        print(f"[{i}/{len(stats_files)}] Procesando carpeta: {exp_dir.name}")

        if not config_json.exists():
            print(f"   Omitiendo: No se encontró 'config.json' en {exp_dir}")
            continue

        # --- PASO 1: Generar config.xml dentro de la carpeta del experimento ---
        # Ejecutamos con cwd=exp_dir para que gem5toMcPAT guarde config.xml en la carpeta correcta
        cmd_convert = [
            "python3",
            str(CONVERTER_SCRIPT),
            stats_path.name,   # stats.txt
            config_json.name,  # config.json
            str(TEMPLATE_XML)  # Plantilla ARM A76
        ]

        try:
            subprocess.run(
                cmd_convert,
                cwd=exp_dir,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"   Error en Paso 1 (gem5toMcPAT):\n{e.stderr}")
            continue
        except Exception as e:
            print(f"   Error inesperado en Paso 1: {e}")
            continue

        if not config_xml.exists():
            print(f"   Error: No se generó 'config.xml' en {exp_dir}")
            continue

        # --- PASO 2: Ejecutar McPAT en el config.xml recién generado ---
        cmd_mcpat = [
            str(MCPAT_EXEC),
            "-infile",
            config_xml.name,
            "-print_level",
            str(PRINT_LEVEL)
        ]

        try:
            with open(mcpat_out, "w") as out_f:
                subprocess.run(
                    cmd_mcpat,
                    cwd=exp_dir,
                    stdout=out_f,
                    stderr=subprocess.PIPE,
                    check=True
                )
            print(f"   Completado: Se guardaron 'config.xml' y 'mcpat_out.txt'")
        except subprocess.CalledProcessError as e:
            print(f"   Error en Paso 2 (McPAT):\n{e.stderr.decode()}")
        except Exception as e:
            print(f"   Error inesperado en Paso 2: {e}")

    print("\n¡Procesamiento masivo finalizado exitosamente!")


if __name__ == "__main__":
    procesar_experimentos()