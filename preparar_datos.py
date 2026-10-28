"""
Prepara los datos del tablero de Corporación La Sirena S.A.C. (CD Lurín).

1. EXTRAE del Excel del proyecto final las cifras reales del diagnóstico
   y de los 5 objetivos (fuente única de datos -> carpeta data/).
2. SIMULA los datos operativos diarios que la empresa todavía no registra
   (stock diario de SKU Kanban, lotes con fecha de vencimiento, productividad
   del picking). Todo archivo simulado lleva el prefijo "sim_".

Uso:
    python preparar_datos.py "ruta/al/Esquema_Proyecto_Final.xlsx"

Solo hace falta correrlo si cambia el Excel: la carpeta data/ ya viene generada.
"""
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

DATA = Path(__file__).parent / "data"
HOY = date(2026, 10, 27)          # fecha de corte del tablero
SEMILLA = 2026                    # reproducibilidad de la simulación


# ----------------------------------------------------------------------------
# 1. EXTRACCIÓN DEL EXCEL
# ----------------------------------------------------------------------------
def filas(ws, rango):
    return [[c.value for c in fila] for fila in ws[rango]]


def soles(v):
    """Convierte textos como 'S/ 23.789' (miles con punto) a número."""
    if isinstance(v, (int, float)):
        return v
    return float(str(v).replace("S/", "").replace(".", "").replace(",", ".").strip())


