import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router";
import { api } from "../api/client";
import type { KnowledgeBase, GeneratedDoc } from "../types";

export default function Generate() {
  const queryClient = useQueryClient();
  const [selectedKbIds, setSelectedKbIds] = useState<string[]>([]);
  const [topic, setTopic] = useState("");

  const { data: knowledgeBases = [] } = useQuery<KnowledgeBase[]>({
    queryKey: ["knowledgeBases"],
    queryFn: () => api.get("/knowledge-bases"),
  });

  const { data: docs = [] } = useQuery<GeneratedDoc[]>({
    queryKey: ["generatedDocs"],
    queryFn: () => api.get("/generate"),
  });

  const generateMutation = useMutation({
    mutationFn: () => api.post<GeneratedDoc>("/generate", { kb_ids: selectedKbIds, topic }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["generatedDocs"] });
      setTopic("");
    },
  });

  function toggleKb(kbId: string) {
    setSelectedKbIds((prev) => (prev.includes(kbId) ? prev.filter((id) => id !== kbId) : [...prev, kbId]));
  }

  async function handleDelete(docId: string) {
    await api.del(`/generate/${docId}`);
    queryClient.invalidateQueries({ queryKey: ["generatedDocs"] });
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedKbIds.length === 0 || !topic.trim()) return;
    generateMutation.mutate();
  };

  return (
    <div className="p-8 max-w-4xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">知识生成</h1>

      <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">生成新文档</h2>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">选择知识库</label>
          <div className="flex flex-wrap gap-2">
            {knowledgeBases.map((kb) => (
              <button
                key={kb.id}
                type="button"
                onClick={() => toggleKb(kb.id)}
                className={`px-3 py-1.5 text-sm rounded-full border ${
                  selectedKbIds.includes(kb.id)
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-700 border-gray-300 hover:border-blue-400"
                }`}
              >
                {kb.name}
              </button>
            ))}
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">主题要求</label>
          <textarea
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="描述你想生成的文档主题，如「生成一篇关于 Web 安全发展趋势的综述」"
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <button
          type="submit"
          disabled={selectedKbIds.length === 0 || !topic.trim() || generateMutation.isPending}
          className="px-6 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {generateMutation.isPending ? "生成中..." : "开始生成"}
        </button>

        {generateMutation.isError && (
          <p className="mt-2 text-sm text-red-600">{generateMutation.error instanceof Error ? generateMutation.error.message : "生成失败"}</p>
        )}
      </form>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">生成历史</h2>
          <Link to="/generate/history" className="text-sm text-blue-600 hover:text-blue-800">
            查看全部
          </Link>
        </div>

        {docs.length === 0 ? (
          <p className="text-gray-400 text-center py-8">暂无生成记录</p>
        ) : (
          <div className="space-y-3">
            {docs.slice(0, 10).map((doc) => (
              <div key={doc.id} className="flex items-center justify-between bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-gray-900 truncate">{doc.title}</p>
                    <span
                      className={`px-2 py-0.5 text-xs rounded-full ${
                        doc.status === "completed"
                          ? "bg-green-50 text-green-700"
                          : doc.status === "generating"
                            ? "bg-yellow-50 text-yellow-700"
                            : "bg-red-50 text-red-700"
                      }`}
                    >
                      {doc.status === "completed" ? "已完成" : doc.status === "generating" ? "生成中" : "失败"}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    {doc.word_count} 字 · {new Date(doc.created_at).toLocaleDateString("zh-CN")}
                  </p>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  {doc.status === "completed" && (
                    <Link
                      to={`/generate/history/${doc.id}`}
                      className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded"
                    >
                      查看
                    </Link>
                  )}
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
                  >
                    删除
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
