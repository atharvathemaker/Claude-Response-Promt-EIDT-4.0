import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Command Center",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# SYNTHETIC DATA GENERATION
# ==========================================
@st.cache_data
def load_hospital_data():
    """
    Generates synthetic data dictionaries containing baseline and target metrics 
    for 7 distinct hospital domains.
    """
    data = {
        "Outcomes": {
            "30_Day_Readmission": {"baseline": 18.5, "target": 12.2, "unit": "%", "invert_delta": True},
            "Code_Blue_Frequency": {"baseline": 2.3, "target": 0.8, "unit": " per 1000", "invert_delta": True},
            "Sepsis_Mortality": {"baseline": 28.0, "target": 18.0, "unit": "%", "invert_delta": True},
            "HAI_Rate": {"baseline": 8.5, "target": 4.2, "unit": " per 1000", "invert_delta": True}
        },
        "Operations": {
            "Length_of_Stay": {"baseline": 4.2, "target": 3.1, "unit": " days", "invert_delta": True},
            "Bed_Occupancy": {"baseline": 82.0, "target": 87.0, "unit": "%", "invert_delta": False},
            "Nurse_Overtime": {"baseline": 420.0, "target": 180.0, "unit": " hrs", "invert_delta": True},
            "ED_Wait_Time": {"baseline": 18.0, "target": 5.0, "unit": " mins", "invert_delta": True}
        },
        "Financials": {
            "Readmission_Penalties": {"baseline": -54.5, "target": -8.2, "unit": "L", "invert_delta": False},
            "Revenue_per_Case": {"baseline": 1.2, "target": 1.32, "unit": "L", "invert_delta": False},
            "EBITDA_Margin": {"baseline": 6.2, "target": 12.5, "unit": "%", "invert_delta": False}
        },
        "Experience": {
            "NPS": {"baseline": 28.0, "target": 62.0, "unit": "", "invert_delta": False},
            "Readmission_Disparities": {"baseline": 24.0, "target": 14.0, "unit": "%", "invert_delta": True}
        },
        "Safety": {
            "Sepsis_Bundle_Compliance": {"baseline": 76.0, "target": 98.0, "unit": "%", "invert_delta": False},
            "Leapfrog_Safety_Grade": {"baseline": 70.0, "target": 95.0, "unit": " Score", "invert_delta": False}
        },
        "Workforce": {
            "Staff_Turnover": {"baseline": 18.0, "target": 8.0, "unit": "%", "invert_delta": True},
            "Nurse_Satisfaction": {"baseline": 6.2, "target": 8.1, "unit": " / 10", "invert_delta": False}
        },
        "Strategic": {
            "Market_Share": {"baseline": 18.0, "target": 24.0, "unit": "%", "invert_delta": False},
            "FHIR_Interoperability": {"baseline": 18.0, "target": 87.0, "unit": "%", "invert_delta": False}
        }
    }
    return data

# ==========================================
# HEADER & SIDEBAR INTERACTIVITY
# ==========================================
st.title("Enterprise Healthcare Digital Transformation Command Center")
st.markdown("---")

st.sidebar.header("Command Controls")
activate_transformation = st.sidebar.toggle("Activate Digital Transformation", value=False)

if activate_transformation:
    st.sidebar.success("Transformation Active: Showing Target State")
else:
    st.sidebar.info("Transformation Inactive: Showing Baseline State")

# Load data into context
hospital_data = load_hospital_data()

# Helper for getting the correct state value
def get_metric_value(domain, metric_key, is_active):
    metric = hospital_data[domain][metric_key]
    return metric["target"] if is_active else metric["baseline"]

# ==========================================
# MAIN DASHBOARD ARCHITECTURE (TABS)
# ==========================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Outcomes", 
    "Operations", 
    "Financials", 
    "Experience", 
    "Safety", 
    "Workforce", 
    "Strategic"
])

def render_top_metrics(domain, columns, is_active):
    """Renders the top row metrics for a given domain."""
    domain_data = hospital_data[domain]
    for col, (metric_key, metric_info) in zip(columns, domain_data.items()):
        current_val = get_metric_value(domain, metric_key, is_active)
        
        # Calculate delta if active
        delta_val = None
        if is_active:
            raw_delta = metric_info["target"] - metric_info["baseline"]
            # Formatting delta
            delta_val = f"{raw_delta:+.1f}{metric_info['unit']}"
            
            # Streamlit by default shows green for positive, red for negative.
            # Sometimes a negative value is good (like lower readmissions).
            # We use 'inverse' delta_color to make negative green.
            delta_color = "inverse" if metric_info.get("invert_delta", False) else "normal"
        else:
            delta_color = "normal"

        formatted_val = f"{current_val}{metric_info['unit']}"
        label = metric_key.replace("_", " ")
        
        with col:
            st.metric(label=label, value=formatted_val, delta=delta_val, delta_color=delta_color)

