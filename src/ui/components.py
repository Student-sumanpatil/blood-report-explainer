"""
UI Components for the Blood Report Explainer Streamlit application.
Renders responsive medical cards, range indicators, badges, and doctor checklists.
"""
import streamlit as st
from src.models.report_schema import LabMeasurement, TestStatus


def render_privacy_banner():
    st.markdown(
        """
        <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 10px 16px; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.2rem;">🔒</span>
                <div>
                    <strong style="color: #166534;">Private & Ephemeral Processing:</strong>
                    <span style="color: #15803d; font-size: 0.95rem;">
                        Your lab reports are parsed purely in-memory. Zero health data or personal files are persisted to any database or disk.
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def get_status_badge(status: TestStatus, is_critical: bool) -> str:
    if is_critical or status in (TestStatus.CRITICAL_LOW, TestStatus.CRITICAL_HIGH):
        return '<span style="background-color: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 9999px; font-weight: 600; font-size: 0.85rem; border: 1px solid #f87171;">🚨 CRITICAL / URGENT</span>'
    elif status == TestStatus.LOW:
        return '<span style="background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 9999px; font-weight: 600; font-size: 0.85rem; border: 1px solid #fcd34d;">🟡 LOW</span>'
    elif status == TestStatus.HIGH:
        return '<span style="background-color: #ffedd5; color: #9a3412; padding: 4px 10px; border-radius: 9999px; font-weight: 600; font-size: 0.85rem; border: 1px solid #fdba74;">🟠 HIGH</span>'
    elif status == TestStatus.NORMAL:
        return '<span style="background-color: #dcfce7; color: #166534; padding: 4px 10px; border-radius: 9999px; font-weight: 600; font-size: 0.85rem; border: 1px solid #86efac;">🟢 NORMAL</span>'
    else:
        return '<span style="background-color: #f3f4f6; color: #374151; padding: 4px 10px; border-radius: 9999px; font-weight: 600; font-size: 0.85rem;">⚪ UNKNOWN</span>'


def render_measurement_card(m: LabMeasurement, idx: int):
    badge_html = get_status_badge(m.status, m.is_critical)
    ref_str = f"{m.ref_min} - {m.ref_max} {m.unit}" if (m.ref_min is not None and m.ref_max is not None) else "Standard interval not specified"

    with st.container():
        st.markdown(
            f"""
            <div style="background-color: white; border: 1px solid #e5e7eb; border-radius: 10px; padding: 18px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
                    <div>
                        <h4 style="margin: 0; color: #111827; font-size: 1.15rem;">{m.canonical_name}</h4>
                        <span style="color: #6b7280; font-size: 0.85rem;">Report label: {m.test_name}</span>
                    </div>
                    <div>{badge_html}</div>
                </div>
                <div style="display: flex; gap: 24px; margin-bottom: 12px; font-size: 0.95rem;">
                    <div><strong>Measured Value:</strong> <span style="font-size: 1.1rem; color: #1f2937; font-weight: 700;">{m.measured_value} {m.unit}</span></div>
                    <div><strong>Reference Range:</strong> <span style="color: #4b5563;">{ref_str}</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Explanation box
        if m.explanation:
            st.info(m.explanation)

        # Questions for Doctor
        if m.questions_for_doctor:
            with st.expander(f"🩺 Questions to Ask Your Doctor about {m.canonical_name}", expanded=False):
                for q in m.questions_for_doctor:
                    st.markdown(f"- **{q}**")

        # Source Citation
        if m.citations:
            st.caption(f"📚 Grounded Reference: [{m.citations[0]}]({m.citations[0]})")
        
        st.divider()
