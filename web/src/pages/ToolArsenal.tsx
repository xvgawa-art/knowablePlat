import { Link } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { PaginatedResponse, WikiPageListItem } from "../types";

const TYPE_LABELS: Record<string, { label: string; color: string }> = {
  tool: { label: "工具", color: "bg-blue-100 text-blue-700" },
  tool_category: { label: "分类", color: "bg-purple-100 text-purple-700" },
  source: { label: "来源", color: "bg-green-100 text-green-700" },
};

export default function ToolArsenal() {
  const { data: wikiData, isLoading } = useQuery<PaginatedResponse<WikiPageListItem>>({
    queryKey: ["wikiPages", "tool-arsenal"],
    queryFn: () => api.get("/kb/tool-arsenal/wiki"),
  });
  const pages = wikiData?.items ?? [];

  const categories = pages.filter((p) => p.page_type === "tool_category");
  const tools = pages.filter((p) => p.page_type === "tool");

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold text-gray-900">工具装备库</h1>
          {!isLoading && pages.length > 0 && (
            <span className="text-sm text-gray-500">
              {categories.length} 个分类 · {tools.length} 个工具
            </span>
          )}
        </div>
        <Link
          to="/kb/tool-arsenal/sources/submit"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
        >
          提交工具 URL
        </Link>
      </div>

      {isLoading ? (
        <p className="text-gray-500">加载中...</p>
      ) : pages.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-2">工具装备库暂无内容</p>
          <p className="text-sm text-gray-400">
            向工具装备库提交工具 URL，系统会自动提取信息并归类
          </p>
        </div>
      ) : (
        <>
          {categories.length > 0 && (
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-gray-800 mb-3">工具分类</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {categories.map((cat) => (
                  <Link
                    key={cat.id}
                    to={`/kb/tool-arsenal/wiki/${cat.slug}`}
                    className="block p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md"
                  >
                    <h3 className="font-semibold text-gray-900">{cat.title}</h3>
                    <p className="text-sm text-gray-400 mt-1">{new Date(cat.created_at).toLocaleDateString("zh-CN")}</p>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {tools.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-gray-800 mb-3">全部工具</h2>
              <div className="space-y-3">
                {tools.map((tool) => {
                  const typeInfo = TYPE_LABELS[tool.page_type] ?? {
                    label: tool.page_type,
                    color: "bg-gray-100",
                  };
                  return (
                    <Link
                      key={tool.id}
                      to={`/kb/tool-arsenal/wiki/${tool.slug}`}
                      className="block p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md"
                    >
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-gray-900">{tool.title}</h3>
                        <span className={`text-xs px-2 py-1 rounded-full ${typeInfo.color}`}>
                          {typeInfo.label}
                        </span>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
