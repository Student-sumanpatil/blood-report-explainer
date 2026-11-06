"""
Report Extraction and Ingestion Engine.
Parses digital PDFs, text tables, and images, returning structured LabReport objects.
Includes pre-configured authentic sample reports for immediate 1-click evaluation.
"""
import io
import re
from typing import List, Optional, Union
import pdfplumber

from src.models.report_schema import LabMeasurement, LabReport
from src.core.rule_engine import evaluate_report, normalize_test_name


class ReportExtractor:
    @staticmethod
    def extract_from_pdf(file_bytes: Union[bytes, io.BytesIO]) -> LabReport:
        """
        Parses text and tables from a digital PDF lab report using pdfplumber.
        """
        if isinstance(file_bytes, bytes):
            stream = io.BytesIO(file_bytes)
        else:
            stream = file_bytes

        extracted_text = ""
        with pdfplumber.open(stream) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"

        return ReportExtractor.extract_from_text(extracted_text)

    @staticmethod
    def extract_from_text(raw_text: str) -> LabReport:
        """
        Extracts structured measurements from raw report text via regex and tabular pattern matching.
        """
        measurements: List[LabMeasurement] = []
        lines = raw_text.split("\n")

        # Regex pattern matching:
        # Matches: "Hemoglobin 10.2 g/dL 12.0 - 15.0" or "WBC : 12500 /uL ( 4000 - 11000 )"
        pattern = re.compile(
            r"([A-Za-z0-9\s\.\-\(\)]+?)"                                # Test name
            r"[:\t\s]+"                                                 # Separator
            r"([0-9]+(?:\.[0-9]+)?)"                                     # Measured value
            r"\s*([a-zA-Z/%µuL\^0-9]+(?:\s*[a-zA-Z/%µuL\^0-9]+)?)"    # Unit
            r"(?:[^\d\n]*?([0-9]+(?:\.[0-9]+)?)\s*[-–toTO]+\s*([0-9]+(?:\.[0-9]+)?))?", # Optional range min - max
            re.IGNORECASE
        )

        for line in lines:
            line_str = line.strip()
            if not line_str or len(line_str) < 4:
                continue

            match = pattern.search(line_str)
            if match:
                test_name = match.group(1).strip()
                val_str = match.group(2).strip()
                unit_str = match.group(3).strip()
                ref_min = float(match.group(4)) if match.group(4) else None
                ref_max = float(match.group(5)) if match.group(5) else None

                # Discard table headers or non-test matches
                if test_name.lower() in ("test", "investigation", "parameter", "result", "normal", "reference"):
                    continue

                try:
                    val = float(val_str)
                    canonical, meta = normalize_test_name(test_name)
                    measurement = LabMeasurement(
                        test_name=test_name,
                        canonical_name=canonical,
                        measured_value=val,
                        unit=unit_str,
                        ref_min=ref_min,
                        ref_max=ref_max
                    )
                    measurements.append(measurement)
                except ValueError:
                    continue

        report = LabReport(
            report_id="EXTRACTED-001",
            patient_id="Anonymized Patient",
            measurements=measurements
        )
        return evaluate_report(report)

    @staticmethod
    def get_sample_report(sample_id: str) -> LabReport:
        """
        Returns authentic pre-built clinical sample panels for instant testing.
        """
        samples = {
            "cbc_anemia": LabReport(
                report_id="SAMPLE-CBC-01",
                patient_id="Patient A (Female, 32)",
                lab_name="Metropolis Healthcare",
                measurements=[
                    LabMeasurement(test_name="Hemoglobin", canonical_name="Hemoglobin", measured_value=9.4, unit="g/dL", ref_min=12.0, ref_max=15.0),
                    LabMeasurement(test_name="RBC Count", canonical_name="Red Blood Cell Count", measured_value=3.4, unit="million/µL", ref_min=4.0, ref_max=5.2),
                    LabMeasurement(test_name="Total WBC Count", canonical_name="White Blood Cell Count", measured_value=7200, unit="cells/µL", ref_min=4000, ref_max=11000),
                    LabMeasurement(test_name="Platelet Count", canonical_name="Platelet Count", measured_value=240000, unit="/µL", ref_min=150000, ref_max=450000),
                ]
            ),
            "lipid_cardiac": LabReport(
                report_id="SAMPLE-LIPID-02",
                patient_id="Patient B (Male, 48)",
                lab_name="Dr Lal PathLabs",
                measurements=[
                    LabMeasurement(test_name="Total Cholesterol", canonical_name="Total Cholesterol", measured_value=248, unit="mg/dL", ref_min=0, ref_max=200),
                    LabMeasurement(test_name="HDL Cholesterol", canonical_name="HDL Cholesterol", measured_value=34, unit="mg/dL", ref_min=40, ref_max=60),
                    LabMeasurement(test_name="LDL Cholesterol", canonical_name="LDL Cholesterol", measured_value=162, unit="mg/dL", ref_min=0, ref_max=100),
                    LabMeasurement(test_name="Triglycerides", canonical_name="Triglycerides", measured_value=260, unit="mg/dL", ref_min=0, ref_max=150),
                ]
            ),
            "diabetes_panel": LabReport(
                report_id="SAMPLE-DIAB-03",
                patient_id="Patient C (Female, 56)",
                lab_name="SRL Diagnostics",
                measurements=[
                    LabMeasurement(test_name="Fasting Blood Glucose", canonical_name="Fasting Blood Glucose", measured_value=142, unit="mg/dL", ref_min=70, ref_max=99),
                    LabMeasurement(test_name="Post Prandial Glucose", canonical_name="Postprandial Blood Glucose", measured_value=210, unit="mg/dL", ref_min=70, ref_max=140),
                    LabMeasurement(test_name="HbA1c", canonical_name="Glycated Hemoglobin (HbA1c)", measured_value=7.8, unit="%", ref_min=4.0, ref_max=5.6),
                ]
            ),
            "thyroid_panel": LabReport(
                report_id="SAMPLE-THYR-04",
                patient_id="Patient D (Female, 29)",
                lab_name="Thyrocare Technologies",
                measurements=[
                    LabMeasurement(test_name="TSH - Ultrasensitive", canonical_name="Thyroid-Stimulating Hormone (TSH)", measured_value=8.4, unit="µIU/mL", ref_min=0.4, ref_max=4.5),
                    LabMeasurement(test_name="Free T4", canonical_name="Free T4 (Thyroxine)", measured_value=0.72, unit="ng/dL", ref_min=0.8, ref_max=1.8),
                    LabMeasurement(test_name="Free T3", canonical_name="Free T3 (Triiodothyronine)", measured_value=2.8, unit="pg/mL", ref_min=2.3, ref_max=4.2),
                ]
            ),
            "critical_panic": LabReport(
                report_id="SAMPLE-CRIT-05",
                patient_id="Patient E (Emergency Walk-in)",
                lab_name="City Hospital Pathology",
                measurements=[
                    LabMeasurement(test_name="Platelet Count", canonical_name="Platelet Count", measured_value=22000, unit="/µL", ref_min=150000, ref_max=450000),
                    LabMeasurement(test_name="Hemoglobin", canonical_name="Hemoglobin", measured_value=6.4, unit="g/dL", ref_min=12.0, ref_max=16.0),
                    LabMeasurement(test_name="Fasting Glucose", canonical_name="Fasting Blood Glucose", measured_value=410, unit="mg/dL", ref_min=70, ref_max=99),
                ]
            ),
        }
        report = samples.get(sample_id, samples["cbc_anemia"])
        return evaluate_report(report)
