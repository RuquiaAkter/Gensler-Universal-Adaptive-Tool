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

# Initialize a nested dictionary to store scores for each program separately
if 'program_memory' not in st.session_state:
    st.session_state.program_memory = {p: {} for p in program_options}

# -- 3. PAGE CONFIG --
st.set_page_config(page_title="Universal Adaptive Building Tool", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #E03C31; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    div[data-testid="stExpander"] { background-color: white; border-radius: 8px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏗️ Universal Adaptive Building Tool")

if not df.empty:
    # -- 4. SELECT TARGET VIEW --
    # We move this to the top so it controls which "Memory" we are accessing
    col_top1, col_top2 = st.columns([1, 2])
    with col_top1:
        target_program = st.selectbox("🎯 Select Target Typology to Optimize", program_options)

    # -- 5. SIDEBAR: BUILDING AUDIT (Linked to specific Memory) --
    st.sidebar.header(f"🛠️ {target_program} Audit")
    st.sidebar.markdown(f"Adjust these sliders to optimize the building specifically for **{target_program}**.")

    # Ensure memory is populated for the selected program
    for _, row in df.iterrows():
        if row['Criterion'] not in st.session_state.program_memory[target_program]:
            st.session_state.program_memory[target_program][row['Criterion']] = 3

    # Create sliders that update ONLY the selected program's memory
    for cat in df['Category'].unique():
        with st.sidebar.expander(f"📍 {cat}", expanded=True):
            cat_group = df[df['Category'] == cat]
            for _, row in cat_group.iterrows():
                # Key is unique to the typology + criterion so Streamlit doesn't get confused
                key_name = f"{target_program}_{row['Criterion']}"
                st.session_state.program_memory[target_program][row['Criterion']] = st.slider(
                    row['Criterion'], 0, 5, 
                    value=st.session_state.program_memory[target_program][row['Criterion']],
                    help=str(row['Scoring Notes (0-5)']),
                    key=key_name
                )

    # -- 6. MATH ENGINE --
    # Map the stored scores for the ACTIVE typology
    df['Current_Score'] = df['Criterion'].map(st.session_state.program_memory[target_program])
    
    # Calculate scores for ALL programs using their own saved settings
    comparison_data = []
    for p in program_options:
        w_col = f"{p} Weight"
        # Get scores saved for this specific program
        p_scores = pd.Series(df['Criterion'].map(st.session_state.program_memory[p])).fillna(3)
        p_total_pct = (p_scores / 5 * df[w_col]).sum()
        comparison_data.append({"Typology": p, "Compatibility": p_total_pct})
    
    comp_df = pd.DataFrame(comparison_data)

    # -- 7. DASHBOARD LAYOUT --
    col1, col2 = st.columns([1, 1.2])

    with col1:
        current_pct = comp_df[comp_df['Typology'] == target_program]['Compatibility'].values[0]
        st.metric(f"Current {target_program} Score", f"{current_pct:.1f}%")
        
        # Radar Chart for Active Typology
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=df['Current_Score'], theta=df['Criterion'], 
            fill='toself', line_color='#E03C31', fillcolor='rgba(224, 60, 49, 0.3)'
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
            title=f"Technical Fingerprint: {target_program}"
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col2:
        st.write("### Cross-Scenario Performance")
        st.markdown("_How your saved designs for each typology compare:_")
        
        fig_comp = px.bar(
            comp_df, x='Typology', y='Compatibility', 
            color='Typology', color_discrete_sequence=['#333333', '#666666', '#E03C31', '#999999'],
            text_auto='.1f', range_y=[0, 105]
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        st.write(f"### Priority Gaps: {target_program}")
        w_col = f"{target_program} Weight"
        df['Gap'] = (5 - df['Current_Score']) * df[w_col]
        top_gaps = df.sort_values('Gap', ascending=False).head(4)
        
        fig_gap = px.bar(top_gaps, x='Gap', y='Criterion', orientation='h', color_discrete_sequence=['#E03C31'])
        st.plotly_chart(fig_gap, use_container_width=True)

else:
    st.warning("Please check your Google Sheet connection.")
