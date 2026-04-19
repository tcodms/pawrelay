export type PostStatus = "recruiting" | "waiting" | "in_progress" | "completed";

export interface Volunteer {
  id: number;
  name: string;
  from: string;
  to: string;
}

export interface RelaySegment {
  volunteer: string;
  from: string;
  to: string;
  time: string;
}

export interface Post {
  id: number;
  chain_id?: number;
  chain_expires_at?: string;
  chain_status?: "pending_shelter" | "auto_approved";
  share_token?: string;
  animal_info: {
    name: string;
    size: "small" | "medium" | "large";
    photo_url?: string;
    notes?: string;
  };
  origin: string;
  destination: string;
  scheduled_date: string;
  status: PostStatus;
  volunteers: Volunteer[];
  volunteer_count?: number;
  relayChain?: RelaySegment[];
  matchingReason?: string;
}

export const URGENT_POST_IDS: number[] = [];

export const DUMMY_POSTS: Post[] = [
  {
    id: 1,
    animal_info: {
      name: "뽀삐",
      size: "medium",
      photo_url: "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400",
    },
    origin: "부산광역시 해운대구",
    destination: "대구광역시 수성구",
    scheduled_date: "2026-04-25",
    status: "recruiting",
    volunteers: [
      { id: 1, name: "최자원", from: "부산역", to: "밀양역" },
      { id: 2, name: "정봉사", from: "밀양역", to: "경산역" },
    ],
  },
  {
    id: 2,
    chain_id: 201,
    chain_expires_at: "2026-04-20T06:00:00Z",
    chain_status: "pending_shelter",
    animal_info: {
      name: "초코",
      size: "small",
      photo_url: "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400",
    },
    origin: "광주광역시 북구",
    destination: "서울특별시 강남구",
    scheduled_date: "2026-04-22",
    status: "waiting",
    volunteers: [
      { id: 3, name: "김봉사", from: "광주역", to: "천안역" },
      { id: 4, name: "이릴레이", from: "천안역", to: "서울 강남구" },
    ],
    relayChain: [
      { volunteer: "김봉사", from: "광주역", to: "천안역", time: "09:00" },
      { volunteer: "이릴레이", from: "천안역", to: "서울 강남구", time: "11:30" },
    ],
    matchingReason: "두 봉사자의 이동 경로가 천안역에서 연결되며, 인계 시간 간격이 충분히 확보됩니다.",
  },
  {
    id: 3,
    chain_id: 202,
    chain_expires_at: "2026-04-19T06:00:00Z",
    chain_status: "auto_approved",
    animal_info: {
      name: "나비",
      size: "small",
      photo_url: "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=400",
    },
    origin: "인천광역시 남동구",
    destination: "경기도 수원시",
    scheduled_date: "2026-04-21",
    status: "waiting",
    volunteers: [
      { id: 5, name: "홍길동", from: "인천터미널", to: "수원역" },
    ],
    relayChain: [
      { volunteer: "홍길동", from: "인천터미널", to: "수원역", time: "10:00" },
    ],
    matchingReason: "출발지와 도착지가 일치하며 단일 봉사자로 완전한 이동이 가능합니다.",
  },
  {
    id: 4,
    share_token: "abc123-dummy-token",
    animal_info: {
      name: "몽이",
      size: "medium",
      photo_url: "https://images.unsplash.com/photo-1518717758536-85ae29035b6d?w=400",
    },
    origin: "전라북도 전주시",
    destination: "경기도 고양시",
    scheduled_date: "2026-04-20",
    status: "in_progress",
    volunteers: [
      { id: 6, name: "황봉사", from: "전주역", to: "대전역" },
      { id: 7, name: "윤릴레이", from: "대전역", to: "고양시" },
    ],
    relayChain: [
      { volunteer: "황봉사", from: "전주역", to: "대전역", time: "08:30" },
      { volunteer: "윤릴레이", from: "대전역", to: "고양시", time: "11:00" },
    ],
  },
  {
    id: 5,
    animal_info: {
      name: "까미",
      size: "large",
      photo_url: "https://images.unsplash.com/photo-1477884213360-7e9d7dcc1e48?w=400",
    },
    origin: "대전광역시 유성구",
    destination: "서울특별시 송파구",
    scheduled_date: "2026-03-28",
    status: "completed",
    volunteers: [
      { id: 8, name: "신봉사", from: "대전역", to: "천안아산역" },
      { id: 9, name: "오릴레이", from: "천안아산역", to: "서울 송파구" },
    ],
  },
];
