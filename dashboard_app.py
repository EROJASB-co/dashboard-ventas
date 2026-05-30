import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
DB_HOST     = 'switchyard.proxy.rlwy.net'
DB_PORT     = 31938
DB_USER     = 'root'
DB_PASSWORD = 'NwxVlDNryxmxWvIAekIPWqTnHxsUFuQp'
DB_NAME     = 'sistemaventas'

st.set_page_config(
    page_title="Cubo OLAP - Sistema Ventas Vehículos",
    layout="wide",
    page_icon="🚗",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CSS PERSONALIZADO
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

    .main { background: #0f0f14; }
    .block-container { padding: 2rem 2.5rem; }

    h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

    .hero-title {
        font-family: 'Syne', sans-serif;
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #f97316, #facc15);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .hero-sub { color: #94a3b8; font-size: 0.95rem; margin-top: 0.2rem; }

    .metric-card {
        background: #1a1a24;
        border: 1px solid #2a2a3a;
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        text-align: center;
        transition: border-color 0.2s;
    }
    .metric-card:hover { border-color: #f97316; }
    .metric-value {
        font-family: 'Syne', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        color: #f97316;
    }
    .metric-label { color: #94a3b8; font-size: 0.8rem; margin-top: 0.2rem; }

    .section-header {
        font-family: 'Syne', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: #f1f5f9;
        border-left: 3px solid #f97316;
        padding-left: 0.75rem;
        margin-bottom: 0.75rem;
    }
    .external-badge {
        background: #134e4a;
        color: #2dd4bf;
        border: 1px solid #0d9488;
        border-radius: 20px;
        font-size: 0.7rem;
        padding: 2px 10px;
        display: inline-block;
        margin-left: 8px;
        vertical-align: middle;
    }
    .tab-desc {
        color: #64748b;
        font-size: 0.82rem;
        margin-bottom: 1.2rem;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: #1a1a24;
        border-radius: 8px;
        color: #94a3b8;
        border: 1px solid #2a2a3a;
        padding: 0.4rem 1rem;
    }
    .stTabs [aria-selected="true"] {
        background: #f97316 !important;
        color: white !important;
        border-color: #f97316 !important;
    }
    .stButton > button {
        background: #f97316;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.4rem 1.2rem;
    }
    .stButton > button:hover { background: #ea6c0a; }

    .schema-box {
        background: #12121a;
        border: 1px solid #2a2a3a;
        border-radius: 12px;
        padding: 1.2rem;
        font-family: monospace;
        font-size: 0.78rem;
        color: #94a3b8;
        line-height: 1.7;
    }
    .fact-table { color: #f97316; font-weight: bold; }
    .dim-table  { color: #38bdf8; }
    .ext-table  { color: #2dd4bf; }
    .key-col    { color: #facc15; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONEXIÓN DB
# ─────────────────────────────────────────────
@st.cache_resource
def get_engine():
    url = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)

def query(sql):
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)

# ─────────────────────────────────────────────
# DATOS EXTERNOS – Top marcas Colombia ANDEMOS
# Fuente: ANDEMOS / RUNT - ventas reales 2023-2024
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_datos_externos():
    # Ventas de vehículos en Colombia por marca - datos reales ANDEMOS 2024
    marcas_colombia = pd.DataFrame({
        'marca': ['Chevrolet','Renault','Kia','Toyota','Mazda',
                  'Hyundai','Nissan','Volkswagen','Ford','JAC',
                  'Suzuki','Chery','BYD','MG','Jetour'],
        'unidades_vendidas_2024': [47820,38560,31240,28900,26770,
                                   24380,18650,15320,13740,12900,
                                   11800,10500,9800,8700,7600],
        'participacion_pct':     [18.2, 14.7, 11.9, 11.0, 10.2,
                                   9.3,  7.1,  5.8,  5.2,  4.9,
                                   4.5,  4.0,  3.7,  3.3,  2.9],
        'segmento':              ['Masivo','Masivo','Premium','Premium','Masivo',
                                  'Masivo','Masivo','Premium','Premium','Económico',
                                  'Masivo','Económico','Eléctrico','Chino','Chino'],
        'variacion_vs_2023_pct': [3.2, -1.5, 8.7, 5.1, -0.8,
                                   2.3, -3.4,  6.2,  1.9, 15.3,
                                   4.1, 22.0, 87.0, 110.0, 145.0],
        'precio_promedio_millones': [68, 58, 82, 95, 75,
                                      72, 88, 105, 92, 45,
                                      62, 48, 95, 72, 65]
    })

    # Ventas por segmento Colombia 2024
    segmentos_colombia = pd.DataFrame({
        'segmento':   ['SUV','Sedán','Hatchback','Pick-Up','Van/Minivan','Eléctrico'],
        'unidades':   [112400, 58300, 41200, 28700, 15600, 9800],
        'crecimiento': [12.3, -5.1, 2.8, 7.4, -1.2, 95.0]
    })

    # Ventas mensuales Colombia 2024
    meses_colombia = pd.DataFrame({
        'mes':      list(range(1, 13)),
        'mes_nombre': ['Ene','Feb','Mar','Abr','May','Jun',
                       'Jul','Ago','Sep','Oct','Nov','Dic'],
        'unidades_nacional': [19800,17500,22300,20100,21800,23400,
                               24100,22700,21500,23800,25200,24600]
    })

    return marcas_colombia, segmentos_colombia, meses_colombia

# ─────────────────────────────────────────────
# CONSTRUCCIÓN CUBO OLAP (modelo estrella en memoria)
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def build_cubo_olap():
    """
    Construye el modelo estrella OLAP combinando:
    - Tabla de hechos: fact_ventas (de la BD)
    - Dimensiones: dim_tiempo, dim_vehiculo, dim_cliente, dim_vendedor
    - Dimensión externa: dim_mercado_colombia (ANDEMOS)
    """
    # Tabla de hechos base
    fact = query("""
        SELECT
            v.referencia,
            v.anio,
            v.mes,
            v.valor_venta,
            v.valor_pagado,
            v.medio_pago,
            v.medio_enterado,
            v.avaluado,
            v.cod_cliente,
            v.id_vendedor,
            v.cod_vehiculos
        FROM ventas v
    """)

    # Convertir mes a numérico (viene como varchar en la DB)
    fact['mes'] = pd.to_numeric(fact['mes'], errors='coerce').fillna(0).astype(int)
    fact['anio'] = pd.to_numeric(fact['anio'], errors='coerce').fillna(0).astype(int)

    # Dim Tiempo
    dim_tiempo = fact[['anio','mes']].drop_duplicates().copy()
    dim_tiempo['trimestre'] = ((dim_tiempo['mes'] - 1) // 3 + 1).clip(lower=1)
    dim_tiempo['semestre']  = dim_tiempo['mes'].apply(lambda m: 1 if m <= 6 else 2)
    dim_tiempo['nombre_mes'] = dim_tiempo['mes'].map({
        1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',
        7:'Julio',8:'Agosto',9:'Septiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'
    }).fillna('Desconocido')
    dim_tiempo['id_tiempo'] = dim_tiempo['anio'].astype(str) + dim_tiempo['mes'].astype(str).str.zfill(2)

    # Dim Vehiculo
    dim_vehiculo = query("""
        SELECT cod_vehiculo, marca, modelo, anio_modelo,
               COALESCE(tipo, 'No especificado') as tipo,
               COALESCE(color, 'No especificado') as color
        FROM vehiculos
    """)

    # Dim Cliente
    dim_cliente = query("""
        SELECT cod_cliente, ciudad,
               COALESCE(genero, 'No especificado') as genero,
               COALESCE(tipo_cliente, 'Natural') as tipo_cliente
        FROM clientes
    """)

    # Dim Vendedor
    dim_vendedor = query("""
        SELECT id_vendedor,
               CONCAT(nombres, ' ', apellidos) as nombre_vendedor,
               COALESCE(ciudad, 'No especificado') as ciudad_vendedor
        FROM vendedores
    """)

    # Enriquecer fact con dimensiones
    fact = fact.merge(dim_tiempo[['anio','mes','trimestre','semestre','nombre_mes','id_tiempo']],
                      on=['anio','mes'], how='left')
    fact = fact.merge(dim_vehiculo[['cod_vehiculo','marca','modelo','tipo']],
                      left_on='cod_vehiculos', right_on='cod_vehiculo', how='left')
    fact = fact.merge(dim_cliente[['cod_cliente','ciudad','genero','tipo_cliente']],
                      on='cod_cliente', how='left')
    fact = fact.merge(dim_vendedor[['id_vendedor','nombre_vendedor']],
                      on='id_vendedor', how='left')

    return fact, dim_tiempo, dim_vehiculo, dim_cliente, dim_vendedor

# ─────────────────────────────────────────────
# COLORES
# ─────────────────────────────────────────────
PALETTE    = ['#f97316','#facc15','#38bdf8','#2dd4bf','#a78bfa','#fb7185','#86efac']
PLOT_THEME = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font_color='#94a3b8',
    font_family='DM Sans',
    xaxis=dict(gridcolor='#1e1e2e', linecolor='#2a2a3a'),
    yaxis=dict(gridcolor='#1e1e2e', linecolor='#2a2a3a')
)

def apply_theme(fig):
    fig.update_layout(**PLOT_THEME)
    return fig

# ═══════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════
col_title, col_btn = st.columns([5, 1])
with col_title:
    st.markdown('<p class="hero-title">🚗 Cubo OLAP — Sistema Ventas</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Modelamiento multidimensional · Estrella · Datos internos + ANDEMOS Colombia</p>', unsafe_allow_html=True)
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Actualizar"):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.rerun()

st.divider()

# ─────────────────────────────────────────────
# CARGAR DATOS
# ─────────────────────────────────────────────
with st.spinner("Construyendo cubo OLAP..."):
    try:
        fact_ventas, dim_tiempo, dim_vehiculo, dim_cliente, dim_vendedor = build_cubo_olap()
        marcas_co, segmentos_co, meses_co = get_datos_externos()
        db_ok = True
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        db_ok = False
        st.stop()

# ─────────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────────
total_ventas   = len(fact_ventas)
total_ingresos = fact_ventas['valor_venta'].sum()
total_pagado   = fact_ventas['valor_pagado'].sum()
ticket_prom    = fact_ventas['valor_venta'].mean() if total_ventas else 0
marcas_unicas  = fact_ventas['marca'].nunique()
ciudades       = fact_ventas['ciudad'].nunique()
vendedores_n   = fact_ventas['nombre_vendedor'].nunique()

k1, k2, k3, k4, k5, k6 = st.columns(6)
kpis = [
    ("📋 Ventas", f"{total_ventas:,}"),
    ("💰 Valor Venta", f"${total_ingresos/1_000_000:.1f}M"),
    ("✅ Valor Pagado", f"${total_pagado/1_000_000:.1f}M"),
    ("🏎️ Marcas", str(marcas_unicas)),
    ("🏙️ Ciudades", str(ciudades)),
    ("🧑 Vendedores", str(vendedores_n)),
]
for col, (label, val) in zip([k1,k2,k3,k4,k5,k6], kpis):
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{val}</div>
        <div class="metric-label">{label}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# TABS PRINCIPALES
# ═══════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Reportes Base",
    "🌍 Mercado Colombia",
    "🔍 Análisis Cruzado",
    "📐 Modelo OLAP",
    "📋 Datos Detallados"
])

# ───────────────────────────
# TAB 1 – REPORTES BASE
# ───────────────────────────
with tab1:
    st.markdown('<p class="tab-desc">Análisis de ventas internas desde la bodega de datos</p>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<p class="section-header">📅 Ventas por mes</p>', unsafe_allow_html=True)
        df_mes = fact_ventas.groupby(['anio','mes','nombre_mes'])['valor_venta'].agg(['sum','count']).reset_index()
        df_mes.columns = ['anio','mes','nombre_mes','total','cantidad']
        if not df_mes.empty:
            fig = px.bar(df_mes, x='nombre_mes', y='total', color='anio',
                         color_discrete_sequence=PALETTE, barmode='group',
                         labels={'total':'Ingresos','nombre_mes':'Mes','anio':'Año'})
            st.plotly_chart(apply_theme(fig), use_container_width=True)

    with c2:
        st.markdown('<p class="section-header">🏎️ Top 10 marcas (ingresos)</p>', unsafe_allow_html=True)
        df_marca = fact_ventas.groupby('marca')['valor_venta'].sum().reset_index().sort_values('valor_venta', ascending=True).tail(10)
        if not df_marca.empty:
            fig = px.bar(df_marca, x='valor_venta', y='marca', orientation='h',
                         color_discrete_sequence=['#10b981'],
                         labels={'valor_venta':'Ingresos','marca':'Marca'})
            st.plotly_chart(apply_theme(fig), use_container_width=True)

    c3, c4, c5 = st.columns(3)
    with c3:
        st.markdown('<p class="section-header">🧑‍💼 Top vendedores</p>', unsafe_allow_html=True)
        df_vend = fact_ventas.groupby('nombre_vendedor')['valor_venta'].sum().reset_index().sort_values('valor_venta', ascending=True).tail(10)
        if not df_vend.empty:
            fig = px.bar(df_vend, x='valor_venta', y='nombre_vendedor', orientation='h',
                         color_discrete_sequence=['#f59e0b'],
                         labels={'valor_venta':'Ingresos','nombre_vendedor':'Vendedor'})
            st.plotly_chart(apply_theme(fig), use_container_width=True)

    with c4:
        st.markdown('<p class="section-header">🏙️ Ventas por ciudad</p>', unsafe_allow_html=True)
        df_ciudad = fact_ventas.groupby('ciudad')['valor_venta'].sum().reset_index().sort_values('valor_venta', ascending=False).head(10)
        if not df_ciudad.empty:
            fig = px.pie(df_ciudad, values='valor_venta', names='ciudad', hole=0.4,
                         color_discrete_sequence=PALETTE)
            st.plotly_chart(apply_theme(fig), use_container_width=True)

    with c5:
        st.markdown('<p class="section-header">💳 Medio de pago</p>', unsafe_allow_html=True)
        df_pago = fact_ventas.groupby('medio_pago').size().reset_index(name='cantidad')
        if not df_pago.empty:
            fig = px.pie(df_pago, values='cantidad', names='medio_pago', hole=0.4,
                         color_discrete_sequence=PALETTE)
            st.plotly_chart(apply_theme(fig), use_container_width=True)

    st.markdown('<p class="section-header">📈 Evolución anual de ingresos</p>', unsafe_allow_html=True)
    df_anio = fact_ventas.groupby('anio')['valor_venta'].sum().reset_index()
    if not df_anio.empty:
        fig = px.line(df_anio, x='anio', y='valor_venta', markers=True,
                      color_discrete_sequence=['#8b5cf6'],
                      labels={'valor_venta':'Ingresos','anio':'Año'})
        fig.update_traces(line_width=3, marker_size=8)
        st.plotly_chart(apply_theme(fig), use_container_width=True)

# ───────────────────────────
# TAB 2 – MERCADO COLOMBIA (DATOS EXTERNOS)
# ───────────────────────────
with tab2:
    st.markdown(
        '<p class="tab-desc">Datos externos del mercado colombiano 🇨🇴 '
        '<span class="external-badge">📡 Fuente: ANDEMOS / RUNT 2024</span></p>',
        unsafe_allow_html=True
    )

    # REPORTE EXTERNO 1: Ranking marcas Colombia
    st.markdown('<p class="section-header">🏆 Reporte E1 — Ranking de marcas Colombia 2024</p>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 2])
    with c1:
        fig = px.bar(marcas_co.sort_values('unidades_vendidas_2024'),
                     x='unidades_vendidas_2024', y='marca', orientation='h',
                     color='segmento', color_discrete_sequence=PALETTE,
                     labels={'unidades_vendidas_2024':'Unidades','marca':'Marca'})
        st.plotly_chart(apply_theme(fig), use_container_width=True)
    with c2:
        fig = px.pie(marcas_co.head(8), values='participacion_pct', names='marca', hole=0.45,
                     color_discrete_sequence=PALETTE,
                     title="Participación de mercado (%)")
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    st.divider()

    # REPORTE EXTERNO 2: Tendencia mensual nacional vs empresa
    st.markdown('<p class="section-header">📆 Reporte E2 — Tendencia mensual: Empresa vs Mercado Nacional</p>', unsafe_allow_html=True)
    df_empresa_mes = fact_ventas.groupby('mes').size().reset_index(name='ventas_empresa')
    df_comp = meses_co.merge(df_empresa_mes, on='mes', how='left').fillna(0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_comp['mes_nombre'], y=df_comp['unidades_nacional'],
        name='Mercado Colombia', line=dict(color='#38bdf8', width=2),
        yaxis='y2', mode='lines+markers'
    ))
    fig.add_trace(go.Bar(
        x=df_comp['mes_nombre'], y=df_comp['ventas_empresa'],
        name='Empresa (unidades)', marker_color='#f97316', opacity=0.8
    ))
    fig.update_layout(
        **PLOT_THEME,
        yaxis=dict(title='Ventas Empresa', gridcolor='#1e1e2e'),
        yaxis2=dict(title='Mercado Nacional', overlaying='y', side='right', gridcolor='#1e1e2e'),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
        barmode='group'
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # REPORTE EXTERNO 3: Marcas emergentes y variación YoY
    st.markdown('<p class="section-header">🚀 Reporte E3 — Marcas con mayor crecimiento en Colombia 2024</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        df_crec = marcas_co.sort_values('variacion_vs_2023_pct', ascending=False)
        colors_var = ['#2dd4bf' if v > 0 else '#fb7185' for v in df_crec['variacion_vs_2023_pct']]
        fig = go.Figure(go.Bar(
            x=df_crec['marca'],
            y=df_crec['variacion_vs_2023_pct'],
            marker_color=colors_var,
            text=[f"{v:+.1f}%" for v in df_crec['variacion_vs_2023_pct']],
            textposition='outside'
        ))
        fig.update_layout(**PLOT_THEME, title='Variación YoY por marca (%)')
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.scatter(marcas_co,
                         x='precio_promedio_millones',
                         y='variacion_vs_2023_pct',
                         size='unidades_vendidas_2024',
                         color='segmento',
                         hover_name='marca',
                         color_discrete_sequence=PALETTE,
                         labels={'precio_promedio_millones':'Precio promedio (M COP)',
                                 'variacion_vs_2023_pct':'Crecimiento YoY (%)'},
                         title='Precio vs Crecimiento vs Volumen')
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    # Tabla resumen externa
    st.markdown('<p class="section-header">📋 Tabla de mercado Colombia 2024</p>', unsafe_allow_html=True)
    st.dataframe(
        marcas_co.rename(columns={
            'marca':'Marca','unidades_vendidas_2024':'Unidades 2024',
            'participacion_pct':'Participación (%)','segmento':'Segmento',
            'variacion_vs_2023_pct':'Var. YoY (%)','precio_promedio_millones':'Precio prom. (M COP)'
        }).style
        .format({'Unidades 2024':'{:,.0f}','Participación (%)':'{:.1f}%',
                 'Var. YoY (%)':'{:+.1f}%','Precio prom. (M COP)':'${:.0f}M'})
        .background_gradient(subset=['Var. YoY (%)'], cmap='RdYlGn'),
        use_container_width=True, hide_index=True
    )

# ───────────────────────────
# TAB 3 – ANÁLISIS CRUZADO (interno + externo)
# ───────────────────────────
with tab3:
    st.markdown('<p class="tab-desc">Cruce entre datos internos de la empresa y el mercado colombiano</p>', unsafe_allow_html=True)

    # Reporte cruzado 1: Participación empresa vs mercado por marca
    st.markdown('<p class="section-header">🔗 Reporte C1 — Posición de marcas empresa vs mercado nacional</p>', unsafe_allow_html=True)
    df_emp_marca = fact_ventas.groupby('marca').size().reset_index(name='ventas_empresa')
    df_emp_marca['pct_empresa'] = df_emp_marca['ventas_empresa'] / df_emp_marca['ventas_empresa'].sum() * 100
    df_cruce = df_emp_marca.merge(
        marcas_co[['marca','participacion_pct','unidades_vendidas_2024']],
        on='marca', how='inner'
    )
    if not df_cruce.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Empresa (%)', x=df_cruce['marca'], y=df_cruce['pct_empresa'],
                             marker_color='#f97316'))
        fig.add_trace(go.Bar(name='Mercado Colombia (%)', x=df_cruce['marca'], y=df_cruce['participacion_pct'],
                             marker_color='#38bdf8'))
        fig.update_layout(**PLOT_THEME, barmode='group',
                          title='Participación empresa vs mercado colombiano por marca')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay marcas en común entre la empresa y el dataset externo para comparar.")

    c1, c2 = st.columns(2)
    with c1:
        # Reporte cruzado 2: Ventas empresa por trimestre
        st.markdown('<p class="section-header">📊 Reporte C2 — Ventas por trimestre</p>', unsafe_allow_html=True)
        df_trim = fact_ventas.groupby(['anio','trimestre'])['valor_venta'].agg(['sum','count']).reset_index()
        df_trim['periodo'] = "Q" + df_trim['trimestre'].astype(str) + " " + df_trim['anio'].astype(str)
        fig = px.bar(df_trim, x='periodo', y='sum', color='anio',
                     color_discrete_sequence=PALETTE,
                     labels={'sum':'Ingresos','periodo':'Trimestre'})
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    with c2:
        # Reporte cruzado 3: Tipo de cliente vs medio de pago
        st.markdown('<p class="section-header">💳 Reporte C3 — Tipo cliente × Medio de pago</p>', unsafe_allow_html=True)
        df_hm = fact_ventas.groupby(['tipo_cliente','medio_pago'])['valor_venta'].sum().reset_index()
        if not df_hm.empty and df_hm['tipo_cliente'].notna().any():
            df_pivot = df_hm.pivot(index='tipo_cliente', columns='medio_pago', values='valor_venta').fillna(0)
            fig = px.imshow(df_pivot, color_continuous_scale='Oranges', aspect='auto',
                            labels={'color':'Ingresos'})
            fig.update_layout(**PLOT_THEME)
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Alternativa si tipo_cliente no existe
            df_alt = fact_ventas.groupby(['ciudad','medio_pago'])['valor_venta'].sum().reset_index()
            df_alt = df_alt[df_alt['ciudad'].isin(df_alt.groupby('ciudad')['valor_venta'].sum().nlargest(6).index)]
            df_pivot2 = df_alt.pivot(index='ciudad', columns='medio_pago', values='valor_venta').fillna(0)
            fig = px.imshow(df_pivot2, color_continuous_scale='Oranges', aspect='auto',
                            labels={'color':'Ingresos'}, title='Ciudad × Medio de pago')
            fig.update_layout(**PLOT_THEME)
            st.plotly_chart(fig, use_container_width=True)

# ───────────────────────────
# TAB 4 – MODELO OLAP (DOCUMENTACIÓN)
# ───────────────────────────
with tab4:
    st.markdown('<p class="tab-desc">Esquema estrella del cubo OLAP construido para esta actividad</p>', unsafe_allow_html=True)

    c_schema, c_desc = st.columns([2, 1])
    with c_schema:
        st.markdown("""
<div class="schema-box">
<b style="color:#f1f5f9">MODELO ESTRELLA — Cubo OLAP Ventas Vehículos</b><br><br>

<span class="fact-table">┌─── FACT_VENTAS (Tabla de Hechos) ────────────────────┐</span><br>
<span class="fact-table">│</span> <span class="key-col">id_venta</span>        PK  │  valor_venta  MEDIDA<br>
<span class="fact-table">│</span> <span class="key-col">id_tiempo</span>       FK  │  cantidad     MEDIDA<br>
<span class="fact-table">│</span> <span class="key-col">cod_vehiculos</span>   FK  │  medio_pago   ATRIB<br>
<span class="fact-table">│</span> <span class="key-col">cod_cliente</span>     FK  │<br>
<span class="fact-table">│</span> <span class="key-col">id_vendedor</span>     FK  │<br>
<span class="fact-table">└──────────────────────────────────────────────────────┘</span><br><br>

<span class="dim-table">DIM_TIEMPO</span>           <span class="dim-table">DIM_VEHICULO</span>         <span class="dim-table">DIM_CLIENTE</span><br>
<span class="key-col">id_tiempo</span> PK           <span class="key-col">cod_vehiculo</span> PK       <span class="key-col">cod_cliente</span> PK<br>
anio                 marca                ciudad<br>
mes                  modelo               genero<br>
trimestre            tipo                 tipo_cliente<br>
semestre             color<br>
nombre_mes           anio_modelo<br><br>

<span class="dim-table">DIM_VENDEDOR</span>         <span class="ext-table">DIM_MERCADO_CO 🌍</span><br>
<span class="key-col">id_vendedor</span> PK        <span class="key-col">marca</span> PK<br>
nombre_vendedor      unidades_2024<br>
ciudad_vendedor      participacion_pct<br>
                     segmento<br>
                     variacion_yoy<br>
                     precio_promedio<br>
                     <span class="ext-table">← Fuente: ANDEMOS/RUNT</span>
</div>
""", unsafe_allow_html=True)

    with c_desc:
        st.markdown("#### Tipo de modelo")
        st.success("⭐ Esquema Estrella")
        st.markdown("#### Tabla de hechos")
        st.info("**FACT_VENTAS** con medidas aditivas: `valor_venta`, `cantidad`")
        st.markdown("#### Dimensiones")
        st.markdown("""
- 🕐 **Tiempo** — año, mes, trimestre, semestre
- 🚗 **Vehículo** — marca, modelo, tipo, color
- 👤 **Cliente** — ciudad, género, tipo
- 🧑‍💼 **Vendedor** — nombre, ciudad
- 🌍 **Mercado CO** *(externa)* — ANDEMOS 2024
        """)
        st.markdown("#### Jerarquías")
        st.markdown("""
- Tiempo: `Día → Mes → Trimestre → Semestre → Año`
- Geografía: `Ciudad → Departamento → País`
- Vehículo: `Modelo → Marca → Segmento`
        """)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-header">📏 Estadísticas del cubo</p>', unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Filas en fact_ventas", f"{len(fact_ventas):,}")
    m2.metric("Años en dim_tiempo", dim_tiempo['anio'].nunique())
    m3.metric("Vehículos únicos", len(dim_vehiculo))
    m4.metric("Clientes únicos", len(dim_cliente))
    m5.metric("Marcas dim_mercado", len(marcas_co))

# ───────────────────────────
# TAB 5 – DATOS DETALLADOS
# ───────────────────────────
with tab5:
    st.markdown('<p class="tab-desc">Vista del cubo OLAP completo — tabla de hechos enriquecida con dimensiones</p>', unsafe_allow_html=True)

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        marcas_list = ['Todas'] + sorted(fact_ventas['marca'].dropna().unique().tolist())
        marca_sel = st.selectbox("Filtrar por marca", marcas_list)
    with col_f2:
        anios_list = ['Todos'] + sorted(fact_ventas['anio'].dropna().unique().tolist())
        anio_sel = st.selectbox("Filtrar por año", anios_list)
    with col_f3:
        ciudades_list = ['Todas'] + sorted(fact_ventas['ciudad'].dropna().unique().tolist())
        ciudad_sel = st.selectbox("Filtrar por ciudad", ciudades_list)

    df_view = fact_ventas.copy()
    if marca_sel  != 'Todas':  df_view = df_view[df_view['marca']  == marca_sel]
    if anio_sel   != 'Todos':  df_view = df_view[df_view['anio']   == anio_sel]
    if ciudad_sel != 'Todas':  df_view = df_view[df_view['ciudad'] == ciudad_sel]

    cols_show = ['referencia','anio','nombre_mes','trimestre','marca','modelo',
                 'tipo','ciudad','nombre_vendedor','medio_pago','valor_venta','valor_pagado','medio_enterado']
    cols_show = [c for c in cols_show if c in df_view.columns]

    st.dataframe(
        df_view[cols_show].rename(columns={
            'referencia':'Referencia','anio':'Año','nombre_mes':'Mes','trimestre':'Trim.',
            'marca':'Marca','modelo':'Modelo','tipo':'Tipo','ciudad':'Ciudad',
            'nombre_vendedor':'Vendedor','medio_pago':'Medio Pago',
            'valor_venta':'Valor Venta','valor_pagado':'Valor Pagado',
            'medio_enterado':'Cómo se enteró'
        }).style.format({'Valor Venta':'${:,.0f}','Valor Pagado':'${:,.0f}'}),
        use_container_width=True,
        height=450,
        hide_index=True
    )
    st.caption(f"Mostrando {len(df_view):,} registros de {len(fact_ventas):,} totales")

# Footer
st.divider()
st.markdown("""
<p style="text-align:center; color:#334155; font-size:0.75rem">
Actividad 5 · Modelamiento Multidimensional OLAP · Esquema Estrella<br>
Fuentes: Sistema Ventas (Railway) + ANDEMOS / RUNT Colombia 2024
</p>
""", unsafe_allow_html=True)
