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
  chain_id?: number;   // relay_chains.id — waiting 상태에서 승인/거절 시 필요
  share_token?: string;
  animal: {
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
  relayChain?: RelaySegment[];
  matchingReason?: string;
}

export const DUMMY_POSTS: Post[] = [
  {
    id: 1,
    chain_id: 101,
    animal: {
      name: "초코",
      size: "small",
      photo_url: "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400",
      notes: "겁이 많아 조용한 이동이 필요합니다. 낯선 사람에게 짖을 수 있어요.",
    },
    origin: "광주광역시 북구",
    destination: "서울특별시 강남구",
    scheduled_date: "2026-04-10",
    status: "waiting",
    volunteers: [
      { id: 1, name: "김봉사", from: "광주역", to: "천안역" },
      { id: 2, name: "이릴레이", from: "천안역", to: "수원역" },
      { id: 3, name: "박도움", from: "수원역", to: "서울 강남구" },
    ],
    relayChain: [
      { volunteer: "김봉사", from: "광주역", to: "천안역", time: "09:00" },
      { volunteer: "이릴레이", from: "천안역", to: "수원역", time: "11:30" },
      { volunteer: "박도움", from: "수원역", to: "서울 강남구", time: "13:00" },
    ],
    matchingReason: "세 분의 이동 경로가 완벽하게 연결되며, 인계 시간 간격이 모두 30분 이상 확보됩니다.",
  },
  {
    id: 2,
    animal: {
      name: "뽀삐",
      size: "medium",
      photo_url: "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400",
      notes: "차량 이동에 익숙합니다. 간식을 좋아하며 순합니다.",
    },
    origin: "부산광역시 해운대구",
    destination: "대구광역시 수성구",
    scheduled_date: "2026-04-12",
    status: "recruiting",
    volunteers: [
      { id: 4, name: "최자원", from: "부산역", to: "밀양역" },
      { id: 5, name: "정봉사", from: "밀양역", to: "경산역" },
    ],
  },
  {
    id: 3,
    animal: {
      name: "나비",
      size: "small",
      photo_url: "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=400",
      notes: "이동장에 가두면 스트레스를 받습니다. 가능하면 넓은 공간 확보 부탁드립니다.",
    },
    origin: "인천광역시 남동구",
    destination: "경기도 수원시",
    scheduled_date: "2026-04-08",
    status: "recruiting",
    volunteers: [
      { id: 6, name: "홍길동", from: "인천터미널", to: "수원역" },
    ],
  },
  {
    id: 4,
    animal: {
      name: "까미",
      size: "large",
      photo_url: "https://images.unsplash.com/photo-1477884213360-7e9d7dcc1e48?w=400",
      notes: "대형견이므로 충분한 차량 공간이 필요합니다.",
    },
    origin: "대전광역시 유성구",
    destination: "서울특별시 송파구",
    scheduled_date: "2026-03-28",
    status: "completed",
    volunteers: [
      { id: 7, name: "신봉사", from: "대전역", to: "천안아산역" },
      { id: 8, name: "오릴레이", from: "천안아산역", to: "서울 송파구" },
    ],
  },
  {
    id: 5,
    chain_id: 102,
    animal: {
      name: "흰둥이",
      size: "small",
      photo_url: "https://images.unsplash.com/photo-1574144611937-0df059b5ef3e?w=400",
      notes: "특이사항 없음. 건강하고 활발한 성격입니다.",
    },
    origin: "광주광역시 동구",
    destination: "경기도 성남시",
    scheduled_date: "2026-04-15",
    status: "waiting",
    volunteers: [
      { id: 9, name: "강자원", from: "광주송정역", to: "오송역" },
      { id: 10, name: "배봉사", from: "오송역", to: "경기 성남" },
    ],
    relayChain: [
      { volunteer: "강자원", from: "광주송정역", to: "오송역", time: "10:00" },
      { volunteer: "배봉사", from: "오송역", to: "경기 성남", time: "12:00" },
    ],
    matchingReason: "두 봉사자의 경로가 오송역에서 연결되며, 이동 시간과 인계 여유 시간이 최적화되어 있습니다.",
  },
  {
    id: 7,
    share_token: "abc123-dummy-token",
    animal: {
      name: "몽이",
      size: "medium",
      photo_url: "https://images.unsplash.com/photo-1518717758536-85ae29035b6d?w=400",
      notes: "온순하고 차량 이동에 익숙합니다.",
    },
    origin: "전라북도 전주시",
    destination: "경기도 고양시",
    scheduled_date: "2026-04-16",
    status: "in_progress",
    volunteers: [
      { id: 14, name: "황봉사", from: "전주역", to: "대전역" },
      { id: 15, name: "윤릴레이", from: "대전역", to: "수원역" },
      { id: 16, name: "장도움", from: "수원역", to: "고양시" },
    ],
    relayChain: [
      { volunteer: "황봉사", from: "전주역", to: "대전역", time: "08:30" },
      { volunteer: "윤릴레이", from: "대전역", to: "수원역", time: "11:00" },
      { volunteer: "장도움", from: "수원역", to: "고양시", time: "13:30" },
    ],
    matchingReason: "세 봉사자의 이동 경로가 매끄럽게 연결되며, 인계 여유 시간이 충분합니다.",
  },
  {
    id: 6,
    animal: {
      name: "루시",
      size: "medium",
      photo_url: "https://images.unsplash.com/photo-1537151625747-768eb6cf92b2?w=400",
      notes: "사람을 잘 따르며 다른 동물과도 잘 지냅니다.",
    },
    origin: "대구광역시 달서구",
    destination: "충청북도 청주시",
    scheduled_date: "2026-04-20",
    status: "recruiting",
    volunteers: [
      { id: 11, name: "임자원", from: "대구역", to: "김천구미역" },
      { id: 12, name: "한봉사", from: "김천구미역", to: "오송역" },
      { id: 13, name: "조릴레이", from: "오송역", to: "청주" },
    ],
  },
];
