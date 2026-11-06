"""
Blood Test Report Explainer — Main Streamlit Application
A patient-centric, responsible AI lab report explainer with deterministic verification,
grounded RAG citations (MedlinePlus/NIH), and open model support (Meta Llama 3.3).
"""
import os
import streamlit as st
from dotenv import load_dotenv

from src.core.extractor import ReportExtractor
from src.core.explainer import ReportExplainer
from src.models.report_schema import TestStatus
from src.ui.components import render_privacy_banner, render_measurement_card

load_dotenv()

st.set_page_config(
    page_title="Blood Lab Report Explainer",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished medical look
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1e3a8a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4b5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border-radius: 8px;
        padding: 12px;
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar Configuration
st.sidebar.title("⚙️ Settings & Controls")

# Language Selection
language_labels = {
    "en": "English",
    "hi": "हिंदी (Hindi)",
    "mr": "मराठी (Marathi)"
}
selected_lang = st.sidebar.selectbox(
    "🌐 Explanation Language",
    options=["en", "hi", "mr"],
    format_func=lambda x: language_labels[x],
    index=0
)

# Open Model Inference Key
env_key = os.getenv("GROQ_API_KEY", "")
api_key_input = st.sidebar.text_input(
    "🔑 Groq API Key (Optional)",
    value=env_key if env_key != "your_groq_api_key_here" else "",
    type="password",
    help="Free open-model API key from console.groq.com. If omitted, smart offline fallback mode is used automatically."
)

if api_key_input:
    st.sidebar.success("⚡ Connected to Meta Llama 3.3 via Groq")
else:
    st.sidebar.info("💡 Running in Smart Offline Fallback Mode (Zero API calls)")

st.sidebar.divider()
st.sidebar.markdown(
    """
    **🛡️ Responsible AI Guardrails**:
    - 🧮 **Deterministic Engine**: Arithmetic & thresholds computed in pure Python
    - 📚 **Grounded RAG**: Curated from MedlinePlus & NIH
    - 🚫 **Strict Non-Diagnostic**: No disease pronouncements
    - 💊 **No Dosage Advice**: Medication prescriptions blocked
    - 🔒 **Zero Persistence**: Memory-only session
    """
)

# Main Title Header
st.markdown('<div class="main-header">🩸 Patient-Friendly Blood Report Explainer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Understand your laboratory results with deterministic accuracy, grounded medical references, and zero guesswork.</div>', unsafe_allow_html=True)

render_privacy_banner()

# Input Method Tabs
tab_sample, tab_upload, tab_paste = st.tabs(["🧪 Try Sample Reports", "📄 Upload PDF / Image", "✍️ Paste Report Text"])

report = None

with tab_sample:
    sample_choice = st.selectbox(
        "Select an authentic clinical test panel:",
        options=[
            ("cbc_anemia", "1. Complete Blood Count (CBC) — Mild Anemia Profile"),
            ("lipid_cardiac", "2. Lipid Profile — Elevated Total Cholesterol & Triglycerides"),
            ("diabetes_panel", "3. Glycemic Panel — High Fasting Glucose & HbA1c"),
            ("thyroid_panel", "4. Thyroid Function Test — Elevated TSH Profile"),
            ("critical_panic", "5. Urgent Panic Values — Low Platelets & Severe Glucose Alert"),
        ],
        format_func=lambda x: x[1]
    )
    if st.button("🚀 Analyze Sample Report", type="primary", use_container_width=True):
        with st.spinner("Extracting parameters and verifying ranges..."):
            report = ReportExtractor.get_sample_report(sample_choice[0])

with tab_upload:
    uploaded_file = st.file_uploader("Upload blood test report (PDF)", type=["pdf"])
    if uploaded_file is not None:
        if st.button("🚀 Extract & Analyze Uploaded PDF", type="primary", use_container_width=True):
            with st.spinner("Parsing PDF tables and evaluating ranges..."):
                report = ReportExtractor.extract_from_pdf(uploaded_file)

with tab_paste:
    raw_text_input = st.text_area(
        "Paste lab report text here:",
        height=140,
        placeholder="Example:\nHemoglobin: 11.2 g/dL (12.0 - 15.0)\nPlatelet Count: 180000 /uL (150000 - 450000)\nTotal Cholesterol: 235 mg/dL (0 - 200)"
    )
    if st.button("🚀 Analyze Pasted Text", type="primary", use_container_width=True):
        if raw_text_input.strip():
            with st.spinner("Parsing text parameters..."):
                report = ReportExtractor.extract_from_text(raw_text_input)
        else:
            st.warning("Please paste some report text first.")

# Processing & Display Results
if report is not None and report.measurements:
    # Run Explainer
    explainer = ReportExplainer(api_key=api_key_input)
    report = explainer.explain_report(report, language=selected_lang)

    st.markdown("### 📊 Clinical Overview & Executive Summary")

    # Metrics Summary Row
    total_tests = len(report.measurements)
    normal_tests = sum(1 for m in report.measurements if m.status == TestStatus.NORMAL)
    attention_tests = sum(1 for m in report.measurements if m.status in (TestStatus.LOW, TestStatus.HIGH))
    critical_tests = sum(1 for m in report.measurements if m.is_critical)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Parameters", total_tests)
    with col2:
        st.metric("🟢 Normal Range", normal_tests)
    with col3:
        st.metric("🟡 Outside Range", attention_tests)
    with col4:
        st.metric("🚨 Urgent / Critical", critical_tests)

    # Executive Summary Banner
    if report.overall_status == "CRITICAL":
        st.error(f"⚠️ **Attention Required**: {report.summary}")
    elif report.overall_status == "ATTENTION_NEEDED":
        st.warning(f"ℹ️ **Summary**: {report.summary}")
    else:
        st.success(f"✅ **Summary**: {report.summary}")

    st.markdown("---")
    st.markdown("### 📋 Detailed Biomarker Breakdown")

    # Render each test card
    for idx, measurement in enumerate(report.measurements):
        render_measurement_card(measurement, idx)

    # Exportable Doctor Discussion Checklist
    st.markdown("### 🩺 Doctor Discussion Checklist")
    st.markdown("Take these customized questions to your next physician appointment:")
    
    checklist_items = []
    for m in report.measurements:
        if m.questions_for_doctor and m.status != TestStatus.NORMAL:
            checklist_items.append(f"**{m.canonical_name} ({m.measured_value} {m.unit})**:")
            for q in m.questions_for_doctor:
                checklist_items.append(f"  - [ ] {q}")

    if checklist_items:
        checklist_str = "\n".join(checklist_items)
        st.text_area("Copy checklist for appointment:", value=checklist_str, height=180)
    else:
        st.info("All parameters are in normal ranges. Discuss routine wellness checks with your doctor.")

elif report is not None and not report.measurements:
    st.warning("No matching lab test parameters could be detected from the provided text. Please try one of the pre-loaded samples or check the formatting.")
