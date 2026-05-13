import { useState } from "react";
import { useParams } from "react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import FeedForm from "../components/rss/FeedForm";
import FeedCard from "../components/rss/FeedCard";
import { EMPTY_FORM, parseList } from "../components/rss/types";
import type { RssFeed, RssEntry, FeedFormData } from "../components/rss/types";

export default function RssManager() {
  const { kbSlug } = useParams();
  const queryClient = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const [editingFeed, setEditingFeed] = useState<string | null>(null);
  const [form, setForm] = useState<FeedFormData>(EMPTY_FORM);
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
    mutationFn: (data: Record<string, unknown>) => api.post(`/kb/${kbSlug}/rss`, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["rssFeeds", kbSlug] }); setForm(EMPTY_FORM); setShowAdd(false); },
  });

  const editMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => api.put(`/kb/${kbSlug}/rss/${editingFeed}`, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["rssFeeds", kbSlug] }); setEditingFeed(null); setForm(EMPTY_FORM); },
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

  function startEdit(feed: RssFeed) {
    setEditingFeed(feed.id);
    setForm({
      name: feed.name, url: feed.url, poll_interval: feed.poll_interval,
      filter_keywords: parseList(feed.filter_keywords),
      filter_authors: parseList(feed.filter_authors),
      filter_categories: parseList(feed.filter_categories),
    });
  }

  const isFormOpen = showAdd || editingFeed !== null;
  const activeMutation = editingFeed ? editMutation : addMutation;

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">RSS 订阅管理</h1>
        <button
          onClick={() => { setForm(EMPTY_FORM); setEditingFeed(null); setShowAdd(!showAdd); }}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          添加订阅
        </button>
      </div>

      {isFormOpen && (
        <FeedForm
          form={form}
          setForm={setForm}
          isEditing={!!editingFeed}
          isPending={addMutation.isPending || editMutation.isPending}
          error={activeMutation.isError ? (activeMutation.error instanceof Error ? activeMutation.error : null) : null}
          onSubmit={(data) => {
            const payload = { name: form.name, url: form.url, ...data };
            if (editingFeed) editMutation.mutate(payload);
            else addMutation.mutate(payload);
          }}
          onCancel={() => { setShowAdd(false); setEditingFeed(null); setForm(EMPTY_FORM); }}
        />
      )}

      {isLoading ? (
        <p className="text-gray-500">加载中...</p>
      ) : feeds.length === 0 ? (
        <p className="text-gray-500">暂无 RSS 订阅源。点击上方按钮添加。</p>
      ) : (
        <div className="space-y-4">
          {feeds.map((feed) => (
            <FeedCard
              key={feed.id}
              feed={feed}
              entries={expandedFeed === feed.id ? entries : []}
              isExpanded={expandedFeed === feed.id}
              onToggleExpand={() => setExpandedFeed(expandedFeed === feed.id ? null : feed.id)}
              onFetch={() => fetchMutation.mutate(feed.id)}
              onToggle={() => toggleMutation.mutate({ feedId: feed.id, isActive: !feed.is_active })}
              onEdit={() => startEdit(feed)}
              onDelete={() => { if (confirm(`确定删除订阅「${feed.name}」？`)) deleteMutation.mutate(feed.id); }}
              fetchPending={fetchMutation.isPending}
            />
          ))}
        </div>
      )}
    </div>
  );
}
