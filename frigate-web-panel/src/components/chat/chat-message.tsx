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

const FRIGATE_URL =
  process.env.NEXT_PUBLIC_FRIGATE_URL || "http://192.168.85.203:5000";

export function ChatMessage({ message }: { message: ChatMessageData }) {
  const isUser = message.role === "user";

  const idColIndex = message.columns?.findIndex((c) => c === "id") ?? -1;
  const hasSnapshots = idColIndex >= 0 && (message.rows?.length ?? 0) > 0;

  const snapshotRows = hasSnapshots
    ? message.rows!.slice(0, 12).map((row) => {
        const eventId = String(row[idColIndex]);
        const hasClipIndex = message.columns!.findIndex((c) => c === "has_clip");
        const hasClip = hasClipIndex >= 0 ? row[hasClipIndex] === 1 || row[hasClipIndex] === "1" : false;
        return { eventId, hasClip };
      })
    : [];

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

        {hasSnapshots && (
          <div className="mt-4">
            <p className="text-xs text-gray-400 mb-2">📸 تصاویر رویدادها</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
              {snapshotRows.map(({ eventId, hasClip }, idx) => (
                <div
                  key={idx}
                  className="relative group rounded-lg overflow-hidden border border-gray-700 shadow-sm bg-gray-900"
                >
                  <img
                    src={`${FRIGATE_URL}/api/events/${eventId}/snapshot.jpg`}
                    alt={eventId}
                    className="w-full max-h-48 object-cover transition-opacity"
                    loading="lazy"
                    onError={(e) => {
                      const img = e.target as HTMLImageElement;
                      const container = img.parentElement!;
                      if (hasClip) {
                        const video = document.createElement("video");
                        video.src = `${FRIGATE_URL}/api/events/${eventId}/clip.mp4`;
                        video.className = "w-full max-h-48 object-cover";
                        video.muted = true;
                        video.loop = true;
                        video.autoplay = true;
                        video.playsInline = true;
                        container.replaceChild(video, img);
                      } else {
                        container.style.display = "none";
                      }
                    }}
                  />
                  <div className="absolute bottom-0 left-0 right-0 bg-black/60 px-2 py-1 text-[10px] text-gray-300 truncate">
                    {eventId}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {message.sql && (
          <pre className="mt-3 bg-gray-900 rounded-lg p-3 text-xs text-green-400 overflow-x-auto">
            <code>{message.sql}</code>
          </pre>
        )}

        {message.columns && message.columns.length > 0 && (
          <div className="mt-3 max-w-full overflow-x-auto">
            <table className="text-xs">
              <thead>
                <tr className="border-b border-gray-700">
                  {message.columns.map((col, i) => (
                    <th key={i} className="px-2 py-1 text-left text-gray-400 whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {message.rows?.slice(0, 20).map((row, i) => (
                  <tr key={i} className="border-b border-gray-800">
                    {row.map((cell, j) => (
                      <td key={j} className="px-2 py-1 whitespace-nowrap max-w-xs truncate">
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
