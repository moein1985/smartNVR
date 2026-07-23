"use client";

import { useParams, useRouter } from "next/navigation";
import { useRuleHistory } from "@/hooks/use-report-rules";

export default function RuleHistoryPage() {
  const params = useParams();
  const router = useRouter();
  const ruleId = params.id as string;
  const { data: entries, isLoading, isError } = useRuleHistory(ruleId);

  if (isLoading) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="text-gray-500 text-sm">در حال بارگذاری تاریخچه...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="text-red-400 text-sm">خطا در دریافت تاریخچه</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.push("/reports")}
          className="text-gray-400 hover:text-cyan-400 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
        </button>
        <div>
          <h1 className="text-xl font-bold text-gray-200">تاریخچه اجرا</h1>
          <p className="text-sm text-gray-500 mt-1">آخرین ۱۰۰ اجرای این قانون</p>
        </div>
      </div>

      {(!entries || entries.length === 0) ? (
        <div className="bg-gray-800 rounded-3xl p-12 text-center">
          <p className="text-gray-500 text-sm">هیچ اجرایی ثبت نشده است</p>
        </div>
      ) : (
        <div className="bg-gray-800 rounded-3xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700 text-gray-400">
                <th className="text-right px-4 py-3 font-medium">زمان اجرا</th>
                <th className="text-right px-4 py-3 font-medium">وضعیت</th>
                <th className="text-right px-4 py-3 font-medium">مقصد</th>
                <th className="text-right px-4 py-3 font-medium">پیش‌نمایش پیام</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr
                  key={entry.id}
                  className="border-b border-gray-800 hover:bg-gray-750 transition-colors"
                >
                  <td className="px-4 py-3 text-gray-300 text-xs">
                    {new Date(entry.executed_at).toLocaleString("fa-IR")}
                  </td>
                  <td className="px-4 py-3">
                    {entry.status === "success" && (
                      <span className="text-green-400 text-xs">موفق</span>
                    )}
                    {entry.status === "error" && (
                      <span className="text-red-400 text-xs">خطا</span>
                    )}
                    {entry.status === "send_failed" && (
                      <span className="text-yellow-400 text-xs">ارسال ناموفق</span>
                    )}
                    {!["success", "error", "send_failed"].includes(entry.status) && (
                      <span className="text-gray-500 text-xs">{entry.status}</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">
                    {entry.destination === "telegram" ? "تلگرام" : "بله"}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs max-w-xs truncate">
                    {entry.message_preview || "—"}
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
