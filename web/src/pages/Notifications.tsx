import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { NotificationList } from "../types";

export default function Notifications() {
  const queryClient = useQueryClient();
  const [showUnread, setShowUnread] = useState(false);

  const { data, isLoading } = useQuery<NotificationList>({
    queryKey: ["notifications", showUnread],
    queryFn: () => api.get(`/notifications${showUnread ? "?unread=true" : ""}`),
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) => api.put(`/notifications/${id}/read`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => api.put("/notifications/read-all"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const notifications = data?.items ?? [];

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          通知中心
          {data && data.unread_count > 0 && (
            <span className="ml-2 px-2 py-0.5 text-sm bg-red-100 text-red-700 rounded-full">
              {data.unread_count} 未读
            </span>
          )}
        </h1>
        <div className="flex gap-3">
          <button
            onClick={() => setShowUnread(!showUnread)}
            className={`px-3 py-1.5 text-sm rounded-md ${
              showUnread ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            {showUnread ? "显示全部" : "仅未读"}
          </button>
          <button
            onClick={() => markAllReadMutation.mutate()}
            disabled={markAllReadMutation.isPending}
            className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            全部已读
          </button>
        </div>
      </div>

      {isLoading ? (
        <p className="text-gray-500">加载中...</p>
      ) : notifications.length === 0 ? (
        <p className="text-gray-500">暂无通知</p>
      ) : (
        <div className="space-y-3">
          {notifications.map((notif) => (
            <div
              key={notif.id}
              className={`p-4 bg-white rounded-lg border ${
                notif.is_read ? "border-gray-200" : "border-blue-300 bg-blue-50/30"
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{notif.title}</h3>
                  {notif.summary && (
                    <p className="mt-2 text-sm text-gray-600">{notif.summary}</p>
                  )}
                  {notif.related_points && Array.isArray(notif.related_points) && notif.related_points.length > 0 && (
                    <div className="mt-3 space-y-1">
                      <p className="text-xs font-medium text-gray-500">关联知识点：</p>
                      {notif.related_points.map((point, i) => {
                        if (typeof point === "object" && point !== null && "wiki_page_slug" in point) {
                          const p = point as { wiki_page_slug?: string; title?: string; relation_desc?: string };
                          return (
                            <a
                              key={i}
                              href={`/kb/tool-arsenal/wiki/${p.wiki_page_slug}`}
                              className="block text-sm text-blue-600 hover:underline"
                            >
                              {p.title ?? p.wiki_page_slug} — {p.relation_desc}
                            </a>
                          );
                        }
                        return null;
                      })}
                    </div>
                  )}
                  <p className="mt-2 text-xs text-gray-400">
                    {new Date(notif.created_at).toLocaleString("zh-CN")}
                  </p>
                </div>
                {!notif.is_read && (
                  <button
                    onClick={() => markReadMutation.mutate(notif.id)}
                    className="ml-4 px-2 py-1 text-xs bg-blue-50 text-blue-600 rounded hover:bg-blue-100"
                  >
                    标记已读
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
