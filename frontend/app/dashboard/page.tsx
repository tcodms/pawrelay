import Link from "next/link";

function Sidebar({ active }: { active: string }) {
  const links = [
    { label: "대시보드", href: "/dashboard" },
    { label: "공고 관리", href: "/dashboard/posts" },
    { label: "지원자 관리", href: "/dashboard/applicants" },
    { label: "매칭 결과", href: "/dashboard/matching" },
    { label: "마이페이지", href: "/dashboard/mypage" },
  ];
  return (
    <aside className="w-52 shrink-0 border-r border-gray-100 bg-white p-5 flex flex-col min-h-screen">
      <div className="mb-8">
        <p className="text-lg font-bold text-orange-500">PawRelay</p>
        <p className="text-xs text-gray-400 mt-0.5">보호소 관리</p>
      </div>
      <nav className="flex flex-col gap-0.5">
        {links.map(({ label, href }) => (
          <Link
            key={href}
            href={href}
            className={`rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
              active === href
                ? "bg-orange-50 text-orange-600 font-semibold"
                : "text-gray-500 hover:bg-gray-50"
            }`}
          >
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}

const statCards = [
  { label: "모집중", count: 3, bg: "bg-orange-50", text: "text-orange-600" },
  { label: "매칭완료", count: 7, bg: "bg-blue-50", text: "text-blue-600" },
  { label: "이동중", count: 2, bg: "bg-green-50", text: "text-green-600" },
  { label: "완료", count: 41, bg: "bg-gray-50", text: "text-gray-500" },
];

const recentPosts = [
  { status: "모집중", chipClass: "bg-orange-100 text-orange-600" },
  { status: "매칭완료", chipClass: "bg-blue-100 text-blue-600" },
  { status: "이동중", chipClass: "bg-green-100 text-green-600" },
  { status: "완료", chipClass: "bg-gray-100 text-gray-500" },
];

export default function DashboardPage() {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar active="/dashboard" />
      <main className="flex-1 p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-xl font-bold text-gray-900">안녕하세요, ○○보호소님</h1>
            <p className="text-sm text-gray-400 mt-0.5">오늘도 릴레이 이동봉사를 도와드릴게요.</p>
          </div>
          <Link
            href="/dashboard/posts/new"
            className="rounded-2xl bg-orange-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-orange-600 transition-colors"
          >
            + 공고 등록
          </Link>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-8">
          {statCards.map(({ label, count, bg, text }) => (
            <div key={label} className={`rounded-2xl border border-gray-100 ${bg} p-5`}>
              <p className="text-sm text-gray-500 mb-1">{label}</p>
              <p className={`text-3xl font-bold ${text}`}>{count}건</p>
            </div>
          ))}
        </div>

        <div className="rounded-2xl border border-gray-100 bg-white p-6">
          <h2 className="text-base font-semibold text-gray-800 mb-4">최근 공고</h2>
          <div className="flex flex-col gap-3">
            {recentPosts.map(({ status, chipClass }, index) => (
              <div
                key={index}
                className="flex items-center gap-4 rounded-xl bg-gray-50 px-4 py-3"
              >
                <div className="h-4 flex-1 rounded bg-gray-200" />
                <span className={`rounded-full px-3 py-1 text-xs font-medium ${chipClass}`}>
                  {status}
                </span>
                <div className="h-3 w-20 rounded bg-gray-200" />
                <Link
                  href="/dashboard/posts/1"
                  className="text-sm text-orange-500 font-medium hover:underline"
                >
                  보기
                </Link>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
