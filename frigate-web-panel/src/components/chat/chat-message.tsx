"use client";

export interface ChatMessageData {
  id: string;
  role: "user" | "assistant";
  content: string;
  sql?: string;
  rows?: unknown[][];
  columns?: string[];
  error?: string;
}

export function ChatMessage({ message }: { message: ChatMessageData }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-3xl rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-cyan-600 text-white"
            : "bg-gray-800 text-gray-100"
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>

        {message.sql && (
          <pre className="mt-3 bg-gray-900 rounded-lg p-3 text-xs text-green-400 overflow-x-auto">
            <code>{message.sql}</code>
          </pre>
        )}

        {message.columns && message.columns.length > 0 && (
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-700">
                  {message.columns.map((col, i) => (
                    <th key={i} className="px-2 py-1 text-left text-gray-400">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {message.rows?.slice(0, 20).map((row, i) => (
                  <tr key={i} className="border-b border-gray-800">
                    {row.map((cell, j) => (
                      <td key={j} className="px-2 py-1">
                        {String(cell)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {message.error && (
          <p className="mt-2 text-red-400 text-sm">❌ {message.error}</p>
        )}
      </div>
    </div>
  );
}
