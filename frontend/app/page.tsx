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
  const [dark, setDark] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = savedTheme ? savedTheme === "dark" : prefersDark;
    setDark(isDark);
    document.documentElement.classList.toggle("dark", isDark);

    const saved = localStorage.getItem(STORAGE_KEY);
    let convos: Conversation[] = saved ? JSON.parse(saved) : [];
    if (convos.length === 0) convos = [createConversation()];
    setConversations(convos);
    setActiveId(convos[0].id);
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted) localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
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

  const activeConversation = conversations.find((c) => c.id === activeId);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeConversation?.messages, loading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || loading || !activeId) return;

    setConversations((prev) =>
      prev.map((c) =>
        c.id === activeId
          ? {
              ...c,
              messages: [...c.messages, { role: "user", content: trimmed }],
              title: c.messages.length === 0 ? trimmed.slice(0, 40) : c.title,
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
            ? { ...c, messages: [...c.messages, { role: "assistant", content: data.answer, sources: data.sources }] }
            : c
        )
      );
    } catch {
      setError("Oups, je n'arrive pas à joindre l'assistant. L'API tourne-t-elle ?");
    } finally {
      setLoading(false);
    }
  }

  if (!mounted || !activeConversation) return null;

  return (
    <main className="h-screen flex bg-[#FFFBF3] dark:bg-[#1C1712] transition-colors">

      {/* Barre latérale */}
      <aside
        className={`${sidebarOpen ? "w-64" : "w-0"} shrink-0 border-r border-orange-100 dark:border-[#3A3025] bg-white dark:bg-[#221B14] flex flex-col transition-all overflow-hidden`}
      >
        <div className="p-3">
          <button
            onClick={handleNewChat}
            className="group w-full flex items-center gap-2 bg-[#FF7A33] hover:bg-[#FF6A1A] transition-all hover:scale-[1.02] active:scale-95 text-white text-sm font-semibold px-3 py-2.5 rounded-2xl shadow-sm"
            style={{ fontFamily: "var(--font-display)" }}
          >
            <svg
              width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
              className="transition-transform duration-300 group-hover:rotate-90"
            >
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
              className={`group flex items-center justify-between gap-2 px-3 py-2.5 rounded-2xl cursor-pointer text-sm transition-colors ${
                conv.id === activeId
                  ? "bg-orange-50 dark:bg-[#332A1E] text-[#2B2118] dark:text-orange-100"
                  : "text-[#6B5F4F] dark:text-[#B8A98F] hover:bg-orange-50/60 dark:hover:bg-[#2A2219]"
              }`}
            >
              <span className="truncate">{conv.title}</span>
              <button
                onClick={(e) => handleDeleteChat(conv.id, e)}
                className="opacity-0 group-hover:opacity-100 text-[#B8A98F] hover:text-[#FF7A33] shrink-0 transition-opacity"
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
        <div className="flex items-center justify-between px-5 py-4 border-b border-orange-100 dark:border-[#3A3025] bg-white dark:bg-[#221B14]">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen((s) => !s)}
              className="w-9 h-9 rounded-full flex items-center justify-center text-[#8A7B63] dark:text-[#B8A98F] hover:bg-orange-50 dark:hover:bg-[#332A1E] transition-colors shrink-0"
              aria-label="Afficher/masquer l'historique"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="4" />
                <path d="M9 3v18" />
              </svg>
            </button>
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#FF7A33] to-[#FFC93C] flex items-center justify-center text-white text-lg shrink-0 shadow-sm">
              🛒
            </div>
            <div>
              <h1
                className="text-base font-semibold text-[#2B2118] dark:text-orange-50"
                style={{ fontFamily: "var(--font-display)" }}
              >
                Ton assistant marché
              </h1>
              <p className="text-xs text-[#8A7B63] dark:text-[#B8A98F]">
                Produits · stock · bons plans anti-gaspi
              </p>
            </div>
          </div>

          <button
            onClick={toggleTheme}
            aria-label="Changer de thème"
            className="w-9 h-9 rounded-full flex items-center justify-center text-[#8A7B63] dark:text-[#B8A98F] hover:bg-orange-50 dark:hover:bg-[#332A1E] transition-colors"
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
              <div className="text-4xl mb-3">🥬</div>
              <p
                className="text-[#2B2118] dark:text-orange-50 text-base font-semibold"
                style={{ fontFamily: "var(--font-display)" }}
              >
                Salut ! Qu&apos;est-ce qu&apos;on cherche aujourd&apos;hui ?
              </p>
              <p className="text-[#8A7B63] dark:text-[#B8A98F] text-sm mt-1">
                Essayez : « Vous avez des yaourts en promo ? »
              </p>
            </div>
          )}

          {activeConversation.messages.map((msg, i) => (
            <div key={i} className={`flex gap-2.5 animate-message ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm shrink-0 shadow-sm ${
                  msg.role === "user"
                    ? "bg-[#2B2118] dark:bg-orange-100"
                    : "bg-gradient-to-br from-[#3FA66B] to-[#4CAF6D]"
                }`}
              >
                {msg.role === "user" ? "🙂" : "🛒"}
              </div>
              <div
                className={`max-w-[78%] rounded-3xl px-4 py-2.5 text-sm leading-relaxed shadow-sm ${
                  msg.role === "user"
                    ? "bg-[#FF7A33] text-white rounded-tr-md"
                    : "bg-white dark:bg-[#2A2219] text-[#2B2118] dark:text-orange-50 rounded-tl-md border border-orange-100 dark:border-[#3A3025]"
                }`}
              >
                <p className="whitespace-pre-line">{msg.content}</p>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2.5 pt-2.5 border-t border-orange-100 dark:border-[#3A3025]">
                    {msg.sources.map((source, j) => (
                      <span
                        key={j}
                        className="text-[11px] px-2.5 py-0.5 rounded-full bg-[#F1F9F0] dark:bg-[#22301F] text-[#3FA66B] dark:text-[#7FD498] border border-[#CFEBD3] dark:border-[#3A4A32] font-medium"
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
            <div className="flex gap-2.5 animate-message">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#3FA66B] to-[#4CAF6D] flex items-center justify-center text-sm shrink-0 shadow-sm">
                🛒
              </div>
              <div className="bg-white dark:bg-[#2A2219] border border-orange-100 dark:border-[#3A3025] rounded-3xl rounded-tl-md px-5 py-3.5 flex items-center gap-1.5 shadow-sm">
                <span className="dot w-2 h-2 rounded-full bg-[#FF7A33]" />
                <span className="dot w-2 h-2 rounded-full bg-[#3FA66B]" />
                <span className="dot w-2 h-2 rounded-full bg-[#FFC93C]" />
              </div>
            </div>
          )}

          {error && (
            <p className="text-[#E5484D] text-sm text-center">{error}</p>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Saisie */}
        <form onSubmit={handleSubmit} className="border-t border-orange-100 dark:border-[#3A3025] bg-white dark:bg-[#221B14] p-3 flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Écrivez votre question..."
            disabled={loading}
            className="flex-1 border border-orange-100 dark:border-[#3A3025] bg-[#FFFBF3] dark:bg-[#2A2219] rounded-full px-4 py-2.5 text-sm text-[#2B2118] dark:text-orange-50 placeholder:text-[#B8A98F] focus:outline-none focus:ring-2 focus:ring-[#FF7A33] disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-[#FF7A33] hover:bg-[#FF6A1A] hover:scale-105 active:scale-95 transition-all text-white w-10 h-10 rounded-full flex items-center justify-center disabled:opacity-50 disabled:hover:scale-100 shrink-0 shadow-sm"
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