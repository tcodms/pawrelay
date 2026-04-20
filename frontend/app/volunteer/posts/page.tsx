"use client";

import { useState, useRef, useEffect, useCallback, Suspense } from "react";
import dynamic from "next/dynamic";
import Image from "next/image";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowRight, Bell, Search } from "lucide-react";
import { getVolunteerPosts } from "@/lib/api/posts";
import type { VolunteerPost } from "@/lib/api/posts";

// ── 옵션 ──────────────────────────────────────────────────────────────────────

const REGION_OPTIONS = [
  "서울특별시", "부산광역시", "대구광역시", "인천광역시",
  "광주광역시", "대전광역시", "울산광역시", "세종특별자치시",
  "경기도", "강원도", "충청북도", "충청남도",
  "전북특별자치도", "전라남도", "경상북도", "경상남도", "제주특별자치도",
];

const SIZE_OPTIONS = [
  { value: "small",  label: "소형" },
  { value: "medium", label: "중형" },
  { value: "large",  label: "대형" },
] as const;

type AnimalSize = "small" | "medium" | "large";

// ── 헬퍼 ─────────────────────────────────────────────────────────────────────

function sizeBadge(size: string) {
  const map: Record<string, { label: string; cls: string }> = {
    small:  { label: "소형", cls: "bg-gray-100 text-gray-500" },
    medium: { label: "중형", cls: "bg-gray-100 text-gray-500" },
    large:  { label: "대형", cls: "bg-gray-100 text-gray-500" },
  };
  const { label, cls } = map[size] ?? { label: size, cls: "bg-gray-100 text-gray-500" };
  return { label, cls };
}

// ── 페이지 ────────────────────────────────────────────────────────────────────

const PAGE_SIZE = 20;

function PostsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const search = searchParams.get("q") ?? "";
  const region = searchParams.get("region") ?? "";
  const date   = searchParams.get("date") ?? "";
  const size   = (searchParams.get("size") ?? "") as AnimalSize | "";
  const page   = Number(searchParams.get("page") ?? "1");

  const [regionSearch, setRegionSearch] = useState("");
  const [open, setOpen] = useState<"region" | "date" | "size" | null>(null);
  const [activeCard, setActiveCard] = useState(0);
  const carouselRef = useRef<HTMLDivElement>(null);

  const [posts, setPosts] = useState<VolunteerPost[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchPosts = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const res = await getVolunteerPosts({
        region: region || search || undefined,
        date: date || undefined,
        animal_size: (size as AnimalSize) || undefined,
        page,
        limit: PAGE_SIZE,
      });
      setPosts(res.posts);
      setTotal(res.total);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [region, search, date, size, page]);

  useEffect(() => { fetchPosts(); }, [fetchPosts]);

  const urgentPosts = posts.slice(0, 3);
  const totalPages = Math.ceil(total / PAGE_SIZE);

  function pushParams(updates: Record<string, string>) {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(updates).forEach(([k, v]) => {
      if (v) params.set(k, v); else params.delete(k);
    });
    params.set("page", "1");
    router.replace(`/volunteer/posts?${params.toString()}`, { scroll: false });
  }

  function setPage(p: number) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", String(p));
    router.replace(`/volunteer/posts?${params.toString()}`, { scroll: false });
  }

  function handleCarouselScroll() {
    const el = carouselRef.current;
    if (!el || urgentPosts.length === 0) return;
    const cardWidth = el.scrollWidth / urgentPosts.length;
    setActiveCard(Math.round(el.scrollLeft / cardWidth));
  }

  function toggle(key: "region" | "date" | "size") {
    setOpen((prev) => {
      if (prev === key) return null;
      if (key === "region") setRegionSearch("");
      return key;
    });
  }

  const filteredRegions = REGION_OPTIONS.filter((r) => r.includes(regionSearch));

  return (
    <main className="min-h-screen bg-gray-50">

      {/* ── 1. 히어로 배너 ───────────────────────────────────────────────── */}
      <section className="relative overflow-hidden w-full">
        <svg className="w-full block md:hidden" viewBox="0 0 390 155" xmlns="http://www.w3.org/2000/svg">
          <path d="M0 0 L390 0 L390 125 C315 150 210 112 110 132 C55 143 0 140 0 126 Z" fill="#EEA968" opacity="0.30"/>
          <path d="M265 0 L390 0 L390 100 C372 122 338 105 305 78 C275 54 260 22 265 0 Z" fill="#7A4A28" opacity="0.10"/>
        </svg>
        <svg className="w-full hidden md:block h-[140px]" viewBox="0 0 1440 130" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0 0 L1440 0 L1440 105 C1100 128 750 96 450 112 C200 125 80 122 0 110 Z" fill="#EEA968" opacity="0.30"/>
          <path d="M1150 0 L1440 0 L1440 100 C1420 118 1378 108 1338 88 C1300 70 1272 32 1265 0 Z" fill="#7A4A28" opacity="0.10"/>
        </svg>
        <div className="absolute inset-0 flex flex-col justify-between">
          <div className="mx-auto w-full max-w-2xl px-5 pt-5 pb-4 flex flex-col justify-between h-full">
            <div>
              <p className="text-[21px] font-bold text-[#5C3317] leading-snug">
                안녕하세요, 김봉사님
              </p>
              <p className="text-[13px] text-[#7A4A28]/70 mt-0.5">오늘도 따뜻한 손길을 기다리고 있어요.</p>
            </div>
            <div className="flex items-center gap-2 w-full rounded-2xl bg-white/80 backdrop-blur-sm border border-white/60 shadow-sm px-4 py-2.5">
              <Search size={16} className="text-gray-400 shrink-0" />
              <input
                type="text"
                value={search}
                onChange={(e) => pushParams({ q: e.target.value })}
                placeholder="지역 이름으로 검색"
                className="flex-1 bg-transparent text-[13px] text-gray-700 placeholder:text-gray-400 outline-none"
              />
            </div>
          </div>
        </div>
      </section>

      {/* ── 2. 긴급 릴레이 ───────────────────────────────────────────────── */}
      {!loading && urgentPosts.length > 0 && (
        <div className="mx-auto max-w-2xl">
          <div className="flex items-center gap-2 px-4 mt-4 mb-2.5">
            <div className="flex h-5 w-5 items-center justify-center rounded-full bg-red-500">
              <Bell size={11} className="text-white" fill="white" />
            </div>
            <p className="text-[13px] font-bold text-gray-800">최신 릴레이</p>
          </div>
          <div
            ref={carouselRef}
            onScroll={handleCarouselScroll}
            className="flex gap-3 overflow-x-auto snap-x snap-mandatory scroll-pl-4 pb-2 [&::-webkit-scrollbar]:hidden"
          >
            <div className="shrink-0 w-4" />
            {urgentPosts.map((post) => {
              const { label, cls } = sizeBadge(post.animal_size);
              return (
                <Link
                  key={post.id}
                  href={`/volunteer/posts/${post.id}`}
                  className="snap-start shrink-0 w-52 rounded-2xl bg-white border border-orange-100 shadow-sm overflow-hidden active:scale-[0.97] transition-transform"
                >
                  <div className="relative h-32 w-full bg-[#FDF3EC]">
                    {post.animal_photo_url ? (
                      <Image src={post.animal_photo_url} alt="동물" fill className="object-cover" />
                    ) : (
                      <div className="flex h-full items-center justify-center text-4xl">🐾</div>
                    )}
                    <div className={`absolute top-2 right-2 rounded-full px-2 py-0.5 text-[9px] font-bold ${cls}`}>
                      {label}
                    </div>
                  </div>
                  <div className="px-4 py-3.5">
                    <div className="flex items-center gap-1">
                      <span className="text-[12px] font-semibold text-gray-700 truncate">{post.origin}</span>
                      <ArrowRight size={11} className="text-gray-400 shrink-0" />
                      <span className="text-[12px] font-semibold text-gray-700 truncate">{post.destination}</span>
                    </div>
                    <p className="text-[10px] text-gray-400 mt-2">{post.scheduled_date}</p>
                  </div>
                </Link>
              );
            })}
            <div className="shrink-0 w-4" />
          </div>
          <div className="flex items-center justify-center gap-1.5 mt-2 mb-1">
            {urgentPosts.map((_, i) => (
              <span
                key={i}
                className={`rounded-full transition-all duration-300 ${
                  i === activeCard ? "w-4 h-1.5 bg-[#EEA968]" : "w-1.5 h-1.5 bg-gray-200"
                }`}
              />
            ))}
          </div>
        </div>
      )}

      {/* ── 3. 전체 공고 리스트 ──────────────────────────────────────────── */}
      <section className="mx-auto max-w-2xl mt-5 px-4 pb-8">
        <div className="flex items-center justify-between mb-3">
          <p className="text-[17px] font-bold text-gray-800">
            전체 공고 <span className="text-[#EEA968]">{loading ? "…" : total}</span>
          </p>
          <p className="text-[11px] text-gray-400">최신순</p>
        </div>

        {/* 필터 뱃지 */}
        <div className="mb-4">
          {open && <div className="fixed inset-0 z-10" onClick={() => setOpen(null)} />}
          <div className="flex items-center gap-2">
            {/* 지역 */}
            <div className="relative">
              <button
                onClick={() => toggle("region")}
                className={`flex items-center gap-1 rounded-full px-3 py-1.5 text-[12px] font-semibold border transition-all ${
                  open === "region" ? "bg-white text-[#EEA968] border-[#EEA968]" : "bg-white text-gray-600 border-gray-200"
                }`}
              >
                지역
              </button>
              {open === "region" && (
                <div className="absolute left-0 top-full mt-1.5 z-20 w-52 rounded-2xl bg-white border border-gray-100 shadow-lg overflow-hidden">
                  <div className="px-3 pt-3 pb-2">
                    <div className="flex items-center gap-2 rounded-xl bg-gray-50 border border-gray-200 px-3 py-2">
                      <Search size={13} className="text-gray-400 shrink-0" />
                      <input
                        autoFocus
                        type="text"
                        value={regionSearch}
                        onChange={(e) => setRegionSearch(e.target.value)}
                        placeholder="지역 검색"
                        className="flex-1 bg-transparent text-[12px] text-gray-700 placeholder:text-gray-400 outline-none"
                      />
                    </div>
                  </div>
                  <div className="max-h-40 overflow-y-auto pb-2">
                    {filteredRegions.length === 0 ? (
                      <p className="px-4 py-3 text-[12px] text-gray-400 text-center">결과 없음</p>
                    ) : (
                      filteredRegions.map((r) => (
                        <button
                          key={r}
                          onClick={() => { pushParams({ region: region === r ? "" : r }); setOpen(null); setRegionSearch(""); }}
                          className={`w-full px-4 py-2.5 text-left text-[13px] font-semibold transition-colors ${
                            region === r ? "text-[#EEA968] bg-[#FDF3EC]" : "text-gray-700 hover:bg-gray-50"
                          }`}
                        >
                          {r}
                        </button>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* 날짜 */}
            <div className="relative">
              <button
                onClick={() => toggle("date")}
                className={`flex items-center gap-1 rounded-full px-3 py-1.5 text-[12px] font-semibold border transition-all ${
                  open === "date" ? "bg-white text-[#EEA968] border-[#EEA968]" : "bg-white text-gray-600 border-gray-200"
                }`}
              >
                날짜
              </button>
              {open === "date" && (
                <div className="absolute left-0 top-full mt-1.5 z-20 w-52 rounded-2xl bg-white border border-gray-100 shadow-lg p-3">
                  <p className="text-[11px] text-gray-400 mb-2">날짜 선택</p>
                  <input
                    type="date"
                    value={date}
                    onChange={(e) => { pushParams({ date: e.target.value }); setOpen(null); }}
                    className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-[13px] text-gray-700 focus:outline-none focus:border-[#EEA968]/60"
                  />
                  {date && (
                    <button
                      onClick={() => { pushParams({ date: "" }); setOpen(null); }}
                      className="mt-2 w-full text-[11px] text-gray-400 text-center"
                    >
                      날짜 해제
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* 크기 */}
            <div className="relative">
              <button
                onClick={() => toggle("size")}
                className={`flex items-center gap-1 rounded-full px-3 py-1.5 text-[12px] font-semibold border transition-all ${
                  open === "size" ? "bg-white text-[#EEA968] border-[#EEA968]" : "bg-white text-gray-600 border-gray-200"
                }`}
              >
                크기
              </button>
              {open === "size" && (
                <div className="absolute left-0 top-full mt-1.5 z-20 w-36 rounded-2xl bg-white border border-gray-100 shadow-lg overflow-hidden">
                  <div className="flex flex-col py-1">
                    {SIZE_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        onClick={() => { pushParams({ size: size === opt.value ? "" : opt.value }); setOpen(null); }}
                        className={`px-4 py-2.5 text-left text-[13px] font-semibold transition-colors ${
                          size === opt.value ? "text-[#EEA968] bg-[#FDF3EC]" : "text-gray-700 hover:bg-gray-50"
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 선택된 필터 칩 */}
          {(region || date || size) && (
            <div className="flex flex-wrap items-center gap-1.5 mt-2.5">
              {region && (
                <span className="flex items-center gap-1 rounded-full bg-[#EEA968] px-3 py-1 text-[11px] font-semibold text-white">
                  {region}
                  <button onClick={() => pushParams({ region: "" })} className="ml-0.5 leading-none">×</button>
                </span>
              )}
              {date && (
                <span className="flex items-center gap-1 rounded-full bg-[#EEA968] px-3 py-1 text-[11px] font-semibold text-white">
                  {date}
                  <button onClick={() => pushParams({ date: "" })} className="ml-0.5 leading-none">×</button>
                </span>
              )}
              {size && (
                <span className="flex items-center gap-1 rounded-full bg-[#EEA968] px-3 py-1 text-[11px] font-semibold text-white">
                  {SIZE_OPTIONS.find((o) => o.value === size)?.label}
                  <button onClick={() => pushParams({ size: "" })} className="ml-0.5 leading-none">×</button>
                </span>
              )}
            </div>
          )}
        </div>

        {/* 공고 카드 목록 */}
        {loading ? (
          <div className="flex flex-col gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-36 rounded-2xl bg-white border border-gray-100 shadow-sm animate-pulse" />
            ))}
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <p className="text-[15px] font-bold text-gray-700 mb-1">불러오기 실패</p>
            <p className="text-[13px] text-gray-400 mb-4">네트워크를 확인해주세요.</p>
            <button
              onClick={fetchPosts}
              className="rounded-full bg-[#EEA968] px-5 py-2 text-[13px] font-bold text-white"
            >
              다시 시도
            </button>
          </div>
        ) : posts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <p className="text-[15px] font-bold text-gray-700 mb-1">공고가 없어요</p>
            <p className="text-[13px] text-gray-400">다른 필터로 검색해보세요.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {posts.map((post) => {
              const { label, cls } = sizeBadge(post.animal_size);
              return (
                <Link
                  key={post.id}
                  href={`/volunteer/posts/${post.id}`}
                  className="rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden active:scale-[0.97] transition-transform"
                >
                  <div className="flex gap-4 p-4">
                    <div className="relative shrink-0 w-28 h-28 rounded-2xl overflow-hidden bg-[#FDF3EC]">
                      {post.animal_photo_url ? (
                        <Image src={post.animal_photo_url} alt="동물" fill className="object-cover" />
                      ) : (
                        <div className="flex h-full items-center justify-center text-3xl">🐾</div>
                      )}
                    </div>
                    <div className="flex flex-col justify-between flex-1 min-w-0 py-0.5">
                      <div>
                        <div className="flex flex-col min-w-0 mb-2.5">
                          <span className="text-[13px] font-bold text-gray-900 leading-snug">{post.origin}</span>
                          <div className="flex items-center gap-1 mt-1">
                            <ArrowRight size={11} className="text-gray-400 shrink-0" />
                            <span className="text-[13px] font-bold text-gray-900 leading-snug">{post.destination}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 mt-3">
                        <span className={`rounded-full px-2 py-0.5 text-[9px] font-bold ${cls}`}>{label}</span>
                        <span className="text-[10px] text-gray-400">{post.scheduled_date}</span>
                      </div>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}

        {/* 페이지네이션 */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-1.5 mt-6 mb-2">
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
              <button
                key={p}
                onClick={() => setPage(p)}
                className={`w-8 h-8 rounded-full text-[13px] font-semibold transition-all ${
                  p === page ? "bg-[#EEA968] text-white" : "bg-white border border-gray-200 text-gray-500"
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        )}
      </section>

    </main>
  );
}

function PostsPageSkeleton() {
  return (
    <main className="min-h-screen bg-gray-50">
      <div className="h-[155px] w-full bg-[#EEA968]/20 animate-pulse" />
      <div className="mx-auto max-w-2xl px-4 pt-4 space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 rounded-2xl bg-gray-100 animate-pulse" />
        ))}
      </div>
    </main>
  );
}

const PostsPageClient = dynamic(() => Promise.resolve(PostsPage), {
  ssr: false,
  loading: PostsPageSkeleton,
});

export default function PostsPageWrapper() {
  return <PostsPageClient />;
}
