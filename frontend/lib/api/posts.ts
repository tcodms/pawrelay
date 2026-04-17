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
import { DUMMY_POSTS } from "@/lib/dummy-posts";
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

export async function getPosts(): Promise<Post[]> {
  // TODO: const res = await request<{ posts: Post[] }>("/shelter/dashboard");
  //       return res.posts;
  //
  // 주의: GET /shelter/dashboard 응답에 animal_info, chain_id, share_token 등이
  //       누락되어 있음 → 백엔드에 필드 추가 요청 필요. (api-spec.md 스펙 갭)
  //       지역/날짜/크기 필터(region, date, animal_size)는 GET /posts 파라미터이며
  //       보호소 대시보드에는 해당 없음.
  return DUMMY_POSTS;
}

export async function getPost(id: number): Promise<Post | null> {
  // TODO: return request<Post>(`/posts/${id}`).catch(() => null);
  return DUMMY_POSTS.find((p) => p.id === id) ?? null;
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
