import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router";
import { api } from "../api/client";
import type { KnowledgeBase } from "../types";
import EditForm from "../components/kb/EditForm";

export default function KnowledgeBases() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [editingSlug, setEditingSlug] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");

  const { data: knowledgeBases = [] } = useQuery<KnowledgeBase[]>({
    queryKey: ["knowledgeBases"],
    queryFn: () => api.get("/knowledge-bases"),
  });

  const createMutation = useMutation({
    mutationFn: (data: { name: string; slug: string; description?: string }) =>
      api.post("/knowledge-bases", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledgeBases"] });
      setName("");
      setSlug("");
      setDescription("");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ kbSlug, data }: { kbSlug: string; data: { name?: string; description?: string } }) =>
      api.put(`/knowledge-bases/${kbSlug}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledgeBases"] });
      setEditingSlug(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (kbSlug: string) => api.del(`/knowledge-bases/${kbSlug}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["knowledgeBases"] }),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !slug.trim()) return;
    createMutation.mutate({ name: name.trim(), slug: slug.trim(), description: description.trim() || undefined });
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">知识库管理</h1>

      <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg border border-gray-200 mb-8">
        <h2 className="text-lg font-semibold mb-4">创建知识库</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">名称</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="如：Web 安全"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Slug</label>
            <input
              type="text"
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="如：web-security"
            />
          </div>
        </div>
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            rows={2}
            placeholder="知识库描述（可选）"
          />
        </div>
        <button
          type="submit"
          disabled={createMutation.isPending}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          创建
        </button>
      </form>

      <div className="space-y-4">
        {knowledgeBases.map((kb) => (
          <div key={kb.id} className="bg-white p-4 rounded-lg border border-gray-200">
            {editingSlug === kb.slug ? (
              <EditForm
                kb={kb}
                editName={editName}
                editDesc={editDesc}
                setEditName={setEditName}
                setEditDesc={setEditDesc}
                onSave={() => {
                  if (!editName.trim()) return;
                  updateMutation.mutate({ kbSlug: kb.slug, data: { name: editName.trim(), description: editDesc.trim() } });
                }}
                onCancel={() => setEditingSlug(null)}
                isPending={updateMutation.isPending}
              />
            ) : (
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-gray-900">{kb.name}</h3>
                    {kb.is_system && (
                      <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded">系统</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500">{kb.slug}</p>
                  {kb.description && (
                    <p className="text-sm text-gray-400 mt-1 line-clamp-1">{kb.description}</p>
                  )}
                  <div className="flex gap-3 mt-1 text-xs text-gray-400">
                    <span>{kb.source_count} 来源</span>
                    <span>{kb.wiki_page_count} Wiki</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setEditName(kb.name);
                      setEditDesc(kb.description ?? "");
                      setEditingSlug(kb.slug);
                    }}
                    disabled={kb.is_system}
                    className={`px-3 py-1 text-sm rounded-md ${
                      kb.is_system
                        ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                        : "bg-gray-50 text-gray-700 hover:bg-gray-100"
                    }`}
                    title={kb.is_system ? "系统内置知识库，不可编辑" : "编辑"}
                  >
                    编辑
                  </button>
                  <Link
                    to={`/kb/${kb.slug}`}
                    className="px-3 py-1 text-sm bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100"
                  >
                    进入
                  </Link>
                  <button
                    onClick={() => {
                      if (confirm(`确定删除知识库「${kb.name}」？`)) deleteMutation.mutate(kb.slug);
                    }}
                    disabled={kb.is_system}
                    className={`px-3 py-1 text-sm rounded-md ${
                      kb.is_system
                        ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                        : "bg-red-50 text-red-700 hover:bg-red-100"
                    }`}
                    title={kb.is_system ? "系统内置知识库，不可删除" : "删除"}
                  >
                    删除
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

