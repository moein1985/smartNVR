# Phase 7: Web UI (Next.js) — Detailed Roadmap

## Objective

Build a centralized Web UI using Next.js (App Router), TypeScript, TailwindCSS, and React Query. API clients and TypeScript types are auto-generated from the FastAPI backend's OpenAPI spec (running on port 8088). The first page to implement is a Chat UI for natural language queries.

---

## Prerequisites

- Phase 2 complete (REST API running on `http://192.168.85.202:8088`)
- Node.js 20+ installed
- npm or pnpm available
- FastAPI backend serving OpenAPI spec at `/openapi.json`

---

## Step 7.1: Project Scaffolding

**Create Next.js project:**

```bash
cd C:\Users\Moein\Documents\Codes\YOLO
npx create-next-app@latest frigate-web-panel --typescript --tailwind --app --eslint --src-dir --import-alias "@/*" --no-turbopack
```

**Resulting structure:**
```
frigate-web-panel/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/
│   ├── lib/
│   │   ├── api/
│   │   │   └── generated.ts        # Auto-generated OpenAPI types
│   │   └── api-client.ts           # openapi-fetch client
│   └── providers/
│       └── query-provider.tsx      # React Query provider
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.ts
└── openapi.json                     # Downloaded spec (gitignored)
```

**Acceptance Criteria:**
- [x] `npx create-next-app` completes without errors (Next.js 16.2.10)
- [x] `npm run dev` starts dev server on `http://localhost:3000`
- [x] TypeScript strict mode enabled
- [x] TailwindCSS working (TailwindCSS 4)
- [x] `src/` directory structure used
- [x] Import alias `@/*` configured in `tsconfig.json`

---

## Step 7.2: Install Dependencies

**Runtime dependencies:**
```bash
cd frigate-web-panel
npm install @tanstack/react-query openapi-fetch
```

**Dev dependencies:**
```bash
npm install -D openapi-typescript
```

**Package purposes:**

| Package | Type | Purpose |
|---------|------|---------|
| `@tanstack/react-query` | runtime | Server state management, caching, retries |
| `openapi-fetch` | runtime | Type-safe fetch client generated from OpenAPI spec |
| `openapi-typescript` | dev | Generates TypeScript types from `openapi.json` |

**Acceptance Criteria:**
- [x] `@tanstack/react-query` installed and importable (^5.101.2)
- [x] `openapi-fetch` installed and importable (^0.17.0)
- [x] `openapi-typescript` installed as dev dependency (^7.13.0)
- [x] No version conflicts in `package.json`

---

## Step 7.3: Configure OpenAPI Code Generation

**File: `frigate-web-panel/package.json` (scripts section)**

Add the following scripts:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "generate-api": "openapi-typescript http://192.168.85.202:8088/openapi.json -o src/lib/api/generated.ts"
  }
}
```

**How it works:**
1. `npm run generate-api` fetches `openapi.json` from the running FastAPI backend
2. `openapi-typescript` parses the spec and generates TypeScript types in `src/lib/api/generated.ts`
3. The generated file exports a `paths` type that `openapi-fetch` uses for type-safe API calls
4. Re-run this command whenever the backend API changes

**Acceptance Criteria:**
- [x] `npm run generate-api` fetches spec from `http://192.168.85.202:8088/openapi.json`
- [x] `src/lib/api/generated.ts` is created with TypeScript types (354 lines)
- [x] Generated file contains `paths` interface with all API routes (query, health, events, pos/correlate, analytics/summary)
- [x] Script works even if backend is on a different host (change URL in script)

---

## Step 7.4: API Client Setup

**File: `src/lib/api-client.ts`**

```typescript
import createClient from "openapi-fetch";
import type { paths } from "./api/generated";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://192.168.85.202:8088";

export const apiClient = createClient<paths>({
  baseUrl: BASE_URL,
});

// Optional: Add request interceptor for auth headers
// apiClient.use({
//   async ({ request }) => {
//     request.headers.set("Authorization", `Bearer ${token}`);
//     return request;
//   },
// });
```

**File: `.env.local`**

```env
NEXT_PUBLIC_API_URL=http://192.168.85.202:8088
```

