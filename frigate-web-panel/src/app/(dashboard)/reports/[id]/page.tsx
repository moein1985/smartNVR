"use client";

import { useParams } from "next/navigation";
import { useReportRule } from "@/hooks/use-report-rules";
import { ReportRuleForm } from "@/components/report-rule-form";

export default function ReportEditorPage() {
  const params = useParams();
  const id = params.id as string;
  const isNew = id === "new";
  const { data: rule, isLoading, isError } = useReportRule(isNew ? null : id);

  if (isNew) {
    return <ReportRuleForm key="new" rule={null} />;
  }

  if (isLoading) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <div className="text-gray-500 text-sm">در حال بارگذاری قانون...</div>
      </div>
    );
  }

  if (isError || !rule) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <div className="text-red-400 text-sm">قانون یافت نشد</div>
      </div>
    );
  }

  return <ReportRuleForm key={rule.id} rule={rule} />;
}
