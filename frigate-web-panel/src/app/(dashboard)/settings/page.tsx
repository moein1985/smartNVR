"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { getSettings, updateSettings, type SettingsPayload } from "@/lib/settings-api";

const LLM_MODELS = [
  "gemini-3.1-flash-lite",
  "gemini-2.5-flash",
  "gemini-2.5-pro",
  "gpt-4o-mini",
  "gpt-4o",
];

const REPORT_FREQUENCIES = [
  { value: "disabled", label: "غیرفعال" },
  { value: "daily_8am", label: "روزانه ساعت ۸ صبح" },
  { value: "daily_8pm", label: "روزانه ساعت ۸ شب" },
  { value: "weekly", label: "هفتگی (یکشنبه‌ها)" },
];

const REPORT_TARGETS = [
  { value: "telegram", label: "ارسال به تلگرام" },
  { value: "bale", label: "ارسال به بله" },
  { value: "both", label: "ارسال به هر دو" },
];

interface Settings {
  avalaiApiKey: string;
  llmModel: string;
  telegramEnabled: boolean;
  telegramBotToken: string;
  telegramChatId: string;
  baleEnabled: boolean;
  baleBotToken: string;
  baleChatId: string;
  reportFrequency: string;
  reportTarget: string;
}

const DEFAULT_SETTINGS: Settings = {
  avalaiApiKey: "",
  llmModel: "gemini-3.1-flash-lite",
  telegramEnabled: false,
  telegramBotToken: "",
  telegramChatId: "",
  baleEnabled: false,
  baleBotToken: "",
  baleChatId: "",
  reportFrequency: "disabled",
  reportTarget: "telegram",
};

function fromPayload(p: SettingsPayload): Settings {
  return {
    avalaiApiKey: p.avalai_api_key,
    llmModel: p.llm_model,
    telegramEnabled: p.telegram_enabled,
    telegramBotToken: p.telegram_bot_token,
    telegramChatId: p.telegram_chat_id,
    baleEnabled: p.bale_enabled,
    baleBotToken: p.bale_bot_token,
    baleChatId: p.bale_chat_id,
    reportFrequency: p.report_frequency,
    reportTarget: p.report_target,
  };
}

function toPayload(s: Settings): SettingsPayload {
  return {
    avalai_api_key: s.avalaiApiKey,
    llm_model: s.llmModel,
    telegram_enabled: s.telegramEnabled,
    telegram_bot_token: s.telegramBotToken,
    telegram_chat_id: s.telegramChatId,
    bale_enabled: s.baleEnabled,
    bale_bot_token: s.baleBotToken,
    bale_chat_id: s.baleChatId,
    report_frequency: s.reportFrequency,
    report_target: s.reportTarget,
  };
}

function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full transition-colors ${
        checked ? "bg-cyan-600" : "bg-gray-600"
      }`}
    >
      <span
        className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg transition-transform mt-0.5 ${
          checked ? "translate-x-5" : "translate-x-0.5"
        }`}
      />
      <span className="sr-only">{label}</span>
    </button>
  );
}

function SectionCard({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-gray-800 rounded-3xl p-6 space-y-4">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-2xl bg-gray-700 text-cyan-400">
          {icon}
        </div>
        <h2 className="text-lg font-semibold text-gray-200">{title}</h2>
      </div>
      {children}
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label className="block text-sm text-gray-400">{label}</label>
      {children}
    </div>
  );
}

