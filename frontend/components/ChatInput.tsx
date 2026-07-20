interface ChatInputProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  loading: boolean;
}

export default function ChatInput({ value, onChange, onSubmit, loading }: ChatInputProps) {
  return (
    <form onSubmit={onSubmit} className="border-t border-orange-100 dark:border-[#3A3025] bg-white dark:bg-[#221B14] p-3 flex gap-2">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
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
  );
}