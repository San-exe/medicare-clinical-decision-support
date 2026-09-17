import React, { useMemo, useState } from "react";
import {
  Search,
  Bell,
  ChevronDown,
  BookOpen,
  Bookmark,
  ExternalLink,
  HeartPulse,
  Pill,
  Stethoscope,
  ShieldCheck,
  Filter,
  Clock3,
  Star,
} from "lucide-react";

import Sidebar from "./sidebar";
import { useTheme } from "../ThemeContext";

const knowledgeItems = [
  {
    title: "Type 2 Diabetes Mellitus",
    category: "Endocrinology",
    type: "Clinical Guideline",
    updated: "22 Aug 2026",
    readTime: "8 min read",
    summary:
      "Evidence-based overview of diagnosis, glycemic targets, medication classes, monitoring, and follow-up considerations.",
    tags: ["Diabetes", "HbA1c", "Monitoring"],
  },
  {
    title: "Hypertension Management",
    category: "Cardiology",
    type: "Treatment Guide",
    updated: "21 Aug 2026",
    readTime: "7 min read",
    summary:
      "Practical reference for blood-pressure assessment, treatment thresholds, lifestyle measures, and medication selection.",
    tags: ["Blood Pressure", "ACEi", "ARB"],
  },
  {
    title: "Lipid Management",
    category: "Cardiology",
    type: "Clinical Reference",
    updated: "20 Aug 2026",
    readTime: "6 min read",
    summary:
      "Quick reference covering cardiovascular risk, LDL goals, statin intensity, monitoring, and follow-up decisions.",
    tags: ["LDL", "Statins", "Risk"],
  },
  {
    title: "Antibiotic Stewardship",
    category: "Infectious Disease",
    type: "Safety Guide",
    updated: "19 Aug 2026",
    readTime: "9 min read",
    summary:
      "Decision-support reference for appropriate antibiotic selection, duration, de-escalation, and common safety checks.",
    tags: ["Antibiotics", "Safety", "Resistance"],
  },
  {
    title: "Thyroid Function Testing",
    category: "Endocrinology",
    type: "Diagnostic Guide",
    updated: "18 Aug 2026",
    readTime: "5 min read",
    summary:
      "Interpretation guide for TSH, free T4, common patterns, repeat testing, and follow-up considerations.",
    tags: ["TSH", "T4", "Diagnostics"],
  },
  {
    title: "Acute Chest Pain Assessment",
    category: "Emergency Medicine",
    type: "Clinical Pathway",
    updated: "17 Aug 2026",
    readTime: "10 min read",
    summary:
      "Structured approach to risk assessment, initial investigations, red flags, and escalation for acute chest pain.",
    tags: ["Chest Pain", "ECG", "Risk"],
  },
];

const categories = [
  "All Categories",
  "Cardiology",
  "Endocrinology",
  "Emergency Medicine",
  "Infectious Disease",
];

