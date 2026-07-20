export default function EmptyState() {
  return (
    <div className="text-center mt-16">
      <div className="text-4xl mb-3">🥬</div>
      <p className="text-[#2B2118] dark:text-orange-50 text-base font-semibold" style={{ fontFamily: "var(--font-display)" }}>
        Salut ! Qu&apos;est-ce qu&apos;on cherche aujourd&apos;hui ?
      </p>
      <p className="text-[#8A7B63] dark:text-[#B8A98F] text-sm mt-1">
        Essayez : « Vous avez des yaourts en promo ? »
      </p>
    </div>
  );
}