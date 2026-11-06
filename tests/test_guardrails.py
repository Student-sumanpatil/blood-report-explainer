"""
Unit tests for the Responsible AI Guardrail Engine.
"""
from src.core.guardrails import GuardrailEngine


def test_guardrails_catches_diagnostic_claims():
    bad_output = "Based on this hemoglobin level of 9.5, you have anemia. You need immediate intervention."
    is_safe, sanitized, violations = GuardrailEngine.audit_explanation(bad_output)

    assert not is_safe
    assert len(violations) > 0
    assert "you have anemia" not in sanitized.lower()
    assert "associated with or observed in" in sanitized


def test_guardrails_blocks_prescription_and_dosage():
    prescriptive_text = "Your blood sugar is 210. You should take 500mg metformin daily after meals."
    is_safe, sanitized, violations = GuardrailEngine.audit_explanation(prescriptive_text)

    assert not is_safe
    assert any("Prescriptive medication" in v for v in violations)
    assert "500mg" not in sanitized
    assert "Discuss treatments exclusively with your doctor" in sanitized


def test_guardrails_appends_educational_disclaimer():
    clean_text = "Hemoglobin transports oxygen from the lungs to peripheral tissues."
    is_safe, sanitized, violations = GuardrailEngine.audit_explanation(clean_text)

    assert is_safe
    assert len(violations) == 0
    assert "Educational Note:" in sanitized
