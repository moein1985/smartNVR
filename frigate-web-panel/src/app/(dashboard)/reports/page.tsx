"use client";

import Link from "next/link";
import { useReportRules, useTestReportRule, useUpdateReportRule } from "@/hooks/use-report-rules";

function Toggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors ${
        checked ? "bg-cyan-600" : "bg-gray-600"
      }`}
    >
      <span
        className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-lg transition-transform mt-0.5 ${
          checked ? "translate-x-4" : "translate-x-0.5"
        }`}
      />
    </button>
  );
}

export default function ReportsPage() {
  const { data: rules, isLoading, isError } = useReportRules();
  const testMutation = useTestReportRule();
  const updateMutation = useUpdateReportRule();

  const handleToggle = (id: string, enabled: boolean) => {
    updateMutation.mutate({ id, payload: { enabled: !enabled } });
  };

  const handleTest = (id: string) => {
    testMutation.mutate(id);
  };

  if (isLoading) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <div className="text-gray-500 text-sm">در حال بارگذاری...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <div className="text-red-400 text-sm">خطا در دریافت قوانین</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-200">قوانین گزارش</h1>
          <p className="text-sm text-gray-500 mt-1">مدیریت گزارش‌های خودکار</p>
        </div>
        <Link
          href="/reports/new"
          className="bg-cyan-600 hover:bg-cyan-700 text-white font-medium rounded-2xl px-5 py-2.5 text-sm transition-colors flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          ایجاد قانون
        </Link>
      </div>

      {(!rules || rules.length === 0) ? (
        <div className="bg-gray-800 rounded-3xl p-12 text-center">
          <p className="text-gray-500 text-sm">هنوز قانونی ایجاد نشده است</p>
          <Link
            href="/reports/new"
            className="inline-block mt-4 text-cyan-400 text-sm hover:text-cyan-300"
          >
            ایجاد اولین قانون گزارش
          </Link>
        </div>
      ) : (
        <div className="bg-gray-800 rounded-3xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700 text-gray-400">
                <th className="text-right px-4 py-3 font-medium">نام</th>
                <th className="text-right px-4 py-3 font-medium">مناطق</th>
                <th className="text-right px-4 py-3 font-medium">بازه</th>
                <th className="text-right px-4 py-3 font-medium">مقصد</th>
                <th className="text-center px-4 py-3 font-medium">فعال</th>
                <th className="text-right px-4 py-3 font-medium">آخرین اجرا</th>
                <th className="text-right px-4 py-3 font-medium">وضعیت</th>
                <th className="text-center px-4 py-3 font-medium">عملیات</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((rule) => (
                <tr
                  key={rule.id}
                  className="border-b border-gray-800 hover:bg-gray-750 transition-colors"
                >
                  <td className="px-4 py-3 text-gray-200 font-medium">
                    {rule.name}
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {rule.zones.length > 0
                      ? rule.zones.length === 1
                        ? rule.zones[0]
                        : `${rule.zones.length} منطقه`
                      : "—"}
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {rule.interval_hours} ساعت
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {rule.destination === "telegram" ? "تلگرام" : "بله"}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <Toggle
                      checked={rule.enabled}
                      onChange={() => handleToggle(rule.id, rule.enabled)}
                    />
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {rule.last_run
                      ? new Date(rule.last_run).toLocaleString("fa-IR")
                      : "—"}
                  </td>
                  <td className="px-4 py-3">
                    {rule.last_status === "success" && (
                      <span className="text-green-400 text-xs">موفق</span>
                    )}
                    {rule.last_status === "error" && (
                      <span className="text-red-400 text-xs">خطا</span>
                    )}
                    {rule.last_status === "send_failed" && (
                      <span className="text-yellow-400 text-xs">ارسال ناموفق</span>
                    )}
                    {!rule.last_status && (
                      <span className="text-gray-600 text-xs">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-2">
                      <Link
                        href={`/reports/${rule.id}`}
                        className="text-gray-400 hover:text-cyan-400 transition-colors"
                        title="ویرایش"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" />
                        </svg>
                      </Link>
                      <button
                        onClick={() => handleTest(rule.id)}
                        disabled={testMutation.isPending}
                        className="text-gray-400 hover:text-cyan-400 transition-colors disabled:opacity-50"
                        title="تست اجرا"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
                        </svg>
                      </button>
                      <Link
                        href={`/reports/${rule.id}/history`}
                        className="text-gray-400 hover:text-cyan-400 transition-colors"
                        title="تاریخچه"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