**Acceptance Criteria:**
- [x] `apiClient` is typed with `paths` from generated types
- [x] Base URL configurable via `NEXT_PUBLIC_API_URL` env var
- [x] `apiClient.GET` and `apiClient.POST` are type-safe (autocomplete for paths and params)

---

## Step 7.5: React Query Provider

**File: `src/providers/query-provider.tsx`**

```typescript
"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

export function QueryProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,          // 1 minute
            retry: 2,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
```

**File: `src/app/layout.tsx` (update)**

Wrap the app with `QueryProvider`:

```typescript
import type { Metadata } from "next";
import { QueryProvider } from "@/providers/query-provider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Frigate Intelligence Panel",
  description: "AI-powered surveillance analytics web panel",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fa" dir="rtl">
      <body>
        <QueryProvider>{children}</body>
    </html>
  );
}
```

**Acceptance Criteria:**
- [x] `QueryProvider` wraps the entire app in `layout.tsx`
- [x] `QueryClient` configured with sensible defaults (staleTime 60s, retry 2)
- [x] `useQuery` and `useMutation` hooks work in any component
- [x] HTML lang set to `fa` and dir to `rtl` for Persian UI

---

## Step 7.6: Chat Page — UI Layout

**File: `src/app/page.tsx`**

Replace default page with Chat UI shell:

```typescript
import { ChatView } from "@/components/chat/chat-view";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-950 text-gray-100">
      <ChatView />
    </main>
  );
}
```

**File: `src/components/chat/chat-view.tsx`**

```typescript
"use client";

import { useState } from "react";
import { ChatMessages } from "./chat-messages";
import { ChatInput } from "./chat-input";
import { ChatHeader } from "./chat-header";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sql?: string;
  rows?: unknown[][];
  columns?: string[];
  error?: string;
}

export function ChatView() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto">
      <ChatHeader />
      <ChatMessages messages={messages} />
      <ChatInput messages={messages} setMessages={setMessages} />
    </div>
  );
}
```

**Acceptance Criteria:**
- [x] Chat page renders with header, messages area, and input box
- [x] Layout is full-height flex column
- [x] RTL layout works correctly (Persian text direction)
- [x] Dark theme applied (gray-950 background)

---

## Step 7.7: Chat Components

**File: `src/components/chat/chat-header.tsx`**

```typescript
export function ChatHeader() {
  return (
    <header className="border-b border-gray-800 px-6 py-4">
      <h1 className="text-xl font-bold text-cyan-400">
        Frigate Intelligence Panel
      </h1>
      <p className="text-sm text-gray-500">دستیار هوشمند دوربین‌های نظارتی</p>
    </header>
  );
}
```

**File: `src/components/chat/chat-messages.tsx`**

```typescript
"use client";

import type { ChatMessage } from "./chat-view";
import { ChatBubble } from "./chat-bubble";

export function ChatMessages({ messages }: { messages: ChatMessage[] }) {
  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
      {messages.length === 0 && (
        <div className="text-center text-gray-600 mt-20">
          <p className="text-lg">سوال خود را درباره رویدادهای دوربین بپرسید</p>
          <p className="text-sm mt-2">مثال: آخرین رویدادهای شخصی چه زمانی بود؟</p>
        </div>
      )}
      {messages.map((msg) => (
        <ChatBubble key={msg.id} message={msg} />
      ))}
    </div>
  );
}
```

**File: `src/components/chat/chat-bubble.tsx`**

```typescript
"use client";

import type { ChatMessage } from "./chat-view";

export function ChatBubble({ message }: { message: ChatMessage }) {
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
```

**File: `src/components/chat/chat-input.tsx`**

```typescript
"use client";

import { useState } from "react";
import type { ChatMessage } from "./chat-view";
import { useSendQuery } from "@/hooks/use-send-query";

interface ChatInputProps {
  messages: ChatMessage[];
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
}

export function ChatInput({ messages, setMessages }: ChatInputProps) {
  const [input, setInput] = useState("");
  const mutation = useSendQuery();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || mutation.isPending) return;

    const userMsg: ChatMessage = {
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
          const assistantMsg: ChatMessage = {
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
          const errorMsg: ChatMessage = {
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
```

