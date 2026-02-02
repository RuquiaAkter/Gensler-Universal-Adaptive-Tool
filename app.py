import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

# -- 2. TYPOLOGY-SPECIFIC MEMORY --
program_options = ["Housing", "Education", "Lab", "Data Center"]
# Color mapping for vibrant, distinct graphics
color_map = {
    "Housing": "#FF5733",      # Vibrant Orange
    "Education": "#33FF57",    # Leaf Green
    "Lab": "#E03C31",          # Gensler Red
    "Data Center": "#3357FF"   # Electric Blue
}

if 'program_memory' not in st.session_state:
    st.session_state.program_memory = {p: {row['Criterion']: 3 for _, row in df.iterrows()} for p in program_options}

# -- 3. PAGE CONFIG --
st.set_page_config(page_title="Universal Adaptive Building Tool", layout="wide")
st.markdown(f"""
    <style>
    .main {{ background-color: #f4f7f6; }}
    .stMetric {{ background-color: #ffffff; padding: 20px; border-radius: 12px; border-top: 6px solid {color_map["Lab"]}; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    .recommendation-card {{ background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 8px solid #333333; margin-top: 20px; }}
    </style>
    """, unsafe_allow_html=True)

st.title("🏗️ Universal Adaptive Building Tool")

if not df.empty:
    # -- 4. SELECT TARGET --
    col_top1, col_top2 = st.columns([1, 2])
    with col_top1:
        target_program = st.selectbox("🎯 Select Typology to Edit", program_options)

    # -- 5. SIDEBAR AUDIT --
    st.sidebar.header(f"🛠️ {target_program} Specs")
    for cat in df['Category'].unique():
        with st.sidebar.expander(f"📍 {cat}", expanded=True):
            cat_group = df[df['Category'] == cat]
            for _, row in cat_group.iterrows():
                key_name = f"{target_program}_{row['Criterion']}"
                st.session_state.program_memory[target_program][row['Criterion']] = st.slider(
                    row['Criterion'], 0, 5, 
                    value=st.session_state.program_memory[target_program][row['Criterion']],
                    help=str(row['Scoring Notes (0-5)']),
                    key=key_name
                )

    # -- 6. MATH & CONVERSION ENGINE --
    # Calculate scores for ALL programs
    comparison_data = []
    for p in program_options:
        w_col = f"{p} Weight"
        p_scores = pd.Series(df['Criterion'].map(st.session_state.program_memory[p])).fillna(3)
        p_total_pct = (p_scores / 5 * df[w_col]).sum()
        comparison_data.append({"Typology": p, "Compatibility": p_total_pct, "Color": color_map[p]})
    
    comp_df = pd.DataFrame(comparison_data).sort_values("Compatibility", ascending=False)
    
    # Identify the best conversion target (the one with the highest score that isn't the current target)
    best_alt = comp_df[comp_df['Typology'] != target_program].iloc[0]

    # -- 7. DASHBOARD LAYOUT --
    col1, col2 = st.columns([1, 1.2])

    with col1:
        current_score = comp_df[comp_df['Typology'] == target_program]['Compatibility'].values[0]
        st.metric(f"{target_program} Compatibility", f"{current_score:.1f}%")
        
        # Multi-Color Radar Chart
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=list(st.session_state.program_memory[target_program].values()),
            theta=list(st.session_state.program_memory[target_program].keys()), 
            fill='toself', line_color=color_map[target_program], fillcolor=f"rgba{tuple(int(color_map[target_program].lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.3,)}"
        ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), title="Structural Fingerprint")
        st.plotly_chart(fig_radar, use_container_width=True)

    with col2:
        st.write("### 🔄 Smart Conversion Suggestion")
        st.markdown(f"""
            <div class="recommendation-card">
                <h3>Best Pivot: <b>{best_alt['Typology']}</b></h3>
                <p>Based on your current building chassis, converting to <b>{best_alt['Typology']}</b> 
                is the most feasible option with a <b>{best_alt['Compatibility']:.1f}%</b> compatibility rating.</p>
            </div>
        """, unsafe_allow_html=True)

        st.write("### Portfolio Comparison")
        fig_comp = px.bar(
            comp_df, x='Typology', y='Compatibility', 
            color='Typology', color_discrete_map=color_map,
            text_auto='.1f', range_y=[0, 105]
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    # -- 8. BOTTOM GAP ANALYSIS --
    st.write(f"### Priority Fixes to improve {target_program} Score")
    df['Current_Score'] = df['Criterion'].map(st.session_state.program_memory[target_program])
    df['Gap'] = (5 - df['Current_Score']) * df[f"{target_program} Weight"]
    top_gaps = df.sort_values('Gap', ascending=False).head(5)
    
    fig_gap = px.bar(top_gaps, x='Gap', y='Criterion', orientation='h', 
                     color='Gap', color_continuous_scale='Reds')
    st.plotly_chart(fig_gap, use_container_width=True)

else:
    st.warning("Please check your Google Sheet connection.")
