import { useState } from "react";
import { useParams, Link } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { WikiPageListItem } from "../types";

const TYPE_LABELS: Record<string, string> = {
  source: "来源",
  entity: "实体",
  concept: "概念",
  comparison: "对比",
  tool: "工具",
  tool_category: "工具分类",
};

type SearchMode = "keyword" | "semantic";

const TYPE_COLORS: Record<string, string> = {
  source: "bg-blue-100 text-blue-700",
  entity: "bg-green-100 text-green-700",
  concept: "bg-purple-100 text-purple-700",
  comparison: "bg-yellow-100 text-yellow-700",
  tool: "bg-red-100 text-red-700",
  tool_category: "bg-pink-100 text-pink-700",
};

export default function WikiBrowser() {
  const { kbSlug } = useParams();
  const [searchQuery, setSearchQuery] = useState("");
  const [searchMode, setSearchMode] = useState<SearchMode>("keyword");
  const [activeSearch, setActiveSearch] = useState("");
  const [activeMode, setActiveMode] = useState<SearchMode>("keyword");
  const [filterType, setFilterType] = useState<string | null>(null);

  const isSearching = activeSearch.length > 0;

  const { data: pages = [], isLoading } = useQuery<WikiPageListItem[]>({
    queryKey: ["wikiPages", kbSlug, filterType],
    queryFn: () => api.get(`/kb/${kbSlug}/wiki`, { ...(filterType ? { page_type: filterType } : {}), limit: 50 }),
    enabled: !!kbSlug && !isSearching,
  });

  const { data: searchResults = [], isLoading: searchLoading } = useQuery<WikiPageListItem[]>({
    queryKey: ["wikiSearch", kbSlug, activeSearch, activeMode],
    queryFn: () => {
      if (activeMode === "semantic") {
        return api.post(`/kb/${kbSlug}/wiki/semantic-search`, { query: activeSearch, limit: 20 });
      }
      return api.get(`/kb/${kbSlug}/wiki`, { search: activeSearch, limit: 50 });
    },
    enabled: !!kbSlug && isSearching,
  });

  const displayedPages = isSearching ? searchResults : pages;
  const loading = isSearching ? searchLoading : isLoading;

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setActiveSearch("");
      return;
    }
    setActiveSearch(searchQuery.trim());
    setActiveMode(searchMode);
  }

  function clearSearch() {
    setSearchQuery("");
    setActiveSearch("");
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900">Wiki 页面</h1>
        <Link to={`/kb/${kbSlug}/wiki/graph`} className="text-sm text-blue-600 hover:text-blue-800">
          图谱视图
        </Link>
      </div>

      <form onSubmit={handleSearch} className="mb-6 flex gap-2">
        <div className="flex gap-1 bg-gray-100 rounded-lg p-0.5">
          <button
            type="button"
            onClick={() => setSearchMode("keyword")}
            className={`px-3 py-1 text-xs rounded-md ${
              searchMode === "keyword" ? "bg-white shadow text-gray-900" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            关键词
          </button>
          <button
            type="button"
            onClick={() => setSearchMode("semantic")}
            className={`px-3 py-1 text-xs rounded-md ${
              searchMode === "semantic" ? "bg-white shadow text-gray-900" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            语义搜索
          </button>
        </div>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={searchMode === "semantic" ? "输入自然语言描述搜索..." : "输入关键词搜索..."}
          className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          搜索
        </button>
        {isSearching && (
          <button
            type="button"
            onClick={clearSearch}
            className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            清除
          </button>
        )}
      </form>

      {!isSearching && (
        <div className="mb-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setFilterType(null)}
            className={`px-3 py-1 text-xs rounded-full ${
              filterType === null ? "bg-gray-800 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            全部
          </button>
          {Object.entries(TYPE_LABELS).map(([type, label]) => (
            <button
              key={type}
              type="button"
              onClick={() => setFilterType(filterType === type ? null : type)}
              className={`px-3 py-1 text-xs rounded-full ${
                filterType === type
                  ? TYPE_COLORS[type] ?? "bg-gray-800 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      )}

      {isSearching && (
        <p className="text-sm text-gray-500 mb-4">
          {activeMode === "semantic" ? "语义" : "关键词"}搜索: "{activeSearch}" — 找到 {searchResults.length} 个结果
        </p>
      )}

      {loading ? (
        <p className="text-gray-500">加载中...</p>
      ) : displayedPages.length === 0 ? (
        <p className="text-gray-500">
          {isSearching ? "未找到匹配的 Wiki 页面" : "暂无 Wiki 页面。提交来源后系统会自动生成。"}
        </p>
      ) : (
        <div className="space-y-3">
          {displayedPages.map((page) => (
            <Link
              key={page.id}
              to={`/kb/${kbSlug}/wiki/${page.slug}`}
              className="block p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-gray-900">{page.title}</h3>
                <span className={`text-xs px-2 py-1 rounded-full ${TYPE_COLORS[page.page_type] ?? "bg-gray-100 text-gray-600"}`}>
                  {TYPE_LABELS[page.page_type] ?? page.page_type}
                </span>
              </div>
              <p className="text-sm text-gray-400 mt-1">
                {new Date(page.created_at).toLocaleDateString("zh-CN")}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