def extraer(xlsx: Path):
    wb = openpyxl.load_workbook(xlsx, data_only=True)

    # --- Línea base única (hoja CUANTITATIVO) --------------------------------
    cu = wb["CUANTITATIVO"]
    base = {
        "inventario_total": cu["F32"].value,
        "vencido": cu["F33"].value,
        "danado": cu["F34"].value,
        "sin_rotacion": cu["F35"].value,
        "costo_ventas_anual": cu["F36"].value,
        "inventario_promedio": cu["F37"].value,
        "exactitud_pronostico": cu["H71"].value,
        "cumplimiento_senalizacion": cu["H88"].value,
        "activos_criticos": cu["F111"].value,
        "trabajadores_almacen": cu["F118"].value,
        "horas_disponibles_mes": cu["F120"].value,
        "horas_productivas_mes": cu["F121"].value,
        "meta_vejez": wb["Planteamiento"]["E12"].value,
    }
    pd.Series(base, name="valor").rename_axis("concepto").to_csv(DATA / "linea_base.csv")

    # --- Serie mensual 2025: inventario, vencido, pronóstico vs real ----------
    da = wb["Datos"]
    meses = ["ene", "feb", "mar", "abr", "may", "jun",
             "jul", "ago", "set", "oct", "nov", "dic"]
    inv = filas(da, "C5:E16")
    dem = filas(da, "C20:E31")
    pd.DataFrame({
        "mes": [f"{m}-25" for m in meses],
        "fecha": pd.date_range("2025-01-01", periods=12, freq="MS"),
        "inventario_total": [r[0] for r in inv],
        "vencido": [r[2] for r in inv],
        "demanda_pronosticada": [r[0] for r in dem],
        "demanda_real": [r[2] for r in dem],
    }).to_csv(DATA / "mensual_2025.csv", index=False)

    # --- Objetivo 1: parámetros Kanban de los SKU estrella --------------------
    o1 = wb["Desarrollo Obj1"]
    info = filas(o1, "C31:H34")          # nombre, %venta, precio, unidad, und/paq, LT
    par = filas(o1, "C65:K68")           # nombre, d, sigma, SS, ROP, costo, EOQ, Q, política
    comp = filas(o1, "C102:I105")        # nombre, inv u asis, tobe, S/ asis, S/ tobe, días asis, días tobe
    o1_df = pd.DataFrame({
        "sku": ["CEM-425", "TAN-25K", "LLV-2CIM", "COR-NMT"],
        "producto": [r[0] for r in info],
        "participacion_ventas": [r[1] for r in info],
        "precio_venta": [r[2] for r in info],
        "unidad": [r[3] for r in info],
        "und_contenedor": [r[4] for r in info],
        "lead_time_dias": [r[5] for r in info],
        "demanda_diaria": [r[1] for r in par],
        "sigma_diaria": [r[2] for r in par],
        "stock_seguridad": [r[3] for r in par],
        "rop": [r[4] for r in par],
        "costo_unitario": [r[5] for r in par],
        "eoq": [r[6] for r in par],
        "lote_q": [r[7] if isinstance(r[7], (int, float)) else None for r in par],
        "politica": [r[8] for r in par],
        "inv_prom_asis_soles": [r[3] for r in comp],
        "inv_prom_tobe_soles": [r[4] if isinstance(r[4], (int, float)) else 0 for r in comp],
        "dias_asis": [r[5] for r in comp],
        "dias_tobe": [r[6] if isinstance(r[6], (int, float)) else 0 for r in comp],
    })
    o1_df.to_csv(DATA / "obj1_kanban.csv", index=False)
    pd.Series({
        "dias_asis": o1["D132"].value, "dias_tobe": o1["E132"].value,
        "ahorro_costo_mantener": o1["D140"].value,
        "capital_liberado": o1["D141"].value,
        "compras_evitadas": o1["D142"].value,
    }, name="valor").rename_axis("concepto").to_csv(DATA / "obj1_resultados.csv")

    # --- Objetivo 2: FEFO (proyección mensual y curva de cumplimiento) --------
    h2 = wb["2"]
    proy = filas(h2, "C41:L52")
    pd.DataFrame({
        "mes": [f"{m}-26" for m in meses],
        "fecha": pd.date_range("2026-01-01", periods=12, freq="MS"),
        "cumplimiento_fefo": [r[0] for r in proy],
        "vencido": [r[5] for r in proy],
        "inventario_total": [r[7] for r in proy],
        "indice_vencido": [r[9] for r in proy],
    }).to_csv(DATA / "obj2_proyeccion_2026.csv", index=False)
    sem = filas(h2, "B28:AX34")
    curva = pd.DataFrame({r[0]: r[1:] for r in sem})
    curva.insert(0, "semana", range(1, len(curva) + 1))
    curva.to_csv(DATA / "obj2_curva_fefo.csv", index=False)
    m2 = wb["MOTIVO2"]
    pd.Series({
        "inversion": m2["I95"].value,
        "perdida_evitada": wb["OBJETIVO 2"]["O166"].value,
        "beneficio_costo": wb["OBJETIVO 2"]["O167"].value,
        "indice_asis_prom": wb["OBJETIVO 2"]["R147"].value,
        "indice_tobe_prom": wb["OBJETIVO 2"]["U147"].value,
        "estandar": wb["OBJETIVO 2"]["W147"].value,
    }, name="valor").rename_axis("concepto").to_csv(DATA / "obj2_resultados.csv")

    # --- Objetivo 3: ABC + antigüedad -----------------------------------------
    m3 = wb["MOTIVO 3"]
    ag = filas(m3, "D19:J23")
    abc = {r[0]: r[2] for r in filas(m3, "D72:F76")}
    pd.DataFrame({
        "codigo": [r[0] for r in ag], "producto": [r[1] for r in ag],
        "stock": [r[2] for r in ag], "costo_unitario": [r[3] for r in ag],
        "ultima_salida": [r[4] for r in ag], "dias_sin_mov": [r[5] for r in ag],
        "valor": [r[6] for r in ag], "clase_abc": [abc[r[0]].strip() for r in ag],
    }).to_csv(DATA / "obj3_antiguedad.csv", index=False)

    # --- Objetivo 4: análisis P-Q y zonas (30 SKU) ----------------------------
    pq = filas(wb["OBJ 4"], "A123:O152")
    pd.DataFrame(pq, columns=[
        "n", "producto", "codigo", "familia", "consumo_anual", "pct", "pct_acum",
        "clase_pq", "stock", "costo_unitario", "valor_stock", "situacion",
        "riesgo_dano", "tipo_carga", "zona"]).to_csv(DATA / "obj4_pq.csv", index=False)

    o4 = wb["OBJ 4"]
    pd.Series({
        "indice_asis": o4["C517"].value, "indice_tobe": o4["E517"].value,
        "valor_danado_tobe": soles(o4["E518"].value), "perdida_evitada": soles(o4["E528"].value),
    }, name="valor").rename_axis("concepto").to_csv(DATA / "obj4_resultados.csv")
    pd.Series({
        "pct_sin_rotacion_asis": m3["E92"].value, "pct_sin_rotacion_tobe": m3["F92"].value,
        "valor_sin_rotacion_asis": m3["E91"].value, "valor_sin_rotacion_tobe": m3["F91"].value,
    }, name="valor").rename_axis("concepto").to_csv(DATA / "obj3_resultados.csv")

    # --- Objetivo 5: maestro ABC, conteos cíclicos y checklist ---------------
    o5 = wb["Objetivo 5 "]
    pd.Series({
        "eri_base": o5["D2574"].value, "eri_final": o5["D2576"].value, "meta": o5["E2574"].value,
        "faltantes_soles": o5["F63"].value, "sobrantes_soles": o5["J63"].value,
    }, name="valor").rename_axis("concepto").to_csv(DATA / "obj5_resultados.csv")
    ma = filas(o5, "A450:M1449")
    pd.DataFrame([[r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[10], r[12]] for r in ma],
                 columns=["codigo", "descripcion", "lineas_12m", "unid_12m", "costo",
                          "valor_12m", "criticidad", "puntaje", "clase"]
                 ).to_csv(DATA / "obj5_maestro_abc.csv", index=False)
    co = filas(o5, "A1509:M2552")
    pd.DataFrame([[r[2], r[3], r[4], r[5], r[6], r[9], r[10], r[11], r[12]] for r in co],
                 columns=["semana", "codigo", "ubicacion", "clase", "cant_sistema",
                          "cant_final", "diferencia", "coincide", "causa"]
                 ).to_csv(DATA / "obj5_conteos.csv", index=False)
    lb = filas(o5, "I58:L60")
    causas = filas(o5, "P58:Q64")
    pd.DataFrame({"clase": [r[0] for r in lb], "contados": [r[1] for r in lb],
                  "coinciden": [r[2] for r in lb]}).to_csv(DATA / "obj5_linea_base.csv", index=False)
    pd.DataFrame(causas, columns=["causa", "n"]).to_csv(DATA / "obj5_causas_base.csv", index=False)
    pd.DataFrame(filas(o5, "A30:F44"), columns=[
        "n", "dimension", "criterio", "observacion", "estado", "puntaje"]
    ).to_csv(DATA / "obj5_checklist.csv", index=False)


