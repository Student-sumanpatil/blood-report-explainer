"""
Deterministic verification and rule engine for blood test measurements.
Performs arithmetic comparison against reference ranges and critical alert thresholds.
Guarantees 100% deterministic status tagging without relying on LLM logic.
"""
from typing import Dict, Any, Optional, Tuple
from src.models.report_schema import LabMeasurement, LabReport, TestStatus

# Canonical test registry with standard clinical defaults and panic values
CANONICAL_TESTS: Dict[str, Dict[str, Any]] = {
    "hemoglobin": {
        "canonical_name": "Hemoglobin",
        "aliases": ["hb", "hgb", "hemoglobin", "haemoglobin", "s. hemoglobin"],
        "default_min": 12.0,
        "default_max": 17.0,
        "default_unit": "g/dL",
        "critical_low": 7.0,
        "critical_high": 20.0,
    },
    "white_blood_cells": {
        "canonical_name": "White Blood Cell Count",
        "aliases": ["wbc", "tlc", "total leukocyte count", "leukocytes", "white blood cells", "total wbc"],
        "default_min": 4000.0,
        "default_max": 11000.0,
        "default_unit": "cells/µL",
        "critical_low": 2000.0,
        "critical_high": 30000.0,
    },
    "platelets": {
        "canonical_name": "Platelet Count",
        "aliases": ["plt", "platelets", "platelet count", "thrombocytes", "total platelets"],
        "default_min": 150000.0,
        "default_max": 450000.0,
        "default_unit": "/µL",
        "critical_low": 30000.0,
        "critical_high": 1000000.0,
    },
    "rbc": {
        "canonical_name": "Red Blood Cell Count",
        "aliases": ["rbc", "red blood cell", "erythrocytes", "total rbc"],
        "default_min": 4.0,
        "default_max": 5.9,
        "default_unit": "million/µL",
        "critical_low": 2.0,
        "critical_high": 7.5,
    },
    "total_cholesterol": {
        "canonical_name": "Total Cholesterol",
        "aliases": ["total cholesterol", "cholesterol total", "s. cholesterol", "serum cholesterol"],
        "default_min": 0.0,
        "default_max": 200.0,
        "default_unit": "mg/dL",
        "critical_low": None,
        "critical_high": 350.0,
    },
    "hdl_cholesterol": {
        "canonical_name": "HDL Cholesterol",
        "aliases": ["hdl", "hdl cholesterol", "good cholesterol", "serum hdl"],
        "default_min": 40.0,
        "default_max": 100.0,
        "default_unit": "mg/dL",
        "critical_low": 25.0,
        "critical_high": None,
    },
    "ldl_cholesterol": {
        "canonical_name": "LDL Cholesterol",
        "aliases": ["ldl", "ldl cholesterol", "bad cholesterol", "calculated ldl"],
        "default_min": 0.0,
        "default_max": 100.0,
        "default_unit": "mg/dL",
        "critical_low": None,
        "critical_high": 250.0,
    },
    "triglycerides": {
        "canonical_name": "Triglycerides",
        "aliases": ["triglycerides", "serum triglycerides", "tg"],
        "default_min": 0.0,
        "default_max": 150.0,
        "default_unit": "mg/dL",
        "critical_low": None,
        "critical_high": 500.0,  # Acute pancreatitis risk
    },
    "fasting_glucose": {
        "canonical_name": "Fasting Blood Glucose",
        "aliases": ["fasting blood glucose", "fasting blood sugar", "fbs", "fasting glucose", "glucose fasting", "sugar fasting"],
        "default_min": 70.0,
        "default_max": 99.0,
        "default_unit": "mg/dL",
        "critical_low": 54.0,   # Severe hypoglycemia
        "critical_high": 350.0, # Severe hyperglycemia
    },
    "postprandial_glucose": {
        "canonical_name": "Postprandial Blood Glucose",
        "aliases": ["ppbs", "pp blood sugar", "post prandial glucose", "glucose pp", "2hr post prandial"],
        "default_min": 70.0,
        "default_max": 140.0,
        "default_unit": "mg/dL",
        "critical_low": 54.0,
        "critical_high": 350.0,
    },
    "hba1c": {
        "canonical_name": "Glycated Hemoglobin (HbA1c)",
        "aliases": ["hba1c", "glycated hemoglobin", "glycosylated hemoglobin", "hemoglobin a1c"],
        "default_min": 4.0,
        "default_max": 5.6,
        "default_unit": "%",
        "critical_low": None,
        "critical_high": 12.0,
    },
    "tsh": {
        "canonical_name": "Thyroid-Stimulating Hormone (TSH)",
        "aliases": ["tsh", "thyrotropin", "s. tsh", "serum tsh", "ultrasensitive tsh"],
        "default_min": 0.40,
        "default_max": 4.50,
        "default_unit": "µIU/mL",
        "critical_low": 0.01,
        "critical_high": 20.0,
    },
    "free_t4": {
        "canonical_name": "Free T4 (Thyroxine)",
        "aliases": ["free t4", "ft4", "free thyroxine"],
        "default_min": 0.8,
        "default_max": 1.8,
        "default_unit": "ng/dL",
        "critical_low": 0.3,
        "critical_high": 4.0,
    },
    "free_t3": {
        "canonical_name": "Free T3 (Triiodothyronine)",
        "aliases": ["free t3", "ft3", "free triiodothyronine"],
        "default_min": 2.3,
        "default_max": 4.2,
        "default_unit": "pg/mL",
        "critical_low": 1.0,
        "critical_high": 10.0,
    },
}


