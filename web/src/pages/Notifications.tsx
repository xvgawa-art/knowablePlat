import { useState } from "react";
import { useParams } from "react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import NotificationDetail from "../components/notification/NotificationDetail";
import Pagination from "../components/Pagination";
import { usePagination } from "../hooks/usePagination";
import { useBatchSelect } from "../hooks/useBatchSelect";
import type { KnowledgeBase, Notification, NotificationList } from "../types";

export default function Notifications() {
  const { id } = useParams();
  if (id) return <NotificationDetail notificationId={id} />;
  return <NotificationListPage />;
}

function NotificationListPage() {
  const queryClient = useQueryClient();
  const [showUnread, setShowUnread] = useState(false);
  const [filterKbId, setFilterKbId] = useState<string | null>(null);
  const pagination = usePagination(20);
  const batch = useBatchSelect();

  const { data: knowledgeBases = [] } = useQuery<KnowledgeBase[]>({
    queryKey: ["knowledgeBases"],
    queryFn: () => api.get("/knowledge-bases"),
  });

  const { data, isLoading } = useQuery<NotificationList>({
    queryKey: ["notifications", showUnread, filterKbId, pagination.offset, pagination.pageSize],
    queryFn: () => {
      const params: Record<string, string | number> = { offset: pagination.offset, limit: pagination.pageSize };
      if (showUnread) params.unread = "true";
      if (filterKbId) params.kb_id = filterKbId;
      return api.get("/notifications", params);
    },
  });

  const notifications = data?.items ?? [];
  const total = data?.total ?? 0;
  const allIds = notifications.map((n) => n.id);

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

  const batchDeleteMutation = useMutation({
    mutationFn: (ids: string[]) => api.post("/notifications/batch-delete", { ids }),
    onSuccess: () => {
      batch.clearAll();
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  function handleBatchDelete() {
    if (!confirm(`确定删除选中的 ${batch.selectedIds.size} 项？`)) return;
    batchDeleteMutation.mutate(Array.from(batch.selectedIds));
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          通知中心
          {data && data.unread_count > 0 && (
            <span className="ml-2 px-2 py-0.5 text-sm bg-red-100 text-red-700 rounded-full">{data.unread_count} 未读</span>
          )}
        </h1>
        <div className="flex gap-3 items-center">
          {batch.selectedIds.size > 0 && (
            <button onClick={handleBatchDelete} disabled={batchDeleteMutation.isPending}
              className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50">
              删除选中 ({batch.selectedIds.size})
            </button>
          )}
          <select value={filterKbId ?? ""} onChange={(e) => { setFilterKbId(e.target.value || null); pagination.reset(); batch.clearAll(); }}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-md bg-white">
            <option value="">全部知识库</option>
            {knowledgeBases.map((kb) => <option key={kb.id} value={kb.id}>{kb.name}</option>)}
          </select>
          <button onClick={() => { setShowUnread(!showUnread); pagination.reset(); batch.clearAll(); }}
            className={`px-3 py-1.5 text-sm rounded-md ${showUnread ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"}`}>
            {showUnread ? "显示全部" : "仅未读"}</button>
          <button onClick={() => markAllReadMutation.mutate()} disabled={markAllReadMutation.isPending}
            className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50">
            全部已读</button>
        </div>
      </div>

      {isLoading ? (
        <p className="text-gray-500">加载中...</p>
      ) : notifications.length === 0 ? (
        <p className="text-gray-500">暂无通知</p>
      ) : (
        <>
          <div className="mb-2 flex items-center gap-2">
            <input type="checkbox"
              checked={allIds.length > 0 && allIds.every((id) => batch.isSelected(id))}
              onChange={() => (allIds.every((id) => batch.isSelected(id)) ? batch.clearAll() : batch.selectAll(allIds))}
              className="rounded border-gray-300" />
            <span className="text-xs text-gray-500">全选</span>
          </div>
          <div className="space-y-3">
            {notifications.map((notif) => (
              <NotificationCard key={notif.id} notification={notif} isSelected={batch.isSelected(notif.id)}
                onToggle={() => batch.toggle(notif.id)} onMarkRead={() => markReadMutation.mutate(notif.id)} />
            ))}
          </div>
          <Pagination page={pagination.page} pageSize={pagination.pageSize} total={total} onPageChange={pagination.setPage} />
        </>
      )}
    </div>
  );
}

function NotificationCard({ notification, isSelected, onToggle, onMarkRead }: {
  notification: Notification; isSelected: boolean; onToggle: () => void; onMarkRead: () => void;
}) {
  return (
    <div className={`flex items-center gap-3 p-4 bg-white rounded-lg border ${
      notification.is_read ? "border-gray-200" : "border-blue-300 bg-blue-50/30"}`}>
      <input type="checkbox" checked={isSelected} onChange={onToggle} className="rounded border-gray-300" />
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <a href={`/notifications/${notification.id}`} className="font-semibold text-gray-900 hover:text-blue-600">
              {notification.title}</a>
            {notification.summary && <p className="mt-1 text-sm text-gray-600 line-clamp-2">{notification.summary}</p>}
            <p className="mt-1 text-xs text-gray-400">{new Date(notification.created_at).toLocaleString("zh-CN")}</p>
          </div>
          {!notification.is_read && (
            <button onClick={(e) => { e.preventDefault(); onMarkRead(); }}
              className="ml-4 px-2 py-1 text-xs bg-blue-50 text-blue-600 rounded hover:bg-blue-100">标记已读</button>
          )}
        </div>
      </div>
    </div>
  );
}
