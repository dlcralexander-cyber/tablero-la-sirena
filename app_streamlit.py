"""
Tablero de Gestión Estratégica de Operaciones · Corporación La Sirena S.A.C.
CD Lurín · Streamlit + Plotly

Ejecutar:  streamlit run app_streamlit.py
"""
import pandas as pd
import streamlit as st

from nucleo import graficos as g
from nucleo import kpis

st.set_page_config(page_title="La Sirena · Tablero de Operaciones", page_icon="📦", layout="wide")

ICONO = {"VERDE": "🟢", "AMARILLO": "🟡", "ÁMBAR": "🟡", "ROJO": "🔴", "VENCIDO": "⚫"}
PLOT = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]}


def grafico(fig):
    st.plotly_chart(fig, width="stretch", config=PLOT, theme=None)


def nota_simulado():
    st.caption("🧪 **Datos simulados**: la empresa aún no registra esta información de forma diaria. "
               "Se reemplazan por datos reales cuando operen el QR (Obj. 2) y la codificación de ubicaciones (Obj. 5).")


def decision(texto):
    st.info(f"**Decisión que habilita:** {texto}", icon="🎯")


# ----------------------------------------------------------------------------
# Barra lateral
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📦 Corporación La Sirena")
    st.caption("Centro de distribución Lurín")
    vista = st.radio("Vista", ["Directorio", "Gerencia de Operaciones", "Jefe de almacén"],
                     captions=["Estratégica", "Táctica · 5 objetivos", "Operativa · día a día"])
    st.divider()
    st.caption(f"Corte de datos: {kpis.FECHA_CORTE:%d/%m/%Y}")
    st.caption("**Fuentes**\n\n📊 Diagnóstico y objetivos: Excel del proyecto final (GEESOP 2026-2)\n\n"
               "🧪 Operación diaria: simulada y rotulada")

# ============================================================================
# VISTA 1 · DIRECTORIO
# ============================================================================
if vista == "Directorio":
    d = kpis.directorio()
    st.title("¿Qué tan sano está nuestro inventario?")
    st.caption("Vista estratégica para el Directorio · problema central: acumulación y falta de rotación del inventario")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Índice de vejez", f"{d.vejez_asis:.1%}", f"{d.vejez_asis - d.meta_vejez:+.1%} vs meta {d.meta_vejez:.0%}",
              delta_color="inverse", help="(Vencido + Dañado + Sin rotación) / Valor total del inventario")
    c2.metric("Capital en riesgo", f"S/ {d.capital_en_riesgo / 1000:,.0f} mil",
              help="Vencido S/ 74,650 + dañado S/ 51,280 + sin rotación S/ 265,000")
    c3.metric("Días de inventario", f"{d.dias_inventario:.1f}", f"rotación {d.rotacion:.1f} veces/año",
              delta_color="off", delta_arrow="off")
    c4.metric("Exactitud del pronóstico", f"{d.exactitud_pronostico:.1%}", f"sesgo {d.sesgo_pronostico:+.0%}",
              delta_color="inverse")
    c5.metric("Exactitud del registro (ERI)", f"{d.eri:.0%}", "meta 97 %", delta_color="off", delta_arrow="off")
    c6.metric("Fill rate", f"{d.fill_rate_30d:.1%}", "últimos 30 días · simulado",
              delta_color="off", delta_arrow="off", help="Indicador de control: bajar inventario no debe generar quiebres")

    st.divider()
    izq, der = st.columns([1.1, 1])
    with izq:
        grafico(g.fig_vejez(d))
    with der:
        brecha = d.vejez_tobe - d.meta_vejez
        st.markdown("#### Lectura para el Directorio")
        st.markdown(
            f"- Hoy **{d.vejez_asis:.1%}** del inventario está vencido, dañado o sin rotar: "
            f"**S/ {d.capital_en_riesgo:,.0f}**.\n"
            f"- Con los 5 objetivos cumplidos, el índice baja a **{d.vejez_tobe:.1%}**.\n"
            f"- Aún quedan **{brecha:.1%}** sobre la meta de {d.meta_vejez:.0%}: el componente que no cierra "
            "es el **stock sin rotación**. Para llegar a la meta debe bajar a ≈ 3 % del inventario, no a 5 %.")
        decision("Endurecer la meta del Objetivo 3 o reformular la meta general a ≈ 7 %.")

    izq, der = st.columns(2)
    with izq:
        grafico(g.fig_pronostico())
    with der:
        grafico(g.fig_vencido_mensual())

    st.subheader("Cartera de objetivos")
    tabla = kpis.resumen_objetivos()
    st.dataframe(tabla, hide_index=True, width="stretch", column_config={
        "Decisión que habilita": st.column_config.TextColumn(width="large")})
    st.caption("«Por cuantificar»: el proyecto aún no estima ese beneficio o inversión.")

