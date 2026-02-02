import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -- 1. LIVE DATA CONNECTION --
# Ensure this URL matches your "Published to Web" CSV link
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS1UOhKUDHJP2tWaAOL0E9M72g3coDNY5HI_3d6DA37Gf4lznsxWBl9WyY25-tDhrTivb76BrZwdqKI/pub?output=csv"

@st.cache_data(ttl=10)
def load_live_data():
    try:
        df = pd.read_csv(SHEET_URL)
        # Clean column names to prevent mapping errors
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

df = load_live_data()

# -- 2. SESSION STATE (Memory for Sliders) --
if 'user_scores' not in st.session_state:
    st.session_state.user_scores = {}

# -- 3. PAGE CONFIG & BRANDING --
st.set_page_config(page_title="Universal Adaptive Building Tool", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #E03C31; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    div[data-testid="stExpander"] { background-color: white; border-radius: 8px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏗️ Universal Adaptive Building Tool")
st.subheader("Future-Proof Chassis Analysis: Plug-and-Play vs. Invasive Design")

if not df.empty:
    # -- 4. SIDEBAR: BUILDING AUDIT --
    st.sidebar.header("🛠️ Universal Chassis Audit")
    st.sidebar.markdown("Adjust sliders based on your **Modular Waffle** and **Safety Grid** innovations.")

    # Populate session state with sheet defaults if empty
    for _, row in df.iterrows():
        if row['Criterion'] not in st.session_state.user_scores:
            st.session_state.user_scores[row['Criterion']] = 3

    # Create sliders in Sidebar grouped by Category
    for cat in df['Category'].unique():
        with st.sidebar.expander(f"📍 {cat}", expanded=True):
            cat_group = df[df['Category'] == cat]
            for _, row in cat_group.iterrows():
                st.session_state.user_scores[row['Criterion']] = st.slider(
                    row['Criterion'], 0, 5, 
                    value=st.session_state.user_scores[row['Criterion']],
                    help=str(row['Scoring Notes (0-5)'])
                )

    # -- 5. MATH ENGINE --
    program_options = ["Housing", "Education", "Lab", "Data Center"]
    df['Current_Score'] = df['Criterion'].map(st.session_state.user_scores)
    
    # Calculate percentages for all programs
    comparison_data = []
    for p in program_options:
        w_col = f"{p} Weight"
        # Since weights sum to 100, (score/5 * weight) summed = Total %
        p_score = (df['Current_Score'] / 5 * df[w_col]).sum()
        comparison_data.append({"Typology": p, "Compatibility": p_score})
    
    comp_df = pd.DataFrame(comparison_data)

    # -- 6. DASHBOARD LAYOUT --
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.write("### Target Typology Focus")
        target_program = st.selectbox("Select View", program_options)
        
        current_pct = comp_df[comp_df['Typology'] == target_program]['Compatibility'].values[0]
        st.metric(f"{target_program} Compatibility Index", f"{current_pct:.1f}%")
        
        # Radar Chart
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=df['Current_Score'], theta=df['Criterion'], 
            fill='toself', line_color='#E03C31', fillcolor='rgba(224, 60, 49, 0.3)'
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
            margin=dict(l=40, r=40, t=40, b=40),
            title=f"Technical Footprint: {target_program}"
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col2:
        st.write("### Portfolio Resilience Matrix")
        st.markdown("_Compatibility of the current design across all four future scenarios:_")
        
        fig_comp = px.bar(
            comp_df, x='Typology', y='Compatibility', 
            color='Compatibility', color_continuous_scale='RdYlGn',
            text_auto='.1f', range_y=[0, 105]
        )
        fig_comp.update_layout(showlegend=False)
        st.plotly_chart(fig_comp, use_container_width=True)

        # Highlight Gaps for the selected target
        st.write(f"### Critical Gaps for {target_program}")
        w_col = f"{target_program} Weight"
        df['Gap'] = (5 - df['Current_Score']) * df[w_col]
        top_gaps = df.sort_values('Gap', ascending=False).head(4)
        
        fig_gap = px.bar(
            top_gaps, x='Gap', y='Criterion', orientation='h',
            color_discrete_sequence=['#333333'],
            labels={'Gap': 'Impact on Score'}
        )
        st.plotly_chart(fig_gap, use_container_width=True)

    # -- 7. THE UNIVERSAL VERDICT --
    st.markdown("---")
    avg_compat = comp_df['Compatibility'].mean()
    
    v_col1, v_col2 = st.columns(2)
    with v_col1:
        st.subheader(f"Portfolio Versatility Score: {avg_compat:.1f}%")
        st.write("This score represents the building's ability to pivot markets without invasive structural demolition.")
    
    with v_col2:
        if avg_compat > 85:
            st.success("✅ **Universal Chassis Verified:** This design is highly liquid and future-proof.")
        elif avg_compat > 60:
            st.warning("⚠️ **Limited Versatility:** Design is optimized for specific types but invasive for others.")
        else:
            st.error("❌ **Static Asset:** High risk of functional obsolescence.")

else:
    st.warning("Awaiting Data... Please ensure your Google Sheet is 'Published to Web' as a CSV.")
