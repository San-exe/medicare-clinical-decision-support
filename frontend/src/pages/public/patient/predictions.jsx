import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Sidebar from "../patient/sidebar";
import {
  Activity,
  AlertTriangle,
  Bell,
  Brain,
  CalendarDays,
  ChevronDown,
  CircleDot,
  ClipboardList,
  FileText,
  Heart,
  Home,
  Info,
  LogIn,
  Moon,
  Pill,
  Search,
  Settings,
  ShieldAlert,
  Sparkles,
  Stethoscope,
  Sun,
  TrendingUp,
  UserRound,
  X,
} from "lucide-react";

const baselineRisks = [
  {
    id: "cardio",
    title: "Cardiovascular Risk",
    score: 18,
    level: "Low",
    description: "Current indicators suggest a relatively low short-term cardiovascular risk.",
    factors: ["Blood pressure within target", "Stable resting heart rate", "Healthy BMI"],
  },
  {
    id: "diabetes",
    title: "Diabetes Risk",
    score: 22,
    level: "Low",
    description: "Recent glucose values are broadly within the expected range.",
    factors: ["Glucose 102 mg/dL", "No recent abnormal trend", "BMI 23.4 kg/m²"],
  },
  {
    id: "respiratory",
    title: "Respiratory Risk",
    score: 31,
    level: "Moderate",
    description: "Recent symptom history suggests monitoring respiratory symptoms is useful.",
    factors: ["Occasional cough history", "No persistent fever reported", "Oxygen level remains stable"],
  },
];

const trendData = [
  { month: "Jan", score: 32 },
  { month: "Feb", score: 30 },
  { month: "Mar", score: 27 },
  { month: "Apr", score: 25 },
  { month: "May", score: 22 },
];

const predictionHistory = [
  {
    date: "18 May 2026",
    category: "Diabetes Risk",
    prediction: "Low risk",
    confidence: 86,
  },
  {
    date: "10 May 2026",
    category: "Cardiovascular Risk",
    prediction: "Low risk",
    confidence: 82,
  },
  {
    date: "28 Apr 2026",
    category: "Respiratory Risk",
    prediction: "Moderate risk",
    confidence: 74,
  },
];

function useDarkMode() {
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window === "undefined") return false;

    const saved = localStorage.getItem("medicare-theme");
    if (saved === "dark") return true;
    if (saved === "light") return false;

    return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
  });

  useEffect(() => {
    localStorage.setItem("medicare-theme", darkMode ? "dark" : "light");
    document.documentElement.classList.toggle("dark", darkMode);
    document.documentElement.style.colorScheme = darkMode ? "dark" : "light";
    document.body.style.background = darkMode ? "#0b1413" : "#f8faf9";
  }, [darkMode]);

  return [darkMode, setDarkMode];
}

