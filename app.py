import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Enterprise Command Center",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# UI & STYLING OVERHAUL
# ==========================================
st.markdown("""
<style>
    /* Import modern sleek font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Remove padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Metric styling */
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #1B263B;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 1rem;
        font-weight: 600;
        color: #415A77;
    }
</style>
""", unsafe_allow_html=True)

# Color Palette
DEEP_NAVY = "#1B263B"
SLATE = "#415A77"
EMERALD = "#2A9D8F"
CRIMSON = "#E76F51"
LIGHT_GREY = "#E2E8F0"

# Set global plotly template
import plotly.io as pio
pio.templates.default = "plotly_white"

def apply_corporate_theme(fig):
    fig.update_layout(
        font=dict(family="Inter, sans-serif", color=DEEP_NAVY),
        margin=dict(l=40, r=40, t=60, b=40),
        title_font=dict(size=18, color=DEEP_NAVY, family="Inter, sans-serif", weight="bold")
    )
    return fig

# ==========================================
# SYNTHETIC DATA GENERATION
# ==========================================
@st.cache_data
def load_hospital_data():
    data = {
        "Outcomes": {
            "30_Day_Readmission": {"baseline": 18.5, "target": 12.2, "unit": "%", "invert_delta": True},
            "Sepsis_Mortality": {"baseline": 28.0, "target": 18.0, "unit": "%", "invert_delta": True}
        },
        "Operations": {
            "Length_of_Stay": {"baseline": 4.2, "target": 3.1, "unit": " days", "invert_delta": True},
            "Nurse_Overtime": {"baseline": 420.0, "target": 180.0, "unit": " hrs", "invert_delta": True}
        },
        "Financials": {
            "Readmission_Penalties": {"baseline": -54.5, "target": -8.2, "unit": "L", "invert_delta": False},
            "EBITDA_Margin": {"baseline": 6.2, "target": 12.5, "unit": "%", "invert_delta": False}
        },
        "Experience": {
            "NPS": {"baseline": 28.0, "target": 62.0, "unit": "", "invert_delta": False}
        },
        "Safety": {
            "Leapfrog_Safety_Grade": {"baseline": 70.0, "target": 95.0, "unit": " Score", "invert_delta": False}
        },
        "Workforce": {
            "Staff_Turnover": {"baseline": 18.0, "target": 8.0, "unit": "%", "invert_delta": True}
        },
        "Strategic": {
            "FHIR_Interoperability": {"baseline": 18.0, "target": 87.0, "unit": "%", "invert_delta": False}
        }
    }
    return data

@st.cache_data
def load_patient_database():
    np.random.seed(42)
    time_index = pd.date_range("2023-10-25 00:00", "2023-10-25 23:00", freq="h")
    
    patients = [
        {"id": "P-1001", "name": "Arthur Pendelton", "age": 68, "diagnosis": "Congestive Heart Failure", "ward": "Cardiology"},
        {"id": "P-1002", "name": "Maria Gonzalez", "age": 54, "diagnosis": "Sepsis Protocol", "ward": "ICU"},
        {"id": "P-1003", "name": "James Smith", "age": 72, "diagnosis": "Post-Op Orthopedic", "ward": "Surgery"},
        {"id": "P-1004", "name": "Linda Chen", "age": 45, "diagnosis": "Pneumonia", "ward": "Pulmonary"},
        {"id": "P-1005", "name": "Robert Brown", "age": 81, "diagnosis": "Acute Kidney Injury", "ward": "Nephrology"}
    ]
    
    db = []
    for p in patients:
        base_hr = np.random.randint(70, 100)
        base_spo2 = np.random.randint(90, 98)
        
        continuous_hr = base_hr + np.random.normal(0, 3, 24)
        continuous_spo2 = np.clip(base_spo2 + np.random.normal(0, 1, 24), 80, 100)
        
        # Create fragmented data for baseline (only measured every 4 hours)
        fragmented_hr = [val if i % 4 == 0 else np.nan for i, val in enumerate(continuous_hr)]
        fragmented_spo2 = [val if i % 4 == 0 else np.nan for i, val in enumerate(continuous_spo2)]
        
        p["timeline"] = time_index
        p["hr_continuous"] = continuous_hr
        p["hr_fragmented"] = fragmented_hr
        p["spo2_continuous"] = continuous_spo2
        p["spo2_fragmented"] = fragmented_spo2
        
        db.append(p)
        
    return {p["id"]: p for p in db}

