"use client";

import { useState, useCallback } from "react";
import { ChatMessage, type ChatMessageData } from "@/components/chat/chat-message";
import { ChatInput } from "@/components/chat/chat-input";
import { useSendQueryStream } from "@/hooks/use-send-query-stream";

function genId() {
  return Date.now().toString(36) + Math.random().toString(36).substring(2);
}

const SUGGESTED_PROMPTS = [
  "امروز چند نفر دیده شدند؟",
  "آخرین رویداد چه زمانی بود؟",
  "تعداد رویدادها به تفکیک دوربین چیست؟",
  "پرترفیک‌ترین ساعت روز کدام است؟",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const { mutate, isPending } = useSendQueryStream();

  const sendQuery = useCallback(
    (question: string) => {
      if (!question.trim() || isPending) return;

      const userMsg: ChatMessageData = {
        id: genId(),
        role: "user",
        content: question,
      };

      const assistantId = genId();
      const assistantMsg: ChatMessageData = {
        id: assistantId,
        role: "assistant",
        content: "",
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);

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
    },
    [isPending, mutate]
  );

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto">
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-600 mt-20">
            <p className="text-lg">سوال خود را درباره رویدادهای دوربین بپرسید</p>
            <div className="mt-6 flex flex-wrap gap-2 justify-center">
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => sendQuery(prompt)}
                  className="bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-full px-4 py-2 text-sm transition-colors"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
      </div>

      <ChatInput sendQuery={sendQuery} isPending={isPending} />
    </div>
  );
}
