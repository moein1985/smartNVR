"use client";

import { useState } from "react";
import type { ContainerInfo, ResourceAssignment } from "@/hooks/use-containers";
import type { HardwareInfo } from "@/hooks/use-hardware";

const inputClass =
  "w-full bg-gray-900 border border-gray-700 rounded-2xl px-3 py-2 text-gray-200 text-sm focus:outline-none focus:border-cyan-600 focus:ring-1 focus:ring-cyan-600 transition-colors";

interface BindingRow {
  service: string;
  image: string;
  status: string;
  supportsGpu: boolean;
  cpuset: string;
  gpuIds: string[];
  memoryLimit: string;
}

export function ServiceBindingTable({
  containers,
  hardware,
  onApply,
  isApplying,
}: {
  containers: ContainerInfo[];
  hardware: HardwareInfo | undefined;
  onApply: (assignments: ResourceAssignment[]) => void;
  isApplying: boolean;
}) {
  const cpuCores = hardware?.cpu.cores || 0;
  const gpuCount = hardware?.gpus.length || 0;

  const [rows, setRows] = useState<BindingRow[]>(() =>
    containers.map((c) => ({
      service: c.name,
      image: c.image,
      status: c.status,
      supportsGpu: c.capability?.supports_gpu ?? false,
      cpuset: "",
      gpuIds: [],
      memoryLimit: "",
    }))
  );

  const updateRow = (idx: number, updates: Partial<BindingRow>) => {
    setRows((prev) =>
      prev.map((r, i) => (i === idx ? { ...r, ...updates } : r))
    );
  };

  const toggleCpuCore = (idx: number, core: number) => {
    setRows((prev) =>
      prev.map((r, i) => {
        if (i !== idx) return r;
        const cores = r.cpuset
          ? r.cpuset.split(",").map(Number)
          : [];
        if (cores.includes(core)) {
          return { ...r, cpuset: cores.filter((c) => c !== core).join(",") };
        }
        return { ...r, cpuset: [...cores, core].sort((a, b) => a - b).join(",") };
      })
    );
  };

  const toggleGpu = (idx: number, gpuId: number) => {
    setRows((prev) =>
      prev.map((r, i) => {
        if (i !== idx) return r;
        if (r.gpuIds.includes(String(gpuId))) {
          return {
            ...r,
            gpuIds: r.gpuIds.filter((g) => g !== String(gpuId)),
          };
        }
        return { ...r, gpuIds: [...r.gpuIds, String(gpuId)] };
      })
    );
  };

  const handleApply = () => {
    const assignments: ResourceAssignment[] = rows.map((r) => ({
      service: r.service,
      cpuset: r.cpuset || undefined,
      gpu_ids: r.gpuIds.length > 0 ? r.gpuIds : undefined,
      memory_limit: r.memoryLimit || undefined,
    }));
    onApply(assignments);
  };

  if (containers.length === 0) {
    return (
      <div className="bg-gray-800 rounded-3xl p-12 text-center">
        <p className="text-gray-500 text-sm">هیچ کانتینری یافت نشد</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-3xl overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-700 text-gray-400">
            <th className="text-right px-4 py-3 font-medium">سرویس</th>
            <th className="text-right px-4 py-3 font-medium">وضعیت</th>
            <th className="text-right px-4 py-3 font-medium">هسته‌های CPU</th>
            <th className="text-right px-4 py-3 font-medium">GPU</th>
            <th className="text-right px-4 py-3 font-medium">محدودیت حافظه</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr
              key={row.service}
              className="border-b border-gray-800 hover:bg-gray-750 transition-colors"
            >
              <td className="px-4 py-3">
                <div className="text-gray-200 font-medium">{row.service}</div>
                <div className="text-gray-600 text-xs mt-0.5">{row.image}</div>
              </td>
              <td className="px-4 py-3">
                <span
                  className={`text-xs ${
                    row.status === "running"
                      ? "text-green-400"
                      : "text-gray-500"
                  }`}
                >
                  {row.status}
                </span>
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-1 max-w-xs">
                  {Array.from({ length: cpuCores }, (_, core) => {
                    const selected = row.cpuset
                      .split(",")
                      .map(Number)
                      .includes(core);
                    return (
                      <button
                        key={core}
                        type="button"
                        onClick={() => toggleCpuCore(idx, core)}
                        className={`w-7 h-7 rounded-lg text-xs font-medium transition-colors ${
                          selected
                            ? "bg-cyan-600 text-white"
                            : "bg-gray-900 text-gray-500 hover:bg-gray-700"
                        }`}
                      >
                        {core}
                      </button>
                    );
                  })}
                </div>
              </td>
              <td className="px-4 py-3">
                {row.supportsGpu ? (
                  <div className="flex flex-wrap gap-1">
                    {Array.from({ length: gpuCount }, (_, gpuIdx) => {
                      const selected = row.gpuIds.includes(String(gpuIdx));
                      return (
                        <button
                          key={gpuIdx}
                          type="button"
                          onClick={() => toggleGpu(idx, gpuIdx)}
                          className={`px-2 py-1 rounded-lg text-xs font-medium transition-colors ${
                            selected
                              ? "bg-green-600 text-white"
                              : "bg-gray-900 text-gray-500 hover:bg-gray-700"
                          }`}
                        >
                          GPU {gpuIdx}
                        </button>
                      );
                    })}
                    {gpuCount === 0 && (
                      <span className="text-gray-600 text-xs">GPU موجود نیست</span>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <span className="text-gray-600 text-xs">غیرفعال</span>
                    <div className="group relative">
                      <span className="cursor-help text-yellow-500">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                        </svg>
                      </span>
                      <span className="absolute right-0 top-6 z-40 hidden group-hover:block bg-gray-900 border border-gray-700 rounded-xl px-3 py-2 text-xs text-gray-300 whitespace-nowrap shadow-xl">
                        این کانتینر از GPU پشتیبانی نمی‌کند
                      </span>
                    </div>
                  </div>
                )}
              </td>
              <td className="px-4 py-3">
                <input
                  type="text"
                  value={row.memoryLimit}
                  onChange={(e) => updateRow(idx, { memoryLimit: e.target.value })}
                  placeholder="مثال: 2g"
                  className={inputClass + " w-24"}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="px-4 py-4 border-t border-gray-700 flex justify-end">
        <button
          onClick={handleApply}
          disabled={isApplying}
          className="bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50 text-white font-medium rounded-2xl px-6 py-2.5 text-sm transition-colors"
        >
          {isApplying ? "در حال اعمال..." : "اعمال تغییرات"}
        </button>
      </div>
    </div>
  );
}
