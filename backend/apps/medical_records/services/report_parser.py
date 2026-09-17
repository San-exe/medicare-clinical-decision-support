import re
from typing import Union, List, Dict, Any, Optional


def extract_text_from_stream(content: Union[str, bytes]) -> str:
    """
    Extracts plain text from string, raw bytes, or simple PDF byte streams.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, bytes):
        # Check if PDF
        if content.startswith(b"%PDF"):
            text_chunks = []
            # Extract PDF stream text literals (e.g. (text) Tj or /Text (text))
            matches = re.findall(rb"\(([^\(\)]*)\)\s*(?:Tj|TJ|\')?", content)
            for m in matches:
                try:
                    decoded = m.decode("utf-8", errors="ignore").strip()
                    if decoded and len(decoded) > 1:
                        text_chunks.append(decoded)
                except Exception:
                    pass

            if text_chunks:
                return " ".join(text_chunks)

            # Fallback: decode printable ASCII
            printable = re.sub(rb"[^\x20-\x7E\r\n\t]", b" ", content)
            return printable.decode("utf-8", errors="ignore")

        return content.decode("utf-8", errors="replace")

    return str(content)


def classify_blood_pressure(systolic: float, diastolic: float) -> tuple[str, str]:
    """Classifies blood pressure per AHA/ACC clinical guidelines."""
    if systolic >= 180 or diastolic >= 120:
        return "critical", "Hypertensive crisis. Immediate emergency clinical attention advised."
    if systolic >= 140 or diastolic >= 90:
        return "high", "Stage 2 Hypertension. Clinical management recommended."
    if systolic >= 130 or diastolic >= 80:
        return "elevated", "Stage 1 Hypertension or elevated reading."
    if systolic < 90 or diastolic < 60:
        return "low", "Hypotension reading."
    return "normal", "Blood pressure within normal clinical limits."


def classify_glucose(val: float) -> tuple[str, str]:
    """Classifies blood glucose reading in mg/dL."""
    if val >= 300 or val < 54:
        return "critical", "Severe hypoglycemia/hyperglycemia alert."
    if val >= 126:
        return "high", "Fasting glucose indicates diabetic range."
    if val >= 100:
        return "elevated", "Impaired fasting glucose (prediabetic range)."
    if val < 70:
        return "low", "Hypoglycemic range."
    return "normal", "Normal fasting glucose."


def classify_hba1c(val: float) -> tuple[str, str]:
    """Classifies HbA1c percentage."""
    if val >= 10.0:
        return "critical", "Severely elevated glycation index."
    if val >= 6.5:
        return "high", "Diabetic diagnostic threshold (HbA1c >= 6.5%)."
    if val >= 5.7:
        return "elevated", "Prediabetic range (5.7% - 6.4%)."
    return "normal", "Normal glycemic regulation (< 5.7%)."


def classify_cholesterol(val: float) -> tuple[str, str]:
    """Classifies Total Cholesterol in mg/dL."""
    if val >= 300:
        return "critical", "Markedly elevated total cholesterol."
    if val >= 240:
        return "high", "High total cholesterol."
    if val >= 200:
        return "elevated", "Borderline elevated cholesterol."
    return "normal", "Desirable total cholesterol (< 200 mg/dL)."


def classify_ldl(val: float) -> tuple[str, str]:
    """Classifies LDL cholesterol in mg/dL."""
    if val >= 190:
        return "critical", "Very high LDL. Increased cardiovascular event risk."
    if val >= 160:
        return "high", "High LDL cholesterol."
    if val >= 130:
        return "elevated", "Borderline high LDL."
    return "normal", "Optimal/desirable LDL cholesterol."


def classify_hdl(val: float) -> tuple[str, str]:
    """Classifies HDL cholesterol in mg/dL."""
    if val < 40:
        return "low", "Low HDL cholesterol (cardiovascular risk factor)."
    return "normal", "Protective HDL level (>= 40 mg/dL)."


def classify_triglycerides(val: float) -> tuple[str, str]:
    """Classifies Triglycerides in mg/dL."""
    if val >= 500:
        return "critical", "Very high triglycerides. Pancreatitis risk."
    if val >= 200:
        return "high", "High triglyceride level."
    if val >= 150:
        return "elevated", "Borderline high triglycerides."
    return "normal", "Normal triglyceride level (< 150 mg/dL)."


def classify_hemoglobin(val: float) -> tuple[str, str]:
    """Classifies Hemoglobin in g/dL."""
    if val < 7.0 or val > 20.0:
        return "critical", "Critical hemoglobin requiring urgent attention."
    if val < 12.0:
        return "low", "Low hemoglobin (anemic range)."
    if val > 17.5:
        return "high", "Elevated hemoglobin / polycythemia."
    return "normal", "Hemoglobin within normal reference range."


def classify_platelets(val: float) -> tuple[str, str]:
    """Classifies Platelet count."""
    # Normalize if given in thousands (e.g. 250 -> 250,000)
    actual = val * 1000 if val < 1000 else val
    if actual < 50000:
        return "critical", "Severe thrombocytopenia alert."
    if actual < 150000:
        return "low", "Mild to moderate thrombocytopenia."
    if actual > 450000:
        return "high", "Thrombocytosis."
    return "normal", "Platelet count within standard clinical limits."


def classify_wbc(val: float) -> tuple[str, str]:
    """Classifies WBC count."""
    # Normalize if given in units (e.g. 8.5 -> 8500 or 8.5)
    actual = val if val < 50 else val / 1000.0
    if actual < 2.0 or actual > 30.0:
        return "critical", "Critical leukopenia/leukocytosis alert."
    if actual < 4.0:
        return "low", "Leukopenia."
    if actual > 11.0:
        return "high", "Leukocytosis (potential infection/inflammation)."
    return "normal", "WBC within normal limits."


def classify_creatinine(val: float) -> tuple[str, str]:
    """Classifies Serum Creatinine in mg/dL."""
    if val > 4.0:
        return "critical", "Critical renal impairment indicator."
    if val > 1.3:
        return "high", "Elevated creatinine. Potential reduced GFR."
    if val < 0.6:
        return "low", "Low serum creatinine."
    return "normal", "Serum creatinine within normal renal reference."


def extract_metrics_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extracts key quantitative metrics and reference range flags from text using regex.
    """
    metrics = []

    # 1. Blood Pressure: e.g. "135/88", "BP: 120/80 mmHg"
    bp_match = re.search(
        r"(?:blood\s*pressure|b\.?p\.?)?[:\s]*\b([0-9]{2,3})\s*[/]\s*([0-9]{2,3})\s*(?:mm\s*hg)?\b",
        text,
        re.IGNORECASE,
    )
    if bp_match:
        sys_val = float(bp_match.group(1))
        dia_val = float(bp_match.group(2))
        flag, note = classify_blood_pressure(sys_val, dia_val)
        metrics.append({
            "test_name": "Blood Pressure",
            "value": f"{int(sys_val)}/{int(dia_val)}",
            "unit": "mmHg",
            "reference_range": "90-120 / 60-80",
            "flag": flag,
            "clinical_note": note,
        })

    # 2. Glucose / Fasting Blood Sugar
    fbs_match = re.search(
        r"(?:fasting\s*(?:blood)?\s*(?:sugar|glucose)|fbs|blood\s*glucose|glucose)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(?:mg\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if fbs_match:
        val = float(fbs_match.group(1))
        flag, note = classify_glucose(val)
        metrics.append({
            "test_name": "Fasting Blood Glucose",
            "value": str(val),
            "unit": "mg/dL",
            "reference_range": "70-99",
            "flag": flag,
            "clinical_note": note,
        })

    # 3. HbA1c
    hba1c_match = re.search(
        r"(?:hba1c|glycated\s*hemoglobin|a1c)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*%?",
        text,
        re.IGNORECASE,
    )
    if hba1c_match:
        val = float(hba1c_match.group(1))
        flag, note = classify_hba1c(val)
        metrics.append({
            "test_name": "HbA1c",
            "value": str(val),
            "unit": "%",
            "reference_range": "< 5.7",
            "flag": flag,
            "clinical_note": note,
        })

    # 4. Total Cholesterol
    chol_match = re.search(
        r"(?:total\s*cholesterol|cholesterol)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(?:mg\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if chol_match:
        val = float(chol_match.group(1))
        flag, note = classify_cholesterol(val)
        metrics.append({
            "test_name": "Total Cholesterol",
            "value": str(val),
            "unit": "mg/dL",
            "reference_range": "< 200",
            "flag": flag,
            "clinical_note": note,
        })

    # 5. LDL Cholesterol
    ldl_match = re.search(
        r"(?:ldl(?:\s*cholesterol)?|bad\s*cholesterol)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(?:mg\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if ldl_match:
        val = float(ldl_match.group(1))
        flag, note = classify_ldl(val)
        metrics.append({
            "test_name": "LDL Cholesterol",
            "value": str(val),
            "unit": "mg/dL",
            "reference_range": "< 100",
            "flag": flag,
            "clinical_note": note,
        })

    # 6. HDL Cholesterol
    hdl_match = re.search(
        r"(?:hdl(?:\s*cholesterol)?|good\s*cholesterol)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(?:mg\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if hdl_match:
        val = float(hdl_match.group(1))
        flag, note = classify_hdl(val)
        metrics.append({
            "test_name": "HDL Cholesterol",
            "value": str(val),
            "unit": "mg/dL",
            "reference_range": ">= 40",
            "flag": flag,
            "clinical_note": note,
        })

    # 7. Triglycerides
    tg_match = re.search(
        r"(?:triglycerides|trigs)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(?:mg\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if tg_match:
        val = float(tg_match.group(1))
        flag, note = classify_triglycerides(val)
        metrics.append({
            "test_name": "Triglycerides",
            "value": str(val),
            "unit": "mg/dL",
            "reference_range": "< 150",
            "flag": flag,
            "clinical_note": note,
        })

    # 8. Hemoglobin
    hb_match = re.search(
        r"(?:hemoglobin|hb|hgb)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(?:g\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if hb_match:
        val = float(hb_match.group(1))
        flag, note = classify_hemoglobin(val)
        metrics.append({
            "test_name": "Hemoglobin",
            "value": str(val),
            "unit": "g/dL",
            "reference_range": "12.0-17.5",
            "flag": flag,
            "clinical_note": note,
        })

    # 9. Platelets
    plt_match = re.search(
        r"(?:platelets?|platelet\s*count|plt)[:\s]*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(?:x10\^?[0-9]*/u[lL]|cells/mc[lL]|/mc[lL]|k/u[lL])?",
        text,
        re.IGNORECASE,
    )
    if plt_match:
        raw_val = plt_match.group(1).replace(",", "")
        val = float(raw_val)
        flag, note = classify_platelets(val)
        metrics.append({
            "test_name": "Platelet Count",
            "value": str(int(val * 1000 if val < 1000 else val)),
            "unit": "cells/mcL",
            "reference_range": "150,000-450,000",
            "flag": flag,
            "clinical_note": note,
        })

    # 10. White Blood Cells (WBC)
    wbc_match = re.search(
        r"(?:white\s*blood\s*(?:cells?|count)|wbc|leukocytes?)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(?:x10\^?[0-9]*/u[lL]|/mc[lL])?",
        text,
        re.IGNORECASE,
    )
    if wbc_match:
        val = float(wbc_match.group(1))
        flag, note = classify_wbc(val)
        metrics.append({
            "test_name": "White Blood Cell Count",
            "value": str(val),
            "unit": "x10^3/mcL",
            "reference_range": "4.0-11.0",
            "flag": flag,
            "clinical_note": note,
        })

    # 11. Serum Creatinine
    cr_match = re.search(
        r"(?:serum\s*creatinine|creatinine)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(?:mg\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if cr_match:
        val = float(cr_match.group(1))
        flag, note = classify_creatinine(val)
        metrics.append({
            "test_name": "Serum Creatinine",
            "value": str(val),
            "unit": "mg/dL",
            "reference_range": "0.6-1.3",
            "flag": flag,
            "clinical_note": note,
        })

    return metrics


def parse_report_content(content: Union[str, bytes], title: str = "") -> Dict[str, Any]:
    """
    Main parser entrypoint. Accepts raw text or binary stream, extracts metrics,
    and returns a structured clinical summary.
    """
    text = extract_text_from_stream(content)
    metrics = extract_metrics_from_text(text)

    abnormal_metrics = [m for m in metrics if m["flag"] != "normal"]
    critical_metrics = [m for m in metrics if m["flag"] == "critical"]

    summary_lines = []
    if title:
        summary_lines.append(f"Clinical Report Analysis for '{title}':")
    summary_lines.append(f"Total metrics identified: {len(metrics)}.")

    if critical_metrics:
        crit_names = ", ".join(m["test_name"] for m in critical_metrics)
        summary_lines.append(f"CRITICAL WARNING: Critical alerts for {crit_names}.")
    elif abnormal_metrics:
        abn_names = ", ".join(m["test_name"] for m in abnormal_metrics)
        summary_lines.append(f"Attention required: Abnormal findings detected for {abn_names}.")
    else:
        summary_lines.append("All extracted clinical indicators are within standard reference ranges.")

    return {
        "extracted_text": text.strip(),
        "metrics": metrics,
        "total_metrics_extracted": len(metrics),
        "abnormal_flags_count": len(abnormal_metrics),
        "critical_flags_count": len(critical_metrics),
        "summary": " ".join(summary_lines),
    }
