"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChatMessage, type ChatMessageData } from "./chat/chat-message";
import { ChatInput } from "./chat/chat-input";
import { HealthBadge } from "./health/health-badge";

const SUGGESTED_PROMPTS = [
  "امروز چند نفر دیده شدند؟",
  "آخرین رویداد چه زمانی بود؟",
  "تعداد رویدادها به تفکیک دوربین چیست؟",
  "پرترفیک‌ترین ساعت روز کدام است؟",
];

export function ChatView() {
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const sendQueryRef = useRef<((q: string) => void) | null>(null);
  const pathname = usePathname();

  const handleSuggestedPrompt = (prompt: string) => {
    sendQueryRef.current?.(prompt);
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto">
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div>
            <h1 className="text-xl font-bold text-cyan-400">
              Frigate Intelligence Panel
            </h1>
            <p className="text-sm text-gray-500">
              دستیار هوشمند دوربین‌های نظارتی
            </p>
          </div>
          <nav className="flex gap-2">
            <Link
              href="/"
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                pathname === "/"
                  ? "bg-cyan-600 text-white"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              چت
            </Link>
            <Link
              href="/analytics"
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                pathname === "/analytics"
                  ? "bg-cyan-600 text-white"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              تحلیل‌ها
            </Link>
          </nav>
        </div>
        <HealthBadge />
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-600 mt-20">
            <p className="text-lg">سوال خود را درباره رویدادهای دوربین بپرسید</p>
            <div className="mt-6 flex flex-wrap gap-2 justify-center">
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => handleSuggestedPrompt(prompt)}
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

      <ChatInput setMessages={setMessages} sendQueryRef={sendQueryRef} />
    </div>
  );
}
