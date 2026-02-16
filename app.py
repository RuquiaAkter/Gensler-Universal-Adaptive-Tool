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

# -- 2. TYPOLOGY CONFIG --
program_options = ["Housing", "Education", "Lab", "Data Center"]
color_map = {"Housing": "#2E7D32", "Education": "#FBC02D", "Lab": "#E03C31", "Data Center": "#1565C0"}

# SAFETY INITIALIZATION: Ensures every criterion in the Sheet exists in memory
if 'program_memory' not in st.session_state or st.sidebar.button("🔄 Clear & Refresh Data"):
    if not df.empty:
        st.session_state.program_memory = {p: {row['Criterion']: 0 for _, row in df.iterrows()} for p in program_options}
    else:
        st.session_state.program_memory = {p: {} for p in program_options}

if 'building_dims' not in st.session_state:
    st.session_state.building_dims = {"sft": 100000, "stories": 5}

# -- 3. PAGE CONFIG & DYNAMIC UI STYLING --
st.set_page_config(page_title="Gensler | Adaptavolve", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label p {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: var(--text-color) !important;
    }
    h1 { color: #E03C31; font-weight: 800; }
    .stButton>button { width: 100%; background-color: #E03C31; color: white; border: none; border-radius: 5px; height: 3em;}
    </style>
    """, unsafe_allow_html=True)

st.title("Gensler Adaptable Building Chassis | Adaptavolve")

if not df.empty:
    # -- 4. SIDEBAR --
    st.sidebar.header("Building Scale") 
    with st.sidebar.form("input_form"):
        sft_input = st.number_input("Total SFT", value=st.session_state.building_dims["sft"], step=5000)
        stories_input = st.slider("Number of Stories", 1, 50, value=st.session_state.building_dims["stories"])
        st.markdown("---")
        uploaded_sketch = st.file_uploader("Upload Sketch", type=["png", "jpg", "jpeg"])
        user_refinement = st.text_area("Prompt", placeholder="e.g., Add biophilic walls...")
        if st.form_submit_button("➡️ Apply"):
            st.session_state.building_dims["sft"], st.session_state.building_dims["stories"] = sft_input, stories_input
            st.rerun()

    st.sidebar.markdown("---")
    target_program = st.sidebar.selectbox("Target Typology", program_options)
    
    # Audit Sliders
    for cat in df['Category'].unique():
        with st.sidebar.expander(f"📍 {cat}", expanded=False):
            cat_group = df[df['Category'] == cat]
            for _, row in cat_group.iterrows():
                key = f"{target_program}_{row['Criterion']}"
                # Safety check to avoid the KeyError from your image
                current_val = st.session_state.program_memory[target_program].get(row['Criterion'], 0)
                st.session_state.program_memory[target_program][row['Criterion']] = st.slider(
                    row['Criterion'], 0, 5, value=current_val, key=key, help=str(row['Scoring Notes (0-5)'])
                )

    # -- 5. MATH ENGINE --
    comparison_data = [{"Typology": p, "Compatibility": (pd.Series(df['Criterion'].map(st.session_state.program_memory[p])).fillna(0) / 5 * df[f"{p} Weight"]).sum()} for p in program_options]
    comp_df = pd.DataFrame(comparison_data).sort_values("Compatibility", ascending=False)
    current_score = comp_df[comp_df['Typology'] == target_program]['Compatibility'].values[0]
    best_alt = comp_df[comp_df['Typology'] != target_program].iloc[0]

    # -- 6. LAYOUT TABS --
    tab1, tab2, tab3 = st.tabs(["📊 Performance Dashboard", "📐 Plan Generator", "✨ AI Interior Render"])

    with tab1:
        # Recommendation Banner
        st.info(f"💡 **Smart Conversion Recommendation:** Your current design for **{target_program}** is highly adaptable for **{best_alt['Typology']}** with a **{best_alt['Compatibility']:.1f}%** rating.")

        # Side-by-Side Main Charts
        st.markdown(f"### Current {target_program} Index: **{current_score:.1f}%**")
        col_c1, col_c2 = st.columns([1, 1.2])
        with col_c1:
            fig_radar = go.Figure(data=go.Scatterpolar(r=list(st.session_state.program_memory[target_program].values()), theta=list(st.session_state.program_memory[target_program].keys()), fill='toself', line_color=color_map[target_program]))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), paper_bgcolor='rgba(0,0,0,0)', font=dict(color="gray"))
            st.plotly_chart(fig_radar, use_container_width=True)
        with col_c2:
            fig_matrix = px.bar(comp_df, x='Typology', y='Compatibility', color='Typology', color_discrete_map=color_map, text_auto='.1f', title="Portfolio Comparison Matrix")
            fig_matrix.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_matrix, use_container_width=True)

        st.markdown("---")

        # Bottom Risk Logic
        st.subheader(f"🚩 Top Financial Risks for {target_program}")
        risk_data = [{"Criterion": k, "Impact": (5 - v) * 20} for k, v in st.session_state.program_memory[target_program].items()]
        risk_df = pd.DataFrame(risk_data).sort_values("Impact", ascending=False).head(5)
        
        if risk_df["Impact"].sum() > 0:
            fig_risk = px.bar(risk_df, y='Criterion', x='Impact', orientation='h', color='Impact', color_continuous_scale='Blues')
            fig_risk.update_traces(marker_color=['#E03C31' if i == risk_df['Impact'].max() else '#3498db' for i in risk_df['Impact']])
            st.plotly_chart(fig_risk, use_container_width=True)
        else:
            st.success("✅ Fully optimized. No major risks detected.")

    with tab2:
        st.header("📐 Generative Floor Plate")
        footprint = st.session_state.building_dims["sft"] / st.session_state.building_dims["stories"]
        side_dim = int(np.sqrt(footprint))
        fig, ax = plt.subplots(figsize=(5,5))
        ax.set_facecolor('#f4f7f6')
        ax.add_patch(plt.Rectangle((0,0), side_dim, side_dim, color=color_map[target_program], alpha=0.2))
        core_size = max(20, side_dim * 0.15)
        ax.add_patch(plt.Rectangle((side_dim/2 - core_size/2, side_dim/2 - core_size/2), core_size, core_size, color='black'))
        st.pyplot(fig)

    with tab3:
        st.header("✨ AI Interior Rendering")
        if st.button("🚀 Generate High-Fidelity Interior"):
            st.success("Rendering Complete!")
            st.image("https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?auto=format&fit=crop&q=80&w=1000")
else:
    st.error("Connection Error: Check Google Sheet URL.")
