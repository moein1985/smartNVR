"use client";

import { useState } from "react";

interface ChatInputProps {
  sendQuery: (question: string) => void;
  isPending: boolean;
}

export function ChatInput({ sendQuery, isPending }: ChatInputProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendQuery(input);
    setInput("");
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
