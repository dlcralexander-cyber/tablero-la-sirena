"""
Versión Dash del mismo tablero (mismos datos y mismas figuras que Streamlit).

Ejecutar:  python app_dash.py      ->  abrir http://127.0.0.1:8050
"""
from dash import Dash, Input, Output, dash_table, dcc, html

from nucleo import graficos as g
from nucleo import kpis

AZUL, TEXTO_2, BORDE = "#2a78d6", "#52514e", "#e6e5e1"
ICONO = {"VERDE": "🟢", "AMARILLO": "🟡", "ÁMBAR": "🟡", "ROJO": "🔴", "VENCIDO": "⚫"}
CFG = {"displaylogo": False}

app = Dash(__name__, title="La Sirena · Tablero de Operaciones")
server = app.server  # para desplegar con gunicorn


# ----------------------------------------------------------------------------
# Componentes
# ----------------------------------------------------------------------------
def tarjeta(titulo, valor, nota=None, color_nota=TEXTO_2):
    return html.Div(className="kpi", children=[
        html.Div(titulo, className="kpi-titulo"),
        html.Div(valor, className="kpi-valor"),
        html.Div(nota, className="kpi-nota", style={"color": color_nota}) if nota else None,
    ])


def fila(*hijos, cols=None):
    plantilla = cols or f"repeat({len(hijos)}, minmax(0, 1fr))"
    return html.Div(hijos, className="fila", style={"gridTemplateColumns": plantilla})


def grafico(fig, id_=None):
    return dcc.Graph(figure=fig, config=CFG, **({"id": id_} if id_ else {}))


def decision(texto):
    return html.Div([html.B("🎯 Decisión que habilita: "), texto], className="decision")


def tabla(df, columnas, alto=None, condicional=None):
    return dash_table.DataTable(
        data=df.to_dict("records"),
        columns=[{"name": n, "id": c} for c, n in columnas.items()],
        style_table={"overflowX": "auto", **({"height": alto, "overflowY": "auto"} if alto else {})},
        style_cell={"fontFamily": "Inter, Segoe UI, Arial", "fontSize": 13, "padding": "6px 10px",
                    "textAlign": "left", "border": f"1px solid {BORDE}", "whiteSpace": "normal"},
        style_header={"backgroundColor": "#f0efec", "fontWeight": 600},
        style_data_conditional=condicional or [],
    )


SIMULADO = html.P("🧪 Datos simulados: la empresa aún no registra esta información de forma diaria.",
                  className="nota")


# ----------------------------------------------------------------------------
# Vista 1 · Directorio
# ----------------------------------------------------------------------------
def vista_directorio():
    d = kpis.directorio()
    brecha = d.vejez_tobe - d.meta_vejez
    rojo = "#d03b3b"
    return html.Div([
        html.H1("¿Qué tan sano está nuestro inventario?"),
        html.P("Vista estratégica · problema central: acumulación y falta de rotación del inventario", className="sub"),
        fila(
            tarjeta("Índice de vejez", f"{d.vejez_asis:.1%}", f"+{d.vejez_asis - d.meta_vejez:.1%} vs meta {d.meta_vejez:.0%}", rojo),
            tarjeta("Capital en riesgo", f"S/ {d.capital_en_riesgo / 1000:,.0f} mil"),
            tarjeta("Días de inventario", f"{d.dias_inventario:.1f}", f"rotación {d.rotacion:.1f} veces/año"),
            tarjeta("Exactitud del pronóstico", f"{d.exactitud_pronostico:.1%}", f"sesgo {d.sesgo_pronostico:+.0%}", rojo),
            tarjeta("ERI", f"{d.eri:.0%}", "meta 97 %"),
            tarjeta("Fill rate", f"{d.fill_rate_30d:.1%}", "30 días · simulado"),
        ),
        fila(
            grafico(g.fig_vejez(d)),
            html.Div([
                html.H3("Lectura para el Directorio"),
                html.Ul([
                    html.Li([f"Hoy {d.vejez_asis:.1%} del inventario está vencido, dañado o sin rotar: ",
                             html.B(f"S/ {d.capital_en_riesgo:,.0f}"), "."]),
                    html.Li(["Con los 5 objetivos cumplidos, el índice baja a ", html.B(f"{d.vejez_tobe:.1%}"), "."]),
                    html.Li([f"Quedan {brecha:.1%} sobre la meta de {d.meta_vejez:.0%}: no cierra el ",
                             html.B("stock sin rotación"), ", que debe bajar a ≈ 3 % del inventario."]),
                ]),
                decision("Endurecer la meta del Objetivo 3 o reformular la meta general a ≈ 7 %."),
            ]),
            cols="1.1fr 1fr",
        ),
        fila(grafico(g.fig_pronostico()), grafico(g.fig_vencido_mensual())),
        html.H3("Cartera de objetivos"),
        tabla(kpis.resumen_objetivos(), {c: c for c in kpis.resumen_objetivos().columns}),
    ])


