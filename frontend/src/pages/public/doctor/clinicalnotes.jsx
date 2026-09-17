import React, { useMemo, useState } from "react";
import {
  Search,
  Bell,
  ChevronDown,
  FileText,
  UserRound,
  CalendarDays,
  Clock3,
  Plus,
  MoreHorizontal,
  Edit3,
  Eye,
  CheckCircle2,
  FilePenLine,
  Stethoscope,
  Save,
} from "lucide-react";

import Sidebar from "./sidebar";
import { useTheme } from "../ThemeContext";

const notes = [
  {
    id: "CN-2048",
    patient: "Aarav Mehta",
    date: "23 Aug 2026",
    time: "09:24 AM",
    type: "Follow-up",
    title: "Diabetes follow-up",
    status: "Draft",
    preview:
      "Patient reports improved glucose control with current medication...",
  },
  {
    id: "CN-2047",
    patient: "Priya Sharma",
    date: "23 Aug 2026",
    time: "08:58 AM",
    type: "Consultation",
    title: "Routine consultation",
    status: "Signed",
    preview:
      "Patient presented for routine review. No new acute complaints...",
  },
  {
    id: "CN-2046",
    patient: "Rohan Desai",
    date: "22 Aug 2026",
    time: "04:35 PM",
    type: "Cardiology",
    title: "Cardiology review",
    status: "Signed",
    preview:
      "Blood pressure remains elevated. Discussed medication adherence...",
  },
  {
    id: "CN-2045",
    patient: "Ananya Patel",
    date: "22 Aug 2026",
    time: "02:12 PM",
    type: "Follow-up",
    title: "Post-treatment review",
    status: "Signed",
    preview:
      "Symptoms have improved since previous visit. Continue current plan...",
  },
  {
    id: "CN-2044",
    patient: "Vikram Singh",
    date: "21 Aug 2026",
    time: "11:47 AM",
    type: "Hypertension",
    title: "Blood pressure review",
    status: "Draft",
    preview:
      "Recent home readings reviewed. Continue monitoring and lifestyle changes...",
  },
  {
    id: "CN-2043",
    patient: "Meera Kapoor",
    date: "21 Aug 2026",
    time: "10:15 AM",
    type: "Consultation",
    title: "Thyroid follow-up",
    status: "Signed",
    preview:
      "Latest thyroid function results reviewed with the patient...",
  },
];

function StatusBadge({ status }) {
  if (status === "Signed") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-[10px] font-medium text-emerald-500">
        <CheckCircle2 size={12} />
        Signed
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-[10px] font-medium text-amber-500">
      <FilePenLine size={12} />
      Draft
    </span>
  );
}

