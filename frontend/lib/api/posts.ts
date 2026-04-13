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
  status: string;
}

export interface PhotoUploadUrl {
  upload_url: string;
  photo_url: string;
}

// ── API 함수 ──────────────────────────────────────────────────────────────────

export async function getPosts(_query?: PostsQuery): Promise<Post[]> {
  // TODO: const params = new URLSearchParams({ ...(_query ?? {}) } as Record<string, string>);
  //       const res = await request<{ posts: Post[] }>(`/posts?${params}`);
  //       return res.posts;
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
