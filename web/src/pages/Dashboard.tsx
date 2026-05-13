import { Link } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { KnowledgeBase, Notification } from "../types";

export default function Dashboard() {
  const { data: knowledgeBases = [], isLoading } = useQuery<KnowledgeBase[]>({
    queryKey: ["knowledgeBases"],
    queryFn: () => api.get("/knowledge-bases"),
  });

  const { data: notificationsData } = useQuery<{
    items: Notification[];
    unread_count: number;
  }>({
    queryKey: ["notifications", { limit: 5 }],
    queryFn: () => api.get("/notifications", { limit: 5 }),
  });

  const totalSources = knowledgeBases.reduce((sum, kb) => sum + kb.source_count, 0);
  const totalWikiPages = knowledgeBases.reduce((sum, kb) => sum + kb.wiki_page_count, 0);
  const unreadCount = notificationsData?.unread_count ?? 0;

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">仪表盘</h1>

      {isLoading ? (
        <p className="text-gray-500">加载中...</p>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white p-5 rounded-lg border border-gray-200">
              <p className="text-sm text-gray-500">知识库</p>
              <p className="text-2xl font-bold text-gray-900">{knowledgeBases.length}</p>
            </div>
            <div className="bg-white p-5 rounded-lg border border-gray-200">
              <p className="text-sm text-gray-500">来源文档</p>
              <p className="text-2xl font-bold text-gray-900">{totalSources}</p>
            </div>
            <div className="bg-white p-5 rounded-lg border border-gray-200">
              <p className="text-sm text-gray-500">Wiki 页面</p>
              <p className="text-2xl font-bold text-gray-900">{totalWikiPages}</p>
            </div>
            <Link
              to="/notifications"
              className="bg-white p-5 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
            >
              <p className="text-sm text-gray-500">未读通知</p>
              <p className="text-2xl font-bold text-gray-900">
                {unreadCount > 0 ? unreadCount : 0}
              </p>
            </Link>
          </div>

          {knowledgeBases.length === 0 ? (
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
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">知识库</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {knowledgeBases.map((kb) => (
                    <Link
                      key={kb.id}
                      to={`/kb/${kb.slug}`}
                      className="block p-5 bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-gray-900">{kb.name}</h3>
                        {kb.is_system && (
                          <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded">
                            系统
                          </span>
                        )}
                      </div>
                      {kb.description && (
                        <p className="mt-1 text-sm text-gray-600 line-clamp-2">{kb.description}</p>
                      )}
                      <div className="mt-3 flex gap-4 text-sm text-gray-500">
                        <span>{kb.source_count} 来源</span>
                        <span>{kb.wiki_page_count} Wiki</span>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>

              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-4">最近通知</h2>
                {notificationsData?.items && notificationsData.items.length > 0 ? (
                  <div className="space-y-3">
                    {notificationsData.items.map((n) => (
                      <Link
                        key={n.id}
                        to="/notifications"
                        className={`block p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md ${
                          !n.is_read ? "border-l-4 border-l-blue-500" : ""
                        }`}
                      >
                        <p className="text-sm font-medium text-gray-900 truncate">{n.title}</p>
                        {n.summary && (
                          <p className="mt-1 text-xs text-gray-500 line-clamp-2">{n.summary}</p>
                        )}
                        <p className="mt-2 text-xs text-gray-400">
                          {new Date(n.created_at).toLocaleDateString()}
                        </p>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">暂无通知</p>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
