"use client";

import { useState, useEffect, useRef } from "react";
import { Message, Conversation } from "@/types/chat";
import {
  createConversation, loadConversations, saveConversations,
  loadThemePreference, saveThemePreference,
} from "@/lib/storage";
import Sidebar from "@/components/Sidebar";
import ChatHeader from "@/components/ChatHeader";
import MessageBubble from "@/components/MessageBubble";
import LoadingBubble from "@/components/LoadingBubble";
import ChatInput from "@/components/ChatInput";
import EmptyState from "@/components/EmptyState";

interface ChatResponse {
  answer: string;
  sources: string[];
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
    const isDark = loadThemePreference();
    setDark(isDark);
    document.documentElement.classList.toggle("dark", isDark);

    const convos = loadConversations();
    setConversations(convos);
    setActiveId(convos[0].id);
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted) saveConversations(conversations);
  }, [conversations, mounted]);

  function toggleTheme() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    saveThemePreference(next);
  }

  function handleNewChat() {
    const conv = createConversation();
    setConversations((prev) => [conv, ...prev]);
    setActiveId(conv.id);
  }

  function handleDeleteChat(id: string) {
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

  function handleRenameChat(id: string, title: string) {
    setConversations((prev) => prev.map((c) => (c.id === id ? { ...c, title } : c)));
  }

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
          ? { ...c, messages: [...c.messages, userMsg], title: c.messages.length === 0 ? trimmed.slice(0, 40) : c.title }
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
      <Sidebar
        open={sidebarOpen}
        conversations={conversations}
        activeId={activeId}
        onSelect={setActiveId}
        onNewChat={handleNewChat}
        onDelete={handleDeleteChat}
        onRename={handleRenameChat}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <ChatHeader
          onToggleSidebar={() => setSidebarOpen((s) => !s)}
          dark={dark}
          onToggleTheme={toggleTheme}
        />

        <div className="flex-1 overflow-y-auto px-5 py-5 space-y-4">
          {activeConversation.messages.length === 0 && !loading && <EmptyState />}
          {activeConversation.messages.map((msg, i) => (
            <MessageBubble key={i} message={msg} />
          ))}
          {loading && <LoadingBubble />}
          {error && <p className="text-[#E5484D] text-sm text-center">{error}</p>}
          <div ref={bottomRef} />
        </div>

        <ChatInput value={question} onChange={setQuestion} onSubmit={handleSubmit} loading={loading} />
      </div>
    </main>
  );
}