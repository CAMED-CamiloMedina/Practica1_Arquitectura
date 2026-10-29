import os
import subprocess
from itertools import product
from multiprocessing import Pool

def parsear_stats(directorio_sim):
    """Extrae métricas clave del stats.txt dentro de la subcarpeta de la simulación."""
    stats_path = os.path.join(directorio_sim, "stats.txt")
    if not os.path.exists(stats_path):
        return None

    metricas = {}
    with open(stats_path, "r") as f:
        for line in f:
            if not line.strip() or line.startswith("---"):
                continue
            partes = line.split()
            if len(partes) >= 2:
                stat_name = partes[0]
                stat_val = partes[1]
                if stat_name == "simSeconds":
                    metricas["sim_seconds"] = float(stat_val)
                elif "l1i.overallMissRate::total" in stat_name or "icache.overallMissRate::total" in stat_name:
                    metricas["l1i_miss_rate"] = float(stat_val)
                elif "l1d.overallMissRate::total" in stat_name or "dcache.overallMissRate::total" in stat_name:
                    metricas["l1d_miss_rate"] = float(stat_val)
                elif stat_name == "system.cpu.ipc":
                    metricas["ipc"] = float(stat_val)
    return metricas

def ejecutar_simulacion(config):
    """
    Ejecuta una simulación con su propia carpeta dedicada dentro del directorio contenedor principal.
    config: Tupla (l3_size, l2_size, l1_size)
    """
    l3_size,num_alu,num_load,num_store = config
    
    # 1. Directorio principal contenedor de todo el experimento
    directorio_raiz = "experimentos_gem5"
    
    # 2. Nombre y ruta de la subcarpeta específica para ESTA simulación
    nombre_subcarpeta = f"sim_L3_{l3_size}_ALU{num_alu}_Load{num_load}_Store{num_store}"
    ruta_subcarpeta = os.path.abspath(os.path.join(directorio_raiz, nombre_subcarpeta))
    
    # Crear la subcarpeta
    os.makedirs(ruta_subcarpeta, exist_ok=True)
    
    # 3. Rutas absolutas a los binarios y scripts para evitar errores con paths relativos
    gem5_binary = os.path.abspath("./build/ARM/gem5.fast")
    script_config = os.path.abspath("scripts/CortexA76_scripts_gem5/CortexA76.py")
    input_file = os.path.abspath("workloads/mp3_dec/mp3dec_testfile.mp3")
    executable_workload = os.path.abspath("workloads/mp3_dec/mp3_dec")
    
    # La salida de la imagen se guardará directamente dentro de la subcarpeta
    comando_workload = f"-s -i {input_file} > /dev/null"
    
    argumentos = [
        gem5_binary,
        f"--outdir={ruta_subcarpeta}", 
        script_config,
        "-c", executable_workload,
        "-o", comando_workload,
        f"--l3_size={l3_size}",
        f"--num_fu_intALU={num_alu}",
        f"--num_fu_read={num_load}",
        f"--num_fu_write={num_store}"
    ]
    
    print(f" [Lanzando] L3={l3_size} | Alu={num_alu} | Load={num_load} | Store={num_store}")
    
    # Al especificar cwd=ruta_subcarpeta, se asegura que cualquier archivo temporal
    # o log secundario generado por la carga de trabajo quede dentro de su carpeta.
    resultado = subprocess.run(
        argumentos, 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL,
        cwd=ruta_subcarpeta
    )
    
    if resultado.returncode != 0:
        print(f"[ERROR] Falló la combinación en: {nombre_subcarpeta}")
        return (config, "Error", None)
    
    stats = parsear_stats(ruta_subcarpeta)
    print(f" [ÉXITO] Guardado en: {nombre_subcarpeta}")
    return (config, "Ok", stats)

if __name__ == "__main__":
    # Combinaciones de cachés
    valores_l3 = ["1MiB", "2MiB", "4MiB"]
    valores_alu = [1,2,3,4,6,8,10]
    valores_load = [4,6,8,10]
    valores_store = [8,10]

    
    # 7 x 7 x 7 x 3 = 1029 configuraciones únicas
    configuraciones = list(product(valores_l3, valores_alu,valores_load,valores_store))
    
    print(f"Iniciando {len(configuraciones)} simulaciones en total.")
    print("Ejecutando en tandas de 3 procesos simultáneos...\n")
    
    num_procesos_paralelos = 3 
    
    with Pool(processes=num_procesos_paralelos) as pool:
        resultados = pool.map(ejecutar_simulacion, configuraciones)
        
    print("\n🏁 ¡Todas las simulaciones han finalizado!")
    print("Estructura generada:")
    print(" └── experimentos_gem5/")
    print("      ├── sim_L3_1MiB_L2_128KiB_L1_16KiB/")
    print("      │    ├── stats.txt")
    print("      │    ├── config.ini")
    print("      │    ├── config.json")
    print("      │    └── output_decoded.pgm")
    print("      ├── sim_L3_1MiB_L2_128KiB_L1_32KiB/")
    print("      └── ... (45 carpetas en total)")