"use client";

import { useState, useEffect } from "react";
import { useSendQueryStream } from "@/hooks/use-send-query-stream";
import type { ChatMessageData } from "./chat-message";

interface ChatInputProps {
  setMessages: React.Dispatch<React.SetStateAction<ChatMessageData[]>>;
  sendQueryRef?: React.MutableRefObject<((q: string) => void) | null>;
}

export function ChatInput({ setMessages, sendQueryRef }: ChatInputProps) {
  const [input, setInput] = useState("");
  const { mutate, isPending } = useSendQueryStream();

  const sendQuery = (question: string) => {
    if (!question.trim() || isPending) return;

    const userMsg: ChatMessageData = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
    };

    const assistantId = crypto.randomUUID();
    const assistantMsg: ChatMessageData = {
      id: assistantId,
      role: "assistant",
      content: "",
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setInput("");

    mutate(
      { question },
      {
        onMeta: (meta) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    sql: meta.sql,
                    columns: meta.columns,
                    rows: meta.rows,
                    error: meta.error ?? undefined,
                  }
                : m
            )
          );
        },
        onChunk: (chunk) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content + chunk }
                : m
            )
          );
        },
        onError: (err) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: "خطا در ارتباط با سرور", error: err }
                : m
            )
          );
        },
      }
    );
  };

  useEffect(() => {
    if (sendQueryRef) {
      sendQueryRef.current = sendQuery;
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendQuery(input);
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-gray-800 p-4">
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="سوال خود را بنویسید..."
          className="flex-1 bg-gray-800 text-gray-100 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-cyan-500"
          disabled={isPending}
        />
        <button
          type="submit"
          disabled={isPending || !input.trim()}
          className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white rounded-xl px-6 py-3 font-medium transition-colors"
        >
          {isPending ? "..." : "ارسال"}
        </button>
      </div>
    </form>
  );
}
