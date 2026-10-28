"""
Figuras Plotly compartidas por Streamlit y Dash.
Reglas de diseño: un solo eje Y por gráfico, colores por identidad en orden fijo,
colores de estado reservados para semáforos (siempre con texto), líneas de 2 px.
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from . import kpis

# --- Paleta (validada para daltonismo en orden adyacente) ---------------------
AZUL, NARANJA, AGUA = "#2a78d6", "#eb6834", "#1baf7a"
GRIS = "#8a8984"
TEXTO, TEXTO_2, REJILLA, FONDO = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"
ESTADO = {"VERDE": "#0ca30c", "AMARILLO": "#fab219", "ÁMBAR": "#fab219",
          "ROJO": "#d03b3b", "VENCIDO": "#5b1d1d",
          "Bajo": "#0ca30c", "Medio": "#fab219", "Alto": "#d03b3b"}
SECUENCIAL = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]

pio.templates["sirena"] = go.layout.Template(layout=dict(
    font=dict(family="Inter, Segoe UI, Arial, sans-serif", size=13, color=TEXTO),
    paper_bgcolor=FONDO, plot_bgcolor=FONDO,
    colorway=[AZUL, NARANJA, AGUA],
    xaxis=dict(automargin=True, gridcolor=REJILLA, linecolor=REJILLA, zeroline=False, tickfont=dict(color=TEXTO_2)),
    yaxis=dict(automargin=True, gridcolor=REJILLA, linecolor=REJILLA, zeroline=False, tickfont=dict(color=TEXTO_2)),
    legend=dict(orientation="h", y=-0.12, yanchor="top", x=0, font=dict(color=TEXTO_2)),
    hoverlabel=dict(bgcolor="white", font_size=12),
    margin=dict(l=10, r=10, t=70, b=10),
    title=dict(font=dict(size=16), x=0, xanchor="left"),
))
pio.templates.default = "plotly_white+sirena"


def _titulo(fig, texto, sub=None):
    t = f"<b>{texto}</b>" + (f"<br><span style='font-size:12px;color:{TEXTO_2}'>{sub}</span>" if sub else "")
    fig.update_layout(title_text=t, plot_bgcolor=FONDO, paper_bgcolor=FONDO)
    if fig.layout.xaxis.title.text:          # deja espacio entre el título del eje y la leyenda
        fig.update_layout(legend_y=-0.24)
    return fig


# ============================================================================
# DIRECTORIO
# ============================================================================
def fig_vejez(dir_: kpis.Directorio):
    """Composición del índice de vejez: As-Is vs proyección, contra la meta."""
    c = dir_.componentes
    fig = go.Figure()
    for comp, color in zip(c["componente"].unique(), [NARANJA, AGUA, AZUL]):
        sub = c[c["componente"] == comp]
        fig.add_bar(x=sub["escenario"], y=sub["pct_inventario"], name=comp, marker_color=color,
                    customdata=sub["soles"],
                    hovertemplate="%{x}<br>" + comp + ": %{y:.1%} (S/ %{customdata:,.0f})<extra></extra>")
    totales = c.groupby("escenario", sort=False)["pct_inventario"].sum()
    for esc, v in totales.items():
        fig.add_annotation(x=esc, y=v, text=f"<b>{v:.1%}</b>", showarrow=False, yshift=12)
    fig.add_hline(y=dir_.meta_vejez, line_dash="dash", line_color=TEXTO_2, line_width=2,
                  annotation_text=f"Meta {dir_.meta_vejez:.0%}", annotation_position="top right")
    fig.update_layout(barmode="stack", bargap=0.45, yaxis_tickformat=".0%", height=420)
    return _titulo(fig, "Índice de vejez del inventario",
                   "Vencido + dañado + sin rotación, como % del inventario total")


def fig_pronostico():
    m = kpis.cargar()["mensual"]
    fig = go.Figure()
    fig.add_scatter(x=m["mes"], y=m["demanda_pronosticada"], name="Pronosticada", mode="lines+markers",
                    line=dict(color=NARANJA, width=2), marker_size=8,
                    hovertemplate="%{x}: S/ %{y:,.0f}<extra>Pronosticada</extra>")
    fig.add_scatter(x=m["mes"], y=m["demanda_real"], name="Real", mode="lines+markers",
                    line=dict(color=AZUL, width=2), marker_size=8,
                    hovertemplate="%{x}: S/ %{y:,.0f}<extra>Real</extra>")
    fig.update_layout(yaxis_tickprefix="S/ ", yaxis_tickformat=",.0f", height=380, hovermode="x unified")
    return _titulo(fig, "Demanda pronosticada vs real (2025)",
                   "El pronóstico supera a la venta real los 12 meses: es sesgo, no error aleatorio")


def fig_vencido_mensual():
    d = kpis.cargar()
    m, p = d["mensual"], d["o2_proy"]
    fig = go.Figure()
    fig.add_scatter(x=m["fecha"], y=m["vencido"] / m["inventario_total"], name="Real 2025",
                    mode="lines+markers", line=dict(color=AZUL, width=2), marker_size=8,
                    hovertemplate="%{x|%m/%Y}: %{y:.2%}<extra>Real</extra>")
    fig.add_scatter(x=p["fecha"], y=p["indice_vencido"], name="Proyección 2026 con FEFO",
                    mode="lines+markers", line=dict(color=AZUL, width=2, dash="dot"), marker_size=8,
                    hovertemplate="%{x|%m/%Y}: %{y:.2%}<extra>Proyección</extra>")
    fig.add_hline(y=d["o2_res"]["estandar"], line_dash="dash", line_color=TEXTO_2,
                  annotation_text="Estándar 0.34 %", annotation_position="bottom right")
    fig.update_layout(yaxis_tickformat=".1%", height=380, yaxis_rangemode="tozero", xaxis_tickformat="%m/%Y")
    return _titulo(fig, "Índice de inventario vencido", "Objetivo 2 · la proyección es simulada")


# ============================================================================
# GERENCIA DE OPERACIONES
# ============================================================================
def fig_obj1_dias():
    o = kpis.cargar()["o1"]
    fig = go.Figure()
    fig.add_bar(y=o["producto"], x=o["dias_asis"], orientation="h", name="As-Is",
                marker_color=NARANJA, hovertemplate="%{y}<br>As-Is: %{x:.1f} días<extra></extra>")
    fig.add_bar(y=o["producto"], x=o["dias_tobe"], orientation="h", name="To-Be (Kanban)",
                marker_color=AZUL, text=[f"{v:.1f} d" if v else "contra pedido" for v in o["dias_tobe"]],
                textposition="outside", hovertemplate="%{y}<br>To-Be: %{x:.1f} días<extra></extra>")
    fig.update_layout(barmode="group", height=380, xaxis_title="Días de inventario",
                      yaxis_autorange="reversed")
    return _titulo(fig, "Días de inventario por SKU estrella", "Objetivo 1 · Kanban + ROP + EOQ")


def fig_obj2_curva():
    c = kpis.cargar()["o2_curva"]
    fig = go.Figure()
    fig.add_scatter(x=c["semana"], y=c["Despachos conformes FEFO"], name="Despachos conformes FEFO",
                    mode="lines", line=dict(color=AZUL, width=2),
                    hovertemplate="Semana %{x}: %{y:.0%}<extra>Conformes FEFO</extra>")
    fig.add_scatter(x=c["semana"], y=c["Promedio semanal"], name="Promedio de los 6 controles",
                    mode="lines", line=dict(color=NARANJA, width=2),
                    hovertemplate="Semana %{x}: %{y:.0%}<extra>Promedio controles</extra>")
    fig.update_layout(yaxis_tickformat=".0%", xaxis_title="Semana desde el arranque", height=380,
                      hovermode="x unified", yaxis_range=[0, 1.05])
    return _titulo(fig, "Curva de aprendizaje FEFO", "Objetivo 2 · cumplimiento semanal proyectado")


def fig_obj3_antiguedad():
    t = kpis.antiguedad_buckets()
    g = t.groupby("tramo", observed=False)["valor"].sum().reset_index()
    colores = [SECUENCIAL[1], SECUENCIAL[2], SECUENCIAL[3], SECUENCIAL[4]]
    fig = go.Figure(go.Bar(x=g["tramo"].astype(str), y=g["valor"], marker_color=colores,
                           text=[f"S/ {v:,.0f}" for v in g["valor"]], textposition="outside",
                           hovertemplate="%{x}: S/ %{y:,.0f}<extra></extra>"))
    fig.update_layout(yaxis_tickprefix="S/ ", yaxis_tickformat=",.0f", height=360, showlegend=False)
    return _titulo(fig, "Valor del inventario por antigüedad", "Objetivo 3 · días sin movimiento")


def fig_obj3_matriz():
    t = kpis.antiguedad_buckets()
    piv = t.pivot_table(index="clase_abc", columns="tramo", values="valor", aggfunc="sum",
                        fill_value=0, observed=False).reindex(["A", "B", "C"])
    fig = go.Figure(go.Heatmap(
        z=piv.values, x=[str(c) for c in piv.columns], y=[f"Clase {i}" for i in piv.index],
        colorscale=[[0, "#f0efec"], [0.01, SECUENCIAL[0]], [1, SECUENCIAL[4]]],
        text=[[f"S/ {v:,.0f}" if v else "—" for v in fila] for fila in piv.values],
        texttemplate="%{text}", xgap=2, ygap=2, showscale=False,
        hovertemplate="%{y} · %{x}: %{text}<extra></extra>"))
    fig.update_layout(height=320, yaxis_autorange="reversed")
    return _titulo(fig, "Matriz ABC × antigüedad", "Color = valor en stock · clase A con > 90 días = atención inmediata")


def fig_obj4_pq():
    o = kpis.cargar()["o4"].sort_values("consumo_anual")
    fig = go.Figure()
    for riesgo in ["Alto", "Medio", "Bajo"]:
        s = o[o["riesgo_dano"] == riesgo]
        fig.add_bar(y=s["producto"], x=s["consumo_anual"], orientation="h", name=f"Riesgo {riesgo.lower()}",
                    marker_color=ESTADO[riesgo], customdata=s[["clase_pq", "zona", "situacion"]],
                    hovertemplate="%{y}<br>Consumo: %{x:,} und/año<br>Clase %{customdata[0]} · "
                                  "Zona %{customdata[1]}<br>%{customdata[2]}<extra></extra>")
    fig.update_layout(height=720, xaxis_title="Consumo anual (und)", barmode="overlay",
                      yaxis=dict(categoryorder="array", categoryarray=o["producto"].tolist()))
    _titulo(fig, "Análisis P-Q y riesgo de daño (30 SKU)",
            "Objetivo 4 · SLP · color = riesgo según su ubicación actual")
    return fig.update_layout(legend_y=-0.1)


def fig_obj5_eri():
    e = kpis.eri_semanal()
    meta = kpis.cargar()["o5_res"]["meta"]
    base = kpis.cargar()["o5_res"]["eri_base"]
    fig = go.Figure()
    fig.add_scatter(x=e["semana"], y=e["eri"], name="ERI semanal", mode="lines+markers",
                    line=dict(color=AZUL, width=2), marker_size=8,
                    customdata=e[["coinciden", "contados"]],
                    hovertemplate="Semana %{x}: %{y:.1%}<br>%{customdata[0]} de %{customdata[1]} ítems"
                                  "<extra></extra>")
    fig.add_hline(y=meta, line_dash="dash", line_color=TEXTO_2, annotation_text=f"Meta {meta:.0%}",
                  annotation_position="top left")
    fig.add_hline(y=base, line_dash="dot", line_color=GRIS, annotation_text=f"Línea base {base:.0%}",
                  annotation_position="bottom left")
    fig.update_layout(yaxis_tickformat=".0%", yaxis_range=[0.8, 1.0], height=380,
                      xaxis_title="Semana del programa de conteos")
    return _titulo(fig, "Exactitud del registro de inventario (ERI)", "Objetivo 5 · conteos cíclicos ABC")


def fig_obj5_clase():
    e = kpis.eri_por_clase()
    fig = go.Figure()
    for per, color in [("Línea base", NARANJA), ("Semanas 23–26", AZUL)]:
        s = e[e["periodo"] == per]
        fig.add_bar(x="Clase " + s["clase"], y=s["eri"], name=per, marker_color=color,
                    text=[f"{v:.0%}" for v in s["eri"]], textposition="outside",
                    hovertemplate="%{x}: %{y:.1%}<extra>" + per + "</extra>")
    fig.update_layout(barmode="group", yaxis_tickformat=".0%", yaxis_range=[0, 1.1], height=360)
    return _titulo(fig, "ERI por clase ABC", "Base vs cierre del programa")


def fig_obj5_causas():
    c = kpis.cargar()["o5_causas"].sort_values("n")
    fig = go.Figure(go.Bar(y=c["causa"], x=c["n"], orientation="h", marker_color=AZUL,
                           text=c["n"], textposition="outside",
                           hovertemplate="%{y}: %{x} diferencias<extra></extra>"))
    fig.update_layout(height=340, showlegend=False, xaxis_title="N.° de diferencias (conteo base)")
    return _titulo(fig, "Causas de las diferencias de inventario", "49 diferencias en 350 ítems contados")


def fig_oee_diario(oee: dict):
    p = oee["diario"]
    fig = go.Figure()
    fig.add_scatter(x=p["fecha"], y=p["oee"], name="OEE logístico", mode="lines+markers",
                    line=dict(color=AZUL, width=2), marker_size=8,
                    customdata=p[["disponibilidad", "rendimiento", "calidad"]],
                    hovertemplate="%{x|%d/%m}<br>OEE %{y:.1%}<br>D %{customdata[0]:.1%} · "
                                  "R %{customdata[1]:.1%} · C %{customdata[2]:.1%}<extra></extra>")
    fig.add_hline(y=0.85, line_dash="dash", line_color=TEXTO_2, annotation_text="Clase mundial 85 %",
                  annotation_position="top left")
    fig.update_layout(yaxis_tickformat=".0%", yaxis_range=[0.5, 1.0], height=360, showlegend=False,
                      xaxis_tickformat="%d/%m")
    return _titulo(fig, "OEE logístico diario (últimos 30 días)", "Datos simulados")


# ============================================================================
# JEFE DE ALMACÉN
# ============================================================================
def fig_stock_sku(sku: str):
    s = kpis.cargar()["sim_stock"]
    s = s[s["sku"] == sku]
    s = s[s["fecha"] > s["fecha"].max() - pd.Timedelta(days=90)]
    fig = go.Figure()
    fig.add_scatter(x=s["fecha"], y=s["stock_cierre"], name="Stock", mode="lines",
                    line=dict(color=AZUL, width=2), hovertemplate="%{x|%d/%m}: %{y:,.0f}<extra>Stock</extra>")
    lleg = s[s["llegada"] > 0]
    fig.add_scatter(x=lleg["fecha"], y=lleg["stock_cierre"], name="Llegada de lote", mode="markers",
                    marker=dict(color=AGUA, size=10, symbol="triangle-up", line=dict(color=FONDO, width=2)),
                    hovertemplate="%{x|%d/%m}: llegó un lote<extra></extra>")
    rop, ss = s["rop"].iloc[0], s["ss"].iloc[0]
    fig.add_hline(y=rop, line_dash="dash", line_color=ESTADO["AMARILLO"], line_width=2,
                  annotation_text=f"ROP {rop:,.0f}", annotation_position="top left")
    fig.add_hline(y=ss, line_dash="dash", line_color=ESTADO["ROJO"], line_width=2,
                  annotation_text=f"Stock de seguridad {ss:,.0f}", annotation_position="bottom left")
    fig.update_layout(height=380, yaxis_title="Unidades", yaxis_rangemode="tozero", hovermode="x unified",
                      xaxis_tickformat="%d/%m")
    return _titulo(fig, f"Stock diario · {s['producto'].iloc[0]}", "Últimos 90 días · datos simulados")


def fig_lotes_estado(lotes):
    orden = ["VENCIDO", "ROJO", "ÁMBAR", "VERDE"]
    g = lotes.groupby("estado")["valor_soles"].sum().reindex(orden, fill_value=0)
    etiquetas = {"VENCIDO": "Vencido", "ROJO": "Rojo ≤ 30 d", "ÁMBAR": "Ámbar 31–90 d", "VERDE": "Verde > 90 d"}
    fig = go.Figure(go.Bar(x=[etiquetas[e] for e in g.index], y=g.values,
                           marker_color=[ESTADO[e] for e in g.index],
                           text=[f"S/ {v:,.0f}" for v in g.values], textposition="outside",
                           hovertemplate="%{x}: S/ %{y:,.0f}<extra></extra>"))
    fig.update_layout(height=340, showlegend=False, yaxis_tickprefix="S/ ", yaxis_tickformat=",.0f")
    return _titulo(fig, "Valor en stock por estado de vencimiento", "Datos simulados")
