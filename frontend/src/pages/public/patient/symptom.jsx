import React, { useState, useEffect } from "react";
import { useTheme } from "../ThemeContext";
import Sidebar from "./sidebar";
import {
  Activity,
  Sparkles,
  Search,
  Bell,
  Sun,
  Moon,
  ChevronDown,
  Plus,
  Trash2,
  ArrowRight,
  Clock3,
  CheckCircle2,
  Info,
  Loader2,
  AlertTriangle,
  ShieldAlert,
  X,
  TrendingUp,
  BarChart2,
} from "lucide-react";
import { useAuth } from "../../../_core/hooks/useAuth";
import aiService from "../../../services/aiService";

export default function SymptomAnalysis() {
  const { isDark, toggleTheme } = useTheme();
  const { user } = useAuth();

  // Input states
  const [inputText, setInputText] = useState("");
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);
  const [suggestedSymptoms, setSuggestedSymptoms] = useState([]);
  const [duration, setDuration] = useState("1-3 days");
  const [severity, setSeverity] = useState("Mild");
  const [ageGroup, setAgeGroup] = useState("Adult");

  // Analysis & Prediction state
  const [analyzing, setAnalyzing] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [analysisError, setAnalysisError] = useState("");

  // History state
  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);

  const quickSymptoms = [
    "Headache",
    "Fever",
    "Cough",
    "Fatigue",
    "Sore throat",
    "Nausea",
    "Dizziness",
    "Chest pain",
  ];

  const loadHistory = async () => {
    try {
      setLoadingHistory(true);
      const data = await aiService.getPredictionHistory();
      setHistory(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load prediction history:", err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  // Debounced auto-symptom parsing when user inputs text or selects symptoms
  useEffect(() => {
    const timer = setTimeout(async () => {
      const combined = [
        ...selectedSymptoms,
        ...(inputText.trim() ? [inputText.trim()] : []),
      ];
      if (combined.length === 0) {
        setSuggestedSymptoms([]);
        return;
      }
      try {
        const res = await aiService.parseSymptoms(
          inputText.trim() ? inputText : selectedSymptoms
        );
        if (res && res.suggested_symptoms) {
          setSuggestedSymptoms(
            res.suggested_symptoms.filter(
              (s) =>
                !selectedSymptoms.map((x) => x.toLowerCase()).includes(s.toLowerCase())
            )
          );
        }
      } catch (err) {
        // Silent parse error for typing
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [inputText, selectedSymptoms]);

  const toggleSymptom = (symptom) => {
    if (selectedSymptoms.includes(symptom)) {
      setSelectedSymptoms(selectedSymptoms.filter((s) => s !== symptom));
    } else {
      setSelectedSymptoms([...selectedSymptoms, symptom]);
    }
  };

  const handleClear = () => {
    setInputText("");
    setSelectedSymptoms([]);
    setSuggestedSymptoms([]);
    setPrediction(null);
    setAnalysisError("");
  };

  const handleAnalyze = async () => {
    const allSymptoms = [
      ...selectedSymptoms,
      ...(inputText.trim() ? [inputText.trim()] : []),
    ];

    if (allSymptoms.length === 0) {
      setAnalysisError("Please select or describe at least one symptom.");
      return;
    }

    try {
      setAnalyzing(true);
      setAnalysisError("");
      const payload = {
        symptoms: allSymptoms,
        patient_id: user?.id,
      };
      const result = await aiService.predictDisease(payload);
      setPrediction(result);
      loadHistory();
    } catch (err) {
      console.error("Prediction analysis failed:", err);
      setAnalysisError(
        err.response?.data?.error?.message ||
          err.response?.data?.detail ||
          "Failed to compute clinical prediction. Please check symptom inputs."
      );
    } finally {
      setAnalyzing(false);
    }
  };

  const patientName = user
    ? `${user.first_name || ""} ${user.last_name || ""}`.trim() || user.email.split("@")[0]
    : "Patient";

  return (
    <div style={styles.app}>
      <Sidebar darkMode={isDark} />

      {/* =====================================================
          MAIN PAGE
      ===================================================== */}
      <main style={styles.main}>
        {/* ===================================================
            HEADER
        =================================================== */}
        <header style={styles.header}>
          <div style={styles.heading}>
            <div style={styles.headingIcon}>
              <Activity size={25} />
            </div>

            <div>
              <h1 style={styles.title}>Symptom Analysis & CDSS</h1>
              <p style={styles.subtitle}>
                AI-assisted diagnostic assessment, differential ranking & SHAP feature attribution
              </p>
            </div>
          </div>

          <div style={styles.headerActions}>
            <div style={styles.search}>
              <Search size={17} color="var(--muted)" />
              <span style={styles.searchText}>Search clinical terms...</span>
              <span style={styles.searchShortcut}>⌘ K</span>
            </div>

            <button
              style={styles.headerIconButton}
              onClick={toggleTheme}
              type="button"
              aria-label="Toggle theme"
            >
              {isDark ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            <button
              style={{
                ...styles.headerIconButton,
                position: "relative",
              }}
              type="button"
            >
              <Bell size={18} />
              <span style={styles.notificationDot} />
            </button>

            <div style={styles.profile}>
              <div style={styles.profileAvatar}>
                {patientName.slice(0, 2).toUpperCase()}
              </div>

              <div style={styles.profileInfo}>
                <strong style={{ fontSize: "11px" }}>{patientName}</strong>
                <span style={{ fontSize: "9px", color: "var(--muted)" }}>Patient</span>
              </div>

              <ChevronDown size={15} color="#819496" />
            </div>
          </div>
        </header>

        {/* ===================================================
            CONTENT
        =================================================== */}
        <div style={styles.content}>
          <div style={styles.topGrid}>
            {/* ===============================================
                PANEL 1: DESCRIBE SYMPTOMS
            =============================================== */}
            <section style={styles.panel}>
              <div style={styles.panelHeader}>
                <div>
                  <h2 style={styles.panelTitle}>
                    <Sparkles size={18} />
                    Describe Your Symptoms
                  </h2>
                  <p style={styles.panelSubtitle}>
                    Select active symptoms or describe your clinical complaints in free text.
                  </p>
                </div>
              </div>

              {/* Quick Add Chips */}
              <div style={styles.quickLabel}>Quick add common symptoms</div>
              <div style={styles.quickSymptoms}>
                {quickSymptoms.map((symptom) => {
                  const active = selectedSymptoms.includes(symptom);
                  return (
                    <button
                      key={symptom}
                      type="button"
                      onClick={() => toggleSymptom(symptom)}
                      style={{
                        ...styles.symptomChip,
                        background: active ? "var(--accent-soft)" : "var(--card-soft)",
                        borderColor: active ? "var(--accent)" : "var(--border)",
                        color: active ? "var(--accent-medium)" : "var(--text-secondary)",
                      }}
                    >
                      <Plus size={12} />
                      {symptom}
                    </button>
                  );
                })}
              </div>

              {/* Free Text Input */}
              <div style={{ marginTop: "10px" }}>
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value.slice(0, 500))}
                  placeholder="Example: I have had a persistent mild cough, sore throat, and high fever for the past two days..."
                  style={{
                    width: "100%",
                    height: "100px",
                    boxSizing: "border-box",
                    padding: "12px",
                    border: "1px solid var(--border)",
                    borderRadius: "14px",
                    background: "var(--card-soft)",
                    color: "var(--text)",
                    fontSize: "11px",
                    outline: "none",
                    resize: "none",
                    fontFamily: "inherit",
                  }}
                />
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "9px", color: "var(--muted)", marginTop: "3px" }}>
                  <span>
                    {selectedSymptoms.length > 0 && (
                      <strong>Selected tags: {selectedSymptoms.join(", ")}</strong>
                    )}
                  </span>
                  <span>{inputText.length}/500</span>
                </div>
              </div>

              {/* Suggested Symptoms */}
              {suggestedSymptoms.length > 0 && (
                <div style={{ marginTop: "6px" }}>
                  <span style={{ fontSize: "9px", color: "var(--muted-strong)" }}>
                    Related symptom suggestions:
                  </span>
                  <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "4px" }}>
                    {suggestedSymptoms.slice(0, 5).map((s) => (
                      <button
                        key={s}
                        type="button"
                        onClick={() => toggleSymptom(s)}
                        style={{
                          fontSize: "8px",
                          padding: "2px 7px",
                          borderRadius: "6px",
                          border: "1px dashed var(--accent)",
                          background: "var(--accent-soft)",
                          color: "var(--accent-medium)",
                          cursor: "pointer",
                        }}
                      >
                        + {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Context Selector Fields */}
              <div style={styles.fields}>
                <div style={styles.field}>
                  <label style={styles.fieldLabel}>Duration</label>
                  <select
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                    style={styles.select}
                  >
                    <option>Less than 24h</option>
                    <option>1-3 days</option>
                    <option>4-7 days</option>
                    <option>More than a week</option>
                  </select>
                </div>

                <div style={styles.field}>
                  <label style={styles.fieldLabel}>Severity</label>
                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value)}
                    style={styles.select}
                  >
                    <option>Mild</option>
                    <option>Moderate</option>
                    <option>Severe</option>
                  </select>
                </div>

                <div style={styles.field}>
                  <label style={styles.fieldLabel}>Age Group</label>
                  <select
                    value={ageGroup}
                    onChange={(e) => setAgeGroup(e.target.value)}
                    style={styles.select}
                  >
                    <option>Pediatric (0-17)</option>
                    <option>Adult (18-64)</option>
                    <option>Senior (65+)</option>
                  </select>
                </div>
              </div>

              {/* Error Banner */}
              {analysisError && (
                <div style={{ marginTop: "10px", padding: "8px", borderRadius: "8px", background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.2)", color: "#ef4444", fontSize: "10px", display: "flex", alignItems: "center", gap: "6px" }}>
                  <AlertTriangle size={14} />
                  <span>{analysisError}</span>
                </div>
              )}

              {/* Action Buttons */}
              <div style={styles.actionRow}>
                <button
                  type="button"
                  disabled={analyzing}
                  onClick={handleAnalyze}
                  style={{
                    ...styles.analyzeButton,
                    opacity: analyzing ? 0.7 : 1,
                    cursor: analyzing ? "not-allowed" : "pointer",
                    color: "#ffffff",
                  }}
                >
                  {analyzing ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Computing ML Inference...
                    </>
                  ) : (
                    <>
                      <Sparkles size={16} />
                      Analyze Symptoms
                    </>
                  )}
                </button>

                <button
                  type="button"
                  onClick={handleClear}
                  style={styles.clearButton}
                >
                  <Trash2 size={15} />
                  Clear
                </button>
              </div>

              {/* Mandatory Clinical Notice */}
              <div style={styles.disclaimer}>
                <Info size={15} style={{ flexShrink: 0 }} />
                <span>
                  This tool provides automated clinical decision support for informational and triage purposes only. It is not a definitive medical diagnosis. Seek professional medical care for emergencies.
                </span>
              </div>
            </section>

            {/* ===============================================
                PANEL 2: AI ASSESSMENT & SHAP ATTRIBUTION
            =============================================== */}
            <section style={{ ...styles.panel, display: "flex", flexDirection: "column" }}>
              <div style={styles.assessmentHeader}>
                <div>
                  <h2 style={styles.panelTitle}>AI Clinical Assessment</h2>
                  <p style={styles.panelSubtitle}>
                    Disease classification & SHAP explainability model
                  </p>
                </div>
                <span style={styles.aiBadge}>
                  <Sparkles size={12} />
                  CDSS AI
                </span>
              </div>

              {analyzing ? (
                <div style={styles.assessmentContent}>
                  <Loader2 size={40} className="animate-spin text-emerald-400 mb-3" />
                  <h3 style={styles.readyTitle}>Evaluating Symptoms</h3>
                  <p style={styles.readyText}>
                    Running multi-label disease classifier and computing Shapley feature attributions...
                  </p>
                </div>
              ) : prediction ? (
                <div style={{ flex: 1, minHeight: 0, overflowY: "auto", paddingRight: "4px", marginTop: "10px" }}>
                  {/* Top Prediction Badge */}
                  <div
                    style={{
                      padding: "12px",
                      borderRadius: "12px",
                      background: "var(--card-soft)",
                      border: "1px solid var(--border)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <div>
                      <span style={{ fontSize: "8px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--muted-strong)", fontWeight: 700 }}>
                        Most Likely Condition
                      </span>
                      <h3 style={{ margin: "2px 0 0", fontSize: "16px", fontWeight: 700, color: "var(--text)" }}>
                        {prediction.predicted_condition}
                      </h3>
                    </div>

                    <div style={{ textAlign: "right" }}>
                      <span
                        style={{
                          display: "inline-block",
                          padding: "3px 8px",
                          borderRadius: "999px",
                          fontSize: "9px",
                          fontWeight: 700,
                          background:
                            prediction.severity === "high" || prediction.severity === "critical"
                              ? "rgba(239, 68, 68, 0.15)"
                              : prediction.severity === "moderate"
                              ? "rgba(245, 158, 11, 0.15)"
                              : "rgba(16, 185, 129, 0.15)",
                          color:
                            prediction.severity === "high" || prediction.severity === "critical"
                              ? "#ef4444"
                              : prediction.severity === "moderate"
                              ? "#f59e0b"
                              : "#10b981",
                          border: "1px solid currentColor",
                          textTransform: "capitalize",
                        }}
                      >
                        {prediction.severity} severity
                      </span>
                      <div style={{ marginTop: "3px", fontSize: "11px", fontWeight: 700, color: "var(--accent-medium)" }}>
                        {Math.round((prediction.confidence || 0) * 100)}% confidence
                      </div>
                    </div>
                  </div>

                  {/* Recommendation */}
                  {prediction.recommendation && (
                    <div style={{ marginTop: "10px", padding: "10px", borderRadius: "10px", background: "var(--accent-soft)", border: "1px solid var(--accent)", color: "var(--text)", fontSize: "10px", lineHeight: 1.4 }}>
                      <strong>Clinical Recommendation:</strong> {prediction.recommendation}
                    </div>
                  )}

                  {/* SHAP Feature Attribution Visualization */}
                  <div style={{ marginTop: "14px" }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
                      <span style={{ fontSize: "10px", fontWeight: 700, color: "var(--text)", display: "flex", alignItems: "center", gap: "5px" }}>
                        <BarChart2 size={13} />
                        SHAP Feature Attribution
                      </span>
                      <span style={{ fontSize: "8px", color: "var(--muted)" }}>
                        Base value: {prediction.shap_explanations?.base_value ? Math.round(prediction.shap_explanations.base_value * 100) : 10}%
                      </span>
                    </div>

                    <div style={{ background: "var(--card-soft)", border: "1px solid var(--border)", borderRadius: "10px", padding: "8px 10px" }}>
                      {prediction.shap_explanations?.features && prediction.shap_explanations.features.length > 0 ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: "7px" }}>
                          {prediction.shap_explanations.features.slice(0, 5).map((f, i) => {
                            const isIncrease = f.direction === "increases_risk" || f.contribution > 0;
                            const absContrib = Math.min(100, Math.max(10, Math.round(Math.abs(f.contribution) * 100)));

                            return (
                              <div key={i}>
                                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "9px", marginBottom: "2px" }}>
                                  <span style={{ fontWeight: 600, color: "var(--text)", textTransform: "capitalize" }}>
                                    {f.feature}
                                  </span>
                                  <span
                                    style={{
                                      fontWeight: 700,
                                      color: isIncrease ? "#ef4444" : "#10b981",
                                    }}
                                  >
                                    {isIncrease ? `+${f.contribution.toFixed(2)} (Increases Risk)` : `${f.contribution.toFixed(2)} (Protective)`}
                                  </span>
                                </div>
                                <div style={{ height: "6px", width: "100%", background: "var(--border)", borderRadius: "3px", overflow: "hidden" }}>
                                  <div
                                    style={{
                                      height: "100%",
                                      width: `${absContrib}%`,
                                      background: isIncrease
                                        ? "linear-gradient(90deg, #f59e0b, #ef4444)"
                                        : "linear-gradient(90deg, #06b6d4, #10b981)",
                                      borderRadius: "3px",
                                      transition: "width 0.5s ease-in-out",
                                    }}
                                  />
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <span style={{ fontSize: "9px", color: "var(--muted)" }}>
                          No individual feature attributions recorded.
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Differential Diagnoses (Ranked candidates) */}
                  {prediction.ranked_diagnoses && prediction.ranked_diagnoses.length > 1 && (
                    <div style={{ marginTop: "12px" }}>
                      <span style={{ fontSize: "9px", fontWeight: 700, color: "var(--muted-strong)", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                        Differential Diagnoses
                      </span>
                      <div style={{ marginTop: "4px", display: "flex", flexDirection: "column", gap: "4px" }}>
                        {prediction.ranked_diagnoses.slice(1, 4).map((d, idx) => (
                          <div
                            key={idx}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "space-between",
                              padding: "5px 8px",
                              borderRadius: "6px",
                              background: "var(--card-soft)",
                              fontSize: "9px",
                            }}
                          >
                            <span style={{ color: "var(--text)" }}>{d.disease}</span>
                            <span style={{ fontWeight: 700, color: "var(--muted)" }}>
                              {Math.round(d.probability * 100)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Non-removable Regulatory Disclaimer Banner */}
                  <div
                    style={{
                      marginTop: "12px",
                      padding: "8px",
                      borderRadius: "8px",
                      border: "1px solid rgba(245, 158, 11, 0.3)",
                      background: "rgba(245, 158, 11, 0.08)",
                      color: "var(--text-secondary)",
                      fontSize: "8px",
                      lineHeight: 1.4,
                      display: "flex",
                      gap: "6px",
                      alignItems: "flex-start",
                    }}
                  >
                    <ShieldAlert size={14} style={{ color: "#f59e0b", flexShrink: 0, marginTop: "1px" }} />
                    <span>
                      {prediction.disclaimer ||
                        "This prediction is generated by an automated clinical decision support system for informational and triage purposes only. Consult a licensed medical practitioner for clinical evaluation."}
                    </span>
                  </div>
                </div>
              ) : (
                <div style={styles.assessmentContent}>
                  <div style={styles.assessmentIcon}>
                    <Activity size={34} />
                  </div>

                  <h3 style={styles.readyTitle}>Ready to analyze</h3>
                  <p style={styles.readyText}>
                    Select or describe symptoms and click “Analyze Symptoms”
                    to receive ML predictions with SHAP explainability.
                  </p>

                  <div style={styles.tipsBox}>
                    <h4 style={styles.tipsTitle}>
                      <Sparkles size={14} />
                      Tips for better results
                    </h4>
                    <Tip text="Be specific about your primary symptoms" />
                    <Tip text="Indicate how long you've experienced them" />
                    <Tip text="Select duration and severity filters" />
                  </div>
                </div>
              )}
            </section>
          </div>

          {/* =================================================
              RECENT ANALYSES — DATABASE BACKED
          ================================================= */}
          <section style={styles.recentPanel}>
            <div style={styles.recentHeader}>
              <div>
                <h2 style={styles.panelTitle}>
                  <Clock3 size={17} />
                  Recent Prediction History
                </h2>
                <p style={styles.panelSubtitle}>
                  Historical clinical evaluations and diagnostic assessments stored in your chart
                </p>
              </div>

              <button style={styles.viewAll} onClick={loadHistory} type="button">
                Refresh Log
              </button>
            </div>

            <div style={styles.tableContainer}>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={{ width: "15%" }}>RECORDED DATE</th>
                    <th style={{ width: "30%" }}>INPUT SYMPTOMS</th>
                    <th style={{ width: "25%" }}>PREDICTED CONDITION</th>
                    <th style={{ width: "15%" }}>CONFIDENCE</th>
                    <th style={{ width: "15%" }}>ACTION</th>
                  </tr>
                </thead>

                <tbody>
                  {loadingHistory ? (
                    <tr>
                      <td colSpan="5" style={{ textAlign: "center", padding: "16px", color: "var(--muted)" }}>
                        Loading prediction history from database...
                      </td>
                    </tr>
                  ) : history.length === 0 ? (
                    <tr>
                      <td colSpan="5" style={{ textAlign: "center", padding: "16px", color: "var(--muted)" }}>
                        No past symptom predictions on record. Run your first analysis above.
                      </td>
                    </tr>
                  ) : (
                    history.slice(0, 4).map((item) => {
                      const inputSyms =
                        item.input_data?.canonical_symptoms ||
                        (Array.isArray(item.input_data?.symptoms_input)
                          ? item.input_data.symptoms_input
                          : [String(item.input_data?.symptoms_input || "Symptoms")]);

                      const dateStr = item.created_at
                        ? new Date(item.created_at).toLocaleDateString("en-US", {
                            day: "numeric",
                            month: "short",
                            year: "numeric",
                          })
                        : "Recent";

                      return (
                        <tr key={item.id}>
                          <td style={styles.tableDate}>{dateStr}</td>
                          <td>
                            <div style={styles.tableSymptoms}>
                              {inputSyms.slice(0, 3).map((sym, idx) => (
                                <span key={idx} style={styles.tableSymptom}>
                                  {sym}
                                </span>
                              ))}
                              {inputSyms.length > 3 && (
                                <span style={{ fontSize: "8px", color: "var(--muted)" }}>
                                  +{inputSyms.length - 3} more
                                </span>
                              )}
                            </div>
                          </td>

                          <td style={styles.assessmentName}>
                            {item.predicted_condition}
                          </td>

                          <td>
                            <span style={styles.risk}>
                              {Math.round((item.confidence || 0) * 100)}%
                            </span>
                          </td>

                          <td>
                            <button
                              type="button"
                              onClick={() => {
                                setPrediction({
                                  predicted_condition: item.predicted_condition,
                                  confidence: item.confidence,
                                  severity: item.explanation?.severity || "moderate",
                                  recommendation: item.explanation?.recommendation || "",
                                  shap_explanations: item.explanation?.shap_attributions || {},
                                  ranked_diagnoses: item.explanation?.ranked_diagnoses || [],
                                  disclaimer: item.disclaimer || "",
                                });
                              }}
                              style={styles.reportButton}
                            >
                              Load View
                              <ArrowRight size={14} />
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

/* ===========================================================
   SMALL COMPONENTS
=========================================================== */

function Tip({ text }) {
  return (
    <div style={styles.tip}>
      <CheckCircle2 size={13} />
      <span>{text}</span>
    </div>
  );
}

/* ===========================================================
   ALL STYLES — PRESERVING 100% OF EXISTING PATTERNS
=========================================================== */

const styles = {
  app: {
    width: "100vw",
    height: "100vh",
    minHeight: "100vh",
    display: "flex",
    overflow: "hidden",
    background: "var(--bg)",
    color: "var(--text)",
    fontFamily:
      "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  },

  main: {
    marginLeft: "255px",
    flex: 1,
    minWidth: 0,
    height: "100vh",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },

  header: {
    height: "92px",
    minHeight: "92px",
    padding: "16px 28px",
    boxSizing: "border-box",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    borderBottom: "1px solid var(--border)",
  },

  heading: {
    display: "flex",
    alignItems: "center",
    gap: "13px",
  },

  headingIcon: {
    width: "47px",
    height: "47px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: "13px",
    background: "var(--accent)",
    border: "1px solid var(--accent)",
    color: "#d9fffb",
  },

  title: {
    margin: 0,
    fontSize: "25px",
    lineHeight: 1.1,
    letterSpacing: "-0.5px",
    fontWeight: 700,
  },

  subtitle: {
    margin: "4px 0 0",
    color: "var(--muted)",
    fontSize: "11px",
  },

  headerActions: {
    display: "flex",
    alignItems: "center",
    gap: "9px",
  },

  search: {
    width: "285px",
    height: "42px",
    boxSizing: "border-box",
    display: "flex",
    alignItems: "center",
    gap: "9px",
    padding: "0 11px",
    border: "1px solid var(--border)",
    borderRadius: "10px",
    background: "var(--card-soft)",
  },

  searchText: {
    flex: 1,
    color: "var(--muted)",
    fontSize: "11px",
  },

  searchShortcut: {
    padding: "4px 6px",
    borderRadius: "5px",
    background: "var(--card-hover)",
    color: "var(--muted)",
    fontSize: "9px",
  },

  headerIconButton: {
    width: "42px",
    height: "42px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    border: "1px solid var(--border)",
    borderRadius: "10px",
    background: "var(--card-soft)",
    color: "var(--text-secondary)",
    cursor: "pointer",
  },

  notificationDot: {
    position: "absolute",
    top: "8px",
    right: "8px",
    width: "6px",
    height: "6px",
    borderRadius: "50%",
    background: "#46d0c2",
  },

  profile: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginLeft: "4px",
  },

  profileAvatar: {
    width: "38px",
    height: "38px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: "50%",
    background: "linear-gradient(135deg, #778398, #414c5c)",
    color: "#fff",
    fontSize: "10px",
    fontWeight: 600,
  },

  profileInfo: {
    display: "flex",
    flexDirection: "column",
    gap: "1px",
    minWidth: "57px",
  },

  content: {
    flex: 1,
    minHeight: 0,
    padding: "14px 28px 17px",
    boxSizing: "border-box",
    display: "flex",
    flexDirection: "column",
    gap: "13px",
    overflow: "hidden",
  },

  topGrid: {
    flex: "0 0 455px",
    minHeight: 0,
    display: "grid",
    gridTemplateColumns: "1.4fr 1.15fr",
    gap: "13px",
  },

  panel: {
    minWidth: 0,
    minHeight: 0,
    boxSizing: "border-box",
    padding: "18px",
    border: "1px solid var(--border)",
    borderRadius: "16px",
    background: "var(--card)",
    overflow: "hidden",
  },

  panelHeader: {
    display: "flex",
    alignItems: "flex-start",
  },

  panelTitle: {
    margin: 0,
    display: "flex",
    alignItems: "center",
    gap: "8px",
    color: "var(--text)",
    fontSize: "16px",
    fontWeight: 650,
  },

  panelSubtitle: {
    margin: "4px 0 0",
    color: "var(--muted)",
    fontSize: "10px",
    lineHeight: 1.4,
  },

  quickLabel: {
    marginTop: "10px",
    marginBottom: "5px",
    color: "var(--muted-strong)",
    fontSize: "9px",
  },

  quickSymptoms: {
    display: "flex",
    gap: "6px",
    overflowX: "auto",
    whiteSpace: "nowrap",
    paddingBottom: "2px",
  },

  symptomChip: {
    height: "28px",
    flexShrink: 0,
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
    padding: "0 8px",
    border: "1px solid var(--border)",
    borderRadius: "8px",
    background: "var(--card-soft)",
    color: "var(--text-secondary)",
    fontSize: "9px",
    cursor: "pointer",
    transition: "all 0.15s ease",
  },

  fields: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr",
    gap: "9px",
    marginTop: "9px",
  },

  field: {
    minWidth: 0,
  },

  fieldLabel: {
    display: "block",
    marginBottom: "4px",
    color: "var(--muted-strong)",
    fontSize: "9px",
  },

  select: {
    width: "100%",
    height: "34px",
    boxSizing: "border-box",
    padding: "0 8px",
    border: "1px solid var(--border)",
    borderRadius: "8px",
    background: "var(--card-soft)",
    color: "var(--text-secondary)",
    fontSize: "10px",
    outline: "none",
  },

  actionRow: {
    display: "flex",
    gap: "9px",
    marginTop: "10px",
  },

  analyzeButton: {
    flex: 1,
    height: "38px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "7px",
    border: 0,
    borderRadius: "9px",
    background: "var(--accent)",
    color: "#ffffff",
    fontSize: "11px",
    fontWeight: 600,
  },

  clearButton: {
    width: "95px",
    height: "38px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "6px",
    border: "1px solid var(--border-soft)",
    borderRadius: "9px",
    background: "transparent",
    color: "var(--text-secondary)",
    fontSize: "10px",
    cursor: "pointer",
  },

  disclaimer: {
    minHeight: "32px",
    boxSizing: "border-box",
    marginTop: "9px",
    padding: "5px 8px",
    display: "flex",
    alignItems: "center",
    gap: "7px",
    border: "1px solid #5a4d22",
    borderRadius: "8px",
    background: "var(--card-soft)",
    color: "#ad9f6d",
    fontSize: "8px",
    lineHeight: 1.3,
  },

  assessmentHeader: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
  },

  aiBadge: {
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
    padding: "5px 8px",
    borderRadius: "7px",
    background: "var(--accent-soft)",
    color: "var(--accent-medium)",
    fontSize: "9px",
    fontWeight: 600,
  },

  assessmentContent: {
    height: "calc(100% - 50px)",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    textAlign: "center",
  },

  assessmentIcon: {
    width: "60px",
    height: "60px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: "10px",
    border: "1px solid var(--accent)",
    borderRadius: "50%",
    background: "var(--accent-surface)",
    color: "var(--text)",
  },

  readyTitle: {
    margin: 0,
    color: "var(--text)",
    fontSize: "15px",
    fontWeight: 600,
  },

  readyText: {
    margin: "6px 0 14px",
    color: "var(--muted)",
    fontSize: "9px",
    lineHeight: 1.6,
  },

  tipsBox: {
    width: "100%",
    boxSizing: "border-box",
    padding: "11px",
    border: "1px solid var(--border)",
    borderRadius: "12px",
    textAlign: "left",
    background: "var(--card-soft)",
  },

  tipsTitle: {
    margin: "0 0 7px",
    display: "flex",
    alignItems: "center",
    gap: "6px",
    color: "var(--text)",
    fontSize: "10px",
    fontWeight: 600,
  },

  tip: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    marginTop: "6px",
    color: "var(--muted)",
    fontSize: "8px",
  },

  recentPanel: {
    flex: 1,
    minHeight: 0,
    boxSizing: "border-box",
    padding: "14px 17px",
    display: "flex",
    flexDirection: "column",
    border: "1px solid var(--border)",
    borderRadius: "16px",
    background: "var(--card)",
    overflow: "hidden",
  },

  recentHeader: {
    flexShrink: 0,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },

  viewAll: {
    height: "30px",
    padding: "0 10px",
    border: "1px solid var(--border-soft)",
    borderRadius: "8px",
    background: "transparent",
    color: "var(--text-secondary)",
    fontSize: "9px",
    cursor: "pointer",
  },

  tableContainer: {
    flex: 1,
    minHeight: 0,
    marginTop: "8px",
    border: "1px solid var(--border)",
    borderRadius: "10px",
    overflowY: "auto",
  },

  table: {
    width: "100%",
    borderCollapse: "collapse",
    tableLayout: "fixed",
  },

  tableDate: {
    color: "var(--text-secondary)",
  },

  tableSymptoms: {
    display: "flex",
    gap: "4px",
    flexWrap: "wrap",
  },

  tableSymptom: {
    padding: "2px 6px",
    borderRadius: "4px",
    background: "var(--card-soft)",
    color: "var(--accent-medium)",
    border: "1px solid var(--border)",
    fontSize: "8px",
  },

  assessmentName: {
    color: "var(--text-secondary)",
    fontWeight: 600,
  },

  risk: {
    display: "inline-flex",
    padding: "3px 7px",
    borderRadius: "999px",
    background: "var(--accent-soft)",
    color: "var(--accent-medium)",
    border: "1px solid var(--accent)",
    fontSize: "8px",
    fontWeight: 700,
  },

  reportButton: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "flex-end",
    gap: "4px",
    border: 0,
    background: "transparent",
    color: "var(--accent-medium)",
    fontSize: "9px",
    cursor: "pointer",
    fontWeight: 600,
  },
};