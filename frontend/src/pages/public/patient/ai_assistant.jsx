import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  Bell,
  BookOpen,
  Bot,
  CalendarDays,
  ChevronDown,
  ClipboardList,
  ExternalLink,
  Heart,
  History,
  Info,
  Loader2,
  MessageSquare,
  Moon,
  Plus,
  Search,
  Send,
  ShieldAlert,
  Sparkles,
  Sun,
  UserRound,
} from "lucide-react";

import Sidebar from "./sidebar";
import { useAuth } from "../../../_core/hooks/useAuth";
import aiService from "../../../services/aiService";

/* =========================================================
   ROUTES
========================================================= */

const ROUTES = {
  dashboard: "/patient/dashboard",
  settings: "/patient/settings",
};

/* =========================================================
   DEFAULT WELCOME MESSAGE
========================================================= */

const initialWelcomeMessage = {
  id: "welcome",
  role: "assistant",
  text:
    "Hello! I am your MediCare AI Clinical Assistant, grounded in real-time PubMed literature and your clinical records. How can I assist you with your health questions today?",
  time: "Just now",
  citations: [],
  disclaimer: null,
};

const quickPrompts = [
  "Summarize my health today",
  "Explain my latest lab results",
  "What should I ask my doctor?",
  "What does an elevated blood pressure mean?",
];

/* =========================================================
   THEME
========================================================= */

function useDarkMode() {
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window === "undefined") return true;
    const savedTheme = window.localStorage.getItem("medicare-theme");
    if (savedTheme === "dark") return true;
    if (savedTheme === "light") return false;
    return true;
  });

  useEffect(() => {
    window.localStorage.setItem("medicare-theme", darkMode ? "dark" : "light");
    document.documentElement.classList.toggle("dark", darkMode);
    document.documentElement.style.colorScheme = darkMode ? "dark" : "light";
    document.body.style.background = darkMode ? "#0b1413" : "#f8faf9";
  }, [darkMode]);

  return [darkMode, setDarkMode];
}

/* =========================================================
   HEADER
========================================================= */

