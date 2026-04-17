"use client";

import { useState, useRef } from "react";
import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Users, Bell, Search } from "lucide-react";
import { DUMMY_POSTS } from "@/lib/dummy-posts";

// ── 긴급 공고 더미 ────────────────────────────────────────────────────────────

const URGENT_POSTS = [
  {
    id: 301,
    animal: { name: "콩이",  photo_url: "https://images.unsplash.com/photo-1552053831-71594a27632d?w=600", size: "small"  },
    origin: "광주", destination: "서울", scheduled_date: "2026-04-18",
  },
  {
    id: 302,
    animal: { name: "복실이", photo_url: "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=600", size: "small"  },
    origin: "부산", destination: "인천", scheduled_date: "2026-04-18",
  },
  {
    id: 303,
    animal: { name: "두부",  photo_url: "https://images.unsplash.com/photo-1574144611937-0df059b5ef3e?w=600", size: "small"  },
    origin: "전주", destination: "수원", scheduled_date: "2026-04-19",
  },
  {
    id: 304,
    animal: { name: "몽실",  photo_url: "https://images.unsplash.com/photo-1477884213360-7e9d7dcc1e48?w=600", size: "large"  },
    origin: "대전", destination: "서울", scheduled_date: "2026-04-19",
  },
];

// ── 추가 더미 공고 (그리드 채우기) ───────────────────────────────────────────

const EXTRA_POSTS = [
  {
    id: 401,
    animal: { name: "해피",  photo_url: "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400", size: "medium" as const },
    origin: "대구광역시", destination: "경기도 용인시",
    scheduled_date: "2026-04-21", volunteers: [] as { id: number }[],
    status: "recruiting" as const,
  },
  {
    id: 402,
    animal: { name: "쿠키",  photo_url: "https://images.unsplash.com/photo-1518717758536-85ae29035b6d?w=400", size: "small"  as const },
    origin: "울산광역시", destination: "서울특별시 마포구",
    scheduled_date: "2026-04-22", volunteers: [{ id: 1 }] as { id: number }[],
    status: "recruiting" as const,
  },
  {
    id: 403,
    animal: { name: "보리",  photo_url: "https://images.unsplash.com/photo-1537151625747-768eb6cf92b2?w=400", size: "medium" as const },
    origin: "강원도 춘천시", destination: "인천광역시",
    scheduled_date: "2026-04-23", volunteers: [{ id: 1 }, { id: 2 }] as { id: number }[],
    status: "recruiting" as const,
  },
];

// ── 동물 크기 필터 옵션 ───────────────────────────────────────────────────────

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

function shortRegion(full: string) {
  return full.split(" ")[0].replace("광역시", "").replace("특별시", "").replace("광역도", "");
}

// ── 페이지 ────────────────────────────────────────────────────────────────────

const REGION_OPTIONS = [
  "서울특별시", "부산광역시", "대구광역시", "인천광역시",
  "광주광역시", "대전광역시", "울산광역시", "세종특별자치시",
  "경기도", "강원도", "충청북도", "충청남도",
  "전북특별자치도", "전라남도", "경상북도", "경상남도", "제주특별자치도",
];

