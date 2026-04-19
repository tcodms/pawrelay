/**
 * 공고(Transport Posts) 관련 API 함수
 * 더미 데이터 기반으로 동작 중. TODO 위치에서 실제 API로 교체합니다.
 *
 * api-spec.md 참고:
 *   GET    /posts            공고 목록
 *   GET    /posts/{id}       공고 상세
 *   POST   /posts            공고 등록
 *   PUT    /posts/{id}       공고 수정
 *   GET    /posts/upload-url 사진 업로드 Presigned URL
 */
import { request } from "@/lib/api";
import type { Post, PostStatus } from "@/lib/dummy-posts";

export type { Post, PostStatus };

// ── Query / Request 타입 ──────────────────────────────────────────────────────

// PostsQuery (region, date, animal_size 등)는 GET /posts (봉사자용 공개 목록) 전용.
// 보호소 대시보드는 GET /shelter/dashboard 를 파라미터 없이 호출함.
export interface PostsQuery {
  region?: string;
  date?: string;
  animal_size?: "small" | "medium" | "large";
  page?: number;
  limit?: number;
}

export interface CreatePostData {
  origin: string;
  destination: string;
  scheduled_date: string;
  animal_info: {
    name: string;
    size: "small" | "medium" | "large";
    photo_url?: string;
    notes?: string;
  };
}

export interface CreatePostResponse {
  id: number;
  share_token: string;
  status: PostStatus;
}

export interface PhotoUploadUrl {
  upload_url: string;
  photo_url: string;
}

// ── API 함수 ──────────────────────────────────────────────────────────────────

interface DashboardPostItem {
  id: number;
  origin: string;
  destination: string;
  scheduled_date: string;
  status: PostStatus;
  volunteer_count: number;
  animal_info: { name: string; size: "small" | "medium" | "large"; photo_url: string | null };
  chain_id: number | null;
  share_token: string;
}

export interface VolunteerPost {
  id: number;
  origin: string;
  destination: string;
  scheduled_date: string;
  animal_size: "small" | "medium" | "large";
  status: string;
  animal_photo_url: string | null;
}

export interface VolunteerPostsResponse {
  posts: VolunteerPost[];
  total: number;
  page: number;
  limit: number;
}

export async function getVolunteerPosts(query: PostsQuery): Promise<VolunteerPostsResponse> {
  const params = new URLSearchParams();
  if (query.region) params.set("region", query.region);
  if (query.date) params.set("date", query.date);
  if (query.animal_size) params.set("animal_size", query.animal_size);
  params.set("page", String(query.page ?? 1));
  params.set("limit", String(query.limit ?? 20));
  return request<VolunteerPostsResponse>(`/posts?${params.toString()}`);
}

export async function getPosts(): Promise<Post[]> {
  const res = await request<{ posts: DashboardPostItem[] }>("/shelter/dashboard");
  return res.posts.map((item) => ({
    id: item.id,
    origin: item.origin,
    destination: item.destination,
    scheduled_date: item.scheduled_date,
    status: item.status,
    animal_info: {
      name: item.animal_info.name,
      size: item.animal_info.size,
      photo_url: item.animal_info.photo_url ?? undefined,
    },
    volunteers: Array(item.volunteer_count).fill({ id: 0, name: "", from: "", to: "" }),
    chain_id: item.chain_id ?? undefined,
    share_token: item.share_token,
  }));
}

interface PostDetailItem {
  id: number;
  origin: string;
  destination: string;
  scheduled_date: string;
  status: PostStatus;
  animal_info: { name: string; size: "small" | "medium" | "large"; photo_url: string | null; notes: string | null };
  volunteers?: { id: number; name: string; from_area: string; to_area: string }[];
  volunteer_count?: number;
}

export async function getPost(id: number): Promise<Post | null> {
  return request<PostDetailItem>(`/posts/${id}`)
    .then((item) => ({
      id: item.id,
      origin: item.origin,
      destination: item.destination,
      scheduled_date: item.scheduled_date,
      status: item.status,
      animal_info: {
        name: item.animal_info.name,
        size: item.animal_info.size,
        photo_url: item.animal_info.photo_url ?? undefined,
        notes: item.animal_info.notes ?? undefined,
      },
      volunteers: item.volunteers?.map((v) => ({ id: v.id, name: v.name, from: v.from_area, to: v.to_area })) ?? [],
      volunteer_count: item.volunteer_count,
    }))
    .catch(() => null);
}

export async function createPost(data: CreatePostData): Promise<CreatePostResponse> {
  return request<CreatePostResponse>("/posts", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updatePost(id: number, data: Partial<CreatePostData>): Promise<void> {
  await request<{ ok: boolean }>(`/posts/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deletePost(id: number): Promise<void> {
  await request<{ ok: boolean }>(`/posts/${id}`, { method: "DELETE" });
}

export async function getPhotoUploadUrl(filename: string): Promise<PhotoUploadUrl> {
  return request<PhotoUploadUrl>(
    `/posts/upload-url?filename=${encodeURIComponent(filename)}`
  );
}
