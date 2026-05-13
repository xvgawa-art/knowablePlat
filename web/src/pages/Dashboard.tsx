import { Link } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { KnowledgeBase } from "../types";

export default function Dashboard() {
  const { data: knowledgeBases = [], isLoading } = useQuery<KnowledgeBase[]>({
    queryKey: ["knowledgeBases"],
    queryFn: () => api.get("/knowledge-bases"),
  });

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">仪表盘</h1>

      {isLoading ? (
        <p className="text-gray-500">加载中...</p>
      ) : knowledgeBases.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">还没有知识库</p>
          <Link
            to="/kb"
            className="inline-block px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            创建知识库
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {knowledgeBases.map((kb) => (
            <Link
              key={kb.id}
              to={`/kb/${kb.slug}`}
              className="block p-6 bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
            >
              <h2 className="text-lg font-semibold text-gray-900">{kb.name}</h2>
              {kb.description && (
                <p className="mt-2 text-sm text-gray-600">{kb.description}</p>
              )}
              <div className="mt-4 flex gap-4 text-sm text-gray-500">
                <span>{kb.source_count} 来源</span>
                <span>{kb.wiki_page_count} Wiki</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
