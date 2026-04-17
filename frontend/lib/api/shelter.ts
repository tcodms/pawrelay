import { request } from "@/lib/api";

export interface ShelterProfile {
  id: number;
  name: string;
  email: string;
  verified_at: string | null;
}

export async function getShelterProfile(): Promise<ShelterProfile> {
  return request<ShelterProfile>("/shelter/me");
}