function Header({ darkMode, setDarkMode }) {
  return (
    <header
      className={`flex h-[78px] shrink-0 items-center justify-between border-b px-8 ${
        darkMode
          ? "border-slate-800 bg-[#111c1b]"
          : "border-slate-100 bg-white"
      }`}
    >
      <div>
        <h1
          className={`text-[26px] font-bold tracking-[-0.7px] ${
            darkMode ? "text-white" : "text-emerald-950"
          }`}
        >
          Predictions
        </h1>

        <p
          className={`mt-1 text-[12px] ${
            darkMode ? "text-slate-500" : "text-slate-500"
          }`}
        >
          AI-assisted health risk predictions from your available data
        </p>
      </div>

      <div className="flex items-center gap-4">
        <div
          className={`flex h-10 w-[250px] items-center gap-3 rounded-xl border px-4 ${
            darkMode
              ? "border-slate-700 bg-slate-900/40"
              : "border-slate-200 bg-white"
          }`}
        >
          <Search size={17} className="text-slate-500" />
          <input
            placeholder="Search anything..."
            className={`w-full bg-transparent text-sm outline-none ${
              darkMode
                ? "text-white placeholder:text-slate-500"
                : "text-slate-700 placeholder:text-slate-400"
            }`}
          />
        </div>

        <button
          type="button"
          onClick={() => setDarkMode((value) => !value)}
          className={`flex h-10 w-10 items-center justify-center rounded-xl border transition ${
            darkMode
              ? "border-slate-700 bg-slate-900 text-yellow-300 hover:bg-slate-800"
              : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
          }`}
          aria-label="Toggle theme"
        >
          {darkMode ? <Sun size={19} /> : <Moon size={19} />}
        </button>

        <button
          type="button"
          className={`relative ${
            darkMode ? "text-slate-300" : "text-slate-700"
          }`}
          aria-label="Notifications"
        >
          <Bell size={21} strokeWidth={1.7} />
          <span
            className={`absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full border-2 ${
              darkMode ? "border-[#111c1b]" : "border-white"
            } bg-emerald-500`}
          />
        </button>

        <Link to="/patient/settings" className="flex items-center gap-3">
          <div
            className={`h-10 w-10 overflow-hidden rounded-full ${
              darkMode ? "bg-slate-700" : "bg-slate-200"
            }`}
          >
            <img
              src="https://i.pravatar.cc/100?img=12"
              alt="Patient profile"
              className="h-full w-full object-cover"
            />
          </div>

          <span
            className={`text-[14px] font-semibold ${
              darkMode ? "text-slate-200" : "text-slate-800"
            }`}
          >
            John Doe
          </span>

          <ChevronDown
            size={16}
            className={darkMode ? "text-slate-400" : "text-slate-600"}
          />
        </Link>
      </div>
    </header>
  );
}

function RiskBadge({ level, darkMode }) {
  const classes =
    level === "Low"
      ? darkMode
        ? "bg-emerald-500/10 text-emerald-400"
        : "bg-emerald-50 text-emerald-700"
      : level === "Moderate"
        ? darkMode
          ? "bg-amber-500/10 text-amber-400"
          : "bg-amber-50 text-amber-700"
        : darkMode
          ? "bg-red-500/10 text-red-400"
          : "bg-red-50 text-red-600";

  return (
    <span className={`rounded-full px-2.5 py-1 text-[8px] font-medium ${classes}`}>
      {level} risk
    </span>
  );
}

function PredictionCard({ item, darkMode, onView }) {
  const ringColor =
    item.level === "Low"
      ? "#20b480"
      : item.level === "Moderate"
        ? "#f59e0b"
        : "#ef4444";

  return (
    <div
      className={`rounded-[14px] border p-4 ${
        darkMode
          ? "border-slate-800 bg-[#15211f]"
          : "border-slate-200 bg-white"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <div
            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
              darkMode ? "bg-emerald-500/10" : "bg-emerald-50"
            }`}
          >
            <Brain size={16} className="text-emerald-500" />
          </div>

          <div className="min-w-0">
            <h3
              className={`truncate text-[11px] font-bold ${
                darkMode ? "text-white" : "text-emerald-950"
              }`}
            >
              {item.title}
            </h3>

            <p
              className={`mt-1 text-[8px] ${
                darkMode ? "text-slate-600" : "text-slate-400"
              }`}
            >
              AI risk estimate
            </p>
          </div>
        </div>

        <RiskBadge level={item.level} darkMode={darkMode} />
      </div>

      <div className="mt-4 flex items-center gap-4">
        <div className="relative h-[76px] w-[76px] shrink-0">
          <svg className="-rotate-90" viewBox="0 0 76 76">
            <circle
              cx="38"
              cy="38"
              r="30"
              fill="none"
              stroke={darkMode ? "#263936" : "#e5e7eb"}
              strokeWidth="7"
            />
            <circle
              cx="38"
              cy="38"
              r="30"
              fill="none"
              stroke={ringColor}
              strokeWidth="7"
              strokeLinecap="round"
              strokeDasharray={`${(item.score / 100) * 188.5} 188.5`}
            />
          </svg>

          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span
              className={`text-[17px] font-bold ${
                darkMode ? "text-white" : "text-emerald-950"
              }`}
            >
              {item.score}%
            </span>
            <span className="text-[7px] text-slate-500">risk</span>
          </div>
        </div>

        <p
          className={`text-[9px] leading-4 ${
            darkMode ? "text-slate-400" : "text-slate-500"
          }`}
        >
          {item.description}
        </p>
      </div>

      <div className="mt-4">
        <p
          className={`text-[8px] font-semibold uppercase tracking-[0.08em] ${
            darkMode ? "text-slate-600" : "text-slate-400"
          }`}
        >
          Key factors
        </p>

        <div className="mt-2 space-y-1.5">
          {item.factors.map((factor) => (
            <div
              key={factor}
              className={`flex items-center gap-2 text-[9px] ${
                darkMode ? "text-slate-400" : "text-slate-500"
              }`}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              {factor}
            </div>
          ))}
        </div>
      </div>

      <button
        type="button"
        onClick={() => onView(item)}
        className="mt-4 w-full rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-3 py-2 text-[9px] font-medium text-emerald-500 hover:bg-emerald-500/10"
      >
        View detailed prediction
      </button>
    </div>
  );
}

