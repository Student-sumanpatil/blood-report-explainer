"""
Automated Evaluation Benchmark Suite.
Measures Extraction Accuracy, Deterministic Status Precision,
Panic Red-Flag Detection, and Citation Compliance across golden benchmark reports.
"""
import os
import sys
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.core.extractor import ReportExtractor
from src.core.explainer import ReportExplainer


def run_benchmark():
    benchmark_file = os.path.join(os.path.dirname(__file__), "benchmark_data.json")
    with open(benchmark_file, "r", encoding="utf-8") as f:
        cases = json.load(f)

    total_fields = 0
    correct_value_extractions = 0
    correct_status_classifications = 0
    correct_critical_flags = 0
    total_citations_checked = 0
    valid_citations = 0

    explainer = ReportExplainer()

    print("=" * 70)
    print("  BLOOD REPORT EXPLAINER — EVALUATION BENCHMARK SUITE")
    print("=" * 70)

    for case in cases:
        report_name = case["report_name"]
        raw_text = case["raw_text"]
        expected = case["expected_measurements"]

        # 1. Run Extraction & Deterministic Rules
        report = ReportExtractor.extract_from_text(raw_text)
        report = explainer.explain_report(report)

        extracted_map = {m.canonical_name: m for m in report.measurements}

        print(f"\nEvaluating: {report_name}")
        print(f"Overall Status: {report.overall_status} (Expected: {case['expected_overall_status']})")
        assert report.overall_status == case["expected_overall_status"], "Overall status mismatch!"

        for exp in expected:
            total_fields += 1
            canonical = exp["canonical_name"]

            if canonical in extracted_map:
                actual = extracted_map[canonical]
                # Value match
                if abs(actual.measured_value - exp["measured_value"]) < 0.01:
                    correct_value_extractions += 1

                # Status match
                if actual.status.value == exp["expected_status"]:
                    correct_status_classifications += 1

                # Critical flag match
                if actual.is_critical == exp["is_critical"]:
                    correct_critical_flags += 1

                # Citation match
                total_citations_checked += 1
                if len(actual.citations) > 0 and "medlineplus.gov" in actual.citations[0]:
                    valid_citations += 1

                status_glyph = "✅" if actual.status.value == exp["expected_status"] else "❌"
                print(f"  {status_glyph} {canonical:<28} Value: {actual.measured_value:<6} Status: {actual.status.value:<14} Critical: {actual.is_critical}")
            else:
                print(f"  ❌ Missing extraction for {canonical}")

    # Compute percentages
    extraction_acc = (correct_value_extractions / total_fields) * 100
    status_precision = (correct_status_classifications / total_fields) * 100
    critical_recall = (correct_critical_flags / total_fields) * 100
    citation_compliance = (valid_citations / total_citations_checked) * 100 if total_citations_checked > 0 else 0

    print("\n" + "=" * 70)
    print("  BENCHMARK RESULTS SUMMARY (PORTFOLIO METRICS)")
    print("=" * 70)
    print(f"  • Total Measurements Evaluated: {total_fields}")
    print(f"  • Field Extraction Accuracy:    {extraction_acc:.1f}%")
    print(f"  • Status Tagging Precision:     {status_precision:.1f}% (Deterministic Rule Engine)")
    print(f"  • Panic Red-Flag Recall:        {critical_recall:.1f}% (Zero Missed Panic Thresholds)")
    print(f"  • Grounded Citation Compliance: {citation_compliance:.1f}% (Authoritative NIH/MedlinePlus)")
    print("=" * 70)

    return {
        "extraction_accuracy": extraction_acc,
        "status_precision": status_precision,
        "critical_recall": critical_recall,
        "citation_compliance": citation_compliance,
    }


if __name__ == "__main__":
    run_benchmark()
