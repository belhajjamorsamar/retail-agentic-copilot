import { Conversation } from "@/types/chat";

const STORAGE_KEY = "retail-copilot-conversations";
const THEME_KEY = "theme";

export function createConversation(): Conversation {
  return {
    id: crypto.randomUUID(),
    title: "Nouvelle conversation",
    messages: [],
    createdAt: Date.now(),
  };
}

export function loadConversations(): Conversation[] {
  const saved = localStorage.getItem(STORAGE_KEY);
  const convos: Conversation[] = saved ? JSON.parse(saved) : [];
  return convos.length > 0 ? convos : [createConversation()];
}

export function saveConversations(conversations: Conversation[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
}

export function loadThemePreference(): boolean {
  const saved = localStorage.getItem(THEME_KEY);
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  return saved ? saved === "dark" : prefersDark;
}

export function saveThemePreference(isDark: boolean) {
  localStorage.setItem(THEME_KEY, isDark ? "dark" : "light");
}