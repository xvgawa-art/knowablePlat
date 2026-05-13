import type { RssFeed, RssEntry } from "./types";
import { STATUS_MAP, ENTRY_STATUS } from "./types";

interface FeedCardProps {
  feed: RssFeed;
  entries: RssEntry[];
  isExpanded: boolean;
  onToggleExpand: () => void;
  onFetch: () => void;
  onToggle: () => void;
  onEdit: () => void;
  onDelete: () => void;
  fetchPending: boolean;
}

export default function FeedCard({
  feed, entries, isExpanded, onToggleExpand, onFetch, onToggle, onEdit, onDelete, fetchPending,
}: FeedCardProps) {
  const statusInfo = STATUS_MAP[feed.last_fetch_status ?? ""] ?? { label: "未抓取", color: "bg-gray-100 text-gray-500" };
  const hasFilters =
    ((feed.filter_keywords?.length ?? 0) > 0) ||
    ((feed.filter_authors?.length ?? 0) > 0) ||
    ((feed.filter_categories?.length ?? 0) > 0);

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="p-4 flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <FeedHeader feed={feed} statusInfo={statusInfo} hasFilters={hasFilters} />
          <FeedDetails feed={feed} hasFilters={hasFilters} />
        </div>
        <FeedActions
          feed={feed}
          fetchPending={fetchPending}
          isExpanded={isExpanded}
          onFetch={onFetch}
          onToggle={onToggle}
          onEdit={onEdit}
          onToggleExpand={onToggleExpand}
          onDelete={onDelete}
        />
      </div>
      {isExpanded && <EntryTable entries={entries} />}
    </div>
  );
}

function FeedHeader({ feed, statusInfo, hasFilters }: { feed: RssFeed; statusInfo: { label: string; color: string }; hasFilters: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <h3 className="font-semibold text-gray-900">{feed.name}</h3>
      <span className={`text-xs px-2 py-0.5 rounded-full ${statusInfo.color}`}>{statusInfo.label}</span>
      {!feed.is_active && <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">已暂停</span>}
      {hasFilters && <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">过滤</span>}
    </div>
  );
}

function FeedDetails({ feed, hasFilters }: { feed: RssFeed; hasFilters: boolean }) {
  return (
    <>
      <p className="text-sm text-gray-500 mt-1 truncate">{feed.url}</p>
      <div className="flex flex-wrap gap-3 mt-2 text-xs text-gray-400">
        <span>累计抓取: {feed.total_fetched}</span>
        <span>间隔: {feed.poll_interval}分钟</span>
        {feed.last_fetched_at && <span>上次抓取: {new Date(feed.last_fetched_at).toLocaleString("zh-CN")}</span>}
        {feed.last_error && <span className="text-red-500">错误: {feed.last_error.slice(0, 80)}</span>}
      </div>
      {hasFilters && <FilterTags feed={feed} />}
    </>
  );
}

function FilterTags({ feed }: { feed: RssFeed }) {
  return (
    <div className="flex flex-wrap gap-2 mt-2">
      {feed.filter_keywords?.map((kw) => (
        <span key={kw} className="text-xs px-2 py-0.5 bg-blue-50 text-blue-600 rounded">关键词: {kw}</span>
      ))}
      {feed.filter_authors?.map((a) => (
        <span key={a} className="text-xs px-2 py-0.5 bg-green-50 text-green-600 rounded">作者: {a}</span>
      ))}
      {feed.filter_categories?.map((c) => (
        <span key={c} className="text-xs px-2 py-0.5 bg-purple-50 text-purple-600 rounded">分类: {c}</span>
      ))}
    </div>
  );
}

function FeedActions({ feed, fetchPending, isExpanded, onFetch, onToggle, onEdit, onToggleExpand, onDelete }: {
  feed: RssFeed; fetchPending: boolean; isExpanded: boolean;
  onFetch: () => void; onToggle: () => void; onEdit: () => void;
  onToggleExpand: () => void; onDelete: () => void;
}) {
  return (
    <div className="flex gap-2 ml-4 shrink-0">
      <button onClick={onFetch} disabled={fetchPending} className="px-3 py-1 text-sm bg-green-50 text-green-700 rounded-md hover:bg-green-100">抓取</button>
      <button onClick={onToggle} className={`px-3 py-1 text-sm rounded-md ${feed.is_active ? "bg-yellow-50 text-yellow-700 hover:bg-yellow-100" : "bg-blue-50 text-blue-700 hover:bg-blue-100"}`}>
        {feed.is_active ? "暂停" : "启用"}
      </button>
      <button onClick={onEdit} className="px-3 py-1 text-sm bg-gray-50 text-gray-700 rounded-md hover:bg-gray-100">编辑</button>
      <button onClick={onToggleExpand} className="px-3 py-1 text-sm bg-gray-50 text-gray-700 rounded-md hover:bg-gray-100">
        {isExpanded ? "收起" : "历史"}
      </button>
      <button onClick={onDelete} className="px-3 py-1 text-sm bg-red-50 text-red-700 rounded-md hover:bg-red-100">删除</button>
    </div>
  );
}

function EntryTable({ entries }: { entries: RssEntry[] }) {
  if (entries.length === 0) return <div className="border-t border-gray-200 p-4"><p className="text-sm text-gray-500">暂无抓取记录</p></div>;

  return (
    <div className="border-t border-gray-200 p-4">
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
            const es = ENTRY_STATUS[entry.status] ?? { label: entry.status, color: "bg-gray-100" };
            return (
              <tr key={entry.id} className="border-t border-gray-100">
                <td className="py-2">
                  <a href={entry.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                    {entry.title ?? entry.url}
                  </a>
                </td>
                <td><span className={`text-xs px-2 py-0.5 rounded-full ${es.color}`}>{es.label}</span></td>
                <td className="text-gray-400">{new Date(entry.created_at).toLocaleString("zh-CN")}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
