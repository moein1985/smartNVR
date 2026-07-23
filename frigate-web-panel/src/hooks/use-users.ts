"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import {
  fetchUsers,
  createUser,
  updateUser,
  deleteUser,
  type User,
  type CreateUserPayload,
  type UpdateUserPayload,
} from "@/lib/users-api";

export function useUsers() {
  return useQuery<User[]>({
    queryKey: ["users"],
    queryFn: fetchUsers,
    staleTime: 30_000,
  });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateUserPayload) => createUser(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (err) => {
      console.error("[Users] Create failed:", err);
    },
  });
}

export function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: string;
      payload: UpdateUserPayload;
    }) => updateUser(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (err) => {
      console.error("[Users] Update failed:", err);
    },
  });
}

export function useDeleteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteUser(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (err) => {
      console.error("[Users] Delete failed:", err);
    },
  });
}
