import VolunteerHeader from "@/components/VolunteerHeader";

export default function PostsPage() {
  return (
    <main className="flex min-h-[calc(100vh-4rem)] flex-col">
      <VolunteerHeader title="공고 목록" />
      <div className="flex flex-1 items-center justify-center">
        <p className="text-[14px] text-gray-400">공고 목록이 여기에 표시됩니다.</p>
      </div>
    </main>
  );
}
