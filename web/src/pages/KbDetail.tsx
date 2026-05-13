import { useParams, Link } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { KnowledgeBase } from "../types";

export default function KbDetail() {
  const { kbSlug } = useParams();
  const { data: kb, isLoading, error } = useQuery<KnowledgeBase>({
    queryKey: ["kb", kbSlug],
    queryFn: () => api.get(`/knowledge-bases/${kbSlug}`),
    enabled: !!kbSlug,
  });

  if (isLoading) return <div className="p-8 text-gray-500">加载中...</div>;
  if (error || !kb) return <div className="p-8 text-red-600">知识库不存在</div>;

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900">{kb.name}</h1>
      {kb.description && <p className="mt-2 text-gray-600">{kb.description}</p>}

      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          to={`/kb/${kbSlug}/wiki`}
          className="p-6 bg-white rounded-lg border border-gray-200 hover:shadow-md"
        >
          <h2 className="text-lg font-semibold">📖 Wiki</h2>
          <p className="mt-2 text-sm text-gray-500">浏览知识库的 wiki 页面</p>
        </Link>
        <Link
          to={`/kb/${kbSlug}/sources`}
          className="p-6 bg-white rounded-lg border border-gray-200 hover:shadow-md"
        >
          <h2 className="text-lg font-semibold">📄 来源</h2>
          <p className="mt-2 text-sm text-gray-500">{kb.source_count} 个来源文档</p>
        </Link>
        <div className="p-6 bg-white rounded-lg border border-gray-200">
          <h2 className="text-lg font-semibold">📊 统计</h2>
          <div className="mt-4 space-y-2 text-sm">
            <p>来源数: {kb.source_count}</p>
            <p>Wiki 页数: {kb.wiki_page_count}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
