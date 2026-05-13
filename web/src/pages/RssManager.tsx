import { useState } from "react";
import { useParams } from "react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

interface RssFeed {
  id: string;
  name: string;
  url: string;
  feed_type: string;
  is_active: boolean;
  poll_interval: number;
  last_fetched_at: string | null;
  last_fetch_status: string | null;
  last_error: string | null;
  total_fetched: number;
}

interface RssEntry {
  id: string;
  guid: string;
  url: string;
  title: string | null;
  status: string;
  published_at: string | null;
  created_at: string;
}

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  success: { label: "成功", color: "bg-green-100 text-green-700" },
  partial: { label: "部分成功", color: "bg-yellow-100 text-yellow-700" },
  failed: { label: "失败", color: "bg-red-100 text-red-700" },
};

const ENTRY_STATUS: Record<string, { label: string; color: string }> = {
  new: { label: "新", color: "bg-blue-100 text-blue-700" },
  ingesting: { label: "处理中", color: "bg-yellow-100 text-yellow-700" },
  completed: { label: "已完成", color: "bg-green-100 text-green-700" },
  filtered: { label: "已过滤", color: "bg-gray-100 text-gray-700" },
  failed: { label: "失败", color: "bg-red-100 text-red-700" },
};

export default function RssManager() {
  const { kbSlug } = useParams();
  const queryClient = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const [name, setName] = useState("");
  const [feedUrl, setFeedUrl] = useState("");
  const [expandedFeed, setExpandedFeed] = useState<string | null>(null);

  const { data: feeds = [], isLoading } = useQuery<RssFeed[]>({
    queryKey: ["rssFeeds", kbSlug],
    queryFn: () => api.get(`/kb/${kbSlug}/rss`),
    enabled: !!kbSlug,
  });

  const { data: entries = [] } = useQuery<RssEntry[]>({
    queryKey: ["rssEntries", expandedFeed],
    queryFn: () => api.get(`/kb/${kbSlug}/rss/${expandedFeed}/entries`),
    enabled: !!kbSlug && !!expandedFeed,
  });

  const addMutation = useMutation({
    mutationFn: () => api.post(`/kb/${kbSlug}/rss`, { name, url: feedUrl }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rssFeeds", kbSlug] });
      setName("");
      setFeedUrl("");
      setShowAdd(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (feedId: string) => api.del(`/kb/${kbSlug}/rss/${feedId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["rssFeeds", kbSlug] }),
  });

  const fetchMutation = useMutation({
    mutationFn: (feedId: string) => api.post(`/kb/${kbSlug}/rss/${feedId}/fetch`, {}),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["rssFeeds", kbSlug] }),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ feedId, isActive }: { feedId: string; isActive: boolean }) =>
      api.put(`/kb/${kbSlug}/rss/${feedId}`, { is_active: isActive }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["rssFeeds", kbSlug] }),
  });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">RSS 订阅管理</h1>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          添加订阅
        </button>
      </div>

      {showAdd && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (name.trim() && feedUrl.trim()) addMutation.mutate();
          }}
          className="bg-white p-6 rounded-lg border border-gray-200 mb-6"
        >
          <h2 className="text-lg font-semibold mb-4">添加 RSS 订阅源</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">名称</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="如：FreeBuf 安全资讯"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Feed URL</label>
              <input
                type="url"
                value={feedUrl}
                onChange={(e) => setFeedUrl(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="https://example.com/feed.xml"
              />
            </div>
          </div>
          <div className="mt-4 flex gap-3">
            <button
              type="submit"
              disabled={addMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              添加
            </button>
            <button
              type="button"
              onClick={() => setShowAdd(false)}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
            >
              取消
            </button>
          </div>
        </form>
      )}

      {isLoading ? (
        <p className="text-gray-500">加载中...</p>
      ) : feeds.length === 0 ? (
        <p className="text-gray-500">暂无 RSS 订阅源。点击上方按钮添加。</p>
      ) : (
        <div className="space-y-4">
          {feeds.map((feed) => {
            const statusInfo = STATUS_MAP[feed.last_fetch_status ?? ""] ?? {
              label: "未抓取",
              color: "bg-gray-100 text-gray-500",
            };
            return (
              <div key={feed.id} className="bg-white rounded-lg border border-gray-200">
                <div className="p-4 flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h3 className="font-semibold text-gray-900">{feed.name}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${statusInfo.color}`}>
                        {statusInfo.label}
                      </span>
                      {!feed.is_active && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">
                          已暂停
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mt-1 truncate">{feed.url}</p>
                    <div className="flex gap-4 mt-2 text-xs text-gray-400">
                      <span>累计抓取: {feed.total_fetched}</span>
                      {feed.last_fetched_at && (
                        <span>上次抓取: {new Date(feed.last_fetched_at).toLocaleString("zh-CN")}</span>
                      )}
                      {feed.last_error && (
                        <span className="text-red-500">错误: {feed.last_error.slice(0, 80)}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => fetchMutation.mutate(feed.id)}
                      disabled={fetchMutation.isPending}
                      className="px-3 py-1 text-sm bg-green-50 text-green-700 rounded-md hover:bg-green-100"
                    >
                      抓取
                    </button>
                    <button
                      onClick={() => toggleMutation.mutate({ feedId: feed.id, isActive: !feed.is_active })}
                      className={`px-3 py-1 text-sm rounded-md ${
                        feed.is_active
                          ? "bg-yellow-50 text-yellow-700 hover:bg-yellow-100"
                          : "bg-blue-50 text-blue-700 hover:bg-blue-100"
                      }`}
                    >
                      {feed.is_active ? "暂停" : "启用"}
                    </button>
                    <button
                      onClick={() => setExpandedFeed(expandedFeed === feed.id ? null : feed.id)}
                      className="px-3 py-1 text-sm bg-gray-50 text-gray-700 rounded-md hover:bg-gray-100"
                    >
                      {expandedFeed === feed.id ? "收起" : "历史"}
                    </button>
                    <button
                      onClick={() => {
                        if (confirm(`确定删除订阅「${feed.name}」？`)) deleteMutation.mutate(feed.id);
                      }}
                      className="px-3 py-1 text-sm bg-red-50 text-red-700 rounded-md hover:bg-red-100"
                    >
                      删除
                    </button>
                  </div>
                </div>

                {expandedFeed === feed.id && (
                  <div className="border-t border-gray-200 p-4">
                    {entries.length === 0 ? (
                      <p className="text-sm text-gray-500">暂无抓取记录</p>
                    ) : (
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-left text-gray-500">
                            <th className="pb-2">标题</th>
                            <th className="pb-2">状态</th>
                            <th className="pb-2">时间</th>
                          </tr>
                        </thead>
                        <tbody>
                          {entries.map((entry) => {
                            const es = ENTRY_STATUS[entry.status] ?? {
                              label: entry.status,
                              color: "bg-gray-100",
                            };
                            return (
                              <tr key={entry.id} className="border-t border-gray-100">
                                <td className="py-2">
                                  <a
                                    href={entry.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:underline"
                                  >
                                    {entry.title ?? entry.url}
                                  </a>
                                </td>
                                <td>
                                  <span className={`text-xs px-2 py-0.5 rounded-full ${es.color}`}>
                                    {es.label}
                                  </span>
                                </td>
                                <td className="text-gray-400">
                                  {new Date(entry.created_at).toLocaleString("zh-CN")}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
