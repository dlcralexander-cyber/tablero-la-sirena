"""
Carga de datos y cálculo de KPIs. Es la ÚNICA fuente de cifras del tablero:
Streamlit y Dash leen de aquí, así ambas apps muestran exactamente lo mismo.
"""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
FECHA_CORTE = pd.Timestamp("2026-10-27")


def _serie(nombre: str) -> pd.Series:
    return pd.read_csv(DATA / nombre, index_col=0)["valor"].astype(float)


@lru_cache(maxsize=None)
def cargar() -> dict:
    """Lee todos los CSV una sola vez."""
    d = {
        "base": _serie("linea_base.csv"),
        "mensual": pd.read_csv(DATA / "mensual_2025.csv", parse_dates=["fecha"]),
        "o1": pd.read_csv(DATA / "obj1_kanban.csv"),
        "o1_res": _serie("obj1_resultados.csv"),
        "o2_proy": pd.read_csv(DATA / "obj2_proyeccion_2026.csv", parse_dates=["fecha"]),
        "o2_curva": pd.read_csv(DATA / "obj2_curva_fefo.csv"),
        "o2_res": _serie("obj2_resultados.csv"),
        "o3": pd.read_csv(DATA / "obj3_antiguedad.csv"),
        "o3_res": _serie("obj3_resultados.csv"),
        "o4": pd.read_csv(DATA / "obj4_pq.csv"),
        "o4_res": _serie("obj4_resultados.csv"),
        "o5_conteos": pd.read_csv(DATA / "obj5_conteos.csv"),
        "o5_base": pd.read_csv(DATA / "obj5_linea_base.csv"),
        "o5_causas": pd.read_csv(DATA / "obj5_causas_base.csv"),
        "o5_res": _serie("obj5_resultados.csv"),
        "o5_maestro": pd.read_csv(DATA / "obj5_maestro_abc.csv"),
        "sim_stock": pd.read_csv(DATA / "sim_stock_diario.csv", parse_dates=["fecha"]),
        "sim_lotes": pd.read_csv(DATA / "sim_lotes_fefo.csv", parse_dates=["fecha_vencimiento"]),
        "sim_prod": pd.read_csv(DATA / "sim_productividad.csv", parse_dates=["fecha"]),
    }
    return d


# ----------------------------------------------------------------------------
# Vista Directorio
# ----------------------------------------------------------------------------
@dataclass
class Directorio:
    vejez_asis: float
    vejez_tobe: float
    meta_vejez: float
    capital_en_riesgo: float
    dias_inventario: float
    rotacion: float
    exactitud_pronostico: float
    sesgo_pronostico: float
    eri: float
    fill_rate_30d: float
    componentes: pd.DataFrame       # vencido / dañado / sin rotación, As-Is vs To-Be


def directorio() -> Directorio:
    d = cargar()
    b = d["base"]
    total = b["inventario_total"]

    # To-Be proyectado = resultado de cada objetivo según el Excel
    venc_tobe = d["o2_proy"]["vencido"].iloc[-1]                 # dic-26, Obj. 2
    dan_tobe = d["o4_res"]["valor_danado_tobe"]                   # Obj. 4
    sinrot_tobe = d["o3_res"]["pct_sin_rotacion_tobe"] * total     # meta 5 % (Obj. 3)
    comp = pd.DataFrame({
        "componente": ["Vencido", "Dañado", "Sin rotación (> 3 meses)"] * 2,
        "escenario": ["As-Is 2025"] * 3 + ["Proyección con los 5 objetivos"] * 3,
        "soles": [b["vencido"], b["danado"], b["sin_rotacion"], venc_tobe, dan_tobe, sinrot_tobe],
    })
    comp["pct_inventario"] = comp["soles"] / total

    m = d["mensual"]
    sesgo = (m["demanda_pronosticada"].sum() - m["demanda_real"].sum()) / m["demanda_real"].sum()

    return Directorio(
        vejez_asis=(b["vencido"] + b["danado"] + b["sin_rotacion"]) / total,
        vejez_tobe=(venc_tobe + dan_tobe + sinrot_tobe) / total,
        meta_vejez=b["meta_vejez"],
        capital_en_riesgo=b["vencido"] + b["danado"] + b["sin_rotacion"],
        dias_inventario=d["o1_res"]["dias_asis"],
        rotacion=b["costo_ventas_anual"] / b["inventario_promedio"],
        exactitud_pronostico=b["exactitud_pronostico"],
        sesgo_pronostico=sesgo,
        eri=d["o5_res"]["eri_base"],
        fill_rate_30d=fill_rate(30),
        componentes=comp,
    )