function TrendChart({ darkMode }) {
  const width = 520;
  const height = 170;
  const paddingLeft = 34;
  const paddingRight = 8;
  const paddingTop = 12;
  const paddingBottom = 28;

  const min = 15;
  const max = 40;

  const points = trendData
    .map((item, index) => {
      const x =
        paddingLeft +
        (index / (trendData.length - 1)) *
          (width - paddingLeft - paddingRight);

      const y =
        height -
        paddingBottom -
        ((item.score - min) / (max - min)) *
          (height - paddingTop - paddingBottom);

      return {
        ...item,
        x,
        y,
      };
    });

  const polyline = points.map((point) => `${point.x},${point.y}`).join(" ");

  return (
    <div className="mt-3 h-[190px] w-full">
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
      >
        {[20, 25, 30, 35, 40].map((tick) => {
          const y =
            height -
            paddingBottom -
            ((tick - min) / (max - min)) *
              (height - paddingTop - paddingBottom);

          return (
            <g key={tick}>
              <line
                x1={paddingLeft}
                y1={y}
                x2={width - paddingRight}
                y2={y}
                stroke={darkMode ? "#263936" : "#e5e7eb"}
                strokeDasharray="3 4"
              />
              <text
                x="5"
                y={y + 3}
                fontSize="9"
                fill={darkMode ? "#64748b" : "#94a3b8"}
              >
                {tick}%
              </text>
            </g>
          );
        })}

        {trendData.map((item, index) => {
          const point = points[index];

          return (
            <text
              key={item.month}
              x={point.x}
              y={height - 8}
              textAnchor="middle"
              fontSize="9"
              fill={darkMode ? "#64748b" : "#94a3b8"}
            >
              {item.month}
            </text>
          );
        })}

        <polyline
          points={polyline}
          fill="none"
          stroke="#20b480"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {points.map((point) => (
          <circle
            key={point.month}
            cx={point.x}
            cy={point.y}
            r="4"
            fill={darkMode ? "#15211f" : "#ffffff"}
            stroke="#20b480"
            strokeWidth="2"
          />
        ))}
      </svg>
    </div>
  );
}

