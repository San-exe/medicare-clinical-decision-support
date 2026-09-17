import React, { useMemo, useState } from "react";

import {
  Search,
  Bell,
  ChevronDown,
  FileText,
  Filter,
  Download,
  Eye,
  MoreHorizontal,
  CalendarDays,
  AlertCircle,
  CheckCircle2,
  Clock3,
  ArrowUpDown,
} from "lucide-react";

import Sidebar from "./sidebar";
import { useTheme } from "../ThemeContext";


// =========================================================
// REPORT DATA
// =========================================================

const reports = [
  {
    id: "RPT-8421",
    patient: "Aarav Mehta",
    type: "Blood Test",
    category: "Laboratory",
    date: "Aug 21, 2026",
    status: "Reviewed",
    priority: "Normal",
  },
  {
    id: "RPT-8420",
    patient: "Rohan Desai",
    type: "Lipid Profile",
    category: "Laboratory",
    date: "Aug 20, 2026",
    status: "Needs Review",
    priority: "High",
  },
  {
    id: "RPT-8419",
    patient: "Priya Sharma",
    type: "HbA1c",
    category: "Laboratory",
    date: "Aug 20, 2026",
    status: "Pending",
    priority: "Medium",
  },
  {
    id: "RPT-8418",
    patient: "Ananya Patel",
    type: "MRI Scan",
    category: "Imaging",
    date: "Aug 19, 2026",
    status: "Reviewed",
    priority: "Normal",
  },
  {
    id: "RPT-8417",
    patient: "Arjun Rao",
    type: "ECG",
    category: "Cardiology",
    date: "Aug 18, 2026",
    status: "Needs Review",
    priority: "High",
  },
  {
    id: "RPT-8416",
    patient: "Meera Kapoor",
    type: "Thyroid Panel",
    category: "Laboratory",
    date: "Aug 17, 2026",
    status: "Reviewed",
    priority: "Normal",
  },
  {
    id: "RPT-8415",
    patient: "Vikram Singh",
    type: "Kidney Function",
    category: "Laboratory",
    date: "Aug 16, 2026",
    status: "Pending",
    priority: "Medium",
  },
  {
    id: "RPT-8414",
    patient: "Neha Joshi",
    type: "Chest X-Ray",
    category: "Imaging",
    date: "Aug 15, 2026",
    status: "Reviewed",
    priority: "Normal",
  },
];


// =========================================================
// STATUS
// =========================================================

function StatusBadge({ status }) {
  const config = {
    Reviewed: {
      icon: CheckCircle2,
      className:
        "bg-emerald-500/10 text-emerald-500",
    },

    "Needs Review": {
      icon: AlertCircle,
      className:
        "bg-red-500/10 text-red-500",
    },

    Pending: {
      icon: Clock3,
      className:
        "bg-amber-500/10 text-amber-500",
    },
  };

  const item =
    config[status] || config.Pending;

  const Icon = item.icon;

  return (
    <span
      className={`
        inline-flex
        items-center
        gap-1.5
        rounded-full
        px-2.5
        py-1
        text-[11px]
        font-medium
        ${item.className}
      `}
    >
      <Icon size={12} />
      {status}
    </span>
  );
}


// =========================================================
// PRIORITY
// =========================================================

function PriorityBadge({ priority }) {
  const styles = {
    Normal:
      "bg-[var(--card-soft)] text-[var(--muted)]",
    Medium:
      "bg-amber-500/10 text-amber-500",
    High:
      "bg-red-500/10 text-red-500",
  };

  return (
    <span
      className={`
        inline-flex
        rounded-full
        px-2.5
        py-1
        text-[11px]
        font-medium
        ${styles[priority]}
      `}
    >
      {priority}
    </span>
  );
}


// =========================================================
// REPORTS PAGE
// =========================================================

