export default function StepIndicator({ current }: { current: 1 | 2 }) {
  return (
    <div className="flex items-center justify-center gap-2 py-4">
      {[1, 2].map((s) => (
        <div key={s} className="flex items-center gap-2">
          <div
            className={`flex h-7 w-7 items-center justify-center rounded-full text-[12px] font-bold transition-colors duration-200 ${
              s <= current
                ? "bg-[#EEA968] text-white"
                : "bg-gray-100 text-gray-400"
            }`}
          >
            {s}
          </div>
          {s === 1 && (
            <div className={`h-px w-10 transition-colors duration-200 ${current === 2 ? "bg-[#EEA968]" : "bg-gray-200"}`} />
          )}
        </div>
      ))}
      <div className="sr-only">{current}단계 / 2단계</div>
    </div>
  );
}
