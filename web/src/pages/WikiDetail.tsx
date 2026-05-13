import { useParams } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { WikiPage } from "../types";

export default function WikiDetail() {
  const { kbSlug, slug } = useParams();
  const { data: page, isLoading, error } = useQuery<WikiPage>({
    queryKey: ["wikiPage", kbSlug, slug],
    queryFn: () => api.get(`/kb/${kbSlug}/wiki/${slug}`),
    enabled: !!kbSlug && !!slug,
  });

  if (isLoading) return <div className="p-8 text-gray-500">加载中...</div>;
  if (error || !page) return <div className="p-8 text-red-600">页面不存在</div>;

  return (
    <div className="p-8 max-w-4xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">{page.title}</h1>

      <div className="flex gap-4 text-sm text-gray-500 mb-6">
        <span>类型: {page.page_type}</span>
        {page.source_ids && page.source_ids.length > 0 && <span>来源数: {page.source_ids.length}</span>}
      </div>

      {page.content && (
        <div className="prose prose-gray max-w-none">
          <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-6 rounded-lg border border-gray-200">
            {page.content}
          </pre>
        </div>
      )}

      {page.outgoing_links && page.outgoing_links.length > 0 && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold mb-2">相关页面</h2>
          <div className="flex flex-wrap gap-2">
            {page.outgoing_links.map((link) => (
              <a
                key={link}
                href={`/kb/${kbSlug}/wiki/${link}`}
                className="px-3 py-1 text-sm bg-blue-50 text-blue-700 rounded-full hover:bg-blue-100"
              >
                {link}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