export default function ClinicalNotes() {
  const { isDark, toggleTheme } = useTheme();

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");

  const filteredNotes = useMemo(() => {
    const query = search.trim().toLowerCase();

    return notes.filter((note) => {
      const matchesSearch =
        !query ||
        note.patient.toLowerCase().includes(query) ||
        note.title.toLowerCase().includes(query) ||
        note.type.toLowerCase().includes(query) ||
        note.id.toLowerCase().includes(query);

      const matchesFilter =
        filter === "All" || note.status === filter;

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
              Clinical Notes
            </h1>

            <div className="flex items-center gap-3">

              {/* SEARCH */}
              <div className="hidden h-10 w-[280px] items-center gap-3 rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-4 md:flex">
                <Search
                  size={18}
                  className="text-[var(--muted)]"
                />

                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search notes..."
                  className="w-full bg-transparent text-sm outline-none placeholder:text-[var(--muted)]"
                />
              </div>

              {/* THEME */}
              <button
                type="button"
                onClick={toggleTheme}
                className="flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] text-[var(--accent)]"
              >
                <span className="text-xl">
                  {isDark ? "☼" : "☾"}
                </span>
              </button>

              {/* NOTIFICATIONS */}
              <button
                type="button"
                className="relative p-2 text-[var(--text-secondary)]"
              >
                <Bell size={20} />

                <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-[var(--accent)]" />
              </button>

              {/* PROFILE */}
              <div className="hidden items-center gap-2 sm:flex">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--accent-soft)]">
                  <Stethoscope
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

          {/* PAGE */}
          <section className="grid h-[calc(100vh-72px)] min-h-0 grid-rows-[auto_auto_minmax(0,1fr)] gap-4 overflow-hidden px-5 py-5 sm:px-7 lg:px-8">

            {/* INTRO */}
            <div className="flex items-end justify-between gap-4">

              <div>
                <h2 className="text-[22px] font-bold">
                  Patient Clinical Notes
                </h2>

                <p className="mt-1 text-sm text-[var(--muted)]">
                  Create, review, and manage clinical documentation.
                </p>
              </div>

              <button
                type="button"
                className="hidden items-center gap-2 rounded-xl bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-[#06231d] sm:flex"
              >
                <Plus size={17} />
                New Clinical Note
              </button>

            </div>

            {/* SUMMARY */}
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">

              {/* TOTAL */}
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">

                <div className="flex items-center justify-between">

                  <span className="text-xs text-[var(--muted)]">
                    Total Notes
                  </span>

                  <FileText
                    size={17}
                    className="text-[var(--accent)]"
                  />

                </div>

                <p className="mt-2 text-2xl font-bold">
                  326
                </p>

                <p className="mt-1 text-[10px] text-[var(--muted)]">
                  All clinical documentation
                </p>

              </div>

              {/* TODAY */}
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">

                <div className="flex items-center justify-between">

                  <span className="text-xs text-[var(--muted)]">
                    Today's Notes
                  </span>

                  <CalendarDays
                    size={17}
                    className="text-blue-500"
                  />

                </div>

                <p className="mt-2 text-2xl font-bold">
                  08
                </p>

                <p className="mt-1 text-[10px] text-blue-500">
                  3 completed today
                </p>

              </div>

              {/* DRAFTS */}
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">

                <div className="flex items-center justify-between">

                  <span className="text-xs text-[var(--muted)]">
                    Drafts
                  </span>

                  <Edit3
                    size={17}
                    className="text-amber-500"
                  />

                </div>

                <p className="mt-2 text-2xl font-bold">
                  05
                </p>

                <p className="mt-1 text-[10px] text-amber-500">
                  Awaiting completion
                </p>

              </div>

              {/* SIGNED */}
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">

                <div className="flex items-center justify-between">

                  <span className="text-xs text-[var(--muted)]">
                    Signed
                  </span>

                  <CheckCircle2
                    size={17}
                    className="text-emerald-500"
                  />

                </div>

                <p className="mt-2 text-2xl font-bold">
                  321
                </p>

                <p className="mt-1 text-[10px] text-emerald-500">
                  Completed records
                </p>

              </div>

            </div>

            {/* NOTES PANEL */}
            <div className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--card)]">

              {/* TOOLBAR */}
              <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] px-4 py-3">

                <div className="flex items-center gap-2">

                  <FileText
                    size={16}
                    className="text-[var(--muted)]"
                  />

                  <span className="text-sm font-medium">
                    Recent Notes
                  </span>

                  <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-[10px] font-medium text-[var(--accent)]">
                    {filteredNotes.length}
                  </span>

                </div>

                <div className="flex items-center gap-1.5">

                  {["All", "Draft", "Signed"].map(
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

              {/* TABLE */}
              <div className="min-h-0 flex-1 overflow-hidden">

                <table className="w-full table-fixed border-collapse">

                  <thead>
                    <tr className="border-b border-[var(--border)]">

                      <th className="w-[22%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                        Patient
                      </th>

                      <th className="w-[24%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                        Clinical Note
                      </th>

                      <th className="hidden w-[14%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)] sm:table-cell">
                        Type
                      </th>

                      <th className="hidden w-[15%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)] md:table-cell">
                        Date
                      </th>

                      <th className="hidden w-[13%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)] lg:table-cell">
                        Status
                      </th>

                      <th className="w-[12%] px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                        Action
                      </th>

                    </tr>
                  </thead>

                  <tbody>

                    {filteredNotes.map((note) => (
                      <tr
                        key={note.id}
                        className="border-b border-[var(--border)] transition hover:bg-[var(--card-soft)] last:border-b-0"
                      >

                        {/* PATIENT */}
                        <td className="px-4 py-3">

                          <div className="flex min-w-0 items-center gap-3">

                            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--accent-soft)]">
                              <UserRound
                                size={16}
                                className="text-[var(--accent)]"
                              />
                            </div>

                            <div className="min-w-0">

                              <p className="truncate text-sm font-semibold">
                                {note.patient}
                              </p>

                              <p className="mt-0.5 text-[10px] text-[var(--muted)]">
                                {note.id}
                              </p>

                            </div>

                          </div>

                        </td>

                        {/* NOTE */}
                        <td className="px-4 py-3">

                          <p className="truncate text-sm font-medium">
                            {note.title}
                          </p>

                          <p className="mt-1 truncate text-[10px] text-[var(--muted)]">
                            {note.preview}
                          </p>

                        </td>

                        {/* TYPE */}
                        <td className="hidden px-4 py-3 sm:table-cell">

                          <span className="rounded-lg bg-[var(--card-soft)] px-2.5 py-1 text-[10px] font-medium text-[var(--text-secondary)]">
                            {note.type}
                          </span>

                        </td>

                        {/* DATE */}
                        <td className="hidden px-4 py-3 md:table-cell">

                          <div className="flex items-center gap-2">

                            <CalendarDays
                              size={13}
                              className="text-[var(--muted)]"
                            />

                            <div>

                              <p className="text-xs">
                                {note.date}
                              </p>

                              <p className="mt-0.5 flex items-center gap-1 text-[10px] text-[var(--muted)]">
                                <Clock3 size={10} />
                                {note.time}
                              </p>

                            </div>

                          </div>

                        </td>

                        {/* STATUS */}
                        <td className="hidden px-4 py-3 lg:table-cell">

                          <StatusBadge status={note.status} />

                        </td>

                        {/* ACTIONS */}
                        <td className="px-4 py-3">

                          <div className="flex items-center justify-end gap-1">

                            <button
                              type="button"
                              title="View note"
                              className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--muted)] hover:bg-[var(--accent-soft)] hover:text-[var(--accent)]"
                            >
                              <Eye size={15} />
                            </button>

                            <button
                              type="button"
                              title="Edit note"
                              className="hidden h-8 w-8 items-center justify-center rounded-lg text-[var(--muted)] hover:bg-[var(--accent-soft)] hover:text-[var(--accent)] sm:flex"
                            >
                              <Edit3 size={15} />
                            </button>

                            <button
                              type="button"
                              className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--muted)] hover:bg-[var(--card-soft)] hover:text-[var(--text)]"
                            >
                              <MoreHorizontal size={15} />
                            </button>

                          </div>

                        </td>

                      </tr>
                    ))}

                  </tbody>

                </table>

                {filteredNotes.length === 0 && (
                  <div className="flex h-full items-center justify-center">

                    <div className="text-center">

                      <FileText
                        size={34}
                        className="mx-auto text-[var(--muted)]"
                      />

                      <p className="mt-3 text-sm font-medium">
                        No clinical notes found
                      </p>

                      <p className="mt-1 text-xs text-[var(--muted)]">
                        Try another search or filter.
                      </p>

                    </div>

                  </div>
                )}

              </div>

              {/* FOOTER */}
              <div className="flex shrink-0 items-center justify-between border-t border-[var(--border)] px-4 py-2.5">

                <div className="flex items-center gap-2 text-[10px] text-[var(--muted)]">

                  <Save
                    size={13}
                    className="text-emerald-500"
                  />

                  Draft changes are saved automatically.

                </div>

                <div className="flex items-center gap-2 text-[10px] text-[var(--muted)]">

                  <Clock3 size={12} />

                  Last updated moments ago

                </div>

              </div>

            </div>

          </section>
        </main>
      </div>
    </div>
  );
}