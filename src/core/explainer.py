"""
Grounded Patient-Centric Explainer Engine with Open Model Support (Groq / Meta Llama 3.3).
Synthesizes clear explanations in English, Hindi, and Marathi based on deterministic statuses,
grounded MedlinePlus context, and strict safety guardrails.
"""
import os
from typing import Optional, List
from dotenv import load_dotenv

from src.models.report_schema import LabMeasurement, LabReport, TestStatus
from src.core.rag_indexer import MedicalRAGRetriever
from src.core.guardrails import GuardrailEngine

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_LLM_MODEL", "llama-3.3-70b-versatile")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()


class ReportExplainer:
    def __init__(self, retriever: Optional[MedicalRAGRetriever] = None, api_key: Optional[str] = None):
        self.retriever = retriever or MedicalRAGRetriever()
        self.api_key = api_key or GROQ_API_KEY
        self.client = None
        if self.api_key and self.api_key != "your_groq_api_key_here":
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except Exception:
                self.client = None

    def explain_measurement(self, m: LabMeasurement, language: str = "en") -> LabMeasurement:
        """
        Enriches a single measurement with patient-friendly explanations, citations, and doctor questions.
        """
        # Retrieve authoritative medical context
        chunk = self.retriever.retrieve(m.canonical_name or m.test_name)
        source_url = chunk.source_url if chunk else "https://medlineplus.gov/lab-tests/"
        m.citations = [source_url]

        # Extract doctor questions from knowledge base if available
        if chunk and "Questions for Your Doctor" in chunk.content:
            questions_text = chunk.content.split("Questions for Your Doctor")[-1]
            questions = [q.strip("- *").strip() for q in questions_text.split("\n") if q.strip().startswith(("-", "*"))]
            m.questions_for_doctor = questions[:3]
        else:
            m.questions_for_doctor = [
                f"What could be contributing to my {m.canonical_name} level of {m.measured_value} {m.unit}?",
                "Do you recommend repeating this test or scheduling any follow-up tests?"
            ]

        # Determine explanation content
        if self.client:
            raw_explanation = self._call_open_model(m, chunk.content if chunk else "", language)
        else:
            raw_explanation = self._deterministic_template_explanation(m, chunk.content if chunk else "", language)

        # Apply Safety Guardrails
        is_safe, sanitized, violations = GuardrailEngine.audit_explanation(raw_explanation)

        # Prepend critical alert if panic threshold is breached
        if m.is_critical:
            alert_prefix = GuardrailEngine.format_critical_alert(m.canonical_name, m.measured_value, m.unit)
            sanitized = f"{alert_prefix}\n\n{sanitized}"

        m.explanation = sanitized
        return m

    def explain_report(self, report: LabReport, language: str = "en") -> LabReport:
        """
        Explains every measurement in the report and adds an overall summary.
        """
        report.language = language
        for m in report.measurements:
            self.explain_measurement(m, language=language)

        # Generate summary
        attention_items = [m.canonical_name for m in report.measurements if m.status in (TestStatus.LOW, TestStatus.HIGH, TestStatus.CRITICAL_LOW, TestStatus.CRITICAL_HIGH)]
        
        if language == "hi":
            if not attention_items:
                report.summary = "आपके रक्त परीक्षण के सभी मान सामान्य सीमा के भीतर हैं। अपने डॉक्टर से नियमित स्वास्थ्य जांच पर चर्चा करें।"
            else:
                report.summary = f"जांच परिणाम: {len(report.measurements)} में से {len(attention_items)} परीक्षणों ({', '.join(attention_items)}) पर ध्यान देने की आवश्यकता है। कृपया डॉक्टर से परामर्श लें।"
        elif language == "mr":
            if not attention_items:
                report.summary = "तुमच्या रक्त तपासणीचे सर्व मूल्ये सामान्य मर्यादेत आहेत. नियमित तपासणीसाठी डॉक्टरांचा सल्ला घ्या."
            else:
                report.summary = f"तपासणी निकाल: {len(report.measurements)} पैकी {len(attention_items)} चाचण्यांवर ({', '.join(attention_items)}) लक्ष देणे आवश्यक आहे. कृपया डॉक्टरांशी संपर्क साधा."
        else:
            if not attention_items:
                report.summary = f"All {len(report.measurements)} lab measurements fall within standard reference intervals. Keep maintaining a balanced diet and regular checkups."
            else:
                report.summary = (
                    f"Out of {len(report.measurements)} tests, {len(attention_items)} item(s) "
                    f"({', '.join(attention_items)}) are outside standard ranges. "
                    "Review the detailed cards below and discuss these findings with your doctor."
                )

        return report

    def _call_open_model(self, m: LabMeasurement, kb_context: str, language: str) -> str:
        """Calls Groq Llama 3.3 with strict system instructions."""
        lang_prompts = {
            "en": "Explain in simple, encouraging English for a patient without medical training.",
            "hi": "Explain in clear, simple conversational Hindi (Devanagari script) so an Indian patient can easily understand.",
            "mr": "Explain in clear, simple conversational Marathi (Devanagari script) so a patient in Maharashtra can easily understand.",
        }
        lang_instruction = lang_prompts.get(language, lang_prompts["en"])

        system_prompt = (
            "You are a compassionate, patient-first lab report educator. Follow these rules strictly:\n"
            "1. NEVER give a medical diagnosis (do not say 'you have X disease'). Say 'this level is often observed when...'.\n"
            "2. NEVER prescribe drugs, treatments, or dosages.\n"
            "3. Rely only on the provided authoritative context.\n"
            f"4. Language requirement: {lang_instruction}"
        )

        user_content = (
            f"Test: {m.canonical_name} ({m.test_name})\n"
            f"Measured Value: {m.measured_value} {m.unit}\n"
            f"Reference Interval: {m.ref_min} - {m.ref_max} {m.unit}\n"
            f"Evaluated Status: {m.status.value}\n\n"
            f"Authoritative Context from MedlinePlus:\n{kb_context}\n\n"
            "Provide a 2 to 3 sentence patient-friendly explanation of what this test measures and what this status typically means."
        )

        try:
            response = self.client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.2,
                max_tokens=250
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return self._deterministic_template_explanation(m, kb_context, language)

    def _deterministic_template_explanation(self, m: LabMeasurement, kb_context: str, language: str) -> str:
        """
        Lightweight fallback explanation when offline or no API key is set.
        Guarantees zero downtime and instant local evaluation.
        """
        status = m.status.value

        if language == "hi":
            status_hi = "कम" if "LOW" in status else ("अधिक" if "HIGH" in status else "सामान्य")
            return (
                f"{m.canonical_name} का स्तर {m.measured_value} {m.unit} दर्ज किया गया है, "
                f"जो सामान्य सीमा ({m.ref_min} - {m.ref_max} {m.unit}) की तुलना में {status_hi} है। "
                f"यह परीक्षण शरीर के सामान्य संतुलन को समझने में मदद करता है।"
            )
        elif language == "mr":
            status_mr = "कमी" if "LOW" in status else ("जास्त" if "HIGH" in status else "सामान्य")
            return (
                f"{m.canonical_name} ची पातळी {m.measured_value} {m.unit} नोंदवली गेली आहे, "
                f"जी सामान्य मर्यादेच्या ({m.ref_min} - {m.ref_max} {m.unit}) तुलनेत {status_mr} आहे. "
                f"या निकालाची अचूक माहिती घेण्यासाठी डॉक्टरांशी चर्चा करा."
            )
        else:
            status_desc = "lower than" if "LOW" in status else ("higher than" if "HIGH" in status else "within")
            return (
                f"{m.canonical_name} is measured at {m.measured_value} {m.unit}, which is {status_desc} "
                f"the standard reference range ({m.ref_min} to {m.ref_max} {m.unit}). "
                f"Physicians evaluate this biomarker to understand overall physiological health."
            )
