"use client";

import { useState, useCallback } from "react";

const BASE_URL = "";

interface StreamCallbacks {
  onMeta?: (meta: {
    sql: string;
    columns: string[];
    rows: unknown[][];
    row_count: number;
    attempts: number;
    error: string | null;
  }) => void;
  onChunk?: (chunk: string) => void;
  onDone?: () => void;
  onError?: (err: string) => void;
}

export function useSendQueryStream() {
  const [isPending, setIsPending] = useState(false);

  const mutate = useCallback(
    async (body: { question: string; max_retries?: number }, cb: StreamCallbacks) => {
      setIsPending(true);
      try {
        const res = await fetch(`${BASE_URL}/api/v1/query/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: body.question,
            max_retries: body.max_retries ?? 3,
          }),
        });

        if (!res.ok) {
          cb.onError?.(`HTTP ${res.status}`);
          setIsPending(false);
          return;
        }

        const reader = res.body?.getReader();
        if (!reader) {
          cb.onError?.("No response body");
          setIsPending(false);
          return;
        }

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const payload = line.slice(6).trim();
            if (payload === "[DONE]") {
              cb.onDone?.();
              setIsPending(false);
              return;
            }
            try {
              const parsed = JSON.parse(payload);
              if (parsed.chunk) {
                cb.onChunk?.(parsed.chunk);
              } else if (parsed.sql !== undefined) {
                cb.onMeta?.(parsed);
              }
            } catch {
              // ignore malformed lines
            }
          }
        }
        cb.onDone?.();
      } catch (err) {
        cb.onError?.(String(err));
      } finally {
        setIsPending(false);
      }
    },
    []
  );

  return { mutate, isPending };
}
