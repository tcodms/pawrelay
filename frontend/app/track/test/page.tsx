"use client";

import { TrackContent } from "@/app/track/[token]/page";
import type { PublicPost, PublicPostCheckpoint } from "@/lib/api/posts";

const DUMMY_POST: PublicPost = {
  animal_info: {
    name: "초코",
    size: "small",
    photo_url: "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=200",
  },
  origin: "광주광역시 북구",
  destination: "서울특별시 마포구",
  scheduled_date: "2026-05-15",
  current_segment: null,
  checkpoints: [],
  timeline: [
    { segment_order: 1, completed_at: "2026-05-15T09:30:00Z" },
    { segment_order: 2, completed_at: "2026-05-15T13:00:00Z" },
  ],
};

const DUMMY_CHECKPOINTS: PublicPostCheckpoint[] = [
  { latitude: 35.1595, longitude: 126.8526, recorded_at: "2026-05-15T08:00:00Z" },
  { latitude: 35.2800, longitude: 127.0500, recorded_at: "2026-05-15T09:30:00Z" },
  { latitude: 36.3500, longitude: 127.3800, recorded_at: "2026-05-15T11:00:00Z" },
];

export default function TrackTestPage() {
  if (process.env.NODE_ENV === "production") return null;
  return <TrackContent post={DUMMY_POST} checkpoints={DUMMY_CHECKPOINTS} />;
}
