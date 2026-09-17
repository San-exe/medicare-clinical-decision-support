import React, { useMemo, useState } from "react";
import {
  Search,
  Bell,
  ChevronDown,
  Sparkles,
  Brain,
  AlertTriangle,
  TrendingUp,
  Activity,
  UserRound,
  ArrowRight,
  Clock3,
  ShieldCheck,
  MoreHorizontal,
  SlidersHorizontal,
} from "lucide-react";

import Sidebar from "./sidebar";
import { useTheme } from "../ThemeContext";

const insights = [
  {
    id: "AI-1024",
    patient: "Rohan Desai",
    type: "Risk Alert",
    title: "Cardiovascular risk increased",
    description:
      "Recent vitals and lipid results indicate an elevated cardiovascular risk pattern.",
    severity: "High",
    confidence: "94%",
    time: "18 min ago",
  },
  {
    id: "AI-1023",
    patient: "Priya Sharma",
    type: "Trend",
    title: "Glucose trend requires monitoring",
    description:
      "Average glucose readings have increased over the previous 14 days.",
    severity: "Medium",
    confidence: "89%",
    time: "42 min ago",
  },
  {
    id: "AI-1022",
    patient: "Arjun Rao",
    type: "Prediction",
    title: "Hypertension pattern detected",
    description:
      "Multiple recent readings are consistent with a persistent elevated blood-pressure pattern.",
    severity: "High",
    confidence: "91%",
    time: "1 hr ago",
  },
  {
    id: "AI-1021",
    patient: "Ananya Patel",
    type: "Recommendation",
    title: "Follow-up may be beneficial",
    description:
      "The patient's recent symptom pattern suggests a routine follow-up could be considered.",
    severity: "Low",
    confidence: "83%",
    time: "2 hrs ago",
  },
  {
    id: "AI-1020",
    patient: "Vikram Singh",
    type: "Trend",
    title: "HbA1c trend improving",
    description:
      "Recent laboratory values show a favorable change compared with previous measurements.",
    severity: "Low",
    confidence: "96%",
    time: "3 hrs ago",
  },
  {
    id: "AI-1019",
    patient: "Meera Kapoor",
    type: "Recommendation",
    title: "Thyroid monitoring suggested",
    description:
      "The latest results may warrant continued monitoring during the next clinical review.",
    severity: "Medium",
    confidence: "86%",
    time: "4 hrs ago",
  },
];

function SeverityBadge({ severity }) {
  const styles = {
    High: "bg-red-500/10 text-red-500",
    Medium: "bg-amber-500/10 text-amber-500",
    Low: "bg-emerald-500/10 text-emerald-500",
  };

  return (
    <span
      className={`rounded-full px-2.5 py-1 text-[11px] font-medium ${styles[severity]}`}
    >
      {severity}
    </span>
  );
}

function TypeIcon({ type }) {
  if (type === "Risk Alert") {
    return <AlertTriangle size={16} />;
  }

  if (type === "Trend") {
    return <TrendingUp size={16} />;
  }

  if (type === "Prediction") {
    return <Brain size={16} />;
  }

  return <Sparkles size={16} />;
}

