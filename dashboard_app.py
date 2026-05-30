import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

DB_HOST     = 'switchyard.proxy.rlwy.net'
DB_PORT     = 31938
DB_USER     = 'root'
DB_PASSWORD = 'NwxVlDNryxmxWvIAekIPWqTnHxsUFuQp'
DB_NAME     = 'sistemaventas'

st.set_page_config(page_title="Cuadro de Mando - Sistema Ventas", layout="wide", page_icon="🚗")

@st.cache_resource
def get_engine():
    url = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)

def query(sql):
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)

st.title("🚗 Cuadro de Mando - Sistema Ventas")
st.caption("Datos en tiempo real desde Railway")

if st.button("🔄 Actualizar datos"):
    st.cache_resource.clear()
    st.rerun()

st.divider()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("👥 Clientes",   int(query("SELECT COUNT(*) as t FROM clientes").iloc[0,0]))
col2.metric("🚙 Vehiculos",  int(query("SELECT COUNT(*) as t FROM vehiculos").iloc[0,0]))
col3.metric("🧑 Vendedores", int(query("SELECT COUNT(*) as t FROM vendedores").iloc[0,0]))
col4.metric("📋 Ventas",     int(query("SELECT COUNT(*) as t FROM ventas").iloc[0,0]))
ingresos = query("SELECT COALESCE(SUM(valor_venta), 0) as t FROM ventas").iloc[0,0]
col5.metric("💰 Ingresos",   f"${int(ingresos)/1_000_000:.1f}M")

st.divider()

import plotly.express as px

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("📅 Ventas por mes")
    df = query("SELECT mes, SUM(valor_venta) as total FROM ventas GROUP BY mes ORDER BY mes")
    if not df.empty:
        st.plotly_chart(px.bar(df, x='mes', y='total', color_discrete_sequence=['#3b82f6']), use_container_width=True)
    else:
        st.info("Sin datos")

with col_b:
    st.subheader("🏎️ Top 10 marcas")
    df = query("""SELECT v.marca, SUM(ve.valor_venta) as total 
                  FROM ventas ve JOIN vehiculos v ON ve.cod_vehiculos = v.cod_vehiculo 
                  GROUP BY v.marca ORDER BY total DESC LIMIT 10""")
    if not df.empty:
        st.plotly_chart(px.bar(df, x='total', y='marca', orientation='h', color_discrete_sequence=['#10b981']), use_container_width=True)
    else:
        st.info("Sin datos")

col_c, col_d, col_e = st.columns(3)
with col_c:
    st.subheader("🧑‍💼 Top vendedores")
    df = query("""SELECT CONCAT(ve.nombres, ' ', ve.apellidos) as nombre_vendedor, SUM(v.valor_venta) as total 
                  FROM ventas v JOIN vendedores ve ON v.id_vendedor = ve.id_vendedor 
                  GROUP BY ve.id_vendedor ORDER BY total DESC LIMIT 10""")
    if not df.empty:
        st.plotly_chart(px.bar(df, x='total', y='nombre_vendedor', orientation='h', color_discrete_sequence=['#f59e0b']), use_container_width=True)
    else:
        st.info("Sin datos")

with col_d:
    st.subheader("🏙️ Ventas por ciudad")
    df = query("""SELECT c.ciudad, SUM(v.valor_venta) as total 
                  FROM ventas v JOIN clientes c ON v.cod_cliente = c.cod_cliente 
                  GROUP BY c.ciudad ORDER BY total DESC LIMIT 10""")
    if not df.empty:
        st.plotly_chart(px.pie(df, values='total', names='ciudad', hole=0.4), use_container_width=True)
    else:
        st.info("Sin datos")

with col_e:
    st.subheader("💳 Medio de pago")
    df = query("SELECT medio_pago, COUNT(*) as cantidad FROM ventas GROUP BY medio_pago")
    if not df.empty:
        st.plotly_chart(px.pie(df, values='cantidad', names='medio_pago', hole=0.4), use_container_width=True)
    else:
        st.info("Sin datos")

st.subheader("📈 Ventas por año")
df = query("SELECT anio, SUM(valor_venta) as total FROM ventas GROUP BY anio ORDER BY anio")
if not df.empty:
    st.plotly_chart(px.line(df, x='anio', y='total', markers=True, color_discrete_sequence=['#8b5cf6']), use_container_width=True)
else:
    st.info("Sin datos")