def resumen_objetivos() -> pd.DataFrame:
    """Tabla para el directorio: un renglón por objetivo, con su decisión."""
    d = cargar()
    r1, r2, r3, r4, r5 = d["o1_res"], d["o2_res"], d["o3_res"], d["o4_res"], d["o5_res"]
    t = pd.DataFrame([
        ["1. Kanban + ROP + EOQ", "Días de inventario (SKU estrella)",
         f"{r1['dias_asis']:.1f} d", f"{r1['dias_tobe']:.1f} d", r1["ahorro_costo_mantener"], None,
         "Comprar según consumo real, no según proyección"],
        ["2. FEFO con trazabilidad QR", "Índice de inventario vencido",
         f"{r2['indice_asis_prom']:.2%}", f"{r2['indice_tobe_prom']:.2%}", r2["perdida_evitada"], r2["inversion"],
         "Aprobar la compra de lectores y etiquetas QR"],
        ["3. ABC + antigüedad", "% inventario sin rotación (muestra)",
         f"{r3['pct_sin_rotacion_asis']:.1%}", f"{r3['pct_sin_rotacion_tobe']:.1%}", None, None,
         "Autorizar liquidación o devolución del stock > 90 días"],
        ["4. Distribución SLP", "Índice de mercadería dañada",
         f"{r4['indice_asis']:.2%}", f"{r4['indice_tobe']:.2%}", r4["perdida_evitada"], None,
         "Liberar presupuesto para rack cantilever y demarcación"],
        ["5. Codificación + conteos ABC", "Exactitud del registro (ERI)",
         f"{r5['eri_base']:.0%}", f"{r5['eri_final']:.0%}", None, None,
         "Asignar 2 contadores al programa de conteos cíclicos"],
    ], columns=["Objetivo", "Indicador", "As-Is", "To-Be", "Beneficio anual (S/)",
                "Inversión (S/)", "Decisión que habilita"])
    for col in ["Beneficio anual (S/)", "Inversión (S/)"]:
        t[col] = t[col].map(lambda v: f"S/ {v:,.0f}" if pd.notna(v) else "por cuantificar")
    return t


# ----------------------------------------------------------------------------
# Vista Gerencia de Operaciones
# ----------------------------------------------------------------------------
def eri_semanal() -> pd.DataFrame:
    c = cargar()["o5_conteos"]
    # solo conteos ejecutados (los programados sin ejecutar quedan vacíos)
    g = c.groupby("semana").agg(contados=("coincide", "count"), coinciden=("coincide", "sum")).reset_index()
    g["eri"] = g["coinciden"] / g["contados"]
    return g


def eri_por_clase() -> pd.DataFrame:
    d = cargar()
    base = d["o5_base"].assign(eri=lambda x: x["coinciden"] / x["contados"], periodo="Línea base")
    fin = d["o5_conteos"].query("semana >= 23").groupby("clase")["coincide"].agg(["count", "sum"]).reset_index()
    fin = fin.rename(columns={"count": "contados", "sum": "coinciden"})
    fin["eri"] = fin["coinciden"] / fin["contados"]
    fin["periodo"] = "Semanas 23–26"
    return pd.concat([base, fin], ignore_index=True)[["clase", "periodo", "contados", "coinciden", "eri"]]


def antiguedad_buckets() -> pd.DataFrame:
    o3 = cargar()["o3"]
    tramos = pd.cut(o3["dias_sin_mov"], [-1, 30, 60, 90, 10_000],
                    labels=["0–30 días", "31–60 días", "61–90 días", "> 90 días"])
    return o3.assign(tramo=tramos)


