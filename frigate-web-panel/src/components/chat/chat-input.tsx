"use client";

import { useState } from "react";
import { useSendQuery } from "@/hooks/use-send-query";
import type { ChatMessageData } from "./chat-message";

interface ChatInputProps {
  setMessages: React.Dispatch<React.SetStateAction<ChatMessageData[]>>;
}

export function ChatInput({ setMessages }: ChatInputProps) {
  const [input, setInput] = useState("");
  const mutation = useSendQuery();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || mutation.isPending) return;

    const userMsg: ChatMessageData = {
      id: crypto.randomUUID(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    mutation.mutate(
      { question: input },
      {
        onSuccess: (data) => {
          const assistantMsg: ChatMessageData = {
            id: crypto.randomUUID(),
            role: "assistant",
            content: data.explanation,
            sql: data.sql,
            columns: data.columns,
            rows: data.rows,
            error: data.error ?? undefined,
          };
          setMessages((prev) => [...prev, assistantMsg]);
        },
        onError: (err) => {
          const errorMsg: ChatMessageData = {
            id: crypto.randomUUID(),
            role: "assistant",
            content: "خطا در ارتباط با سرور",
            error: String(err),
          };
          setMessages((prev) => [...prev, errorMsg]);
        },
      }
    );
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
          disabled={mutation.isPending}
        />
        <button
          type="submit"
          disabled={mutation.isPending || !input.trim()}
          className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white rounded-xl px-6 py-3 font-medium transition-colors"
        >
          {mutation.isPending ? "..." : "ارسال"}
        </button>
      </div>
    </form>
  );
}