# ----------------------------------------------------------------------------
# Vista 2 · Gerencia de Operaciones
# ----------------------------------------------------------------------------
def vista_gerencia():
    dt = kpis.cargar()
    r1, r2, r3, r4, r5 = dt["o1_res"], dt["o2_res"], dt["o3_res"], dt["o4_res"], dt["o5_res"]
    o4 = dt["o4"]
    alto = o4[o4["riesgo_dano"] == "Alto"]
    oee = kpis.oee_logistico(30)
    res = oee["resumen"]
    verde = "#0a7d0a"

    pestañas = [
        dcc.Tab(label="1 · Kanban", children=[
            fila(tarjeta("Días de inventario", f"{r1['dias_tobe']:.1f}", f"{r1['dias_tobe'] - r1['dias_asis']:+.1f} días", verde),
                 tarjeta("Ahorro costo de mantener", f"S/ {r1['ahorro_costo_mantener']:,.0f}/año"),
                 tarjeta("Capital liberado", f"S/ {r1['capital_liberado']:,.0f}"),
                 tarjeta("Compras evitadas", f"S/ {r1['compras_evitadas']:,.0f}")),
            fila(grafico(g.fig_obj1_dias()),
                 html.Div([tabla(dt["o1"][["producto", "politica", "lead_time_dias", "stock_seguridad", "rop", "lote_q"]].round(0),
                                 {"producto": "Producto", "politica": "Política", "lead_time_dias": "LT (d)",
                                  "stock_seguridad": "SS", "rop": "ROP", "lote_q": "Lote Q"}),
                           decision("Compras emite la orden solo cuando el stock llega al ROP, por el lote Q.")])),
        ]),
        dcc.Tab(label="2 · FEFO", children=[
            fila(tarjeta("Índice de vencido", f"{r2['indice_tobe_prom']:.2%}",
                         f"{r2['indice_tobe_prom'] - r2['indice_asis_prom']:+.2%}", verde),
                 tarjeta("Inversión", f"S/ {r2['inversion']:,.0f}"),
                 tarjeta("Pérdida evitada", f"S/ {r2['perdida_evitada']:,.0f}/año"),
                 tarjeta("Beneficio / costo", f"{r2['beneficio_costo']:.2f}")),
            fila(grafico(g.fig_vencido_mensual()), grafico(g.fig_obj2_curva())),
        ]),
        dcc.Tab(label="3 · ABC + antigüedad", children=[
            fila(tarjeta("% sin rotación (muestra)", f"{r3['pct_sin_rotacion_asis']:.1%}", "meta 5 %"),
                 tarjeta("Valor sin rotación", f"S/ {r3['valor_sin_rotacion_asis']:,.0f}"),
                 tarjeta("Valor a recuperar", f"S/ {r3['valor_sin_rotacion_asis'] - r3['valor_sin_rotacion_tobe']:,.0f}")),
            fila(grafico(g.fig_obj3_antiguedad()), grafico(g.fig_obj3_matriz())),
            decision("Malla raschel (A, 127 d) atención inmediata; tanque 1100 L y cordón 3x14 a venta por lote "
                     "o devolución al proveedor."),
        ]),
        dcc.Tab(label="4 · Layout SLP", children=[
            fila(tarjeta("Índice de mercadería dañada", f"{r4['indice_tobe']:.2%}",
                         f"{r4['indice_tobe'] - r4['indice_asis']:+.2%}", verde),
                 tarjeta("Pérdida evitada", f"S/ {r4['perdida_evitada']:,.0f}/año"),
                 tarjeta("SKU en riesgo alto", f"{len(alto)} de {len(o4)}", f"S/ {alto['valor_stock'].sum():,.0f} en stock")),
            fila(grafico(g.fig_obj4_pq()),
                 html.Div([tabla(alto, {"producto": "Producto", "situacion": "Situación actual",
                                        "tipo_carga": "Tipo de carga", "zona": "Zona"}),
                           decision("Retirar del piso los 8 SKU de riesgo alto y asignarles zona (Z7, Z8, Z9).")]),
                 cols="1.3fr 1fr"),
        ]),
        dcc.Tab(label="5 · ERI", children=[
            fila(tarjeta("ERI", f"{r5['eri_final']:.1%}", f"{r5['eri_final'] - r5['eri_base']:+.1%} vs base", verde),
                 tarjeta("Faltantes valorizados (base)", f"S/ {abs(r5['faltantes_soles']):,.0f}"),
                 tarjeta("Sobrantes valorizados (base)", f"S/ {r5['sobrantes_soles']:,.0f}")),
            grafico(g.fig_obj5_eri()),
            fila(grafico(g.fig_obj5_clase()), grafico(g.fig_obj5_causas())),
        ]),
        dcc.Tab(label="OEE logístico", children=[
            html.P("La Sirena no fabrica: el OEE se adapta al almacén, donde el recurso que se aprovecha es la "
                   "cuadrilla de picking (18 trabajadores)."),
            fila(tarjeta("OEE logístico", f"{res['oee']:.1%}", "clase mundial 85 %"),
                 tarjeta("Disponibilidad", f"{res['disponibilidad']:.1%}", "horas productivas / disponibles"),
                 tarjeta("Rendimiento", f"{res['rendimiento']:.1%}", "líneas por hora / estándar 45"),
                 tarjeta("Calidad", f"{res['calidad']:.1%}", "líneas sin error / preparadas")),
            grafico(g.fig_oee_diario(oee)),
            SIMULADO,
        ]),
    ]
    return html.Div([
        html.H1("Avance de los 5 objetivos"),
        html.P("Vista táctica · cada pestaña muestra el indicador del objetivo, su As-Is y su To-Be", className="sub"),
        dcc.Tabs(pestañas, className="subtabs"),
    ])