hospital_data = load_hospital_data()
patient_db = load_patient_database()

def get_metric_value(domain, metric_key, is_active):
    metric = hospital_data[domain][metric_key]
    return metric["target"] if is_active else metric["baseline"]

# ==========================================
# HEADER & SIDEBAR INTERACTIVITY
# ==========================================
st.sidebar.header("Command Controls")
activate_transformation = st.sidebar.toggle("Activate Digital Transformation", value=False)

if activate_transformation:
    st.sidebar.success("Transformation Active: Showing Target State")
else:
    st.sidebar.warning("Transformation Inactive: Showing Baseline State")

st.sidebar.markdown("---")
st.sidebar.subheader("Live Patient Risk Simulator")
sim_name = st.sidebar.text_input("Patient Name", value="John Doe")
sim_age = st.sidebar.number_input("Age", min_value=1, max_value=120, value=65)
sim_hr = st.sidebar.slider("Current Heart Rate (bpm)", min_value=40, max_value=180, value=110)
sim_spo2 = st.sidebar.slider("SpO2 Level (%)", min_value=70, max_value=100, value=88)

st.title("Enterprise Healthcare Digital Transformation Command Center")
st.markdown("---")

# ==========================================
# LIVE PATIENT FEED (TOP METRIC CARD)
# ==========================================
st.subheader("Live Patient Feed")

# Calculate dynamic risk
base_risk = 50
if sim_age > 60: base_risk += 15
if sim_hr > 100 or sim_hr < 50: base_risk += 20
if sim_spo2 < 92: base_risk += 25

if activate_transformation:
    # Predictive intervention drops risk
    calculated_risk = max(10, base_risk - 45)
    risk_color = "normal" if calculated_risk <= 50 else "inverse"
    risk_label = "Low" if calculated_risk < 40 else ("Medium" if calculated_risk < 70 else "High")
    delta_risk = "-45% (AI Intervention)"
else:
    calculated_risk = min(99, base_risk)
    risk_color = "inverse"
    risk_label = "High" if calculated_risk > 70 else ("Medium" if calculated_risk > 40 else "Low")
    delta_risk = "+0% (No Intervention)"

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Patient Name", sim_name)
with col2:
    st.metric("Age", str(sim_age))
with col3:
    st.metric("Current Vitals", f"HR: {sim_hr} | SpO2: {sim_spo2}%")
with col4:
    st.metric("Real-Time Readmission Risk", f"{calculated_risk}% ({risk_label})", delta=delta_risk, delta_color="inverse")

st.markdown("---")

# ==========================================
# MAIN DASHBOARD ARCHITECTURE (8 TABS)
# ==========================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Outcomes", 
    "Operations", 
    "Financials", 
    "Experience", 
    "Safety", 
    "Workforce", 
    "Strategic",
    "Patient Search"
])

def render_top_metrics(domain, columns, is_active):
    domain_data = hospital_data[domain]
    for col, (metric_key, metric_info) in zip(columns, domain_data.items()):
        current_val = get_metric_value(domain, metric_key, is_active)
        
        delta_val = None
        if is_active:
            raw_delta = metric_info["target"] - metric_info["baseline"]
            delta_val = f"{raw_delta:+.1f}{metric_info['unit']}"
            delta_color = "inverse" if metric_info.get("invert_delta", False) else "normal"
        else:
            delta_color = "normal"

        formatted_val = f"{current_val}{metric_info['unit']}"
        label = metric_key.replace("_", " ")
        
        with col:
            st.metric(label=label, value=formatted_val, delta=delta_val, delta_color=delta_color)

