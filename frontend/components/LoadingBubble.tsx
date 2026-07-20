export default function LoadingBubble() {
  return (
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
  );
}