"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { ArrowLeft, ArrowRight, Calendar, MapPin, Users } from "lucide-react";
import { getPost } from "@/lib/api/posts";
import type { Post } from "@/lib/api/posts";
import { StatusBadge, SizeBadge } from "@/components/ui/PostBadges";
import { CHATBOT_SESSION_KEY, CHATBOT_POST_CONTEXT_KEY } from "@/lib/api/chatbot";
import type { PostContext } from "@/lib/api/chatbot";

export default function VolunteerPostDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    getPost(Number(params.id))
      .then(setPost)
      .finally(() => setLoading(false));
  }, [params.id]);

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

        {/* 동물 사진 영역 */}
        <div className="relative w-full h-[50vh] min-h-[260px] max-h-[420px] bg-[#FDF3EC]">

          {/* 뒤로가기 버튼 */}
          <button
            onClick={() => router.back()}
            aria-label="뒤로 가기"
            className="absolute top-5 left-4 z-10 flex h-9 w-9 items-center justify-center rounded-full bg-white/80 backdrop-blur-sm text-gray-700 shadow-sm hover:bg-white transition-colors"
          >
            <ArrowLeft size={20} />
          </button>

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

        {/* 바텀시트 스타일 상세정보 */}
        <div className="-mt-6 relative z-10 rounded-t-3xl bg-white px-5 pt-4 pb-36 min-h-[60vh]">

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

        </div>

      </div>

      {/* 신청 버튼 (하단 고정 — BottomNav h-16 위에 배치) */}
      <div className="fixed bottom-16 left-0 right-0 z-20 px-4 pb-3 pt-3">
        <div className="mx-auto max-w-lg">
          {post.status === "recruiting" ? (
            <button
              onClick={() => {
                const sessionId = crypto.randomUUID();
                const postContext: PostContext = {
                  post_id: post.id,
                  destination: post.destination,
                  available_date: post.scheduled_date,
                  max_animal_size: post.animal_info.size,
                };
                sessionStorage.setItem(CHATBOT_SESSION_KEY, sessionId);
                sessionStorage.setItem(CHATBOT_POST_CONTEXT_KEY, JSON.stringify(postContext));
                router.push(`/volunteer/chat/${sessionId}`);
              }}
              className="flex w-full items-center justify-center h-14 rounded-full bg-[#EEA968] text-[15px] font-bold text-white shadow-md shadow-[#EEA968]/20 transition-all active:scale-[0.97] hover:bg-[#D99A55]"
            >
              이 공고 신청하기
            </button>
          ) : (
            <div className="flex w-full items-center justify-center h-14 rounded-full bg-gray-100 text-[15px] font-bold text-gray-400">
              신청이 마감된 공고입니다
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