# ==========================================
# TAB 1: OUTCOMES
# ==========================================
with tab1:
    cols = st.columns(2)
    render_top_metrics("Outcomes", cols, activate_transformation)
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        # Donut Chart for Readmission
        val = get_metric_value("Outcomes", "30_Day_Readmission", activate_transformation)
        fig1 = go.Figure(data=[go.Pie(labels=['Readmitted', 'Not Readmitted'], 
                                     values=[val, 100-val], 
                                     hole=.6,
                                     marker_colors=[CRIMSON if val > 15 else EMERALD, LIGHT_GREY])])
        fig1.update_layout(title="30 Day Readmission Distribution")
        fig1 = apply_corporate_theme(fig1)
        st.plotly_chart(fig1, use_container_width=True)
        
        if activate_transformation:
            st.success("Actionable Insight: AI predictive discharge scoring actively identifies high risk patients prior to release, bringing readmissions down to industry leading levels.")
        else:
            st.info("Actionable Insight: Current readmission volumes exceed acceptable clinical thresholds, triggering massive CMS penalties and indicating poor discharge protocols.")

    with c2:
        # Area chart for Sepsis
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        if activate_transformation:
            sepsis_trend = [28, 25, 22, 20, 19, 18]
            color = EMERALD
        else:
            sepsis_trend = [27, 28, 28, 29, 28, 28]
            color = CRIMSON
            
        fig2 = px.area(x=months, y=sepsis_trend, title="Sepsis Mortality Trend (%)")
        fig2.update_traces(line_color=color, fillcolor=color, opacity=0.3)
        fig2 = apply_corporate_theme(fig2)
        st.plotly_chart(fig2, use_container_width=True)
        
        if activate_transformation:
            st.success("Actionable Insight: Automated EHR sepsis alerts enable immediate rapid response team intervention, successfully preserving life and improving critical outcomes.")
        else:
            st.info("Actionable Insight: Late identification of septic shock is driving preventable mortality. Staff lack real time deterioration tracking systems.")

# ==========================================
# TAB 2: OPERATIONS
# ==========================================
with tab2:
    cols = st.columns(2)
    render_top_metrics("Operations", cols, activate_transformation)
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        # Grouped Bar for LOS
        depts = ["Cardio", "Neuro", "Ortho", "Surg"]
        if activate_transformation:
            los = [3.5, 4.1, 2.5, 2.3]
            color = EMERALD
        else:
            los = [4.8, 5.5, 3.2, 3.3]
            color = SLATE
            
        fig3 = px.bar(x=depts, y=los, title="Average Length of Stay by Dept", barmode="group")
        fig3.update_traces(marker_color=color)
        fig3 = apply_corporate_theme(fig3)
        st.plotly_chart(fig3, use_container_width=True)
        
        if activate_transformation:
            st.success("Actionable Insight: Digital care pathways and automated bed management have optimized patient throughput across all primary service lines.")
        else:
            st.info("Actionable Insight: Severe operational bottlenecks exist in interdepartmental communication, artificially inflating length of stay.")

    with c2:
        months = ["Q1", "Q2", "Q3", "Q4"]
        if activate_transformation:
            ot = [350, 250, 200, 180]
            color = EMERALD
        else:
            ot = [410, 420, 415, 420]
            color = CRIMSON
            
        fig4 = px.line(x=months, y=ot, title="Quarterly Nurse Overtime (Hrs)", markers=True)
        fig4.update_traces(line_color=color, marker=dict(size=10))
        fig4 = apply_corporate_theme(fig4)
        st.plotly_chart(fig4, use_container_width=True)
        
        if activate_transformation:
            st.success("Actionable Insight: Machine learning scheduling models align staffing with predictive patient census, practically eliminating premium pay leakage.")
        else:
            st.info("Actionable Insight: Manual scheduling processes are failing to adapt to volume surges, driving burnout and unacceptable overtime costs.")

