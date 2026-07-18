"use client";

import { useHealth } from "@/hooks/use-health";

export function HealthBadge() {
  const { data, isLoading, isError } = useHealth();

  const status = isError
    ? "offline"
    : isLoading
      ? "connecting"
      : data?.db_connected
        ? "online"
        : "no-db";

  const colors: Record<string, string> = {
    online: "bg-green-500",
    "no-db": "bg-yellow-500",
    connecting: "bg-gray-500 animate-pulse",
    offline: "bg-red-500",
  };

  const labels: Record<string, string> = {
    online: "آنلاین",
    "no-db": "DB قطع",
    connecting: "در حال اتصال",
    offline: "آفلاین",
  };

  return (
    <div className="flex items-center gap-2 text-xs text-gray-400">
      <span className={`w-2 h-2 rounded-full ${colors[status]}`} />
      {labels[status]}
    </div>
  );
}
