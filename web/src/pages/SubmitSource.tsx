import { useState } from "react";
import { useParams, useNavigate } from "react-router";
import { useMutation } from "@tanstack/react-query";
import { api } from "../api/client";

interface SourceResponse {
  id: string;
  url: string;
  status: string;
}

export default function SubmitSource() {
  const { kbSlug } = useParams();
  const navigate = useNavigate();
  const [url, setUrl] = useState("");
  const [batchUrls, setBatchUrls] = useState("");
  const [mode, setMode] = useState<"single" | "batch">("single");

  const singleMutation = useMutation({
    mutationFn: (sourceUrl: string) => api.post(`/kb/${kbSlug}/sources`, { url: sourceUrl }),
    onSuccess: () => navigate(`/kb/${kbSlug}/sources`),
  });

  const batchMutation = useMutation({
    mutationFn: (urls: string[]) => api.post<SourceResponse[]>(`/kb/${kbSlug}/sources/batch`, { urls }),
    onSuccess: () => navigate(`/kb/${kbSlug}/sources`),
  });

  const handleSingleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    singleMutation.mutate(url.trim());
  };

  const handleBatchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const urls = batchUrls
      .split("\n")
      .map((u) => u.trim())
      .filter(Boolean);
    if (urls.length === 0) return;
    batchMutation.mutate(urls);
  };

  const isPending = singleMutation.isPending || batchMutation.isPending;
  const error = singleMutation.error ?? batchMutation.error;

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">提交来源 URL</h1>

      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setMode("single")}
          className={`px-4 py-2 text-sm rounded-md ${
            mode === "single" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          单个提交
        </button>
        <button
          onClick={() => setMode("batch")}
          className={`px-4 py-2 text-sm rounded-md ${
            mode === "batch" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          批量提交
        </button>
      </div>

      {mode === "single" ? (
        <form onSubmit={handleSingleSubmit} className="bg-white p-6 rounded-lg border border-gray-200">
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

          {error && <p className="mt-4 text-sm text-red-600">提交失败: {error.message}</p>}

          <div className="mt-6 flex gap-3">
            <button
              type="submit"
              disabled={isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isPending ? "提交中..." : "提交"}
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
      ) : (
        <form onSubmit={handleBatchSubmit} className="bg-white p-6 rounded-lg border border-gray-200">
          <label className="block text-sm font-medium text-gray-700 mb-2">批量 URL（每行一个）</label>
          <textarea
            value={batchUrls}
            onChange={(e) => setBatchUrls(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md font-mono text-sm"
            rows={8}
            placeholder={"https://example.com/article1\nhttps://example.com/article2\nhttps://example.com/article3"}
            required
          />
          <p className="mt-2 text-sm text-gray-500">
            已输入 {batchUrls.split("\n").filter((u) => u.trim()).length} 个 URL。重复的 URL 会被自动跳过。
          </p>

          {error && <p className="mt-4 text-sm text-red-600">提交失败: {error.message}</p>}

          <div className="mt-6 flex gap-3">
            <button
              type="submit"
              disabled={isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isPending ? "提交中..." : "批量提交"}
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
      )}
    </div>
  );
}
