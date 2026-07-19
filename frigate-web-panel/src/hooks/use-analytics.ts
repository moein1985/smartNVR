"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

interface AnalyticsSummary {
  total_events: number;
  events_by_label: Record<string, number>;
  events_by_hour: Record<string, number>;
  events_by_camera: Record<string, number>;
  peak_hour: number;
  avg_daily_events: number;
}

export function useAnalytics(camera?: string) {
  return useQuery({
    queryKey: ["analytics", camera],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/api/v1/analytics/summary", {
        params: camera ? { query: { camera } } : undefined,
      });
      if (error) throw error;
      return data as AnalyticsSummary;
    },
    staleTime: 60_000,
  });
}
