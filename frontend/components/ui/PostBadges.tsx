import type { PostStatus } from "@/lib/api/posts";

const STATUS_MAP: Record<PostStatus, { label: string; color: string }> = {
  urgent:      { label: "긴급",     color: "bg-red-100 text-red-600" },
  recruiting:  { label: "모집 중",  color: "bg-green-100 text-green-700" },
  waiting:     { label: "대기 중",  color: "bg-yellow-100 text-yellow-700" },
  in_progress: { label: "봉사 중",  color: "bg-blue-100 text-blue-700" },
  completed:   { label: "봉사 종료", color: "bg-gray-100 text-gray-500" },
};

const SIZE_COLOR: Record<string, string> = {
  소형: "bg-sky-50 text-sky-600",
  중형: "bg-indigo-50 text-indigo-600",
  대형: "bg-purple-50 text-purple-600",
};

/** variant="sm" — 목록 카드용, variant="md" — 상세 페이지용 */
export function StatusBadge({
  status,
  variant = "md",
}: {
  status: PostStatus;
  variant?: "sm" | "md";
}) {
  const { label, color } = STATUS_MAP[status];
  const size = variant === "sm" ? "px-2.5 py-0.5 text-[11px]" : "px-3 py-1 text-[12px]";
  return (
    <span className={`rounded-full font-semibold ${size} ${color}`}>{label}</span>
  );
}

export function SizeBadge({
  size,
  variant = "md",
}: {
  size: string;
  variant?: "sm" | "md";
}) {
  const sizeClass = variant === "sm" ? "px-2 py-0.5 text-[10px]" : "px-3 py-1 text-[12px]";
  return (
    <span className={`rounded-full font-medium ${sizeClass} ${SIZE_COLOR[size] ?? ""}`}>
      {size}
    </span>
  );
}