# ==========================================
# TAB 3: FINANCIALS
# ==========================================
with tab3:
    cols = st.columns(2)
    render_top_metrics("Financials", cols, activate_transformation)
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        val = get_metric_value("Financials", "Readmission_Penalties", activate_transformation)
        fig5 = go.Figure(go.Indicator(
            mode = "number+delta",
            value = val,
            title = {"text": "Readmission Penalties (Lakhs)"},
            delta = {'reference': -54.5, 'relative': False, 'increasing': {'color': EMERALD}},
            domain = {'x': [0, 1], 'y': [0, 1]}
        ))
        fig5 = apply_corporate_theme(fig5)
        st.plotly_chart(fig5, use_container_width=True)
        
        if activate_transformation:
            st.success("Actionable Insight: Transformation efforts have effectively mitigated clinical penalties, securing millions in previously lost bottom line revenue.")
        else:
            st.info("Actionable Insight: The hospital is actively bleeding gross revenue due to CMS penalty structures triggered by poor clinical outcomes.")

    with c2:
        val = get_metric_value("Financials", "EBITDA_Margin", activate_transformation)
        fig6 = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = val,
            title = {'text': "EBITDA Margin (%)"},
            gauge = {
                'axis': {'range': [0, 20]},
                'bar': {'color': DEEP_NAVY},
                'steps': [
                    {'range': [0, 8], 'color': CRIMSON},
                    {'range': [8, 20], 'color': EMERALD}
                ]
            }
        ))
        fig6 = apply_corporate_theme(fig6)
        st.plotly_chart(fig6, use_container_width=True)
        
        if activate_transformation:
            st.success("Actionable Insight: Synergistic operational efficiencies have driven a doubling of operating margins, establishing a highly profitable growth trajectory.")
        else:
            st.info("Actionable Insight: Thin operating margins place the institution at severe financial risk. Immediate structural intervention is required.")

# ==========================================
# TAB 4: EXPERIENCE
# ==========================================
with tab4:
    cols = st.columns(1)
    render_top_metrics("Experience", cols, activate_transformation)
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        quarters = ["Q1", "Q2", "Q3", "Q4"]
        if activate_transformation:
            nps = [35, 45, 55, 62]
            color = EMERALD
        else:
            nps = [28, 27, 28, 28]
            color = SLATE
            
        fig7 = px.bar(x=quarters, y=nps, title="Net Promoter Score Progression")
        fig7.update_traces(marker_color=color)
        fig7 = apply_corporate_theme(fig7)
        st.plotly_chart(fig7, use_container_width=True)
        
        if activate_transformation:
            st.success("Actionable Insight: Digital front door strategies and self service portals have drastically elevated consumer perception and loyalty.")
        else:
            st.info("Actionable Insight: The patient experience is highly friction laden. Outdated administrative workflows are damaging brand equity.")

    with c2:
        if activate_transformation:
            labels = ["Detractors", "Passives", "Promoters"]
            values = [15, 23, 62]
            colors = [CRIMSON, LIGHT_GREY, EMERALD]
        else:
            labels = ["Detractors", "Passives", "Promoters"]
            values = [42, 30, 28]
            colors = [CRIMSON, LIGHT_GREY, SLATE]
            
        fig8 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4, marker_colors=colors)])
        fig8.update_layout(title="Current Patient Sentiment Breakdown")
        fig8 = apply_corporate_theme(fig8)
        st.plotly_chart(fig8, use_container_width=True)
        
        if activate_transformation:
            st.success("Actionable Insight: Streamlined billing and virtual care follow ups have successfully converted the majority of patients into active brand promoters.")
        else:
            st.info("Actionable Insight: A dangerous volume of patients are detractors, threatening market share via negative community word of mouth.")

# ==========================================
# TAB 5: SAFETY
# ==========================================
with tab5:
    cols = st.columns(1)
    render_top_metrics("Safety", cols, activate_transformation)
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        val = get_metric_value("Safety", "Leapfrog_Safety_Grade", activate_transformation)
        fig9 = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = val,
            title = {'text': "Leapfrog Safety Score"},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': DEEP_NAVY},
                'steps': [
                    {'range': [0, 75], 'color': CRIMSON},
                    {'range': [75, 100], 'color': EMERALD}
                ]
            }
        ))
        fig9 = apply_corporate_theme(fig9)
        st.plotly_chart(fig9, use_container_width=True)
        
        if activate_transformation:
            st.success("Actionable Insight: Reaching an A grade standard establishes the hospital as a regional leader in adverse event prevention and clinical excellence.")
        else:
            st.info("Actionable Insight: The current C grade indicates deep systemic flaws in clinical safety mechanisms and risks severe reputational damage.")

    with c2:
        incidents = ["Med Errors", "Falls", "Infections"]
        if activate_transformation:
            counts = [12, 8, 5]
            color = EMERALD
        else:
            counts = [45, 32, 28]
            color = CRIMSON
            
        fig10 = px.bar(x=incidents, y=counts, title="Monthly Adverse Safety Incidents", text=counts)
        fig10.update_traces(marker_color=color)
        fig10 = apply_corporate_theme(fig10)
        st.plotly_chart(fig10, use_container_width=True)
        
        if activate_transformation:
            st.success("Actionable Insight: Barcode medication administration and AI visual fall monitoring have suppressed adverse events to absolute minimums.")
        else:
            st.info("Actionable Insight: High rates of preventable errors point to a lack of automated safety guardrails at the point of care.")

