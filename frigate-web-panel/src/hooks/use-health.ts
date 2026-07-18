"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/api/v1/health");
      if (error) throw error;
      return data;
    },
    refetchInterval: 30_000,
  });
}