def oee_logistico(dias: int = 30) -> dict:
    """
    OEE adaptado al almacén (no hay máquinas: el 'equipo' es la cuadrilla):
      Disponibilidad = horas productivas / horas disponibles
      Rendimiento    = líneas preparadas por hora productiva / estándar
      Calidad        = líneas sin error / líneas preparadas
    Datos SIMULADOS hasta que la empresa registre la productividad diaria.
    """
    p = cargar()["sim_prod"]
    p = p[p["fecha"] > FECHA_CORTE - pd.Timedelta(days=dias)].copy()
    p["disponibilidad"] = p["horas_productivas"] / p["horas_disponibles"]
    p["rendimiento"] = p["lineas_preparadas"] / p["horas_productivas"] / p["estandar_lineas_hora"]
    p["calidad"] = 1 - p["lineas_con_error"] / p["lineas_preparadas"]
    p["oee"] = p["disponibilidad"] * p["rendimiento"] * p["calidad"]
    tot = {
        "disponibilidad": p["horas_productivas"].sum() / p["horas_disponibles"].sum(),
        "rendimiento": p["lineas_preparadas"].sum() / p["horas_productivas"].sum() / p["estandar_lineas_hora"].iloc[0],
        "calidad": 1 - p["lineas_con_error"].sum() / p["lineas_preparadas"].sum(),
    }
    tot["oee"] = tot["disponibilidad"] * tot["rendimiento"] * tot["calidad"]
    return {"resumen": tot, "diario": p}


# ----------------------------------------------------------------------------
# Vista Jefe de almacén (operativa)
# ----------------------------------------------------------------------------
def fill_rate(dias: int = 30) -> float:
    s = cargar()["sim_stock"]
    s = s[s["fecha"] > FECHA_CORTE - pd.Timedelta(days=dias)]
    return s["atendida"].sum() / s["demanda"].sum()


def semaforo_kanban() -> pd.DataFrame:
    d = cargar()
    s = d["sim_stock"]
    hoy = s[s["fecha"] == s["fecha"].max()].copy()
    o1 = d["o1"].set_index("sku")
    hoy["demanda_diaria"] = hoy["sku"].map(o1["demanda_diaria"])
    plural = {"bolsa": "bolsas", "unidad": "und", "rollo": "rollos"}
    hoy["unidad"] = hoy["sku"].map(o1["unidad"]).map(lambda u: plural.get(u, u))
    hoy["lote_q"] = hoy["sku"].map(o1["lote_q"])
    hoy["cobertura_dias"] = hoy["stock_cierre"] / hoy["demanda_diaria"]

    def estado(r):
        if r["stock_cierre"] <= r["ss"]:
            return "ROJO"
        if r["stock_cierre"] <= r["rop"]:
            return "AMARILLO"
        return "VERDE"

    hoy["estado"] = hoy.apply(estado, axis=1)
    hoy["accion"] = hoy.apply(lambda r: {
        "VERDE": "No pedir",
        "AMARILLO": (f"Pedido de {r['lote_q']:.0f} {r['unidad']} en tránsito" if r["en_transito"] > 0
                     else f"Emitir OC por {r['lote_q']:.0f} {r['unidad']}"),
        "ROJO": "Urgente: confirmar llegada con Compras",
    }[r["estado"]], axis=1)
    return hoy[["sku", "producto", "stock_cierre", "ss", "rop", "en_transito",
                "cobertura_dias", "estado", "accion"]]


def lotes_fefo(familia: str | None = None) -> pd.DataFrame:
    l = cargar()["sim_lotes"].copy()
    if familia and familia != "Todas":
        l = l[l["familia"] == familia]
    l["estado"] = pd.cut(l["dias_para_vencer"], [-10_000, 0, 30, 90, 10_000],
                         labels=["VENCIDO", "ROJO", "ÁMBAR", "VERDE"], right=True).astype(str)
    return l.sort_values("dias_para_vencer")


def conteos_semana(semana: int) -> pd.DataFrame:
    c = cargar()["o5_conteos"]
    return c[c["semana"] == semana]
