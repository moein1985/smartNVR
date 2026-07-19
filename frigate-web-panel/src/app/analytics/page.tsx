"use client";

import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { useAnalytics } from "@/hooks/use-analytics";
import { HealthBadge } from "@/components/health/health-badge";
import Link from "next/link";
import { usePathname } from "next/navigation";

const COLORS = ["#06b6d4", "#8b5cf6", "#f59e0b", "#ef4444", "#10b981", "#ec4899"];

export default function AnalyticsPage() {
  const { data, isLoading, isError } = useAnalytics();
  const pathname = usePathname();

  const hourlyData = data
    ? Object.entries(data.events_by_hour).map(([hour, count]) => ({
        hour: `${hour}:00`,
        count,
      }))
    : [];

  const labelData = data
    ? Object.entries(data.events_by_label).map(([label, count]) => ({
        name: label,
        value: count,
      }))
    : [];

  return (
    <div className="flex flex-col h-screen max-w-5xl mx-auto">
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div>
            <h1 className="text-xl font-bold text-cyan-400">
              Frigate Intelligence Panel
            </h1>
            <p className="text-sm text-gray-500">داشبورد تحلیلی</p>
          </div>
          <nav className="flex gap-2">
            <Link
              href="/"
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                pathname === "/"
                  ? "bg-cyan-600 text-white"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              چت
            </Link>
            <Link
              href="/analytics"
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                pathname === "/analytics"
                  ? "bg-cyan-600 text-white"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              تحلیل‌ها
            </Link>
          </nav>
        </div>
        <HealthBadge />
      </header>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {isLoading && (
          <div className="text-center text-gray-500 mt-20">در حال بارگذاری...</div>
        )}
        {isError && (
          <div className="text-center text-red-400 mt-20">خطا در دریافت داده‌ها</div>
        )}

        {data && (
          <>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-800 rounded-xl p-6">
                <p className="text-sm text-gray-400">کل رویدادها</p>
                <p className="text-3xl font-bold text-cyan-400 mt-2">
                  {data.total_events.toLocaleString("fa-IR")}
                </p>
              </div>
              <div className="bg-gray-800 rounded-xl p-6">
                <p className="text-sm text-gray-400">میانگین روزانه</p>
                <p className="text-3xl font-bold text-purple-400 mt-2">
                  {data.avg_daily_events.toLocaleString("fa-IR")}
                </p>
              </div>
            </div>

            <div className="bg-gray-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold text-gray-200 mb-4">
                رویدادها به تفکیک ساعت
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={hourlyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="hour" stroke="#9ca3af" fontSize={12} />
                  <YAxis stroke="#9ca3af" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1f2937",
                      border: "1px solid #374151",
                      borderRadius: "8px",
                    }}
                  />
                  <Bar dataKey="count" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-gray-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold text-gray-200 mb-4">
                رویدادها به تفکیک برچسب
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={labelData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={(entry) => `${entry.name}: ${entry.value}`}
                  >
                    {labelData.map((_, index) => (
                      <Cell key={index} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1f2937",
                      border: "1px solid #374151",
                      borderRadius: "8px",
                    }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