export default function Reports() {
  const { isDark, toggleTheme } =
    useTheme();

  const [search, setSearch] =
    useState("");

  const [statusFilter, setStatusFilter] =
    useState("All");

  const [categoryFilter, setCategoryFilter] =
    useState("All");

  const filteredReports =
    useMemo(() => {
      const query =
        search.trim().toLowerCase();

      return reports.filter((report) => {
        const matchesSearch =
          !query ||
          report.patient
            .toLowerCase()
            .includes(query) ||
          report.id
            .toLowerCase()
            .includes(query) ||
          report.type
            .toLowerCase()
            .includes(query) ||
          report.category
            .toLowerCase()
            .includes(query);

        const matchesStatus =
          statusFilter === "All" ||
          report.status === statusFilter;

        const matchesCategory =
          categoryFilter === "All" ||
          report.category === categoryFilter;

        return (
          matchesSearch &&
          matchesStatus &&
          matchesCategory
        );
      });
    }, [
      search,
      statusFilter,
      categoryFilter,
    ]);

  return (
    <div
      className="
        h-dvh
        min-h-0
        overflow-hidden
        bg-[var(--bg)]
        text-[var(--text)]
      "
      style={{
        colorScheme: isDark
          ? "dark"
          : "light",
      }}
    >
      <div className="flex h-full min-h-0">

        {/* =================================================
            SIDEBAR
        ================================================= */}

        <Sidebar />


        {/* =================================================
            MAIN
        ================================================= */}

        <main className="ml-[217px] min-h-0 min-w-0 w-[calc(100%-217px)] flex-none overflow-hidden">

          {/* =================================================
              HEADER
          ================================================= */}

          <header
            className="
              flex
              h-[72px]
              shrink-0
              items-center
              justify-between
              gap-4

              border-b
              border-[var(--border)]

              px-5
              sm:px-7
              lg:px-8
            "
          >

            <h1 className="text-[26px] font-bold tracking-tight">
              Reports
            </h1>


            <div className="flex items-center gap-3">

              {/* SEARCH */}

              <div
                className="
                  hidden
                  h-10
                  w-[280px]
                  items-center
                  gap-3

                  rounded-xl

                  border
                  border-[var(--border-soft)]

                  bg-[var(--card-soft)]

                  px-4

                  md:flex
                "
              >
                <Search
                  size={18}
                  className="text-[var(--muted)]"
                />

                <input
                  value={search}
                  onChange={(event) =>
                    setSearch(
                      event.target.value
                    )
                  }
                  placeholder="Search reports..."
                  className="
                    w-full
                    bg-transparent
                    text-sm
                    outline-none
                    placeholder:text-[var(--muted)]
                  "
                />
              </div>


              {/* THEME */}

              <button
                type="button"
                onClick={toggleTheme}
                className="
                  flex
                  h-10
                  w-10
                  items-center
                  justify-center

                  rounded-xl

                  border
                  border-[var(--border-soft)]

                  bg-[var(--card-soft)]

                  text-[var(--accent)]
                "
              >
                <span className="text-xl">
                  {isDark ? "☼" : "☾"}
                </span>
              </button>


              {/* NOTIFICATION */}

              <button
                type="button"
                className="
                  relative
                  p-2
                  text-[var(--text-secondary)]
                "
              >
                <Bell size={20} />

                <span
                  className="
                    absolute
                    right-1.5
                    top-1.5
                    h-2
                    w-2
                    rounded-full
                    bg-[var(--accent)]
                  "
                />
              </button>


              {/* PROFILE */}

              <div className="hidden items-center gap-2 sm:flex">

                <div
                  className="
                    flex
                    h-10
                    w-10
                    items-center
                    justify-center
                    rounded-full
                    bg-[var(--accent-soft)]
                  "
                >
                  <FileText
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


          {/* =================================================
              CONTENT
          ================================================= */}

          <section
            className="
              grid
              h-[calc(100vh-72px)]
              min-h-0

              grid-rows-[auto_auto_minmax(0,1fr)]

              gap-4

              overflow-hidden

              px-5
              py-5

              sm:px-7
              lg:px-8
            "
          >

            {/* =================================================
                INTRO
            ================================================= */}

            <div className="flex items-end justify-between gap-4">

              <div>

                <h2 className="text-[22px] font-bold">
                  Clinical Reports
                </h2>

                <p className="mt-1 text-sm text-[var(--muted)]">
                  Review laboratory, imaging, and
                  diagnostic reports from your patients.
                </p>

              </div>


              <button
                type="button"
                className="
                  hidden
                  shrink-0
                  items-center
                  gap-2

                  rounded-xl

                  border
                  border-[var(--border-soft)]

                  bg-[var(--card-soft)]

                  px-4
                  py-2.5

                  text-sm
                  font-medium

                  text-[var(--text-secondary)]

                  sm:flex
                "
              >
                <Download size={16} />

                Export
              </button>

            </div>


            {/* =================================================
                SUMMARY
            ================================================= */}

            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">

              <div
                className="
                  rounded-2xl
                  border
                  border-[var(--border)]
                  bg-[var(--card)]
                  px-4
                  py-3
                "
              >
                <div className="flex items-center justify-between">

                  <span className="text-xs text-[var(--muted)]">
                    Total Reports
                  </span>

                  <FileText
                    size={17}
                    className="text-[var(--accent)]"
                  />

                </div>

                <p className="mt-2 text-2xl font-bold">
                  186
                </p>
              </div>


              <div
                className="
                  rounded-2xl
                  border
                  border-[var(--border)]
                  bg-[var(--card)]
                  px-4
                  py-3
                "
              >
                <div className="flex items-center justify-between">

                  <span className="text-xs text-[var(--muted)]">
                    Needs Review
                  </span>

                  <AlertCircle
                    size={17}
                    className="text-red-500"
                  />

                </div>

                <p className="mt-2 text-2xl font-bold">
                  12
                </p>
              </div>


              <div
                className="
                  rounded-2xl
                  border
                  border-[var(--border)]
                  bg-[var(--card)]
                  px-4
                  py-3
                "
              >
                <div className="flex items-center justify-between">

                  <span className="text-xs text-[var(--muted)]">
                    Pending
                  </span>

                  <Clock3
                    size={17}
                    className="text-amber-500"
                  />

                </div>

                <p className="mt-2 text-2xl font-bold">
                  07
                </p>
              </div>


              <div
                className="
                  rounded-2xl
                  border
                  border-[var(--border)]
                  bg-[var(--card)]
                  px-4
                  py-3
                "
              >
                <div className="flex items-center justify-between">

                  <span className="text-xs text-[var(--muted)]">
                    Reviewed
                  </span>

                  <CheckCircle2
                    size={17}
                    className="text-emerald-500"
                  />

                </div>

                <p className="mt-2 text-2xl font-bold">
                  167
                </p>
              </div>

            </div>


            {/* =================================================
                REPORT TABLE
            ================================================= */}

            <div
              className="
                flex
                min-h-0
                flex-col
                overflow-hidden

                rounded-2xl

                border
                border-[var(--border)]

                bg-[var(--card)]
              "
            >

              {/* TOOLBAR */}

              <div
                className="
                  flex
                  shrink-0
                  flex-wrap
                  items-center
                  justify-between
                  gap-3

                  border-b
                  border-[var(--border)]

                  px-4
                  py-3
                "
              >

                <div className="flex items-center gap-2">

                  <Filter
                    size={16}
                    className="text-[var(--muted)]"
                  />

                  <span className="text-sm font-medium">
                    Report List
                  </span>

                  <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-[10px] font-medium text-[var(--accent)]">
                    {filteredReports.length}
                  </span>

                </div>


                <div className="flex items-center gap-2">

                  {/* STATUS */}

                  <select
                    value={statusFilter}
                    onChange={(event) =>
                      setStatusFilter(
                        event.target.value
                      )
                    }
                    className="
                      rounded-lg

                      border
                      border-[var(--border-soft)]

                      bg-[var(--card-soft)]

                      px-3
                      py-1.5

                      text-xs

                      text-[var(--text-secondary)]

                      outline-none
                    "
                  >
                    <option value="All">
                      All Status
                    </option>

                    <option value="Reviewed">
                      Reviewed
                    </option>

                    <option value="Needs Review">
                      Needs Review
                    </option>

                    <option value="Pending">
                      Pending
                    </option>
                  </select>


                  {/* CATEGORY */}

                  <select
                    value={categoryFilter}
                    onChange={(event) =>
                      setCategoryFilter(
                        event.target.value
                      )
                    }
                    className="
                      hidden
                      rounded-lg

                      border
                      border-[var(--border-soft)]

                      bg-[var(--card-soft)]

                      px-3
                      py-1.5

                      text-xs

                      text-[var(--text-secondary)]

                      outline-none

                      sm:block
                    "
                  >
                    <option value="All">
                      All Categories
                    </option>

                    <option value="Laboratory">
                      Laboratory
                    </option>

                    <option value="Imaging">
                      Imaging
                    </option>

                    <option value="Cardiology">
                      Cardiology
                    </option>
                  </select>


                  <button
                    type="button"
                    className="
                      flex
                      h-8
                      w-8
                      items-center
                      justify-center

                      rounded-lg

                      text-[var(--muted)]

                      hover:bg-[var(--card-soft)]
                    "
                  >
                    <ArrowUpDown size={15} />
                  </button>

                </div>

              </div>


              {/* TABLE */}

              <div className="min-h-0 flex-1 overflow-hidden">

                <table className="w-full table-fixed border-collapse">

                  <thead>
                    <tr className="border-b border-[var(--border)]">

                      <th className="w-[13%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                        Report ID
                      </th>

                      <th className="w-[20%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                        Patient
                      </th>

                      <th className="w-[21%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                        Report
                      </th>

                      <th className="hidden w-[14%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)] md:table-cell">
                        Date
                      </th>

                      <th className="hidden w-[12%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)] lg:table-cell">
                        Priority
                      </th>

                      <th className="w-[15%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                        Status
                      </th>

                      <th className="w-[5%] px-2 py-3" />

                    </tr>
                  </thead>


                  <tbody>

                    {filteredReports.map(
                      (report) => (
                        <tr
                          key={report.id}
                          className="
                            border-b
                            border-[var(--border)]
                            transition
                            hover:bg-[var(--card-soft)]
                            last:border-b-0
                          "
                        >

                          {/* ID */}

                          <td className="px-4 py-3 text-xs font-medium text-[var(--muted)]">
                            {report.id}
                          </td>


                          {/* PATIENT */}

                          <td className="px-4 py-3">

                            <p className="truncate text-sm font-semibold">
                              {report.patient}
                            </p>

                            <p className="mt-0.5 text-[11px] text-[var(--muted)]">
                              Patient
                            </p>

                          </td>


                          {/* REPORT */}

                          <td className="px-4 py-3">

                            <div className="flex min-w-0 items-center gap-2.5">

                              <div
                                className="
                                  flex
                                  h-8
                                  w-8
                                  shrink-0
                                  items-center
                                  justify-center
                                  rounded-lg
                                  bg-[var(--accent-soft)]
                                "
                              >
                                <FileText
                                  size={15}
                                  className="text-[var(--accent)]"
                                />
                              </div>

                              <div className="min-w-0">

                                <p className="truncate text-sm font-medium">
                                  {report.type}
                                </p>

                                <p className="truncate text-[10px] text-[var(--muted)]">
                                  {report.category}
                                </p>

                              </div>

                            </div>

                          </td>


                          {/* DATE */}

                          <td className="hidden px-4 py-3 text-xs text-[var(--muted)] md:table-cell">
                            <div className="flex items-center gap-2">

                              <CalendarDays
                                size={14}
                              />

                              {report.date}

                            </div>
                          </td>


                          {/* PRIORITY */}

                          <td className="hidden px-4 py-3 lg:table-cell">
                            <PriorityBadge
                              priority={
                                report.priority
                              }
                            />
                          </td>


                          {/* STATUS */}

                          <td className="px-4 py-3">
                            <StatusBadge
                              status={
                                report.status
                              }
                            />
                          </td>


                          {/* ACTIONS */}

                          <td className="px-2 py-3">

                            <div className="flex items-center gap-1">

                              <button
                                type="button"
                                aria-label={`View ${report.id}`}
                                className="
                                  hidden
                                  h-8
                                  w-8
                                  items-center
                                  justify-center
                                  rounded-lg
                                  text-[var(--muted)]
                                  hover:bg-[var(--card-soft)]
                                  hover:text-[var(--text)]
                                  sm:flex
                                "
                              >
                                <Eye size={16} />
                              </button>

                              <button
                                type="button"
                                aria-label={`More actions for ${report.id}`}
                                className="
                                  flex
                                  h-8
                                  w-8
                                  items-center
                                  justify-center
                                  rounded-lg
                                  text-[var(--muted)]
                                  hover:bg-[var(--card-soft)]
                                  hover:text-[var(--text)]
                                "
                              >
                                <MoreHorizontal
                                  size={16}
                                />
                              </button>

                            </div>

                          </td>

                        </tr>
                      )
                    )}

                  </tbody>

                </table>


                {/* EMPTY */}

                {filteredReports.length ===
                  0 && (
                  <div className="flex h-full items-center justify-center">

                    <div className="text-center">

                      <FileText
                        size={34}
                        className="mx-auto text-[var(--muted)]"
                      />

                      <p className="mt-3 text-sm font-medium">
                        No reports found
                      </p>

                      <p className="mt-1 text-xs text-[var(--muted)]">
                        Try changing your search or filters.
                      </p>

                    </div>

                  </div>
                )}

              </div>

            </div>

          </section>

        </main>

      </div>
    </div>
  );
}