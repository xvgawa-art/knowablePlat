import { useState } from "react";
import { useParams, Link } from "react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import Pagination from "../components/Pagination";
import { usePagination } from "../hooks/usePagination";
import { useBatchSelect } from "../hooks/useBatchSelect";
import type { WikiPageListItem, PaginatedResponse } from "../types";

const TYPE_LABELS: Record<string, string> = {
  source: "来源", entity: "实体", concept: "概念",
  comparison: "对比", tool: "工具", tool_category: "工具分类",
};

const TYPE_COLORS: Record<string, string> = {
  source: "bg-blue-100 text-blue-700", entity: "bg-green-100 text-green-700",
  concept: "bg-purple-100 text-purple-700", comparison: "bg-yellow-100 text-yellow-700",
  tool: "bg-red-100 text-red-700", tool_category: "bg-pink-100 text-pink-700",
};

type SearchMode = "keyword" | "semantic";

export default function WikiBrowser() {
  const { kbSlug } = useParams();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [searchMode, setSearchMode] = useState<SearchMode>("keyword");
  const [activeSearch, setActiveSearch] = useState("");
  const [activeMode, setActiveMode] = useState<SearchMode>("keyword");
  const [filterType, setFilterType] = useState<string | null>(null);
  const listPagination = usePagination(20);
  const searchPagination = usePagination(20);
  const listBatch = useBatchSelect();
  const searchBatch = useBatchSelect();

  const isSearching = activeSearch.length > 0;
  const pagination = isSearching ? searchPagination : listPagination;
  const batch = isSearching ? searchBatch : listBatch;

  const { data: listData, isLoading } = useQuery<PaginatedResponse<WikiPageListItem>>({
    queryKey: ["wikiPages", kbSlug, filterType, pagination.offset, pagination.pageSize],
    queryFn: () => api.get(`/kb/${kbSlug}/wiki`, {
      ...(filterType ? { page_type: filterType } : {}),
      offset: listPagination.offset, limit: listPagination.pageSize,
    }),
    enabled: !!kbSlug && !isSearching,
  });

  const { data: searchData, isLoading: searchLoading } = useQuery<PaginatedResponse<WikiPageListItem>>({
    queryKey: ["wikiSearch", kbSlug, activeSearch, activeMode, searchPagination.offset, searchPagination.pageSize],
    queryFn: () => {
      if (activeMode === "semantic") {
        return api.post(`/kb/${kbSlug}/wiki/semantic-search`, {
          query: activeSearch, limit: searchPagination.pageSize, offset: searchPagination.offset,
        });
      }
      return api.get(`/kb/${kbSlug}/wiki`, { search: activeSearch, offset: searchPagination.offset, limit: searchPagination.pageSize });
    },
    enabled: !!kbSlug && isSearching,
  });

  const pages = isSearching ? (searchData?.items ?? []) : (listData?.items ?? []);
  const total = isSearching ? (searchData?.total ?? 0) : (listData?.total ?? 0);
  const loading = isSearching ? searchLoading : isLoading;

  const batchDeleteMutation = useMutation({
    mutationFn: (ids: string[]) => api.post(`/kb/${kbSlug}/wiki/batch-delete`, { ids }),
    onSuccess: () => {
      batch.clearAll();
      queryClient.invalidateQueries({ queryKey: ["wikiPages", kbSlug] });
      queryClient.invalidateQueries({ queryKey: ["wikiSearch", kbSlug] });
    },
  });

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!searchQuery.trim()) { setActiveSearch(""); return; }
    setActiveSearch(searchQuery.trim());
    setActiveMode(searchMode);
    searchPagination.reset();
  }

  function clearSearch() {
    setSearchQuery("");
    setActiveSearch("");
  }

  function handleFilterChange(type: string | null) {
    setFilterType(type);
    listPagination.reset();
    listBatch.clearAll();
  }

  function handleBatchDelete() {
    if (!confirm(`确定删除选中的 ${batch.selectedIds.size} 项？`)) return;
    batchDeleteMutation.mutate(Array.from(batch.selectedIds));
  }

  const allIds = pages.map((p) => p.id);

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900">Wiki 页面</h1>
        <div className="flex gap-3 items-center">
          {batch.selectedIds.size > 0 && (
            <button onClick={handleBatchDelete} disabled={batchDeleteMutation.isPending}
              className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50">
              删除选中 ({batch.selectedIds.size})
            </button>
          )}
          <Link to={`/kb/${kbSlug}/wiki/graph`} className="text-sm text-blue-600 hover:text-blue-800">图谱视图</Link>
        </div>
      </div>

      <form onSubmit={handleSearch} className="mb-6 flex gap-2">
        <div className="flex gap-1 bg-gray-100 rounded-lg p-0.5">
          <button type="button" onClick={() => setSearchMode("keyword")}
            className={`px-3 py-1 text-xs rounded-md ${searchMode === "keyword" ? "bg-white shadow text-gray-900" : "text-gray-500 hover:text-gray-700"}`}>
            关键词</button>
          <button type="button" onClick={() => setSearchMode("semantic")}
            className={`px-3 py-1 text-xs rounded-md ${searchMode === "semantic" ? "bg-white shadow text-gray-900" : "text-gray-500 hover:text-gray-700"}`}>
            语义搜索</button>
        </div>
        <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={searchMode === "semantic" ? "输入自然语言描述搜索..." : "输入关键词搜索..."}
          className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <button type="submit" className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700">搜索</button>
        {isSearching && <button type="button" onClick={clearSearch} className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200">清除</button>}
      </form>

      {!isSearching && (
        <div className="mb-4 flex flex-wrap gap-2">
          <button type="button" onClick={() => handleFilterChange(null)}
            className={`px-3 py-1 text-xs rounded-full ${filterType === null ? "bg-gray-800 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}>
            全部</button>
          {Object.entries(TYPE_LABELS).map(([type, label]) => (
            <button key={type} type="button" onClick={() => handleFilterChange(filterType === type ? null : type)}
              className={`px-3 py-1 text-xs rounded-full ${filterType === type ? (TYPE_COLORS[type] ?? "bg-gray-800 text-white") : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}>
              {label}</button>
          ))}
        </div>
      )}

      {isSearching && (
        <p className="text-sm text-gray-500 mb-4">
          {activeMode === "semantic" ? "语义" : "关键词"}搜索: "{activeSearch}" — 找到 {total} 个结果
        </p>
      )}

      {loading ? (
        <p className="text-gray-500">加载中...</p>
      ) : pages.length === 0 ? (
        <p className="text-gray-500">{isSearching ? "未找到匹配的 Wiki 页面" : "暂无 Wiki 页面。提交来源后系统会自动生成。"}</p>
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
            {pages.map((page) => (
              <WikiPageCard key={page.id} page={page} kbSlug={kbSlug!} isSelected={batch.isSelected(page.id)}
                onToggle={() => batch.toggle(page.id)} />
            ))}
          </div>
          <Pagination page={pagination.page} pageSize={pagination.pageSize} total={total} onPageChange={pagination.setPage} />
        </>
      )}
    </div>
  );
}

function WikiPageCard({ page, kbSlug, isSelected, onToggle }: {
  page: WikiPageListItem; kbSlug: string; isSelected: boolean; onToggle: () => void;
}) {
  return (
    <Link to={`/kb/${kbSlug}/wiki/${page.slug}`}
      className="flex items-center gap-3 p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md">
      <input type="checkbox" checked={isSelected} onChange={onToggle}
        onClick={(e) => e.stopPropagation()} className="rounded border-gray-300" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-900">{page.title}</h3>
          <span className={`text-xs px-2 py-1 rounded-full ${TYPE_COLORS[page.page_type] ?? "bg-gray-100 text-gray-600"}`}>
            {TYPE_LABELS[page.page_type] ?? page.page_type}</span>
        </div>
        <p className="text-sm text-gray-400 mt-1">{new Date(page.created_at).toLocaleDateString("zh-CN")}</p>
      </div>
    </Link>
  );
}
