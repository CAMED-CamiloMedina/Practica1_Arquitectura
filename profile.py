
ruta_archivo = "stats.txt"  #Ruta del archivo stats.txt generado por gem5


lineas = [3-1, 501-1, 497-1, 498-1, 1509-1, 488-1, 1066-1, 602-1, 874-1]

# Ejemplo del arreglo extraído de las estadísticas:
datos = []

with open(ruta_archivo, 'r') as archivo:
    todas_las_lineas = archivo.readlines()
    
    for i in lineas:
        if i < len(todas_las_lineas):
            linea = todas_las_lineas[i]
            
            # Dividir la línea por espacios en blanco
            partes = linea.split()
            
            # Verificar que la línea no esté en blanco y tenga al menos 2 elementos
            if len(partes) >= 2:
                valor_texto = partes[1] # Toma el '0.100364'
                
                # Convertir el texto a un número flotante
                valor_numerico = float(valor_texto) 
                datos.append(valor_numerico)


tiempo = datos[0]            # 3
alus = datos[1]              # 501
loads = datos[2]             # 497
stores = datos[3]            # 498
l3_missrate = datos[4]       # 1509
total_inst = datos[5]        # 488
l2_missrate = datos[6]       # 1066
l1d_missrate = datos[7]      # 602
l2i_missrate = datos[8]      # 874


if total_inst > 0:
    # 2. Calcular los porcentajes reales
    pct_alus = (alus / total_inst) * 100
    pct_loads = (loads / total_inst) * 100
    pct_stores = (stores / total_inst) * 100
    print(f"Total instrucciones: {total_inst:.0f}")
    print(f"Porcentaje de ALUs:    {pct_alus:.2f}%")
    print(f"Porcentaje de Loads:   {pct_loads:.2f}%")
    print(f"Porcentaje de Stores:  {pct_stores:.2f}%")

    print(f"MissRate de L3: {l3_missrate*100:.2f}%")
    print(f"MissRate de L2: {l2_missrate*100:.2f}%")
    print(f"MissRate de L1D: {l1d_missrate*100:.2f}%")
    print(f"MissRate de L2I: {l2i_missrate*100:.2f}%")