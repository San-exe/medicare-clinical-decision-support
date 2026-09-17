import React from "react";
import { Link } from "react-router-dom";
import Sidebar from "./sidebar";
import { useTheme } from "../ThemeContext";
import {
  Activity,
  Bell,
  ChevronDown,
  ClipboardList,
  Moon,
  Search,
  Sparkles,
  Sun,
  Thermometer,
} from "lucide-react";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

/* ---------------------------------------------------------
   GLUCOSE DATA
--------------------------------------------------------- */

const glucoseData = [
  { day: "16 Apr", value: 94 },
  { day: "19 Apr", value: 101 },
  { day: "22 Apr", value: 97 },
  { day: "25 Apr", value: 105 },
  { day: "28 Apr", value: 99 },
  { day: "1 May", value: 108 },
  { day: "4 May", value: 102 },
  { day: "7 May", value: 98 },
  { day: "10 May", value: 105 },
  { day: "13 May", value: 100 },
  { day: "16 May", value: 103 },
  { day: "19 May", value: 101 },
  { day: "22 May", value: 102 },
];

/* ---------------------------------------------------------
   HEADER
--------------------------------------------------------- */

function Header({ darkMode, toggleTheme }) {
  return (
    <header
      className={`flex h-[72px] shrink-0 items-center justify-between border-b px-8 transition-colors duration-200 ${
        darkMode
          ? "border-slate-800 bg-[#111c1b]"
          : "border-slate-200 bg-white"
      }`}
    >
      <div>
        <h1
          className={`text-[27px] font-bold tracking-[-0.8px] ${
            darkMode
              ? "text-white"
              : "text-slate-900"
          }`}
        >
          Health Trends
        </h1>

        <p
          className={`mt-0.5 text-[12px] ${
            darkMode
              ? "text-slate-500"
              : "text-slate-500"
          }`}
        >
          Track your health metrics over time
        </p>
      </div>

      <div className="flex items-center gap-4">
        {/* SEARCH */}

        <div
          className={`flex h-10 w-[280px] items-center gap-3 rounded-xl border px-4 ${
            darkMode
              ? "border-slate-700 bg-slate-900/40"
              : "border-slate-200 bg-slate-50"
          }`}
        >
          <Search
            size={17}
            className={
              darkMode
                ? "text-slate-500"
                : "text-slate-400"
            }
          />

          <input
            className={`w-full bg-transparent text-sm outline-none ${
              darkMode
                ? "text-white placeholder:text-slate-500"
                : "text-slate-900 placeholder:text-slate-400"
            }`}
            placeholder="Search anything..."
          />
        </div>

        {/* THEME BUTTON */}

        <button
          type="button"
          onClick={toggleTheme}
          className={`flex h-10 w-10 items-center justify-center rounded-xl border transition-colors ${
            darkMode
              ? "border-slate-700 bg-slate-900 text-yellow-300"
              : "border-slate-200 bg-slate-50 text-slate-700"
          }`}
        >
          {darkMode ? (
            <Sun size={19} />
          ) : (
            <Moon size={19} />
          )}
        </button>

        {/* NOTIFICATIONS */}

        <button
          type="button"
          className={`relative ${
            darkMode
              ? "text-slate-300"
              : "text-slate-600"
          }`}
        >
          <Bell size={21} />

          <span
            className={`absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full border-2 ${
              darkMode
                ? "border-[#111c1b]"
                : "border-white"
            } bg-emerald-500`}
          />
        </button>

        {/* PROFILE */}

        <Link
          to="/patient/settings"
          className="flex items-center gap-3"
        >
          <img
            src="https://i.pravatar.cc/100?img=12"
            alt="John Doe"
            className="h-10 w-10 rounded-full object-cover"
          />

          <span
            className={`text-[14px] font-semibold ${
              darkMode
                ? "text-white"
                : "text-slate-900"
            }`}
          >
            John Doe
          </span>

          <ChevronDown
            size={16}
            className={
              darkMode
                ? "text-slate-400"
                : "text-slate-500"
            }
          />
        </Link>
      </div>
    </header>
  );
}

/* ---------------------------------------------------------
   METRIC CARD
--------------------------------------------------------- */

