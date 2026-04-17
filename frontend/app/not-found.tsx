import Link from "next/link";

export default function NotFound() {
  return (
    <main className="min-h-screen bg-gray-50 flex flex-col items-center justify-center gap-4 px-6">
      <p className="text-[48px] leading-none">🐾</p>
      <p className="text-[20px] font-bold text-gray-800">페이지를 찾을 수 없어요</p>
      <p className="text-[13px] text-gray-400 text-center">
        주소가 잘못되었거나 삭제된 페이지입니다.
      </p>
      <Link
        href="/"
        className="mt-2 rounded-full bg-[#EEA968] px-6 py-2.5 text-[14px] font-bold text-white shadow-md shadow-[#EEA968]/20"
      >
        홈으로 돌아가기
      </Link>
    </main>
  );
}
