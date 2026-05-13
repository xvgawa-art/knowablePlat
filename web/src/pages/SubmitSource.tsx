import { useState } from "react";
import { useParams, useNavigate } from "react-router";
import { useMutation } from "@tanstack/react-query";
import { api } from "../api/client";

export default function SubmitSource() {
  const { kbSlug } = useParams();
  const navigate = useNavigate();
  const [url, setUrl] = useState("");

  const mutation = useMutation({
    mutationFn: (sourceUrl: string) => api.post(`/kb/${kbSlug}/sources`, { url: sourceUrl }),
    onSuccess: () => navigate(`/kb/${kbSlug}/sources`),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    mutation.mutate(url.trim());
  };

  return (
    <div className="p-8 max-w-lg">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">提交来源 URL</h1>

      <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg border border-gray-200">
        <label className="block text-sm font-medium text-gray-700 mb-2">文章 URL</label>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md"
          placeholder="https://example.com/article"
          required
        />
        <p className="mt-2 text-sm text-gray-500">
          系统将自动抓取文章内容，通过 LLM 提取关键信息并生成 Wiki 页面。
        </p>

        {mutation.isError && (
          <p className="mt-4 text-sm text-red-600">
            提交失败: {(mutation.error as Error).message}
          </p>
        )}

        <div className="mt-6 flex gap-3">
          <button
            type="submit"
            disabled={mutation.isPending}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {mutation.isPending ? "提交中..." : "提交"}
          </button>
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            取消
          </button>
        </div>
      </form>
    </div>
  );
}
