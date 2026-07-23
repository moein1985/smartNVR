"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

function getAuthHeaders(): Record<string, string> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export interface ContainerCapability {
  supports_gpu: boolean;
  detection_strategy: string;
  details: string;
}

export interface ContainerInfo {
  name: string;
  image: string;
  status: string;
  short_id: string;
  ports: Record<string, unknown>[];
  capability: ContainerCapability;
}

export interface ResourceAssignment {
  service: string;
  cpuset?: string;
  gpu_ids?: string[];
  memory_limit?: string;
}

export function useContainers(allStatuses = false) {
  return useQuery<{ containers: ContainerInfo[] }>({
    queryKey: ["containers", allStatuses],
    queryFn: async () => {
      try {
        const res = await fetch(
          `${BASE_URL}/api/v1/system/containers?all_statuses=${allStatuses}`,
          { headers: getAuthHeaders(), cache: "no-store" }
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
      } catch (err) {
        console.error("[Containers] Failed to fetch:", err);
        return { containers: [] };
      }
    },
    refetchInterval: 10_000,
    staleTime: 5_000,
  });
}

export function useAssignResources() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (assignments: ResourceAssignment[]) => {
      const res = await fetch(`${BASE_URL}/api/v1/system/assign`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ assignments }),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail || `HTTP ${res.status}`);
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["containers"] });
    },
    onError: (err) => {
      console.error("[Containers] Assign failed:", err);
    },
  });
}
