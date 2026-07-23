"use client";

import { useState } from "react";
import { useHardware } from "@/hooks/use-hardware";
import { useContainers, useAssignResources } from "@/hooks/use-containers";
import { HardwareOverview } from "@/components/hardware-overview";
import { ServiceBindingTable } from "@/components/service-binding-table";

export default function OrchestratorPage() {
  const { data: hardware, isError: hwError } = useHardware();
  const { data: containerData, isLoading: ctrLoading } = useContainers(true);
  const assignMutation = useAssignResources();
  const [toast, setToast] = useState<"idle" | "success" | "error">("idle");

  const containers = containerData?.containers || [];

  const handleApply = (assignments: Parameters<typeof assignMutation.mutate>[0]) => {
    assignMutation.mutate(assignments, {
      onSuccess: () => {
        setToast("success");
        setTimeout(() => setToast("idle"), 3000);
      },
      onError: () => {
        setToast("error");
        setTimeout(() => setToast("idle"), 3000);
      },
    });
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div>
        <h1 className="text-xl font-bold text-gray-200">ارکستریتور سخت‌افزار</h1>
        <p className="text-sm text-gray-500 mt-1">
          مدیریت منابع سخت‌افزاری و تخصیص به کانتینرها
        </p>
      </div>

      {hwError && (
        <div className="bg-red-950/30 border border-red-800 rounded-2xl px-4 py-3 text-red-400 text-sm">
          خطا در دریافت اطلاعات سخت‌افزار
        </div>
      )}

      <div>
        <h2 className="text-sm font-medium text-gray-400 mb-3">نمای کلی سخت‌افزار</h2>
        <HardwareOverview data={hardware} />
      </div>

      <div>
        <h2 className="text-sm font-medium text-gray-400 mb-3">تخصیص منابع به سرویس‌ها</h2>
        {ctrLoading ? (
          <div className="bg-gray-800 rounded-3xl p-12 text-center text-gray-500 text-sm">
            در حال بارگذاری کانتینرها...
          </div>
        ) : (
          <ServiceBindingTable
            containers={containers}
            hardware={hardware}
            onApply={handleApply}
            isApplying={assignMutation.isPending}
          />
        )}
      </div>

      {toast === "success" && (
        <div className="fixed bottom-6 left-6 bg-green-950 border border-green-800 rounded-2xl px-4 py-3 text-green-400 text-sm shadow-xl">
          تغییرات با موفقیت اعمال شد
        </div>
      )}
      {toast === "error" && (
        <div className="fixed bottom-6 left-6 bg-red-950 border border-red-800 rounded-2xl px-4 py-3 text-red-400 text-sm shadow-xl">
          خطا در اعمال تغییرات
        </div>
      )}
    </div>
  );
}