# ==========================================
# TAB 6: WORKFORCE
# ==========================================
with tab6:
    cols = st.columns(1)
    render_top_metrics("Workforce", cols, activate_transformation)
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        roles = ["RNs", "MDs", "Techs"]
        if activate_transformation:
            turnover = [8, 4, 10]
            color = EMERALD
        else:
            turnover = [22, 9, 18]
            color = CRIMSON
            
        fig11 = px.bar(x=roles, y=turnover, title="Annual Turnover by Role (%)")
        fig11.update_traces(marker_color=color)
        fig11 = apply_corporate_theme(fig11)
        st.plotly_chart(fig11, use_container_width=True)
        
        if activate_transformation:
            st.success("Actionable Insight: Offloading administrative tasks to AI assistants has restored clinical autonomy and dramatically improved talent retention.")
        else:
            st.info("Actionable Insight: Unmanageable documentation burden is causing critical nursing talent to exit the organization at alarming rates.")

    with c2:
        months = ["Jan", "Feb", "Mar", "Apr", "May"]
        if activate_transformation:
            sat = [6.5, 7.0, 7.5, 7.8, 8.1]
            color = EMERALD
        else:
            sat = [6.2, 6.1, 6.2, 6.0, 6.2]
            color = SLATE
            
        fig12 = px.line(x=months, y=sat, title="Clinical Staff Satisfaction Trend (1-10)", markers=True)
        fig12.update_traces(line_color=color, marker=dict(size=10))
        fig12 = apply_corporate_theme(fig12)
        st.plotly_chart(fig12, use_container_width=True)
        
        if activate_transformation:
            st.success("Actionable Insight: Intuitive clinical communication platforms have removed daily friction, driving consistent improvements in workforce morale.")
        else:
            st.info("Actionable Insight: Fragmented communication and outdated pagers remain top complaints, leading to pervasive daily frustration among providers.")

# ==========================================
# TAB 7: STRATEGIC
# ==========================================
with tab7:
    cols = st.columns(1)
    render_top_metrics("Strategic", cols, activate_transformation)
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        categories = ['Analytics', 'Cloud', 'Patient App', 'Automation', 'FHIR']
        if activate_transformation:
            maturity = [9, 8, 9, 8, 9]
            color = EMERALD
        else:
            maturity = [3, 4, 3, 2, 2]
            color = SLATE
            
        fig13 = go.Figure()
        fig13.add_trace(go.Scatterpolar(
            r=maturity,
            theta=categories,
            fill='toself',
            marker_color=color
        ))
        fig13.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            showlegend=False,
            title="Digital Maturity Radar"
        )
        fig13 = apply_corporate_theme(fig13)
        st.plotly_chart(fig13, use_container_width=True)
        
        if activate_transformation:
            st.success("Actionable Insight: Achievement of Stage 7 maturity enables seamless interoperability and scales advanced analytics across the entire enterprise.")
        else:
            st.info("Actionable Insight: The organization operates on siloed, legacy infrastructure, severely limiting strategic growth and data liquidity.")

    with c2:
        val = get_metric_value("Strategic", "FHIR_Interoperability", activate_transformation)
        fig14 = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = val,
            title = {'text': "API Data Exchange Volume (%)"},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': DEEP_NAVY},
                'steps': [
                    {'range': [0, 30], 'color': CRIMSON},
                    {'range': [30, 100], 'color': EMERALD}
                ]
            }
        ))
        fig14 = apply_corporate_theme(fig14)
        st.plotly_chart(fig14, use_container_width=True)
        
        if activate_transformation:
            st.success("Actionable Insight: Open FHIR APIs ensure frictionless data sharing with community partners, enabling true population health management.")
        else:
            st.info("Actionable Insight: Critical patient data is trapped within proprietary EHR silos, blocking coordinated care across external networks.")

