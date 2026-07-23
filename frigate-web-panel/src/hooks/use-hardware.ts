"use client";

import { useQuery } from "@tanstack/react-query";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

function getAuthHeaders(): Record<string, string> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export interface HardwareInfo {
  cpu: {
    cores: number;
    utilization_pct: number;
  };
  memory: {
    total_gb: number;
    available_gb: number;
    used_pct: number;
  };
  gpus: {
    index: number;
    name: string;
    memory_total_mb: number;
    memory_used_mb: number;
    gpu_utilization_pct: number;
    uuid: string;
  }[];
}

export function useHardware() {
  return useQuery<HardwareInfo>({
    queryKey: ["hardware"],
    queryFn: async () => {
      try {
        const res = await fetch(`${BASE_URL}/api/v1/system/hardware`, {
          headers: getAuthHeaders(),
          cache: "no-store",
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
      } catch (err) {
        console.error("[Hardware] Failed to fetch:", err);
        throw err;
      }
    },
    refetchInterval: 5_000,
    staleTime: 3_000,
  });
}
