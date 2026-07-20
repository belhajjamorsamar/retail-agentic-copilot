import ThemeToggle from "./ThemeToggle";

interface ChatHeaderProps {
  onToggleSidebar: () => void;
  dark: boolean;
  onToggleTheme: () => void;
}

export default function ChatHeader({ onToggleSidebar, dark, onToggleTheme }: ChatHeaderProps) {
  return (
    <div className="flex items-center justify-between px-5 py-4 border-b border-orange-100 dark:border-[#3A3025] bg-white dark:bg-[#221B14]">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
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
          <h1 className="text-base font-semibold text-[#2B2118] dark:text-orange-50" style={{ fontFamily: "var(--font-display)" }}>
            Ton assistant marché
          </h1>
          <p className="text-xs text-[#8A7B63] dark:text-[#B8A98F]">Produits · stock · bons plans anti-gaspi</p>
        </div>
      </div>
      <ThemeToggle dark={dark} onToggle={onToggleTheme} />
    </div>
  );
}