function Header({ darkMode, setDarkMode }) {
  const { user } = useAuth();
  const patientName = user
    ? `${user.first_name || ""} ${user.last_name || ""}`.trim() || user.email.split("@")[0]
    : "Patient";

  return (
    <header
      className={`flex h-[76px] shrink-0 items-center justify-between border-b px-6 ${
        darkMode ? "border-slate-800 bg-[#111c1b]" : "border-slate-200 bg-white"
      }`}
    >
      <div className="min-w-0">
        <h1
          className={`text-[22px] font-bold tracking-[-0.4px] ${
            darkMode ? "text-white" : "text-emerald-950"
          }`}
        >
          AI Medical Assistant & PubMed RAG
        </h1>

        <p
          className={`mt-0.5 truncate text-[12px] ${
            darkMode ? "text-slate-400" : "text-slate-500"
          }`}
        >
          Evidence-based health inquiries synthesized with peer-reviewed NCBI PubMed literature
        </p>
      </div>

      <div className="ml-6 flex shrink-0 items-center gap-3">
        <button
          type="button"
          onClick={() => setDarkMode((value) => !value)}
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border transition ${
            darkMode
              ? "border-slate-700 bg-slate-900 text-yellow-300 hover:bg-slate-800"
              : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
          }`}
          aria-label="Toggle theme"
        >
          {darkMode ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        <div className="flex items-center gap-2.5 rounded-xl px-2 py-1.5">
          <div
            className={`h-9 w-9 overflow-hidden rounded-full ${
              darkMode ? "bg-slate-700" : "bg-slate-200"
            }`}
          >
            <img
              src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80"
              alt={patientName}
              className="h-full w-full object-cover"
            />
          </div>

          <span
            className={`text-[13px] font-semibold ${
              darkMode ? "text-slate-200" : "text-slate-800"
            }`}
          >
            {patientName}
          </span>
        </div>
      </div>
    </header>
  );
}

/* =========================================================
   CHAT MESSAGE WITH PUBMED CITATIONS & REGULATORY DISCLAIMER
========================================================= */

function MessageBubble({ message, darkMode }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`flex max-w-[82%] items-end gap-2.5 ${
          isUser ? "flex-row-reverse" : ""
        }`}
      >
        <div
          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
            isUser
              ? "bg-slate-700 text-white"
              : "bg-emerald-500/10 text-emerald-400"
          }`}
        >
          {isUser ? <UserRound size={15} /> : <Bot size={15} />}
        </div>

        <div className="min-w-0 space-y-2">
          {/* Main Bubble Content */}
          <div
            className={`rounded-2xl px-4 py-3 text-[13px] leading-relaxed shadow-sm ${
              isUser
                ? "rounded-br-md bg-emerald-500 text-white"
                : darkMode
                ? "rounded-bl-md border border-slate-800 bg-[#15211f] text-slate-200"
                : "rounded-bl-md border border-slate-100 bg-white text-slate-700 shadow-sm"
            }`}
          >
            <p className="whitespace-pre-wrap">{message.text}</p>

            {/* Clickable PubMed Citation Badges */}
            {message.citations && message.citations.length > 0 && (
              <div className="mt-3.5 border-t border-slate-700/40 pt-2.5">
                <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-emerald-400 mb-2">
                  <BookOpen size={12} />
                  <span>Peer-Reviewed PubMed Sources</span>
                </div>

                <div className="flex flex-col gap-1.5">
                  {message.citations.map((cite, idx) => {
                    const pubmedUrl =
                      cite.url || `https://pubmed.ncbi.nlm.nih.gov/${cite.pmid}/`;

                    return (
                      <a
                        key={idx}
                        href={pubmedUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`group flex items-center justify-between gap-2 rounded-lg border p-2 text-left transition ${
                          darkMode
                            ? "border-slate-800 bg-[#0d1716] hover:border-emerald-500/40 hover:bg-[#101e1d]"
                            : "border-slate-200 bg-slate-50 hover:border-emerald-300 hover:bg-white"
                        }`}
                      >
                        <div className="min-w-0 flex-1">
                          <p className="line-clamp-1 text-[11px] font-semibold text-slate-200 group-hover:text-emerald-400">
                            {cite.title || `PubMed Study #${cite.pmid}`}
                          </p>
                          <p className="text-[9px] text-slate-400">
                            {cite.journal ? `${cite.journal} • ` : ""}
                            {cite.year || "NCBI"}
                          </p>
                        </div>

                        <div className="flex shrink-0 items-center gap-1 rounded bg-emerald-500/10 px-1.5 py-0.5 text-[9px] font-mono font-bold text-emerald-400">
                          <span>PMID: {cite.pmid}</span>
                          <ExternalLink size={10} />
                        </div>
                      </a>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Mandatory Regulatory Clinical Disclaimer */}
            {message.disclaimer && (
              <div className="mt-3 flex items-start gap-2 rounded-lg border border-amber-500/20 bg-amber-500/10 p-2 text-[9px] leading-normal text-amber-300/90">
                <ShieldAlert size={12} className="shrink-0 mt-0.5 text-amber-400" />
                <span>{message.disclaimer}</span>
              </div>
            )}
          </div>

          <p
            className={`px-1 text-[10px] ${
              isUser
                ? "text-right text-slate-500"
                : darkMode
                ? "text-slate-500"
                : "text-slate-400"
            }`}
          >
            {message.time}
          </p>
        </div>
      </div>
    </div>
  );
}

/* =========================================================
   QUICK PROMPT
========================================================= */

function QuickPrompt({ text, darkMode, onClick }) {
  return (
    <button
      type="button"
      onClick={() => onClick(text)}
      className={`rounded-xl border px-3 py-1.5 text-left text-[11px] transition ${
        darkMode
          ? "border-slate-800 bg-[#101918] text-slate-400 hover:border-emerald-500/30 hover:text-slate-200"
          : "border-slate-200 bg-white text-slate-500 hover:border-emerald-200 hover:text-slate-700"
      }`}
    >
      {text}
    </button>
  );
}

/* =========================================================
   MAIN ASSISTANT PAGE
========================================================= */

export default function AIAssistant() {
  const { user } = useAuth();
  const [darkMode, setDarkMode] = useDarkMode();
  const [messages, setMessages] = useState([initialWelcomeMessage]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  const scrollRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    const node = scrollRef.current;
    if (node) {
      node.scrollTop = node.scrollHeight;
    }
  }, [messages, typing]);

  // Load chat history from backend on mount
  useEffect(() => {
    async function loadHistory() {
      try {
        setLoadingHistory(true);
        const data = await aiService.getChatHistory(1);
        const convList = Array.isArray(data) ? data : [];
        setConversations(convList);

        // If active conversation exists, load its messages
        if (convList.length > 0) {
          const mostRecent = convList[0];
          setConversationId(mostRecent.id);
          if (mostRecent.messages && mostRecent.messages.length > 0) {
            const formatted = mostRecent.messages.map((m) => ({
              id: m.id,
              role: m.role,
              text: m.content,
              time: m.created_at
                ? new Date(m.created_at).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                : "Past message",
              citations: m.sources || [],
              disclaimer:
                m.role === "assistant"
                  ? "This system provides AI-assisted clinical information based on medical literature and available clinical records. Consult a licensed physician before making clinical decisions."
                  : null,
            }));
            setMessages(formatted);
          }
        }
      } catch (err) {
        console.error("Failed to load chat history:", err);
      } finally {
        setLoadingHistory(false);
      }
    }
    loadHistory();
  }, []);

  const sendMessage = async (value = input) => {
    const trimmed = value.trim();
    if (!trimmed || typing) return;

    const userTime = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    const userMessage = {
      id: Date.now(),
      role: "user",
      text: trimmed,
      time: userTime,
      citations: [],
    };

    setMessages((current) => [...current, userMessage]);
    setInput("");
    setTyping(true);

    try {
      const payload = {
        prompt: trimmed,
        conversation_id: conversationId,
        patient_id: user?.id,
      };

      const result = await aiService.sendChatMessage(payload);

      if (result.conversation_id && result.conversation_id !== conversationId) {
        setConversationId(result.conversation_id);
      }

      const assistantMessage = {
        id: result.message_id || Date.now() + 1,
        role: "assistant",
        text: result.response,
        time: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        citations: result.citations || [],
        disclaimer: result.disclaimer,
      };

      setMessages((current) => [...current, assistantMessage]);
    } catch (err) {
      console.error("Chat error:", err);
      const errorMessage = {
        id: Date.now() + 1,
        role: "assistant",
        text:
          err.response?.data?.error?.message ||
          err.response?.data?.detail ||
          "Unable to complete PubMed medical search and synthesis. Please try again or ask a more specific clinical question.",
        time: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        citations: [],
        disclaimer: null,
      };
      setMessages((current) => [...current, errorMessage]);
    } finally {
      setTyping(false);
    }
  };

  const handleNewChat = () => {
    setConversationId(null);
    setMessages([initialWelcomeMessage]);
    setInput("");
    setTyping(false);
  };

  const loadConversationThread = (conv) => {
    setConversationId(conv.id);
    if (conv.messages && conv.messages.length > 0) {
      const formatted = conv.messages.map((m) => ({
        id: m.id,
        role: m.role,
        text: m.content,
        time: m.created_at
          ? new Date(m.created_at).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })
          : "Past message",
        citations: m.sources || [],
        disclaimer:
          m.role === "assistant"
            ? "This system provides AI-assisted clinical information based on medical literature and available clinical records. Consult a licensed physician before making clinical decisions."
            : null,
      }));
      setMessages(formatted);
    } else {
      setMessages([initialWelcomeMessage]);
    }
  };

  return (
    <div
      className={`fixed inset-0 overflow-hidden ${
        darkMode ? "bg-[#0b1413] text-white" : "bg-[#f8faf9] text-slate-900"
      }`}
    >
      <div
        className={`flex h-full w-full overflow-hidden ${
          darkMode ? "bg-[#111c1b]" : "bg-white"
        }`}
      >
        <Sidebar darkMode={darkMode} />

        <main className="ml-[255px] flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          <Header darkMode={darkMode} setDarkMode={setDarkMode} />

          <div className="min-h-0 flex-1 overflow-hidden px-6 py-5">
            <div className="grid h-full min-h-0 grid-cols-[minmax(0,1fr)_320px] gap-5">
              {/* =================================================
                  MAIN CHAT CONTAINER
              ================================================= */}
              <section
                className={`flex min-h-0 min-w-0 flex-col overflow-hidden rounded-2xl border ${
                  darkMode ? "border-slate-800 bg-[#15211f]" : "border-slate-200 bg-white"
                }`}
              >
                {/* CHAT HEADER */}
                <div
                  className={`flex shrink-0 items-center justify-between border-b px-5 py-3.5 ${
                    darkMode ? "border-slate-800" : "border-slate-100"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-500 text-white">
                      <Bot size={17} />
                    </div>

                    <div>
                      <h2
                        className={`text-[14px] font-bold ${
                          darkMode ? "text-white" : "text-emerald-950"
                        }`}
                      >
                        MediCare RAG Assistant
                      </h2>
                      <p className="text-[10px] text-emerald-400 flex items-center gap-1">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        PubMed Evidence-Grounded
                      </p>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={handleNewChat}
                    className="flex items-center gap-1.5 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-[11px] font-semibold text-emerald-400 hover:bg-emerald-500/20 transition"
                  >
                    <Plus size={13} />
                    New Chat
                  </button>
                </div>

                {/* CHAT MESSAGES SCROLL AREA */}
                <div
                  ref={scrollRef}
                  className="min-h-0 flex-1 overflow-y-auto px-5 py-4"
                >
                  <div className="space-y-4">
                    {messages.map((message) => (
                      <MessageBubble
                        key={message.id}
                        message={message}
                        darkMode={darkMode}
                      />
                    ))}

                    {typing && (
                      <div className="flex items-start gap-2.5">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-400 shrink-0">
                          <Bot size={15} />
                        </div>

                        <div
                          className={`rounded-2xl rounded-bl-md border px-4 py-3 text-[12px] ${
                            darkMode
                              ? "border-slate-800 bg-[#101918] text-slate-300"
                              : "border-slate-100 bg-slate-50 text-slate-600"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <Loader2 size={13} className="animate-spin text-emerald-400" />
                            <span>Retrieving PubMed literature & synthesizing clinical guidance...</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* COMPOSER */}
                <div
                  className={`shrink-0 border-t p-4 ${
                    darkMode ? "border-slate-800" : "border-slate-100"
                  }`}
                >
                  {/* Quick Prompts */}
                  <div className="mb-2.5 flex flex-wrap gap-1.5">
                    {quickPrompts.map((prompt) => (
                      <QuickPrompt
                        key={prompt}
                        text={prompt}
                        darkMode={darkMode}
                        onClick={sendMessage}
                      />
                    ))}
                  </div>

                  {/* Input Box */}
                  <div
                    className={`flex items-end gap-2 rounded-xl border p-2.5 ${
                      darkMode
                        ? "border-slate-700 bg-[#101918]"
                        : "border-slate-200 bg-slate-50"
                    }`}
                  >
                    <textarea
                      value={input}
                      onChange={(event) => setInput(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" && !event.shiftKey) {
                          event.preventDefault();
                          sendMessage();
                        }
                      }}
                      rows={2}
                      placeholder="Ask any clinical or health question (e.g. 'What does elevated HbA1c indicate?')..."
                      className={`min-h-[44px] flex-1 resize-none bg-transparent px-2 py-1 text-[12px] leading-5 outline-none ${
                        darkMode
                          ? "text-slate-200 placeholder:text-slate-600"
                          : "text-slate-700 placeholder:text-slate-400"
                      }`}
                    />

                    <button
                      type="button"
                      onClick={() => sendMessage()}
                      disabled={!input.trim() || typing}
                      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
                        input.trim() && !typing
                          ? "bg-emerald-500 text-white hover:bg-emerald-600"
                          : "cursor-not-allowed bg-slate-300 text-slate-500"
                      }`}
                      aria-label="Send message"
                    >
                      <Send size={15} />
                    </button>
                  </div>
                </div>
              </section>

              {/* =================================================
                  RIGHT SIDEBAR: CONVERSATION HISTORY & SNAPSHOT
              ================================================= */}
              <aside className="min-h-0 overflow-y-auto space-y-4">
                {/* PAST CONVERSATIONS */}
                <section
                  className={`rounded-2xl border p-4 ${
                    darkMode ? "border-slate-800 bg-[#15211f]" : "border-slate-200 bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <History size={16} className="text-emerald-400" />
                      <h3
                        className={`text-[13px] font-bold ${
                          darkMode ? "text-white" : "text-emerald-950"
                        }`}
                      >
                        Saved Threads
                      </h3>
                    </div>

                    <span className="text-[10px] text-slate-500">
                      {conversations.length} sessions
                    </span>
                  </div>

                  {loadingHistory ? (
                    <p className="text-[10px] text-slate-500 py-3 text-center">
                      Loading saved chats...
                    </p>
                  ) : conversations.length === 0 ? (
                    <p className="text-[10px] text-slate-500 py-2">
                      No saved conversation threads yet.
                    </p>
                  ) : (
                    <div className="space-y-1.5 max-h-[160px] overflow-y-auto pr-1">
                      {conversations.map((conv) => {
                        const isCurrent = conv.id === conversationId;
                        return (
                          <button
                            key={conv.id}
                            type="button"
                            onClick={() => loadConversationThread(conv)}
                            className={`w-full text-left rounded-lg p-2 text-[11px] transition truncate flex items-center gap-2 ${
                              isCurrent
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                : darkMode
                                ? "text-slate-300 hover:bg-[#101918]"
                                : "text-slate-600 hover:bg-slate-100"
                            }`}
                          >
                            <MessageSquare size={12} className="shrink-0 text-emerald-500" />
                            <span className="truncate">{conv.title || `Chat #${conv.id}`}</span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </section>

                {/* CLINICAL SNAPSHOT */}
                <section
                  className={`rounded-2xl border p-4 ${
                    darkMode ? "border-slate-800 bg-[#15211f]" : "border-slate-200 bg-white"
                  }`}
                >
                  <div className="flex items-center gap-2 mb-3">
                    <Activity size={16} className="text-emerald-400" />
                    <h3
                      className={`text-[13px] font-bold ${
                        darkMode ? "text-white" : "text-emerald-950"
                      }`}
                    >
                      Patient Clinical Context
                    </h3>
                  </div>

                  <p className="text-[10px] text-slate-400 mb-3">
                    The assistant automatically factors your profile and recent health metrics into its clinical synthesis:
                  </p>

                  <div className="space-y-2">
                    {[
                      ["Blood Pressure", "120/80 mmHg (Target)"],
                      ["Recent HbA1c", "5.4% (Normal)"],
                      ["Heart Rate", "72 bpm (Resting)"],
                      ["Clinical Chart", "Active EHR Profile"],
                    ].map(([label, value]) => (
                      <div
                        key={label}
                        className={`flex items-center justify-between border-b pb-2 text-[10px] ${
                          darkMode ? "border-slate-800" : "border-slate-100"
                        }`}
                      >
                        <span className="text-slate-400">{label}</span>
                        <span className="font-semibold text-slate-200">{value}</span>
                      </div>
                    ))}
                  </div>
                </section>

                {/* SAFETY & CDSS DISCLAIMER */}
                <section
                  className={`flex items-start gap-2.5 rounded-2xl border p-3.5 ${
                    darkMode
                      ? "border-amber-500/20 bg-amber-500/5"
                      : "border-amber-100 bg-amber-50/60"
                  }`}
                >
                  <Info size={14} className="mt-0.5 shrink-0 text-amber-500" />
                  <p className="text-[9px] leading-relaxed text-slate-400">
                    <strong>CDSS Triage Safety:</strong> Do not use this assistant for urgent symptoms, chest pain, or emergency conditions. Seek emergency medical care immediately when experiencing severe distress.
                  </p>
                </section>
              </aside>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}