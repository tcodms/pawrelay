"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Calendar, MapPin, CheckCircle2, ChevronRight } from "lucide-react";
import VolunteerHeader from "@/components/VolunteerHeader";
import { getMySchedules } from "@/lib/api/chatbot";
import type { ScheduleItem } from "@/lib/api/chatbot";
import { request } from "@/lib/api";

interface MySegment {
  segment_id: number;
  status: string;
  animal_name: string;
  animal_photo_url: string | null;
  scheduled_date: string | null;
  pickup_location: string;
  dropoff_location: string;
  depart_time: string | null;
}

async function getMySegments(): Promise<MySegment[]> {
  const res = await request<{ segments: MySegment[] }>("/matching/my-segments");
  return res.segments;
}

const SIZE_LABEL: Record<string, string> = {
  small: "소형",
  medium: "중형",
  large: "대형",
};

const STATUS_LABEL: Record<string, { label: string; cls: string }> = {
  available: { label: "대기 중", cls: "bg-green-100 text-green-700" },
  matched:   { label: "매칭 완료", cls: "bg-[#FDF3EC] text-[#C17A3A]" },
  expired:   { label: "만료", cls: "bg-gray-100 text-gray-400" },
};

export default function MyPage() {
  const [schedules, setSchedules] = useState<ScheduleItem[]>([]);
  const [mySegments, setMySegments] = useState<MySegment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getMySchedules().catch(() => []),
      getMySegments().catch(() => []),
    ]).then(([s, segs]) => {
      setSchedules(s);
      setMySegments(segs);
    }).finally(() => setLoading(false));
  }, []);

  const applied = schedules.filter((s) => s.post_id !== null);
  const routes  = schedules.filter((s) => s.post_id === null);

  return (
    <main className="min-h-screen bg-gray-50">
      <VolunteerHeader title="나의 봉사" />

      {loading ? (
        <div className="flex justify-center pt-20">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#EEA968] border-t-transparent" />
        </div>
      ) : (
        <div className="mx-auto max-w-2xl px-4 pt-4 pb-24 space-y-6">

          {/* 매칭 제안 */}
          {mySegments.length > 0 && (
            <section>
              <h2 className="text-[13px] font-bold text-gray-400 mb-2.5 px-1">매칭 제안</h2>
              <div className="space-y-2.5">
                {mySegments.map((seg) => (
                  <Link
                    key={seg.segment_id}
                    href={`/volunteer/matching/${seg.segment_id}`}
                    className="flex items-center gap-3.5 rounded-2xl bg-white border border-[#EEA968]/30 shadow-sm px-4 py-3.5 active:scale-[0.98] transition-transform"
                  >
                    <div className="relative h-12 w-12 shrink-0 rounded-xl overflow-hidden bg-gray-100">
                      {seg.animal_photo_url ? (
                        <Image src={seg.animal_photo_url} alt={seg.animal_name} fill className="object-cover" />
                      ) : (
                        <div className="flex h-full items-center justify-center text-xl">🐾</div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[15px] font-bold text-gray-900">{seg.animal_name}</span>
                        <span className={`text-[11px] px-1.5 py-0.5 rounded-full font-semibold ${seg.status === "pending" ? "bg-orange-50 text-orange-500" : "bg-green-50 text-green-600"}`}>
                          {seg.status === "pending" ? "수락 대기 중" : "수락 완료"}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 text-[12px] text-gray-500">
                        <span>{seg.pickup_location}</span>
                        <ArrowRight size={10} className="text-gray-300 shrink-0" />
                        <span>{seg.dropoff_location}</span>
                      </div>
                      {seg.scheduled_date && (
                        <div className="flex items-center gap-1 text-[11px] text-gray-400 mt-0.5">
                          <Calendar size={10} />
                          <span>{seg.scheduled_date}{seg.depart_time && ` · ${seg.depart_time} 출발`}</span>
                        </div>
                      )}
                    </div>
                    <ChevronRight size={16} className="text-gray-300 shrink-0" />
                  </Link>
                ))}
              </div>
            </section>
          )}

          {/* 직접 지원한 공고 */}
          <section>
            <h2 className="text-[13px] font-bold text-gray-400 mb-2.5 px-1">직접 지원한 공고</h2>
            {applied.length === 0 ? (
              <div className="rounded-2xl bg-white border border-gray-100 px-5 py-8 text-center text-[13px] text-gray-400">
                직접 지원한 공고가 없어요.
              </div>
            ) : (
              <div className="space-y-2.5">
                {applied.map((s) => (
                  <div key={s.id} className="rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
                    <div className="flex gap-3.5 p-4">
                      {/* 동물 사진 */}
                      <div className="relative h-[60px] w-[60px] shrink-0 rounded-xl overflow-hidden bg-gray-100">
                        {s.applied_post?.animal_photo_url ? (
                          <Image
                            src={s.applied_post.animal_photo_url}
                            alt={s.applied_post.animal_name}
                            fill
                            className="object-cover"
                          />
                        ) : (
                          <div className="flex h-full items-center justify-center text-2xl">🐾</div>
                        )}
                      </div>

                      {/* 공고 정보 */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-[15px] font-bold text-gray-900">
                            {s.applied_post?.animal_name ?? "-"}
                          </span>
                          <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-500">
                            {SIZE_LABEL[s.applied_post?.animal_size ?? ""] ?? "-"}
                          </span>
                          <span className={`text-[11px] px-1.5 py-0.5 rounded-full font-medium ${STATUS_LABEL[s.status]?.cls ?? "bg-gray-100 text-gray-400"}`}>
                            {STATUS_LABEL[s.status]?.label ?? s.status}
                          </span>
                        </div>
                        <div className="flex items-center gap-1 text-[12px] text-gray-500 mb-1">
                          <MapPin size={11} className="text-[#EEA968] shrink-0" />
                          <span className="truncate">{s.applied_post?.origin}</span>
                          <ArrowRight size={10} className="shrink-0 text-gray-300" />
                          <span className="truncate">{s.applied_post?.destination}</span>
                        </div>
                        <div className="flex items-center gap-1 text-[12px] text-gray-400">
                          <Calendar size={11} className="shrink-0" />
                          <span>{s.available_date}</span>
                          {s.available_time && <span>· {s.available_time}</span>}
                        </div>
                      </div>
                    </div>

                    {/* 내 담당 구간 */}
                    <div className="border-t border-gray-100 px-4 py-2.5 flex items-center gap-1.5 text-[12px] text-gray-500">
                      <CheckCircle2 size={12} className="text-[#EEA968]" />
                      <span>내 구간:</span>
                      <span className="font-medium text-gray-700">{s.origin_area}</span>
                      <ArrowRight size={10} className="text-gray-300" />
                      <span className="font-medium text-gray-700">{s.destination_area}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* 독립 동선 */}
          <section>
            <h2 className="text-[13px] font-bold text-gray-400 mb-2.5 px-1">등록한 이동 동선</h2>
            {routes.length === 0 ? (
              <div className="rounded-2xl bg-white border border-gray-100 px-5 py-8 text-center text-[13px] text-gray-400">
                등록한 동선이 없어요.
              </div>
            ) : (
              <div className="space-y-2">
                {routes.map((s) => (
                  <div key={s.id} className="rounded-2xl bg-white border border-gray-100 shadow-sm px-4 py-3.5">
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-1.5 text-[14px] font-semibold text-gray-800">
                        <span>{s.origin_area}</span>
                        <ArrowRight size={12} className="text-gray-300" />
                        <span>{s.destination_area}</span>
                      </div>
                      <span className={`text-[11px] px-1.5 py-0.5 rounded-full font-medium ${STATUS_LABEL[s.status]?.cls ?? "bg-gray-100 text-gray-400"}`}>
                        {STATUS_LABEL[s.status]?.label ?? s.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-[12px] text-gray-400">
                      <span className="flex items-center gap-1">
                        <Calendar size={11} />
                        {s.available_date}
                        {s.available_time && ` · ${s.available_time}`}
                      </span>
                      <span className="px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-500">
                        {SIZE_LABEL[s.max_animal_size] ?? s.max_animal_size} 가능
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

        </div>
      )}
    </main>
  );
}
