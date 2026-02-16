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

# Logic to ensure the index starts at 0%
if 'program_memory' not in st.session_state:
    if not df.empty:
        st.session_state.program_memory = {p: {row['Criterion']: 0 for _, row in df.iterrows()} for p in program_options}
    else:
        st.session_state.program_memory = {p: {} for p in program_options}

if 'building_dims' not in st.session_state:
    st.session_state.building_dims = {"sft": 100000, "stories": 5}

# -- 3. PAGE CONFIG & DYNAMIC UI STYLING --
st.set_page_config(page_title="Gensler | Adaptavolve", layout="wide")

# CSS using dynamic variables to support both Light and Dark modes
st.markdown("""
    <style>
    /* 1. Targets Sidebar Headers and Labels using Dynamic Theme Variables */
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] label p {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: var(--text-color) !important; /* Dynamic color fix */
        opacity: 1 !important;
        margin-bottom: 10px !important;
    }

    /* 2. Fixes the '?' Tooltip icon color */
    [data-testid="stSidebar"] .stTooltipIcon {
        color: var(--text-color) !important;
    }

    /* 3. Gensler Branding (Main Title) */
    h1 {
        color: #E03C31; /* Gensler Red */
        font-weight: 800;
    }
    
    /* 4. Desktop App Button Styling */
    .stButton>button { 
        width: 100%; 
        border-radius: 5px; 
        height: 3em; 
        background-color: #E03C31; 
        color: white; 
        border: none; 
    }
    .stButton>button:hover { background-color: #c0342a; color: white; }
    </style>
    """, unsafe_allow_html=True)

# UPDATED BRANDING
st.title("Gensler Adaptable Building Chassis | Adaptavolve")

if not df.empty:
    # -- 4. SIDEBAR: BUILDING SCALE --
    st.sidebar.header("Building Scale") 
    
    with st.sidebar.form("input_form"):
        sft_input = st.number_input("Total SFT", value=st.session_state.building_dims["sft"], step=5000)
        stories_input = st.slider("Number of Stories", 1, 50, value=st.session_state.building_dims["stories"])
        st.markdown("---")
        uploaded_sketch = st.file_uploader("Upload Sketch", type=["png", "jpg", "jpeg"])
        user_refinement = st.text_area("Prompt", placeholder="e.g., Add biophilic walls and modular pods...")
        
        # Friendly "Apply" button
        submitted = st.form_submit_button("➡️ Apply")
        
        if submitted:
            st.session_state.building_dims["sft"] = sft_input
            st.session_state.building_dims["stories"] = stories_input
            st.success("Applied!")

    st.sidebar.markdown("---")
    target_program = st.sidebar.selectbox("Target Typology", program_options)
    
    # CRITERIA WITH HELP TOOLTIPS (COLLAPSED BY DEFAULT)
    for cat in df['Category'].unique():
        with st.sidebar.expander(f"📍 {cat}", expanded=False):
            cat_group = df[df['Category'] == cat]
            for _, row in cat_group.iterrows():
                key = f"{target_program}_{row['Criterion']}"
                # help= provides the hover "?" icons with the Scoring Notes from the Sheet
                st.session_state.program_memory[target_program][row['Criterion']] = st.slider(
                    row['Criterion'], 0, 5, 
                    value=st.session_state.program_memory[target_program][row['Criterion']], 
                    key=key,
                    help=str(row['Scoring Notes (0-5)'])
                )

    # -- 5. MATH ENGINE --
    comparison_data = [{"Typology": p, "Compatibility": (pd.Series(df['Criterion'].map(st.session_state.program_memory[p])).fillna(0) / 5 * df[f"{p} Weight"]).sum()} for p in program_options]
    comp_df = pd.DataFrame(comparison_data).sort_values("Compatibility", ascending=False)

    # -- 6. LAYOUT TABS --
    tab1, tab2, tab3 = st.tabs(["📊 Performance Dashboard", "📐 Plan Generator", "✨ AI Interior Render"])

    with tab1:
        st.metric(f"{target_program} Index", f"{comp_df[comp_df['Typology']==target_program]['Compatibility'].values[0]:.1f}%")
        
        # Responsive columns for Desktop/Mobile window resizing
        col1, col2 = st.columns([1, 1], gap="large")
        
        with col1:
            # Radar chart for Typology DNA
            fig_radar = go.Figure(data=go.Scatterpolar(
                r=list(st.session_state.program_memory[target_program].values()), 
                theta=list(st.session_state.program_memory[target_program].keys()), 
                fill='toself', 
                line_color=color_map[target_program]
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 5])), 
                margin=dict(l=40, r=40, t=40, b=40),
                paper_bgcolor='rgba(0,0,0,0)', # Transparent background
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="gray")
            )
            st.plotly_chart(fig_radar, use_container_width=True)
            
        with col2:
            # Bar chart for Comparison
            fig_comp = px.bar(comp_df, x='Typology', y='Compatibility', color='Typology', color_discrete_map=color_map, text_auto='.1f', range_y=[0, 110])
            fig_comp.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_comp, use_container_width=True)

    with tab2:
        st.header("📐 Generative Floor Plate")
        footprint = st.session_state.building_dims["sft"] / st.session_state.building_dims["stories"]
        side_dim = int(np.sqrt(footprint))
        
        fig, ax = plt.subplots(figsize=(5,5))
        ax.set_facecolor('#f4f7f6')
        ax.add_patch(plt.Rectangle((0,0), side_dim, side_dim, color=color_map[target_program], alpha=0.2))
        core_size = max(20, side_dim * 0.15)
        ax.add_patch(plt.Rectangle((side_dim/2 - core_size/2, side_dim/2 - core_size/2), core_size, core_size, color='black'))
        ax.set_xlim(-10, side_dim + 10); ax.set_ylim(-10, side_dim + 10); ax.set_aspect('equal')
        st.pyplot(fig)

    with tab3:
        st.header("✨ AI Interior Rendering")
        ff_height = st.session_state.program_memory[target_program].get("Floor-to-floor height", 0)
        height_desc = "soaring triple-height volume" if ff_height > 4 else "spacious open-plan"
        
        base_prompt = f"Hyper-realistic interior 3D rendering of a {target_program} with {height_desc}. Exposed structural waffle ceiling. "
        
        if user_refinement:
            final_prompt = f"{base_prompt} Details: {user_refinement}. Cinematic lighting, 8k resolution."
        else:
            final_prompt = f"{base_prompt} Floor-to-ceiling glass, minimalist modern aesthetic, 8k resolution."
        
        st.info(f"**Current Prompt:** {final_prompt}")
        
        if st.button("🚀 Generate High-Fidelity Interior"):
            with st.spinner("Processing architectural data..."):
                st.success("Rendering Complete!")
                st.image("https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?auto=format&fit=crop&q=80&w=1000")
else:
    st.error("Connection Error: Check Google Sheet URL.")
