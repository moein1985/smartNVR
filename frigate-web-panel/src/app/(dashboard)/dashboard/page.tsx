"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export default function DashboardPage() {
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/api/v1/health");
      if (error) throw error;
      return data as Record<string, unknown>;
    },
    refetchInterval: 30_000,
  });

  const { data: hardware } = useQuery({
    queryKey: ["hardware"],
    queryFn: async () => {
      const res = await fetch(`${BASE_URL}/api/v1/system/hardware`);
      if (!res.ok) throw new Error("Failed to fetch hardware");
      return res.json();
    },
    refetchInterval: 5_000,
  });

  const { data: containers } = useQuery({
    queryKey: ["containers"],
    queryFn: async () => {
      const res = await fetch(`${BASE_URL}/api/v1/system/containers`);
      if (!res.ok) throw new Error("Failed to fetch containers");
      return res.json();
    },
    refetchInterval: 10_000,
  });

  const cpu = hardware?.cpu;
  const ram = hardware?.ram;
  const gpus = hardware?.gpus || [];
  const containerList = containers?.containers || [];

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div>
        <h1 className="text-xl font-bold text-gray-200">داشبورد</h1>
        <p className="text-sm text-gray-500 mt-1">نمای کلی سیستم</p>
      </div>

      {/* Health Status */}
      <div className="bg-gray-800 rounded-3xl p-6">
        <h2 className="text-sm font-medium text-gray-400 mb-4">وضعیت سیستم</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <p className="text-xs text-gray-500">وضعیت دیتابیس</p>
            <p className={`text-sm font-medium mt-1 ${health?.db_connected ? "text-green-400" : "text-red-400"}`}>
              {health?.db_connected ? "متصل" : "قطع"}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">منطقه زمانی سرور</p>
            <p className="text-sm font-medium mt-1 text-gray-200">
              {String(health?.server_timezone || "—")}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">زمان سرور</p>
            <p className="text-sm font-medium mt-1 text-gray-200">
              {String(health?.server_datetime_iso || "—")}
            </p>
          </div>
        </div>
      </div>

      {/* Hardware Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* CPU */}
        <div className="bg-gray-800 rounded-3xl p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-3">CPU</h3>
          {cpu ? (
            <>
              <p className="text-2xl font-bold text-cyan-400">{cpu.cores} هسته</p>
              <p className="text-xs text-gray-500 mt-1">{cpu.model || "—"}</p>
              <div className="mt-3">
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-cyan-500 rounded-full transition-all"
                    style={{ width: `${cpu.percent}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">{cpu.percent?.toFixed(1)}% استفاده</p>
              </div>
            </>
          ) : (
            <p className="text-sm text-gray-600">در حال بارگذاری...</p>
          )}
        </div>

        {/* RAM */}
        <div className="bg-gray-800 rounded-3xl p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-3">حافظه RAM</h3>
          {ram ? (
            <>
              <p className="text-2xl font-bold text-cyan-400">
                {(ram.total / (1024**3)).toFixed(1)} GB
              </p>
              <div className="mt-3">
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-cyan-500 rounded-full transition-all"
                    style={{ width: `${ram.percent}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {ram.percent?.toFixed(1)}% استفاده — {(ram.available / (1024**3)).toFixed(1)} GB آزاد
                </p>
              </div>
            </>
          ) : (
            <p className="text-sm text-gray-600">در حال بارگذاری...</p>
          )}
        </div>

        {/* GPU */}
        <div className="bg-gray-800 rounded-3xl p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-3">GPU</h3>
          {gpus.length > 0 ? (
            gpus.map((gpu: { name: string; memory_total_mb: number; utilization_percent: number }, i: number) => (
              <div key={i} className={i > 0 ? "mt-3 pt-3 border-t border-gray-700" : ""}>
                <p className="text-sm font-bold text-cyan-400">{gpu.name}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {gpu.memory_total_mb} MB — {gpu.utilization_percent}% استفاده
                </p>
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-600">GPU یافت نشد</p>
          )}
        </div>
      </div>

      {/* Containers */}
      <div className="bg-gray-800 rounded-3xl p-6">
        <h2 className="text-sm font-medium text-gray-400 mb-4">کانتینرها</h2>
        <div className="space-y-2">
          {containerList.length > 0 ? (
            containerList.map((c: { name: string; image: string; status: string; short_id: string }) => (
              <div
                key={c.short_id}
                className="flex items-center justify-between bg-gray-900 rounded-2xl px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <span className={`w-2 h-2 rounded-full ${c.status === "running" ? "bg-green-500" : "bg-red-500"}`} />
                  <div>
                    <p className="text-sm font-medium text-gray-200">{c.name}</p>
                    <p className="text-xs text-gray-500">{c.image}</p>
                  </div>
                </div>
                <span className="text-xs text-gray-500">{c.status}</span>
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-600">کانتینری یافت نشد</p>
          )}
        </div>
      </div>
    </div>
  );
}
