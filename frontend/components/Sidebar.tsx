"use client";

import { useEffect, useRef, useState } from "react";
import { Conversation } from "@/types/chat";

interface SidebarProps {
  open: boolean;
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDelete: (id: string) => void;
  onRename: (id: string, title: string) => void;
}

export default function Sidebar({
  open, conversations, activeId, onSelect, onNewChat, onDelete, onRename,
}: SidebarProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const editInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (editingId) editInputRef.current?.focus();
  }, [editingId]);

  function startEditing(conv: Conversation, e: React.MouseEvent) {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditingTitle(conv.title);
  }

  function saveEdit() {
    if (editingId && editingTitle.trim()) onRename(editingId, editingTitle.trim());
    setEditingId(null);
  }

  function handleEditKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") { e.preventDefault(); saveEdit(); }
    else if (e.key === "Escape") setEditingId(null);
  }

  return (
    <aside className={`${open ? "w-64" : "w-0"} shrink-0 border-r border-orange-100 dark:border-[#3A3025] bg-white dark:bg-[#221B14] flex flex-col transition-all overflow-hidden`}>
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="group w-full flex items-center gap-2 bg-[#FF7A33] hover:bg-[#FF6A1A] transition-all hover:scale-[1.02] active:scale-95 text-white text-sm font-semibold px-3 py-2.5 rounded-2xl shadow-sm"
          style={{ fontFamily: "var(--font-display)" }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="transition-transform duration-300 group-hover:rotate-90">
            <path d="M12 5v14M5 12h14" />
          </svg>
          Nouveau chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 space-y-1">
        {conversations.map((conv) => (
          <div
            key={conv.id}
            onClick={() => editingId !== conv.id && onSelect(conv.id)}
            onDoubleClick={(e) => startEditing(conv, e)}
            className={`group flex items-center justify-between gap-1 px-3 py-2.5 rounded-2xl cursor-pointer text-sm transition-colors ${
              conv.id === activeId
                ? "bg-orange-50 dark:bg-[#332A1E] text-[#2B2118] dark:text-orange-100"
                : "text-[#6B5F4F] dark:text-[#B8A98F] hover:bg-orange-50/60 dark:hover:bg-[#2A2219]"
            }`}
          >
            {editingId === conv.id ? (
              <input
                ref={editInputRef}
                value={editingTitle}
                onChange={(e) => setEditingTitle(e.target.value)}
                onBlur={saveEdit}
                onKeyDown={handleEditKeyDown}
                onClick={(e) => e.stopPropagation()}
                className="flex-1 bg-white dark:bg-[#1C1712] border border-[#FF7A33] rounded-lg px-2 py-0.5 text-sm text-[#2B2118] dark:text-orange-50 focus:outline-none min-w-0"
              />
            ) : (
              <>
                <span className="truncate">{conv.title}</span>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                  <button onClick={(e) => startEditing(conv, e)} className="text-[#B8A98F] hover:text-[#FF7A33] p-0.5" aria-label="Renommer">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                      <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                    </svg>
                  </button>
                  <button onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }} className="text-[#B8A98F] hover:text-[#FF7A33] p-0.5" aria-label="Supprimer">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M18 6L6 18M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </aside>
  );
}