const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

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

export interface ReportRule {
  id: string;
  name: string;
  enabled: boolean;
  zones: string[];
  cameras: string[];
  labels: string[];
  interval_hours: number;
  timezone: string;
  destination: string;
  chat_id: string;
  prompt_template: string;
  include_summary: boolean;
  include_raw_data: boolean;
  created_at: string;
  last_run: string;
  last_status: string;
}

export interface CreateReportRulePayload {
  name: string;
  enabled?: boolean;
  zones?: string[];
  cameras?: string[];
  labels?: string[];
  interval_hours?: number;
  timezone?: string;
  destination?: string;
  chat_id?: string;
  prompt_template?: string;
  include_summary?: boolean;
  include_raw_data?: boolean;
}

export interface UpdateReportRulePayload {
  name?: string;
  enabled?: boolean;
  zones?: string[];
  cameras?: string[];
  labels?: string[];
  interval_hours?: number;
  timezone?: string;
  destination?: string;
  chat_id?: string;
  prompt_template?: string;
  include_summary?: boolean;
  include_raw_data?: boolean;
}

export interface HistoryEntry {
  id: string;
  rule_id: string;
  rule_name: string;
  executed_at: string;
  status: string;
  message_preview: string;
  destination: string;
}

export interface FrigateConfig {
  cameras: Record<
    string,
    {
      enabled: boolean;
      zones: Record<string, unknown>;
    }
  >;
}

export interface CameraInfo {
  name: string;
  enabled: boolean;
  zones: string[];
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    const msg = detail.detail || `HTTP ${res.status}`;
    console.error(`[ReportRules] API error: ${msg}`);
    throw new Error(msg);
  }
  return res.json();
}

export async function fetchReportRules(): Promise<ReportRule[]> {
  const res = await fetch(`${BASE_URL}/api/v1/report-rules`, {
    headers: getAuthHeaders(),
    cache: "no-store",
  });
  return handleResponse<ReportRule[]>(res);
}

export async function fetchReportRule(id: string): Promise<ReportRule> {
  const res = await fetch(`${BASE_URL}/api/v1/report-rules/${id}`, {
    headers: getAuthHeaders(),
    cache: "no-store",
  });
  return handleResponse<ReportRule>(res);
}

export async function createReportRule(
  payload: CreateReportRulePayload
): Promise<ReportRule> {
  const res = await fetch(`${BASE_URL}/api/v1/report-rules`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  return handleResponse<ReportRule>(res);
}

export async function updateReportRule(
  id: string,
  payload: UpdateReportRulePayload
): Promise<ReportRule> {
  const res = await fetch(`${BASE_URL}/api/v1/report-rules/${id}`, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  return handleResponse<ReportRule>(res);
}

export async function deleteReportRule(
  id: string
): Promise<{ status: string; message: string }> {
  const res = await fetch(`${BASE_URL}/api/v1/report-rules/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  return handleResponse<{ status: string; message: string }>(res);
}

export async function testReportRule(
  id: string
): Promise<{ status: string; message: string }> {
  const res = await fetch(`${BASE_URL}/api/v1/report-rules/${id}/test`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  return handleResponse<{ status: string; message: string }>(res);
}

export async function fetchRuleHistory(
  id: string
): Promise<HistoryEntry[]> {
  const res = await fetch(`${BASE_URL}/api/v1/report-rules/${id}/history`, {
    headers: getAuthHeaders(),
    cache: "no-store",
  });
  return handleResponse<HistoryEntry[]>(res);
}

export async function fetchAllHistory(): Promise<HistoryEntry[]> {
  const res = await fetch(`${BASE_URL}/api/v1/report-rules/history/all`, {
    headers: getAuthHeaders(),
    cache: "no-store",
  });
  return handleResponse<HistoryEntry[]>(res);
}

export async function fetchFrigateConfig(): Promise<FrigateConfig> {
  const res = await fetch(`${BASE_URL}/api/v1/system/frigate-config`, {
    headers: getAuthHeaders(),
    cache: "no-store",
  });
  return handleResponse<FrigateConfig>(res);
}

export async function fetchCameras(): Promise<{
  cameras: CameraInfo[];
  total: number;
}> {
  const res = await fetch(`${BASE_URL}/api/v1/cameras`, {
    headers: getAuthHeaders(),
    cache: "no-store",
  });
  return handleResponse<{ cameras: CameraInfo[]; total: number }>(res);
}

export function parseZonesFromConfig(config: FrigateConfig): string[] {
  const zones = new Set<string>();
  for (const cam of Object.values(config.cameras || {})) {
    for (const zoneKey of Object.keys(cam.zones || {})) {
      zones.add(zoneKey);
    }
  }
  return Array.from(zones).sort();
}
