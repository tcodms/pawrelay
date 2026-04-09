export default function VolunteerHeader({ title }: { title: string }) {
  return (
    <header className="sticky top-0 z-10 border-b border-gray-100 bg-white/90 px-5 py-4 backdrop-blur-sm">
      <div className="flex items-baseline gap-2.5">
        <span className="font-[family-name:var(--font-fredoka)] text-[22px] font-bold text-orange-500">
          PawRelay
        </span>
        <span className="text-gray-300">|</span>
        <h1 className="font-[family-name:var(--font-jua)] text-[15px] text-gray-500">
          {title}
        </h1>
      </div>
    </header>
  );
}
