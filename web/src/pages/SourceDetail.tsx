import { useParams, Link } from "react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";
import type { PaginatedResponse, SourceDetail as SourceDetailType, WikiPageListItem } from "../types";

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending: { label: "待处理", color: "bg-yellow-100 text-yellow-800" },
  processing: { label: "处理中", color: "bg-blue-100 text-blue-800" },
  completed: { label: "已完成", color: "bg-green-100 text-green-800" },
  failed: { label: "失败", color: "bg-red-100 text-red-800" },
};

export default function SourceDetail() {
  const { kbSlug, sourceId } = useParams();
  const queryClient = useQueryClient();
  const [retrying, setRetrying] = useState(false);

  const { data: source, isLoading, error } = useQuery<SourceDetailType>({
    queryKey: ["source", kbSlug, sourceId],
    queryFn: () => api.get(`/kb/${kbSlug}/sources/${sourceId}`),
    enabled: !!kbSlug && !!sourceId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === "processing" || data?.status === "pending") {
        return 5000;
      }
      return false;
    },
  });

  const retryMutation = useMutation({
    mutationFn: () => api.post(`/kb/${kbSlug}/sources/${sourceId}/retry`, {}),
    onSettled: () => {
      setRetrying(false);
      queryClient.invalidateQueries({ queryKey: ["source", kbSlug, sourceId] });
    },
  });

  const { data: wikiData } = useQuery<PaginatedResponse<WikiPageListItem>>({
    queryKey: ["wikiBySource", kbSlug, sourceId],
    queryFn: () => api.get(`/kb/${kbSlug}/wiki`, { source_id: sourceId! }),
    enabled: !!kbSlug && !!sourceId,
  });
  const wikiPages = wikiData?.items ?? [];

  if (isLoading) return <div className="p-8 text-gray-500">加载中...</div>;
  if (error || !source) return <div className="p-8 text-red-600">来源不存在</div>;

  const statusInfo = STATUS_LABELS[source.status] ?? { label: source.status, color: "bg-gray-100" };

  return (
    <div className="p-8 max-w-4xl">
      <div className="mb-4">
        <Link to={`/kb/${kbSlug}/sources`} className="text-sm text-blue-600 hover:text-blue-800">
          ← 返回来源列表
        </Link>
      </div>

      <h1 className="text-2xl font-bold text-gray-900 mb-4">
        {source.title ?? "未命名来源"}
      </h1>

      <div className="flex items-center gap-4 text-sm text-gray-500 mb-6">
        <span className={`px-2 py-1 rounded-full ${statusInfo.color}`}>{statusInfo.label}</span>
        <a
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
        >
          {source.url}
        </a>
        <span>{new Date(source.created_at).toLocaleString("zh-CN")}</span>
        {source.token_usage > 0 && (
          <span>Token 消耗: {source.token_usage.toLocaleString()}</span>
        )}
        {source.status === "failed" && (
          <button
            onClick={() => { setRetrying(true); retryMutation.mutate(); }}
            disabled={retrying}
            className="px-3 py-1 text-sm rounded bg-orange-100 text-orange-700 hover:bg-orange-200 disabled:opacity-50"
          >
            {retrying ? "重试中..." : "重试摄入"}
          </button>
        )}
      </div>

      {source.raw_content && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-2">原始内容</h2>
          <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-6 rounded-lg border border-gray-200 max-h-[600px] overflow-y-auto">
            {source.raw_content}
          </pre>
        </div>
      )}

      {wikiPages.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3">生成的 Wiki 页面</h2>
          <div className="space-y-2">
            {wikiPages.map((page) => (
              <Link
                key={page.id}
                to={`/kb/${kbSlug}/wiki/${page.slug}`}
                className="block p-3 bg-white rounded-lg border border-gray-200 hover:shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900">{page.title}</span>
                  <span className="text-xs text-gray-400">{page.page_type}</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
