import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# ============================================
# CAMBIA ESTOS VALORES POR LOS DE RAILWAY
# ============================================
DB_HOST     = 'switchyard.proxy.rlwy.net'
DB_PORT     = 31938
DB_USER     = 'root'
DB_PASSWORD = 'NwxVlDNryxmxWvIAekIPWqTnHxsUFuQp'
DB_NAME     = 'sistemaventas'
# ============================================

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
        st.plotly_chart(px.bar(df, x='mes', y='total', color_discrete_sequence=['#3b82f6']), width='stretch')
    else:
        st.info("Sin datos")

with col_b:
    st.subheader("🏎️ Top 10 marcas")
    df = query("""SELECT v.marca, SUM(ve.valor_venta) as total 
                  FROM ventas ve JOIN vehiculos v ON ve.cod_vehiculos = v.cod_vehiculo 
                  GROUP BY v.marca ORDER BY total DESC LIMIT 10""")
    if not df.empty:
        st.plotly_chart(px.bar(df, x='total', y='marca', orientation='h', color_discrete_sequence=['#10b981']), width='stretch')
    else:
        st.info("Sin datos")

col_c, col_d, col_e = st.columns(3)

with col_c:
    st.subheader("🧑‍💼 Top vendedores")
    df = query("""SELECT CONCAT(ve.nombres, ' ', ve.apellidos) as nombre_vendedor, SUM(v.valor_venta) as total 
                  FROM ventas v JOIN vendedores ve ON v.id_vendedor = ve.id_vendedor 
                  GROUP BY ve.id_vendedor ORDER BY total DESC LIMIT 10""")
    if not df.empty:
        st.plotly_chart(px.bar(df, x='total', y='nombre_vendedor', orientation='h', color_discrete_sequence=['#f59e0b']), width='stretch')
    else:
        st.info("Sin datos")

with col_d:
    st.subheader("🏙️ Ventas por ciudad")
    df = query("""SELECT c.ciudad, SUM(v.valor_venta) as total 
                  FROM ventas v JOIN clientes c ON v.cod_cliente = c.cod_cliente 
                  GROUP BY c.ciudad ORDER BY total DESC LIMIT 10""")
    if not df.empty:
        st.plotly_chart(px.pie(df, values='total', names='ciudad', hole=0.4), width='stretch')
    else:
        st.info("Sin datos")

with col_e:
    st.subheader("💳 Medio de pago")
    df = query("SELECT medio_pago, COUNT(*) as cantidad FROM ventas GROUP BY medio_pago")
    if not df.empty:
        st.plotly_chart(px.pie(df, values='cantidad', names='medio_pago', hole=0.4), width='stretch')
    else:
        st.info("Sin datos")

st.subheader("📈 Ventas por año")
df = query("SELECT anio, SUM(valor_venta) as total FROM ventas GROUP BY anio ORDER BY anio")
if not df.empty:
    st.plotly_chart(px.line(df, x='anio', y='total', markers=True, color_discrete_sequence=['#8b5cf6']), width='stretch')
else:
    st.info("Sin datos")