export default function MedicalKnowledge() {
  const { isDark, toggleTheme } = useTheme();
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All Categories");
  const [bookmarked, setBookmarked] = useState([]);

  const filteredItems = useMemo(() => {
    const query = search.trim().toLowerCase();

    return knowledgeItems.filter((item) => {
      const searchable = [
        item.title,
        item.category,
        item.type,
        item.summary,
        ...item.tags,
      ]
        .join(" ")
        .toLowerCase();

      const matchesSearch = !query || searchable.includes(query);
      const matchesCategory =
        category === "All Categories" || item.category === category;

      return matchesSearch && matchesCategory;
    });
  }, [search, category]);

  const toggleBookmark = (title) => {
    setBookmarked((current) =>
      current.includes(title)
        ? current.filter((item) => item !== title)
        : [...current, title]
    );
  };

  return (
    <div
      className="h-dvh min-h-0 overflow-hidden medicare-doctor-shell bg-[var(--bg)] text-[var(--text)]"
      style={{ colorScheme: isDark ? "dark" : "light" }}
    >
      <div className="flex h-full min-h-0">
        <Sidebar />

        <main className="ml-[217px] min-h-0 min-w-0 w-[calc(100%-217px)] flex-1 overflow-hidden">
          <header className="flex h-[72px] shrink-0 items-center justify-between border-b border-[var(--border)] px-5 sm:px-7 lg:px-8">
            <h1 className="text-[26px] font-bold tracking-tight">Medical Knowledge</h1>

            <div className="flex items-center gap-3">
              <div className="hidden h-10 w-[280px] items-center gap-3 rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-4 md:flex">
                <Search size={18} className="text-[var(--muted)]" />
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search medical knowledge..."
                  className="w-full bg-transparent text-sm outline-none placeholder:text-[var(--muted)]"
                />
              </div>

              <button
                type="button"
                onClick={toggleTheme}
                className="flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] text-[var(--accent)]"
                aria-label="Toggle theme"
              >
                {isDark ? "☼" : "☾"}
              </button>

              <button
                type="button"
                className="relative p-2 text-[var(--text-secondary)]"
                aria-label="Notifications"
              >
                <Bell size={20} />
                <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-[var(--accent)]" />
              </button>

              <div className="hidden items-center gap-2 sm:flex">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--accent-soft)]">
                  <Stethoscope size={18} className="text-[var(--accent)]" />
                </div>
                <ChevronDown size={15} className="text-[var(--muted)]" />
              </div>
            </div>
          </header>

          <section className="h-[calc(100vh-72px)] min-h-0 overflow-y-auto px-5 py-5 sm:px-7 lg:px-8">
            <div className="mx-auto max-w-[1500px]">
              <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                  <h2 className="text-[22px] font-bold">Clinical Medical Knowledge</h2>
                  <p className="mt-1 max-w-2xl text-sm text-[var(--muted)]">
                    Evidence-informed references, clinical pathways, and treatment resources for point-of-care decision support.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-2 rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-3 py-2">
                    <Filter size={16} className="text-[var(--muted)]" />
                    <select
                      value={category}
                      onChange={(event) => setCategory(event.target.value)}
                      className="bg-transparent text-sm outline-none"
                    >
                      {categories.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                <KnowledgeStat icon={BookOpen} label="Clinical references" value="48" />
                <KnowledgeStat icon={ShieldCheck} label="Safety resources" value="16" />
                <KnowledgeStat icon={HeartPulse} label="Updated this week" value="12" />
              </div>

              <div className="mt-5 rounded-2xl border border-[var(--border)] bg-[var(--card)]">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] px-4 py-4 sm:px-5">
                  <div>
                    <h3 className="text-[17px] font-bold">Reference Library</h3>
                    <p className="mt-0.5 text-xs text-[var(--muted)]">
                      {filteredItems.length} resources match your search.
                    </p>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-[var(--muted)]">
                    <Star size={14} className="text-[var(--accent)]" />
                    Curated for clinicians
                  </div>
                </div>

                <div className="grid gap-3 p-4 sm:p-5 lg:grid-cols-2">
                  {filteredItems.map((item) => {
                    const isBookmarked = bookmarked.includes(item.title);

                    return (
                      <article
                        key={item.title}
                        className="rounded-2xl border border-[var(--border-soft)] bg-[var(--card-soft)] p-4 transition hover:border-[var(--accent)]"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex min-w-0 items-start gap-3">
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--accent-soft)] text-[var(--accent)]">
                              {item.type.includes("Treatment") ? <Pill size={18} /> : <BookOpen size={18} />}
                            </div>
                            <div className="min-w-0">
                              <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--muted)]">
                                {item.category}
                              </p>
                              <h4 className="mt-1 truncate text-[16px] font-semibold">{item.title}</h4>
                              <p className="mt-1 text-xs text-[var(--muted)]">{item.type}</p>
                            </div>
                          </div>

                          <button
                            type="button"
                            onClick={() => toggleBookmark(item.title)}
                            className={`rounded-lg p-2 transition ${isBookmarked ? "bg-[var(--accent-soft)] text-[var(--accent)]" : "text-[var(--muted)] hover:bg-[var(--card-hover)] hover:text-[var(--text)]"}`}
                            aria-label={isBookmarked ? "Remove bookmark" : "Bookmark resource"}
                          >
                            <Bookmark size={16} fill={isBookmarked ? "currentColor" : "none"} />
                          </button>
                        </div>

                        <p className="mt-4 text-sm leading-6 text-[var(--text-secondary)]">{item.summary}</p>

                        <div className="mt-4 flex flex-wrap gap-1.5">
                          {item.tags.map((tag) => (
                            <span key={tag} className="rounded-full bg-[var(--accent-soft)] px-2.5 py-1 text-[10px] font-medium text-[var(--accent)]">
                              {tag}
                            </span>
                          ))}
                        </div>

                        <div className="mt-4 flex items-center justify-between border-t border-[var(--border)] pt-3">
                          <div className="flex items-center gap-3 text-[10px] text-[var(--muted)]">
                            <span className="flex items-center gap-1"><Clock3 size={12} /> {item.readTime}</span>
                            <span>Updated {item.updated}</span>
                          </div>
                          <button
                            type="button"
                            className="flex items-center gap-1.5 text-xs font-semibold text-[var(--accent)] hover:brightness-110"
                          >
                            Open reference
                            <ExternalLink size={13} />
                          </button>
                        </div>
                      </article>
                    );
                  })}

                  {!filteredItems.length && (
                    <div className="lg:col-span-2 rounded-2xl border border-dashed border-[var(--border-soft)] p-10 text-center">
                      <BookOpen className="mx-auto text-[var(--muted)]" size={28} />
                      <p className="mt-3 text-sm font-semibold">No references found</p>
                      <p className="mt-1 text-xs text-[var(--muted)]">Try a different search term or category.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

function KnowledgeStat({ icon: Icon, label, value }) {
  return (
    <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
      <div className="flex items-center justify-between">
        <span className="text-xs text-[var(--muted)]">{label}</span>
        <Icon size={17} className="text-[var(--accent)]" />
      </div>
      <p className="mt-2 text-2xl font-bold">{value}</p>
    </div>
  );
}
