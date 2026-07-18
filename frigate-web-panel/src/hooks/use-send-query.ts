"use client";

import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export function useSendQuery() {
  return useMutation({
    mutationFn: async (body: { question: string; max_retries?: number }) => {
      const { data, error } = await apiClient.POST("/api/v1/query", {
        body: {
          question: body.question,
          max_retries: body.max_retries ?? 3,
        },
      });
      if (error) throw error;
      return data;
    },
  });
}
