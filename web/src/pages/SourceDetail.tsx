import { useParams } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { SourceDetail as SourceDetailType } from "../types";

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending: { label: "待处理", color: "bg-yellow-100 text-yellow-800" },
  processing: { label: "处理中", color: "bg-blue-100 text-blue-800" },
  completed: { label: "已完成", color: "bg-green-100 text-green-800" },
  failed: { label: "失败", color: "bg-red-100 text-red-800" },
};

export default function SourceDetail() {
  const { kbSlug, sourceId } = useParams();
  const { data: source, isLoading, error } = useQuery<SourceDetailType>({
    queryKey: ["source", kbSlug, sourceId],
    queryFn: () => api.get(`/kb/${kbSlug}/sources/${sourceId}`),
    enabled: !!kbSlug && !!sourceId,
  });

  if (isLoading) return <div className="p-8 text-gray-500">加载中...</div>;
  if (error || !source) return <div className="p-8 text-red-600">来源不存在</div>;

  const statusInfo = STATUS_LABELS[source.status] ?? { label: source.status, color: "bg-gray-100" };

  return (
    <div className="p-8 max-w-4xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">
        {source.title ?? "未命名来源"}
      </h1>

      <div className="flex gap-4 text-sm text-gray-500 mb-6">
        <span className={`px-2 py-1 rounded-full ${statusInfo.color}`}>{statusInfo.label}</span>
        <a
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
        >
          {source.url}
        </a>
      </div>

      {source.raw_content && (
        <div>
          <h2 className="text-lg font-semibold mb-2">原始内容</h2>
          <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-6 rounded-lg border border-gray-200 max-h-[600px] overflow-y-auto">
            {source.raw_content}
          </pre>
        </div>
      )}
    </div>
  );
}
