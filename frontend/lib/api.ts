const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly code: string,
    public readonly status: number,
  ) {
    super(code);
    this.name = "ApiError";
  }
}

// Prevent concurrent refresh calls
let refreshPromise: Promise<void> | null = null;

async function refreshToken(): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) {
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new ApiError("REFRESH_TOKEN_EXPIRED", 401);
  }
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  // FormData일 때는 Content-Type을 직접 지정하지 않음 (브라우저가 boundary 포함하여 자동 설정)
  const isFormData = init.body instanceof FormData;
  const options: RequestInit = {
    ...init,
    credentials: "include",
    headers: isFormData
      ? { ...(init.headers ?? {}) }
      : { "Content-Type": "application/json", ...(init.headers ?? {}) },
  };

  const res = await fetch(`${API_BASE}${path}`, options);

  const isAuthEndpoint = path === "/auth/login" || path.startsWith("/auth/signup");

  if (res.status === 401 && !isAuthEndpoint) {
    // Deduplicate concurrent refresh calls
    if (!refreshPromise) {
      refreshPromise = refreshToken().finally(() => {
        refreshPromise = null;
      });
    }
    await refreshPromise;

    // Retry once after refresh
    const retryRes = await fetch(`${API_BASE}${path}`, options);
    if (!retryRes.ok) {
      const body = await retryRes.json().catch(() => ({}));
      throw new ApiError(body.error ?? "UNKNOWN_ERROR", retryRes.status);
    }
    return retryRes.json() as Promise<T>;
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(body.error ?? "UNKNOWN_ERROR", res.status);
  }

  if (res.status === 204) return undefined as unknown as T;
  return res.json() as Promise<T>;
}

// ── Types ──────────────────────────────────────────────────────────────────

export type UserRole = "volunteer" | "shelter" | "admin";

export interface User {
  id: number;
  email: string;
  role: UserRole;
  name: string;
}

export interface LoginResponse {
  user: User;
}

export type AnimalSize = "small" | "medium" | "large";

export interface SignupVolunteerRequest {
  email: string;
  password: string;
  name: string;
  vehicle_available: boolean;
  max_animal_size: AnimalSize;
  activity_regions: string[];
}

export interface SignupShelterRequest {
  email: string;
  password: string;
  name: string;
  phone: string;
  contact_email: string;
  address: string;
  shelter_registration_doc_url: string | null;
}

export interface SignupShelterResponse {
  user: User;
}

// ── Auth API ───────────────────────────────────────────────────────────────

export async function login(
  email: string,
  password: string,
): Promise<LoginResponse> {
  return request<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function signupVolunteer(
  data: SignupVolunteerRequest,
): Promise<LoginResponse> {
  return request<LoginResponse>("/auth/signup/volunteer", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function signupShelter(
  data: SignupShelterRequest,
): Promise<SignupShelterResponse> {
  return request<SignupShelterResponse>("/auth/signup/shelter", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function logout(): Promise<void> {
  await request<{ ok: boolean }>("/auth/logout", { method: "POST" });
}

export async function getMe(): Promise<User> {
  return request<User>("/auth/me");
}
