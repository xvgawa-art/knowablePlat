import type { FeedFormData } from "./types";
import { EMPTY_FORM, buildList } from "./types";

interface FeedFormProps {
  form: FeedFormData;
  setForm: (form: FeedFormData) => void;
  isEditing: boolean;
  isPending: boolean;
  error: Error | null;
  onSubmit: (data: { filter_keywords: string[] | null; filter_authors: string[] | null; filter_categories: string[] | null; poll_interval: number }) => void;
  onCancel: () => void;
}

export default function FeedForm({ form, setForm, isEditing, isPending, error, onSubmit, onCancel }: FeedFormProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim() || !form.url.trim()) return;
    onSubmit({
      filter_keywords: buildList(form.filter_keywords),
      filter_authors: buildList(form.filter_authors),
      filter_categories: buildList(form.filter_categories),
      poll_interval: form.poll_interval,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg border border-gray-200 mb-6">
      <h2 className="text-lg font-semibold mb-4">{isEditing ? "编辑订阅源" : "添加 RSS 订阅源"}</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">名称</label>
          <input
            type="text"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="如：FreeBuf 安全资讯"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Feed URL</label>
          <input
            type="url"
            value={form.url}
            onChange={(e) => setForm({ ...form, url: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="https://example.com/feed.xml"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">关键词过滤（逗号分隔）</label>
          <input
            type="text"
            value={form.filter_keywords}
            onChange={(e) => setForm({ ...form, filter_keywords: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="如：XSS, SQL注入（留空不过滤）"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">作者过滤（逗号分隔）</label>
          <input
            type="text"
            value={form.filter_authors}
            onChange={(e) => setForm({ ...form, filter_authors: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="如：Alice, Bob（留空不过滤）"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">分类过滤（逗号分隔）</label>
          <input
            type="text"
            value={form.filter_categories}
            onChange={(e) => setForm({ ...form, filter_categories: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="如：Security, Web（留空不过滤）"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">轮询间隔（分钟）</label>
          <input
            type="number"
            min={5}
            value={form.poll_interval}
            onChange={(e) => setForm({ ...form, poll_interval: Number(e.target.value) || 60 })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>
      </div>
      <div className="mt-4 flex items-center gap-3">
        <button
          type="submit"
          disabled={isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {isPending ? "处理中..." : isEditing ? "保存" : "添加"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
        >
          取消
        </button>
        {error && <p className="text-sm text-red-600">{error.message}</p>}
      </div>
    </form>
  );
}

export { EMPTY_FORM };
