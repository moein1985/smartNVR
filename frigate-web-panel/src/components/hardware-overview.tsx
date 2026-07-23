"use client";

import type { HardwareInfo } from "@/hooks/use-hardware";

function MetricCard({
  label,
  value,
  unit,
  subValue,
  color = "cyan",
}: {
  label: string;
  value: string;
  unit?: string;
  subValue?: string;
  color?: "cyan" | "purple" | "green";
}) {
  const colorMap = {
    cyan: "text-cyan-400",
    purple: "text-purple-400",
    green: "text-green-400",
  };
  return (
    <div className="bg-gray-800 rounded-3xl p-5">
      <p className="text-sm text-gray-400">{label}</p>
      <p className={`text-2xl font-bold ${colorMap[color]} mt-2`}>
        {value}
        {unit && <span className="text-sm text-gray-500 mr-1">{unit}</span>}
      </p>
      {subValue && (
        <p className="text-xs text-gray-500 mt-1">{subValue}</p>
      )}
    </div>
  );
}

export function HardwareOverview({ data }: { data: HardwareInfo | undefined }) {
  if (!data) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="bg-gray-800 rounded-3xl p-5 animate-pulse h-24"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="پردازنده"
          value={String(data.cpu.cores)}
          unit="هسته"
          subValue={`استفاده: ${data.cpu.utilization_pct}%`}
          color="cyan"
        />
        <MetricCard
          label="حافظه RAM"
          value={data.memory.total_gb.toFixed(1)}
          unit="GB"
          subValue={`آزاد: ${data.memory.available_gb.toFixed(1)} GB (${data.memory.used_pct}%)`}
          color="purple"
        />
        {data.gpus.length > 0 ? (
          data.gpus.map((gpu) => (
            <MetricCard
              key={gpu.index}
              label={`GPU ${gpu.index}: ${gpu.name}`}
              value={`${gpu.memory_total_mb}`}
              unit="MB"
              subValue={`استفاده: ${gpu.gpu_utilization_pct}% | ${gpu.memory_used_mb} MB`}
              color="green"
            />
          ))
        ) : (
          <MetricCard
            label="GPU"
            value="—"
            subValue="GPU یافت نشد"
            color="green"
          />
        )}
      </div>
    </div>
  );
}