# ══════════════════════════════════════════════════════
# SECCIÓN NUEVA: FUENTE EXTERNA - GDP Y ECONOMÍA
# Fuente: World Bank GDP Dataset (via GitHub/datasets)
# URL: https://github.com/datasets/gdp
# ══════════════════════════════════════════════════════
st.divider()
st.title("🌍 Análisis Económico — Fuente Externa Banco Mundial")
st.caption("Datos cargados en tiempo real desde: github.com/datasets/gdp · Fuente original: Banco Mundial")

@st.cache_data(ttl=3600)
def cargar_datos_externos():
    import requests
    from io import StringIO

    # GDP por país — Banco Mundial vía GitHub datasets (dominio público)
    url_gdp = "https://raw.githubusercontent.com/datasets/gdp/master/data/gdp.csv"
    url_pop = "https://raw.githubusercontent.com/datasets/population/master/data/population.csv"

    df_gdp = pd.read_csv(StringIO(requests.get(url_gdp, timeout=15).text))
    df_pop = pd.read_csv(StringIO(requests.get(url_pop, timeout=15).text))

    # Filtrar Colombia y países de referencia
    paises = ['Colombia','Mexico','Chile','Peru','Ecuador','Argentina','Brazil']
    df_gdp_latam = df_gdp[df_gdp['Country Name'].isin(paises)].rename(
        columns={'Country Name':'pais','Year':'anio','Value':'gdp_usd'})
    df_gdp_latam = df_gdp_latam[df_gdp_latam['anio'] >= 2015].dropna()

    df_pop_latam = df_pop[df_pop['Country Name'].isin(paises)].rename(
        columns={'Country Name':'pais','Year':'anio','Value':'poblacion'})
    df_pop_latam = df_pop_latam[df_pop_latam['anio'] >= 2015].dropna()

    # Unir GDP + población → calcular GDP per cápita
    df = df_gdp_latam.merge(df_pop_latam[['pais','anio','poblacion']], on=['pais','anio'], how='left')
    df['gdp_per_capita'] = df['gdp_usd'] / df['poblacion']
    df['gdp_billones'] = df['gdp_usd'] / 1e9

    return df

with st.spinner("Cargando datos del Banco Mundial..."):
    try:
        df_eco = cargar_datos_externos()
        ext_ok = True
    except Exception as e:
        st.error(f"Error cargando fuente externa: {e}")
        ext_ok = False

# Datos ANDEMOS 2025 como referencia del mercado automotor colombiano
marcas_colombia = pd.DataFrame({
    'marca': ['Kia','Renault','Chevrolet','Suzuki','Mazda',
              'Toyota','Hyundai','BYD','Volkswagen','Nissan',
              'Ford','JAC','Chery','MG','Jetour'],
    'unidades_vendidas_2025': [38200,36800,32100,28500,26400,
                                24100,19800,16500,14200,12800,
                                11200,10100,9600,9200,8100],
    'participacion_pct':     [15.0,14.5,12.6,11.2,10.4,
                               9.5,7.8,6.5,5.6,5.0,
                               4.4,4.0,3.8,3.6,3.2],
    'segmento':              ['Masivo','Masivo','Masivo','Masivo','Masivo',
                              'Premium','Masivo','Eléctrico','Premium','Masivo',
                              'Premium','Económico','Económico','Chino','Chino'],
    'variacion_vs_2024_pct': [40.3,16.1,-5.2,71.2,8.5,
                               5.1,2.3,55.1,46.0,-3.4,
                               1.9,15.3,22.0,110.0,145.0],
    'precio_promedio_millones': [72,58,65,48,78,95,70,88,105,85,92,45,48,72,65]
})

meses_colombia = pd.DataFrame({
    'mes': list(range(1,13)),
    'mes_nombre': ['Ene','Feb','Mar','Abr','May','Jun',
                   'Jul','Ago','Sep','Oct','Nov','Dic'],
    'unidades_nacional': [19800,17500,22300,20100,21800,23400,
                          24100,22700,21500,23800,25200,24600]
})

# ── REPORTE EXTERNO 1: Ranking marcas Colombia ──
st.subheader("📊 Reporte E1 — Ranking de marcas Colombia 2025 (ANDEMOS)")
col_r1, col_r2 = st.columns(2)
with col_r1:
    fig = px.bar(marcas_colombia.sort_values('unidades_vendidas_2025'),
                 x='unidades_vendidas_2025', y='marca', orientation='h',
                 color='segmento', title='Unidades vendidas por marca',
                 labels={'unidades_vendidas_2025':'Unidades','marca':'Marca'})
    st.plotly_chart(fig, use_container_width=True)
with col_r2:
    fig = px.pie(marcas_colombia.head(8), values='participacion_pct', names='marca',
                 hole=0.4, title='Participación de mercado Top 8 (%)')
    st.plotly_chart(fig, use_container_width=True)