const inputClass =
  "w-full bg-gray-900 border border-gray-700 rounded-2xl px-4 py-2.5 text-gray-200 text-sm placeholder-gray-600 focus:outline-none focus:border-cyan-600 focus:ring-1 focus:ring-cyan-600 transition-colors";

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
  const [loaded, setLoaded] = useState(false);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<"idle" | "success" | "error">("idle");

  useEffect(() => {
    let cancelled = false;
    getSettings()
      .then((data) => {
        if (!cancelled) {
          setSettings(fromPayload(data));
          setLoaded(true);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setLoaded(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const update = useCallback(
    <K extends keyof Settings>(key: K, value: Settings[K]) => {
      setSettings((prev) => ({ ...prev, [key]: value }));
    },
    []
  );

  const handleSave = async () => {
    setSaving(true);
    setToast("idle");
    try {
      await updateSettings(toPayload(settings));
      setToast("success");
    } catch {
      setToast("error");
    } finally {
      setSaving(false);
      setTimeout(() => setToast("idle"), 3000);
    }
  };

  if (!loaded) {
    return (
      <div className="p-6 space-y-6 max-w-4xl mx-auto">
        <div className="bg-gray-800 rounded-3xl p-6 space-y-4 animate-pulse">
          <div className="h-10 w-48 bg-gray-700 rounded-2xl" />
          <div className="h-12 w-full bg-gray-700 rounded-2xl" />
          <div className="h-12 w-full bg-gray-700 rounded-2xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-xl font-bold text-gray-200">تنظیمات سیستم</h1>
        <p className="text-sm text-gray-500 mt-1">پیکربندی پلتفرم</p>
      </div>

      <Link
        href="/settings/users"
        className="bg-gray-800 rounded-3xl p-5 flex items-center justify-between hover:bg-gray-750 transition-colors group"
      >
        <div className="flex items-center gap-4">
          <div className="flex items-center justify-center w-10 h-10 rounded-2xl bg-gray-700 text-cyan-400">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.243m15.94 2.655a4.125 4.125 0 00-8.048 0m15.94 2.655a4.125 4.125 0 00-8.048 0m15.94 2.655a4.125 4.125 0 00-8.048 0M3 4.984v15.5a.75.75 0 001.227.579L7.5 18.75l3.273 2.313A.75.75 0 0012 20.484V4.984a.75.75 0 00-.75-.75H3.75A.75.75 0 003 4.984z" />
            </svg>
          </div>
          <div>
            <h2 className="text-base font-semibold text-gray-200">مدیریت کاربران</h2>
            <p className="text-sm text-gray-500 mt-0.5">افزودن، ویرایش و حذف کاربران سیستم</p>
          </div>
        </div>
        <svg className="w-5 h-5 text-gray-600 group-hover:text-cyan-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
        </svg>
      </Link>

      {/* AI Configuration */}
      <SectionCard
        title="پیکربندی هوش مصنوعی"
        icon={
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
          </svg>
        }
      >
        <Field label="Avalai API Key">
          <input
            type="password"
            value={settings.avalaiApiKey}
            onChange={(e) => update("avalaiApiKey", e.target.value)}
            placeholder="avalai-xxxxxxxxxxxxx"
            className={inputClass}
          />
        </Field>
        <Field label="مدل LLM">
          <select
            value={settings.llmModel}
            onChange={(e) => update("llmModel", e.target.value)}
            className={inputClass}
          >
            {LLM_MODELS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </Field>
      </SectionCard>

      {/* Telegram Bot */}
      <SectionCard
        title="ربات تلگرام"
        icon={
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
          </svg>
        }
      >
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">فعال‌سازی ربات تلگرام</span>
          <Toggle
            checked={settings.telegramEnabled}
            onChange={(v) => update("telegramEnabled", v)}
            label="تلگرام"
          />
        </div>
        {settings.telegramEnabled && (
          <div className="space-y-4 pt-2 border-t border-gray-700">
            <Field label="Bot Token">
              <input
                type="password"
                value={settings.telegramBotToken}
                onChange={(e) => update("telegramBotToken", e.target.value)}
                placeholder="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
                className={inputClass}
              />
            </Field>
            <Field label="Target Chat ID">
              <input
                type="text"
                value={settings.telegramChatId}
                onChange={(e) => update("telegramChatId", e.target.value)}
                placeholder="-1001234567890"
                className={inputClass}
              />
            </Field>
          </div>
        )}
      </SectionCard>

      {/* Bale Bot */}
      <SectionCard
        title="ربات بله"
        icon={
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
          </svg>
        }
      >
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">فعال‌سازی ربات بله</span>
          <Toggle
            checked={settings.baleEnabled}
            onChange={(v) => update("baleEnabled", v)}
            label="بله"
          />
        </div>
        {settings.baleEnabled && (
          <div className="space-y-4 pt-2 border-t border-gray-700">
            <Field label="Bot Token">
              <input
                type="password"
                value={settings.baleBotToken}
                onChange={(e) => update("baleBotToken", e.target.value)}
                placeholder="bale-bot-token"
                className={inputClass}
              />
            </Field>
            <Field label="Target Chat ID">
              <input
                type="text"
                value={settings.baleChatId}
                onChange={(e) => update("baleChatId", e.target.value)}
                placeholder="chat-id"
                className={inputClass}
              />
            </Field>
          </div>
        )}
      </SectionCard>

      {/* Automated Reporting */}
      <SectionCard
        title="گزارش‌های خودکار (Cron)"
        icon={
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        }
      >
        <Field label="دوره گزارش‌گیری">
          <select
            value={settings.reportFrequency}
            onChange={(e) => update("reportFrequency", e.target.value)}
            className={inputClass}
          >
            {REPORT_FREQUENCIES.map((f) => (
              <option key={f.value} value={f.value}>
                {f.label}
              </option>
            ))}
          </select>
        </Field>
        {settings.reportFrequency !== "disabled" && (
          <Field label="مقصد ارسال گزارش">
            <select
              value={settings.reportTarget}
              onChange={(e) => update("reportTarget", e.target.value)}
              className={inputClass}
            >
              {REPORT_TARGETS.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </Field>
        )}
      </SectionCard>

      {/* Save Button + Toast */}
      <div className="flex items-center justify-between pb-6">
        <button
          onClick={handleSave}
          disabled={saving}
          className="bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-2xl px-6 py-2.5 transition-colors flex items-center gap-2"
        >
          {saving ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              در حال ذخیره...
            </>
          ) : (
            "ذخیره تنظیمات"
          )}
        </button>

        {toast === "success" && (
          <span className="text-green-400 text-sm flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            تنظیمات با موفقیت ذخیره شد
          </span>
        )}
        {toast === "error" && (
          <span className="text-red-400 text-sm flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
            خطا در ذخیره‌سازی
          </span>
        )}
      </div>
    </div>
  );
}
