import { useParams, Link } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { WikiPageListItem } from "../types";

const TYPE_LABELS: Record<string, string> = {
  source: "来源",
  entity: "实体",
  concept: "概念",
  comparison: "对比",
  tool: "工具",
  tool_category: "工具分类",
};

export default function WikiBrowser() {
  const { kbSlug } = useParams();
  const { data: pages = [], isLoading } = useQuery<WikiPageListItem[]>({
    queryKey: ["wikiPages", kbSlug],
    queryFn: () => api.get(`/kb/${kbSlug}/wiki`),
    enabled: !!kbSlug,
  });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Wiki 页面</h1>
        <Link
          to={`/kb/${kbSlug}/wiki/graph`}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          图谱视图
        </Link>
      </div>

      {isLoading ? (
        <p className="text-gray-500">加载中...</p>
      ) : pages.length === 0 ? (
        <p className="text-gray-500">暂无 Wiki 页面。提交来源后系统会自动生成。</p>
      ) : (
        <div className="space-y-3">
          {pages.map((page) => (
            <Link
              key={page.id}
              to={`/kb/${kbSlug}/wiki/${page.slug}`}
              className="block p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-gray-900">{page.title}</h3>
                <span className="text-xs px-2 py-1 bg-gray-100 rounded-full">
                  {TYPE_LABELS[page.page_type] ?? page.page_type}
                </span>
              </div>
              <p className="text-sm text-gray-500 mt-1">{page.slug}</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