def normalize_test_name(raw_name: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Maps a raw test string from an OCR/report to its canonical medical name.
    """
    cleaned = raw_name.strip().lower()
    
    # 1. Exact match on canonical name
    for _, meta in CANONICAL_TESTS.items():
        if meta["canonical_name"].lower() == cleaned:
            return meta["canonical_name"], meta

    # 2. Exact match on alias
    for _, meta in CANONICAL_TESTS.items():
        for alias in meta["aliases"]:
            if alias == cleaned:
                return meta["canonical_name"], meta

    # 3. Substring match on alias
    for _, meta in CANONICAL_TESTS.items():
        for alias in meta["aliases"]:
            if alias in cleaned:
                return meta["canonical_name"], meta

    return raw_name.strip().title(), None


def evaluate_measurement(measurement: LabMeasurement) -> LabMeasurement:
    """
    Deterministically compares measured value against min, max, and panic thresholds.
    """
    canonical_name, meta = normalize_test_name(measurement.test_name)
    measurement.canonical_name = canonical_name

    val = measurement.measured_value
    # Use lab's own reported min/max if present; otherwise fall back to canonical defaults
    min_val = measurement.ref_min if measurement.ref_min is not None else (meta["default_min"] if meta else None)
    max_val = measurement.ref_max if measurement.ref_max is not None else (meta["default_max"] if meta else None)

    # Unit fallback if missing
    if (not measurement.unit or measurement.unit.strip() == "") and meta:
        measurement.unit = meta["default_unit"]

    measurement.ref_min = min_val
    measurement.ref_max = max_val

    # Check critical panic thresholds first
    is_critical = False
    if meta:
        crit_low = meta.get("critical_low")
        crit_high = meta.get("critical_high")

        if crit_low is not None and val <= crit_low:
            measurement.status = TestStatus.CRITICAL_LOW
            measurement.is_critical = True
            return measurement
        elif crit_high is not None and val >= crit_high:
            measurement.status = TestStatus.CRITICAL_HIGH
            measurement.is_critical = True
            return measurement

    # Standard range comparison
    if min_val is not None and val < min_val:
        measurement.status = TestStatus.LOW
        measurement.is_critical = False
    elif max_val is not None and val > max_val:
        measurement.status = TestStatus.HIGH
        measurement.is_critical = False
    elif min_val is not None or max_val is not None:
        measurement.status = TestStatus.NORMAL
        measurement.is_critical = False
    else:
        measurement.status = TestStatus.UNKNOWN
        measurement.is_critical = False

    return measurement


def evaluate_report(report: LabReport) -> LabReport:
    """
    Evaluates every measurement in the report and sets the overall risk status.
    """
    evaluated_measurements = []
    has_critical = False
    has_abnormal = False

    for m in report.measurements:
        eval_m = evaluate_measurement(m)
        evaluated_measurements.append(eval_m)
        if eval_m.is_critical:
            has_critical = True
        elif eval_m.status in (TestStatus.LOW, TestStatus.HIGH):
            has_abnormal = True

    report.measurements = evaluated_measurements

    if has_critical:
        report.overall_status = "CRITICAL"
    elif has_abnormal:
        report.overall_status = "ATTENTION_NEEDED"
    else:
        report.overall_status = "NORMAL"

    return report