**Acceptance Criteria:**
- [x] `ChatHeader` shows app title and Persian subtitle
- [x] `ChatMessages` renders empty state with example question
- [x] `ChatBubble` displays user messages (right, cyan) and assistant messages (left, gray)
- [x] `ChatBubble` renders SQL in a code block with green syntax
- [x] `ChatBubble` renders result table with columns and rows (max 20 rows)
- [x] `ChatBubble` shows error in red when present
- [x] `ChatInput` sends question on Enter or button click
- [x] Input is disabled while mutation is pending
- [x] RTL layout works for Persian text

---

## Step 7.8: React Query Hooks

**File: `src/hooks/use-send-query.ts`**

```typescript
"use client";

import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export function useSendQuery() {
  return useMutation({
    mutationFn: async (body: { question: string; max_retries?: number }) => {
      const { data, error } = await apiClient.POST("/api/v1/query", {
        body,
      });
      if (error) throw error;
      return data;
    },
  });
}
```

**File: `src/hooks/use-health.ts`**

```typescript
"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/api/v1/health");
      if (error) throw error;
      return data;
    },
    refetchInterval: 30_000,  // Poll every 30s
  });
}
```

**Acceptance Criteria:**
- [x] `useSendQuery` is a mutation that POSTs to `/api/v1/query`
- [x] Request body is type-safe (autocomplete for `question` and `max_retries`)
- [x] Response is typed (autocomplete for `sql`, `columns`, `rows`, `explanation`)
- [x] `useHealth` polls `/api/v1/health` every 30 seconds
- [x] Error handling throws on non-2xx responses

---

## Step 7.9: Health Status Indicator

**File: `src/components/health/health-badge.tsx`**

```typescript
"use client";

import { useHealth } from "@/hooks/use-health";

export function HealthBadge() {
  const { data, isLoading, isError } = useHealth();

  const status = isError
    ? "offline"
    : isLoading
      ? "connecting"
      : data?.db_connected
        ? "online"
        : "no-db";

  const colors = {
    online: "bg-green-500",
    "no-db": "bg-yellow-500",
    connecting: "bg-gray-500 animate-pulse",
    offline: "bg-red-500",
  };

  const labels = {
    online: "آنلاین",
    "no-db": "DB قطع",
    connecting: "در حال اتصال",
    offline: "آفلاین",
  };

  return (
    <div className="flex items-center gap-2 text-xs text-gray-400">
      <span className={`w-2 h-2 rounded-full ${colors[status]}`} />
      {labels[status]}
    </div>
  );
}
```

**Update `ChatHeader` to include `HealthBadge`:**

```typescript
import { HealthBadge } from "@/components/health/health-badge";

export function ChatHeader() {
  return (
    <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
      <div>
        <h1 className="text-xl font-bold text-cyan-400">Frigate Intelligence Panel</h1>
        <p className="text-sm text-gray-500">دستیار هوشمند دوربین‌های نظارتی</p>
      </div>
      <HealthBadge />
    </header>
  );
}
```

**Acceptance Criteria:**
- [x] Green dot when backend is online and DB connected
- [x] Yellow dot when backend is online but DB not connected
- [x] Red dot when backend is offline
- [x] Pulsing gray dot while connecting
- [x] Status auto-refreshes every 30 seconds

---

## Step 7.10: Analytics Page (Optional, Post-Chat)

**File: `src/app/analytics/page.tsx`**

```typescript
import { AnalyticsView } from "@/components/analytics/analytics-view";

export default function AnalyticsPage() {
  return (
    <main className="min-h-screen bg-gray-950 text-gray-100 p-6">
      <AnalyticsView />
    </main>
  );
}
```

**File: `src/hooks/use-analytics.ts`**

```typescript
"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export function useAnalytics(camera?: string) {
  return useQuery({
    queryKey: ["analytics", camera],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/api/v1/analytics/summary", {
        params: { query: camera ? { camera } : {} },
      });
      if (error) throw error;
      return data;
    },
  });
}
```

**Acceptance Criteria:**
- [ ] `/analytics` page renders analytics summary
- [ ] `useAnalytics` hook fetches from `/api/v1/analytics/summary`
- [ ] Camera filter is supported via query param
- [ ] Loading and error states are handled

---

## Step 7.11: Navigation

