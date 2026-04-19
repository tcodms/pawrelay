import { PawPrint } from "lucide-react";

export default function MatchingReasonBubble({ reason }: { reason: string }) {
  return (
    <div className="rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
      <div className="bg-[#A07050] px-4 py-2.5 flex items-center gap-1.5">
        <PawPrint size={12} className="text-white/70" />
        <p className="text-[12px] font-bold text-white">AI 매칭 이유</p>
      </div>
      <div className="px-4 py-3.5">
        <p className="text-[13px] text-gray-600 leading-relaxed">{reason}</p>
      </div>
    </div>
  );
}
