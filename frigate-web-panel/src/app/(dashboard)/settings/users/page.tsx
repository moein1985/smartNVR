"use client";

import { useState } from "react";
import {
  useUsers,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
} from "@/hooks/use-users";
import type { User } from "@/lib/users-api";

const inputClass =
  "w-full bg-gray-900 border border-gray-700 rounded-2xl px-4 py-2.5 text-gray-200 text-sm placeholder-gray-600 focus:outline-none focus:border-cyan-600 focus:ring-1 focus:ring-cyan-600 transition-colors";

interface ModalState {
  type: "add" | "edit" | null;
  user?: User | null;
}

export default function UsersPage() {
  const { data: users, isLoading, isError } = useUsers();
  const createMutation = useCreateUser();
  const updateMutation = useUpdateUser();
  const deleteMutation = useDeleteUser();

  const [modal, setModal] = useState<ModalState>({ type: null });
  const [toast, setToast] = useState<
    { type: "success" | "error"; msg: string } | null
  >(null);

  const showToast = (type: "success" | "error", msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 4000);
  };

  const handleDelete = (user: User) => {
    if (user.is_seed) return;
    if (!confirm(`حذف کاربر «${user.username}»؟`)) return;
    deleteMutation.mutate(user.id, {
      onSuccess: () => showToast("success", "کاربر حذف شد"),
      onError: (err) =>
        showToast("error", err instanceof Error ? err.message : "خطا در حذف"),
    });
  };

  if (isLoading) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="text-gray-500 text-sm">در حال بارگذاری...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="text-red-400 text-sm">خطا در دریافت کاربران</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-200">مدیریت کاربران</h1>
          <p className="text-sm text-gray-500 mt-1">کاربران سیستم و سطح دسترسی</p>
        </div>
        <button
          onClick={() => setModal({ type: "add" })}
          className="bg-cyan-600 hover:bg-cyan-700 text-white font-medium rounded-2xl px-5 py-2.5 text-sm transition-colors flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          افزودن کاربر
        </button>
      </div>

      <div className="bg-gray-800 rounded-3xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700 text-gray-400">
              <th className="text-right px-4 py-3 font-medium">نام کاربری</th>
              <th className="text-right px-4 py-3 font-medium">نقش</th>
              <th className="text-right px-4 py-3 font-medium">تاریخ ایجاد</th>
              <th className="text-center px-4 py-3 font-medium">عملیات</th>
            </tr>
          </thead>
          <tbody>
            {(users || []).map((user) => (
              <tr
                key={user.id}
                className="border-b border-gray-800 hover:bg-gray-750 transition-colors"
              >
                <td className="px-4 py-3 text-gray-200 font-medium">
                  {user.username}
                  {user.is_seed && (
                    <span className="mr-2 text-xs text-cyan-500 bg-cyan-950/40 rounded-full px-2 py-0.5">
                      Seed
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`text-xs rounded-full px-2.5 py-1 ${
                      user.role === "admin"
                        ? "bg-cyan-950/40 text-cyan-400"
                        : "bg-gray-700 text-gray-400"
                    }`}
                  >
                    {user.role === "admin" ? "مدیر" : "کاربر"}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">
                  {user.created_at
                    ? new Date(user.created_at).toLocaleDateString("fa-IR")
                    : "—"}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-center gap-3">
                    <button
                      onClick={() => setModal({ type: "edit", user })}
                      className="text-gray-400 hover:text-cyan-400 transition-colors"
                      title="ویرایش"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" />
                      </svg>
                    </button>
                    {user.is_seed ? (
                      <div className="group relative">
                        <button
                          disabled
                          className="text-gray-600 cursor-not-allowed"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                          </svg>
                        </button>
                        <span className="absolute right-0 top-6 z-40 hidden group-hover:block bg-gray-900 border border-gray-700 rounded-xl px-3 py-2 text-xs text-gray-300 whitespace-nowrap shadow-xl">
                          حذف‌نشدنی
                        </span>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleDelete(user)}
                        disabled={deleteMutation.isPending}
                        className="text-gray-400 hover:text-red-400 transition-colors disabled:opacity-50"
                        title="حذف"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                        </svg>
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modal.type && (
        <UserModal
          mode={modal.type}
          user={modal.user}
          onClose={() => setModal({ type: null })}
          onCreate={(payload) =>
            createMutation.mutate(payload, {
              onSuccess: () => {
                showToast("success", "کاربر ایجاد شد");
                setModal({ type: null });
              },
              onError: (err) =>
                showToast(
                  "error",
                  err instanceof Error ? err.message : "خطا در ایجاد"
                ),
            })
          }
          onUpdate={(id, payload) =>
            updateMutation.mutate(
              { id, payload },
              {
                onSuccess: () => {
                  showToast("success", "کاربر به‌روزرسانی شد");
                  setModal({ type: null });
                },
                onError: (err) =>
                  showToast(
                    "error",
                    err instanceof Error ? err.message : "خطا در به‌روزرسانی"
                  ),
              }
            )
          }
          isPending={createMutation.isPending || updateMutation.isPending}
        />
      )}

      {toast && (
        <div
          className={`fixed bottom-6 left-6 rounded-2xl px-4 py-3 text-sm shadow-xl ${
            toast.type === "success"
              ? "bg-green-950 border border-green-800 text-green-400"
              : "bg-red-950 border border-red-800 text-red-400"
          }`}
        >
          {toast.msg}
        </div>
      )}
    </div>
  );
}

function UserModal({
  mode,
  user,
  onClose,
  onCreate,
  onUpdate,
  isPending,
}: {
  mode: "add" | "edit";
  user?: User | null;
  onClose: () => void;
  onCreate: (payload: { username: string; password: string; role: string }) => void;
  onUpdate: (id: string, payload: { password?: string; role?: string }) => void;
  isPending: boolean;
}) {
  const [username, setUsername] = useState(user?.username || "");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState(user?.role || "user");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (mode === "add") {
      if (!username.trim() || !password.trim()) return;
      onCreate({ username: username.trim(), password, role });
    } else if (mode === "edit" && user) {
      const payload: { password?: string; role?: string } = {};
      if (password.trim()) payload.password = password;
      if (role !== user.role) payload.role = role;
      if (Object.keys(payload).length === 0) {
        onClose();
        return;
      }
      onUpdate(user.id, payload);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      onClick={onClose}
    >
      <div
        className="bg-gray-800 rounded-3xl p-6 w-full max-w-md space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-200">
            {mode === "add" ? "افزودن کاربر جدید" : "ویرایش کاربر"}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-300"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === "add" && (
            <div className="space-y-1.5">
              <label className="block text-sm text-gray-400">نام کاربری</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="username"
                className={inputClass}
                autoFocus
              />
            </div>
          )}

          <div className="space-y-1.5">
            <label className="block text-sm text-gray-400">
              {mode === "edit" ? "رمز عبور جدید (اختیاری)" : "رمز عبور"}
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === "edit" ? "••••••••" : "password"}
              className={inputClass}
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-sm text-gray-400">نقش</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className={inputClass}
            >
              <option value="user">کاربر</option>
              <option value="admin">مدیر</option>
            </select>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="bg-gray-700 hover:bg-gray-600 text-gray-200 font-medium rounded-2xl px-5 py-2.5 text-sm transition-colors"
            >
              انصراف
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50 text-white font-medium rounded-2xl px-5 py-2.5 text-sm transition-colors"
            >
              {isPending ? "در حال ذخیره..." : mode === "add" ? "ایجاد" : "ذخیره"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
