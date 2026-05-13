import { useState } from "react";
import { useParams, Link } from "react-router";
import { api } from "../api/client";
import MarkdownRenderer from "../components/MarkdownRenderer";
import type { ChatMessage } from "../types";

interface QueryResponse {
  answer: string;
  referenced_pages: { slug: string; title: string }[];
}

export default function Chat() {
  const { kbSlug } = useParams();
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim() || !kbSlug || loading) return;

    const q = question.trim();
    setQuestion("");
    setError(null);
    setLoading(true);

    try {
      const data = await api.post<QueryResponse>(`/kb/${kbSlug}/wiki/query`, { question: q });
      setMessages((prev) => [...prev, { question: q, answer: data.answer, referenced_pages: data.referenced_pages }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "查询失败");
      setMessages((prev) => [...prev, { question: q, answer: "", referenced_pages: [] }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-900">对话查询</h1>
        <p className="text-sm text-gray-500 mt-1">在当前知识库上下文中提问</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-20">
            <p className="text-4xl mb-4">💬</p>
            <p>输入问题，基于当前知识库的 Wiki 知识进行问答</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className="space-y-3">
            <div className="flex justify-end">
              <div className="max-w-[70%] px-4 py-2 bg-blue-600 text-white rounded-2xl rounded-br-sm">
                {msg.question}
              </div>
            </div>

            <div className="flex justify-start">
              <div className="max-w-[70%] px-4 py-3 bg-gray-100 rounded-2xl rounded-bl-sm">
                {msg.answer ? (
                  <div className="text-sm text-gray-800">
                    <MarkdownRenderer content={msg.answer} kbSlug={kbSlug} />
                  </div>
                ) : (
                  <p className="text-sm text-red-500">查询失败</p>
                )}

                {msg.referenced_pages.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <p className="text-xs text-gray-500 mb-2">引用页面：</p>
                    <div className="flex flex-wrap gap-1">
                      {msg.referenced_pages.map((p) => (
                        <Link
                          key={p.slug}
                          to={`/kb/${kbSlug}/wiki/${p.slug}`}
                          className="px-2 py-0.5 text-xs bg-blue-50 text-blue-600 rounded hover:bg-blue-100"
                        >
                          {p.title}
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="px-4 py-3 bg-gray-100 rounded-2xl rounded-bl-sm">
              <p className="text-sm text-gray-500">思考中...</p>
            </div>
          </div>
        )}
      </div>

      {error && <div className="px-6 py-2 text-sm text-red-600 bg-red-50">{error}</div>}

      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200 bg-white">
        <div className="flex gap-3">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="输入你的问题..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading || !kbSlug}
          />
          <button
            type="submit"
            disabled={loading || !question.trim() || !kbSlug}
            className="px-6 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            发送
          </button>
        </div>
      </form>
    </div>
  );
}
