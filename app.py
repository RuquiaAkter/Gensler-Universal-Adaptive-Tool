import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -- 1. LIVE DATA CONNECTION --
# Using your provided Published CSV link
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS1UOhKUDHJP2tWaAOL0E9M72g3coDNY5HI_3d6DA37Gf4lznsxWBl9WyY25-tDhrTivb76BrZwdqKI/pub?output=csv"

@st.cache_data(ttl=60)
def load_live_data():
    try:
        return pd.read_csv(SHEET_URL)
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return pd.DataFrame()

df = load_live_data()

# -- 2. UI CONFIGURATION --
st.set_page_config(page_title="Gensler Adaptive Scorecard", layout="wide")
st.title("🏗️ Universal Building Adaptation Tool")
st.markdown("### Structural, MEP, and Socio-Economic Feasibility")

if not df.empty:
    # -- 3. PROGRAM SELECTOR --
    program_options = ["Housing", "Education", "Lab", "Data Center"]
    target_program = st.selectbox("🎯 Select Target Analysis", program_options)
    weight_col = f"{target_program} Weight"

    # -- 4. NESTED SIDEBAR INPUTS --
    st.sidebar.header("Building Audit")
    user_scores = {}

    # This creates the 5-Bucket Hierarchy you requested
    for cat in df['Category'].unique():
        with st.sidebar.expander(f"📍 {cat}", expanded=True):
            cat_group = df[df['Category'] == cat]
            for _, row in cat_group.iterrows():
                score = st.sidebar.slider(
                    row['Criterion'], 0, 5, 3, 
                    key=f"{target_program}_{row['Criterion']}",
                    help=str(row.get('Scoring Notes (0-5)', 'Enter score 0-5'))
                )
                user_scores[row['Criterion']] = score

    # -- 5. CALCULATIONS --
    df['Current_Score'] = df['Criterion'].map(user_scores)
    df['Weighted_Score'] = (df['Current_Score'] / 5) * df[weight_col]
    
    final_score_pct = (df['Weighted_Score'].sum() / df[weight_col].sum()) * 100

    # -- 6. DASHBOARD RENDER --
    col1, col2 = st.columns([1, 1])

    with col1:
        st.metric(f"{target_program} Compatibility", f"{final_score_pct:.1f}%")
        
        # Radar Chart: The Visual Fingerprint
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=df['Current_Score'], theta=df['Criterion'], fill='toself', line_color='#E03C31'
        ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), title="Adaptation Fingerprint")
        st.plotly_chart(fig_radar, use_container_width=True)

    with col2:
        st.subheader("Conversion Hurdles (Cost Drivers)")
        # Impact = Weight * Deficiency
        df['Impact'] = (5 - df['Current_Score']) * df[weight_col]
        
        top_blockers = df.sort_values('Impact', ascending=False).head(5)
        fig_bar = px.bar(top_blockers, x='Impact', y='Criterion', orientation='h', color='Category',
                         title=f"Top 5 Financial Risks for {target_program}")
        st.plotly_chart(fig_bar, use_container_width=True)

    # 7. MULTI-PROGRAM COMPARISON
    st.markdown("---")
    st.subheader("Scenario Comparison Matrix")
    comparison = []
    for p in program_options:
        w = f"{p} Weight"
        score = (df['Current_Score'] / 5 * df[w]).sum() / df[w].sum() * 100
        comparison.append({"Program": p, "Score": score})
    
    fig_comp = px.bar(pd.DataFrame(comparison), x='Program', y='Score', color='Score', color_continuous_scale='RdYlGn')
    st.plotly_chart(fig_comp, use_container_width=True)

else:
    st.warning("Data connection pending. Ensure your Google Sheet has columns: Category, Criterion, Housing Weight, Education Weight, Lab Weight, Data Center Weight.")