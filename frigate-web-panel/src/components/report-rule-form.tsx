"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  useCreateReportRule,
  useUpdateReportRule,
  useDeleteReportRule,
  useFrigateZones,
  useCameras,
} from "@/hooks/use-report-rules";
import type { ReportRule } from "@/lib/report-rules-api";

const COMMON_LABELS = ["person", "car", "dog", "cat", "face"];

const INTERVAL_OPTIONS = [
  { value: 1, label: "۱ ساعت" },
  { value: 6, label: "۶ ساعت" },
  { value: 12, label: "۱۲ ساعت" },
  { value: 24, label: "۲۴ ساعت" },
];

const DESTINATION_OPTIONS = [
  { value: "telegram", label: "تلگرام" },
  { value: "bale", label: "بله" },
];

const inputClass =
  "w-full bg-gray-900 border border-gray-700 rounded-2xl px-4 py-2.5 text-gray-200 text-sm placeholder-gray-600 focus:outline-none focus:border-cyan-600 focus:ring-1 focus:ring-cyan-600 transition-colors";

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

function MultiSelect({
  options,
  selected,
  onChange,
  placeholder,
}: {
  options: string[];
  selected: string[];
  onChange: (vals: string[]) => void;
  placeholder: string;
}) {
  const [open, setOpen] = useState(false);

  const toggle = (val: string) => {
    if (selected.includes(val)) {
      onChange(selected.filter((v) => v !== val));
    } else {
      onChange([...selected, val]);
    }
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className={inputClass + " text-right flex items-center justify-between"}
      >
        <span className={selected.length === 0 ? "text-gray-600" : "text-gray-200"}>
          {selected.length === 0
            ? placeholder
            : `${selected.length} انتخاب شده`}
        </span>
        <svg
          className={`w-4 h-4 text-gray-500 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </button>
      {open && (
        <>
          <div
            className="fixed inset-0 z-30"
            onClick={() => setOpen(false)}
          />
          <div className="absolute z-40 mt-1 w-full bg-gray-900 border border-gray-700 rounded-2xl max-h-48 overflow-y-auto shadow-xl">
            {options.length === 0 ? (
              <div className="px-4 py-3 text-sm text-gray-600">
                گزینه‌ای موجود نیست
              </div>
            ) : (
              options.map((opt) => (
                <button
                  key={opt}
                  type="button"
                  onClick={() => toggle(opt)}
                  className={`w-full text-right px-4 py-2.5 text-sm transition-colors hover:bg-gray-800 ${
                    selected.includes(opt)
                      ? "text-cyan-400 bg-cyan-950/30"
                      : "text-gray-300"
                  }`}
                >
                  <span className="flex items-center gap-2">
                    {selected.includes(opt) && (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                    )}
                    {opt}
                  </span>
                </button>
              ))
            )}
          </div>
        </>
      )}
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

export function ReportRuleForm({ rule }: { rule?: ReportRule | null }) {
  const router = useRouter();
  const isEdit = !!rule;

  const [name, setName] = useState(rule?.name || "");
  const [enabled, setEnabled] = useState(rule?.enabled ?? true);
  const [zones, setZones] = useState<string[]>(rule?.zones || []);
  const [cameras, setCameras] = useState<string[]>(rule?.cameras || []);
  const [labels, setLabels] = useState<string[]>(rule?.labels || []);
  const [intervalHours, setIntervalHours] = useState(rule?.interval_hours || 24);
  const [destination, setDestination] = useState(rule?.destination || "telegram");
  const [chatId, setChatId] = useState(rule?.chat_id || "");
  const [promptTemplate, setPromptTemplate] = useState(rule?.prompt_template || "");
  const [includeSummary, setIncludeSummary] = useState(rule?.include_summary ?? true);
  const [includeRawData, setIncludeRawData] = useState(rule?.include_raw_data ?? false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [toast, setToast] = useState<"idle" | "success" | "error">("idle");

  const createMutation = useCreateReportRule();
  const updateMutation = useUpdateReportRule();
  const deleteMutation = useDeleteReportRule();
  const { data: availableZones = [] } = useFrigateZones();
  const { data: camerasData } = useCameras();
  const availableCameras = (camerasData?.cameras || []).map((c) => c.name);

  const handleSave = async () => {
    if (!name.trim()) {
      setToast("error");
      setTimeout(() => setToast("idle"), 3000);
      return;
    }
    setSaving(true);
    setToast("idle");
    try {
      const payload = {
        name: name.trim(),
        enabled,
        zones,
        cameras,
        labels,
        interval_hours: intervalHours,
        timezone: "Asia/Tehran",
        destination,
        chat_id: chatId,
        prompt_template: promptTemplate,
        include_summary: includeSummary,
        include_raw_data: includeRawData,
      };
      if (isEdit && rule) {
        await updateMutation.mutateAsync({ id: rule.id, payload });
      } else {
        await createMutation.mutateAsync(payload);
      }
      setToast("success");
      setTimeout(() => {
        router.push("/reports");
      }, 1000);
    } catch (err) {
      console.error("[ReportRules] Save failed:", err);
      setToast("error");
    } finally {
      setSaving(false);
      setTimeout(() => setToast("idle"), 3000);
    }
  };

  const handleDelete = async () => {
    if (!rule) return;
    if (!confirm(`حذف قانون «${rule.name}»؟`)) return;
    setDeleting(true);
    try {
      await deleteMutation.mutateAsync(rule.id);
      router.push("/reports");
    } catch (err) {
      console.error("[ReportRules] Delete failed:", err);
      setToast("error");
    } finally {
      setDeleting(false);
      setTimeout(() => setToast("idle"), 3000);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-200">
            {isEdit ? "ویرایش قانون گزارش" : "ایجاد قانون گزارش جدید"}
          </h1>
          <p className="text-sm text-gray-500 mt-1">پیکربندی گزارش خودکار</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-400">فعال</span>
          <Toggle checked={enabled} onChange={setEnabled} label="فعال" />
        </div>
      </div>

      <div className="bg-gray-800 rounded-3xl p-6 space-y-4">
        <Field label="نام قانون">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="گزارش روزانه مناطق کاری"
            className={inputClass}
          />
        </Field>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="مناطق (Zones)">
            <MultiSelect
              options={availableZones}
              selected={zones}
              onChange={setZones}
              placeholder="انتخاب مناطق از frigate.yml"
            />
          </Field>
          <Field label="دوربین‌ها">
            <MultiSelect
              options={availableCameras}
              selected={cameras}
              onChange={setCameras}
              placeholder="انتخاب دوربین‌ها"
            />
          </Field>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="برچسب‌ها (Labels)">
            <MultiSelect
              options={COMMON_LABELS}
              selected={labels}
              onChange={setLabels}
              placeholder="person, car, ..."
            />
          </Field>
          <Field label="بازه گزارش‌گیری">
            <select
              value={intervalHours}
              onChange={(e) => setIntervalHours(Number(e.target.value))}
              className={inputClass}
            >
              {INTERVAL_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </Field>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="مقصد ارسال">
            <select
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              className={inputClass}
            >
              {DESTINATION_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Chat ID (اختیاری)">
            <input
              type="text"
              value={chatId}
              onChange={(e) => setChatId(e.target.value)}
              placeholder="پیش‌فرض از تنظیمات"
              className={inputClass}
            />
          </Field>
        </div>
      </div>

      <div className="bg-gray-800 rounded-3xl p-6 space-y-4">
        <Field label="قالب پرامپت سفارشی (اختیاری)">
          <textarea
            value={promptTemplate}
            onChange={(e) => setPromptTemplate(e.target.value)}
            placeholder="خالی بگذارید تا پرامپت به‌صورت خودکار از مناطق و برچسب‌ها تولید شود..."
            rows={4}
            className={inputClass + " resize-none font-mono text-xs"}
          />
        </Field>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">درج خلاصه هوش مصنوعی</span>
            <Toggle checked={includeSummary} onChange={setIncludeSummary} label="خلاصه" />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">درج داده خام</span>
            <Toggle checked={includeRawData} onChange={setIncludeRawData} label="داده خام" />
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between pb-6">
        <div className="flex gap-3">
          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50 text-white font-medium rounded-2xl px-6 py-2.5 transition-colors"
          >
            {saving ? "در حال ذخیره..." : isEdit ? "به‌روزرسانی" : "ایجاد قانون"}
          </button>
          {isEdit && (
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="bg-red-900 hover:bg-red-800 disabled:opacity-50 text-red-200 font-medium rounded-2xl px-6 py-2.5 transition-colors"
            >
              {deleting ? "در حال حذف..." : "حذف"}
            </button>
          )}
        </div>

        {toast === "success" && (
          <span className="text-green-400 text-sm">با موفقیت ذخیره شد</span>
        )}
        {toast === "error" && (
          <span className="text-red-400 text-sm">خطا در عملیات</span>
        )}
      </div>
    </div>
  );
}
