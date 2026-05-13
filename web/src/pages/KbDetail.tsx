import { useParams, Link } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { KnowledgeBase, Source, WikiPageListItem } from "../types";

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending: { label: "待处理", color: "bg-yellow-100 text-yellow-800" },
  processing: { label: "处理中", color: "bg-blue-100 text-blue-800" },
  completed: { label: "已完成", color: "bg-green-100 text-green-800" },
  failed: { label: "失败", color: "bg-red-100 text-red-800" },
};

const TYPE_COLORS: Record<string, string> = {
  source: "bg-blue-100 text-blue-700",
  entity: "bg-green-100 text-green-700",
  concept: "bg-purple-100 text-purple-700",
  comparison: "bg-yellow-100 text-yellow-700",
  tool: "bg-red-100 text-red-700",
  tool_category: "bg-pink-100 text-pink-700",
};

const TYPE_LABELS: Record<string, string> = {
  source: "来源",
  entity: "实体",
  concept: "概念",
  comparison: "对比",
  tool: "工具",
  tool_category: "工具分类",
};

export default function KbDetail() {
  const { kbSlug } = useParams();
  const { data: kb, isLoading, error } = useQuery<KnowledgeBase>({
    queryKey: ["kb", kbSlug],
    queryFn: () => api.get(`/knowledge-bases/${kbSlug}`),
    enabled: !!kbSlug,
  });

  const { data: sources = [] } = useQuery<Source[]>({
    queryKey: ["sources", kbSlug],
    queryFn: () => api.get(`/kb/${kbSlug}/sources`, { limit: 5 }),
    enabled: !!kbSlug,
  });

  const { data: wikiPages = [] } = useQuery<WikiPageListItem[]>({
    queryKey: ["wiki", kbSlug],
    queryFn: () => api.get(`/kb/${kbSlug}/wiki`, { limit: 5 }),
    enabled: !!kbSlug,
  });

  if (isLoading) return <div className="p-8 text-gray-500">加载中...</div>;
  if (error || !kb) return <div className="p-8 text-red-600">知识库不存在</div>;

  const processingCount = sources.filter(
    (s) => s.status === "processing" || s.status === "pending"
  ).length;

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{kb.name}</h1>
          {kb.description && <p className="mt-1 text-gray-600">{kb.description}</p>}
        </div>
        <Link
          to={`/kb/${kbSlug}/sources/submit`}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          提交 URL
        </Link>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-500">来源文档</p>
          <p className="text-xl font-bold text-gray-900">{kb.source_count}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-500">Wiki 页面</p>
          <p className="text-xl font-bold text-gray-900">{kb.wiki_page_count}</p>
        </div>
        <Link
          to={`/kb/${kbSlug}/wiki`}
          className="bg-white p-4 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
        >
          <p className="text-sm text-gray-500">浏览 Wiki</p>
          <p className="text-xl font-bold text-blue-600">进入 &rarr;</p>
        </Link>
        <Link
          to={`/kb/${kbSlug}/chat`}
          className="bg-white p-4 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
        >
          <p className="text-sm text-gray-500">对话查询</p>
          <p className="text-xl font-bold text-blue-600">提问 &rarr;</p>
        </Link>
      </div>

      {processingCount > 0 && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200 text-sm text-blue-700">
          {processingCount} 个来源正在处理中，结果将自动更新
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-gray-900">最近来源</h2>
            <Link to={`/kb/${kbSlug}/sources`} className="text-sm text-blue-600 hover:underline">
              查看全部
            </Link>
          </div>
          {sources.length === 0 ? (
            <p className="text-sm text-gray-500 py-4">暂无来源，点击上方按钮提交 URL</p>
          ) : (
            <div className="space-y-2">
              {sources.map((source) => {
                const statusInfo = STATUS_LABELS[source.status] ?? {
                  label: source.status,
                  color: "bg-gray-100",
                };
                return (
                  <Link
                    key={source.id}
                    to={`/kb/${kbSlug}/sources/${source.id}`}
                    className="block p-3 bg-white rounded-lg border border-gray-200 hover:shadow-sm"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-900 truncate flex-1 mr-2">
                        {source.title ?? source.url}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${statusInfo.color}`}>
                        {statusInfo.label}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1 truncate">{source.url}</p>
                  </Link>
                );
              })}
            </div>
          )}
        </div>

        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-gray-900">最近 Wiki 页面</h2>
            <Link to={`/kb/${kbSlug}/wiki`} className="text-sm text-blue-600 hover:underline">
              查看全部
            </Link>
          </div>
          {wikiPages.length === 0 ? (
            <p className="text-sm text-gray-500 py-4">暂无 Wiki 页面，提交来源后将自动生成</p>
          ) : (
            <div className="space-y-2">
              {wikiPages.map((page) => (
                <Link
                  key={page.id}
                  to={`/kb/${kbSlug}/wiki/${page.slug}`}
                  className="block p-3 bg-white rounded-lg border border-gray-200 hover:shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-900">{page.title}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${TYPE_COLORS[page.page_type] ?? "bg-gray-100 text-gray-600"}`}>
                      {TYPE_LABELS[page.page_type] ?? page.page_type}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
