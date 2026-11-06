"""
Unit tests for the Deterministic Verification and Rule Engine.
"""
import pytest
from src.models.report_schema import LabMeasurement, LabReport, TestStatus
from src.core.rule_engine import evaluate_measurement, evaluate_report, normalize_test_name


def test_alias_normalization():
    name, meta = normalize_test_name("hb")
    assert name == "Hemoglobin"
    assert meta is not None

    name2, meta2 = normalize_test_name("tlc")
    assert name2 == "White Blood Cell Count"

    name3, meta3 = normalize_test_name("s. cholesterol")
    assert name3 == "Total Cholesterol"


def test_normal_measurement():
    m = LabMeasurement(
        test_name="Hemoglobin",
        canonical_name="Hemoglobin",
        measured_value=14.2,
        unit="g/dL",
        ref_min=12.0,
        ref_max=16.0
    )
    evaluated = evaluate_measurement(m)
    assert evaluated.status == TestStatus.NORMAL
    assert not evaluated.is_critical


def test_low_and_high_measurements():
    low_m = LabMeasurement(
        test_name="Hemoglobin",
        canonical_name="Hemoglobin",
        measured_value=10.5,
        unit="g/dL",
        ref_min=12.0,
        ref_max=16.0
    )
    eval_low = evaluate_measurement(low_m)
    assert eval_low.status == TestStatus.LOW
    assert not eval_low.is_critical

    high_m = LabMeasurement(
        test_name="Total Cholesterol",
        canonical_name="Total Cholesterol",
        measured_value=245.0,
        unit="mg/dL",
        ref_min=0.0,
        ref_max=200.0
    )
    eval_high = evaluate_measurement(high_m)
    assert eval_high.status == TestStatus.HIGH
    assert not eval_high.is_critical


def test_critical_panic_thresholds():
    # Severe Anemia Panic value
    crit_hb = LabMeasurement(
        test_name="Hemoglobin",
        canonical_name="Hemoglobin",
        measured_value=6.2,
        unit="g/dL"
    )
    eval_crit = evaluate_measurement(crit_hb)
    assert eval_crit.status == TestStatus.CRITICAL_LOW
    assert eval_crit.is_critical is True

    # Critical Low Platelets
    crit_plt = LabMeasurement(
        test_name="Platelet Count",
        canonical_name="Platelet Count",
        measured_value=25000,
        unit="/µL"
    )
    eval_plt = evaluate_measurement(crit_plt)
    assert eval_plt.status == TestStatus.CRITICAL_LOW
    assert eval_plt.is_critical is True

    # Critical High Blood Sugar
    crit_sugar = LabMeasurement(
        test_name="Fasting Blood Glucose",
        canonical_name="Fasting Blood Glucose",
        measured_value=390,
        unit="mg/dL"
    )
    eval_sugar = evaluate_measurement(crit_sugar)
    assert eval_sugar.status == TestStatus.CRITICAL_HIGH
    assert eval_sugar.is_critical is True


def test_report_rollup_status():
    report_normal = LabReport(
        measurements=[
            LabMeasurement(test_name="Hemoglobin", canonical_name="Hemoglobin", measured_value=14.0, unit="g/dL", ref_min=12, ref_max=16)
        ]
    )
    assert evaluate_report(report_normal).overall_status == "NORMAL"

    report_attention = LabReport(
        measurements=[
            LabMeasurement(test_name="Hemoglobin", canonical_name="Hemoglobin", measured_value=10.5, unit="g/dL", ref_min=12, ref_max=16)
        ]
    )
    assert evaluate_report(report_attention).overall_status == "ATTENTION_NEEDED"

    report_crit = LabReport(
        measurements=[
            LabMeasurement(test_name="Platelet Count", canonical_name="Platelet Count", measured_value=20000, unit="/µL", ref_min=150000, ref_max=450000)
        ]
    )
    assert evaluate_report(report_crit).overall_status == "CRITICAL"
