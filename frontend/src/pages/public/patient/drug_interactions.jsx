import React, { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  Bell,
  Brain,
  CheckCircle2,
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
  Plus,
  Search,
  Settings,
  ShieldAlert,
  Sparkles,
  Stethoscope,
  Sun,
  TrendingUp,
  X,
  XCircle,
} from "lucide-react";

const ROUTES = {
  dashboard: "/patient/dashboard",
  healthTrends: "/patient/health-trends",
  appointments: "/patient/appointments",
  medicalRecords: "/patient/medical-records",
  labTests: "/patient/reports-lab-tests",
  medications: "/patient/medications",
  symptomAnalysis: "/patient/symptom-analysis",
  predictions: "/patient/predictions",
  aiAssistant: "/patient/ai-assistant",
  medicineSearch: "/patient/medicine-search",
  drugInteractions: "/patient/drug-interactions",
  settings: "/patient/settings",
};

const navSections = [
  {
    title: "MAIN",
    items: [{ label: "Dashboard", icon: Home, route: ROUTES.dashboard }],
  },
  {
    title: "HEALTH",
    items: [
      { label: "Health Trends", icon: TrendingUp, route: ROUTES.healthTrends },
      { label: "Appointments", icon: Activity, route: ROUTES.appointments },
    ],
  },
  {
    title: "MEDICAL",
    items: [
      { label: "Medical Records", icon: FileText, route: ROUTES.medicalRecords },
      { label: "Reports & Lab Tests", icon: ClipboardList, route: ROUTES.labTests },
      { label: "Medications", icon: Pill, route: ROUTES.medications },
    ],
  },
  {
    title: "AI HEALTH",
    items: [
      { label: "Symptom Analysis", icon: Stethoscope, route: ROUTES.symptomAnalysis },
      { label: "Predictions", icon: Brain, route: ROUTES.predictions },
      { label: "AI Assistant", icon: Sparkles, route: ROUTES.aiAssistant },
    ],
  },
  {
    title: "MEDICINES",
    items: [
      { label: "Medicine Search", icon: CircleDot, route: ROUTES.medicineSearch },
      { label: "Drug Interactions", icon: AlertTriangle, route: ROUTES.drugInteractions },
    ],
  },
];

const medicineOptions = [
  "Metformin",
  "Atorvastatin",
  "Warfarin",
  "Aspirin",
  "Ibuprofen",
  "Paracetamol",
  "Omeprazole",
  "Cetirizine",
  "Amoxicillin",
];

const interactionDatabase = {
  "Metformin|Aspirin": {
    level: "Moderate",
    title: "Monitor for increased side effects",
    summary:
      "These medicines may be used together in some clinical situations, but a clinician should review the full medication list, medical history and dosing.",
    details: [
      "Check the reason both medicines are being taken.",
      "Review kidney function and other risk factors with the prescribing clinician.",
      "Do not change or stop a prescribed medicine without professional guidance.",
    ],
  },
  "Atorvastatin|Grapefruit": {
    level: "Moderate",
    title: "May increase atorvastatin exposure",
    summary:
      "Grapefruit products can affect the metabolism of some statins, including atorvastatin.",
    details: [
      "Discuss regular grapefruit or grapefruit juice consumption with your clinician.",
      "Ask whether a specific amount is appropriate for your treatment plan.",
    ],
  },
  "Warfarin|Aspirin": {
    level: "High",
    title: "Higher bleeding risk",
    summary:
      "Combining anticoagulant and antiplatelet medicines can substantially increase bleeding risk in some patients.",
    details: [
      "Use this combination only under professional supervision.",
      "Seek urgent care for signs of significant bleeding.",
    ],
  },
  "Warfarin|Ibuprofen": {
    level: "High",
    title: "Higher bleeding risk",
    summary:
      "NSAIDs such as ibuprofen may increase bleeding risk when taken with warfarin.",
    details: [
      "Ask your clinician or pharmacist before using NSAIDs.",
      "Review safer pain-relief options for your individual situation.",
    ],
  },
  "Metformin|Ibuprofen": {
    level: "Moderate",
    title: "Use with clinical review",
    summary:
      "Certain pain medicines can affect kidney function, which can matter for patients taking metformin.",
    details: [
      "Review kidney function and hydration if these medicines are used together.",
      "Use the lowest effective duration under professional advice.",
    ],
  },
};

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

function isActivePath(pathname, route) {
  return pathname.replace(/\/$/, "") === route.replace(/\/$/, "");
}

