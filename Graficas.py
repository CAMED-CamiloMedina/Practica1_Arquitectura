from pathlib import Path
import matplotlib.pyplot as plt
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import json
import re
import webbrowser
import plotly.io as pio
import html


hLines = [12,13,14,18,70,71,329,330,190,191,197,198,204,205,211,212,292]
hsimName = ["A_Processor","P_Processor","T_Leakage","Run_D","A_Core","P_Core","A_L3","P_L3","A_LoadStore","A_DataCache","P_DataCache","P_LoadStore","A_Load","P_Load","A_Store","P_Store","Num_ALU_int"]

lines = [2,9,15,16,17,409,410,411,496,497]
simName = ["simTime","simInst","Cycles","CPI","IPC","ALU_sum","ALU_mult","ALU_div","Load","Store"]

info = []

ruta_principal = Path(__file__).resolve().parent / "experimentos_gem5_McPat_2"

# Buscar todos los archivos llamados mediciones.txt
for archivo in ruta_principal.rglob("stats.txt"):
    #print(f"Procesando archivo: {archivo.parent / 'mcpat_out.txt'}")

    # Abrir y leer el contenido del archivo
    with open(archivo, "r", encoding="utf-8") as f:
        contenido = f.readlines()

    with open(archivo.parent / "mcpat_out.txt", "r", encoding="utf-8") as f:
        contenido2 = f.readlines()
    
    sim = dict(name=archivo.parent.name)

    for i in range(len(lines)):
        sim[simName[i]]= dict(Inst=contenido[lines[i]].split()[0],value=float(contenido[lines[i]].split()[1]))

    for i in range(len(hLines)):
        #sim[hsimName[i]]= dict(Inst=contenido[hLines[i]].split()[0],value=float(contenido[hLines[i]].split()[1]))
        if contenido2[hLines[i]].split()[1] == "=":
            word = ""
        else:
            word = contenido2[hLines[i]].split()[1]
        #print(f"{contenido[hLines[i]].split()[0]+word}={float(contenido[hLines[i]].split()[-2])}")
        sim[hsimName[i]]= dict(Inst=contenido2[hLines[i]].split()[0]+word,value=float(contenido2[hLines[i]].split()[-2]))
        #print(contenido2[hLines[i]])
        
    
    info.append(sim)


for i in range(len(info)):
    valor = (info[i]["T_Leakage"]["value"]+info[i]["Run_D"]["value"])*info[i]["CPI"]["value"]
    info[i]["Energy"] = dict(Inst="Energy", value=valor)
    info[i]["EDP"] = dict(Inst="EDP", value=valor*info[i]["CPI"]["value"])
    info[i]["Num_Load"] = dict(Inst="Num_Load", value=int(info[i]["name"].split('_')[-2].replace("Load","")))
    info[i]["Num_Store"] = dict(Inst="Num_Store", value=int(info[i]["name"].split('_')[-1].replace("Store","")))







import json
import re
import html
import webbrowser
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio


