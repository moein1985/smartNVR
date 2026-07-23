const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export interface AuthUser {
  id: string;
  username: string;
  role: string;
  created_at: string;
  is_seed: boolean;
}

export interface LoginResponse {
  token: string;
  username: string;
  role: string;
}

export async function login(
  username: string,
  password: string
): Promise<LoginResponse> {
  const res = await fetch(`${BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || "Invalid username or password");
  }
  return res.json();
}

export async function getMe(token: string): Promise<AuthUser> {
  const res = await fetch(`${BASE_URL}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error("Failed to fetch user info");
  }
  return res.json();
}
