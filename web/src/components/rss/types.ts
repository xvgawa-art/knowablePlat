export interface RssFeed {
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
  filter_keywords: string[] | null;
  filter_authors: string[] | null;
  filter_categories: string[] | null;
}

export interface RssEntry {
  id: string;
  guid: string;
  url: string;
  title: string | null;
  status: string;
  published_at: string | null;
  created_at: string;
}

export interface FeedFormData {
  name: string;
  url: string;
  filter_keywords: string;
  filter_authors: string;
  filter_categories: string;
  poll_interval: number;
}

export const EMPTY_FORM: FeedFormData = {
  name: "",
  url: "",
  filter_keywords: "",
  filter_authors: "",
  filter_categories: "",
  poll_interval: 60,
};

export const STATUS_MAP: Record<string, { label: string; color: string }> = {
  success: { label: "成功", color: "bg-green-100 text-green-700" },
  partial: { label: "部分成功", color: "bg-yellow-100 text-yellow-700" },
  failed: { label: "失败", color: "bg-red-100 text-red-700" },
};

export const ENTRY_STATUS: Record<string, { label: string; color: string }> = {
  new: { label: "新", color: "bg-blue-100 text-blue-700" },
  ingesting: { label: "处理中", color: "bg-yellow-100 text-yellow-700" },
  completed: { label: "已完成", color: "bg-green-100 text-green-700" },
  filtered: { label: "已过滤", color: "bg-gray-100 text-gray-700" },
  failed: { label: "失败", color: "bg-red-100 text-red-700" },
};

export function parseList(val: string[] | null | undefined): string {
  return val?.join(", ") ?? "";
}

export function buildList(val: string): string[] | null {
  const items = val.split(",").map((s) => s.trim()).filter(Boolean);
  return items.length > 0 ? items : null;
}
