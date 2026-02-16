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

if 'program_memory' not in st.session_state:
    st.session_state.program_memory = {p: {row['Criterion']: 3 for _, row in df.iterrows()} for p in program_options} if not df.empty else {p: {}}

if 'building_dims' not in st.session_state:
    st.session_state.building_dims = {"sft": 100000, "stories": 5}

# -- 3. PAGE CONFIG & UI STYLING --
st.set_page_config(page_title="Gensler | Adaptavolv", layout="wide")

# CSS to unify fonts, force white color, and style the help tooltips
st.markdown("""
    <style>
    /* Unified Header and Label Styling - White for Dark Mode Clarity */
    .stSidebar h2, .stSidebar label p {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
        opacity: 1 !important;
        margin-bottom: 10px !important;
    }
    /* Style the help icon tooltips specifically */
    .stTooltipIcon {
        color: #FFFFFF !important;
    }
    /* Main Title Styling */
    h1 {
        color: #E03C31; /* Gensler Red */
        font-weight: 800;
    }
    </style>
    """, unsafe_allow_html=True)

# UPDATED BRANDING WITH SPACING
st.title("Gensler Adaptable Chassis | Adaptavolv")

if not df.empty:
    # -- 4. SIDEBAR: BUILDING SCALE --
    st.sidebar.header("Building Scale") 
    
    with st.sidebar.form("input_form"):
        sft_input = st.number_input("Total SFT", value=st.session_state.building_dims["sft"], step=5000)
        stories_input = st.slider("Number of Stories", 1, 50, value=st.session_state.building_dims["stories"])
        
        st.markdown("---")
        uploaded_sketch = st.file_uploader("Upload Sketch", type=["png", "jpg", "jpeg"])
        user_refinement = st.text_area("Prompt", placeholder="e.g., Add biophilic walls and modular pods...")
        
        submitted = st.form_submit_button("➡️ Apply")
        
        if submitted:
            st.session_state.building_dims["sft"] = sft_input
            st.session_state.building_dims["stories"] = stories_input
            st.success("Applied!")

    st.sidebar.markdown("---")
    target_program = st.sidebar.selectbox("Target Typology", program_options)
    
    # CRITERIA WITH HELP TOOLTIPS
    for cat in df['Category'].unique():
        with st.sidebar.expander(f"📍 {cat}", expanded=False):
            cat_group = df[df['Category'] == cat]
            for _, row in cat_group.iterrows():
                key = f"{target_program}_{row['Criterion']}"
                # The 'help' parameter provides the hover "?" icons with the Scoring Notes
                st.session_state.program_memory[target_program][row['Criterion']] = st.slider(
                    row['Criterion'], 0, 5, 
                    value=st.session_state.program_memory[target_program][row['Criterion']], 
                    key=key,
                    help=str(row['Scoring Notes (0-5)'])
                )

    # -- 5. MATH ENGINE --
    comparison_data = [{"Typology": p, "Compatibility": (pd.Series(df['Criterion'].map(st.session_state.program_memory[p])).fillna(3) / 5 * df[f"{p} Weight"]).sum()} for p in program_options]
    comp_df = pd.DataFrame(comparison_data).sort_values("Compatibility", ascending=False)

    # -- 6. LAYOUT TABS --
    tab1, tab2, tab3 = st.tabs(["📊 Performance Dashboard", "📐 Plan Generator", "✨ AI Interior Render"])

    with tab1:
        col1, col2 = st.columns([1, 1.2])
        with col1:
            st.metric(f"{target_program} Index", f"{comp_df[comp_df['Typology']==target_program]['Compatibility'].values[0]:.1f}%")
            fig_radar = go.Figure(data=go.Scatterpolar(r=list(st.session_state.program_memory[target