function Sidebar({ darkMode }) {
  const location = useLocation();

  const colors = {
    sidebar: darkMode ? "bg-[#101918]" : "bg-white",
    border: darkMode ? "border-slate-800" : "border-slate-100",
    text: darkMode ? "text-slate-300" : "text-slate-600",
    heading: "text-slate-500",
    hover: darkMode ? "hover:bg-slate-800/60" : "hover:bg-slate-50",
    active: "bg-emerald-500/10 text-emerald-500 font-semibold",
  };

  return (
    <aside
      className={`flex h-full w-[255px] shrink-0 flex-col overflow-y-auto border-r ${colors.border} ${colors.sidebar} px-4 py-5`}
    >
      <Link
        to={ROUTES.dashboard}
        className="mb-5 flex shrink-0 items-center gap-3 px-3"
      >
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500 shadow-sm">
          <Heart size={21} strokeWidth={2.5} className="text-white" />
        </div>
        <span
          className={`text-[21px] font-bold tracking-[-0.5px] ${
            darkMode ? "text-white" : "text-emerald-900"
          }`}
        >
          medicare.
        </span>
      </Link>

      <nav className="min-h-0 flex-1">
        <div className="space-y-3">
          {navSections.map((section) => (
            <div key={section.title}>
              <p
                className={`mb-1.5 px-3 text-[10px] font-semibold tracking-[0.12em] ${colors.heading}`}
              >
                {section.title}
              </p>

              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const active = isActivePath(location.pathname, item.route);

                  return (
                    <Link
                      key={item.label}
                      to={item.route}
                      aria-current={active ? "page" : undefined}
                      className={`relative flex w-full items-center gap-3 rounded-lg px-3 py-[8px] text-left text-[13px] transition-all duration-200 ${
                        active ? colors.active : `${colors.text} ${colors.hover}`
                      }`}
                    >
                      {active && (
                        <span className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-emerald-500" />
                      )}

                      <Icon
                        size={18}
                        strokeWidth={1.8}
                        className={
                          active
                            ? "text-emerald-500"
                            : darkMode
                              ? "text-slate-400"
                              : "text-slate-500"
                        }
                      />
                      <span className="truncate">{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </nav>

      <div
        className={`mt-3 shrink-0 border-t pt-3 ${
          darkMode ? "border-slate-800" : "border-slate-100"
        }`}
      >
        <Link
          to={ROUTES.settings}
          className={`flex w-full items-center gap-3 rounded-lg px-3 py-[8px] text-[13px] transition ${
            isActivePath(location.pathname, ROUTES.settings)
              ? colors.active
              : `${colors.text} ${colors.hover}`
          }`}
        >
          <Settings size={18} strokeWidth={1.8} />
          Settings
        </Link>

        <Link
          to="/login"
          className={`flex w-full items-center gap-3 rounded-lg px-3 py-[8px] text-[13px] transition ${colors.text} ${colors.hover}`}
        >
          <LogIn size={18} strokeWidth={1.8} />
          Logout
        </Link>
      </div>
    </aside>
  );
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
          Drug Interactions
        </h1>
        <p
          className={`mt-1 text-[12px] ${
            darkMode ? "text-slate-500" : "text-slate-500"
          }`}
        >
          Check potential interactions between medicines and substances
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
        <Link to={ROUTES.settings} className="flex items-center gap-3">
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

function SeverityBadge({ level, darkMode }) {
  const className =
    level === "High"
      ? darkMode
        ? "bg-red-500/10 text-red-400"
        : "bg-red-50 text-red-600"
      : level === "Moderate"
        ? darkMode
          ? "bg-amber-500/10 text-amber-400"
          : "bg-amber-50 text-amber-700"
        : darkMode
          ? "bg-emerald-500/10 text-emerald-400"
          : "bg-emerald-50 text-emerald-700";

  return (
    <span className={`rounded-full px-2.5 py-1 text-[8px] font-medium ${className}`}>
      {level} risk
    </span>
  );
}

function Selector({ label, value, onChange, darkMode }) {
  return (
    <label
      className={`block text-[9px] font-medium ${
        darkMode ? "text-slate-300" : "text-slate-700"
      }`}
    >
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className={`mt-1.5 w-full rounded-lg border px-3 py-2 text-[9px] outline-none ${
          darkMode
            ? "border-slate-700 bg-[#101918] text-slate-200"
            : "border-slate-200 bg-white text-slate-700"
        }`}
      >
        {medicineOptions.map((medicine) => (
          <option key={medicine} value={medicine}>
            {medicine}
          </option>
        ))}
      </select>
    </label>
  );
}

function ResultPanel({ result, darkMode }) {
  if (!result) {
    return (
      <div
        className={`flex min-h-[270px] flex-col items-center justify-center rounded-xl border ${
          darkMode
            ? "border-slate-800 bg-[#101918]"
            : "border-slate-100 bg-slate-50"
        }`}
      >
        <div
          className={`flex h-12 w-12 items-center justify-center rounded-full ${
            darkMode ? "bg-emerald-500/10" : "bg-emerald-50"
          }`}
        >
          <ShieldAlert size={21} className="text-emerald-500" />
        </div>

        <p
          className={`mt-3 text-[11px] font-semibold ${
            darkMode ? "text-slate-200" : "text-slate-700"
          }`}
        >
          Ready to check
        </p>

        <p
          className={`mt-1 max-w-[250px] text-center text-[8px] leading-4 ${
            darkMode ? "text-slate-600" : "text-slate-400"
          }`}
        >
          Select two medicines or substances to review a potential interaction.
        </p>
      </div>
    );
  }

  return (
    <div
      className={`rounded-xl border p-4 ${
        darkMode
          ? "border-slate-800 bg-[#101918]"
          : "border-slate-100 bg-slate-50/70"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p
            className={`text-[12px] font-bold ${
              darkMode ? "text-white" : "text-emerald-950"
            }`}
          >
            {result.title}
          </p>
          <p
            className={`mt-1 text-[8px] ${
              darkMode ? "text-slate-600" : "text-slate-400"
            }`}
          >
            {result.pair}
          </p>
        </div>

        <SeverityBadge level={result.level} darkMode={darkMode} />
      </div>

      <div
        className={`mt-4 rounded-xl border p-3 ${
          result.level === "High"
            ? darkMode
              ? "border-red-500/20 bg-red-500/5"
              : "border-red-100 bg-red-50/50"
            : result.level === "Moderate"
              ? darkMode
                ? "border-amber-500/20 bg-amber-500/5"
                : "border-amber-100 bg-amber-50/50"
              : darkMode
                ? "border-emerald-500/20 bg-emerald-500/5"
                : "border-emerald-100 bg-emerald-50/50"
        }`}
      >
        <p
          className={`text-[9px] leading-4 ${
            darkMode ? "text-slate-300" : "text-slate-600"
          }`}
        >
          {result.summary}
        </p>
      </div>

      <div className="mt-4">
        <p
          className={`text-[9px] font-semibold ${
            darkMode ? "text-slate-300" : "text-slate-700"
          }`}
        >
          What to consider
        </p>

        <div className="mt-2 space-y-2">
          {result.details.map((detail) => (
            <div
              key={detail}
              className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-[8px] leading-4 ${
                darkMode
                  ? "border-slate-800 bg-[#15211f] text-slate-500"
                  : "border-slate-100 bg-white text-slate-500"
              }`}
            >
              <CheckCircle2
                size={11}
                className="mt-0.5 shrink-0 text-emerald-500"
              />
              {detail}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function DrugInteractions() {
  const [darkMode, setDarkMode] = useDarkMode();
  const [medicineA, setMedicineA] = useState("Metformin");
  const [medicineB, setMedicineB] = useState("Aspirin");
  const [result, setResult] = useState(null);
  const [recentChecks, setRecentChecks] = useState([]);

  const canCheck = medicineA && medicineB && medicineA !== medicineB;

  const findInteraction = () => {
    if (!canCheck) return;

    const keys = [
      `${medicineA}|${medicineB}`,
      `${medicineB}|${medicineA}`,
    ];

    const found =
      keys.map((key) => interactionDatabase[key]).find(Boolean) || {
        level: "Low",
        title: "No major interaction found in demo database",
        summary:
          "No specific interaction is listed for this pair in the current demonstration dataset. This does not rule out individual risks, duplicate ingredients, dose-related effects, or interactions with other medicines.",
        details: [
          "Check the full medication list, including supplements and non-prescription products.",
          "Confirm the combination with a pharmacist or clinician if you are unsure.",
          "Do not change a prescribed treatment based only on this tool.",
        ],
      };

    const nextResult = {
      ...found,
      pair: `${medicineA} + ${medicineB}`,
    };

    setResult(nextResult);
    setRecentChecks((current) => [
      nextResult,
      ...current.filter((item) => item.pair !== nextResult.pair),
    ].slice(0, 4));
  };

  const clearCheck = () => {
    setResult(null);
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

        <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <Header
            darkMode={darkMode}
            setDarkMode={setDarkMode}
          />

          <div className="min-h-0 flex-1 overflow-y-auto px-8 py-5">
            <div>
              <h2
                className={`text-[19px] font-bold ${
                  darkMode ? "text-white" : "text-emerald-950"
                }`}
              >
                Drug Interactions
              </h2>

              <p
                className={`mt-1 text-[11px] ${
                  darkMode ? "text-slate-500" : "text-slate-500"
                }`}
              >
                Check two medicines or substances for potential interaction risks
              </p>
            </div>

            <div className="mt-4 grid grid-cols-3 gap-3">
              <div
                className={`rounded-[14px] border p-4 ${
                  darkMode
                    ? "border-slate-800 bg-[#15211f]"
                    : "border-slate-200 bg-white"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-[9px] uppercase tracking-[0.08em] text-slate-500">
                      Medicines Checked
                    </p>
                    <p
                      className={`mt-1 text-[25px] font-semibold ${
                        darkMode ? "text-white" : "text-emerald-950"
                      }`}
                    >
                      2
                    </p>
                  </div>
                  <Pill size={16} className="text-emerald-500" />
                </div>
              </div>

              <div
                className={`rounded-[14px] border p-4 ${
                  darkMode
                    ? "border-slate-800 bg-[#15211f]"
                    : "border-slate-200 bg-white"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-[9px] uppercase tracking-[0.08em] text-slate-500">
                      Recent Checks
                    </p>
                    <p
                      className={`mt-1 text-[25px] font-semibold ${
                        darkMode ? "text-white" : "text-emerald-950"
                      }`}
                    >
                      {recentChecks.length}
                    </p>
                  </div>
                  <Activity size={16} className="text-emerald-500" />
                </div>
              </div>

              <div
                className={`rounded-[14px] border p-4 ${
                  darkMode
                    ? "border-slate-800 bg-[#15211f]"
                    : "border-slate-200 bg-white"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-[9px] uppercase tracking-[0.08em] text-slate-500">
                      Safety Reminder
                    </p>
                    <p
                      className={`mt-2 text-[9px] font-medium leading-4 ${
                        darkMode ? "text-slate-300" : "text-slate-600"
                      }`}
                    >
                      Check all medicines, supplements and OTC products.
                    </p>
                  </div>
                  <ShieldAlert size={16} className="text-amber-500" />
                </div>
              </div>
            </div>

            <div className="mt-3 grid grid-cols-[0.95fr_1.05fr] gap-3">
              <section
                className={`rounded-[14px] border p-4 ${
                  darkMode
                    ? "border-slate-800 bg-[#15211f]"
                    : "border-slate-200 bg-white"
                }`}
              >
                <div className="flex items-start gap-2.5">
                  <div
                    className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                      darkMode ? "bg-emerald-500/10" : "bg-emerald-50"
                    }`}
                  >
                    <ShieldAlert size={15} className="text-emerald-500" />
                  </div>

                  <div>
                    <h3
                      className={`text-[13px] font-bold ${
                        darkMode ? "text-white" : "text-emerald-950"
                      }`}
                    >
                      Check Interaction
                    </h3>

                    <p
                      className={`mt-1 text-[9px] ${
                        darkMode ? "text-slate-500" : "text-slate-500"
                      }`}
                    >
                      Select two items from the list below.
                    </p>
                  </div>
                </div>

                <div className="mt-5 space-y-3">
                  <Selector
                    label="Medicine / Substance 1"
                    value={medicineA}
                    onChange={(value) => {
                      setMedicineA(value);
                      setResult(null);
                    }}
                    darkMode={darkMode}
                  />

                  <div className="flex items-center gap-2">
                    <div
                      className={`h-px flex-1 ${
                        darkMode ? "bg-slate-800" : "bg-slate-100"
                      }`}
                    />
                    <span className="rounded-full bg-emerald-500 px-2 py-1 text-[8px] font-semibold text-white">
                      +
                    </span>
                    <div
                      className={`h-px flex-1 ${
                        darkMode ? "bg-slate-800" : "bg-slate-100"
                      }`}
                    />
                  </div>

                  <Selector
                    label="Medicine / Substance 2"
                    value={medicineB}
                    onChange={(value) => {
                      setMedicineB(value);
                      setResult(null);
                    }}
                    darkMode={darkMode}
                  />

                  {!canCheck && (
                    <p className="text-[8px] text-red-500">
                      Choose two different items to run the check.
                    </p>
                  )}

                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={findInteraction}
                      disabled={!canCheck}
                      className={`flex-1 rounded-lg px-4 py-2.5 text-[10px] font-semibold text-white ${
                        canCheck
                          ? "bg-emerald-500 hover:bg-emerald-600"
                          : "cursor-not-allowed bg-slate-400"
                      }`}
                    >
                      Check Interaction
                    </button>

                    <button
                      type="button"
                      onClick={clearCheck}
                      className={`rounded-lg border px-4 py-2.5 text-[10px] font-medium ${
                        darkMode
                          ? "border-slate-700 text-slate-400 hover:bg-slate-800"
                          : "border-slate-200 text-slate-500 hover:bg-slate-50"
                      }`}
                    >
                      Clear
                    </button>
                  </div>
                </div>

                <div
                  className={`mt-4 flex items-start gap-2 rounded-xl border p-3 ${
                    darkMode
                      ? "border-amber-500/20 bg-amber-500/5"
                      : "border-amber-100 bg-amber-50/60"
                  }`}
                >
                  <Info size={13} className="mt-0.5 shrink-0 text-amber-500" />
                  <p
                    className={`text-[8px] leading-4 ${
                      darkMode ? "text-slate-500" : "text-slate-600"
                    }`}
                  >
                    This checker is a demonstration feature. It does not replace
                    a pharmacist or clinician and does not evaluate every
                    possible interaction.
                  </p>
                </div>
              </section>

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
                      Interaction Result
                    </h3>

                    <p
                      className={`mt-1 text-[9px] ${
                        darkMode ? "text-slate-500" : "text-slate-500"
                      }`}
                    >
                      Potential interaction information
                    </p>
                  </div>

                  <AlertTriangle
                    size={15}
                    className="text-amber-500"
                  />
                </div>

                <div className="mt-4">
                  <ResultPanel result={result} darkMode={darkMode} />
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
                    Recent Interaction Checks
                  </h3>

                  <p
                    className={`mt-1 text-[9px] ${
                      darkMode ? "text-slate-500" : "text-slate-500"
                    }`}
                  >
                    Your latest checks in this session
                  </p>
                </div>

                <span className="text-[8px] text-slate-500">
                  {recentChecks.length} saved
                </span>
              </div>

              <div
                className={`border-t ${
                  darkMode ? "border-slate-800" : "border-slate-100"
                }`}
              >
                {recentChecks.length === 0 ? (
                  <div
                    className={`px-4 py-8 text-center text-[9px] ${
                      darkMode ? "text-slate-600" : "text-slate-400"
                    }`}
                  >
                    Your recent interaction checks will appear here.
                  </div>
                ) : (
                  recentChecks.map((item, index) => (
                    <div
                      key={`${item.pair}-${index}`}
                      className={`flex items-center justify-between px-4 py-3 ${
                        index !== recentChecks.length - 1
                          ? `border-b ${
                              darkMode
                                ? "border-slate-800"
                                : "border-slate-100"
                            }`
                          : ""
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <div
                          className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                            darkMode ? "bg-emerald-500/10" : "bg-emerald-50"
                          }`}
                        >
                          <Pill size={13} className="text-emerald-500" />
                        </div>

                        <div>
                          <p
                            className={`text-[9px] font-medium ${
                              darkMode
                                ? "text-slate-200"
                                : "text-slate-700"
                            }`}
                          >
                            {item.pair}
                          </p>
                          <p
                            className={`mt-0.5 text-[8px] ${
                              darkMode ? "text-slate-600" : "text-slate-400"
                            }`}
                          >
                            {item.title}
                          </p>
                        </div>
                      </div>

                      <SeverityBadge level={item.level} darkMode={darkMode} />
                    </div>
                  ))
                )}
              </div>
            </section>

            <div
              className={`mt-3 flex items-start gap-2 rounded-[14px] border p-4 ${
                darkMode
                  ? "border-red-500/10 bg-red-500/5"
                  : "border-red-100 bg-red-50/40"
              }`}
            >
              <XCircle
                size={14}
                className="mt-0.5 shrink-0 text-red-500"
              />

              <p
                className={`text-[8px] leading-4 ${
                  darkMode ? "text-slate-500" : "text-slate-600"
                }`}
              >
                If you think you may have taken a dangerous combination,
                experience severe symptoms, or have signs of a serious
                reaction, seek urgent medical attention.
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