export default function AIInsights() {
  const { isDark, toggleTheme } = useTheme();

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [lastRun, setLastRun] = useState("18 min ago");

  const runAnalysis = () => {
    if (isAnalyzing) return;

    setIsAnalyzing(true);

    window.setTimeout(() => {
      setLastRun("Just now");
      setIsAnalyzing(false);
    }, 900);
  };

  const filteredInsights = useMemo(() => {
    const query = search.trim().toLowerCase();

    return insights.filter((item) => {
      const matchesSearch =
        !query ||
        item.patient.toLowerCase().includes(query) ||
        item.title.toLowerCase().includes(query) ||
        item.description.toLowerCase().includes(query);

      const matchesFilter =
        filter === "All" || item.severity === filter;

      return matchesSearch && matchesFilter;
    });
  }, [search, filter]);

  return (
    <div
      className="h-dvh min-h-0 overflow-hidden medicare-doctor-shell bg-[var(--bg)] text-[var(--text)]"
      style={{ colorScheme: isDark ? "dark" : "light" }}
    >
      <div className="flex h-full min-h-0">

        {/* GLOBAL SIDEBAR */}
        <Sidebar />

        <main className="ml-[217px] min-h-0 min-w-0 w-[calc(100%-217px)] flex-none overflow-hidden">

          {/* HEADER */}
          <header className="flex h-[72px] shrink-0 items-center justify-between border-b border-[var(--border)] px-5 sm:px-7 lg:px-8">

            <h1 className="text-[26px] font-bold tracking-tight">
              AI Insights
            </h1>

            <div className="flex items-center gap-3">

              <div className="hidden h-10 w-[280px] items-center gap-3 rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-4 md:flex">
                <Search
                  size={18}
                  className="text-[var(--muted)]"
                />

                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search insights..."
                  className="w-full bg-transparent text-sm outline-none placeholder:text-[var(--muted)]"
                />
              </div>

              <button
                type="button"
                onClick={toggleTheme}
                className="flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] text-[var(--accent)]"
              >
                <span className="text-xl">
                  {isDark ? "☼" : "☾"}
                </span>
              </button>

              <button
                type="button"
                className="relative p-2 text-[var(--text-secondary)]"
              >
                <Bell size={20} />

                <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-[var(--accent)]" />
              </button>

              <div className="hidden items-center gap-2 sm:flex">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--accent-soft)]">
                  <Sparkles
                    size={18}
                    className="text-[var(--accent)]"
                  />
                </div>

                <ChevronDown
                  size={15}
                  className="text-[var(--muted)]"
                />
              </div>

            </div>
          </header>

          {/* CONTENT */}
          <section className="grid h-[calc(100vh-72px)] min-h-0 grid-rows-[auto_auto_minmax(0,1fr)] gap-4 overflow-hidden px-5 py-5 sm:px-7 lg:px-8">

            {/* INTRO */}
            <div className="flex items-end justify-between gap-4">

              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-[22px] font-bold">
                    Clinical Intelligence
                  </h2>

                  <span className="flex items-center gap-1 rounded-full bg-[var(--accent-soft)] px-2 py-1 text-[10px] font-semibold text-[var(--accent)]">
                    <Sparkles size={11} />
                    AI Powered
                  </span>
                </div>

                <p className="mt-1 text-sm text-[var(--muted)]">
                  AI-generated patterns, risk signals, and
                  clinical insights across your patients.
                </p>
              </div>

              <button
                type="button"
                onClick={runAnalysis}
                disabled={isAnalyzing}
                className="hidden shrink-0 items-center gap-2 rounded-xl bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-[#06231d] transition hover:brightness-105 disabled:cursor-wait disabled:opacity-70 sm:flex"
              >
                <Brain size={16} className={isAnalyzing ? "animate-pulse" : ""} />
                {isAnalyzing ? "Analyzing..." : "Run Analysis"}
              </button>

            </div>

            {/* SUMMARY CARDS */}
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">

              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">
                    Active Insights
                  </span>

                  <Sparkles
                    size={17}
                    className="text-[var(--accent)]"
                  />
                </div>

                <p className="mt-2 text-2xl font-bold">
                  24
                </p>

                <p className="mt-1 text-[10px] text-emerald-500">
                  +6 this week
                </p>
              </div>

              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">
                    High Risk
                  </span>

                  <AlertTriangle
                    size={17}
                    className="text-red-500"
                  />
                </div>

                <p className="mt-2 text-2xl font-bold">
                  05
                </p>

                <p className="mt-1 text-[10px] text-red-500">
                  Requires attention
                </p>
              </div>

              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">
                    Avg. Confidence
                  </span>

                  <ShieldCheck
                    size={17}
                    className="text-emerald-500"
                  />
                </div>

                <p className="mt-2 text-2xl font-bold">
                  91%
                </p>

                <p className="mt-1 text-[10px] text-emerald-500">
                  High confidence
                </p>
              </div>

              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">
                    Analyses Today
                  </span>

                  <Activity
                    size={17}
                    className="text-[var(--accent)]"
                  />
                </div>

                <p className="mt-2 text-2xl font-bold">
                  38
                </p>

                <p className="mt-1 text-[10px] text-[var(--muted)]">
                  Last run {lastRun}
                </p>
              </div>

            </div>

            {/* INSIGHT LIST */}
            <div className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--card)]">

              {/* TOOLBAR */}
              <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] px-4 py-3">

                <div className="flex items-center gap-2">
                  <SlidersHorizontal
                    size={16}
                    className="text-[var(--muted)]"
                  />

                  <span className="text-sm font-medium">
                    Recent Insights
                  </span>

                  <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-[10px] font-medium text-[var(--accent)]">
                    {filteredInsights.length}
                  </span>
                </div>

                <div className="flex items-center gap-1.5">

                  {["All", "High", "Medium", "Low"].map(
                    (item) => (
                      <button
                        key={item}
                        type="button"
                        onClick={() => setFilter(item)}
                        className={`
                          rounded-lg
                          px-3
                          py-1.5
                          text-xs
                          font-medium
                          transition
                          ${
                            filter === item
                              ? "bg-[var(--accent-soft)] text-[var(--accent)]"
                              : "text-[var(--muted)] hover:bg-[var(--card-soft)]"
                          }
                        `}
                      >
                        {item}
                      </button>
                    )
                  )}

                </div>
              </div>

              {/* LIST */}
              <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden">

                <div className="grid min-h-full grid-cols-1">

                  {filteredInsights.map((item) => (
                    <div
                      key={item.id}
                      className="group flex min-h-[78px] items-center gap-4 border-b border-[var(--border)] px-4 transition hover:bg-[var(--card-soft)] last:border-b-0"
                    >

                      {/* ICON */}
                      <div
                        className={`
                          flex
                          h-10
                          w-10
                          shrink-0
                          items-center
                          justify-center
                          rounded-xl

                          ${
                            item.severity === "High"
                              ? "bg-red-500/10 text-red-500"
                              : item.severity === "Medium"
                              ? "bg-amber-500/10 text-amber-500"
                              : "bg-emerald-500/10 text-emerald-500"
                          }
                        `}
                      >
                        <TypeIcon type={item.type} />
                      </div>

                      {/* CONTENT */}
                      <div className="min-w-0 flex-1">

                        <div className="flex items-center gap-2">

                          <p className="truncate text-sm font-semibold">
                            {item.title}
                          </p>

                          <span className="hidden shrink-0 text-[10px] text-[var(--muted)] lg:inline">
                            {item.type}
                          </span>

                        </div>

                        <p className="mt-1 truncate text-xs text-[var(--muted)]">
                          {item.description}
                        </p>

                      </div>

                      {/* PATIENT */}
                      <div className="hidden w-[120px] shrink-0 items-center gap-2 xl:flex">

                        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--accent-soft)]">
                          <UserRound
                            size={13}
                            className="text-[var(--accent)]"
                          />
                        </div>

                        <span className="truncate text-xs font-medium">
                          {item.patient}
                        </span>

                      </div>

                      {/* CONFIDENCE */}
                      <div className="hidden w-[72px] shrink-0 md:block">
                        <p className="text-[10px] text-[var(--muted)]">
                          Confidence
                        </p>

                        <p className="mt-0.5 text-xs font-semibold">
                          {item.confidence}
                        </p>
                      </div>

                      {/* TIME */}
                      <div className="hidden w-[85px] shrink-0 lg:flex items-center gap-1 text-[10px] text-[var(--muted)]">
                        <Clock3 size={12} />
                        {item.time}
                      </div>

                      {/* SEVERITY */}
                      <div className="hidden w-[75px] shrink-0 sm:block">
                        <SeverityBadge severity={item.severity} />
                      </div>

                      {/* ACTION */}
                      <button
                        type="button"
                        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[var(--muted)] hover:bg-[var(--card-soft)] hover:text-[var(--text)]"
                      >
                        <MoreHorizontal size={16} />
                      </button>

                    </div>
                  ))}

                </div>

                {filteredInsights.length === 0 && (
                  <div className="flex h-full items-center justify-center">

                    <div className="text-center">

                      <Brain
                        size={34}
                        className="mx-auto text-[var(--muted)]"
                      />

                      <p className="mt-3 text-sm font-medium">
                        No insights found
                      </p>

                      <p className="mt-1 text-xs text-[var(--muted)]">
                        Try changing your search or filter.
                      </p>

                    </div>

                  </div>
                )}

              </div>

              {/* FOOTER */}
              <div className="flex shrink-0 items-center justify-between border-t border-[var(--border)] px-4 py-2.5">

                <div className="flex items-center gap-2 text-[10px] text-[var(--muted)]">
                  <ShieldCheck
                    size={13}
                    className="text-emerald-500"
                  />

                  AI insights are decision-support tools and
                  require clinical review.
                </div>

                <button
                  type="button"
                  className="hidden items-center gap-1 text-xs font-medium text-[var(--accent)] sm:flex"
                >
                  View all
                  <ArrowRight size={13} />
                </button>

              </div>

            </div>

          </section>
        </main>
      </div>
    </div>
  );
}