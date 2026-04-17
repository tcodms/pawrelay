"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { ArrowLeft, ArrowRight, Calendar, MapPin, Pencil, Trash2, Users } from "lucide-react";
import { getPost, deletePost } from "@/lib/api/posts";
import type { Post } from "@/lib/api/posts";
import { StatusBadge, SizeBadge } from "@/components/ui/PostBadges";

export default function PostDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPost(Number(params.id))
      .then(setPost)
      .finally(() => setLoading(false));
  }, [params.id]);

  async function handleDelete() {
    if (!post) return;
    if (!confirm(`"${post.animal_info.name}" 공고를 삭제할까요?`)) return;
    try {
      await deletePost(post.id);
      router.push("/dashboard");
    } catch {
      alert("공고 삭제에 실패했습니다. 다시 시도해 주세요.");
    }
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#EEA968] border-t-transparent" />
      </main>
    );
  }

  if (!post) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50">
        <p className="text-[14px] text-gray-400">공고를 찾을 수 없습니다.</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-100">
      <div className="mx-auto max-w-lg">

        {/* ── 동물 사진 영역 ── */}
        <div className="relative w-full h-[50vh] min-h-[260px] max-h-[420px] bg-[#FDF3EC]">

          {/* 뒤로가기 버튼 */}
          <Link
            href="/dashboard"
            aria-label="목록으로 돌아가기"
            className="absolute top-5 left-4 z-10 flex h-9 w-9 items-center justify-center rounded-full bg-white/80 backdrop-blur-sm text-gray-700 shadow-sm hover:bg-white transition-colors"
          >
            <ArrowLeft size={20} />
          </Link>

          {/* 수정 / 삭제 버튼 */}
          <div className="absolute top-5 right-4 z-10 flex gap-2">
            <Link
              href={`/dashboard/posts/${params.id}/edit`}
              aria-label="공고 수정"
              className="flex h-9 w-9 items-center justify-center rounded-full bg-white/80 backdrop-blur-sm text-gray-600 shadow-sm hover:bg-white transition-colors"
            >
              <Pencil size={16} />
            </Link>
            <button
              onClick={handleDelete}
              aria-label="공고 삭제"
              className="flex h-9 w-9 items-center justify-center rounded-full bg-white/80 backdrop-blur-sm text-gray-600 shadow-sm hover:bg-red-50 hover:text-red-500 transition-colors"
            >
              <Trash2 size={16} />
            </button>
          </div>

          {/* 사진 or 플레이스홀더 */}
          {post.animal_info.photo_url ? (
            <Image
              src={post.animal_info.photo_url}
              alt={post.animal_info.name}
              fill
              className="object-cover"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-[64px]">
              🐾
            </div>
          )}
        </div>

        {/* ── 바텀시트 스타일 상세정보 ── */}
        <div className="-mt-6 relative z-10 rounded-t-3xl bg-white px-5 pt-4 pb-28 min-h-[60vh]">

          {/* 드래그 핸들 */}
          <div className="flex justify-center mb-5">
            <div className="h-1 w-10 rounded-full bg-gray-200" />
          </div>

          {/* 상태 배지 */}
          <div className="flex items-center gap-2 mb-3">
            <StatusBadge status={post.status} />
            <SizeBadge size={post.animal_info.size} />
          </div>

          {/* 동물 이름 */}
          <h1 className="text-[24px] font-bold text-gray-900 mb-5">{post.animal_info.name}</h1>

          {/* 이동 경로 */}
          <div className="flex items-center gap-2 mb-3">
            <MapPin size={15} className="text-[#EEA968] shrink-0" />
            <div className="flex items-center gap-1.5 text-[14px] text-gray-700">
              <span>{post.origin}</span>
              <ArrowRight size={13} className="text-gray-300 shrink-0" />
              <span>{post.destination}</span>
            </div>
          </div>

          {/* 이송 날짜 */}
          <div className="flex items-center gap-2 mb-3">
            <Calendar size={15} className="text-[#EEA968] shrink-0" />
            <span className="text-[14px] text-gray-700">{post.scheduled_date}</span>
          </div>

          {/* 지원자 수 */}
          <div className="flex items-center gap-2 mb-5">
            <Users size={15} className="text-[#EEA968] shrink-0" />
            <span className="text-[14px] text-gray-700">
              현재 지원{" "}
              <span className="font-semibold text-gray-900">{post.volunteers.length}명</span>
            </span>
          </div>

          {/* 구분선 */}
          <div className="h-px bg-gray-100 mb-5" />

          {/* 기타 참고 사항 */}
          {post.animal_info.notes && (
            <div className="mb-5">
              <p className="text-[12px] font-semibold text-gray-400 mb-2">기타 참고 사항</p>
              <p className="text-[14px] text-gray-700 leading-relaxed">{post.animal_info.notes}</p>
            </div>
          )}

          {/* 지원자 목록 */}
          {post.volunteers.length > 0 && (
            <div>
              <p className="text-[12px] font-semibold text-gray-400 mb-3">지원자 목록</p>
              <div className="flex flex-col gap-2.5">
                {post.volunteers.map((v) => (
                  <div key={v.id} className="flex items-center gap-3 rounded-2xl bg-gray-50 px-4 py-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#FDF3EC]">
                      <span className="text-[12px] font-bold text-[#7A4A28]">{v.name[0]}</span>
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

      </div>
    </main>
  );
}
