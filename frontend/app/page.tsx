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

const LOADING_STEPS = [
  "Analyse de la question...",
  "Recherche dans le catalogue produits...",
  "Vérification du stock si nécessaire...",
  "Génération de la réponse...",
  "Presque fini, l'assistant local prend son temps...",
];

export default function Home() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [stepIndex, setStepIndex] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

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

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
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
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, sources: data.sources },
      ]);
    } catch (err) {
      setError("Impossible de contacter l'assistant. Vérifie que l'API tourne bien.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 flex flex-col items-center px-4 py-8">
      <div className="w-full max-w-2xl flex flex-col h-[90vh]">
        <div className="mb-4">
          <h1 className="text-2xl font-bold text-slate-800">
            Assistant service client — retail-agentic-copilot
          </h1>
          <p className="text-slate-500 text-sm">
            Posez une question sur nos produits ou notre stock.
          </p>
        </div>

        {/* Zone de conversation */}
        <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-1">
          {messages.length === 0 && !loading && (
            <p className="text-slate-400 text-sm text-center mt-10">
              Aucune question posée pour l&apos;instant. Essayez :
              « Avez-vous des yaourts en promo ? »
            </p>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 ${
                  msg.role === "user"
                    ? "bg-slate-800 text-white"
                    : "bg-white border border-slate-200 text-slate-800"
                }`}
              >
                <p className="whitespace-pre-line text-sm">{msg.content}</p>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {msg.sources.map((source, j) => (
                      <span
                        key={j}
                        className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full"
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
            <div className="flex justify-start">
              <div className="bg-slate-100 border border-slate-200 rounded-lg px-4 py-3 flex items-center gap-3 max-w-[80%]">
                <div className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin shrink-0" />
                <div>
                  <p className="text-slate-700 text-sm font-medium">{LOADING_STEPS[stepIndex]}</p>
                  <p className="text-slate-400 text-xs mt-0.5">
                    Modèle local — peut prendre 1 à 3 minutes
                  </p>
                </div>
              </div>
            </div>
          )}

          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div ref={bottomRef} />
        </div>

        {/* Formulaire */}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ex : Avez-vous des yaourts en promo ?"
            disabled={loading}
            className="flex-1 border border-slate-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400 disabled:bg-slate-100"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-slate-800 text-white px-5 py-2 rounded-lg disabled:opacity-50 whitespace-nowrap"
          >
            {loading ? "..." : "Envoyer"}
          </button>
        </form>
      </div>
    </main>
  );
}