const BASE_URL = "";

function getAuthHeaders(): Record<string, string> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export interface User {
  id: string;
  username: string;
  role: string;
  created_at: string;
  is_seed: boolean;
}

export interface CreateUserPayload {
  username: string;
  password: string;
  role: string;
}

export interface UpdateUserPayload {
  password?: string;
  role?: string;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    const msg = detail.detail || `HTTP ${res.status}`;
    console.error(`[Users] API error: ${msg}`);
    throw new Error(msg);
  }
  return res.json();
}

export async function fetchUsers(): Promise<User[]> {
  const res = await fetch(`${BASE_URL}/api/v1/users`, {
    headers: getAuthHeaders(),
    cache: "no-store",
  });
  return handleResponse<User[]>(res);
}

export async function createUser(
  payload: CreateUserPayload
): Promise<User> {
  const res = await fetch(`${BASE_URL}/api/v1/users`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  return handleResponse<User>(res);
}

export async function updateUser(
  id: string,
  payload: UpdateUserPayload
): Promise<User> {
  const res = await fetch(`${BASE_URL}/api/v1/users/${id}`, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  return handleResponse<User>(res);
}

export async function deleteUser(
  id: string
): Promise<{ status: string; message: string }> {
  const res = await fetch(`${BASE_URL}/api/v1/users/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  return handleResponse<{ status: string; message: string }>(res);
}
