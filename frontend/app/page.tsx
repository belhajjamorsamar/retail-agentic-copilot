"use client";

import { useState } from "react";

interface ChatResponse {
  answer: string;
  sources: string[];
}

export default function Home() {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError("");
    setResponse(null);

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (!res.ok) {
        throw new Error(`Erreur ${res.status}`);
      }

      const data: ChatResponse = await res.json();
      setResponse(data);
    } catch (err) {
      setError("Impossible de contacter l'assistant. Vérifie que l'API tourne bien.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 flex flex-col items-center px-4 py-12">
      <div className="w-full max-w-2xl">
        <h1 className="text-2xl font-bold text-slate-800 mb-2">
          Assistant service client — retail-agentic-copilot
        </h1>
        <p className="text-slate-500 mb-6">
          Posez une question sur nos produits.
        </p>

        <form onSubmit={handleSubmit} className="flex gap-2 mb-6">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ex : Avez-vous des yaourts sans lactose ?"
            className="flex-1 border border-slate-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-slate-800 text-white px-5 py-2 rounded-lg disabled:opacity-50"
          >
            {loading ? "..." : "Envoyer"}
          </button>
        </form>

        {error && (
          <p className="text-red-600 mb-4">{error}</p>
        )}

        {response && (
          <div className="bg-white border border-slate-200 rounded-lg p-5">
            <p className="text-slate-800 mb-4">{response.answer}</p>
            {response.sources.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {response.sources.map((source, i) => (
                  <span
                    key={i}
                    className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded-full"
                  >
                    {source}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}