import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np

# -- 1. LIVE DATA CONNECTION --
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS1UOhKUDHJP2tWaAOL0E9M72g3coDNY5HI_3d6DA37Gf4lznsxWBl9WyY25-tDhrTivb76BrZwdqKI/pub?output=csv"

@st.cache_data(ttl=10)
def load_live_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

df = load_live_data()

# -- 2. TYPOLOGY CONFIG & COLORS --
program_options = ["Housing", "Education", "Lab", "Data Center"]
color_map = {
    "Housing": "#2E7D32", "Education": "#FBC02D",
    "Lab": "#E03C31", "Data Center": "#1565C0"
}

# -- 3. INITIALIZE SESSION STATE --
if 'program_memory' not in st.session_state:
    if not df.empty:
        st.session_state.program_memory = {p: {row['Criterion']: 3 for _, row in df.iterrows()} for p in program_options}
    else:
        st.session_state.program_memory = {p: {} for p in program_options}

# New Physical State Memory
if 'building_dims' not in st.session_state:
    st.session_state.building_dims = {"sft": 50000, "stories": 5}

# -- 4. PAGE CONFIG --
st.set_page_config(page_title="Alchemy Chassis | Universal Tool", layout="wide")
st.markdown(f"""
    <style>
    .main {{ background-color: #f4f7f6; }}
    .stMetric {{ background-color: #ffffff; padding: 15px; border-radius: 12px; border-top: 6px solid #333333; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    .recommendation-card {{ background-color: #ffffff; padding: 25px; border-radius: 12px; border-left: 10px solid #E03C31; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
    </style>
    """, unsafe_allow_html=True)

st.title("🏗️ Alchemy Chassis: Universal Building Tool")

if not df.empty:
    tab1, tab2, tab3 = st.tabs(["📊 Performance Dashboard", "📐 Plan & Massing", "✨ AI Renderings"])

    with tab1:
        # -- 5. SIDEBAR: PROJECT SETTINGS --
        st.sidebar.header("🏢 Global Building Specs")
        st.session_state.building_dims["sft"] = st.sidebar.number_input("Total GFA (SFT)", min_value=5000, max_value=1000000, value=st.session_state.building_dims["sft"], step=5000)
        st.session_state.building_dims["stories"] = st.sidebar.slider("Number of Stories", 1, 50, st.session_state.building_dims["stories"])
        
        target_program = st.selectbox("🎯 Target Typology", program_options)

        # Audit Sliders
        st.sidebar.markdown("---")
        st.sidebar.header(f"🛠️ {target_program} Specs")
        for cat in df['Category'].unique():
            with st.sidebar.expander(f"📍 {cat}"):
                cat_group = df[df['Category'] == cat]
                for _, row in cat_group.iterrows():
                    key = f"{target_program}_{row['Criterion']}"
                    st.session_state.program_memory[target_program][row['Criterion']] = st.sidebar.slider(
                        row['Criterion'], 0, 5, value=st.session_state.program_memory[target_program][row['Criterion']], key=key
                    )

        # Dashboard Math
        comparison_data = []
        for p in program_options:
            w_col = f"{p} Weight"
            p_scores = pd.Series(df['Criterion'].map(st.session_state.program_memory[p])).fillna(3)
            p_total_pct = (p_scores / 5 * df[w_col]).sum()
            comparison_data.append({"Typology": p, "Compatibility": p_total_pct})
        
        comp_df = pd.DataFrame(comparison_data).sort_values("Compatibility", ascending=False)
        best_alt = comp_df[comp_df['Typology'] != target_program].iloc[0]

        # Layout
        c1, c2 = st.columns(2)
        with c1:
            st.metric(f"{target_program} Score", f"{comp_df[comp_df['Typology']==target_program]['Compatibility'].values[0]:.1f}%")
            fig_radar = go.Figure(data=go.Scatterpolar(
                r=list(st.session_state.program_memory[target_program].values()),
                theta=list(st.session_state.program_memory[target_program].keys()), fill='toself', line_color=color_map[target_program]
            ))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), title=f"Signature: {target_program}")
            st.plotly_chart(fig_radar, use_container_width=True)
        with c2:
            st.write("### Portfolio Comparison")
            fig_comp = px.bar(comp_df, x='Typology', y='Compatibility', color='Typology', color_discrete_map=color_map, text_auto='.1f')
            st.plotly_chart(fig_comp, use_container_width=True)
            
        st.markdown(f"""<div class="recommendation-card" style="border-left-color: {color_map[best_alt['Typology']]}">
            <h3>💡 Pivot Strategy: {best_alt['Typology']}</h3>
            <p>Your {st.session_state.building_dims['stories']}-story chassis is most compatible with <b>{best_alt['Typology']}</b> ({best_alt['Compatibility']:.1f}%).</p>
            </div>""", unsafe_allow_html=True)

    with tab2:
        st.header("📐 Generative Plan & Massing")
        # Calculate Footprint
        footprint = st.session_state.building_dims["sft"] / st.session_state.building_dims["stories"]
        side_dim = int(np.sqrt(footprint))
        
        col_m1, col_m2 = st.columns([1, 2])
        with col_m1:
            st.subheader("Massing Data")
            st.write(f"**Footprint:** {footprint:,.0f} SFT")
            st.write(f"**Floor Plate:** {side_dim}' x {side_dim}'")
            st.write(f"**Building Height:** {st.session_state.building_dims['stories'] * 15}' (est.)")
            
        with col_m2:
            # Procedural Plan Grid
            fig, ax = plt.subplots(figsize=(6,6))
            ax.set_facecolor('#f4f7f6')
            # Draw Column Grid based on footprint
            grid_res = 30 # standard 30ft grid
            for x in range(0, side_dim, grid_res):
                ax.axvline(x, color='gray', lw=0.5, alpha=0.5)
            for y in range(0, side_dim, grid_res):
                ax.axhline(y, color='gray', lw=0.5, alpha=0.5)
            
            # Draw Core
            ax.add_patch(plt.Rectangle((side_dim/2.5, side_dim/2.5), side_dim/5, side_dim/5, facecolor='black', alpha=0.7))
            ax.text(side_dim/2, side_dim/2, "CORE", color='white', ha='center', va='center', weight='bold')
            
            ax.set_xlim(0, side_dim); ax.set_ylim(0, side_dim)
            ax.set_title(f"Generated Floor Plate: {target_program}")
            st.pyplot(fig)

    with tab3:
        st.header("✨ AI Architectural Vision")
        # Build prompt using SFT and Story count
        story_type = "High-rise" if st.session_state.building_dims["stories"] > 12 else "Mid-rise"
        prompt = f"Exterior architectural rendering of a {st.session_state.building_dims['sft']:,} SFT {story_type} {target_program} building..."
        st.info(f"AI Prompt: {prompt}")
        if st.button("Generate Render"):
            st.image("https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=1000&auto=format&fit=crop")

else:
    st.warning("Connect Google Sheet to enable tool.")