def grafica(info):

    # =========================================================
    # 1. Extraer características y métricas
    # =========================================================

    def numero_memoria(valor):
        coincidencia = re.search(r"(\d+(?:\.\d+)?)", str(valor))
        return float(coincidencia.group(1)) if coincidencia else 0.0

    def obtener_caracteristicas(nombre):
        patrones = {
            "memoria": r"_L3_(.*?)_ALU",
            "alu": r"_ALU(\d+)",
            "load": r"_Load(\d+)",
            "store": r"_Store(\d+)"
        }

        resultado = {}

        for clave, patron in patrones.items():
            coincidencia = re.search(patron, nombre)

            if coincidencia:
                valor = coincidencia.group(1)
                resultado[clave] = (
                    valor if clave == "memoria" else int(valor)
                )
            else:
                resultado[clave] = None

        return resultado

    simulaciones = []
    metricas_disponibles = set()

    for sim in info:
        nombre = sim.get("name", "Simulacion_sin_nombre")
        caracteristicas = obtener_caracteristicas(nombre)

        registro = {
            "name": nombre,
            "datos": sim,
            **caracteristicas
        }

        for clave, valor in sim.items():
            if (
                isinstance(valor, dict)
                and "value" in valor
                and isinstance(valor["value"], (int, float))
                and not isinstance(valor["value"], bool)
            ):
                registro[clave] = valor["value"]
                metricas_disponibles.add(clave)

        simulaciones.append(registro)

    if not simulaciones:
        print("No hay simulaciones para graficar.")
        return

    metricas_disponibles = sorted(metricas_disponibles)

    # =========================================================
    # 2. Preparar los datos para JavaScript
    # =========================================================

    datos_javascript = {}

    for sim in simulaciones:
        datos_javascript[sim["name"]] = {
            "memoria": sim["memoria"],
            "alu": sim["alu"],
            "load": sim["load"],
            "store": sim["store"],
            "metricas": {
                metrica: sim[metrica]
                for metrica in metricas_disponibles
                if metrica in sim
            }
        }

    # =========================================================
    # 3. Opciones para los filtros
    # =========================================================

    memorias = sorted(
        {s["memoria"] for s in simulaciones if s["memoria"] is not None},
        key=numero_memoria
    )

    alus = sorted(
        {s["alu"] for s in simulaciones if s["alu"] is not None}
    )

    loads = sorted(
        {s["load"] for s in simulaciones if s["load"] is not None}
    )

    stores = sorted(
        {s["store"] for s in simulaciones if s["store"] is not None}
    )

    def opciones_select(valores, etiqueta):
        resultado = f'<option value="">{etiqueta}</option>'

        for valor in valores:
            seguro = html.escape(str(valor), quote=True)
            resultado += (
                f'<option value="{seguro}">{seguro}</option>'
            )

        return resultado

    # =========================================================
    # 4. Crear las cuatro gráficas de rendimiento por recurso
    # =========================================================
    #
    # Rendimiento = 1 / simTime
    #
    # Memoria se representa como categoría (por ejemplo, 512KiB
    # o 1MiB), evitando tratar tamaños con unidades diferentes
    # como si fueran directamente comparables numéricamente.
    #
    # ALU, Load y Store se representan con sus valores numéricos.
    # =========================================================

    
    def crear_grafica_recurso(
        id_grafica,
        titulo,
        eje_x,
        clave_x,
        tipo_x="numerico"
    ):
        fig = go.Figure()

        puntos = [
            sim for sim in simulaciones
            if (
                isinstance(sim.get("simTime"), (int, float))
                and sim["simTime"] > 0
                and sim.get(clave_x) is not None
            )
        ]

        # Ordenar por rendimiento: de menor a mayor.
        puntos.sort(key=lambda sim: 1 / sim["simTime"])

        valores_x = [sim[clave_x] for sim in puntos]
        valores_y = [1 / sim["simTime"] for sim in puntos]

        customdata = [
            [
                sim["name"],
                sim["memoria"],
                sim["alu"],
                sim["load"],
                sim["store"],
                sim["simTime"]
            ]
            for sim in puntos
        ]

        fig.add_trace(go.Scatter(
            x=valores_x,
            y=valores_y,
            mode="markers",
            name="Rendimiento",
            customdata=customdata,
            marker=dict(color="#2878B5", size=9),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Memoria L3: %{customdata[1]}<br>"
                "ALU: %{customdata[2]}<br>"
                "Load: %{customdata[3]}<br>"
                "Store: %{customdata[4]}<br>"
                "simTime: %{customdata[5]}<br>"
                "Recurso (" + html.escape(eje_x) + "): %{x}<br>"
                "Performance: %{y}<extra></extra>"
            )
        ))

        fig.update_layout(
            title=titulo,
            xaxis_title=eje_x,
            yaxis_title="Performance = 1 / simTime",
            template="plotly_white",
            height=450,
            margin=dict(l=65, r=30, t=65, b=60),
            clickmode="event+select"
        )

        if tipo_x == "categorico":
            # Mantener las categorías en el orden de rendimiento.
            categorias_ordenadas = list(dict.fromkeys(valores_x))

            fig.update_xaxes(
                type="category",
                categoryorder="array",
                categoryarray=categorias_ordenadas
            )

        return pio.to_html(
            fig,
            full_html=False,
            include_plotlyjs=False,
            div_id=id_grafica
        )


    memoria_html = crear_grafica_recurso(
        id_grafica="grafica_memoria",
        titulo="Performance vs Memoria L3",
        eje_x="Memoria L3",
        clave_x="memoria",
        tipo_x="categorico"
    )

    alu_html = crear_grafica_recurso(
        id_grafica="grafica_alu",
        titulo="Performance vs ALU",
        eje_x="Cantidad de ALU",
        clave_x="alu"
    )

    load_html = crear_grafica_recurso(
        id_grafica="grafica_load",
        titulo="Performance vs Load",
        eje_x="Cantidad de Load",
        clave_x="load"
    )

    store_html = crear_grafica_recurso(
        id_grafica="grafica_store",
        titulo="Performance vs Store",
        eje_x="Cantidad de Store",
        clave_x="store"
    )

    # =========================================================
    # 5. Gráfica de rendimiento frente a energía
    # =========================================================

    fig_energia = go.Figure()

    puntos_energia = [
        sim for sim in simulaciones
        if (
            isinstance(sim.get("simTime"), (int, float))
            and sim["simTime"] > 0
            and "Energy" in sim
        )
    ]

    fig_energia.add_trace(go.Scatter(
        x=[sim["Energy"] for sim in puntos_energia],
        y=[1 / sim["simTime"] for sim in puntos_energia],
        mode="markers",
        name="Rendimiento",
        customdata=[
            [
                sim["name"],
                sim["Energy"],
                sim["simTime"],
                sim["memoria"],
                sim["alu"],
                sim["load"],
                sim["store"]
            ]
            for sim in puntos_energia
        ],
        marker=dict(color="#2878B5", size=9),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Energy: %{customdata[1]}<br>"
            "simTime: %{customdata[2]}<br>"
            "Memoria L3: %{customdata[3]}<br>"
            "ALU: %{customdata[4]}<br>"
            "Load: %{customdata[5]}<br>"
            "Store: %{customdata[6]}<br>"
            "Performance: %{y}<extra></extra>"
        )
    ))

    fig_energia.update_layout(
        title="Performance vs Energy",
        xaxis_title="Energy",
        yaxis_title="Performance = 1 / simTime",
        template="plotly_white",
        height=450,
        margin=dict(l=65, r=30, t=65, b=60),
        clickmode="event+select"
    )

    energia_html = pio.to_html(
        fig_energia,
        full_html=False,
        include_plotlyjs=False,
        div_id="grafica_energia"
    )

    # =========================================================
    # 6. Gráficas para las métricas seleccionables
    # =========================================================

    graficas_metricas_html = []
    configuracion_graficas = []

    for indice, metrica in enumerate(metricas_disponibles):
        puntos = [
            sim for sim in simulaciones
            if metrica in sim
        ]

        puntos.sort(key=lambda sim: sim[metrica])

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=list(range(len(puntos))),
            y=[sim[metrica] for sim in puntos],
            mode="markers",
            name=metrica,
            customdata=[sim["name"] for sim in puntos],
            marker=dict(color="#2878B5", size=8),
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                + html.escape(metrica)
                + ": %{y}<extra></extra>"
            )
        ))

        fig.update_layout(
            title=f"{metrica} vs. simulaciones",
            xaxis_title="Simulaciones",
            yaxis_title=metrica,
            xaxis=dict(showticklabels=False),
            template="plotly_white",
            height=420,
            margin=dict(l=60, r=30, t=65, b=50),
            clickmode="event+select"
        )

        id_contenedor = f"metrica_{indice}"
        id_grafica = f"plot_{id_contenedor}"

        grafica_html = pio.to_html(
            fig,
            full_html=False,
            include_plotlyjs=False,
            div_id=id_grafica
        )

        graficas_metricas_html.append(
            f'<div class="grafica-metrica" id="{id_contenedor}" '
            f'style="display:none;">{grafica_html}</div>'
        )

        configuracion_graficas.append({
            "nombre": metrica,
            "id": id_contenedor
        })

    casillas_metricas = ""

    for grafica_item in configuracion_graficas:
        nombre_seguro = html.escape(grafica_item["nombre"])
        id_seguro = html.escape(grafica_item["id"], quote=True)

        casillas_metricas += f"""
        <label class="opcion-metrica">
            <input type="checkbox"
                   class="checkbox-metrica"
                   value="{id_seguro}">
            <span>{nombre_seguro}</span>
        </label>
        """

    # =========================================================
    # 7. Panel de filtros y configuraciones seleccionadas
    # =========================================================

    panel = f"""
    <div class="panel">

        <h2>Filtros de configuración</h2>

        <div class="filtros">
            <label>Memoria L3
                <select id="filtro_memoria">
                    {opciones_select(memorias, "Todas")}
                </select>
            </label>

            <label>ALU
                <select id="filtro_alu">
                    {opciones_select(alus, "Todas")}
                </select>
            </label>

            <label>Load
                <select id="filtro_load">
                    {opciones_select(loads, "Todos")}
                </select>
            </label>

            <label>Store
                <select id="filtro_store">
                    {opciones_select(stores, "Todos")}
                </select>
            </label>
        </div>

        <div class="botones">
            <button id="btn_configuracion">
                Seleccionar configuración
            </button>

            <button id="btn_limpiar" class="secundario">
                Limpiar selección
            </button>
        </div>

        <h2>Métricas personalizadas</h2>

        <div class="botones">
            <button id="btn_todas_metricas">
                Seleccionar todas
            </button>

            <button id="btn_limpiar_metricas" class="secundario">
                Limpiar métricas
            </button>
        </div>

        <div class="lista-metricas">
            {casillas_metricas}
        </div>

        <h2>Configuraciones seleccionadas</h2>

        <p class="ayuda">
            El color identifica cada configuración en todas las gráficas.
            Despliega una configuración para consultar sus características
            y métricas. Usa × para quitarla individualmente.
        </p>

        <div id="detalles">
            No hay simulaciones seleccionadas.
        </div>

    </div>
    """

    # =========================================================
    # 8. JavaScript para selección y colores sincronizados
    # =========================================================

    javascript = r"""
    <script>
    const caracteristicas = __CARACTERISTICAS__;
    const graficasMetricas = __GRAFICAS_METRICAS__;

    const idsGraficas = [
        "grafica_memoria",
        "grafica_alu",
        "grafica_load",
        "grafica_store",
        "grafica_energia",
        ...graficasMetricas.map(g => "plot_" + g.id)
    ];

    const seleccionadas = new Set();

    function obtenerNombre(customdata) {
        if (Array.isArray(customdata)) {
            return customdata[0];
        }
        return customdata;
    }

    function obtenerColoresSeleccionados() {
        const colores = {};
        let indice = 0;

        seleccionadas.forEach(nombre => {
            const tono = (indice * 137.508) % 360;
            colores[nombre] = `hsl(${tono}, 75%, 45%)`;
            indice++;
        });

        return colores;
    }

    function actualizarColores() {
        const colores = obtenerColoresSeleccionados();

        idsGraficas.forEach(id => {
            const div = document.getElementById(id);

            if (!div || !div.data) return;

            div.data.forEach((traza, indiceTraza) => {
                const customdata = traza.customdata || [];

                const markerColors = customdata.map(dato => {
                    const nombre = obtenerNombre(dato);

                    return seleccionadas.has(nombre)
                        ? colores[nombre]
                        : "#2878B5";
                });

                const markerSizes = customdata.map(dato => {
                    const nombre = obtenerNombre(dato);
                    return seleccionadas.has(nombre) ? 13 : 8;
                });

                Plotly.restyle(div, {
                    "marker.color": [markerColors],
                    "marker.size": [markerSizes]
                }, [indiceTraza]);
            });
        });

        actualizarDetalles();
    }

    // Construir el panel de configuraciones seleccionadas.
    function actualizarDetalles() {
        const contenedor = document.getElementById("detalles");
        const colores = obtenerColoresSeleccionados();

        // Conservar los desplegables que estaban abiertos.
        const abiertos = new Set();

        contenedor.querySelectorAll("details[data-nombre]")
            .forEach(detalle => {
                if (detalle.open) {
                    abiertos.add(detalle.dataset.nombre);
                }
            });

        contenedor.innerHTML = "";

        if (seleccionadas.size === 0) {
            contenedor.textContent = "No hay simulaciones seleccionadas.";
            return;
        }

        Array.from(seleccionadas).forEach(nombre => {
            const sim = caracteristicas[nombre];

            if (!sim) return;

            const bloque = document.createElement("div");
            bloque.className = "detalle-simulacion";

            const encabezado = document.createElement("div");
            encabezado.className = "configuracion-encabezado";

            const indicador = document.createElement("span");
            indicador.className = "indicador-color";
            indicador.style.backgroundColor = colores[nombre] || "#2878B5";
            indicador.title = "Color de esta configuración";

            const titulo = document.createElement("strong");
            titulo.className = "nombre-configuracion";
            titulo.textContent = nombre;

            // Botón × para eliminar una configuración individual.
            const botonEliminar = document.createElement("button");
            botonEliminar.className = "btn-eliminar-config";
            botonEliminar.textContent = "×";
            botonEliminar.title = "Quitar esta configuración";
            botonEliminar.setAttribute(
                "aria-label",
                `Quitar ${nombre}`
            );

            botonEliminar.addEventListener("click", () => {
                seleccionadas.delete(nombre);
                actualizarColores();
            });

            encabezado.appendChild(indicador);
            encabezado.appendChild(titulo);
            encabezado.appendChild(botonEliminar);
            bloque.appendChild(encabezado);

            const desplegable = document.createElement("details");
            desplegable.className = "detalle-desplegable";
            desplegable.dataset.nombre = nombre;
            desplegable.open = abiertos.has(nombre);

            const resumen = document.createElement("summary");
            resumen.textContent = "Ver características y métricas";
            desplegable.appendChild(resumen);

            const subtituloCaracteristicas = document.createElement("h4");
            subtituloCaracteristicas.textContent = "Características";
            desplegable.appendChild(subtituloCaracteristicas);

            const listaCaracteristicas = document.createElement("ul");

            [
                ["Memoria L3", sim.memoria],
                ["ALU", sim.alu],
                ["Load", sim.load],
                ["Store", sim.store]
            ].forEach(([etiqueta, valor]) => {
                if (valor !== null && valor !== undefined) {
                    const elemento = document.createElement("li");
                    elemento.textContent = `${etiqueta}: ${valor}`;
                    listaCaracteristicas.appendChild(elemento);
                }
            });

            desplegable.appendChild(listaCaracteristicas);

            const subtituloMetricas = document.createElement("h4");
            subtituloMetricas.textContent = "Métricas";
            desplegable.appendChild(subtituloMetricas);

            const listaMetricas = document.createElement("ul");

            Object.entries(sim.metricas || {}).forEach(([metrica, valor]) => {
                const elemento = document.createElement("li");
                elemento.textContent = `${metrica}: ${valor}`;
                listaMetricas.appendChild(elemento);
            });

            desplegable.appendChild(listaMetricas);
            bloque.appendChild(desplegable);
            contenedor.appendChild(bloque);
        });
    }

    function alternarSeleccion(nombre) {
        if (seleccionadas.has(nombre)) {
            seleccionadas.delete(nombre);
        } else {
            seleccionadas.add(nombre);
        }

        actualizarColores();
    }

    // Hacer clic en cualquier punto de cualquiera de las gráficas
    // permite seleccionar o deseleccionar esa simulación.
    idsGraficas.forEach(id => {
        const div = document.getElementById(id);

        if (!div) return;

        div.on("plotly_click", evento => {
            const punto = evento.points[0];
            const nombre = obtenerNombre(punto.customdata);

            if (nombre) {
                alternarSeleccion(nombre);
            }
        });
    });

    // Mostrar u ocultar gráficas de métricas.
    document.querySelectorAll(".checkbox-metrica").forEach(casilla => {
        casilla.addEventListener("change", () => {
            const contenedor = document.getElementById(casilla.value);

            if (contenedor) {
                contenedor.style.display = casilla.checked ? "block" : "none";
            }

            if (casilla.checked) {
                const grafica = document.getElementById(
                    "plot_" + casilla.value
                );

                if (grafica && grafica.data) {
                    Plotly.Plots.resize(grafica);
                }
            }
        });
    });

    document.getElementById("btn_todas_metricas")
        .addEventListener("click", () => {
            document.querySelectorAll(".checkbox-metrica")
                .forEach(casilla => {
                    casilla.checked = true;
                    casilla.dispatchEvent(new Event("change"));
                });
        });

    document.getElementById("btn_limpiar_metricas")
        .addEventListener("click", () => {
            document.querySelectorAll(".checkbox-metrica")
                .forEach(casilla => {
                    casilla.checked = false;
                    casilla.dispatchEvent(new Event("change"));
                });
        });

    // Aplicar los filtros de configuración.
    function buscarSimulaciones() {
        const memoria = document.getElementById("filtro_memoria").value;
        const alu = document.getElementById("filtro_alu").value;
        const load = document.getElementById("filtro_load").value;
        const store = document.getElementById("filtro_store").value;

        return Object.entries(caracteristicas)
            .filter(([nombre, sim]) => {
                return (
                    (!memoria || String(sim.memoria) === memoria) &&
                    (!alu || String(sim.alu) === alu) &&
                    (!load || String(sim.load) === load) &&
                    (!store || String(sim.store) === store)
                );
            })
            .map(([nombre]) => nombre);
    }

    document.getElementById("btn_configuracion")
        .addEventListener("click", () => {
            seleccionadas.clear();

            buscarSimulaciones().forEach(nombre => {
                seleccionadas.add(nombre);
            });

            actualizarColores();
        });

    document.getElementById("btn_limpiar")
        .addEventListener("click", () => {
            seleccionadas.clear();

            [
                "filtro_memoria",
                "filtro_alu",
                "filtro_load",
                "filtro_store"
            ].forEach(id => {
                document.getElementById(id).value = "";
            });

            actualizarColores();
        });

    actualizarColores();
    </script>
    """

    javascript = javascript.replace(
        "__CARACTERISTICAS__",
        json.dumps(datos_javascript, ensure_ascii=False)
    )

    javascript = javascript.replace(
        "__GRAFICAS_METRICAS__",
        json.dumps(configuracion_graficas, ensure_ascii=False)
    )

    # =========================================================
    # 9. Construir la página HTML
    # =========================================================

    contenido_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <title>Análisis de simulaciones gem5</title>

        <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>

        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 24px;
                background: #f4f6f8;
                color: #222;
            }}

            h1 {{ margin-top: 0; }}

            h2 {{
                font-size: 19px;
                margin-top: 24px;
            }}

            .panel,
            .grafica-principal,
            .grafica-metrica {{
                background: white;
                border-radius: 10px;
                padding: 18px;
                margin-bottom: 24px;
                box-shadow: 0 2px 8px #00000012;
            }}

            .filtros {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 12px;
            }}

            .filtros label {{
                display: flex;
                flex-direction: column;
                gap: 6px;
                font-weight: bold;
            }}

            select {{
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background: white;
            }}

            .botones {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 14px;
            }}

            button {{
                border: 0;
                border-radius: 5px;
                padding: 10px 14px;
                background: #2468a2;
                color: white;
                cursor: pointer;
            }}

            button:hover {{ opacity: 0.85; }}

            button.secundario {{ background: #626b73; }}

            .lista-metricas {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 8px;
                margin-top: 15px;
            }}

            .opcion-metrica {{
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 9px;
                border: 1px solid #e0e4e8;
                border-radius: 6px;
                background: #fafbfc;
                overflow-wrap: anywhere;
            }}

            .ayuda {{
                color: #606770;
                font-size: 13px;
                line-height: 1.5;
            }}

            .detalle-simulacion {{
                background: #f8fafc;
                border: 1px solid #e0e4e8;
                border-radius: 8px;
                padding: 12px;
                margin: 10px 0;
                overflow-wrap: anywhere;
            }}

            .configuracion-encabezado {{
                display: flex;
                align-items: center;
                gap: 10px;
                min-width: 0;
            }}

            .indicador-color {{
                width: 15px;
                height: 15px;
                min-width: 15px;
                border-radius: 4px;
                border: 1px solid #00000030;
                display: inline-block;
            }}

            .nombre-configuracion {{
                flex: 1;
                min-width: 0;
                overflow-wrap: anywhere;
                font-size: 14px;
            }}

            .btn-eliminar-config {{
                flex-shrink: 0;
                width: 28px;
                height: 28px;
                padding: 0;
                border: none;
                border-radius: 6px;
                background: #fee2e2;
                color: #b91c1c;
                font-size: 21px;
                line-height: 1;
                cursor: pointer;
            }}

            .btn-eliminar-config:hover {{
                background: #fecaca;
                opacity: 1;
            }}

            .detalle-desplegable {{
                margin-top: 10px;
                padding-left: 25px;
            }}

            .detalle-desplegable summary {{
                cursor: pointer;
                color: #2468a2;
                font-size: 13px;
                user-select: none;
            }}

            .detalle-desplegable summary:hover {{
                text-decoration: underline;
            }}

            .detalle-desplegable ul {{
                margin-top: 8px;
                margin-bottom: 12px;
                padding-left: 20px;
            }}

            .detalle-desplegable li {{
                margin: 5px 0;
                font-size: 13px;
            }}

            .detalle-desplegable h4 {{
                margin: 12px 0 5px;
                font-size: 13px;
            }}

            @media (max-width: 600px) {{
                body {{ padding: 10px; }}
            }}
        </style>
    </head>

    <body>
        <h1>Análisis de simulaciones gem5</h1>

        {panel}

        <h2>Rendimiento frente a cada recurso</h2>

        <div class="grafica-principal">
            {memoria_html}
        </div>

        <div class="grafica-principal">
            {alu_html}
        </div>

        <div class="grafica-principal">
            {load_html}
        </div>

        <div class="grafica-principal">
            {store_html}
        </div>

        <h2>Rendimiento frente a energía</h2>

        <div class="grafica-principal">
            {energia_html}
        </div>

        <h2>Métricas seleccionadas</h2>

        <p class="ayuda">
            Marca las métricas que deseas visualizar.
            Puedes mostrar varias gráficas simultáneamente.
        </p>

        {"".join(graficas_metricas_html)}

        {javascript}
    </body>
    </html>
    """

    # =========================================================
    # 10. Guardar y abrir el HTML
    # =========================================================

    ruta = Path("resultados_gem5.html").resolve()
    ruta.write_text(contenido_html, encoding="utf-8")

    print(f"Página generada correctamente: {ruta}")
    webbrowser.open(ruta.as_uri())


#grafica(["simTime", "simInst" ,"A_Processor", "P_Processor" ,"CPI", "IPC",'Energy','EDP'],info)
grafica(info)