function DetailModal({ prediction, darkMode, onClose }) {
  if (!prediction) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div
        className={`w-full max-w-lg rounded-2xl border shadow-2xl ${
          darkMode
            ? "border-slate-700 bg-[#15211f]"
            : "border-slate-200 bg-white"
        }`}
      >
        <div className="flex items-start justify-between border-b p-5">
          <div>
            <h3
              className={`text-[16px] font-bold ${
                darkMode ? "text-white" : "text-emerald-950"
              }`}
            >
              {prediction.title}
            </h3>
            <p
              className={`mt-1 text-[10px] ${
                darkMode ? "text-slate-500" : "text-slate-500"
              }`}
            >
              Detailed prediction breakdown
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className={`rounded-lg p-1.5 ${
              darkMode
                ? "text-slate-400 hover:bg-slate-800"
                : "text-slate-500 hover:bg-slate-100"
            }`}
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-5">
          <div
            className={`rounded-xl border p-4 ${
              darkMode
                ? "border-emerald-500/20 bg-emerald-500/5"
                : "border-emerald-100 bg-emerald-50/40"
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[8px] uppercase tracking-[0.08em] text-slate-500">
                  Current estimated risk
                </p>
                <p
                  className={`mt-1 text-[30px] font-bold ${
                    darkMode ? "text-white" : "text-emerald-950"
                  }`}
                >
                  {prediction.score}%
                </p>
              </div>

              <RiskBadge
                level={prediction.level}
                darkMode={darkMode}
              />
            </div>
          </div>

          <div className="mt-4">
            <p
              className={`text-[10px] font-semibold ${
                darkMode ? "text-slate-300" : "text-slate-700"
              }`}
            >
              Contributing factors
            </p>

            <div className="mt-2 space-y-2">
              {prediction.factors.map((factor) => (
                <div
                  key={factor}
                  className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-[9px] ${
                    darkMode
                      ? "border-slate-800 bg-[#101918] text-slate-400"
                      : "border-slate-100 bg-slate-50 text-slate-500"
                  }`}
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  {factor}
                </div>
              ))}
            </div>
          </div>

          <div
            className={`mt-4 flex items-start gap-2 rounded-xl border p-3 ${
              darkMode
                ? "border-amber-500/20 bg-amber-500/5"
                : "border-amber-100 bg-amber-50/60"
            }`}
          >
            <Info
              size={14}
              className="mt-0.5 shrink-0 text-amber-500"
            />
            <p
              className={`text-[9px] leading-4 ${
                darkMode ? "text-slate-400" : "text-slate-600"
              }`}
            >
              This is a model-generated risk estimate for demonstration
              purposes, not a medical diagnosis. Predictions should be
              reviewed with a qualified clinician.
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="mt-4 w-full rounded-lg bg-emerald-500 px-4 py-2.5 text-[10px] font-semibold text-white hover:bg-emerald-600"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Predictions() {
  const [darkMode, setDarkMode] = useDarkMode();
  const [selectedPrediction, setSelectedPrediction] = useState(null);
  const [lastUpdated, setLastUpdated] = useState("Today, 10:30 AM");
  const [predictionSet, setPredictionSet] = useState(baselineRisks);

  const overallRisk = useMemo(
    () =>
      Math.round(
        predictionSet.reduce((sum, item) => sum + item.score, 0) /
          predictionSet.length
      ),
    [predictionSet]
  );

  const refreshPredictions = () => {
    const next = predictionSet.map((item, index) => ({
      ...item,
      score: Math.max(
        8,
        Math.min(
          45,
          item.score + (index === 0 ? -1 : index === 1 ? 1 : 0)
        )
      ),
    }));

    setPredictionSet(next);
    setLastUpdated("Just now");
  };

  return (
    <div
      className={`h-screen w-full overflow-hidden p-2 ${
        darkMode
          ? "bg-[#0b1413] text-white"
          : "bg-[#f8faf9] text-slate-900"
      }`}
    >
      <div
        className={`flex h-full w-full overflow-hidden rounded-[18px] border ${
          darkMode
            ? "border-slate-800 bg-[#111c1b]"
            : "border-slate-200 bg-white"
        }`}
      >
        <Sidebar darkMode={darkMode} />

        <main className="ml-[255px] flex min-w-0 flex-1 flex-col overflow-hidden">
          <Header
            darkMode={darkMode}
            setDarkMode={setDarkMode}
          />

          <div className="min-h-0 flex-1 overflow-y-auto px-8 py-5">
            <div className="flex items-center justify-between">
              <div>
                <h2
                  className={`text-[19px] font-bold ${
                    darkMode ? "text-white" : "text-emerald-950"
                  }`}
                >
                  Predictions
                </h2>

                <p
                  className={`mt-1 text-[11px] ${
                    darkMode ? "text-slate-500" : "text-slate-500"
                  }`}
                >
                  View AI-assisted risk predictions based on your available health data
                </p>
              </div>

              <button
                type="button"
                onClick={refreshPredictions}
                className="rounded-lg bg-emerald-500 px-4 py-2 text-[10px] font-semibold text-white hover:bg-emerald-600"
              >
                Refresh Predictions
              </button>
            </div>

            <div className="mt-4 grid grid-cols-4 gap-3">
              <div
                className={`rounded-[14px] border p-4 ${
                  darkMode
                    ? "border-slate-800 bg-[#15211f]"
                    : "border-slate-200 bg-white"
                }`}
              >
                <p
                  className={`text-[9px] uppercase tracking-[0.08em] ${
                    darkMode ? "text-slate-500" : "text-slate-500"
                  }`}
                >
                  Overall Risk
                </p>

                <div className="mt-1 flex items-baseline gap-1">
                  <span
                    className={`text-[27px] font-semibold ${
                      darkMode ? "text-white" : "text-emerald-950"
                    }`}
                  >
                    {overallRisk}%
                  </span>
                  <span className="text-[9px] text-emerald-500">low</span>
                </div>
              </div>

              <div
                className={`rounded-[14px] border p-4 ${
                  darkMode
                    ? "border-slate-800 bg-[#15211f]"
                    : "border-slate-200 bg-white"
                }`}
              >
                <p
                  className={`text-[9px] uppercase tracking-[0.08em] ${
                    darkMode ? "text-slate-500" : "text-slate-500"
                  }`}
                >
                  Predictions
                </p>

                <p
                  className={`mt-1 text-[27px] font-semibold ${
                    darkMode ? "text-white" : "text-emerald-950"
                  }`}
                >
                  {predictionSet.length}
                </p>
              </div>

              <div
                className={`rounded-[14px] border p-4 ${
                  darkMode
                    ? "border-slate-800 bg-[#15211f]"
                    : "border-slate-200 bg-white"
                }`}
              >
                <p
                  className={`text-[9px] uppercase tracking-[0.08em] ${
                    darkMode ? "text-slate-500" : "text-slate-500"
                  }`}
                >
                  Moderate Risk
                </p>

                <p
                  className={`mt-1 text-[27px] font-semibold ${
                    darkMode ? "text-white" : "text-emerald-950"
                  }`}
                >
                  {predictionSet.filter((item) => item.level === "Moderate").length}
                </p>
              </div>

              <div
                className={`rounded-[14px] border p-4 ${
                  darkMode
                    ? "border-slate-800 bg-[#15211f]"
                    : "border-slate-200 bg-white"
                }`}
              >
                <p
                  className={`text-[9px] uppercase tracking-[0.08em] ${
                    darkMode ? "text-slate-500" : "text-slate-500"
                  }`}
                >
                  Last Updated
                </p>

                <p
                  className={`mt-2 text-[10px] font-medium ${
                    darkMode ? "text-slate-200" : "text-slate-700"
                  }`}
                >
                  {lastUpdated}
                </p>
              </div>
            </div>

            <section
              className={`mt-3 rounded-[14px] border p-4 ${
                darkMode
                  ? "border-slate-800 bg-[#15211f]"
                  : "border-slate-200 bg-white"
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3
                    className={`text-[13px] font-bold ${
                      darkMode ? "text-white" : "text-emerald-950"
                    }`}
                  >
                    Health Risk Predictions
                  </h3>

                  <p
                    className={`mt-1 text-[9px] ${
                      darkMode ? "text-slate-500" : "text-slate-500"
                    }`}
                  >
                    Current risk estimates across selected health categories
                  </p>
                </div>

                <div
                  className={`flex items-center gap-1 text-[8px] ${
                    darkMode ? "text-slate-500" : "text-slate-500"
                  }`}
                >
                  <Sparkles size={11} className="text-emerald-500" />
                  AI assisted
                </div>
              </div>

              <div className="mt-4 grid grid-cols-3 gap-3">
                {predictionSet.map((item) => (
                  <PredictionCard
                    key={item.id}
                    item={item}
                    darkMode={darkMode}
                    onView={setSelectedPrediction}
                  />
                ))}
              </div>
            </section>

            <div className="mt-3 grid grid-cols-[1.15fr_0.85fr] gap-3">
              <section
                className={`rounded-[14px] border p-4 ${
                  darkMode
                    ? "border-slate-800 bg-[#15211f]"
                    : "border-slate-200 bg-white"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3
                      className={`text-[13px] font-bold ${
                        darkMode ? "text-white" : "text-emerald-950"
                      }`}
                    >
                      Overall Risk Trend
                    </h3>

                    <p
                      className={`mt-1 text-[9px] ${
                        darkMode ? "text-slate-500" : "text-slate-500"
                      }`}
                    >
                      Recent change in combined estimated risk
                    </p>
                  </div>

                  <span
                    className={`rounded-full px-2 py-1 text-[8px] font-medium ${
                      darkMode
                        ? "bg-emerald-500/10 text-emerald-400"
                        : "bg-emerald-50 text-emerald-700"
                    }`}
                  >
                    Improving
                  </span>
                </div>

                <TrendChart darkMode={darkMode} />
              </section>

              <section
                className={`rounded-[14px] border p-4 ${
                  darkMode
                    ? "border-slate-800 bg-[#15211f]"
                    : "border-slate-200 bg-white"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <div
                    className={`flex h-8 w-8 items-center justify-center rounded-full ${
                      darkMode ? "bg-emerald-500/10" : "bg-emerald-50"
                    }`}
                  >
                    <ShieldAlert
                      size={16}
                      className="text-emerald-500"
                    />
                  </div>

                  <div>
                    <h3
                      className={`text-[13px] font-bold ${
                        darkMode ? "text-white" : "text-emerald-950"
                      }`}
                    >
                      Prediction Guidance
                    </h3>

                    <p
                      className={`mt-0.5 text-[9px] ${
                        darkMode ? "text-slate-500" : "text-slate-500"
                      }`}
                    >
                      How to interpret your results
                    </p>
                  </div>
                </div>

                <div className="mt-4 space-y-3">
                  <div
                    className={`rounded-xl border p-3 ${
                      darkMode
                        ? "border-emerald-500/10 bg-emerald-500/5"
                        : "border-emerald-100 bg-emerald-50/40"
                    }`}
                  >
                    <p className="text-[9px] font-semibold text-emerald-500">
                      Low risk
                    </p>
                    <p
                      className={`mt-1 text-[8px] leading-4 ${
                        darkMode ? "text-slate-400" : "text-slate-500"
                      }`}
                    >
                      Continue routine care and healthy habits.
                    </p>
                  </div>

                  <div
                    className={`rounded-xl border p-3 ${
                      darkMode
                        ? "border-slate-800 bg-[#101918]"
                        : "border-slate-100 bg-slate-50"
                    }`}
                  >
                    <p className="text-[9px] font-semibold text-amber-500">
                      Moderate risk
                    </p>
                    <p
                      className={`mt-1 text-[8px] leading-4 ${
                        darkMode ? "text-slate-400" : "text-slate-500"
                      }`}
                    >
                      Monitor the relevant indicators and discuss persistent
                      concerns with your clinician.
                    </p>
                  </div>

                  <div
                    className={`flex items-start gap-2 rounded-xl border p-3 ${
                      darkMode
                        ? "border-slate-800 bg-[#101918]"
                        : "border-slate-100 bg-slate-50"
                    }`}
                  >
                    <Info
                      size={12}
                      className="mt-0.5 shrink-0 text-slate-500"
                    />
                    <p
                      className={`text-[8px] leading-4 ${
                        darkMode ? "text-slate-500" : "text-slate-500"
                      }`}
                    >
                      Predictions are estimates for demonstration and should
                      not be treated as a medical diagnosis.
                    </p>
                  </div>
                </div>
              </section>
            </div>

            <section
              className={`mt-3 overflow-hidden rounded-[14px] border ${
                darkMode
                  ? "border-slate-800 bg-[#15211f]"
                  : "border-slate-200 bg-white"
              }`}
            >
              <div className="flex items-center justify-between px-4 py-3">
                <div>
                  <h3
                    className={`text-[13px] font-bold ${
                      darkMode ? "text-white" : "text-emerald-950"
                    }`}
                  >
                    Prediction History
                  </h3>

                  <p
                    className={`mt-1 text-[9px] ${
                      darkMode ? "text-slate-500" : "text-slate-500"
                    }`}
                  >
                    Previous generated health risk predictions
                  </p>
                </div>

                <CalendarDays
                  size={15}
                  className={darkMode ? "text-slate-600" : "text-slate-400"}
                />
              </div>

              <div
                className={`border-t ${
                  darkMode ? "border-slate-800" : "border-slate-100"
                }`}
              >
                <div
                  className={`grid grid-cols-[0.8fr_1.2fr_1fr_0.7fr] px-4 py-2.5 text-[8px] font-semibold uppercase tracking-[0.08em] ${
                    darkMode ? "text-slate-600" : "text-slate-400"
                  }`}
                >
                  <span>Date</span>
                  <span>Category</span>
                  <span>Prediction</span>
                  <span>Confidence</span>
                </div>

                {predictionHistory.map((item, index) => (
                  <div
                    key={`${item.category}-${item.date}`}
                    className={`grid grid-cols-[0.8fr_1.2fr_1fr_0.7fr] items-center px-4 py-3 ${
                      index !== predictionHistory.length - 1
                        ? `border-t ${
                            darkMode
                              ? "border-slate-800"
                              : "border-slate-100"
                          }`
                        : ""
                    }`}
                  >
                    <span
                      className={`text-[9px] ${
                        darkMode ? "text-slate-500" : "text-slate-500"
                      }`}
                    >
                      {item.date}
                    </span>

                    <span
                      className={`text-[9px] ${
                        darkMode ? "text-slate-300" : "text-slate-600"
                      }`}
                    >
                      {item.category}
                    </span>

                    <span
                      className={`inline-flex w-fit rounded-full px-2 py-1 text-[8px] font-medium ${
                        item.prediction === "Low risk"
                          ? darkMode
                            ? "bg-emerald-500/10 text-emerald-400"
                            : "bg-emerald-50 text-emerald-700"
                          : darkMode
                            ? "bg-amber-500/10 text-amber-400"
                            : "bg-amber-50 text-amber-700"
                      }`}
                    >
                      {item.prediction}
                    </span>

                    <span
                      className={`text-[9px] ${
                        darkMode ? "text-slate-400" : "text-slate-500"
                      }`}
                    >
                      {item.confidence}%
                    </span>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </main>
      </div>

      <DetailModal
        prediction={selectedPrediction}
        darkMode={darkMode}
        onClose={() => setSelectedPrediction(null)}
      />
    </div>
  );
}