# ----------------------------------------------------------------------------
# 2. SIMULACIÓN DE DATOS OPERATIVOS (no existen todavía en la empresa)
# ----------------------------------------------------------------------------
def simular():
    rng = np.random.default_rng(SEMILLA)
    sku = pd.read_csv(DATA / "obj1_kanban.csv")
    dias = pd.date_range(HOY - timedelta(days=119), HOY, freq="D")

    # 2.1 Stock diario de los SKU estrella bajo la política Kanban (ROP, Q)
    registros = []
    for _, s in sku[sku.politica == "Kanban"].iterrows():   # el tanque va contra pedido: sin stock
        d, sd, lt = s.demanda_diaria, s.sigma_diaria, int(s.lead_time_dias)
        ss, rop, q = s.stock_seguridad, s.rop, s.lote_q
        stock = ss + q / 2 + d * lt / 2
        pedidos = []                      # [(día_llegada, cantidad)]
        for t, dia in enumerate(dias):
            llega = sum(c for (tl, c) in pedidos if tl == t)
            pedidos = [(tl, c) for (tl, c) in pedidos if tl != t]
            stock += llega
            dem = max(0.0, rng.normal(d, sd))
            atendida = min(stock, dem)
            stock -= atendida
            en_transito = sum(c for _, c in pedidos)
            orden = 0
            if stock + en_transito <= rop:
                orden = q
                pedidos.append((t + lt, q))
            registros.append({
                "fecha": dia.date(), "sku": s.sku, "producto": s.producto,
                "demanda": round(dem, 2), "atendida": round(atendida, 2),
                "llegada": llega, "orden_emitida": orden,
                "stock_cierre": round(stock, 2), "en_transito": en_transito + orden,
                "ss": ss, "rop": rop,
            })
    pd.DataFrame(registros).to_csv(DATA / "sim_stock_diario.csv", index=False)

    # 2.2 Lotes con fecha de vencimiento (familias del Obj. 2)
    familias = {
        "Cemento": (["Cemento Andino Tipo I 42.5 kg", "Cemento Sol Tipo I 42.5 kg"], 90, 28.8),
        "Pegamentos y fraguas": (["Pegamento cerámico 25 kg", "Fragua blanca 1 kg", "Pegamento PVC 1/4 gal"], 365, 22.0),
        "Pinturas": (["Pintura látex 4 L", "Esmalte sintético galón", "Pintura spray"], 730, 45.0),
        "Selladores": (["Silicona acética 280 ml", "Sellador acrílico 300 ml"], 540, 14.0),
        "Aditivos": (["Impermeabilizante 4 L", "Acelerante de fragua 1 L"], 365, 38.0),
    }
    lotes = []
    n = 1
    for fam, (prods, vida, costo) in familias.items():
        for p in prods:
            for _ in range(rng.integers(3, 6)):
                restante = int(rng.integers(-20, vida))
                und = int(rng.integers(20, 400))
                lotes.append({
                    "lote": f"{fam[:3].upper()}-{n:04d}", "familia": fam, "producto": p,
                    "fecha_vencimiento": HOY + timedelta(days=restante),
                    "dias_para_vencer": restante, "unidades": und,
                    "valor_soles": round(und * costo * rng.uniform(0.8, 1.2), 2),
                    "ubicacion": f"{rng.choice(list('ABC'))}-{rng.integers(1, 4):02d}-"
                                 f"{rng.integers(1, 13):02d}-{rng.integers(1, 4)}",
                })
                n += 1
    pd.DataFrame(lotes).to_csv(DATA / "sim_lotes_fefo.csv", index=False)

    # 2.3 Productividad diaria del picking (base del OEE logístico adaptado)
    base = pd.read_csv(DATA / "linea_base.csv", index_col=0)["valor"]
    disp_base = base["horas_productivas_mes"] / base["horas_disponibles_mes"]
    prod = []
    for dia in dias:
        if dia.weekday() == 6:      # domingo no se opera
            continue
        horas_disp = base["trabajadores_almacen"] * 8
        horas_prod = horas_disp * np.clip(rng.normal(disp_base, 0.03), 0.7, 0.99)
        estandar = 45                                 # líneas/hora-hombre (supuesto)
        lineas = horas_prod * estandar * np.clip(rng.normal(0.82, 0.06), 0.6, 1.0)
        errores = rng.binomial(int(lineas), 0.035)
        prod.append({
            "fecha": dia.date(), "horas_disponibles": horas_disp,
            "horas_productivas": round(horas_prod, 1),
            "lineas_preparadas": int(lineas), "estandar_lineas_hora": estandar,
            "lineas_con_error": int(errores),
        })
    pd.DataFrame(prod).to_csv(DATA / "sim_productividad.csv", index=False)


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    if len(sys.argv) > 1:
        extraer(Path(sys.argv[1]))
        print("Datos extraídos del Excel.")
    simular()
    print("Datos simulados generados en", DATA)
