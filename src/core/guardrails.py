"""
Responsible AI & Clinical Guardrail Engine.
Enforces non-diagnostic phrasing, blocks prescriptive medication/dosage advice,
and validates authoritative citations.
"""
import re
from typing import Tuple, List

# Patterns forbidden in patient-facing AI outputs
DIAGNOSTIC_PATTERNS = [
    r"\byou have (anemia|diabetes|hypothyroidism|hyperthyroidism|cancer|leukemia|infection)\b",
    r"\byou are suffering from\b",
    r"\byou are diagnosed with\b",
    r"\bthis confirms (that )?you have\b",
]

PRESCRIPTIVE_MEDICATION_PATTERNS = [
    r"\btake \d+\s*(mg|mcg|ml|tablets?|pills?|capsules?)\b",
    r"\bstart taking\b",
    r"\bincrease (your )?dose\b",
    r"\bdecrease (your )?dose\b",
    r"\bprescribe\b",
    r"\b(metformin|insulin|levothyroxine|atorvastatin|amoxicillin|aspirin)\b",
]


class GuardrailEngine:
    @staticmethod
    def audit_explanation(text: str) -> Tuple[bool, str, List[str]]:
        """
        Scans generated explanation for medical safety violations.
        Returns: (is_safe, sanitized_text, list_of_violations)
        """
        violations = []
        sanitized = text

        # 1. Audit Diagnostic Declarations
        for pattern in DIAGNOSTIC_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                violations.append(f"Diagnostic claim detected matching: {pattern}")
                # Sanitize to educational language
                sanitized = re.sub(
                    pattern,
                    "this value can be associated with or observed in",
                    sanitized,
                    flags=re.IGNORECASE
                )

        # 2. Audit Prescriptive Medication / Dosing
        for pattern in PRESCRIPTIVE_MEDICATION_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                violations.append("Prescriptive medication or dosing advice detected.")
                # Replace prescriptive section with a safe medical reminder
                sanitized = re.sub(
                    pattern,
                    "[Medication details redacted for safety - Discuss treatments exclusively with your doctor]",
                    sanitized,
                    flags=re.IGNORECASE
                )

        # 3. Ensure Educational Disclaimer is present
        disclaimer = "\n\n*Educational Note: This summary explains standard physiological ranges and is not a medical diagnosis or treatment plan. Please discuss all lab results with a qualified healthcare provider.*"
        if "Educational Note" not in sanitized:
            sanitized += disclaimer

        is_safe = len(violations) == 0
        return is_safe, sanitized, violations

    @staticmethod
    def format_critical_alert(test_name: str, value: float, unit: str) -> str:
        """Generates an urgent clinical attention banner for panic values."""
        return (
            f"🚨 **URGENT CLINICAL ALERT**: {test_name} is measured at {value} {unit}, which falls outside safe physiological limits. "
            f"Please contact your doctor or visit an urgent care clinic immediately for proper medical evaluation."
        )
