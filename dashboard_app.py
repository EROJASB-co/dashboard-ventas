import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px

# ============================================
# CAMBIA ESTOS VALORES POR LOS DE RAILWAY
# ============================================
DB_HOST     = 'switchyard.proxy.rlwy.net'
DB_PORT     = 31938
DB_USER     = 'root'
DB_PASSWORD = 'TU_PASSWORD_RAILWAY'
DB_NAME     = 'sistemaventas'
# ============================================

st.set_page_config(page_title="Cuadro de Mando - Sistema Ventas", layout="wide", page_icon="car")

@st.cache_resource
def get_conn():
    return mysql.connector.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASSWORD,
        database=DB_NAME
    )

def query(sql):
    conn = get_conn()
    return pd.read_sql(sql, conn)

st.title("Cuadro de Mando - Sistema Ventas")
st.caption("Datos en tiempo real desde Railway")

if st.button("Actualizar datos"):
    st.cache_resource.clear()
    st.rerun()

st.divider()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Clientes",    query("SELECT COUNT(*) as t FROM clientes").iloc[0,0])
col2.metric("Vehiculos",   query("SELECT COUNT(*) as t FROM vehiculos").iloc[0,0])
col3.metric("Vendedores",  query("SELECT COUNT(*) as t FROM vendedores").iloc[0,0])
col4.metric("Ventas",      query("SELECT COUNT(*) as t FROM ventas").iloc[0,0])
ingresos = query("SELECT SUM(valor_venta) as t FROM ventas").iloc[0,0]
col5.metric("Ingresos",    f"${int(ingresos)/1_000_000:.1f}M")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Ventas por mes")
    df = query("SELECT mes, SUM(valor_venta) as total FROM ventas GROUP BY mes ORDER BY mes")
    st.plotly_chart(px.bar(df, x='mes', y='total', color_discrete_sequence=['#3b82f6']), use_container_width=True)

with col_b:
    st.subheader("Top 10 marcas")
    df = query("""SELECT v.marca, SUM(ve.valor_venta) as total 
                  FROM ventas ve JOIN vehiculos v ON ve.cod_vehiculos = v.cod_vehiculo 
                  GROUP BY v.marca ORDER BY total DESC LIMIT 10""")
    st.plotly_chart(px.bar(df, x='total', y='marca', orientation='h', color_discrete_sequence=['#10b981']), use_container_width=True)

col_c, col_d, col_e = st.columns(3)

with col_c:
    st.subheader("Top vendedores")
    df = query("""SELECT ve.nombre_vendedor, SUM(v.valor_venta) as total 
                  FROM ventas v JOIN vendedores ve ON v.id_vendedor = ve.id_vendedor 
                  GROUP BY ve.id_vendedor ORDER BY total DESC LIMIT 10""")
    st.plotly_chart(px.bar(df, x='total', y='nombre_vendedor', orientation='h', color_discrete_sequence=['#f59e0b']), use_container_width=True)

with col_d:
    st.subheader("Ventas por ciudad")
    df = query("""SELECT c.ciudad, SUM(v.valor_venta) as total 
                  FROM ventas v JOIN clientes c ON v.cod_cliente = c.cod_cliente 
                  GROUP BY c.ciudad ORDER BY total DESC LIMIT 10""")
    st.plotly_chart(px.pie(df, values='total', names='ciudad', hole=0.4), use_container_width=True)

with col_e:
    st.subheader("Medio de pago")
    df = query("SELECT medio_pago, COUNT(*) as cantidad FROM ventas GROUP BY medio_pago")
    st.plotly_chart(px.pie(df, values='cantidad', names='medio_pago', hole=0.4), use_container_width=True)

st.subheader("Ventas por anno")
df = query("SELECT anio, SUM(valor_venta) as total FROM ventas GROUP BY anio ORDER BY anio")
st.plotly_chart(px.line(df, x='anio', y='total', markers=True, color_discrete_sequence=['#8b5cf6']), use_container_width=True)
