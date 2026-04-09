"use client";

import Link from "next/link";
import Image from "next/image";
import { ArrowLeft, ArrowDown, ArrowRight, Calendar, MapPin, Pencil, Trash2, Users } from "lucide-react";
import { getPost, PostStatus } from "@/lib/api/posts";

function statusBadge(status: PostStatus) {
  const map: Record<PostStatus, { label: string; className: string }> = {
    urgent:      { label: "긴급",     className: "bg-red-100 text-red-600" },
    recruiting:  { label: "모집 중", className: "bg-green-100 text-green-700" },
    waiting:     { label: "대기 중", className: "bg-yellow-100 text-yellow-700" },
    in_progress: { label: "봉사 중", className: "bg-blue-100 text-blue-700" },
    completed:   { label: "봉사 종료", className: "bg-gray-100 text-gray-500" },
  };
  const { label, className } = map[status];
  return (
    <span className={`rounded-full px-3 py-1 text-[12px] font-semibold ${className}`}>
      {label}
    </span>
  );
}

function SizeTag({ size }: { size: string }) {
  const map: Record<string, string> = {
    소형: "bg-sky-50 text-sky-600",
    중형: "bg-indigo-50 text-indigo-600",
    대형: "bg-purple-50 text-purple-600",
  };
  return (
    <span className={`rounded-full px-3 py-1 text-[12px] font-medium ${map[size] ?? ""}`}>
      {size}
    </span>
  );
}

export default async function PostDetailPage({ params }: { params: { id: string } }) {
  const post = await getPost(Number(params.id));

  if (!post) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-[14px] text-gray-400">공고를 찾을 수 없습니다.</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="sticky top-0 z-10 flex items-center gap-3 border-b border-gray-100 bg-white/90 px-4 py-4 backdrop-blur-sm">
        <Link
          href="/dashboard"
          className="flex h-9 w-9 items-center justify-center rounded-xl text-gray-500 hover:bg-gray-100 transition-colors"
        >
          <ArrowLeft size={20} />
        </Link>
        <h2 className="flex-1 text-[17px] font-bold text-gray-900">공고 상세</h2>
        <div className="flex items-center gap-1">
          <Link
            href={`/dashboard/posts/${params.id}/edit`}
            className="flex h-9 w-9 items-center justify-center rounded-xl text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
            aria-label="공고 수정"
          >
            <Pencil size={17} />
          </Link>
          <button
            className="flex h-9 w-9 items-center justify-center rounded-xl text-gray-400 hover:bg-red-50 hover:text-red-500 transition-colors"
            aria-label="공고 삭제"
          >
            <Trash2 size={17} />
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-lg px-4 py-5 flex flex-col gap-4">

        {/* 사진 */}
        <div className="relative w-full aspect-[4/3] rounded-2xl overflow-hidden bg-gray-100">
          {post.animal.photoUrl ? (
            <Image
              src={post.animal.photoUrl}
              alt={post.animal.name}
              fill
              className="object-cover"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-gray-300 text-[40px]">
              🐾
            </div>
          )}
        </div>

        {/* 기본 정보 카드 */}
        <div className="rounded-2xl bg-white border border-gray-100 p-5">
          <div className="flex items-center gap-2 mb-3">
            {statusBadge(post.status)}
            <SizeTag size={post.animal.size} />
          </div>

          <h1 className="text-[22px] font-bold text-gray-900 mb-4">{post.animal.name}</h1>

          <div className="flex flex-col gap-3">
            <div className="flex items-start gap-3">
              <MapPin size={16} className="text-gray-400 mt-0.5 shrink-0" />
              <div className="flex flex-col gap-1 text-[14px] text-gray-700">
                <span>{post.origin}</span>
                <div className="flex justify-center w-full">
                  <ArrowDown size={13} className="text-gray-300" />
                </div>
                <span>{post.destination}</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Calendar size={16} className="text-gray-400 shrink-0" />
              <span className="text-[14px] text-gray-700">{post.scheduledDate}</span>
            </div>

            <div className="flex items-center gap-3">
              <Users size={16} className="text-gray-400 shrink-0" />
              <span className="text-[14px] text-gray-700">
                현재 지원 <span className="font-semibold text-gray-900">{post.volunteers.length}명</span>
              </span>
            </div>
          </div>
        </div>

        {/* 기타 참고 사항 */}
        {post.animal.notes && (
          <div className="rounded-2xl bg-white border border-gray-100 p-5">
            <p className="text-[12px] font-semibold text-gray-400 mb-2">기타 참고 사항</p>
            <p className="text-[14px] text-gray-700 leading-relaxed">{post.animal.notes}</p>
          </div>
        )}

        {/* 지원자 목록 */}
        {post.volunteers.length > 0 && (
          <div className="rounded-2xl bg-white border border-gray-100 p-5">
            <p className="text-[12px] font-semibold text-gray-400 mb-3">지원자 목록</p>
            <div className="flex flex-col gap-2.5">
              {post.volunteers.map((v) => (
                <div key={v.id} className="flex items-center gap-3 rounded-xl bg-gray-50 px-4 py-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-orange-100">
                    <span className="text-[12px] font-bold text-orange-600">{v.name[0]}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-semibold text-gray-800">{v.name}</p>
                    <div className="flex items-center gap-1 text-[11px] text-gray-400">
                      <span>{v.from}</span>
                      <ArrowRight size={10} />
                      <span>{v.to}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
