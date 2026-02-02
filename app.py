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

# -- 2. TYPOLOGY-SPECIFIC MEMORY & DISTINCT COLORS --
program_options = ["Housing", "Education", "Lab", "Data Center"]

color_map = {
    "Housing": "#2E7D32",      # Forest Green
    "Education": "#FBC02D",    # Golden Yellow
    "Lab": "#E03C31",          # Gensler Red
    "Data Center": "#1565C0"   # Deep Cobalt Blue
}

# Critical Fix: Initialize memory BEFORE the rest of the app runs
if 'program_memory' not in st.session_state:
    if not df.empty:
        st.session_state.program_memory = {p: {row['Criterion']: 3 for _, row in df.iterrows()} for p in program_options}
    else:
        st.session_state.program_memory = {p: {} for p in program_options}

# -- 3. PAGE CONFIG --
st.set_page_config(page_title="Universal Adaptive Building Tool", layout="wide")
st.markdown(f"""
    <style>
    .main {{ background-color: #f4f7f6; }}
    .stMetric {{ background-color: #ffffff; padding: 15px; border-radius: 12px; border-top: 6px solid #333333; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }}
    .recommendation-card {{ background-color: #ffffff; padding: 25px; border-radius: 12px; border-left: 10px solid #E03C31; margin-top: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
    </style>
    """, unsafe_allow_html=True)

st.title("🏗️ Universal Adaptive Building Tool")

if not df.empty:
    # -- 4. SELECT TARGET --
    col_top1, _ = st.columns([1, 2])
    with col_top1:
        target_program = st.selectbox("🎯 Select Typology to Optimize", program_options)

    # -- 5. SIDEBAR AUDIT --
    st.sidebar.header(f"🛠️ {target_program} Specifications")
    for cat in df['Category'].unique():
        with st.sidebar.expander(f"📍 {cat}", expanded=True):
            cat_group = df[df['Category'] == cat]
            for _, row in cat_group.iterrows():
                key_name = f"{target_program}_{row['Criterion']}"
                
                # Safety check for memory keys
                if row['Criterion'] not in st.session_state.program_memory[target_program]:
                    st.session_state.program_memory[target_program][row['Criterion']] = 3
                
                st.session_state.program_memory[target_program][row['Criterion']] = st.slider(
                    row['Criterion'], 0, 5, 
                    value=st.session_state.program_memory[target_program][row['Criterion']],
                    help=str(row['Scoring Notes (0-5)']),
                    key=key_name
                )

    # -- 6. MATH & CONVERSION ENGINE --
    comparison_data = []
    for p in program_options:
        w_col = f"{p} Weight"
        p_scores = pd.Series(df['Criterion'].map(st.session_state.program_memory[p])).fillna(3)
        p_total_pct = (p_scores / 5 * df[w_col]).sum()
        comparison_data.append({"Typology": p, "Compatibility": p_total_pct})
    
    comp_df = pd.DataFrame(comparison_data).sort_values("Compatibility", ascending=False)
    best_alt = comp_df[comp_df['Typology'] != target_program].iloc[0]

    # -- 7. DASHBOARD LAYOUT (Symmetrical Realignment) --
    col1, col2 = st.columns([1, 1])

    with col1:
        current_score = comp_df[comp_df['Typology'] == target_program]['Compatibility'].values[0]
        st.metric(f"Current {target_program} Compatibility", f"{current_score:.1f}%")
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=list(st.session_state.program_memory[target_program].values()),
            theta=list(st.session_state.program_memory[target_program].keys()), 
            fill='toself', 
            line_color=color_map[target_program], 
            fillcolor=f"rgba{tuple(int(color_map[target_program].lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.3,)}"
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
            title=dict(text=f"Structural Signature: {target_program}", font=dict(color=color_map[target_program], size=20)),
            margin=dict(l=50, r=50, t=50, b=50)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.write("### Portfolio Comparison Matrix")
        fig_comp = px.bar(
            comp_df, x='Typology', y='Compatibility', 
            color='Typology', color_discrete_map=color_map,
            text_auto='.1f', range_y=[0, 105]
        )
        fig_comp.update_layout(
            showlegend=False, 
            plot_bgcolor="rgba(0,0,0,0)", 
            paper_bgcolor="rgba(0,0,0,0)",
            height=450 
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    # ROW 2: The Logic and Recommendations
    st.markdown("---")
    rec_col, gap_col = st.columns([1, 1])

    with rec_col:
        st.markdown(f"""
            <div class="recommendation-card" style="border-left-color: {color_map[best_alt['Typology']]}">
                <h3 style="color: {color_map[best_alt['Typology']]}">💡 Smart Conversion Recommendation</h3>
                <p>Based on your current building chassis, your <b>{target_program}</b> design is highly adaptable for 
                <b>{best_alt['Typology']}</b> with a <b>{best_alt['Compatibility']:.1f}%</b> compatibility rating.</p>
                <small><i>This pivot requires the least invasive structural intervention.</i></small>
            </div>
        """, unsafe_allow_html=True)

    with gap_col:
        df['Current_Score'] = df['Criterion'].map(st.session_state.program_memory[target_program])
        df['Gap'] = (5 - df['Current_Score']) * df[f"{target_program} Weight"]
        top_gaps = df.sort_values('Gap', ascending=False).head(4)
        
        # Fixed the cut-off code here:
        fig_gap = px.bar(top_gaps, x='Gap', y='Criterion', orientation='h', 
                         color='Gap', color_continuous_scale='Greys',
                         title=f"Critical Fixes for {target_program}")
        fig_gap.update_layout(height=250, margin=dict(t=50, b=0))
        st.plotly_chart(fig_gap, use_container_width=True)

else:
    st.warning("Please check your Google Sheet connection.")