# ==========================================
# TAB 8: PATIENT SEARCH
# ==========================================
with tab8:
    st.header("Individual Patient Deep Dive (Digital Twin)")
    
    patient_options = [f"{p['id']} - {p['name']}" for p in patient_db.values()]
    selected_option = st.selectbox("Search and Select Patient:", patient_options)
    
    if selected_option:
        pid = selected_option.split(" - ")[0]
        patient = patient_db[pid]
        
        # Demographics Header
        st.markdown(f"### {patient['name']} | Age: {patient['age']} | Ward: {patient['ward']}")
        st.markdown(f"**Primary Diagnosis:** {patient['diagnosis']}")
        st.markdown("---")
        
        c1, c2 = st.columns([2, 1])
        
        with c1:
            # Dual Axis Vitals Timeline
            fig15 = make_subplots(specs=[[{"secondary_y": True}]])
            
            time_x = patient["timeline"]
            if activate_transformation:
                hr_y = patient["hr_continuous"]
                spo2_y = patient["spo2_continuous"]
                mode_str = "lines"
                title_str = "24 Hour Vitals Timeline (Continuous Telemetry)"
                hr_color = DEEP_NAVY
                spo2_color = EMERALD
            else:
                hr_y = patient["hr_fragmented"]
                spo2_y = patient["spo2_fragmented"]
                mode_str = "markers+lines"
                title_str = "24 Hour Vitals Timeline (Fragmented Spot Checks)"
                hr_color = SLATE
                spo2_color = CRIMSON
                
            fig15.add_trace(
                go.Scatter(x=time_x, y=hr_y, name="Heart Rate", mode=mode_str, line=dict(color=hr_color, width=3)),
                secondary_y=False,
            )
            fig15.add_trace(
                go.Scatter(x=time_x, y=spo2_y, name="SpO2", mode=mode_str, line=dict(color=spo2_color, width=3)),
                secondary_y=True,
            )
            
            fig15.update_layout(title_text=title_str)
            fig15.update_xaxes(title_text="Time")
            fig15.update_yaxes(title_text="Heart Rate (bpm)", secondary_y=False)
            fig15.update_yaxes(title_text="SpO2 (%)", secondary_y=True, range=[80, 100])
            fig15 = apply_corporate_theme(fig15)
            
            st.plotly_chart(fig15, use_container_width=True)
            
        with c2:
            # Deterioration Risk Score
            # Calculate a mock risk
            recent_hr = patient["hr_continuous"][-1]
            recent_spo2 = patient["spo2_continuous"][-1]
            
            risk_score = 30
            if recent_hr > 90: risk_score += 20
            if recent_spo2 < 94: risk_score += 30
            
            if activate_transformation:
                risk_score = max(10, risk_score - 40)
                gauge_color = EMERALD if risk_score < 40 else SLATE
            else:
                gauge_color = CRIMSON if risk_score > 60 else SLATE
                
            fig16 = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = risk_score,
                title = {'text': "Deterioration Risk Score"},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': gauge_color},
                    'steps': [
                        {'range': [0, 40], 'color': LIGHT_GREY},
                        {'range': [40, 100], 'color': LIGHT_GREY}
                    ]
                }
            ))
            fig16 = apply_corporate_theme(fig16)
            st.plotly_chart(fig16, use_container_width=True)
            
        if activate_transformation:
            st.success("Actionable Insight: Continuous AI telemetry confirms vitals are stable. Protocol suggests transitioning to lower acuity ward in 12 hours.")
        else:
            st.info("Actionable Insight: Blind spots exist between 4 hour nursing rounds. Patient is at risk of undetected deterioration.")