def apply_custom_theme(fig):
    """Applies the mandatory minimalist, beige/grey theme to a Plotly figure."""
    fig.update_layout(
        plot_bgcolor="#f4f4f4", # light grey
        paper_bgcolor="#fdfbf7", # off-white/beige
        font=dict(color="#333333"),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig

# ==========================================
# TAB RENDERERS
# ==========================================

# Outcomes Tab
with tab1:
    st.header("Patient Outcomes")
    cols = st.columns(4)
    render_top_metrics("Outcomes", cols, activate_transformation)
    st.markdown("---")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        current_readmission = get_metric_value("Outcomes", "30_Day_Readmission", activate_transformation)
        fig_readmission = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = current_readmission,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "30 Day Readmission Rate (%)"},
            gauge = {
                'axis': {'range': [None, 25]},
                'bar': {'color': "#2c3e50"},
                'steps': [
                    {'range': [0, 12.5], 'color': "#d5dbdb"},
                    {'range': [12.5, 25], 'color': "#bdc3c7"}
                ]
            }
        ))
        fig_readmission = apply_custom_theme(fig_readmission)
        st.plotly_chart(fig_readmission, use_container_width=True)
        
        if activate_transformation:
            st.success("**Actionable Insight:** AI predictive discharge scoring has reduced readmissions by 34 percent, actively preserving margins and improving care continuity.")
        else:
            st.info("**Actionable Insight:** Current readmission rates are exposing the hospital to severe CMS penalties. Intervention is required at the discharge planning phase.")
            
    with chart_col2:
        current_sepsis = get_metric_value("Outcomes", "Sepsis_Mortality", activate_transformation)
        fig_sepsis = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = current_sepsis,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Sepsis Mortality Rate (%)"},
            gauge = {
                'axis': {'range': [None, 35]},
                'bar': {'color': "#2c3e50"},
                'steps': [
                    {'range': [0, 20], 'color': "#d5dbdb"},
                    {'range': [20, 35], 'color': "#bdc3c7"}
                ]
            }
        ))
        fig_sepsis = apply_custom_theme(fig_sepsis)
        st.plotly_chart(fig_sepsis, use_container_width=True)
        
        if activate_transformation:
            st.success("**Actionable Insight:** Automated sepsis alerting protocols have drastically improved early detection, directly driving down mortality rates.")
        else:
            st.info("**Actionable Insight:** Sepsis mortality remains unacceptably high. Real time deterioration tracking is a critical missing capability.")

# Operations Tab
with tab2:
    st.header("Operational Efficiency")
    cols = st.columns(4)
    render_top_metrics("Operations", cols, activate_transformation)
    st.markdown("---")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Nurse Overtime reduction line chart
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        if activate_transformation:
            overtime_data = [420, 380, 310, 250, 200, 180]
        else:
            overtime_data = [400, 410, 415, 420, 418, 420]
            
        fig_overtime = px.line(x=months, y=overtime_data, title="Nurse Overtime Trajectory (Hours)", markers=True)
        fig_overtime.update_traces(line_color="#2c3e50")
        fig_overtime = apply_custom_theme(fig_overtime)
        st.plotly_chart(fig_overtime, use_container_width=True)
        
        if activate_transformation:
            st.success("**Actionable Insight:** Algorithmic staff scheduling has smoothed shift transitions, heavily reducing premium pay leakage.")
        else:
            st.info("**Actionable Insight:** Reliance on manual scheduling is driving excessive overtime, burning out staff and inflating operational costs.")
            
    with chart_col2:
        # Length of stay bar chart comparing departments
        depts = ["Cardiology", "Neurology", "Orthopedics", "General Surgery"]
        if activate_transformation:
            los_data = [3.5, 4.1, 2.5, 2.3]
        else:
            los_data = [4.8, 5.5, 3.2, 3.3]
            
        fig_los = px.bar(x=depts, y=los_data, title="Average Length of Stay by Department (Days)")
        fig_los.update_traces(marker_color="#7f8c8d")
        fig_los = apply_custom_theme(fig_los)
        st.plotly_chart(fig_los, use_container_width=True)
        
        if activate_transformation:
            st.success("**Actionable Insight:** Digital care pathways have optimized inpatient routing, freeing up bed capacity across all major service lines.")
        else:
            st.info("**Actionable Insight:** Bottlenecks in interdepartmental communication are prolonging stays and limiting patient throughput.")

