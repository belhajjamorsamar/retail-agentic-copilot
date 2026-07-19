"use client";

import { useState, useEffect, useRef } from "react";

interface ChatResponse {
  answer: string;
  sources: string[];
}

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
}

const LOADING_STEPS = [
  "Analyse de la question",
  "Recherche dans le catalogue",
  "Vérification du stock",
  "Rédaction de la réponse",
  "Finalisation",
];

const STORAGE_KEY = "retail-copilot-conversations";

function createConversation(): Conversation {
  return {
    id: crypto.randomUUID(),
    title: "Nouvelle conversation",
    messages: [],
    createdAt: Date.now(),
  };
}

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [stepIndex, setStepIndex] = useState(0);
  const [dark, setDark] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  // Initialisation : thème + conversations sauvegardées
  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = savedTheme ? savedTheme === "dark" : prefersDark;
    setDark(isDark);
    document.documentElement.classList.toggle("dark", isDark);

    const saved = localStorage.getItem(STORAGE_KEY);
    let convos: Conversation[] = saved ? JSON.parse(saved) : [];
    if (convos.length === 0) {
      convos = [createConversation()];
    }
    setConversations(convos);
    setActiveId(convos[0].id);
    setMounted(true);
  }, []);

  // Sauvegarde automatique à chaque changement
  useEffect(() => {
    if (mounted) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    }
  }, [conversations, mounted]);

  function toggleTheme() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("theme", next ? "dark" : "light");
  }

  function handleNewChat() {
    const conv = createConversation();
    setConversations((prev) => [conv, ...prev]);
    setActiveId(conv.id);
  }

  function handleDeleteChat(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    setConversations((prev) => {
      const filtered = prev.filter((c) => c.id !== id);
      if (filtered.length === 0) {
        const fresh = createConversation();
        setActiveId(fresh.id);
        return [fresh];
      }
      if (id === activeId) setActiveId(filtered[0].id);
      return filtered;
    });
  }

  useEffect(() => {
    if (loading) {
      setStepIndex(0);
      intervalRef.current = setInterval(() => {
        setStepIndex((prev) => Math.min(prev + 1, LOADING_STEPS.length - 1));
      }, 12000);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [loading]);

  const activeConversation = conversations.find((c) => c.id === activeId);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeConversation?.messages, loading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || loading || !activeId) return;

    const userMsg: Message = { role: "user", content: trimmed };

    setConversations((prev) =>
      prev.map((c) =>
        c.id === activeId
          ? {
              ...c,
              messages: [...c.messages, userMsg],
              title: c.messages.length === 0 ? trimmed.slice(0, 40) : c.title,
              // ↑ le titre de la conversation devient la première question posée
            }
          : c
      )
    );
    setQuestion("");
    setLoading(true);
    setError("");

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });
      if (!res.ok) throw new Error(`Erreur ${res.status}`);
      const data: ChatResponse = await res.json();

      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeId
            ? {
                ...c,
                messages: [
                  ...c.messages,
                  { role: "assistant", content: data.answer, sources: data.sources },
                ],
              }
            : c
        )
      );
    } catch {
      setError("Impossible de contacter l'assistant. Vérifiez que l'API tourne.");
    } finally {
      setLoading(false);
    }
  }

  if (!mounted || !activeConversation) return null;

  return (
    <main className="h-screen flex bg-slate-50 dark:bg-slate-950 transition-colors">

      {/* Barre latérale */}
      <aside
        className={`${
          sidebarOpen ? "w-64" : "w-0"
        } shrink-0 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col transition-all overflow-hidden`}
      >
        <div className="p-3">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center gap-2 bg-teal-700 hover:bg-teal-800 transition-colors text-white text-sm font-medium px-3 py-2.5 rounded-lg"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" />
            </svg>
            Nouveau chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 space-y-1">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => setActiveId(conv.id)}
              className={`group flex items-center justify-between gap-2 px-3 py-2.5 rounded-lg cursor-pointer text-sm transition-colors ${
                conv.id === activeId
                  ? "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50"
              }`}
            >
              <span className="truncate">{conv.title}</span>
              <button
                onClick={(e) => handleDeleteChat(conv.id, e)}
                className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-500 shrink-0 transition-opacity"
                aria-label="Supprimer"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* Zone principale */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* En-tête */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen((s) => !s)}
              className="w-9 h-9 rounded-lg flex items-center justify-center text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors shrink-0"
              aria-label="Afficher/masquer l'historique"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <path d="M9 3v18" />
              </svg>
            </button>
            <div className="w-9 h-9 rounded-lg bg-teal-700 flex items-center justify-center text-white font-semibold text-sm shrink-0">
              RA
            </div>
            <div>
              <h1 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                Assistant retail-agentic-copilot
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Produits · stock · anti-gaspillage
              </p>
            </div>
          </div>

          <button
            onClick={toggleTheme}
            aria-label="Changer de thème"
            className="w-9 h-9 rounded-lg flex items-center justify-center text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            {dark ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
          </button>
        </div>

        {/* Conversation */}
        <div className="flex-1 overflow-y-auto px-5 py-5 space-y-4">
          {activeConversation.messages.length === 0 && !loading && (
            <div className="text-center mt-16">
              <p className="text-slate-400 dark:text-slate-500 text-sm">
                Aucune conversation pour l&apos;instant
              </p>
              <p className="text-slate-400 dark:text-slate-500 text-xs mt-1">
                Essayez : « Vous avez des yaourts en promo ? »
              </p>
            </div>
          )}

          {activeConversation.messages.map((msg, i) => (
            <div key={i} className={`flex gap-2.5 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium shrink-0 ${
                  msg.role === "user"
                    ? "bg-slate-800 dark:bg-slate-200 text-white dark:text-slate-900"
                    : "bg-teal-700 text-white"
                }`}
              >
                {msg.role === "user" ? "U" : "IA"}
              </div>
              <div
                className={`max-w-[78%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-slate-800 dark:bg-slate-200 text-white dark:text-slate-900 rounded-tr-sm"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-tl-sm"
                }`}
              >
                <p className="whitespace-pre-line">{msg.content}</p>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2.5 pt-2.5 border-t border-slate-200 dark:border-slate-700">
                    {msg.sources.map((source, j) => (
                      <span
                        key={j}
                        className="text-[11px] px-2 py-0.5 rounded-full bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-900"
                      >
                        {source}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-2.5">
              <div className="w-7 h-7 rounded-full bg-teal-700 flex items-center justify-center text-xs font-medium text-white shrink-0">
                IA
              </div>
              <div className="bg-slate-100 dark:bg-slate-800 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-3">
                <div className="w-3.5 h-3.5 border-2 border-teal-700 border-t-transparent rounded-full animate-spin shrink-0" />
                <div>
                  <p className="text-slate-700 dark:text-slate-200 text-sm">{LOADING_STEPS[stepIndex]}</p>
                  <p className="text-slate-400 dark:text-slate-500 text-xs mt-0.5">
                    Modèle local — jusqu&apos;à 3 min
                  </p>
                </div>
              </div>
            </div>
          )}

          {error && <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>}
          <div ref={bottomRef} />
        </div>

        {/* Saisie */}
        <form onSubmit={handleSubmit} className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3 flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Écrivez votre question..."
            disabled={loading}
            className="flex-1 border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 rounded-full px-4 py-2.5 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-600 disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-teal-700 hover:bg-teal-800 transition-colors text-white w-10 h-10 rounded-full flex items-center justify-center disabled:opacity-50 shrink-0"
            aria-label="Envoyer"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M2 21l21-9L2 3v7l15 2-15 2z" />
            </svg>
          </button>
        </form>
      </div>
    </main>
  );
}