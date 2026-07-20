import { Message } from "@/types/chat";

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex gap-2.5 animate-message ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm shrink-0 shadow-sm ${
        isUser ? "bg-[#2B2118] dark:bg-orange-100" : "bg-gradient-to-br from-[#3FA66B] to-[#4CAF6D]"
      }`}>
        {isUser ? "🙂" : "🛒"}
      </div>
      <div className={`max-w-[78%] rounded-3xl px-4 py-2.5 text-sm leading-relaxed shadow-sm ${
        isUser
          ? "bg-[#FF7A33] text-white rounded-tr-md"
          : "bg-white dark:bg-[#2A2219] text-[#2B2118] dark:text-orange-50 rounded-tl-md border border-orange-100 dark:border-[#3A3025]"
      }`}>
        <p className="whitespace-pre-line">{message.content}</p>
        {message.sources && message.sources.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2.5 pt-2.5 border-t border-orange-100 dark:border-[#3A3025]">
            {message.sources.map((source, j) => (
              <span key={j} className="text-[11px] px-2.5 py-0.5 rounded-full bg-[#F1F9F0] dark:bg-[#22301F] text-[#3FA66B] dark:text-[#7FD498] border border-[#CFEBD3] dark:border-[#3A4A32] font-medium">
                {source}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}