**File: `src/components/layout/navbar.tsx`**

```typescript
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "چت" },
  { href: "/analytics", label: "آمار" },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="flex gap-4 px-6 py-2 border-b border-gray-800">
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className={`px-3 py-1 rounded-lg text-sm transition-colors ${
            pathname === link.href
              ? "bg-cyan-600 text-white"
              : "text-gray-400 hover:text-gray-200"
          }`}
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
```

**Update `layout.tsx` to include `Navbar`:**

```typescript
<body>
  <QueryProvider>
    <Navbar />
    {children}
  </QueryProvider>
</body>
```

**Acceptance Criteria:**
- [ ] Navbar renders on all pages
- [ ] Active link highlighted with cyan background
- [ ] Navigation between Chat (`/`) and Analytics (`/analytics`) works
- [ ] RTL layout correct

---

## Step 7.12: Environment Configuration

**File: `.env.local`**

```env
# Backend API URL (FastAPI on Docker)
NEXT_PUBLIC_API_URL=http://192.168.85.202:8088
```

**File: `.env.example`**

```env
NEXT_PUBLIC_API_URL=http://192.168.85.202:8088
```

**File: `.gitignore` (additions)**

```
# OpenAPI generated types
src/lib/api/generated.ts

# OpenAPI spec download
openapi.json
```

**Acceptance Criteria:**
- [x] `.env.local` exists with `NEXT_PUBLIC_API_URL` (created manually)
- [ ] `.env.example` committed as template
- [x] `generated.ts` is gitignored (regenerated from backend)
- [x] `openapi.json` is gitignored

---

## Step 7.13: Build and Production

**Build the project:**
```bash
npm run generate-api    # Regenerate types from backend
npm run build           # Production build
npm run start           # Start production server
```

**Docker deployment (optional, for serving Web UI):**

**File: `frigate-web-panel/Dockerfile`**

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run generate-api
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

**File: `frigate-web-panel/next.config.ts` (update for standalone output)**

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
};

export default nextConfig;
```

**Acceptance Criteria:**
- [ ] `npm run build` completes without TypeScript errors
- [ ] Production server serves the app on port 3000
- [ ] API calls reach backend at `NEXT_PUBLIC_API_URL`
- [ ] Docker image builds (optional)
- [ ] Standalone output mode enabled for Docker

---

## Final Verification (Phase 7 Complete)

**Run these commands:**

```bash
# 1. Generate API types from backend
npm run generate-api

# 2. Start dev server
npm run dev

# 3. Open browser
# http://localhost:3000 — Chat UI
# http://localhost:3000/analytics — Analytics page

# 4. Test chat
# Type: "آخرین رویدادهای شخصی چه زمانی بود؟"
# Should see: SQL + results table + explanation

# 5. Check health badge
# Should show green "آنلاین" dot

# 6. Production build
npm run build && npm run start
```

**Phase 7 Complete When:**
- [x] Next.js project created with TypeScript + Tailwind + App Router
- [x] `@tanstack/react-query`, `openapi-fetch`, `openapi-typescript` installed
- [x] `npm run generate-api` generates types from backend OpenAPI spec
- [x] API client is type-safe (autocomplete for all endpoints)
- [x] React Query provider wraps the app
- [x] Chat page renders with header, messages, and input
- [x] Chat sends questions to `/api/v1/query` and displays SQL + table + explanation
- [x] Health badge shows real-time backend status
- [x] Analytics page fetches and displays summary statistics
- [x] Navbar navigation works between pages
- [x] RTL layout works for Persian text (lang=fa, dir=rtl in layout.tsx)
- [x] Dark theme applied throughout
- [x] `.env.local` configures backend URL
- [ ] `npm run build` succeeds without errors

---

## Technology Stack Summary

| Component | Technology |
|-----------|-----------|
| Framework | Next.js 15 (App Router) |
| Language | TypeScript (strict) |
| Styling | TailwindCSS 4 |
| Server State | @tanstack/react-query |
| API Client | openapi-fetch (type-safe) |
| Type Generation | openapi-typescript (from FastAPI OpenAPI) |
| Layout | RTL, Dark theme |
| Build Output | Standalone (for Docker) |
| Backend | FastAPI on `http://192.168.85.202:8088` |
