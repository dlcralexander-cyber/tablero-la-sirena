# Tablero de Operaciones · Corporación La Sirena S.A.C. (CD Lurín)

Área estratégica 6 · **Analítica de Operaciones y Dashboards** · Equipo EQ8 · GEESOP 2026-2

El mismo tablero en dos versiones que comparten datos y gráficos:

| Archivo | Librerías | Para qué |
|---|---|---|
| `app_streamlit.py` | Streamlit + Plotly | Versión principal (rápida de publicar) |
| `app_dash.py` | Dash + Plotly | Versión equivalente con callbacks |

## Cómo ejecutarlo

```bash
pip install -r requirements.txt

streamlit run app_streamlit.py     # abre http://localhost:8501
python app_dash.py                 # abre http://127.0.0.1:8050
```

Para publicarlo gratis: subir la carpeta a GitHub y desplegar `app_streamlit.py`
en Streamlit Community Cloud.

## Tres vistas, una por nivel de decisión

| Vista | Usuario | Pregunta que responde |
|---|---|---|
| Directorio | Alta Dirección | ¿Qué tan sano está el inventario y qué decisiones de inversión se necesitan? |
| Gerencia de Operaciones | Gerente de Operaciones | ¿Cómo avanza cada uno de los 5 objetivos (Kanban, FEFO, ABC, SLP, ERI)? + OEE logístico |
| Jefe de almacén | Jefe del CD Lurín | ¿Qué pido hoy, qué despacho primero y qué cuento esta semana? |

## Adaptación de los KPI del curso a un centro de distribución

La Sirena no fabrica, así que los KPI de planta se traducen a su operación:

| KPI del curso | Equivalente en el CD Lurín |
|---|---|
| OEE | **OEE logístico** = Disponibilidad (horas productivas / disponibles) × Rendimiento (líneas por hora / estándar) × Calidad (líneas sin error) |
| Productividad | Utilización de mano de obra y ERI |
| Tiempo de ciclo | Días de inventario (y cobertura por SKU) |
| Calidad | % vencido, % dañado, exactitud del pronóstico |

## Origen de los datos

- **Reales (Excel del proyecto final)**: línea base del diagnóstico, serie mensual 2025,
  parámetros Kanban, proyección FEFO, ABC/antigüedad, análisis P-Q y conteos del ERI.
- **Simulados (archivos `data/sim_*.csv`)**: stock diario de los SKU Kanban, lotes con fecha
  de vencimiento y productividad diaria del picking. La empresa aún no registra estos datos;
  el tablero los rotula como simulados en pantalla.

Si cambia el Excel, regenerar los datos con:

```bash
python preparar_datos.py "ruta/al/Esquema_Proyecto_Final_GEESOP_20262_6_T2.xlsx"
```

## Estructura

```
app_streamlit.py      vista Streamlit
app_dash.py           vista Dash
assets/estilo.css     estilos de la versión Dash
nucleo/kpis.py        cálculo de KPI (única fuente de cifras)
nucleo/graficos.py    figuras Plotly compartidas
preparar_datos.py     extracción del Excel + simulación
data/                 CSV generados
```
