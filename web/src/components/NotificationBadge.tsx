import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { api } from "../api/client";

export default function NotificationBadge() {
  const navigate = useNavigate();
  const { data } = useQuery<{ unread_count: number }>({
    queryKey: ["unreadCount"],
    queryFn: () => api.get("/notifications/unread-count"),
    refetchInterval: 30_000,
  });

  const count = data?.unread_count ?? 0;

  return (
    <button
      onClick={() => navigate("/notifications")}
      className="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
      title="通知"
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
        />
      </svg>
      {count > 0 && (
        <span className="absolute -top-1 -right-1 px-1.5 py-0.5 text-xs font-bold text-white bg-red-500 rounded-full min-w-[18px] text-center">
          {count > 99 ? "99+" : count}
        </span>
      )}
    </button>
  );
}