# Financials Tab
with tab3:
    st.header("Financials & Revenue")
    cols = st.columns(3)
    render_top_metrics("Financials", cols, activate_transformation)
    st.markdown("---")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        current_penalty = get_metric_value("Financials", "Readmission_Penalties", activate_transformation)
        fig_penalty = go.Figure(go.Waterfall(
            name = "Penalties", orientation = "v",
            measure = ["absolute", "relative", "total"],
            x = ["Gross Revenue", "Readmission Penalties", "Net Adjusted"],
            textposition = "outside",
            y = [500, current_penalty, 500 + current_penalty],
            connector = {"line": {"color": "rgb(63, 63, 63)"}}
        ))
        fig_penalty.update_layout(title="Revenue Impact of Penalties (Lakhs)")
        fig_penalty = apply_custom_theme(fig_penalty)
        st.plotly_chart(fig_penalty, use_container_width=True)
        
        if activate_transformation:
            st.success("**Actionable Insight:** Substantial mitigation of readmission penalties is directly bolstering the bottom line and protecting core revenue.")
        else:
            st.info("**Actionable Insight:** Preventable readmissions are eroding gross revenue margins. Clinical workflows must be optimized to halt this revenue leakage.")
            
    with chart_col2:
        current_margin = get_metric_value("Financials", "EBITDA_Margin", activate_transformation)
        fig_margin = go.Figure(go.Indicator(
            mode = "number+delta",
            value = current_margin,
            title = {"text": "EBITDA Margin (%)"},
            delta = {'reference': 6.2, 'relative': False},
            domain = {'x': [0, 1], 'y': [0, 1]}
        ))
        fig_margin = apply_custom_theme(fig_margin)
        st.plotly_chart(fig_margin, use_container_width=True)
        
        if activate_transformation:
            st.success("**Actionable Insight:** The digital transformation portfolio is yielding a strong ROI, doubling EBITDA margins through combined operational efficiencies.")
        else:
            st.info("**Actionable Insight:** Operating margins are dangerously thin. Strategic digital investments are required to unlock new value streams.")

# Experience Tab
with tab4:
    st.header("Patient Experience & Equity")
    cols = st.columns(2)
    render_top_metrics("Experience", cols, activate_transformation)
    st.markdown("---")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        income_groups = ["High Income", "Middle Income", "Low Income"]
        if activate_transformation:
            disp_data = [10.0, 12.0, 14.0]
        else:
            disp_data = [10.0, 15.0, 24.0]
            
        fig_equity = go.Figure(data=[
            go.Bar(name='Readmission Rate', x=income_groups, y=disp_data, marker_color="#34495e")
        ])
        fig_equity.update_layout(title="Readmission Rates by Income Demographic (%)")
        fig_equity = apply_custom_theme(fig_equity)
        st.plotly_chart(fig_equity, use_container_width=True)
        
        if activate_transformation:
            st.success("**Actionable Insight:** Targeted telehealth follow ups for vulnerable populations have dramatically closed the health equity gap.")
        else:
            st.info("**Actionable Insight:** Severe disparities exist in post discharge outcomes. Lower income demographics require better access to transitional care.")
            
    with chart_col2:
        quarters = ["Q1", "Q2", "Q3", "Q4"]
        if activate_transformation:
            nps_data = [35, 45, 55, 62]
        else:
            nps_data = [28, 27, 28, 28]
            
        fig_nps = px.line(x=quarters, y=nps_data, title="Net Promoter Score (NPS) Trend", markers=True)
        fig_nps.update_traces(line_color="#7f8c8d")
        fig_nps = apply_custom_theme(fig_nps)
        st.plotly_chart(fig_nps, use_container_width=True)
        
        if activate_transformation:
            st.success("**Actionable Insight:** Digital patient portals and streamlined check in processes have significantly elevated overall patient satisfaction.")
        else:
            st.info("**Actionable Insight:** Patient experience scores are stagnating. Friction in the administrative journey is degrading clinical perception.")