# ----------------------------------------------------------------------------
# Vista 3 · Jefe de almacén
# ----------------------------------------------------------------------------
def vista_jefe():
    sem = kpis.semaforo_kanban()
    familias = ["Todas"] + sorted(kpis.cargar()["sim_lotes"]["familia"].unique())
    semanas = sorted(kpis.cargar()["o5_conteos"]["semana"].unique())
    tarjetas = [html.Div(className="kpi", children=[
        html.B(f"{ICONO[r['estado']]} {r['estado']} · {r['sku']}"),
        html.Div(r["producto"], className="kpi-titulo"),
        html.Div(f"{r['stock_cierre']:,.0f}", className="kpi-valor"),
        html.Div(f"ROP {r['rop']:,.0f} · SS {r['ss']:,.0f} · cobertura {r['cobertura_dias']:.0f} días", className="kpi-nota"),
        html.Div(f"➡️ {r['accion']}"),
    ]) for _, r in sem.iterrows()]
    return html.Div([
        html.H1("¿Qué hago hoy en el almacén?"),
        html.P("Vista operativa · reposición Kanban, lotes por vencer y conteos de la semana", className="sub"),
        SIMULADO,
        html.H3("Semáforo de reposición Kanban"),
        fila(*tarjetas),
        dcc.Dropdown(id="sku", options=[{"label": r["producto"], "value": r["sku"]} for _, r in sem.iterrows()],
                     value=sem["sku"].iloc[0], clearable=False),
        dcc.Graph(id="graf-stock", config=CFG),
        html.H3("Lotes por vencer (FEFO)"),
        dcc.Dropdown(id="familia", options=familias, value="Todas", clearable=False),
        fila(dcc.Graph(id="graf-lotes", config=CFG), html.Div(id="tabla-lotes"), cols="1fr 1.4fr"),
        html.H3("Programa de conteos cíclicos"),
        dcc.Slider(id="semana", min=min(semanas), max=max(semanas), step=1, value=max(semanas),
                   marks={int(s): str(s) for s in semanas}),
        html.Div(id="conteos"),
    ])


