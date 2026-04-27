import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import re

st.set_page_config(
    page_title="🚀 Emprendedores de Éxito",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.4rem; font-weight: 800; color: #1a1a2e;
        margin-bottom: 0.2rem;
    }
    .sub-header { color: #666; font-size: 1rem; margin-bottom: 2rem; }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px; padding: 1.2rem; color: white;
        text-align: center; margin-bottom: 1rem;
    }
    .metric-card .value { font-size: 2rem; font-weight: 800; }
    .metric-card .label { font-size: 0.85rem; opacity: 0.85; margin-top: 0.2rem; }
    .insight-box {
        background: #f0f4ff; border-left: 4px solid #667eea;
        border-radius: 8px; padding: 1rem; margin: 0.5rem 0;
        font-size: 0.93rem;
    }
    .founder-card {
        background: white; border: 1px solid #e5e7eb;
        border-radius: 12px; padding: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .tag {
        display: inline-block; padding: 2px 10px;
        border-radius: 20px; font-size: 0.78rem; font-weight: 600;
        margin: 2px;
    }
    .tag-blue { background: #dbeafe; color: #1d4ed8; }
    .tag-green { background: #dcfce7; color: #15803d; }
    .tag-orange { background: #ffedd5; color: #c2410c; }
    .tag-purple { background: #f3e8ff; color: #7c3aed; }
</style>
""", unsafe_allow_html=True)

# ── Load & clean data ────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_excel("FOUNDERS_COMPLETED.xlsx")
    # Parse "Tiempo hasta éxito" → numeric (acepta "X", "X años", "X.5 años", "X,5")
    tiempo_raw = df["Tiempo hasta éxito"].astype(str).str.strip()
    tiempo_num = tiempo_raw.str.extract(r"(\d+(?:[\.,]\d+)?)", expand=False)
    df["Años al éxito"] = pd.to_numeric(tiempo_num.str.replace(",", ".", regex=False), errors="coerce")
    # Expand multi-country rows
    df["Países"] = df["País"].str.split(r"\s*/\s*")
    # Normalise "Mercado" to clean category
    df["Tipo mercado"] = df["Inicios Competitivos"].apply(
        lambda x: "Pionero" if "Pionero" in str(x) else "Competencia"
    )
    # Extract competitor name
    df["Competidor"] = df["Inicios Competitivos"].str.extract(r"\((.+?)\)")
    return df

df = load_data()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://em-content.zobj.net/source/animated-noto-color-emoji/356/rocket_1f680.gif", width=60)
    st.markdown("### Filtros globales")

    edad_range = st.slider(
        "Edad de inicio", int(df["Edad inicio"].min()), int(df["Edad inicio"].max()),
        (int(df["Edad inicio"].min()), int(df["Edad inicio"].max()))
    )
    años_range = st.slider(
        "Años hasta el éxito", int(df["Años al éxito"].min()), int(df["Años al éxito"].max()),
        (int(df["Años al éxito"].min()), int(df["Años al éxito"].max()))
    )
    tipo_mercado = st.multiselect(
        "Tipo de mercado", df["Tipo mercado"].unique().tolist(),
        default=df["Tipo mercado"].unique().tolist()
    )
    paises_opt = sorted(set(p.strip() for pl in df["Países"] for p in pl))
    paises_sel = st.multiselect("País", paises_opt, default=paises_opt)

    st.markdown("---")
    st.markdown("**Buscar por experiencia**")
    exp_keyword = st.text_input("Palabra clave (ej: Finanzas, Oracle…)", "")

# ── Filter ───────────────────────────────────────────────────────────────────
mask = (
    (df["Edad inicio"] >= edad_range[0]) & (df["Edad inicio"] <= edad_range[1]) &
    (df["Años al éxito"] >= años_range[0]) & (df["Años al éxito"] <= años_range[1]) &
    (df["Tipo mercado"].isin(tipo_mercado)) &
    (df["Países"].apply(lambda pl: any(p.strip() in paises_sel for p in pl)))
)
if exp_keyword:
    mask &= df["Experiencia previa"].str.contains(exp_keyword, case=False, na=False)
dff = df[mask].copy()

# ═══════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "🏠 Resumen", "👤 Perfil fundador", "⏱️ Tiempo al éxito",
    "🌍 Geografía", "🔬 Patrones y clusters", "🔎 Explorar fundadores"
])

# ────────────────────────────────────────────────────────────────────────────
# TAB 0: RESUMEN
# ────────────────────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown('<p class="main-header">🚀 Emprendedores de Éxito — Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Explora patrones y conclusiones sobre los fundadores más exitosos del mundo</p>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    metrics = [
        (len(dff), "Fundadores analizados"),
        (f"{dff['Edad inicio'].mean():.1f}", "Edad media de inicio"),
        (f"{dff['Años al éxito'].mean():.1f}", "Años medios al éxito"),
        (f"{(dff['Tipo mercado']=='Pionero').mean()*100:.0f}%", "Crearon nuevo mercado"),
        (f"{dff['Nº intentos previos'].mean():.1f}", "Intentos previos promedio"),
    ]
    for col, (val, label) in zip([c1, c2, c3, c4, c5], metrics):
        col.markdown(f"""
        <div class="metric-card">
            <div class="value">{val}</div>
            <div class="label">{label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("📊 Distribución de edad de inicio")
        fig = px.histogram(dff, x="Edad inicio", nbins=10, color_discrete_sequence=["#667eea"],
                           labels={"Edad inicio": "Edad al fundar"})
        fig.add_vline(x=dff["Edad inicio"].mean(), line_dash="dash", line_color="#e74c3c",
                      annotation_text=f"Media: {dff['Edad inicio'].mean():.1f}")
        fig.update_layout(showlegend=False, height=320, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("🏆 Años hasta el éxito por empresa")
        dff_sorted = dff.sort_values("Años al éxito")
        fig = px.bar(dff_sorted, x="Empresa", y="Años al éxito", color="Tipo mercado",
                     color_discrete_map={"Pionero": "#667eea", "Competencia": "#f97316"},
                     labels={"Años al éxito": "Años"})
        fig.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("💡 Insights clave")
    insights = [
        f"📌 La edad media de inicio es <b>{dff['Edad inicio'].mean():.1f} años</b> — ni muy joven ni muy mayor.",
        f"⚡ Los fundadores <b>pioneros</b> tardan en promedio <b>{dff[dff['Tipo mercado']=='Pionero']['Años al éxito'].mean():.1f} años</b> vs <b>{dff[dff['Tipo mercado']=='Competencia']['Años al éxito'].mean():.1f} años</b> los que compiten en mercados existentes.",
        f"🔁 La media de intentos previos es <b>{dff['Nº intentos previos'].mean():.1f}</b>. El {(dff['Nº intentos previos']==1).mean()*100:.0f}% lo consiguió al primer intento.",
        "🌍 La mayoría son de EE.UU., pero hay éxitos relevantes en Europa (Spotify, Personio, Shopify).",
        "💻 La experiencia técnica (programación) domina, pero hay perfiles muy diversos (finanzas, ventas, diseño).",
    ]
    for ins in insights:
        st.markdown(f'<div class="insight-box">{ins}</div>', unsafe_allow_html=True)


# ────────────────────────────────────────────────────────────────────────────
# TAB 1: PERFIL FUNDADOR
# ────────────────────────────────────────────────────────────────────────────
with tabs[1]:
    st.header("👤 Perfil del fundador")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎂 Edad de inicio — boxplot")
        fig = px.box(dff, y="Edad inicio", x="Tipo mercado", color="Tipo mercado",
                     color_discrete_map={"Pionero": "#667eea", "Competencia": "#f97316"},
                     points="all", hover_data=["Empresa", "Fundador"])
        fig.update_layout(height=380, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # Stats
        for tipo in dff["Tipo mercado"].unique():
            sub = dff[dff["Tipo mercado"] == tipo]["Edad inicio"]
            st.markdown(f'<div class="insight-box"><b>{tipo}</b>: media {sub.mean():.1f} · mediana {sub.median():.0f} · min {sub.min()} · max {sub.max()}</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("🧠 Experiencia previa — categorías")
        # Keyword-based grouping
        cats = {
            "Programador/Ingeniero": ["programador", "ingeniero", "software", "técnico"],
            "Finanzas/Banca": ["finanzas", "wall street", "banco", "financiero"],
            "Ventas/Marketing": ["ventas", "marketing", "oracle", "comercial"],
            "Consultoría": ["consultoría", "hbs", "mckinsey", "consultor"],
            "Diseño/Creativo": ["diseño", "diseñador", "música", "creativo"],
            "Otros/Mixto": []
        }
        def cat_exp(exp):
            exp_low = str(exp).lower()
            for cat, kws in cats.items():
                if kws and any(k in exp_low for k in kws):
                    return cat
            return "Otros/Mixto"
        dff["Cat experiencia"] = dff["Experiencia previa"].apply(cat_exp)

        exp_counts = dff["Cat experiencia"].value_counts().reset_index()
        exp_counts.columns = ["Categoría", "Count"]
        fig = px.pie(exp_counts, names="Categoría", values="Count",
                     color_discrete_sequence=px.colors.qualitative.Pastel, hole=0.4)
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📈 Edad vs Años al éxito")
    fig = px.scatter(dff, x="Edad inicio", y="Años al éxito",
                     color="Tipo mercado", size="Nº intentos previos",
                     hover_data=["Empresa", "Fundador", "Experiencia previa"],
                     color_discrete_map={"Pionero": "#667eea", "Competencia": "#f97316"},
                     trendline="ols", labels={"Edad inicio": "Edad al fundar", "Años al éxito": "Años hasta el éxito"})
    fig.update_layout(height=420)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🔁 Nº de intentos previos")
    col3, col4 = st.columns(2)
    with col3:
        intento_counts = dff["Nº intentos previos"].value_counts().sort_index().reset_index()
        intento_counts.columns = ["Intentos", "Count"]
        fig = px.bar(intento_counts, x="Intentos", y="Count",
                     color_discrete_sequence=["#667eea"],
                     labels={"Count": "Nº fundadores", "Intentos": "Intentos previos"})
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    with col4:
        # Intentos vs años al éxito
        fig = px.box(dff, x="Nº intentos previos", y="Años al éxito",
                     color_discrete_sequence=["#764ba2"],
                     labels={"Nº intentos previos": "Intentos", "Años al éxito": "Años al éxito"})
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<div class="insight-box">¿Más intentos = más rápido al éxito? Compruébalo aquí.</div>', unsafe_allow_html=True)


# ────────────────────────────────────────────────────────────────────────────
# TAB 2: TIEMPO AL ÉXITO
# ────────────────────────────────────────────────────────────────────────────
with tabs[2]:
    st.header("⏱️ Tiempo al éxito — análisis profundo")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Mercado Pionero vs Competencia")
        fig = px.violin(dff, y="Años al éxito", x="Tipo mercado", color="Tipo mercado",
                        box=True, points="all", hover_data=["Empresa"],
                        color_discrete_map={"Pionero": "#667eea", "Competencia": "#f97316"})
        fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Por categoría de experiencia previa")
        dff_temp = dff.copy()
        cats = {
            "Programador/Ingeniero": ["programador", "ingeniero", "software"],
            "Finanzas/Banca": ["finanzas", "wall street", "banco"],
            "Ventas/Marketing": ["ventas", "marketing", "oracle"],
            "Consultoría": ["consultoría", "hbs"],
            "Diseño/Creativo": ["diseño", "música"],
        }
        def cat_exp2(exp):
            exp_low = str(exp).lower()
            for cat, kws in cats.items():
                if any(k in exp_low for k in kws):
                    return cat
            return "Otros/Mixto"
        dff_temp["Cat exp"] = dff_temp["Experiencia previa"].apply(cat_exp2)
        exp_exito = dff_temp.groupby("Cat exp")["Años al éxito"].agg(["mean", "min", "count"]).reset_index()
        exp_exito.columns = ["Experiencia", "Media años", "Mín años", "N"]
        exp_exito = exp_exito.sort_values("Media años")
        fig = px.bar(exp_exito, x="Media años", y="Experiencia", orientation="h",
                     color="Media años", color_continuous_scale="RdYlGn_r",
                     hover_data=["N", "Mín años"],
                     labels={"Media años": "Años promedio al éxito"})
        fig.update_layout(height=380, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("🔗 Correlación: Edad inicio → Años al éxito")
    corr = dff[["Edad inicio", "Años al éxito", "Nº intentos previos"]].corr()
    fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r",
                    zmin=-1, zmax=1, aspect="auto")
    fig.update_layout(height=320)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("⏩ Los más rápidos al éxito (≤ 3 años)")
    rapidos = dff[dff["Años al éxito"] <= 3].sort_values("Años al éxito")[
        ["Empresa", "Fundador", "Edad inicio", "Experiencia previa", "Ventaja inicial", "Tipo mercado", "País"]
    ]
    st.dataframe(rapidos, use_container_width=True, hide_index=True)

    if not rapidos.empty:
        st.markdown('<div class="insight-box">🏎️ <b>Patrón en los más rápidos:</b> Tendencia a tener ventaja inicial clara (red, contrato o producto propio), y a menudo son fundadores con experiencia técnica directa en el problema que resuelven.</div>', unsafe_allow_html=True)


# ────────────────────────────────────────────────────────────────────────────
# TAB 3: GEOGRAFÍA
# ────────────────────────────────────────────────────────────────────────────
with tabs[3]:
    st.header("🌍 Análisis geográfico")

    # Explode multi-country
    df_geo = dff.explode("Países").copy()
    df_geo["Países"] = df_geo["Países"].str.strip()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Fundadores por país")
        geo_counts = df_geo["Países"].value_counts().reset_index()
        geo_counts.columns = ["País", "Count"]
        fig = px.bar(geo_counts, x="País", y="Count",
                     color="Count", color_continuous_scale="Viridis",
                     labels={"Count": "Nº fundadores"})
        fig.update_layout(showlegend=False, height=360, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Años al éxito por país")
        geo_exito = df_geo.groupby("Países")["Años al éxito"].mean().reset_index()
        geo_exito.columns = ["País", "Media años"]
        geo_exito = geo_exito.sort_values("Media años")
        fig = px.bar(geo_exito, x="País", y="Media años",
                     color="Media años", color_continuous_scale="RdYlGn_r",
                     labels={"Media años": "Promedio años al éxito"})
        fig.update_layout(height=360, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Tipo de mercado por país")
    geo_tipo = df_geo.groupby(["Países", "Tipo mercado"]).size().reset_index(name="Count")
    fig = px.bar(geo_tipo, x="Países", y="Count", color="Tipo mercado",
                 barmode="group",
                 color_discrete_map={"Pionero": "#667eea", "Competencia": "#f97316"})
    fig.update_layout(height=340)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Fundadores con doble país (multi-nacionales)")
    multi = dff[dff["País"].str.contains("/", na=False)][["Empresa", "Fundador", "País", "Años al éxito", "Tipo mercado"]]
    if not multi.empty:
        st.dataframe(multi, use_container_width=True, hide_index=True)
        st.markdown('<div class="insight-box">🌐 Los fundadores con doble nacionalidad o raíces en dos países suelen tener ventaja de red y perspectiva global para escalar antes.</div>', unsafe_allow_html=True)


# ────────────────────────────────────────────────────────────────────────────
# TAB 4: PATRONES Y CLUSTERS
# ────────────────────────────────────────────────────────────────────────────
with tabs[4]:
    st.header("🔬 Patrones, clusters y conclusiones")

    st.subheader("🌡️ Mapa de calor: variables numéricas")
    dff_num = dff[["Edad inicio", "Nº intentos previos", "Años al éxito"]].copy()
    corr = dff_num.corr()
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                    zmin=-1, zmax=1, aspect="auto",
                    labels=dict(color="Correlación"))
    fig.update_layout(height=340)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⚔️ Pivot vs No pivot — ¿importa?")
        dff_piv = dff.copy()
        dff_piv["Hizo pivot"] = dff_piv["Pivot"].apply(
            lambda x: "No pivot" if str(x).upper() == "NAN" or pd.isna(x) else "Pivot"
        )
        piv_exito = dff_piv.groupby("Hizo pivot")["Años al éxito"].mean().reset_index()
        fig = px.bar(piv_exito, x="Hizo pivot", y="Años al éxito",
                     color="Hizo pivot", color_discrete_sequence=["#667eea", "#f97316"],
                     labels={"Años al éxito": "Media años al éxito"})
        fig.update_layout(showlegend=False, height=320)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📊 Scatter 3D: Edad · Intentos · Años")
        fig = px.scatter_3d(dff, x="Edad inicio", y="Nº intentos previos", z="Años al éxito",
                            color="Tipo mercado", hover_data=["Empresa", "Fundador"],
                            color_discrete_map={"Pionero": "#667eea", "Competencia": "#f97316"},
                            size_max=12)
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📌 Tabla de conclusiones estadísticas")
    conclusiones = [
        ("Edad óptima de inicio", f"{dff['Edad inicio'].median():.0f} años (mediana)", "Los 20-30 años dominan, con excepciones notables sobre 35"),
        ("Experiencia más común", "Programador / Técnico", "60%+ tienen perfil técnico como base"),
        ("Tiempo promedio al éxito", f"{dff['Años al éxito'].mean():.1f} años", "La mayoría entre 3 y 6 años"),
        ("¿Mejor ser pionero o competir?", f"Pionero={dff[dff['Tipo mercado']=='Pionero']['Años al éxito'].mean():.1f}a / Competencia={dff[dff['Tipo mercado']=='Competencia']['Años al éxito'].mean():.1f}a", "Ser pionero no garantiza más velocidad, pero sí defensibilidad"),
        ("Intentos previos", f"Media {dff['Nº intentos previos'].mean():.1f}", f"{(dff['Nº intentos previos']==1).mean()*100:.0f}% lo consiguió al primer intento"),
        ("Correlación Edad → Años éxito", f"{dff[['Edad inicio','Años al éxito']].corr().iloc[0,1]:.2f}", "Correlación positiva débil — edad no determina velocidad"),
    ]
    df_conc = pd.DataFrame(conclusiones, columns=["Variable", "Valor", "Interpretación"])
    st.dataframe(df_conc, use_container_width=True, hide_index=True)

    st.subheader("🧩 Ventaja inicial más frecuente")
    vent_counts = dff["Ventaja inicial"].value_counts().head(10).reset_index()
    vent_counts.columns = ["Ventaja", "Count"]
    fig = px.treemap(vent_counts, path=["Ventaja"], values="Count",
                     color="Count", color_continuous_scale="Blues")
    fig.update_layout(height=360)
    st.plotly_chart(fig, use_container_width=True)


# ────────────────────────────────────────────────────────────────────────────
# TAB 5: EXPLORAR FUNDADORES
# ────────────────────────────────────────────────────────────────────────────
with tabs[5]:
    st.header("🔎 Explorar fundadores individualmente")

    founder_sel = st.selectbox(
        "Selecciona un fundador",
        dff["Empresa"] + " — " + dff["Fundador"],
        index=0
    )
    empresa_sel = founder_sel.split(" — ")[0]
    row = dff[dff["Empresa"] == empresa_sel].iloc[0]

    col1, col2 = st.columns([1.2, 1.8])
    with col1:
        st.markdown(f"""
        <div class="founder-card">
            <h2 style="margin-bottom:0.2rem">{row['Empresa']}</h2>
            <p style="color:#666; margin-bottom:1rem">Fundador: <b>{row['Fundador']}</b></p>
            <hr style="margin: 0.5rem 0"/>
            <p>🎂 <b>Edad de inicio:</b> {int(row['Edad inicio'])} años</p>
            <p>🧠 <b>Experiencia previa:</b> {row['Experiencia previa']}</p>
            <p>🔁 <b>Intentos previos:</b> {int(row['Nº intentos previos'])}</p>
            <p>🚀 <b>Primer modelo:</b> {row['Primer modelo']}</p>
            <p>↩️ <b>Pivot:</b> {row['Pivot']}</p>
            <p>⏱️ <b>Tiempo hasta éxito:</b> {row['Tiempo hasta éxito']}</p>
            <p>⚡ <b>Ventaja inicial:</b> {row['Ventaja inicial']}</p>
            <p>🌍 <b>País:</b> {row['País']}</p>
            <p>🏷️ <b>Mercado:</b>
                <span class="tag {'tag-blue' if row['Tipo mercado']=='Pionero' else 'tag-orange'}">{row['Tipo mercado']}</span>
            </p>
            <hr style="margin: 0.5rem 0"/>
            <p style="font-size:0.88rem; color:#555"><i>"{row['Notas/Diferenciador']}"</i></p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.subheader("📊 Comparación con la media del dataset")
        categories = ["Edad inicio", "Años al éxito", "Nº intentos previos"]
        means = [dff[c].mean() for c in categories]
        values = [row[c] for c in categories]
        # Normalise for radar
        max_vals = [dff[c].max() for c in categories]
        norm_mean = [m/mx for m, mx in zip(means, max_vals)]
        norm_val = [v/mx for v, mx in zip(values, max_vals)]
        labels = ["Edad inicio", "Años al éxito", "Intentos previos"]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=norm_val + [norm_val[0]], theta=labels + [labels[0]],
                                      fill="toself", name=row["Empresa"],
                                      line_color="#667eea", fillcolor="rgba(102,126,234,0.3)"))
        fig.add_trace(go.Scatterpolar(r=norm_mean + [norm_mean[0]], theta=labels + [labels[0]],
                                      fill="toself", name="Media dataset",
                                      line_color="#f97316", fillcolor="rgba(249,115,22,0.15)"))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                          showlegend=True, height=380)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📍 Posición en el scatter global")
        fig2 = px.scatter(dff, x="Edad inicio", y="Años al éxito",
                          color="Tipo mercado", size="Nº intentos previos",
                          hover_data=["Empresa"],
                          color_discrete_map={"Pionero": "#667eea", "Competencia": "#f97316"},
                          opacity=0.5)
        fig2.add_scatter(x=[row["Edad inicio"]], y=[row["Años al éxito"]],
                         mode="markers+text", text=[row["Empresa"]],
                         textposition="top center",
                         marker=dict(color="#e74c3c", size=16, symbol="star"),
                         name=row["Empresa"], showlegend=True)
        fig2.update_layout(height=320)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("🔁 Fundadores similares")
    # Similarity: same tipo mercado or same exp category
    cat_actual = dff_temp[dff_temp["Empresa"] == empresa_sel]["Cat exp"].values
    similares = dff[
        (dff["Empresa"] != empresa_sel) &
        ((dff["Tipo mercado"] == row["Tipo mercado"]) |
         (abs(dff["Edad inicio"] - row["Edad inicio"]) <= 5))
    ][["Empresa", "Fundador", "Edad inicio", "Experiencia previa", "Años al éxito", "Tipo mercado"]]
    st.dataframe(similares, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📋 Tabla completa filtrada")
    cols_show = ["Empresa", "Fundador", "Edad inicio", "Experiencia previa",
                 "Nº intentos previos", "Años al éxito", "Tipo mercado", "País", "Ventaja inicial"]
    st.dataframe(dff[cols_show], use_container_width=True, hide_index=True)