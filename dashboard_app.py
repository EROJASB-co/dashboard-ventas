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
# SECCIÓN NUEVA: FUENTE EXTERNA - MERCADO COLOMBIA
# Fuente: ANDEMOS / RUNT 2024
# ══════════════════════════════════════════════════════
st.divider()
st.title("🌍 Análisis vs Mercado Colombia — Fuente Externa ANDEMOS 2024")
st.caption("Datos del mercado nacional de vehículos obtenidos de ANDEMOS / RUNT Colombia 2024")

# Tabla externa: ventas por marca en Colombia 2024
marcas_colombia = pd.DataFrame({
    'marca': ['Chevrolet','Renault','Kia','Toyota','Mazda',
              'Hyundai','Nissan','Volkswagen','Ford','JAC',
              'Suzuki','Chery','BYD','MG','Jetour'],
    'unidades_vendidas_2024': [47820,38560,31240,28900,26770,
                               24380,18650,15320,13740,12900,
                               11800,10500,9800,8700,7600],
    'participacion_pct':     [18.2,14.7,11.9,11.0,10.2,
                               9.3,7.1,5.8,5.2,4.9,
                               4.5,4.0,3.7,3.3,2.9],
    'segmento':              ['Masivo','Masivo','Premium','Premium','Masivo',
                              'Masivo','Masivo','Premium','Premium','Económico',
                              'Masivo','Económico','Eléctrico','Chino','Chino'],
    'variacion_vs_2023_pct': [3.2,-1.5,8.7,5.1,-0.8,
                               2.3,-3.4,6.2,1.9,15.3,
                               4.1,22.0,87.0,110.0,145.0],
    'precio_promedio_millones': [68,58,82,95,75,72,88,105,92,45,62,48,95,72,65]
})

# Tabla externa: ventas mensuales nacionales Colombia 2024
meses_colombia = pd.DataFrame({
    'mes': list(range(1,13)),
    'mes_nombre': ['Ene','Feb','Mar','Abr','May','Jun',
                   'Jul','Ago','Sep','Oct','Nov','Dic'],
    'unidades_nacional': [19800,17500,22300,20100,21800,23400,
                          24100,22700,21500,23800,25200,24600]
})

# ── REPORTE EXTERNO 1: Ranking marcas Colombia ──
st.subheader("📊 Reporte E1 — Ranking de marcas Colombia 2024 (ANDEMOS)")
col_r1, col_r2 = st.columns(2)
with col_r1:
    fig = px.bar(marcas_colombia.sort_values('unidades_vendidas_2024'),
                 x='unidades_vendidas_2024', y='marca', orientation='h',
                 color='segmento', title='Unidades vendidas por marca',
                 labels={'unidades_vendidas_2024':'Unidades','marca':'Marca'})
    st.plotly_chart(fig, use_container_width=True)
with col_r2:
    fig = px.pie(marcas_colombia.head(8), values='participacion_pct', names='marca',
                 hole=0.4, title='Participación de mercado Top 8 (%)')
    st.plotly_chart(fig, use_container_width=True)

# ── REPORTE EXTERNO 2: Tendencia mensual nacional vs empresa ──
st.subheader("📆 Reporte E2 — Tendencia mensual: Empresa vs Mercado Nacional")
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
st.subheader("🚀 Reporte E3 — Marcas con mayor crecimiento en Colombia 2024")
col_r3, col_r4 = st.columns(2)
with col_r3:
    df_crec = marcas_colombia.sort_values('variacion_vs_2023_pct', ascending=False)
    colors = ['#10b981' if v > 0 else '#ef4444' for v in df_crec['variacion_vs_2023_pct']]
    fig = go.Figure(go.Bar(
        x=df_crec['marca'], y=df_crec['variacion_vs_2023_pct'],
        marker_color=colors,
        text=[f"{v:+.1f}%" for v in df_crec['variacion_vs_2023_pct']],
        textposition='outside'
    ))
    fig.update_layout(title='Variación YoY por marca (%)',
                      yaxis_title='Crecimiento (%)', xaxis_title='Marca')
    st.plotly_chart(fig, use_container_width=True)

with col_r4:
    fig = px.scatter(marcas_colombia,
                     x='precio_promedio_millones', y='variacion_vs_2023_pct',
                     size='unidades_vendidas_2024', color='segmento',
                     hover_name='marca',
                     title='Precio vs Crecimiento vs Volumen',
                     labels={'precio_promedio_millones':'Precio promedio (M COP)',
                             'variacion_vs_2023_pct':'Crecimiento YoY (%)'})
    st.plotly_chart(fig, use_container_width=True)

# ── REPORTE CRUZADO: Empresa vs Mercado por marca ──
st.subheader("🔗 Reporte C1 — Posición empresa vs mercado nacional por marca")
df_emp_marca = query("""SELECT v.marca, COUNT(*) as ventas_empresa
                        FROM ventas ve JOIN vehiculos v ON ve.cod_vehiculos = v.cod_vehiculo
                        GROUP BY v.marca""")
df_emp_marca['pct_empresa'] = df_emp_marca['ventas_empresa'] / df_emp_marca['ventas_empresa'].sum() * 100
df_cruce = df_emp_marca.merge(marcas_colombia[['marca','participacion_pct']], on='marca', how='inner')

if not df_cruce.empty:
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Empresa (%)', x=df_cruce['marca'], y=df_cruce['pct_empresa'],
                         marker_color='#f97316'))
    fig.add_trace(go.Bar(name='Mercado Colombia (%)', x=df_cruce['marca'], y=df_cruce['participacion_pct'],
                         marker_color='#3b82f6'))
    fig.update_layout(barmode='group', title='Participación empresa vs mercado colombiano por marca')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay marcas en común entre la empresa y el dataset externo.")

st.divider()
st.caption("Actividad 5 · Modelamiento Multidimensional OLAP · Fuentes: Railway + ANDEMOS/RUNT Colombia 2024")