export default function PostsPage() {
  const [search, setSearch]       = useState("");
  const [region, setRegion]       = useState("");
  const [regionSearch, setRegionSearch] = useState("");
  const [date, setDate]           = useState("");
  const [size, setSize]           = useState<AnimalSize | null>(null);
  const [open, setOpen]           = useState<"region" | "date" | "size" | null>(null);
  const [page, setPage]           = useState(1);
  const [activeCard, setActiveCard] = useState(0);

  const PAGE_SIZE = 5;
  const carouselRef = useRef<HTMLDivElement>(null);

  function handleCarouselScroll() {
    const el = carouselRef.current;
    if (!el) return;
    const cardWidth = el.scrollWidth / URGENT_POSTS.length;
    setActiveCard(Math.round(el.scrollLeft / cardWidth));
  }

  const allPosts = [
    ...DUMMY_POSTS.filter((p) => p.status === "recruiting"),
    ...EXTRA_POSTS,
  ];

  const recruitingPosts = allPosts.filter((p) => {
    if (search && !p.origin.includes(search) && !p.destination.includes(search)) return false;
    if (region && !p.origin.includes(region) && !p.destination.includes(region)) return false;
    if (date   && p.scheduled_date !== date) return false;
    if (size   && p.animal.size !== size)    return false;
    return true;
  });

  const totalPages = Math.ceil(recruitingPosts.length / PAGE_SIZE);
  const pagedPosts = recruitingPosts.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  function toggle(key: "region" | "date" | "size") {
    setOpen((prev) => {
      if (prev === key) return null;
      if (key === "region") setRegionSearch("");
      return key;
    });
  }

  function applyFilter(fn: () => void) {
    fn();
    setPage(1);
  }

  const filteredRegions = REGION_OPTIONS.filter((r) =>
    r.includes(regionSearch)
  );

  return (
    <main className="min-h-screen bg-gray-50">

      {/* ── 1. 히어로: 인사말 + 긴급 캐러셀 ─────────────────────────────── */}
      <section className="relative overflow-hidden w-full">
        {/* 모바일 물결 배경 */}
        <svg className="w-full block md:hidden" viewBox="0 0 390 155" xmlns="http://www.w3.org/2000/svg">
          <path d="M0 0 L390 0 L390 125 C315 150 210 112 110 132 C55 143 0 140 0 126 Z" fill="#EEA968" opacity="0.30"/>
          <path d="M265 0 L390 0 L390 100 C372 122 338 105 305 78 C275 54 260 22 265 0 Z" fill="#7A4A28" opacity="0.10"/>
        </svg>
        {/* 데스크탑 물결 배경 */}
        <svg className="w-full hidden md:block h-[140px]" viewBox="0 0 1440 130" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0 0 L1440 0 L1440 105 C1100 128 750 96 450 112 C200 125 80 122 0 110 Z" fill="#EEA968" opacity="0.30"/>
          <path d="M1150 0 L1440 0 L1440 100 C1420 118 1378 108 1338 88 C1300 70 1272 32 1265 0 Z" fill="#7A4A28" opacity="0.10"/>
        </svg>

        {/* 콘텐츠 오버레이 */}
        <div className="absolute inset-0 flex flex-col justify-between">
          <div className="mx-auto w-full max-w-2xl px-5 pt-5 pb-4 flex flex-col justify-between h-full">
            {/* 인사말 */}
            <div>
              <p className="text-[13px] text-[#7A4A28]/70 mb-0.5">오늘도 따뜻한 손길을 기다리고 있어요.</p>
              <p className="text-[21px] font-bold text-[#5C3317] leading-snug">
                안녕하세요,{" "}
                <span className="text-[#D4863A]">김봉사</span>님!
              </p>
            </div>

            {/* 검색창 */}
            <div className="flex items-center gap-2 w-full rounded-2xl bg-white/80 backdrop-blur-sm border border-white/60 shadow-sm px-4 py-2.5">
              <Search size={16} className="text-gray-400 shrink-0" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="지역 이름으로 검색"
                className="flex-1 bg-transparent text-[13px] text-gray-700 placeholder:text-gray-400 outline-none"
              />
            </div>
          </div>
        </div>
      </section>

      {/* 긴급 릴레이 레이블 + 캐러셀 */}
      <div className="mx-auto max-w-2xl">
        {/* 긴급 릴레이 레이블 */}
        <div className="flex items-center gap-2 px-4 mt-4 mb-2.5">
          <div className="flex h-5 w-5 items-center justify-center rounded-full bg-red-500">
            <Bell size={11} className="text-white" fill="white" />
          </div>
          <p className="text-[13px] font-bold text-gray-800">긴급 릴레이</p>
        </div>

        {/* 긴급 캐러셀 */}
        <div
          ref={carouselRef}
          onScroll={handleCarouselScroll}
          className="flex gap-3 overflow-x-auto snap-x snap-mandatory pb-2 [&::-webkit-scrollbar]:hidden"
        >
          <div className="shrink-0 w-4" />
          {URGENT_POSTS.map((post) => {
            const { label, cls } = sizeBadge(post.animal.size);
            return (
              <Link
                key={post.id}
                href={`/volunteer/posts/${post.id}`}
                className="snap-start shrink-0 w-52 rounded-2xl bg-white border border-red-100 shadow-sm overflow-hidden active:scale-[0.97] transition-transform"
              >
                {/* 사진 */}
                <div className="relative h-32 w-full bg-[#FDF3EC]">
                  <Image
                    src={post.animal.photo_url}
                    alt={post.animal.name}
                    fill
                    className="object-cover"
                  />
                  {/* 긴급 배지 */}
                  <div className="absolute top-2 left-2 flex items-center gap-1 rounded-full bg-red-500 px-2 py-0.5 shadow">
                    <span className="h-1.5 w-1.5 rounded-full bg-white animate-pulse" />
                    <span className="text-[10px] font-bold text-white">긴급</span>
                  </div>
                  {/* 사이즈 배지 */}
                  <div className={`absolute top-2 right-2 rounded-full px-2 py-0.5 text-[9px] font-bold ${cls}`}>
                    {label}
                  </div>
                </div>

                {/* 정보 */}
                <div className="px-4 py-3.5">
                  <p className="text-[14px] font-bold text-[#5C3317] mb-2">{post.animal.name}</p>
                  <div className="flex items-center gap-1">
                    <span className="text-[12px] font-semibold text-gray-700">{post.origin}</span>
                    <ArrowRight size={11} className="text-gray-400 shrink-0" />
                    <span className="text-[12px] font-semibold text-gray-700">{post.destination}</span>
                  </div>
                  <p className="text-[10px] text-gray-400 mt-2">{post.scheduled_date}</p>
                </div>
              </Link>
            );
          })}
          <div className="shrink-0 w-4" />
        </div>

        {/* 점 인디케이터 */}
        <div className="flex items-center justify-center gap-1.5 mt-2 mb-1">
          {URGENT_POSTS.map((_, i) => (
            <span
              key={i}
              className={`rounded-full transition-all duration-300 ${
                i === activeCard
                  ? "w-4 h-1.5 bg-[#EEA968]"
                  : "w-1.5 h-1.5 bg-gray-200"
              }`}
            />
          ))}
        </div>
      </div>

      {/* ── 2. 전체 공고 리스트 (Pinterest Grid) ─────────────────────────── */}
      <section className="mx-auto max-w-2xl mt-5 px-4 pb-8">
        <div className="flex items-center justify-between mb-3">
          <p className="text-[17px] font-bold text-gray-800">
            전체 공고{" "}
            <span className="text-[#EEA968]">{recruitingPosts.length}</span>
          </p>
          <p className="text-[11px] text-gray-400">최신순</p>
        </div>

        {/* 공고 필터 뱃지 */}
        <div className="mb-4">
          {/* 드롭다운 외부 클릭 닫기 */}
          {open && (
            <div className="fixed inset-0 z-10" onClick={() => setOpen(null)} />
          )}

          <div className="flex items-center gap-2">
            {/* 지역 뱃지 */}
            <div className="relative">
              <button
                onClick={() => toggle("region")}
                className={`flex items-center gap-1 rounded-full px-3 py-1.5 text-[12px] font-semibold border transition-all ${
                  open === "region"
                    ? "bg-white text-[#EEA968] border-[#EEA968]"
                    : "bg-white text-gray-600 border-gray-200"
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
                          onClick={() => { setRegion(region === r ? "" : r); setOpen(null); setRegionSearch(""); }}
                          className={`w-full px-4 py-2.5 text-left text-[13px] font-semibold transition-colors ${
                            region === r
                              ? "text-[#EEA968] bg-[#FDF3EC]"
                              : "text-gray-700 hover:bg-gray-50"
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

            {/* 날짜 뱃지 */}
            <div className="relative">
              <button
                onClick={() => toggle("date")}
                className={`flex items-center gap-1 rounded-full px-3 py-1.5 text-[12px] font-semibold border transition-all ${
                  open === "date"
                    ? "bg-white text-[#EEA968] border-[#EEA968]"
                    : "bg-white text-gray-600 border-gray-200"
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
                    onChange={(e) => { setDate(e.target.value); setOpen(null); }}
                    className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-[13px] text-gray-700 focus:outline-none focus:border-[#EEA968]/60"
                  />
                  {date && (
                    <button
                      onClick={() => { setDate(""); setOpen(null); }}
                      className="mt-2 w-full text-[11px] text-gray-400 text-center"
                    >
                      날짜 해제
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* 동물 크기 뱃지 */}
            <div className="relative">
              <button
                onClick={() => toggle("size")}
                className={`flex items-center gap-1 rounded-full px-3 py-1.5 text-[12px] font-semibold border transition-all ${
                  open === "size"
                    ? "bg-white text-[#EEA968] border-[#EEA968]"
                    : "bg-white text-gray-600 border-gray-200"
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
                        onClick={() => { setSize(size === opt.value ? null : opt.value); setOpen(null); }}
                        className={`px-4 py-2.5 text-left text-[13px] font-semibold transition-colors ${
                          size === opt.value
                            ? "text-[#EEA968] bg-[#FDF3EC]"
                            : "text-gray-700 hover:bg-gray-50"
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
                  <button onClick={() => applyFilter(() => setRegion(""))} className="ml-0.5 leading-none">×</button>
                </span>
              )}
              {date && (
                <span className="flex items-center gap-1 rounded-full bg-[#EEA968] px-3 py-1 text-[11px] font-semibold text-white">
                  {date}
                  <button onClick={() => applyFilter(() => setDate(""))} className="ml-0.5 leading-none">×</button>
                </span>
              )}
              {size && (
                <span className="flex items-center gap-1 rounded-full bg-[#EEA968] px-3 py-1 text-[11px] font-semibold text-white">
                  {SIZE_OPTIONS.find((o) => o.value === size)?.label}
                  <button onClick={() => applyFilter(() => setSize(null))} className="ml-0.5 leading-none">×</button>
                </span>
              )}
            </div>
          )}
        </div>

        <div className="flex flex-col gap-3">
          {pagedPosts.map((post) => {
            const { label, cls } = sizeBadge(post.animal.size);
            return (
              <Link
                key={post.id}
                href={`/volunteer/posts/${post.id}`}
                className="rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden active:scale-[0.97] transition-transform"
              >
                <div className="flex gap-4 p-4">
                  {/* 동물 사진 */}
                  <div className="relative shrink-0 w-20 h-20 rounded-2xl overflow-hidden bg-[#FDF3EC]">
                    {post.animal.photo_url ? (
                      <Image
                        src={post.animal.photo_url}
                        alt={post.animal.name}
                        fill
                        className="object-cover"
                      />
                    ) : (
                      <div className="flex h-full items-center justify-center text-3xl">🐾</div>
                    )}
                  </div>

                  {/* 카드 정보 */}
                  <div className="flex flex-col justify-between flex-1 min-w-0 py-0.5">
                    {/* 경로 */}
                    <div>
                      <div className="flex flex-col min-w-0 mb-2.5">
                        <span className="text-[13px] font-bold text-gray-900 leading-snug">{post.origin}</span>
                        <div className="flex items-center gap-1 mt-1">
                          <ArrowRight size={11} className="text-gray-400 shrink-0" />
                          <span className="text-[13px] font-bold text-gray-900 leading-snug">{post.destination}</span>
                        </div>
                      </div>

                      {/* 동물 이름 */}
                      <p className="text-[11px] font-semibold text-[#7A4A28]">{post.animal.name}</p>
                    </div>

                    {/* 날짜 + 사이즈 + 지원자 수 */}
                    <div className="flex items-center gap-2 mt-3">
                      <span className={`rounded-full px-2 py-0.5 text-[9px] font-bold ${cls}`}>{label}</span>
                      <span className="text-[10px] text-gray-400">{post.scheduled_date}</span>
                      <div className="ml-auto flex items-center gap-0.5 text-[10px] text-gray-500">
                        <Users size={10} className="text-gray-300" />
                        <span>{post.volunteers.length}명</span>
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>

        {/* 페이지네이션 */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-1.5 mt-6 mb-2">
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
              <button
                key={p}
                onClick={() => setPage(p)}
                className={`w-8 h-8 rounded-full text-[13px] font-semibold transition-all ${
                  p === page
                    ? "bg-[#EEA968] text-white"
                    : "bg-white border border-gray-200 text-gray-500"
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