# Safety Tab
with tab5:
    st.header("Safety & Quality")
    cols = st.columns(2)
    render_top_metrics("Safety", cols, activate_transformation)
    st.markdown("---")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        current_compliance = get_metric_value("Safety", "Sepsis_Bundle_Compliance", activate_transformation)
        fig_compliance = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = current_compliance,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Sepsis Bundle Compliance (%)"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "#2c3e50"},
                'steps': [
                    {'range': [0, 50], 'color': "#e74c3c"},
                    {'range': [50, 80], 'color': "#f39c12"},
                    {'range': [80, 100], 'color': "#2ecc71"}
                ]
            }
        ))
        fig_compliance = apply_custom_theme(fig_compliance)
        st.plotly_chart(fig_compliance, use_container_width=True)
        
        if activate_transformation:
            st.success("**Actionable Insight:** Electronic Health Record integrations prompt clinicians perfectly, ensuring near flawless bundle compliance.")
        else:
            st.info("**Actionable Insight:** Care gaps in the sepsis bundle are putting patients at risk. Workflow standardization is urgently needed.")
            
    with chart_col2:
        current_leapfrog = get_metric_value("Safety", "Leapfrog_Safety_Grade", activate_transformation)
        fig_leapfrog = go.Figure(go.Indicator(
            mode = "number+delta",
            value = current_leapfrog,
            title = {"text": "Leapfrog Safety Score"},
            delta = {'reference': 70, 'relative': False},
            domain = {'x': [0, 1], 'y': [0, 1]}
        ))
        fig_leapfrog = apply_custom_theme(fig_leapfrog)
        st.plotly_chart(fig_leapfrog, use_container_width=True)
        
        if activate_transformation:
            st.success("**Actionable Insight:** Achieving an 'A' grade standard reflects a systemic overhaul of patient safety protocols driven by data transparency.")
        else:
            st.info("**Actionable Insight:** A 'C' grade safety rating damages institutional reputation and highlights fundamental flaws in adverse event prevention.")

# Workforce Tab
with tab6:
    st.header("Workforce Management")
    cols = st.columns(2)
    render_top_metrics("Workforce", cols, activate_transformation)
    st.markdown("---")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        roles = ["RNs", "Physicians", "Admin", "Support"]
        if activate_transformation:
            turnover_data = [8.5, 4.0, 9.0, 10.5]
        else:
            turnover_data = [22.0, 8.0, 15.0, 18.0]
            
        fig_turnover = px.bar(x=roles, y=turnover_data, title="Annual Turnover by Role (%)", barmode="group")
        fig_turnover.update_traces(marker_color="#95a5a6")
        fig_turnover = apply_custom_theme(fig_turnover)
        st.plotly_chart(fig_turnover, use_container_width=True)
        
        if activate_transformation:
            st.success("**Actionable Insight:** Automating menial tasks has restored clinical autonomy, drastically reducing burnout and retaining vital nursing talent.")
        else:
            st.info("**Actionable Insight:** High nursing turnover is a leading indicator of systemic burnout. Replacement costs are unsustainable.")

    with chart_col2:
        current_sat = get_metric_value("Workforce", "Nurse_Satisfaction", activate_transformation)
        fig_sat = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = current_sat,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Nurse Satisfaction (out of 10)"},
            gauge = {
                'axis': {'range': [None, 10]},
                'bar': {'color': "#2c3e50"}
            }
        ))
        fig_sat = apply_custom_theme(fig_sat)
        st.plotly_chart(fig_sat, use_container_width=True)
        
        if activate_transformation:
            st.success("**Actionable Insight:** Mobile communication tools and AI documentation assistants have vastly improved the daily workflow experience for clinical staff.")
        else:
            st.info("**Actionable Insight:** Documentation burden and inefficient paging systems are actively degrading staff morale.")

# Strategic Tab
with tab7:
    st.header("Strategic Growth & Interoperability")
    cols = st.columns(2)
    render_top_metrics("Strategic", cols, activate_transformation)
    st.markdown("---")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        categories = ['Data Analytics', 'Cloud Infra', 'Patient Engagement', 'Automation', 'Interoperability']
        if activate_transformation:
            maturity = [9, 8, 9, 8, 9]
        else:
            maturity = [3, 4, 3, 2, 2]
            
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=maturity,
            theta=categories,
            fill='toself',
            name='Current State',
            line_color="#2c3e50"
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            showlegend=False,
            title="Digital Maturity Radar"
        )
        fig_radar = apply_custom_theme(fig_radar)
        st.plotly_chart(fig_radar, use_container_width=True)
        
        if activate_transformation:
            st.success("**Actionable Insight:** The organization has achieved advanced digital maturity, unlocking scalable growth and data driven decision making at all levels.")
        else:
            st.info("**Actionable Insight:** Lacking core digital infrastructure limits the ability to scale services or compete effectively in a modern healthcare market.")

    with chart_col2:
        years = ["2020", "2021", "2022", "2023", "2024"]
        if activate_transformation:
            market_share = [15, 16, 18, 21, 24]
        else:
            market_share = [15, 16, 17, 18, 18]
            
        fig_share = px.area(x=years, y=market_share, title="Regional Market Share Growth (%)")
        fig_share.update_traces(line_color="#7f8c8d", fillcolor="rgba(127, 140, 141, 0.3)")
        fig_share = apply_custom_theme(fig_share)
        st.plotly_chart(fig_share, use_container_width=True)
        
        if activate_transformation:
            st.success("**Actionable Insight:** Superior patient experience and outcomes are driving strong market capture against regional competitors.")
        else:
            st.info("**Actionable Insight:** Market share is flat. Without differentiating digital services, the hospital risks losing volume to more agile competitors.")