# ============================================================================
# VISTA 2 · GERENCIA DE OPERACIONES
# ============================================================================
elif vista == "Gerencia de Operaciones":
    st.title("Avance de los 5 objetivos")
    st.caption("Vista táctica · cada pestaña muestra el indicador del objetivo, su As-Is y su To-Be")
    datos = kpis.cargar()
    t1, t2, t3, t4, t5, t6 = st.tabs(["1 · Kanban", "2 · FEFO", "3 · ABC + antigüedad", "4 · Layout SLP",
                                      "5 · ERI", "OEE logístico"])

    with t1:
        r = datos["o1_res"]
        a, b, c, e = st.columns(4)
        a.metric("Días de inventario", f"{r['dias_tobe']:.1f}", f"{r['dias_tobe'] - r['dias_asis']:+.1f} días",
                 delta_color="inverse")
        b.metric("Ahorro en costo de mantener", f"S/ {r['ahorro_costo_mantener']:,.0f}/año")
        c.metric("Capital de trabajo liberado", f"S/ {r['capital_liberado']:,.0f}")
        e.metric("Compras evitadas", f"S/ {r['compras_evitadas']:,.0f}")
        grafico(g.fig_obj1_dias())
        st.markdown("**Parámetros de reposición**")
        p = datos["o1"][["producto", "politica", "lead_time_dias", "stock_seguridad", "rop", "lote_q"]]
        st.dataframe(p, hide_index=True, width="stretch", column_config={
            "producto": "Producto", "politica": "Política", "lead_time_dias": "LT (d)",
            "stock_seguridad": st.column_config.NumberColumn("SS", format="%.0f"),
            "rop": st.column_config.NumberColumn("ROP", format="%.0f"),
            "lote_q": st.column_config.NumberColumn("Lote Q", format="%.0f")})
        decision("Compras emite la orden solo cuando el stock llega al ROP, por el lote Q.")

    with t2:
        r = datos["o2_res"]
        a, b, c, e = st.columns(4)
        a.metric("Índice de vencido", f"{r['indice_tobe_prom']:.2%}",
                 f"{r['indice_tobe_prom'] - r['indice_asis_prom']:+.2%}", delta_color="inverse")
        b.metric("Inversión", f"S/ {r['inversion']:,.0f}")
        c.metric("Pérdida evitada", f"S/ {r['perdida_evitada']:,.0f}/año")
        e.metric("Beneficio / costo", f"{r['beneficio_costo']:.2f}")
        izq, der = st.columns(2)
        with izq:
            grafico(g.fig_vencido_mensual())
        with der:
            grafico(g.fig_obj2_curva())

    with t3:
        r = datos["o3_res"]
        a, b, c = st.columns(3)
        a.metric("% sin rotación (muestra)", f"{r['pct_sin_rotacion_asis']:.1%}", f"meta {r['pct_sin_rotacion_tobe']:.0%}",
                 delta_color="off", delta_arrow="off")
        b.metric("Valor sin rotación", f"S/ {r['valor_sin_rotacion_asis']:,.0f}")
        c.metric("Valor a recuperar", f"S/ {r['valor_sin_rotacion_asis'] - r['valor_sin_rotacion_tobe']:,.0f}")
        izq, der = st.columns(2)
        with izq:
            grafico(g.fig_obj3_antiguedad())
        with der:
            grafico(g.fig_obj3_matriz())
        decision("Malla raschel (A, 127 d) atención inmediata; tanque 1100 L y cordón 3x14 a venta por lote "
                 "o devolución al proveedor.")

    with t4:
        r = datos["o4_res"]
        o4 = datos["o4"]
        alto = o4[o4["riesgo_dano"] == "Alto"]
        a, b, c = st.columns(3)
        a.metric("Índice de mercadería dañada", f"{r['indice_tobe']:.2%}", f"{r['indice_tobe'] - r['indice_asis']:+.2%}",
                 delta_color="inverse")
        b.metric("Pérdida evitada", f"S/ {r['perdida_evitada']:,.0f}/año")
        c.metric("SKU en ubicación de riesgo alto", f"{len(alto)} de {len(o4)}",
                 f"S/ {alto['valor_stock'].sum():,.0f} en stock", delta_color="off", delta_arrow="off")
        izq, der = st.columns([1.3, 1])
        with izq:
            grafico(g.fig_obj4_pq())
        with der:
            st.markdown("**Reubicación de los SKU en riesgo alto**")
            st.dataframe(alto[["producto", "situacion", "tipo_carga", "zona"]], hide_index=True,
                         width="stretch", column_config={
                             "producto": "Producto", "situacion": "Situación actual",
                             "tipo_carga": "Tipo de carga", "zona": "Zona asignada"})
            decision("Retirar del piso los 8 SKU de riesgo alto y asignarles zona (Z7, Z8, Z9).")

    with t5:
        r = datos["o5_res"]
        a, b, c = st.columns(3)
        a.metric("ERI", f"{r['eri_final']:.1%}", f"{r['eri_final'] - r['eri_base']:+.1%} vs base")
        b.metric("Faltantes valorizados (base)", f"S/ {abs(r['faltantes_soles']):,.0f}")
        c.metric("Sobrantes valorizados (base)", f"S/ {r['sobrantes_soles']:,.0f}")
        grafico(g.fig_obj5_eri())
        izq, der = st.columns(2)
        with izq:
            grafico(g.fig_obj5_clase())
        with der:
            grafico(g.fig_obj5_causas())

    with t6:
        oee = kpis.oee_logistico(30)
        res = oee["resumen"]
        st.markdown("La Sirena no fabrica: el OEE se **adapta al almacén**, donde el recurso que se aprovecha "
                    "es la cuadrilla de picking (18 trabajadores).")
        a, b, c, e = st.columns(4)
        a.metric("OEE logístico", f"{res['oee']:.1%}", "clase mundial 85 %", delta_color="off", delta_arrow="off")
        b.metric("Disponibilidad", f"{res['disponibilidad']:.1%}", help="Horas productivas / horas disponibles")
        c.metric("Rendimiento", f"{res['rendimiento']:.1%}", help="Líneas por hora productiva / estándar 45")
        e.metric("Calidad", f"{res['calidad']:.1%}", help="Líneas sin error / líneas preparadas")
        grafico(g.fig_oee_diario(oee))
        nota_simulado()
        peor = min(["disponibilidad", "rendimiento", "calidad"], key=lambda k: res[k])
        accion = {"disponibilidad": "reducir tiempos muertos y reasignar tareas",
                  "rendimiento": "fijar estándares de trabajo y ubicaciones fijas (Obj. 4 y 5)",
                  "calidad": "reforzar la verificación del picking y el ERI (Obj. 5)"}[peor]
        decision(f"La mayor pérdida está en **{peor}** ({res[peor]:.1%}): {accion} antes que contratar personal.")

