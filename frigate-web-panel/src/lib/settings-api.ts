const BASE_URL = "";

export interface SettingsPayload {
  avalai_api_key: string;
  llm_model: string;
  telegram_enabled: boolean;
  telegram_bot_token: string;
  telegram_chat_id: string;
  bale_enabled: boolean;
  bale_bot_token: string;
  bale_chat_id: string;
  report_frequency: string;
  report_target: string;
}

export async function getSettings(): Promise<SettingsPayload> {
  const res = await fetch(`${BASE_URL}/api/v1/settings`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch settings: ${res.status}`);
  }
  return res.json();
}

export async function updateSettings(
  payload: SettingsPayload
): Promise<{ status: string; message: string }> {
  const res = await fetch(`${BASE_URL}/api/v1/settings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Failed to save settings: ${res.status}`);
  }
  return res.json();
}