@app.callback(Output("graf-stock", "figure"), Input("sku", "value"))
def _stock(sku):
    return g.fig_stock_sku(sku)


@app.callback(Output("graf-lotes", "figure"), Output("tabla-lotes", "children"), Input("familia", "value"))
def _lotes(familia):
    lotes = kpis.lotes_fefo(familia)
    urg = lotes[lotes["estado"].isin(["VENCIDO", "ROJO"])].copy()
    urg["estado"] = urg["estado"].map(lambda e: f"{ICONO[e]} {e}")
    urg["valor_soles"] = urg["valor_soles"].map(lambda v: f"S/ {v:,.0f}")
    return g.fig_lotes_estado(lotes), html.Div([
        html.B(f"Despachar primero o mover a cuarentena · {len(urg)} lotes"),
        tabla(urg, {"estado": "Estado", "lote": "Lote", "producto": "Producto", "ubicacion": "Ubicación",
                    "dias_para_vencer": "Días", "unidades": "Und", "valor_soles": "Valor"}, alto="300px"),
    ])


@app.callback(Output("conteos", "children"), Input("semana", "value"))
def _conteos(semana):
    c = kpis.conteos_semana(semana)
    ej = c.dropna(subset=["coincide"])
    dif = c[c["coincide"] == 0]
    return html.Div([
        fila(tarjeta("Conteos programados", f"{len(c)}"),
             tarjeta("ERI de la semana", f"{ej['coincide'].mean():.1%}"),
             tarjeta("Con diferencia", f"{(ej['coincide'] == 0).sum()}")),
        tabla(dif, {"codigo": "SKU", "ubicacion": "Ubicación", "clase": "Clase", "cant_sistema": "Sistema",
                    "cant_final": "Físico", "diferencia": "Diferencia", "causa": "Causa"}),
    ])


# ----------------------------------------------------------------------------
# Layout general
# ----------------------------------------------------------------------------
app.layout = html.Div(className="pagina", children=[
    html.Div(className="cabecera", children=[
        html.Div([html.B("📦 Corporación La Sirena"), html.Span(" · Centro de distribución Lurín")]),
        html.Span(f"Corte: {kpis.FECHA_CORTE:%d/%m/%Y} · Fuentes: Excel del proyecto (diagnóstico y objetivos) "
                  "+ operación diaria simulada", className="nota"),
    ]),
    dcc.Tabs(className="vistas", children=[
        dcc.Tab(label="Directorio · estratégica", children=vista_directorio()),
        dcc.Tab(label="Gerencia de Operaciones · táctica", children=vista_gerencia()),
        dcc.Tab(label="Jefe de almacén · operativa", children=vista_jefe()),
    ]),
])

if __name__ == "__main__":
    app.run(debug=False, port=8050)
