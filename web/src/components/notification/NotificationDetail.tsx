import { Link } from "react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import type { Notification } from "../../types";

export default function NotificationDetail({ notificationId }: { notificationId: string }) {
  const queryClient = useQueryClient();

  const { data: notification, isLoading } = useQuery<Notification>({
    queryKey: ["notification", notificationId],
    queryFn: () => api.get(`/notifications/${notificationId}`),
  });

  const markReadMutation = useMutation({
    mutationFn: () => api.put(`/notifications/${notificationId}/read`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notification", notificationId] }),
  });

  if (isLoading) return <div className="p-8 text-gray-500">加载中...</div>;
  if (!notification) return <div className="p-8 text-red-600">通知不存在</div>;

  const relatedPoints = Array.isArray(notification.related_points) ? notification.related_points : [];

  return (
    <div className="p-8 max-w-4xl">
      <Link to="/notifications" className="text-sm text-blue-600 hover:text-blue-800">
        返回通知列表
      </Link>

      <div className="mt-4 bg-white p-6 rounded-lg border border-gray-200">
        <div className="flex items-start justify-between">
          <h1 className="text-xl font-bold text-gray-900">{notification.title}</h1>
          {!notification.is_read && (
            <button
              onClick={() => markReadMutation.mutate()}
              disabled={markReadMutation.isPending}
              className="px-3 py-1 text-sm bg-blue-50 text-blue-600 rounded hover:bg-blue-100 disabled:opacity-50"
            >
              标记已读
            </button>
          )}
        </div>

        {notification.summary && <p className="mt-4 text-gray-700 leading-relaxed">{notification.summary}</p>}

        {relatedPoints.length > 0 && (
          <div className="mt-6">
            <h2 className="text-sm font-medium text-gray-500 mb-3">关联知识点</h2>
            <div className="space-y-2">
              {relatedPoints.map((point, i) => {
                if (typeof point === "object" && point !== null && "wiki_page_slug" in point) {
                  const p = point as { wiki_page_slug?: string; title?: string; relation_desc?: string };
                  const kbSlug = notification.kb_slug;
                  return kbSlug && p.wiki_page_slug ? (
                    <Link
                      key={i}
                      to={`/kb/${kbSlug}/wiki/${p.wiki_page_slug}`}
                      className="block px-3 py-2 text-sm bg-gray-50 rounded-md hover:bg-blue-50 text-blue-600"
                    >
                      {p.title ?? p.wiki_page_slug}
                      {p.relation_desc ? <span className="text-gray-500 ml-2">— {p.relation_desc}</span> : ""}
                    </Link>
                  ) : (
                    <p key={i} className="px-3 py-2 text-sm text-gray-500 bg-gray-50 rounded-md">
                      {p.title ?? "未知页面"}
                    </p>
                  );
                }
                return null;
              })}
            </div>
          </div>
        )}

        <p className="mt-4 text-xs text-gray-400">
          {new Date(notification.created_at).toLocaleString("zh-CN")}
        </p>
      </div>
    </div>
  );
}
