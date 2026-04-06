import VolunteerHeader from "@/components/VolunteerHeader";

export default function MyPage() {
  return (
    <main className="flex min-h-[calc(100vh-4rem)] flex-col">
      <VolunteerHeader title="마이페이지" />
      <div className="flex flex-1 items-center justify-center">
        <p className="text-[14px] text-gray-400">마이페이지가 여기에 표시됩니다.</p>
      </div>
    </main>
  );
}
