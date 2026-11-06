"""
Pydantic data models for blood lab measurements, report schemas, and status enumerations.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class TestStatus(str, Enum):
    __test__ = False  # Prevents pytest from attempting to collect this Enum as a test suite
    NORMAL = "NORMAL"
    LOW = "LOW"
    HIGH = "HIGH"
    CRITICAL_LOW = "CRITICAL_LOW"
    CRITICAL_HIGH = "CRITICAL_HIGH"
    UNKNOWN = "UNKNOWN"


class LabMeasurement(BaseModel):
    test_name: str = Field(..., description="Original name from report, e.g., 'Hb', 'Platelet Count'")
    canonical_name: str = Field(..., description="Normalized medical standard name, e.g., 'Hemoglobin'")
    measured_value: float = Field(..., description="Numerical measured value")
    unit: str = Field(..., description="Measurement unit, e.g., 'g/dL', 'cells/uL'")
    ref_min: Optional[float] = Field(None, description="Lower reference bound")
    ref_max: Optional[float] = Field(None, description="Upper reference bound")
    status: TestStatus = Field(default=TestStatus.UNKNOWN, description="Deterministic status evaluation")
    is_critical: bool = Field(default=False, description="True if value triggers medical red-flag threshold")
    explanation: Optional[str] = Field(None, description="Patient-friendly plain language explanation")
    citations: List[str] = Field(default_factory=list, description="Authoritative reference URLs or sources")
    questions_for_doctor: List[str] = Field(default_factory=list, description="Suggested questions for patient's physician")


class LabReport(BaseModel):
    report_id: str = Field(default="RPT-001")
    patient_id: Optional[str] = Field(default="Anonymized Patient")
    report_date: Optional[str] = Field(default=None)
    lab_name: Optional[str] = Field(default=None)
    measurements: List[LabMeasurement] = Field(default_factory=list)
    overall_status: str = Field(default="NORMAL", description="NORMAL, ATTENTION_NEEDED, or CRITICAL")
    language: str = Field(default="en", description="Target explanation language (en, hi, mr)")
    summary: Optional[str] = Field(None, description="Overall executive summary for the patient")
