"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import {
  fetchReportRules,
  fetchReportRule,
  createReportRule,
  updateReportRule,
  deleteReportRule,
  testReportRule,
  fetchRuleHistory,
  fetchAllHistory,
  fetchFrigateConfig,
  fetchCameras,
  parseZonesFromConfig,
  type ReportRule,
  type CreateReportRulePayload,
  type UpdateReportRulePayload,
  type HistoryEntry,
  type CameraInfo,
} from "@/lib/report-rules-api";

export function useReportRules() {
  return useQuery<ReportRule[]>({
    queryKey: ["report-rules"],
    queryFn: fetchReportRules,
    staleTime: 30_000,
  });
}

export function useReportRule(id: string | null) {
  return useQuery<ReportRule | null>({
    queryKey: ["report-rules", id],
    queryFn: () => (id ? fetchReportRule(id) : Promise.resolve(null)),
    enabled: !!id,
  });
}

export function useCreateReportRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateReportRulePayload) => createReportRule(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["report-rules"] });
    },
    onError: (err) => {
      console.error("[ReportRules] Create failed:", err);
    },
  });
}

export function useUpdateReportRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: string;
      payload: UpdateReportRulePayload;
    }) => updateReportRule(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["report-rules"] });
    },
    onError: (err) => {
      console.error("[ReportRules] Update failed:", err);
    },
  });
}

export function useDeleteReportRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteReportRule(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["report-rules"] });
    },
    onError: (err) => {
      console.error("[ReportRules] Delete failed:", err);
    },
  });
}

export function useTestReportRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => testReportRule(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["report-rules"] });
      qc.invalidateQueries({ queryKey: ["report-history"] });
    },
    onError: (err) => {
      console.error("[ReportRules] Test run failed:", err);
    },
  });
}

export function useRuleHistory(ruleId: string | null) {
  return useQuery<HistoryEntry[]>({
    queryKey: ["report-history", ruleId],
    queryFn: () => (ruleId ? fetchRuleHistory(ruleId) : Promise.resolve([])),
    enabled: !!ruleId,
    staleTime: 10_000,
  });
}

export function useAllHistory() {
  return useQuery<HistoryEntry[]>({
    queryKey: ["report-history", "all"],
    queryFn: fetchAllHistory,
    staleTime: 10_000,
  });
}

export function useFrigateZones() {
  return useQuery<string[]>({
    queryKey: ["frigate-zones"],
    queryFn: async () => {
      try {
        const config = await fetchFrigateConfig();
        return parseZonesFromConfig(config);
      } catch (err) {
        console.error("[ReportRules] Failed to fetch frigate config:", err);
        return [];
      }
    },
    staleTime: 120_000,
  });
}

export function useCameras() {
  return useQuery<{ cameras: CameraInfo[]; total: number }>({
    queryKey: ["cameras"],
    queryFn: async () => {
      try {
        return await fetchCameras();
      } catch (err) {
        console.error("[ReportRules] Failed to fetch cameras:", err);
        return { cameras: [], total: 0 };
      }
    },
    staleTime: 120_000,
  });
}
