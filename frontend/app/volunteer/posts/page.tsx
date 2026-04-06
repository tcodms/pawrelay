export default function PostsPage() {
  return (
    <main className="flex min-h-[calc(100vh-4rem)] flex-col">
      <header className="sticky top-0 z-10 border-b border-gray-100 bg-white/90 px-5 py-4 backdrop-blur-sm">
        <h1 className="text-[18px] font-bold text-gray-900">공고 목록</h1>
      </header>
      <div className="flex flex-1 items-center justify-center">
        <p className="text-[14px] text-gray-400">공고 목록이 여기에 표시됩니다.</p>
      </div>
    </main>
  );
}