function MetricCard({
  icon,
  label,
  value,
  unit,
  badge,
  darkMode,
}) {
  return (
    <div
      className={`rounded-[14px] border p-5 transition-colors duration-200 ${
        darkMode
          ? "border-slate-800 bg-[#15211f]"
          : "border-slate-200 bg-white shadow-sm"
      }`}
    >
      <div className="flex items-start justify-between">
        <div
          className={`flex h-9 w-9 items-center justify-center rounded-full ${
            darkMode
              ? "bg-emerald-500/10"
              : "bg-emerald-50"
          }`}
        >
          {icon}
        </div>

        <span
          className={`rounded-full px-2 py-1 text-[10px] font-medium ${
            darkMode
              ? "bg-emerald-500/10 text-emerald-500"
              : "bg-emerald-50 text-emerald-600"
          }`}
        >
          {badge}
        </span>
      </div>

      <p
        className={`mt-3 text-[11px] ${
          darkMode
            ? "text-slate-300"
            : "text-slate-600"
        }`}
      >
        {label}
      </p>

      <div className="mt-1 flex items-baseline gap-1.5">
        <span
          className={`text-[25px] font-semibold ${
            darkMode
              ? "text-white"
              : "text-slate-900"
          }`}
        >
          {value}
        </span>

        <span
          className={`text-[9px] ${
            darkMode
              ? "text-slate-500"
              : "text-slate-400"
          }`}
        >
          {unit}
        </span>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------
   BLOOD GLUCOSE CHART
--------------------------------------------------------- */

function BloodGlucoseCard({ darkMode }) {
  const chartGrid = darkMode
    ? "#263936"
    : "#e2e8f0";

  const chartText = darkMode
    ? "#64748b"
    : "#94a3b8";

  const tooltipBg = darkMode
    ? "#101918"
    : "#ffffff";

  const tooltipBorder = darkMode
    ? "#334155"
    : "#e2e8f0";

  const tooltipText = darkMode
    ? "#e2e8f0"
    : "#334155";

  return (
    <section
      className={`min-h-0 flex-1 rounded-[14px] border p-4 transition-colors duration-200 ${
        darkMode
          ? "border-slate-800 bg-[#15211f]"
          : "border-slate-200 bg-white shadow-sm"
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <h3
            className={`text-[14px] font-bold ${
              darkMode
                ? "text-white"
                : "text-slate-900"
            }`}
          >
            Blood Glucose
          </h3>

          <p
            className={`mt-1 text-[9px] ${
              darkMode
                ? "text-slate-500"
                : "text-slate-400"
            }`}
          >
            Recorded readings over time
          </p>
        </div>

        <span className="flex items-center gap-1 text-[9px] text-emerald-500">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          Glucose
        </span>
      </div>

      <div className="mt-3 h-[230px]">
        <ResponsiveContainer
          width="100%"
          height="100%"
        >
          <LineChart
            data={glucoseData}
            margin={{
              top: 4,
              right: 4,
              left: -24,
              bottom: 0,
            }}
          >
            <CartesianGrid
              stroke={chartGrid}
              strokeDasharray="2 4"
            />

            <XAxis
              dataKey="day"
              axisLine={false}
              tickLine={false}
              tick={{
                fontSize: 8,
                fill: chartText,
              }}
            />

            <YAxis
              domain={[80, 120]}
              axisLine={false}
              tickLine={false}
              tick={{
                fontSize: 8,
                fill: chartText,
              }}
            />

            <Tooltip
              content={({ active, payload, label }) => {
                if (
                  !active ||
                  !payload?.length
                ) {
                  return null;
                }

                return (
                  <div
                    className="rounded-xl border px-3 py-2"
                    style={{
                      backgroundColor:
                        tooltipBg,
                      borderColor:
                        tooltipBorder,
                      color: tooltipText,
                    }}
                  >
                    <p className="text-[9px] font-semibold">
                      {label}
                    </p>

                    <p className="mt-1 text-[9px]">
                      Blood glucose:{" "}
                      <strong>
                        {payload[0]?.value} mg/dL
                      </strong>
                    </p>
                  </div>
                );
              }}
            />

            <Line
              type="monotone"
              dataKey="value"
              stroke="#31b481"
              strokeWidth={2}
              dot={false}
              activeDot={{
                r: 5,
                fill: darkMode
                  ? "#15211f"
                  : "#ffffff",
                stroke: "#31b481",
                strokeWidth: 2,
              }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

/* ---------------------------------------------------------
   RECENT MEASUREMENTS
--------------------------------------------------------- */

function RecentMeasurements({ darkMode }) {
  const rows = [
    {
      label: "Blood glucose",
      date: "22 May",
      value: "102 mg/dL",
    },
    {
      label: "Blood pressure",
      date: "22 May",
      value: "120/78 mmHg",
    },
    {
      label: "Blood glucose",
      date: "19 May",
      value: "101 mg/dL",
    },
  ];

  return (
    <section
      className={`shrink-0 rounded-[14px] border p-4 transition-colors duration-200 ${
        darkMode
          ? "border-slate-800 bg-[#15211f]"
          : "border-slate-200 bg-white shadow-sm"
      }`}
    >
      <div className="flex items-center justify-between">
        <div>
          <h3
            className={`text-[13px] font-bold ${
              darkMode
                ? "text-white"
                : "text-slate-900"
            }`}
          >
            Recent Measurements
          </h3>

          <p
            className={`mt-1 text-[9px] ${
              darkMode
                ? "text-slate-500"
                : "text-slate-400"
            }`}
          >
            Latest recorded health values
          </p>
        </div>

        <span
          className={`rounded-full px-2 py-1 text-[8px] font-medium ${
            darkMode
              ? "bg-emerald-500/10 text-emerald-500"
              : "bg-emerald-50 text-emerald-600"
          }`}
        >
          26 records
        </span>
      </div>

      <div
        className={`mt-2 divide-y ${
          darkMode
            ? "divide-slate-800"
            : "divide-slate-200"
        }`}
      >
        {rows.map((row) => (
          <div
            key={`${row.label}-${row.date}`}
            className="flex items-center justify-between py-2"
          >
            <div>
              <p
                className={`text-[10px] font-medium ${
                  darkMode
                    ? "text-slate-200"
                    : "text-slate-700"
                }`}
              >
                {row.label}
              </p>

              <p
                className={`text-[8px] ${
                  darkMode
                    ? "text-slate-500"
                    : "text-slate-400"
                }`}
              >
                {row.date}
              </p>
            </div>

            <span
              className={`text-[10px] font-semibold ${
                darkMode
                  ? "text-white"
                  : "text-slate-900"
              }`}
            >
              {row.value}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ---------------------------------------------------------
   AI INSIGHT
--------------------------------------------------------- */

function AIInsight({ darkMode }) {
  return (
    <section
      className={`flex h-full min-h-0 flex-col rounded-[14px] border p-5 transition-colors duration-200 ${
        darkMode
          ? "border-slate-800 bg-[#15211f]"
          : "border-slate-200 bg-white shadow-sm"
      }`}
    >
      {/* HEADER */}

      <div className="flex shrink-0 items-start justify-between">
        <div className="flex items-center gap-3">
          <div
            className={`flex h-9 w-9 items-center justify-center rounded-full ${
              darkMode
                ? "bg-emerald-500/10"
                : "bg-emerald-50"
            }`}
          >
            <Sparkles
              size={17}
              className="text-emerald-500"
            />
          </div>

          <div>
            <h3
              className={`text-[15px] font-bold ${
                darkMode
                  ? "text-white"
                  : "text-slate-900"
              }`}
            >
              AI Trend Insight
            </h3>

            <p
              className={`mt-0.5 text-[9px] ${
                darkMode
                  ? "text-slate-500"
                  : "text-slate-400"
              }`}
            >
              Your health trends analyzed
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            className={`rounded-xl border px-4 py-2 text-[10px] font-medium ${
              darkMode
                ? "border-slate-700 bg-[#101918] text-slate-200"
                : "border-slate-200 bg-white text-slate-700"
            }`}
          >
            Export
          </button>

          <span
            className={`rounded-full px-2 py-1 text-[8px] font-medium ${
              darkMode
                ? "bg-emerald-500/10 text-emerald-500"
                : "bg-emerald-50 text-emerald-600"
            }`}
          >
            AI
          </span>
        </div>
      </div>

      {/* MAIN INSIGHT */}

      <div className="mt-5 flex flex-1 flex-col">
        <div
          className={`flex-1 rounded-xl border p-4 ${
            darkMode
              ? "border-slate-800 bg-[#101918]"
              : "border-slate-200 bg-slate-50"
          }`}
        >
          <p
            className={`text-[11px] leading-6 ${
              darkMode
                ? "text-slate-300"
                : "text-slate-600"
            }`}
          >
            Your recent blood glucose readings
            have remained relatively stable,
            with only minor variation across
            the recorded period.
          </p>

          <p
            className={`mt-5 text-[11px] leading-6 ${
              darkMode
                ? "text-slate-300"
                : "text-slate-600"
            }`}
          >
            The highest recorded value appears
            around the beginning of May, followed
            by a return toward your recent average.
          </p>

          <p
            className={`mt-5 text-[11px] leading-6 ${
              darkMode
                ? "text-slate-300"
                : "text-slate-600"
            }`}
          >
            Keep your measurements up to date so
            your health trends can be reviewed over
            time.
          </p>
        </div>

        {/* STATS */}

        <div className="mt-4 grid shrink-0 grid-cols-2 gap-3">
          <div
            className={`rounded-xl border p-4 ${
              darkMode
                ? "border-slate-800 bg-[#101918]"
                : "border-slate-200 bg-slate-50"
            }`}
          >
            <p
              className={`text-[9px] ${
                darkMode
                  ? "text-slate-500"
                  : "text-slate-400"
              }`}
            >
              Latest reading
            </p>

            <p
              className={`mt-2 text-[18px] font-semibold ${
                darkMode
                  ? "text-white"
                  : "text-slate-900"
              }`}
            >
              102{" "}
              <span
                className={`text-[9px] font-normal ${
                  darkMode
                    ? "text-slate-500"
                    : "text-slate-400"
                }`}
              >
                mg/dL
              </span>
            </p>
          </div>

          <div
            className={`rounded-xl border p-4 ${
              darkMode
                ? "border-slate-800 bg-[#101918]"
                : "border-slate-200 bg-slate-50"
            }`}
          >
            <p
              className={`text-[9px] ${
                darkMode
                  ? "text-slate-500"
                  : "text-slate-400"
              }`}
            >
              Recent trend
            </p>

            <p
              className={`mt-2 text-[14px] font-semibold ${
                darkMode
                  ? "text-white"
                  : "text-slate-900"
              }`}
            >
              Stable
            </p>
          </div>
        </div>

        {/* BUTTON */}

        <button
          type="button"
          className="mt-4 shrink-0 rounded-lg bg-emerald-500 px-3 py-3 text-[10px] font-semibold text-white transition-colors hover:bg-emerald-600"
        >
          View detailed analysis
        </button>
      </div>
    </section>
  );
}

/* ---------------------------------------------------------
   MAIN HEALTH TRENDS PAGE
--------------------------------------------------------- */

export default function HealthTrends() {
  const { isDark: darkMode, toggleTheme } = useTheme();

  return (
    <div
      className={`h-screen w-full overflow-hidden p-2 transition-colors duration-200 ${
        darkMode
          ? "bg-[#0b1413]"
          : "bg-slate-100"
      }`}
    >
      <div
        className={`relative flex h-full w-full overflow-hidden rounded-[18px] border transition-colors duration-200 ${
          darkMode
            ? "border-slate-800 bg-[#111c1b]"
            : "border-slate-200 bg-white"
        }`}
      >
        {/* UNIVERSAL SIDEBAR */}
        <Sidebar darkMode={darkMode} />

        {/* MAIN CONTENT
            Sidebar is fixed, so reserve its width here. */}
        <main className="ml-[255px] flex min-w-0 flex-1 flex-col overflow-hidden">
          <Header
            darkMode={darkMode}
            toggleTheme={toggleTheme}
          />

          <div className="flex min-h-0 flex-1 flex-col overflow-hidden px-6 pb-3 pt-3">
            {/* METRIC CARDS */}

            <div className="grid shrink-0 grid-cols-3 gap-3">
              {/* BLOOD PRESSURE */}

              <MetricCard
                darkMode={darkMode}
                icon={
                  <Activity
                    size={17}
                    className="text-emerald-500"
                  />
                }
                label="Blood Pressure"
                value="120/78"
                unit="mmHg latest"
                badge="Normal"
              />

              {/* BMI */}

              <MetricCard
                darkMode={darkMode}
                icon={
                  <Thermometer
                    size={17}
                    className="text-emerald-500"
                  />
                }
                label="BMI"
                value="23.4"
                unit="kg/m²"
                badge="Normal"
              />

              {/* RECORDED MEASUREMENTS */}

              <MetricCard
                darkMode={darkMode}
                icon={
                  <ClipboardList
                    size={17}
                    className="text-emerald-500"
                  />
                }
                label="Recorded Measurements"
                value="26"
                unit="records"
                badge="Updated"
              />
            </div>

            {/* MAIN GRID */}

            <div className="mt-3 grid min-h-0 flex-1 grid-cols-[1.72fr_0.78fr] gap-3">
              {/* LEFT COLUMN */}

              <div className="flex min-h-0 min-w-0 flex-col gap-3">
                <BloodGlucoseCard
                  darkMode={darkMode}
                />

                <div className="min-h-[260px] flex-1 pt-17">
                  <RecentMeasurements
                    darkMode={darkMode}
                  />
                </div>
              </div>

              {/* RIGHT COLUMN */}

              <div className="min-h-0">
                <AIInsight
                  darkMode={darkMode}
                />
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}