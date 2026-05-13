import { useParams, Link } from "react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";
import type { Source } from "../types";

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending: { label: "待处理", color: "bg-yellow-100 text-yellow-800" },
  processing: { label: "处理中", color: "bg-blue-100 text-blue-800" },
  completed: { label: "已完成", color: "bg-green-100 text-green-800" },
  failed: { label: "失败", color: "bg-red-100 text-red-800" },
};

export default function Sources() {
  const { kbSlug } = useParams();
  const queryClient = useQueryClient();
  const [retryingId, setRetryingId] = useState<string | null>(null);

  const { data: sources = [], isLoading } = useQuery<Source[]>({
    queryKey: ["sources", kbSlug],
    queryFn: () => api.get(`/kb/${kbSlug}/sources`),
    enabled: !!kbSlug,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.some((s) => s.status === "processing" || s.status === "pending")) {
        return 5000;
      }
      return false;
    },
  });

  const retryMutation = useMutation({
    mutationFn: (sourceId: string) => api.post(`/kb/${kbSlug}/sources/${sourceId}/retry`, {}),
    onSettled: () => {
      setRetryingId(null);
      queryClient.invalidateQueries({ queryKey: ["sources", kbSlug] });
    },
  });

  const handleRetry = (e: React.MouseEvent, sourceId: string) => {
    e.preventDefault();
    e.stopPropagation();
    setRetryingId(sourceId);
    retryMutation.mutate(sourceId);
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">来源列表</h1>
        <Link
          to={`/kb/${kbSlug}/sources/submit`}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          提交 URL
        </Link>
      </div>

      {isLoading ? (
        <p className="text-gray-500">加载中...</p>
      ) : sources.length === 0 ? (
        <p className="text-gray-500">暂无来源。点击上方按钮提交 URL。</p>
      ) : (
        <div className="space-y-3">
          {sources.map((source) => {
            const statusInfo = STATUS_LABELS[source.status] ?? { label: source.status, color: "bg-gray-100" };
            return (
              <Link
                key={source.id}
                to={`/kb/${kbSlug}/sources/${source.id}`}
                className="block p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md"
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-gray-900">
                    {source.title ?? source.url}
                  </h3>
                  <div className="flex items-center gap-2">
                    {source.status === "failed" && (
                      <button
                        onClick={(e) => handleRetry(e, source.id)}
                        disabled={retryingId === source.id}
                        className="text-xs px-2 py-1 rounded bg-orange-100 text-orange-700 hover:bg-orange-200 disabled:opacity-50"
                      >
                        {retryingId === source.id ? "重试中..." : "重试"}
                      </button>
                    )}
                    <span className={`text-xs px-2 py-1 rounded-full ${statusInfo.color}`}>
                      {statusInfo.label}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-500 mt-1 truncate">{source.url}</p>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
