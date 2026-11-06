"""
FastAPI REST API Server for Blood Test Report Explainer.
Exposes endpoints for PDF/text ingestion, deterministic range evaluation,
and guarded RAG explanations with interactive Swagger docs (/docs).
"""
import io
import os
import sys
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure root directory is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models.report_schema import LabReport, LabMeasurement
from src.core.extractor import ReportExtractor
from src.core.rule_engine import evaluate_report, evaluate_measurement
from src.core.explainer import ReportExplainer
from src.core.rag_indexer import MedicalRAGRetriever

app = FastAPI(
    title="Blood Lab Report Explainer API",
    description="Deterministic verification, authoritative MedlinePlus RAG, and responsible AI guardrails.",
    version="1.0.0",
)

# Enable CORS for frontend clients (Streamlit, React, Next.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global shared retriever and explainer instance
retriever = MedicalRAGRetriever()
explainer = ReportExplainer(retriever=retriever)


class TextAnalysisRequest(BaseModel):
    raw_text: str = Field(..., description="Raw text of the lab report")
    language: str = Field(default="en", description="Target explanation language (en, hi, mr)")


class SampleInfo(BaseModel):
    id: str
    name: str
    description: str


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint reporting knowledge base status."""
    return {
        "status": "healthy",
        "service": "Blood Report Explainer REST API",
        "kb_chunks_indexed": len(retriever.chunks),
        "supported_languages": ["en", "hi", "mr"]
    }


@app.get("/api/samples", response_model=List[SampleInfo], tags=["Samples"])
def list_sample_reports():
    """Lists available authentic clinical sample panels."""
    return [
        SampleInfo(id="cbc_anemia", name="CBC Panel (Mild Anemia)", description="Low Hemoglobin and RBC with normal WBC and Platelets"),
        SampleInfo(id="lipid_cardiac", name="Lipid Panel (Elevated Cholesterol)", description="High Total Cholesterol, LDL, and Triglycerides with Low HDL"),
        SampleInfo(id="diabetes_panel", name="Glycemic Panel (Diabetic Range)", description="Elevated Fasting Glucose, Postprandial Glucose, and HbA1c"),
        SampleInfo(id="thyroid_panel", name="Thyroid Panel (Elevated TSH)", description="Elevated TSH with low-normal Free T4"),
        SampleInfo(id="critical_panic", name="Critical Panic Values", description="Severe low Platelets (<30k) and critical high Blood Glucose (>350)"),
    ]


@app.get("/api/samples/{sample_id}", response_model=LabReport, tags=["Samples"])
def get_sample_report(sample_id: str, language: str = "en"):
    """Fetches, evaluates, and explains a pre-configured sample panel."""
    try:
        report = ReportExtractor.get_sample_report(sample_id)
        return explainer.explain_report(report, language=language)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Sample '{sample_id}' not found: {str(e)}")


@app.post("/api/analyze-text", response_model=LabReport, tags=["Analysis"])
def analyze_raw_text(payload: TextAnalysisRequest):
    """
    Parses unstructured lab report text, deterministically verifies values,
    and returns guarded explanations with citations.
    """
    if not payload.raw_text.strip():
        raise HTTPException(status_code=400, detail="Report text cannot be empty.")

    report = ReportExtractor.extract_from_text(payload.raw_text)
    if not report.measurements:
        raise HTTPException(
            status_code=422,
            detail="No recognizable test measurements could be extracted from the provided text."
        )

    return explainer.explain_report(report, language=payload.language)


@app.post("/api/upload-pdf", response_model=LabReport, tags=["Analysis"])
async def upload_pdf_report(
    file: UploadFile = File(..., description="PDF blood report document"),
    language: str = Form(default="en", description="Target explanation language (en, hi, mr)")
):
    """
    Ingests a digital PDF report, extracts tables in-memory, deterministically verifies
    reference intervals, and returns guarded explanations.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        pdf_stream = io.BytesIO(content)
        report = ReportExtractor.extract_from_pdf(pdf_stream)
        if not report.measurements:
            raise HTTPException(
                status_code=422,
                detail="Could not extract tabular lab measurements from the uploaded PDF."
            )
        return explainer.explain_report(report, language=language)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")


@app.post("/api/evaluate-only", response_model=LabReport, tags=["Deterministic"])
def evaluate_measurements_only(measurements: List[LabMeasurement]):
    """
    Pure deterministic evaluation endpoint without LLM explanations.
    Calculates exact numerical statuses, critical red flags, and overall report risk.
    """
    report = LabReport(
        report_id="DETERMINISTIC-01",
        measurements=measurements
    )
    return evaluate_report(report)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
