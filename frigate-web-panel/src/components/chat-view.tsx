"use client";

import { useState } from "react";
import { ChatMessage, type ChatMessageData } from "./chat/chat-message";
import { ChatInput } from "./chat/chat-input";
import { HealthBadge } from "./health/health-badge";

export function ChatView() {
  const [messages, setMessages] = useState<ChatMessageData[]>([]);

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto">
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-cyan-400">
            Frigate Intelligence Panel
          </h1>
          <p className="text-sm text-gray-500">
            دستیار هوشمند دوربین‌های نظارتی
          </p>
        </div>
        <HealthBadge />
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-600 mt-20">
            <p className="text-lg">سوال خود را درباره رویدادهای دوربین بپرسید</p>
            <p className="text-sm mt-2">
              مثال: آخرین رویدادهای شخصی چه زمانی بود؟
            </p>
          </div>
        )}
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
      </div>

      <ChatInput setMessages={setMessages} />
    </div>
  );
}
