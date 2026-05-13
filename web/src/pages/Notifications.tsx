import { useState } from "react";
import { useParams, Link } from "react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { KnowledgeBase, Notification, NotificationList } from "../types";

export default function Notifications() {
  const { id } = useParams();
  if (id) return <NotificationDetail notificationId={id} />;
  return <NotificationList />;
}

function NotificationList() {
  const queryClient = useQueryClient();
  const [showUnread, setShowUnread] = useState(false);
  const [filterKbId, setFilterKbId] = useState<string | null>(null);

  const { data: knowledgeBases = [] } = useQuery<KnowledgeBase[]>({
    queryKey: ["knowledgeBases"],
    queryFn: () => api.get("/knowledge-bases"),
  });

  const { data, isLoading } = useQuery<NotificationList>({
    queryKey: ["notifications", showUnread, filterKbId],
    queryFn: () => {
      const params: Record<string, string> = {};
      if (showUnread) params.unread = "true";
      if (filterKbId) params.kb_id = filterKbId;
      return api.get("/notifications", params);
    },
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) => api.put(`/notifications/${id}/read`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => {
      const params = filterKbId ? `?kb_id=${filterKbId}` : "";
      return api.put(`/notifications/read-all${params}`);
    },
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
        <div className="flex gap-3 items-center">
          <select
            value={filterKbId ?? ""}
            onChange={(e) => setFilterKbId(e.target.value || null)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-md bg-white"
          >
            <option value="">全部知识库</option>
            {knowledgeBases.map((kb) => (
              <option key={kb.id} value={kb.id}>
                {kb.name}
              </option>
            ))}
          </select>
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
            className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50"
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
            <NotificationCard
              key={notif.id}
              notification={notif}
              onMarkRead={() => markReadMutation.mutate(notif.id)}
              isMarking={markReadMutation.isPending}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function NotificationCard({
  notification,
  onMarkRead,
  isMarking,
}: {
  notification: Notification;
  onMarkRead: () => void;
  isMarking: boolean;
}) {
  return (
    <div
      className={`p-4 bg-white rounded-lg border ${
        notification.is_read ? "border-gray-200" : "border-blue-300 bg-blue-50/30"
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <Link
            to={`/notifications/${notification.id}`}
            className="font-semibold text-gray-900 hover:text-blue-600"
          >
            {notification.title}
          </Link>
          {notification.summary && (
            <p className="mt-1 text-sm text-gray-600 line-clamp-2">{notification.summary}</p>
          )}
          <p className="mt-1 text-xs text-gray-400">
            {new Date(notification.created_at).toLocaleString("zh-CN")}
          </p>
        </div>
        {!notification.is_read && (
          <button
            onClick={(e) => {
              e.preventDefault();
              onMarkRead();
            }}
            disabled={isMarking}
            className="ml-4 px-2 py-1 text-xs bg-blue-50 text-blue-600 rounded hover:bg-blue-100 disabled:opacity-50"
          >
            标记已读
          </button>
        )}
      </div>
    </div>
  );
}

function NotificationDetail({ notificationId }: { notificationId: string }) {
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
