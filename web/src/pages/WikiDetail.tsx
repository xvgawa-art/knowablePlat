import { useParams } from "react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";
import MarkdownRenderer from "../components/MarkdownRenderer";
import type { WikiPage } from "../types";

export default function WikiDetail() {
  const { kbSlug, slug } = useParams();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState("");

  const { data: page, isLoading, error } = useQuery<WikiPage>({
    queryKey: ["wikiPage", kbSlug, slug],
    queryFn: () => api.get(`/kb/${kbSlug}/wiki/${slug}`),
    enabled: !!kbSlug && !!slug,
  });

  const updateMutation = useMutation({
    mutationFn: (content: string) =>
      api.put<WikiPage>(`/kb/${kbSlug}/wiki/${slug}`, { content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wikiPage", kbSlug, slug] });
      setEditing(false);
    },
  });

  if (isLoading) return <div className="p-8 text-gray-500">加载中...</div>;
  if (error || !page) return <div className="p-8 text-red-600">页面不存在</div>;

  const startEdit = () => {
    setEditContent(page.content ?? "");
    setEditing(true);
  };

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{page.title}</h1>
        {!editing && (
          <button
            onClick={startEdit}
            className="px-3 py-1.5 text-sm rounded border border-gray-300 hover:bg-gray-50"
          >
            编辑
          </button>
        )}
      </div>

      <div className="flex gap-4 text-sm text-gray-500 mb-6">
        <span>类型: {page.page_type}</span>
        {page.source_ids && page.source_ids.length > 0 && <span>来源数: {page.source_ids.length}</span>}
      </div>

      {editing ? (
        <div>
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            className="w-full h-[600px] p-4 text-sm font-mono border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
          <div className="flex gap-3 mt-4">
            <button
              onClick={() => updateMutation.mutate(editContent)}
              disabled={updateMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {updateMutation.isPending ? "保存中..." : "保存"}
            </button>
            <button
              onClick={() => setEditing(false)}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              取消
            </button>
          </div>
        </div>
      ) : (
        <>
          {page.content && <MarkdownRenderer content={page.content} kbSlug={kbSlug} />}

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
        </>
      )}
    </div>
  );
}