# ============================================================================
# VISTA 3 · JEFE DE ALMACÉN
# ============================================================================
else:
    st.title("¿Qué hago hoy en el almacén?")
    st.caption("Vista operativa · reposición Kanban, lotes por vencer y conteos de la semana")
    nota_simulado()

    st.subheader("Semáforo de reposición Kanban")
    sem = kpis.semaforo_kanban()
    cols = st.columns(len(sem))
    for col, (_, r) in zip(cols, sem.iterrows()):
        with col.container(border=True):
            st.markdown(f"**{ICONO[r['estado']]} {r['estado']}** · {r['sku']}")
            st.caption(r["producto"])
            st.metric("Stock", f"{r['stock_cierre']:,.0f}", f"ROP {r['rop']:,.0f} · SS {r['ss']:,.0f}",
                      delta_color="off", delta_arrow="off")
            st.markdown(f"Cobertura: **{r['cobertura_dias']:.0f} días**  \n➡️ {r['accion']}")

    sku = st.selectbox("Ver evolución del stock", sem["sku"], format_func=lambda s: sem.set_index("sku").loc[s, "producto"])
    grafico(g.fig_stock_sku(sku))

    st.divider()
    st.subheader("Lotes por vencer (FEFO)")
    fam = st.selectbox("Familia", ["Todas"] + sorted(kpis.cargar()["sim_lotes"]["familia"].unique()))
    lotes = kpis.lotes_fefo(fam)
    izq, der = st.columns([1, 1.4])
    with izq:
        grafico(g.fig_lotes_estado(lotes))
    with der:
        urgentes = lotes[lotes["estado"].isin(["VENCIDO", "ROJO"])].copy()
        urgentes["estado"] = urgentes["estado"].map(lambda e: f"{ICONO[e]} {e}")
        st.markdown(f"**Despachar primero o mover a cuarentena · {len(urgentes)} lotes**")
        st.dataframe(urgentes[["estado", "lote", "producto", "ubicacion", "dias_para_vencer", "unidades", "valor_soles"]],
                     hide_index=True, width="stretch", height=300, column_config={
                         "estado": "Estado", "lote": "Lote", "producto": "Producto", "ubicacion": "Ubicación",
                         "dias_para_vencer": st.column_config.NumberColumn("Días", format="%d"),
                         "unidades": "Und", "valor_soles": st.column_config.NumberColumn("Valor", format="S/ %,.0f")})

    st.divider()
    st.subheader("Programa de conteos cíclicos")
    semanas = sorted(kpis.cargar()["o5_conteos"]["semana"].unique())
    semana = st.select_slider("Semana del programa", semanas, value=semanas[-1])
    c = kpis.conteos_semana(semana)
    ej = c.dropna(subset=["coincide"])
    a, b, e = st.columns(3)
    a.metric("Conteos programados", len(c))
    b.metric("ERI de la semana", f"{ej['coincide'].mean():.1%}")
    e.metric("Con diferencia", int((ej["coincide"] == 0).sum()))
    st.dataframe(c[c["coincide"] == 0][["codigo", "ubicacion", "clase", "cant_sistema", "cant_final", "diferencia", "causa"]],
                 hide_index=True, width="stretch", column_config={
                     "codigo": "SKU", "ubicacion": "Ubicación", "clase": "Clase", "cant_sistema": "Sistema",
                     "cant_final": "Físico", "diferencia": "Diferencia", "causa": "Causa"})