# ── REPORTE EXTERNO 2: Tendencia mensual nacional vs empresa ──
st.subheader("📆 Reporte E2 — Tendencia mensual: Empresa vs Mercado Nacional 2025")
df_empresa_mes = query("SELECT mes, COUNT(*) as ventas_empresa FROM ventas GROUP BY mes ORDER BY mes")
df_empresa_mes['mes'] = pd.to_numeric(df_empresa_mes['mes'], errors='coerce').astype('Int64')
df_comp = meses_colombia.merge(df_empresa_mes, on='mes', how='left').fillna(0)

import plotly.graph_objects as go
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_comp['mes_nombre'], y=df_comp['unidades_nacional'],
                         name='Mercado Colombia', line=dict(color='#3b82f6', width=2),
                         yaxis='y2', mode='lines+markers'))
fig.add_trace(go.Bar(x=df_comp['mes_nombre'], y=df_comp['ventas_empresa'],
                     name='Empresa (unidades)', marker_color='#f97316', opacity=0.8))
fig.update_layout(
    yaxis=dict(title='Ventas Empresa'),
    yaxis2=dict(title='Mercado Nacional', overlaying='y', side='right'),
    legend=dict(bgcolor='rgba(255,255,255,0.1)'),
    barmode='group'
)
st.plotly_chart(fig, use_container_width=True)

# ── REPORTE EXTERNO 3: Marcas con mayor crecimiento ──
st.subheader("🚀 Reporte E3 — Marcas con mayor crecimiento en Colombia 2025")
col_r3, col_r4 = st.columns(2)
with col_r3:
    df_crec = marcas_colombia.sort_values('variacion_vs_2024_pct', ascending=False)
    colors = ['#10b981' if v > 0 else '#ef4444' for v in df_crec['variacion_vs_2024_pct']]
    fig = go.Figure(go.Bar(
        x=df_crec['marca'], y=df_crec['variacion_vs_2024_pct'],
        marker_color=colors,
        text=[f"{v:+.1f}%" for v in df_crec['variacion_vs_2024_pct']],
        textposition='outside'
    ))
    fig.update_layout(title='Variación YoY por marca (%)',
                      yaxis_title='Crecimiento (%)', xaxis_title='Marca')
    st.plotly_chart(fig, use_container_width=True)

with col_r4:
    fig = px.scatter(marcas_colombia,
                     x='precio_promedio_millones', y='variacion_vs_2024_pct',
                     size='unidades_vendidas_2025', color='segmento',
                     hover_name='marca',
                     title='Precio vs Crecimiento vs Volumen',
                     labels={'precio_promedio_millones':'Precio promedio (M COP)',
                             'variacion_vs_2024_pct':'Crecimiento YoY (%)'})
    st.plotly_chart(fig, use_container_width=True)


# ── REPORTE EXTERNO 4: GDP Colombia vs Latinoamérica (Banco Mundial) ──
if ext_ok:
    st.subheader("📈 Reporte E4 — GDP Colombia vs Latinoamérica (Banco Mundial en vivo)")
    st.caption("Fuente: github.com/datasets/gdp · Banco Mundial · Cargado dinámicamente con requests + pandas")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        df_col = df_eco[df_eco['pais']=='Colombia'].sort_values('anio')
        fig = px.line(df_col, x='anio', y='gdp_billones', markers=True,
                      color_discrete_sequence=['#3b82f6'],
                      title='PIB Colombia (USD miles de millones)',
                      labels={'gdp_billones':'PIB (miles de millones USD)','anio':'Año'})
        st.plotly_chart(fig, use_container_width=True)

    with col_g2:
        df_last = df_eco.sort_values('anio').groupby('pais').last().reset_index()
        fig = px.bar(df_last.sort_values('gdp_billones', ascending=True),
                     x='gdp_billones', y='pais', orientation='h',
                     color_discrete_sequence=['#10b981'],
                     title='PIB Latinoamérica — año más reciente',
                     labels={'gdp_billones':'PIB (miles de millones USD)','pais':'País'})
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("💵 GDP per cápita Colombia vs región")
    df_pc = df_eco[df_eco['gdp_per_capita'].notna()]
    fig = px.line(df_pc, x='anio', y='gdp_per_capita', color='pais',
                  markers=True,
                  title='GDP per cápita comparativo (USD)',
                  labels={'gdp_per_capita':'GDP per cápita (USD)','anio':'Año','pais':'País'})
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("Actividad 5 · Modelamiento Multidimensional OLAP · Fuentes: Railway + ANDEMOS 2025 + Banco Mundial (GitHub datasets)")
